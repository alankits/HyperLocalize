"""Thin wrappers around ffprobe / ffmpeg (ADR 0004 validation, UC2 analysis, UC4 rendering).

Commands are built as argument lists (never through a shell), and file names are
our own random storage paths, never user-supplied names.
"""
import json
import re
import shutil
import subprocess
from functools import lru_cache

from django.conf import settings


class MediaError(Exception):
    pass


ALLOWED_CONTAINERS = {"mov,mp4,m4a,3gp,3g2,mj2", "matroska,webm", "avi"}
ALLOWED_VIDEO_CODECS = {"h264", "hevc", "vp8", "vp9", "av1", "mpeg4"}
ALLOWED_AUDIO_CODECS = {"aac", "mp3", "opus", "vorbis", "pcm_s16le", "flac"}


@lru_cache(maxsize=None)
def _tool(name):
    configured = getattr(settings, f"HL_{name.upper()}", "")
    if configured:
        return configured
    found = shutil.which(name)
    if found:
        return found
    try:  # development fallback: the static-ffmpeg package (requirements-dev.txt)
        import static_ffmpeg

        static_ffmpeg.add_paths(weak=True)
        found = shutil.which(name)
    except ImportError:
        found = None
    if not found:
        raise MediaError(f"{name} is not installed (set HL_{name.upper()} or install ffmpeg)")
    return found


def ffmpeg():
    return _tool("ffmpeg")


def ffprobe():
    return _tool("ffprobe")


def _run(args, timeout=600):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        raise MediaError("; ".join(tail) or f"exit code {proc.returncode}")
    return proc


def probe(path):
    """Return a dict with container, duration_ms, video/audio codecs. Raises MediaError if unreadable."""
    try:
        proc = _run([ffprobe(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)], 60)
    except subprocess.TimeoutExpired:
        raise MediaError("ffprobe timed out") from None
    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    video = [s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    try:
        duration_ms = int(float(fmt.get("duration", 0)) * 1000)
    except ValueError:
        duration_ms = 0
    return {
        "container": fmt.get("format_name", ""),
        "duration_ms": duration_ms,
        "video_codec": video[0].get("codec_name") if video else None,
        "audio_codec": audio[0].get("codec_name") if audio else None,
        "width": video[0].get("width") if video else None,
        "height": video[0].get("height") if video else None,
    }


def validate_source(info, *, max_seconds):
    """Return a list of problems (empty if acceptable). MVP limits come from settings (ADR 0004)."""
    problems = []
    if info["container"] not in ALLOWED_CONTAINERS:
        problems.append(f"unsupported container '{info['container']}' (use MP4, MOV, MKV, WebM or AVI)")
    if not info["video_codec"]:
        problems.append("no video stream found")
    elif info["video_codec"] not in ALLOWED_VIDEO_CODECS:
        problems.append(f"unsupported video codec '{info['video_codec']}'")
    if not info["audio_codec"]:
        problems.append("no audio stream found (the source speech is needed)")
    elif info["audio_codec"] not in ALLOWED_AUDIO_CODECS:
        problems.append(f"unsupported audio codec '{info['audio_codec']}'")
    if info["duration_ms"] <= 0:
        problems.append("could not read the duration")
    elif info["duration_ms"] > max_seconds * 1000:
        problems.append(f"video is longer than the MVP limit of {max_seconds // 60} minutes")
    return problems


def extract_audio(src, dest_wav):
    """Mono 16 kHz PCM WAV for transcription and mixing."""
    _run([ffmpeg(), "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dest_wav)])


SCENE_RE = re.compile(r"pts_time:([0-9.]+)")


def detect_shot_cuts(src, threshold="0.4"):
    """Times (ms) of visual shot cuts, from ffmpeg's scene-change score. Used only to place scene
    boundaries; no visual content is interpreted (visual context is not implemented)."""
    proc = subprocess.run(
        [ffmpeg(), "-v", "info", "-i", str(src), "-an", "-filter:v", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
        capture_output=True, text=True, timeout=600,
    )
    return [int(float(t) * 1000) for t in SCENE_RE.findall(proc.stderr or "")]


def render_scene_clip(src, start_ms, end_ms, out_mp4, *, speech_track=None):
    """Cut [start, end] from the source. If `speech_track` (a WAV aligned to the scene start) is given,
    mix it over the original audio ducked to 25 %; otherwise keep the original audio."""
    start, dur = f"{start_ms / 1000:.3f}", f"{(end_ms - start_ms) / 1000:.3f}"
    args = [ffmpeg(), "-y", "-v", "error", "-ss", start, "-t", dur, "-i", str(src)]
    if speech_track:
        args += ["-i", str(speech_track), "-filter_complex",
                 "[0:a]volume=0.25[bg];[bg][1:a]amix=inputs=2:duration=first:normalize=0[a]",
                 "-map", "0:v:0", "-map", "[a]"]
    else:
        args += ["-map", "0:v:0", "-map", "0:a:0"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out_mp4)]
    _run(args)


def build_speech_track(placements, total_ms, out_wav):
    """Place WAV files at offsets (ms) on a silent track of `total_ms`. placements: [(path, offset_ms, tempo)]."""
    if not placements:
        _run([ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-t", f"{total_ms / 1000:.3f}", "-i",
              "anullsrc=r=16000:cl=mono", "-c:a", "pcm_s16le", str(out_wav)])
        return
    args = [ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-t", f"{total_ms / 1000:.3f}", "-i", "anullsrc=r=16000:cl=mono"]
    filters = []
    labels = ["[0:a]"]
    for i, (path, offset, tempo) in enumerate(placements, start=1):
        args += ["-i", str(path)]
        chain = f"[{i}:a]aresample=16000"
        if tempo and abs(float(tempo) - 1.0) > 0.001:
            chain += f",atempo={float(tempo):.3f}"
        chain += f",adelay={int(offset)}:all=1[s{i}]"
        filters.append(chain)
        labels.append(f"[s{i}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0[out]")
    args += ["-filter_complex", ";".join(filters), "-map", "[out]", "-ac", "1", "-c:a", "pcm_s16le", str(out_wav)]
    _run(args)


# ISO 639-1 → ISO 639-2 codes for MP4 track tags (players show "Unknown" for "und"). ADR 0022.
ISO639_2 = {"ta": "tam", "en": "eng", "hi": "hin", "te": "tel", "kn": "kan", "ml": "mal", "bn": "ben", "mr": "mar",
            "gu": "guj", "pa": "pan", "ur": "urd", "or": "ori", "as": "asm", "es": "spa", "fr": "fra", "de": "deu"}


def language_tag(code):
    return ISO639_2.get((code or "").split("-")[0].lower(), "und")


def mux_final(src, speech_wav, subtitles_srt, out_mp4, *, target_language="", source_language=""):
    """Full localized video: original picture, original audio ducked under the speech track (if any),
    and a soft subtitle track. Tracks are tagged with their language (dubbed audio = target language,
    original audio = source language, subtitles = target language)."""
    args = [ffmpeg(), "-y", "-v", "error", "-i", str(src)]
    if speech_wav:
        args += ["-i", str(speech_wav)]
    args += ["-i", str(subtitles_srt)]
    sub_index = 2 if speech_wav else 1
    if speech_wav:
        args += ["-filter_complex", "[0:a]volume=0.25[bg];[bg][1:a]amix=inputs=2:duration=first:normalize=0[a]",
                 "-map", "0:v:0", "-map", "[a]"]
    else:
        args += ["-map", "0:v:0", "-map", "0:a:0"]
    audio_language = target_language if speech_wav else source_language
    args += ["-metadata:s:a:0", f"language={language_tag(audio_language)}",
             "-metadata:s:s:0", f"language={language_tag(target_language)}"]
    args += ["-map", f"{sub_index}:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text", "-movflags", "+faststart", str(out_mp4)]
    _run(args, timeout=1800)


def make_test_video(out_path, seconds=12, *, tone=True):
    """Generate a synthetic test video (colour bars + a tone, with a hard cut half-way). Used by tests
    and the demo fixture; contains no real person."""
    half = seconds / 2
    args = [ffmpeg(), "-y", "-v", "error",
            "-f", "lavfi", "-i", f"testsrc2=size=320x180:rate=15:duration={half}",
            "-f", "lavfi", "-i", f"smptebars=size=320x180:rate=15:duration={half}",
            "-f", "lavfi", "-i", f"sine=frequency=330:duration={seconds}" if tone else f"anullsrc=r=16000:cl=mono:d={seconds}",
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(out_path)]
    _run(args)
