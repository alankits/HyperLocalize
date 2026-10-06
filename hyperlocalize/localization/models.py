"""Scenes, segments, localized drafts and critical-content checks (ADR 0014, ADR 0008)."""
from django.conf import settings
from django.db import models


class Localization(models.Model):
    """One target locale of a project (one per project in the MVP, Q14)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        IN_REVIEW = "IN_REVIEW"
        APPROVED = "APPROVED"
        EXPORTED = "EXPORTED"

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="localizations")
    target_locale = models.CharField(max_length=16)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    def __str__(self):
        return f"{self.project} → {self.target_locale}"


class Scene(models.Model):
    """A contiguous time range that groups segments: the unit of rendering, review and
    regeneration (Phase 0 C6)."""

    class Status(models.TextChoices):
        PENDING = "PENDING"
        TRANSLATED = "TRANSLATED"
        IN_REVIEW = "IN_REVIEW"
        CHANGES_REQUESTED = "CHANGES_REQUESTED"
        REGENERATING = "REGENERATING"
        ACCEPTED = "ACCEPTED"
        NEEDS_REGENERATION = "NEEDS_REGENERATION"

    video = models.ForeignKey("projects.Video", on_delete=models.CASCADE, related_name="scenes")
    index = models.IntegerField()
    start_ms = models.IntegerField()
    end_ms = models.IntegerField()
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["index"]
        constraints = [models.UniqueConstraint(fields=["video", "index"], name="uniq_scene_index")]

    def __str__(self):
        return f"Scene {self.index + 1}"


class Segment(models.Model):
    """One speech utterance: the unit of translation and text editing."""

    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name="segments")
    speaker_track = models.ForeignKey(
        "projects.SpeakerTrack", null=True, blank=True, on_delete=models.SET_NULL, related_name="segments"
    )
    index = models.IntegerField()  # position within the video
    start_ms = models.IntegerField()
    end_ms = models.IntegerField()
    source_text = models.TextField()
    asr_confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)

    class Meta:
        ordering = ["index"]

    @property
    def duration_ms(self):
        return self.end_ms - self.start_ms


class SegmentTranslation(models.Model):
    """An append-only version of a segment's localized text. Never updated in place."""

    class Origin(models.TextChoices):
        AI = "AI"
        HUMAN = "HUMAN"

    class AdaptationType(models.TextChoices):
        LITERAL = "LITERAL"
        ADAPTED = "ADAPTED"
        LOCALISED = "LOCALISED"
        KEPT_ORIGINAL = "KEPT_ORIGINAL"

    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="translations")
    localization = models.ForeignKey(Localization, on_delete=models.CASCADE, related_name="translations")
    version = models.IntegerField()
    subtitle_text = models.TextField()
    speech_text = models.TextField()
    adaptation_type = models.CharField(max_length=16, choices=AdaptationType.choices)
    rationale = models.TextField(blank=True)  # the model's stated reason, not a faithful explanation
    uncertainty_flags = models.JSONField(default=list, blank=True)
    origin = models.CharField(max_length=8, choices=Origin.choices)
    adapter = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=32, blank=True)
    is_fallback = models.BooleanField(default=False)
    is_mock = models.BooleanField(default=False)
    context_inputs = models.JSONField(default=list, blank=True)  # names of the context inputs used
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["segment__index", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["segment", "localization", "version"], name="uniq_translation_version")
        ]


class CheckResult(models.Model):
    class Kind(models.TextChoices):
        HARD = "HARD"  # rule-based; blocks approval (ADR 0008)
        AI_FLAG = "AI_FLAG"  # advisory; needs acknowledgement

    class Status(models.TextChoices):
        PASS = "PASS"
        FAIL = "FAIL"
        UNVERIFIABLE = "UNVERIFIABLE"
        FLAGGED = "FLAGGED"
        CHECK_UNAVAILABLE = "CHECK_UNAVAILABLE"

    class Resolution(models.TextChoices):
        FIXED = "FIXED"
        OVERRIDDEN = "OVERRIDDEN"
        ACKNOWLEDGED = "ACKNOWLEDGED"

    segment_translation = models.ForeignKey(SegmentTranslation, on_delete=models.CASCADE, related_name="checks")
    kind = models.CharField(max_length=8, choices=Kind.choices)
    check_type = models.CharField(max_length=32)
    status = models.CharField(max_length=20, choices=Status.choices)
    detail = models.JSONField(default=dict)
    resolution = models.CharField(max_length=16, choices=Resolution.choices, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    reason = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_blocking(self):
        """Unresolved results that block approval (ADR 0014 invariant 5)."""
        if self.resolution:
            return False
        if self.kind == self.Kind.HARD:
            return self.status in (self.Status.FAIL, self.Status.UNVERIFIABLE)
        return self.status in (self.Status.FLAGGED, self.Status.CHECK_UNAVAILABLE)
