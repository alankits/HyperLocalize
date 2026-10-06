"""Append-only, hash-chained audit records (ADR 0007).

Records are written only through `audit.services.record()`. PostgreSQL
triggers (migration 0002) reject UPDATE, DELETE and TRUNCATE on the table.
The chain is tamper-evident within the limits of ADR 0007's threat model;
it is not tamper-proof.
"""
from django.conf import settings
from django.db import models


class AuditChainHead(models.Model):
    """A single row that serialises appends. Always locked last (ADR 0003)."""

    seq = models.BigIntegerField(default=0)
    hash = models.CharField(max_length=64, default="0" * 64)

    class Meta:
        db_table = "audit_chain_head"


class AuditRecord(models.Model):
    seq = models.BigIntegerField(unique=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    # "system" for worker and management-command actions with no user.
    actor_label = models.CharField(max_length=150)
    action = models.CharField(max_length=64, db_index=True)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    project_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    scene_id = models.BigIntegerField(null=True, blank=True)
    consent_version = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField()
    # Identifiers and hashes only; never raw transcripts or audio (ADR 0007).
    details = models.JSONField(default=dict)
    prev_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)

    class Meta:
        db_table = "audit_record"
        ordering = ["seq"]

    def __str__(self):
        return f"#{self.seq} {self.action} {self.entity_type}:{self.entity_id}"
