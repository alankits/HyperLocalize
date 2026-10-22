"""Synthesised speech and rendered scene previews (ADR 0014, UC4)."""
from decimal import Decimal

from django.db import models

# Largest speed-up applied to synthesised speech (ADR 0022: 1.2×; was 1.15× in SPIKE_PLAN M5). Shared by the
# translator's length budget and the renderer.
MAX_TEMPO = Decimal("1.20")


class RenderingMode(models.TextChoices):
    # Resolved by the backend per speaker from the current consent state (ADR 0015).
    CLONED_VOICE = "CLONED_VOICE"
    STOCK_VOICE = "STOCK_VOICE"
    SUBTITLES_ONLY = "SUBTITLES_ONLY"


class ArtefactStatus(models.TextChoices):
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    PURGED = "PURGED"


class SynthesisedSegment(models.Model):
    class Runtime(models.TextChoices):
        LOCAL = "LOCAL"
        KAGGLE = "KAGGLE"  # MVP implementation value (ADR 0019); no remote runtime is built yet

    segment = models.ForeignKey("localization.Segment", on_delete=models.CASCADE, related_name="syntheses")
    localization = models.ForeignKey("localization.Localization", on_delete=models.CASCADE, related_name="+")
    translation = models.ForeignKey("localization.SegmentTranslation", on_delete=models.PROTECT, related_name="+")
    version = models.IntegerField()
    audio_key = models.CharField(max_length=200, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    duration_ms = models.IntegerField(default=0)
    rendering_mode = models.CharField(max_length=16, choices=RenderingMode.choices)
    consent = models.ForeignKey(
        "identity.Consent", null=True, blank=True, on_delete=models.PROTECT, related_name="synthesised_segments"
    )
    consent_version = models.IntegerField(null=True, blank=True)
    adapter = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    runtime = models.CharField(max_length=8, choices=Runtime.choices, default=Runtime.LOCAL)
    tempo = models.DecimalField(max_digits=4, decimal_places=3, default=1)
    is_fallback = models.BooleanField(default=False)
    is_mock = models.BooleanField(default=False)
    # ADR 0022: automatic intelligibility PROXY (faster-whisper back-transcription CER), not a listening test.
    # {"label", "cer", "heard", "model"}; empty when not computed (no Whisper, or a mock voice).
    intelligibility = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=ArtefactStatus.choices, default=ArtefactStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["segment", "localization", "version"], name="uniq_synth_version")
        ]


class RenderedScene(models.Model):
    scene = models.ForeignKey("localization.Scene", on_delete=models.CASCADE, related_name="renders")
    localization = models.ForeignKey("localization.Localization", on_delete=models.CASCADE, related_name="+")
    version = models.IntegerField()
    audio_key = models.CharField(max_length=200, blank=True)
    video_key = models.CharField(max_length=200, blank=True)
    subtitles_vtt = models.TextField(blank=True)
    synthesised_segments = models.ManyToManyField(SynthesisedSegment, blank=True, related_name="rendered_scenes")
    translation_ids = models.JSONField(default=list)  # exact SegmentTranslation versions rendered
    consent_versions = models.JSONField(default=list)  # [{"consent_id": .., "version": ..}]
    rendering_modes = models.JSONField(default=dict)  # speaker label → mode
    is_mock = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=ArtefactStatus.choices, default=ArtefactStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["scene", "localization", "version"], name="uniq_render_version")]
