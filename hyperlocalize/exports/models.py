"""Export packages and their evidence manifests (ADR 0014, UC6)."""
from django.db import models


class Export(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"  # build job queued or running
        ACTIVE = "ACTIVE"
        CONSENT_REVOKED = "CONSENT_REVOKED"
        PURGED = "PURGED"  # package file deleted after withdrawal (ADR 0020)
        FAILED = "FAILED"

    approval = models.ForeignKey("review.Approval", on_delete=models.PROTECT, related_name="exports")
    package_key = models.CharField(max_length=200, blank=True)
    package_sha256 = models.CharField(max_length=64, blank=True)
    manifest = models.JSONField(default=dict)
    manifest_sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
