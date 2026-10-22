"""MMS-TTS Tamil on local CPU: the STOCK-VOICE adapter (ADR 0021; ADR 0018's stock-voice chain).

- Meta's `facebook/mms-tts-tam` (VITS, 36.3M parameters, one fixed voice). Licence CC-BY-NC-4.0:
  academic, non-commercial use only (THIRD_PARTY_TERMS). It never imitates a person, so it is the
  STOCK_VOICE tier only; the identity-preserving (CLONED_VOICE) tier stays pending (ADR 0018).
- Runs inside the inference subprocess (ADR 0005), one model loaded at a time. Text never leaves the laptop.
- The model's vocabulary is Tamil letters, space and apostrophe. Characters outside it would be dropped
  silently, so a number or an English word could vanish from the speech. The adapter therefore REFUSES text
  containing digits, Latin letters or other unpronounceable characters, and the reviewer fixes the speech
  script. Punctuation only becomes a word break.
- Fixed seed, so the same text gives the same audio (VITS samples noise).
Optional dependency: `pip install -r requirements-ml.txt` plus the CPU build of torch (see the README).
Weights download once to HL_MODEL_DIR with `python manage.py download_models --mms-tts`; never committed.
"""
import os
import re
import unicodedata

from .base import SpeechSynthesisProvider, SynthesisResult, Unavailable, register

MODEL_ID = "facebook/mms-tts-tam"
SEED = 1234
PUNCTUATION_RE = re.compile(r"[.,!?;:\"“”‘’()\[\]{}…–—\-/|]+")
# Documented approximation (ADR 0021): the aytham ஃ is missing from the MMS vocabulary. It only modifies the
# sound of the next consonant (e.g. "எஃப்" = "f"), carries no number or negation, and is read without it
# ("எப்"). Every other unknown character is refused, never dropped.
APPROXIMATIONS = {"ஃ": ""}
_MODEL = {}


def model_dir():
    return os.path.expanduser(os.environ.get("HL_MODEL_DIR", "~/.local/hl-dev/models"))


def _snapshot_path():
    """The downloaded snapshot directory, or None (no surprise downloads during a job)."""
    root = os.path.join(model_dir(), "models--" + MODEL_ID.replace("/", "--"), "snapshots")
    if not os.path.isdir(root):
        return None
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.exists(os.path.join(path, "config.json")) and os.path.exists(os.path.join(path, "vocab.json")):
            return path
    return None


class UnspeakableText(ValueError):
    """The speech script contains characters the voice cannot pronounce. The message names the kind of
    character and how many, never the text itself (job errors are shown and logged)."""


def prepare_text(text, vocab):
    """Return the text the model will read, or raise UnspeakableText. Pure function (unit-tested)."""
    text = unicodedata.normalize("NFC", text or "").strip()
    text = PUNCTUATION_RE.sub(" ", text)
    for char, replacement in APPROXIMATIONS.items():
        if char not in vocab:
            text = text.replace(char, replacement)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise UnspeakableText("the speech script is empty")
    digits = sum(c.isdigit() for c in text)
    latin = sum(("a" <= c.lower() <= "z") for c in text)
    other = sum(1 for c in text if not c.isdigit() and not ("a" <= c.lower() <= "z") and c not in vocab)
    problems = []
    if digits:
        problems.append(f"{digits} digit(s): write numbers as Tamil words")
    if latin:
        problems.append(f"{latin} Latin letter(s): write names and acronyms in Tamil script")
    if other:
        problems.append(f"{other} other character(s) the Tamil voice cannot pronounce")
    if problems:
        raise UnspeakableText("speech script cannot be read aloud: " + "; ".join(problems))
    return text


_VOCAB = {}


def vocabulary():
    """The model's character vocabulary from vocab.json, or None if the model is not downloaded."""
    import json

    path = _snapshot_path()
    if path is None:
        return None
    if path not in _VOCAB:
        with open(os.path.join(path, "vocab.json"), encoding="utf-8") as f:
            _VOCAB.clear()
            _VOCAB[path] = set(json.load(f))
    return _VOCAB[path]


def speakability_problem(text):
    """None if MMS-TTS can read the text; otherwise the refusal message (used as a review-time hard check)."""
    vocab = vocabulary()
    if vocab is None:
        return None
    try:
        prepare_text(text, vocab)
    except UnspeakableText as exc:
        return str(exc)
    return None


def synthesize_in_child(text, out_path):
    """Executed in the inference subprocess."""
    import wave

    import numpy as np
    import torch
    from transformers import AutoTokenizer, VitsModel

    path = _snapshot_path()
    if path is None:
        raise Unavailable("MMS-TTS Tamil model is not downloaded")
    if MODEL_ID not in _MODEL:
        _MODEL.clear()  # one model at a time (laptop RAM, ADR 0005)
        _MODEL[MODEL_ID] = (AutoTokenizer.from_pretrained(path), VitsModel.from_pretrained(path).eval())
    tokenizer, model = _MODEL[MODEL_ID]
    spoken = prepare_text(text, set(tokenizer.get_vocab()))
    inputs = tokenizer(spoken, return_tensors="pt")
    torch.manual_seed(SEED)
    with torch.no_grad():
        waveform = model(**inputs).waveform[0].numpy()
    rate = model.config.sampling_rate
    pcm = (np.clip(waveform, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return int(len(pcm) * 1000 / rate)


@register
class MmsTtsTamilStockVoiceProvider(SpeechSynthesisProvider):
    name = "mms_tts_tamil"
    stage = "speech_stock"
    is_mock = False
    supports_cloning = False  # stock voice only (ADR 0021 condition 2)
    description = "MMS-TTS Tamil stock voice on local CPU (CC-BY-NC-4.0; non-commercial)"

    def available(self):
        """Ready only if torch and transformers are installed and the model is downloaded.
        Disabled in test mode unless HL_TEST_MMS=1."""
        from django.conf import settings

        if settings.HYPERLOCALIZE_MODE == "test" and os.environ.get("HL_TEST_MMS") != "1":
            return False
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            return False
        return _snapshot_path() is not None

    def synthesize(self, text, language, out_path, *, voice=None, reference_clip=None, reference_text=None):
        if reference_clip is not None:
            raise Unavailable("MMS-TTS is a stock voice; it never receives a reference clip")
        if (language or "").split("-")[0] != "ta":
            raise Unavailable("MMS-TTS Tamil speaks Tamil only")
        duration_ms = synthesize_in_child(text, out_path)
        return SynthesisResult(str(out_path), duration_ms, model=f"{MODEL_ID} (seed {SEED})")
