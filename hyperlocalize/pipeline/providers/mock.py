"""MOCK adapters for development and tests only (ADR 0005; listed as stubs in docs/STATUS.md).

They are deterministic, call no model, and say so in every output:
- mock text starts with "[MOCK]";
- mock audio is an obvious tone, not speech;
- every artefact made from them is flagged is_mock, the UI shows a MOCK OUTPUT badge,
  and export is refused while any mock artefact is in the approved snapshot.
They are registered only when HYPERLOCALIZE_MODE is dev or test.
"""
import math
import os
import re
import struct
import time
import wave

from .base import (
    LocalizationResult,
    LocalizedSegment,
    MeaningCheckProvider,
    MeaningCheckResult,
    MeaningFlag,
    SpeechSynthesisProvider,
    SynthesisResult,
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptSegment,
    TranslationProvider,
    register,
)

MOCK_SEGMENT_MS = 4000
SAMPLE_RATE = 16000


def wav_duration_ms(path):
    with wave.open(str(path), "rb") as w:
        return int(w.getnframes() * 1000 / w.getframerate())


@register
class MockTranscriptionProvider(TranscriptionProvider):
    """MOCK: placeholder segments every 4 s; no speech recognition happens."""

    name = "mock_transcription"
    is_mock = True
    description = "MOCK placeholder transcript (no speech recognition)"

    def transcribe(self, wav_path, language, *, video=None):
        total = wav_duration_ms(wav_path)
        segments = []
        start = 0
        n = 1
        while start < total:
            end = min(start + MOCK_SEGMENT_MS - 500, total)
            if end - start >= 300:
                segments.append(TranscriptSegment(start, end, f"[MOCK] Transcript segment {n}.", None))
                n += 1
            start += MOCK_SEGMENT_MS
        return TranscriptionResult(segments, language, model="mock-v1")


@register
class MockTranslationProvider(TranslationProvider):
    """MOCK: copies the source, applies glossary target terms, keeps digits. Not a translation."""

    name = "mock_localization"
    requires_hosted_llm_permission = False  # local, no data leaves the laptop
    is_mock = True
    description = "MOCK localization (copies the source text; no model is called)"

    def localize(self, request):
        out = []
        for seg in request.segments:
            text = seg.source_text
            for term in request.glossary:
                if term.get("target_term") and not term.get("do_not_translate"):
                    text = re.sub(rf"(?i)\b{re.escape(term['source_term'])}\b", term["target_term"], text)
            rationale = "[MOCK] Deterministic placeholder; no model was called."
            if request.instruction:
                rationale += f" Reviewer instruction received ({len(request.instruction)} characters)."
            out.append(
                LocalizedSegment(
                    segment_id=seg.segment_id,
                    subtitle_text=f"[MOCK {request.target_locale}] {text}",
                    speech_text=f"[MOCK {request.target_locale}] {text}",
                    adaptation_type="LITERAL",
                    rationale=rationale,
                )
            )
        return LocalizationResult(out, model="mock-v1")


NEGATION_RE = re.compile(r"\b(not|never|no|don't|do not|doesn't|cannot|can't|avoid|stop)\b", re.I)


@register
class MockMeaningCheckProvider(MeaningCheckProvider):
    """MOCK: flags every source segment that contains a negation word, for the reviewer to check."""

    name = "mock_meaning_check"
    requires_hosted_llm_permission = False  # local, no data leaves the laptop
    is_mock = True
    description = "MOCK meaning check (keyword rule, not an AI model)"

    def check(self, source_text, target_text, source_language, target_locale):
        flags = []
        if NEGATION_RE.search(source_text):
            flags.append(MeaningFlag("NEGATION", "[MOCK] The source contains a negation; confirm the target keeps it."))
        return MeaningCheckResult(flags, model="mock-v1")


def _write_tone(path, duration_ms, freq):
    frames = int(SAMPLE_RATE * duration_ms / 1000)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        data = bytearray()
        for i in range(frames):
            # A beeping tone (on 200 ms, off 50 ms) so nobody mistakes it for speech.
            on = (i * 1000 // SAMPLE_RATE) % 250 < 200
            value = int(9000 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)) if on else 0
            data += struct.pack("<h", value)
        w.writeframes(bytes(data))


def _mock_duration(text):
    return max(400, min(15000, 55 * len(text)))


def _mock_delay():
    # Optional delay per segment, so a revocation can land mid-job in a demo or test.
    delay_ms = int(os.environ.get("HL_MOCK_SYNTH_DELAY_MS", "0") or 0)
    if delay_ms:
        time.sleep(delay_ms / 1000)


@register
class MockStockVoiceProvider(SpeechSynthesisProvider):
    """MOCK stock voice: a 440 Hz beeping tone, not speech."""

    name = "mock_stock_voice"
    stage = "speech_stock"
    is_mock = True
    description = "MOCK stock voice (tone, not speech)"

    def synthesize(self, text, language, out_path, *, voice=None, reference_clip=None, reference_text=None):
        _mock_delay()
        duration = _mock_duration(text)
        _write_tone(out_path, duration, 440)
        return SynthesisResult(str(out_path), duration, model="mock-tone-440")


@register
class MockClonedVoiceProvider(SpeechSynthesisProvider):
    """MOCK identity-preserving voice: a 660 Hz beeping tone. It reads the reference clip only to
    prove the clip was handed over under a consent check; it does not imitate anyone."""

    name = "mock_cloned_voice"
    stage = "speech_cloned"
    is_mock = True
    supports_cloning = True
    description = "MOCK cloned voice (tone, not speech; imitates no one)"

    def synthesize(self, text, language, out_path, *, voice=None, reference_clip=None, reference_text=None):
        if not reference_clip or not os.path.exists(reference_clip):
            raise FileNotFoundError("reference clip missing")
        _mock_delay()
        duration = _mock_duration(text)
        _write_tone(out_path, duration, 660)
        return SynthesisResult(str(out_path), duration, model="mock-tone-660")
