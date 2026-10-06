"""faster-whisper on local CPU: a CANDIDATE transcription adapter (ADR 0017; the spike chooses the model
size and whether it stays primary). Source audio never leaves the laptop. MIT licence.

Runs inside the inference subprocess (ADR 0005), one model loaded at a time. Voice-activity filtering
is on, because Whisper is known to invent text on non-speech audio. No speaker diarization: every
segment is labelled "Speaker 1" and speakers are corrected by a person (UC2).
Optional dependency: `pip install -r requirements-ml.txt`. Model weights download once to
HL_MODEL_DIR (default ~/.local/hl-dev/models); they are never committed.
"""
import os

from .base import TranscriptionProvider, TranscriptionResult, TranscriptSegment, Unavailable, register

_MODEL = {}


def model_name():
    return os.environ.get("HL_WHISPER_MODEL", "small")


def model_dir():
    return os.path.expanduser(os.environ.get("HL_MODEL_DIR", "~/.local/hl-dev/models"))


def transcribe_in_child(wav_path, language):
    """Executed in the inference subprocess."""
    from faster_whisper import WhisperModel

    name = model_name()
    if name not in _MODEL:
        _MODEL.clear()  # one model at a time (laptop RAM, ADR 0005)
        _MODEL[name] = WhisperModel(name, device="cpu", compute_type="int8", download_root=model_dir())
    # Our own 16 kHz mono PCM WAV is passed as an array, which also avoids an incompatibility between
    # faster-whisper 1.2.1's file decoder and PyAV 19.
    import wave

    import numpy as np

    with wave.open(str(wav_path), "rb") as w:
        if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError("expected 16 kHz mono 16-bit WAV")
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    segments, info = _MODEL[name].transcribe(audio, language=language or None, vad_filter=True, beam_size=5)
    out = []
    for s in segments:
        text = s.text.strip()
        if text:
            confidence = max(0.0, min(1.0, 1.0 - float(s.no_speech_prob)))
            out.append({"start_ms": int(s.start * 1000), "end_ms": int(s.end * 1000), "text": text,
                        "confidence": f"{confidence:.3f}"})
    return {"segments": out, "model": f"faster-whisper-{name}-int8", "language": info.language}


@register
class FasterWhisperTranscriptionProvider(TranscriptionProvider):
    name = "faster_whisper_transcription"
    is_mock = False
    description = "faster-whisper on local CPU (CANDIDATE; audio stays on the laptop)"

    def available(self):
        """Ready only if the package is installed and the model is already downloaded (no surprise downloads
        during a job). Disabled in test mode unless HL_TEST_WHISPER=1."""
        from django.conf import settings

        if settings.HYPERLOCALIZE_MODE == "test" and os.environ.get("HL_TEST_WHISPER") != "1":
            return False
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return False
        root = model_dir()
        return os.path.isdir(root) and any(f"faster-whisper-{model_name()}" in d for d in os.listdir(root))

    def transcribe(self, wav_path, language, *, video=None):
        from hyperlocalize.pipeline.inference import InferenceError, InferenceProcess

        proc = InferenceProcess()
        try:
            result = proc.call({"op": "transcribe", "wav_path": str(wav_path), "language": language}, timeout=3600)
        except InferenceError as exc:
            raise Unavailable(f"faster-whisper failed: {exc}") from None
        finally:
            proc.kill()
        segments = [TranscriptSegment(s["start_ms"], s["end_ms"], s["text"], s["confidence"]) for s in result["segments"]]
        if not segments:
            raise Unavailable("no speech was detected in the audio")
        return TranscriptionResult(segments, result.get("language") or language, model=result["model"])
