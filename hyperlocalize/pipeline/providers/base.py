"""Provider interfaces, result types, the adapter registry and the provider chain (ADR 0005).

Each AI stage sits behind an interface so adapters can be swapped or mocked.
The adapter that actually ran is recorded on the output and shown to the reviewer.
Mock adapters are registered only when HYPERLOCALIZE_MODE is dev or test, and are
never part of a demo chain.
"""
from dataclasses import dataclass, field

from django.conf import settings


# --------------------------------------------------------------------------- errors

class ProviderError(Exception):
    """Base class. Non-transient unless a subclass says otherwise."""

    transient = False


class QuotaExhausted(ProviderError):
    """Free quota used up: try the next adapter in the chain."""


class RateLimited(ProviderError):
    transient = True


class Unavailable(ProviderError):
    """Adapter not configured, model missing, or service down: try the next adapter."""


class ProviderOutputInvalid(ProviderError):
    """The adapter answered, but not in the expected shape."""


class NoProviderAvailable(Exception):
    """Every adapter in the chain failed or none is registered for this mode."""


CHAIN_FALLTHROUGH = (QuotaExhausted, RateLimited, Unavailable, ProviderOutputInvalid)


# --------------------------------------------------------------------------- results

@dataclass
class TranscriptSegment:
    start_ms: int
    end_ms: int
    text: str
    confidence: str | None = None  # decimal string, or None if the adapter gives none
    speaker: str = "Speaker 1"


@dataclass
class TranscriptionResult:
    segments: list[TranscriptSegment]
    language: str
    model: str = ""


@dataclass
class SegmentContext:
    """One segment to localize, with the context the stage may use (Phase 0 §4.3)."""

    segment_id: int
    source_text: str
    duration_ms: int
    speaker: str
    previous_texts: list[str] = field(default_factory=list)
    next_texts: list[str] = field(default_factory=list)


@dataclass
class LocalizationRequest:
    source_language: str
    target_locale: str
    segments: list[SegmentContext]
    audience: dict  # locale, formality, reading_level, cultural_notes, unit_conversions
    glossary: list[dict]  # source_term, target_term, accepted_forms, do_not_translate
    instruction: str = ""  # reviewer's regeneration instruction, if any
    prompt_version: str = "loc-v1"

    @property
    def context_inputs(self):
        names = ["source_window", "speaker", "audience_profile", "timing_budget"]
        if self.glossary:
            names.append("glossary")
        if self.instruction:
            names.append("reviewer_instruction")
        return names


@dataclass
class LocalizedSegment:
    segment_id: int
    subtitle_text: str
    speech_text: str
    adaptation_type: str  # LITERAL / ADAPTED / LOCALISED / KEPT_ORIGINAL
    rationale: str = ""
    uncertainty_flags: list[str] = field(default_factory=list)


@dataclass
class LocalizationResult:
    segments: list[LocalizedSegment]
    model: str = ""
    uses_context: bool = True  # False for a context-free fallback (e.g. plain NMT)


@dataclass
class MeaningFlag:
    flag_type: str  # NEGATION, MEANING_REVERSAL, OMISSION, ADDITION, REGISTER
    explanation: str


@dataclass
class MeaningCheckResult:
    flags: list[MeaningFlag]
    model: str = ""


@dataclass
class SynthesisResult:
    wav_path: str
    duration_ms: int
    model: str = ""


# --------------------------------------------------------------------------- interfaces

class Provider:
    name = ""  # registry key, e.g. "mock_translation"
    stage = ""
    is_mock = False
    description = ""

    def available(self):
        """True if this adapter can run now (configured, model present)."""
        return True


class TranscriptionProvider(Provider):
    stage = "transcription"

    def transcribe(self, wav_path, language, *, video=None):
        raise NotImplementedError


class TranslationProvider(Provider):
    stage = "localization"

    def localize(self, request: LocalizationRequest) -> LocalizationResult:
        raise NotImplementedError


class MeaningCheckProvider(Provider):
    stage = "meaning_check"

    def check(self, source_text, target_text, source_language, target_locale) -> MeaningCheckResult:
        raise NotImplementedError


class SpeechSynthesisProvider(Provider):
    """Stock or identity-preserving speech. Identity use requires a ConsentCheck (ADR 0006).

    Runs inside the inference subprocess (ADR 0003), so `synthesize` receives plain data.
    """

    stage = "speech"
    supports_cloning = False

    def synthesize(self, text, language, out_path, *, voice=None, reference_clip=None, reference_text=None):
        raise NotImplementedError


# --------------------------------------------------------------------------- registry

_REGISTRY: dict[str, Provider] = {}


def register(provider_cls):
    instance = provider_cls()
    _REGISTRY[instance.name] = instance
    return provider_cls


def mocks_allowed():
    return settings.HYPERLOCALIZE_MODE in ("dev", "test")


def get_adapter(name):
    adapter = _REGISTRY.get(name)
    if adapter is None:
        return None
    if adapter.is_mock and not mocks_allowed():
        return None
    return adapter


def registered(stage=None):
    _load_adapters()
    return [a for a in _REGISTRY.values() if (stage is None or a.stage == stage) and (mocks_allowed() or not a.is_mock)]


DEFAULT_CHAINS = {
    # Candidate real adapters first (each disabled unless configured), mocks last in dev/test.
    "transcription": ["manual_transcript", "faster_whisper_transcription", "mock_transcription"],
    "localization": ["gemini_localization", "mock_localization"],
    "meaning_check": ["gemini_meaning_check", "mock_meaning_check"],
    "speech_stock": ["mock_stock_voice"],
    "speech_cloned": ["mock_cloned_voice"],
}


def _load_adapters():
    # Import adapter modules so their @register decorators run.
    from . import gemini, manual, mock, whisper  # noqa: F401


def chain_for(stage):
    """Ordered adapter names for a stage: the Administrator's ProviderConfig, else the default."""
    from hyperlocalize.pipeline.models import ProviderConfig

    _load_adapters()
    config = ProviderConfig.objects.filter(stage=stage).first()
    return list(config.adapters) if config and config.adapters else list(DEFAULT_CHAINS.get(stage, []))


@dataclass
class ChainOutcome:
    result: object
    adapter: Provider
    is_fallback: bool
    skipped: list[tuple[str, str]]  # (adapter name, reason)


def run_chain(stage, call, *, accept=None):
    """Try each adapter in order. `call(adapter)` returns the result.

    `accept(adapter)` may return a reason string to skip an adapter (e.g. a data-use rule).
    """
    skipped = []
    names = chain_for(stage)
    first = True
    for name in names:
        adapter = get_adapter(name)
        if adapter is None:
            skipped.append((name, "not registered in this mode"))
            first = False
            continue
        if not adapter.available():
            skipped.append((name, "not configured or unavailable"))
            first = False
            continue
        if accept:
            reason = accept(adapter)
            if reason:
                skipped.append((name, reason))
                first = False
                continue
        try:
            result = call(adapter)
        except CHAIN_FALLTHROUGH as exc:
            skipped.append((name, f"{type(exc).__name__}: {exc}"))
            first = False
            continue
        return ChainOutcome(result, adapter, not first, skipped)
    detail = "; ".join(f"{n}: {r}" for n, r in skipped) or "no adapters configured"
    raise NoProviderAvailable(f"No {stage} provider could run ({detail}).")
