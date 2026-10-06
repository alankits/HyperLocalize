"""Scene reviews, regeneration requests and approvals (ADR 0014, UC5, UC6)."""
from django.conf import settings
from django.db import models


class Review(models.Model):
    class Decision(models.TextChoices):
        ACCEPT = "ACCEPT"
        CHANGES_REQUESTED = "CHANGES_REQUESTED"

    scene = models.ForeignKey("localization.Scene", on_delete=models.CASCADE, related_name="reviews")
    localization = models.ForeignKey("localization.Localization", on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    decision = models.CharField(max_length=20, choices=Decision.choices)
    # MQM-style issues: [{"category": "accuracy", "severity": "major", "segment_id": 1}]
    issues = models.JSONField(default=list, blank=True)
    comment = models.TextField(blank=True)
    reviewed_versions = models.JSONField(default=dict)  # translation ids and render id seen by the reviewer
    created_at = models.DateTimeField(auto_now_add=True)


class RegenerationRequest(models.Model):
    class Target(models.TextChoices):
        SCRIPT = "SCRIPT"  # re-run localization (UC3) for the scene
        PREVIEW = "PREVIEW"  # re-run rendering (UC4) for the scene

    scene = models.ForeignKey("localization.Scene", on_delete=models.CASCADE, related_name="regenerations")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    target = models.CharField(max_length=8, choices=Target.choices, default=Target.SCRIPT)
    reason = models.CharField(max_length=300)
    instruction = models.TextField(blank=True)
    job = models.ForeignKey("pipeline.Job", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)


class Approval(models.Model):
    class Status(models.TextChoices):
        VALID = "VALID"
        INVALIDATED = "INVALIDATED"

    localization = models.ForeignKey("localization.Localization", on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    approved_at = models.DateTimeField(auto_now_add=True)
    # Exact SegmentTranslation, SynthesisedSegment and RenderedScene versions (immutable once VALID).
    snapshot = models.JSONField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.VALID)
    invalidated_reason = models.CharField(max_length=300, blank=True)
