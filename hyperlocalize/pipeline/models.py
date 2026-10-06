"""Hand-written Postgres job queue (ADR 0003) and provider configuration (ADR 0005, UC8)."""
from django.db import models


class Lane(models.TextChoices):
    DEFAULT = "default"
    SYNTHESIS = "synthesis"


class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        DISPATCHED = "DISPATCHED"  # remote batch submitted; not used until a remote runtime exists
        SUCCEEDED = "SUCCEEDED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    type = models.CharField(max_length=40, db_index=True)
    lane = models.CharField(max_length=16, choices=Lane.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED, db_index=True)
    cancel_requested = models.BooleanField(default=False)
    cancel_reason = models.CharField(max_length=64, blank=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    run_after = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    remote_ref = models.CharField(max_length=200, blank=True)
    error = models.TextField(blank=True)
    consent_versions = models.JSONField(default=list, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    progress = models.CharField(max_length=200, blank=True)
    # Targets (all nullable).
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    video = models.ForeignKey("projects.Video", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    scene = models.ForeignKey("localization.Scene", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    localization = models.ForeignKey(
        "localization.Localization", null=True, blank=True, on_delete=models.CASCADE, related_name="+"
    )
    identity_owner = models.ForeignKey(
        "identity.IdentityOwner", null=True, blank=True, on_delete=models.CASCADE, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["lane", "status", "run_after"])]

    def __str__(self):
        return f"Job {self.pk} {self.type} {self.status}"

    @property
    def is_active(self):
        return self.status in (self.Status.QUEUED, self.Status.RUNNING, self.Status.DISPATCHED)


class ProviderConfig(models.Model):
    """Ordered adapter chain per pipeline stage, set by the Administrator (ADR 0005)."""

    stage = models.CharField(max_length=32, unique=True)
    adapters = models.JSONField(default=list)  # ordered adapter names
    updated_at = models.DateTimeField(auto_now=True)


class ProviderUsage(models.Model):
    """Free-quota consumption ledger (ADR 0005)."""

    adapter = models.CharField(max_length=100, db_index=True)
    stage = models.CharField(max_length=32)
    units = models.IntegerField(default=0)
    unit_type = models.CharField(max_length=32)  # requests, tokens, audio_seconds
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
