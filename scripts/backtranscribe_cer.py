"""Voice-intelligibility PROXY for one export (ADR 0021).

Each synthesised Tamil line in the approved snapshot is transcribed back with faster-whisper `small`
(language forced to Tamil), and the character error rate (CER) against the speech script it was asked
to say is computed. Pessimistic: Whisper small's own Tamil errors are included. This is NOT a listening
test and NOT a naturalness score.

Usage (dev stack, faster-whisper installed and its model downloaded):
  python scripts/backtranscribe_cer.py <export_id>
"""
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import wave

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hyperlocalize.settings")
import django  # noqa: E402

django.setup()
import numpy as np  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402

from hyperlocalize import media_tools  # noqa: E402
from hyperlocalize.exports.models import Export  # noqa: E402
from hyperlocalize.pipeline.providers.whisper import model_dir  # noqa: E402
from hyperlocalize.projects.storage import get_storage  # noqa: E402
from hyperlocalize.rendering.models import SynthesisedSegment  # noqa: E402


def normalise(text):
    """Compare letters only: drop punctuation and spaces, use one Unicode form."""
    return re.sub(r"\s+", "", re.sub(r"[^\w\s]", " ", unicodedata.normalize("NFC", text)))


def cer(reference, hypothesis):
    """Levenshtein distance between the character strings, divided by the reference length."""
    r, h = normalise(reference), normalise(hypothesis)
    row = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        diagonal, row[0] = row[0], i
        for j in range(1, len(h) + 1):
            diagonal, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, diagonal + (r[i - 1] != h[j - 1]))
    return row[len(h)] / max(1, len(r)), len(r)


def read_wav_16k(path, tmp):
    subprocess.run([media_tools.ffmpeg(), "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", tmp], check=True)
    with wave.open(tmp) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def main(export_id):
    export = Export.objects.get(pk=export_id)
    ids = [i for scene in export.approval.snapshot["scenes"] for i in scene["synthesised_segment_ids"]]
    model = WhisperModel("small", device="cpu", compute_type="int8", download_root=model_dir())
    storage = get_storage()
    errors = characters = 0
    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "line.wav")
        for syn in (SynthesisedSegment.objects.filter(pk__in=ids)
                    .select_related("segment", "translation").order_by("segment__start_ms")):
            segments, _ = model.transcribe(read_wav_16k(storage.local_path(syn.audio_key), tmp),
                                           language="ta", beam_size=5, vad_filter=False)
            heard = " ".join(s.text.strip() for s in segments)
            rate, n = cer(syn.translation.speech_text, heard)
            errors += rate * n
            characters += n
            print(f"line {syn.segment.index + 1:2d}  CER {rate:4.2f}\n  said : {syn.translation.speech_text}\n  heard: {heard}")
    print(f"OVERALL CER {errors / max(1, characters):.2f} over {characters} characters")


if __name__ == "__main__":
    main(int(sys.argv[1]))
