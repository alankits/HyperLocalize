"""Human-made transcript (not AI, not a mock).

The Media Operator uploads a verbatim transcript (SRT or WebVTT) with the video.
This is an IMPLEMENTATION CHOICE behind TranscriptionProvider: it lets the full
workflow run with real, human-authored source text before any ASR model is chosen
by the spike, and it is the honest source for the demo when no ASR runs.
"""
import re

from .base import TranscriptionProvider, TranscriptionResult, TranscriptSegment, Unavailable, register

TIME_RE = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")


def _ms(match):
    h, m, s, ms = match.groups()
    return ((int(h or 0) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def parse_subtitles(text):
    """Parse SRT or WebVTT cues into TranscriptSegments. Raises ValueError on bad input."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    segments = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.split("\n") if ln.strip()]
        timing_index = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if timing_index is None:
            continue  # WEBVTT header, NOTE blocks, or cue numbers alone
        left, right = lines[timing_index].split("-->", 1)
        start, end = TIME_RE.search(left), TIME_RE.search(right)
        if not start or not end:
            raise ValueError(f"bad cue timing: {lines[timing_index]!r}")
        body = " ".join(re.sub(r"<[^>]+>", "", ln).strip() for ln in lines[timing_index + 1 :]).strip()
        speaker = "Speaker 1"
        m = re.match(r"^\[?([A-Za-z][\w .-]{0,40})\]?:\s+(.*)$", body)
        if m and not m.group(1).lower().startswith("http"):
            speaker, body = m.group(1).strip(), m.group(2)
        if body:
            segments.append(TranscriptSegment(_ms(start), _ms(end), body, None, speaker))
    if not segments:
        raise ValueError("no cues found in the transcript file")
    segments.sort(key=lambda s: s.start_ms)
    for a, b in zip(segments, segments[1:]):
        if b.start_ms < a.end_ms:
            raise ValueError("transcript cues overlap; fix the timings")
    return segments


@register
class ManualTranscriptProvider(TranscriptionProvider):
    name = "manual_transcript"
    is_mock = False
    description = "Human-made transcript uploaded by the Media Operator"

    def transcribe(self, wav_path, language, *, video=None):
        from hyperlocalize.projects.storage import get_storage

        if video is None or not video.transcript_key:
            raise Unavailable("no human transcript was uploaded for this video")
        with get_storage().open(video.transcript_key) as f:
            text = f.read().decode("utf-8")
        return TranscriptionResult(parse_subtitles(text), language, model="human-transcript")
