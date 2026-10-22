"""Download local model weights once into HL_MODEL_DIR (never committed). Jobs never download."""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Download local model weights into HL_MODEL_DIR (default ~/.local/hl-dev/models)."

    def add_arguments(self, parser):
        parser.add_argument("--mms-tts", action="store_true", help="MMS-TTS Tamil stock voice (CC-BY-NC-4.0, ~280 MB)")

    def handle(self, *args, mms_tts=False, **options):
        if not mms_tts:
            raise CommandError("Choose a model, e.g. --mms-tts.")
        from huggingface_hub import snapshot_download

        from hyperlocalize.pipeline.providers import mms_tts as mms

        path = snapshot_download(mms.MODEL_ID, cache_dir=mms.model_dir())
        self.stdout.write(self.style.SUCCESS(f"{mms.MODEL_ID} ready at {path}"))
