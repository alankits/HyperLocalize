"""Gemini adapters: a CANDIDATE provider, not a final choice (the spike decides, ADR 0016).

- Free tier only, on a Google project with no Cloud Billing (ADR 0005 zero-spend rule).
- Text only; audio is never sent.
- Skipped unless the project's data_classification is SCRIPTED_TEAM or PUBLISHED_PUBLIC with a recorded
  source and licence (ADR 0021), because free-tier content may be used for training and read by human
  reviewers (THIRD_PARTY_TERMS).
- Disabled when HL_GEMINI_API_KEY is empty.
Uses the public REST endpoint through the standard library (no SDK dependency).
"""
import json
import time
import urllib.error
import urllib.request

from django.conf import settings

from .base import (
    LocalizationResult,
    LocalizedSegment,
    MeaningCheckProvider,
    MeaningCheckResult,
    MeaningFlag,
    ProviderOutputInvalid,
    QuotaExhausted,
    RateLimited,
    TranslationProvider,
    Unavailable,
    register,
)

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 60
# A 429 that is not a daily quota is retried once, if Google's RetryInfo asks for a wait no longer
# than MAX_RETRY_WAIT_SECONDS and the call stays within RETRY_BUDGET_SECONDS overall. Anything else
# (a daily quota says hours) falls through to the next adapter in the chain (ADR 0005). A job
# cancellation is noticed at the next checkpoint, so a wait delays it by at most this long.
MAX_RETRY_WAIT_SECONDS = 20
RETRY_BUDGET_SECONDS = 75
ADAPTATION_TYPES = {"LITERAL", "ADAPTED", "LOCALISED", "KEPT_ORIGINAL"}
FLAG_TYPES = {"NEGATION", "MEANING_REVERSAL", "OMISSION", "ADDITION", "REGISTER"}
_sleep = time.sleep  # replaced in tests


def classify_429(body):
    """Return (exception class, seconds to wait or None) for a Gemini HTTP 429 body.

    Google's 429 message says "quota" for per-minute and per-day limits alike, so the message text
    cannot tell them apart. The QuotaFailure detail names the limit that was hit (a daily one has
    "PerDay" in its quotaId, seen live on 2026-10-12) and RetryInfo gives the wait, e.g. "46032s".
    An unreadable body is treated as a rate limit, without a retry.
    """
    try:
        details = json.loads(body)["error"].get("details") or []
        quota_ids = [v.get("quotaId", "") for d in details if str(d.get("@type", "")).endswith("QuotaFailure")
                     for v in d.get("violations") or []]
        delays = [d.get("retryDelay", "") for d in details if str(d.get("@type", "")).endswith("RetryInfo")]
    except (ValueError, KeyError, TypeError, AttributeError):
        return RateLimited, None
    wait = None
    if delays:
        try:
            wait = float(str(delays[0]).rstrip("s"))
        except ValueError:
            pass
    if any("PerDay" in q for q in quota_ids):
        return QuotaExhausted, wait
    return RateLimited, wait


def _post(prompt, *, opener=None):
    """Send one prompt and return the model's text. `opener` is injectable for tests."""
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT.format(model=settings.HL_GEMINI_MODEL),
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.HL_GEMINI_API_KEY},
        method="POST",
    )
    started = time.monotonic()
    for attempt in (1, 2):
        try:
            with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_SECONDS) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                error, wait = classify_429(exc.read().decode("utf-8", "replace"))
                if (error is RateLimited and attempt == 1 and wait is not None and wait <= MAX_RETRY_WAIT_SECONDS
                        and time.monotonic() - started + wait <= RETRY_BUDGET_SECONDS):
                    _sleep(wait)
                    continue
                kind = "daily quota used up" if error is QuotaExhausted else "rate limited"
                raise error(f"HTTP 429 from Gemini ({kind})") from None
            if exc.code >= 500:
                raise Unavailable(f"HTTP {exc.code} from Gemini") from None
            raise Unavailable(f"HTTP {exc.code} from Gemini (check the key and model name)") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise Unavailable(f"Gemini unreachable: {exc}") from None
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise ProviderOutputInvalid("Gemini response had no text") from None


class _GeminiBase:
    is_mock = False
    requires_hosted_llm_permission = True  # data-use rule (ADR 0005, amended by ADR 0021)

    def available(self):
        return bool(settings.HL_GEMINI_API_KEY)


def localization_prompt(request):
    segs = [
        {
            "id": s.segment_id,
            "speaker": s.speaker,
            "source": s.source_text,
            "max_spoken_seconds": round(s.duration_ms / 1000, 1),
            "previous": s.previous_texts,
            "next": s.next_texts,
        }
        for s in request.segments
    ]
    rules = [
        f"Localize each segment from {request.source_language} for the audience locale {request.target_locale}.",
        "Preserve the intended meaning exactly. Never drop or reverse a negation, warning or instruction.",
        "Write every number as digits (0-9) in subtitle_text. Keep units and their values unchanged unless "
        "the audience profile declares a conversion.",
        "Use the glossary target terms where the source term appears; keep do_not_translate terms unchanged.",
        "speech_text is what a text-to-speech voice reads aloud. Write it entirely in the target language's own "
        "script: numbers, units and dates as words; names and acronyms transliterated; no digits, Latin letters "
        "or symbols. It must say exactly what subtitle_text says.",
        "Fit the spoken length to max_spoken_seconds where possible; say so in uncertainty_flags if not.",
        "adaptation_type is one of LITERAL, ADAPTED, LOCALISED, KEPT_ORIGINAL. rationale is one short sentence "
        "for a human reviewer explaining any adaptation.",
        'Return only JSON: {"segments": [{"id", "subtitle_text", "speech_text", "adaptation_type", '
        '"rationale", "uncertainty_flags"}]} with one entry per input segment.',
    ]
    return json.dumps(
        {
            "task": "context-aware video localization draft (a human will review every segment)",
            "prompt_version": request.prompt_version,
            "rules": rules,
            "audience_profile": request.audience,
            "glossary": request.glossary,
            "reviewer_instruction": request.instruction or None,
            "segments": segs,
        },
        ensure_ascii=False,
    )


@register
class GeminiLocalizationProvider(_GeminiBase, TranslationProvider):
    name = "gemini_localization"
    description = "Gemini (free tier) context-aware localization: CANDIDATE, not final"

    def localize(self, request, *, opener=None):
        raw = _post(localization_prompt(request), opener=opener)
        try:
            data = json.loads(raw)
            items = {int(item["id"]): item for item in data["segments"]}
        except (ValueError, KeyError, TypeError):
            raise ProviderOutputInvalid("Gemini did not return the expected JSON") from None
        out = []
        for seg in request.segments:
            item = items.get(seg.segment_id)
            if not item or not str(item.get("subtitle_text", "")).strip():
                raise ProviderOutputInvalid(f"missing output for segment {seg.segment_id}")
            adaptation = str(item.get("adaptation_type", "LITERAL")).upper()
            out.append(
                LocalizedSegment(
                    segment_id=seg.segment_id,
                    subtitle_text=str(item["subtitle_text"]).strip(),
                    speech_text=str(item.get("speech_text") or item["subtitle_text"]).strip(),
                    adaptation_type=adaptation if adaptation in ADAPTATION_TYPES else "LITERAL",
                    rationale=str(item.get("rationale", ""))[:500],
                    uncertainty_flags=[str(f)[:200] for f in (item.get("uncertainty_flags") or [])][:5],
                )
            )
        return LocalizationResult(out, model=settings.HL_GEMINI_MODEL)


def meaning_prompt(source_text, target_text, source_language, target_locale):
    return json.dumps(
        {
            "task": "Compare a source segment with its localized draft and flag possible meaning problems "
            "for a human reviewer. You are an aid, not a verifier.",
            "flag_types": sorted(FLAG_TYPES),
            "source_language": source_language,
            "target_locale": target_locale,
            "source": source_text,
            "draft": target_text,
            "output": 'Return only JSON: {"flags": [{"type": "...", "explanation": "one sentence"}]}; '
            "an empty list if nothing looks wrong.",
        },
        ensure_ascii=False,
    )


@register
class GeminiMeaningCheckProvider(_GeminiBase, MeaningCheckProvider):
    name = "gemini_meaning_check"
    description = "Gemini (free tier) meaning-reversal flags: CANDIDATE, advisory only"

    def check(self, source_text, target_text, source_language, target_locale, *, opener=None):
        raw = _post(meaning_prompt(source_text, target_text, source_language, target_locale), opener=opener)
        try:
            data = json.loads(raw)
            flags = [
                MeaningFlag(str(f["type"]).upper(), str(f.get("explanation", ""))[:300])
                for f in data.get("flags", [])
                if str(f.get("type", "")).upper() in FLAG_TYPES
            ]
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ProviderOutputInvalid("Gemini did not return the expected JSON") from None
        return MeaningCheckResult(flags, model=settings.HL_GEMINI_MODEL)
