"""Identity owners, versioned consent, voice profiles and offline copies
(ADR 0006, ADR 0014, ADR 0015, ADR 0020).

Only the `identity` app decides consent (ADR 0001). Consent rows are never
updated in place except for the explicitly defined status fields; every change
inserts a new version (ADR 0014 invariant 4).
"""
from django.conf import settings
from django.db import models


class Use(models.TextChoices):
    VOICE_SYNTHESIS = "voice_synthesis"
    REMOTE_VOICE_PROCESSING = "remote_voice_processing"
    EXTERNAL_TRANSCRIPTION = "external_transcription"


class Purpose(models.TextChoices):
    STANDARD = "STANDARD"
    DEMO_REHEARSAL = "DEMO_REHEARSAL"


class CopyKind(models.TextChoices):
    DEMO_SEED_REFERENCE = "DEMO_SEED_REFERENCE"
    DEMO_SEED_CLONED_AUDIO = "DEMO_SEED_CLONED_AUDIO"
    SCREEN_RECORDING = "SCREEN_RECORDING"


# Processors that receive the reference clip or produce cloned audio off the laptop
# (ADR 0020 §3). MVP: Kaggle only. Text-only processors are not in this set.
REMOTE_VOICE_PROCESSORS = {"kaggle"}


class IdentityOwner(models.Model):
    """A real person whose identity (in the MVP: voice) may be used. The lock row for consent."""

    name = models.CharField(max_length=200)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="identity_owner"
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawn_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    withdrawal_evidence = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.name


class Consent(models.Model):
    class Kind(models.TextChoices):
        PROJECT = "PROJECT"
        STANDING = "STANDING"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        REVOKED = "REVOKED"
        EXPIRED = "EXPIRED"

    class GrantReason(models.TextChoices):
        OWNER = "OWNER"  # granted by the owner from their own account
        DEMO_RESET = "DEMO_RESET"  # derived by demo_reset (ADR 0020); never wider than the parent

    identity_owner = models.ForeignKey(IdentityOwner, on_delete=models.PROTECT, related_name="consents")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    version = models.IntegerField()
    parent_consent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="derived"
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="consents"
    )
    uses = models.JSONField(default=list)
    permitted_purposes = models.JSONField(default=list, blank=True)  # STANDING only
    permitted_copy_kinds = models.JSONField(default=list, blank=True)  # STANDING only
    languages = models.JSONField(default=list)
    processors = models.JSONField(default=list, blank=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    evidence_ref = models.CharField(max_length=200)  # e.g. signed form ID and version (the form itself is not stored)
    grant_reason = models.CharField(max_length=12, choices=GrantReason.choices, default=GrantReason.OWNER)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["identity_owner", "kind", "project", "version"],
                name="uniq_consent_version",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=(models.Q(kind="STANDING", project__isnull=True) | models.Q(kind="PROJECT", project__isnull=False)),
                name="consent_kind_project",
            ),
        ]

    def __str__(self):
        scope = f"project {self.project_id}" if self.project_id else "standing"
        return f"Consent {self.identity_owner} {scope} v{self.version} {self.status}"


class VoiceProfile(models.Model):
    """Our stored, consented reference clip and transcript (ADR 0015). No provider-side clone."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        DELETED = "DELETED"

    identity_owner = models.ForeignKey(IdentityOwner, on_delete=models.PROTECT, related_name="voice_profiles")
    consent = models.ForeignKey(Consent, on_delete=models.PROTECT, related_name="voice_profiles")
    storage_key = models.CharField(max_length=200, blank=True)
    transcript = models.TextField()
    language = models.CharField(max_length=16)
    sha256 = models.CharField(max_length=64)
    duration_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)


class OfflineCopy(models.Model):
    """Identity files outside the normal artefact tables (ADR 0020 §4)."""

    class Status(models.TextChoices):
        PRESENT = "PRESENT"
        DELETION_PENDING = "DELETION_PENDING"
        DELETED = "DELETED"

    identity_owner = models.ForeignKey(IdentityOwner, on_delete=models.PROTECT, related_name="offline_copies")
    consent_version = models.ForeignKey(Consent, on_delete=models.PROTECT, related_name="offline_copies")
    kind = models.CharField(max_length=24, choices=CopyKind.choices)
    storage_key = models.CharField(max_length=200)
    language = models.CharField(max_length=16, blank=True)
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=18, choices=Status.choices, default=Status.PRESENT)
