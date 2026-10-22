"""Projects, audience context, glossary, source video and speakers (ADR 0014)."""
from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        # Coarse lifecycle only; workflow progress is shown from the Localization and Scene states.
        ACTIVE = "ACTIVE"
        ARCHIVED = "ARCHIVED"

    class DataClassification(models.TextChoices):
        # MVP implementation value (ADR 0005): decides whether a free-tier hosted LLM may receive text.
        SCRIPTED_TEAM = "SCRIPTED_TEAM", "Scripted, team-authored content"
        PERSONAL = "PERSONAL", "May contain personal data"
        # ADR 0021: already-published content whose licence permits reuse (e.g. public domain, CC BY).
        # Requires source_url and source_licence; both are carried into the export evidence.
        PUBLISHED_PUBLIC = "PUBLISHED_PUBLIC", "Published public content (licence permits reuse)"

    # Classifications whose text a free-tier hosted LLM may receive (ADR 0005 as amended by ADR 0021).
    HOSTED_LLM_ALLOWED = (DataClassification.SCRIPTED_TEAM, DataClassification.PUBLISHED_PUBLIC)

    name = models.CharField(max_length=200)
    source_language = models.CharField(max_length=16, default="en")  # ISO code; MVP: en
    domain = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    data_classification = models.CharField(
        max_length=16, choices=DataClassification.choices, default=DataClassification.PERSONAL
    )
    allow_external_audio = models.BooleanField(default=False)  # CP0, ADR 0006
    # Provenance of PUBLISHED_PUBLIC content (ADR 0021). Recorded by the creator; not verified by the system.
    source_url = models.URLField(max_length=500, blank=True)
    source_licence = models.CharField(max_length=300, blank=True)  # licence or reuse permission, e.g. "CC BY 3.0"
    source_attribution = models.CharField(max_length=300, blank=True)  # credit line required by some licences
    # Set to DEMO_REHEARSAL only by demo_reset (ADR 0020 §2); never by a form or the UI.
    purpose = models.CharField(max_length=16, default="STANDARD", editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AudienceProfile(models.Model):
    """Target-audience context passed to the localization stage (ADR 0016, Phase 0 §4)."""

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="audience")
    locale = models.CharField(max_length=16)  # BCP-47 code; MVP: ta-IN
    formality = models.CharField(max_length=32, default="neutral")
    reading_level = models.CharField(max_length=32, default="general")
    # Declared unit conversions, e.g. [{"from": "oz", "to": "ml"}] (ADR 0008).
    unit_conversions = models.JSONField(default=list, blank=True)
    cultural_notes = models.TextField(blank=True)


class GlossaryTerm(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="glossary")
    source_term = models.CharField(max_length=200)
    target_term = models.CharField(max_length=200, blank=True)
    # Accepted inflected forms (ADR 0008); filled in by a rater who reads the target language.
    accepted_forms = models.JSONField(default=list, blank=True)
    do_not_translate = models.BooleanField(default=False)
    note = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.source_term


class Video(models.Model):
    class Status(models.TextChoices):
        VALIDATED = "VALIDATED"
        ANALYZING = "ANALYZING"
        ANALYZED = "ANALYZED"
        FAILED = "FAILED"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="videos")
    original_name = models.CharField(max_length=255)  # display only; never used in a path
    storage_key = models.CharField(max_length=200)
    audio_key = models.CharField(max_length=200, blank=True)  # extracted mono WAV
    transcript_key = models.CharField(max_length=200, blank=True)  # optional human transcript (SRT/VTT)
    sha256 = models.CharField(max_length=64)
    duration_ms = models.IntegerField()
    container = models.CharField(max_length=64)
    codecs = models.JSONField(default=dict)
    size = models.BigIntegerField()
    has_video_stream = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.VALIDATED)
    # Provenance of the transcript (recorded on every provider call, ADR 0005).
    transcript_adapter = models.CharField(max_length=100, blank=True)
    transcript_model = models.CharField(max_length=100, blank=True)
    transcript_is_mock = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)


class SpeakerTrack(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="speakers")
    label = models.CharField(max_length=100)
    identity_owner = models.ForeignKey(
        "identity.IdentityOwner", null=True, blank=True, on_delete=models.SET_NULL, related_name="speaker_tracks"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return self.label
