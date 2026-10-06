"""The only way to write audit records (ADR 0001, ADR 0007).

`record()` must be called inside the transaction of the action it describes.
It locks the AuditChainHead row last, appends one record, and advances the head.
"""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from django.db import connection, transaction

from .models import AuditChainHead, AuditRecord

GENESIS_HASH = "0" * 64

# Detail keys that must never be stored (raw content). A defensive check, not a filter.
FORBIDDEN_DETAIL_KEYS = {"text", "transcript", "source_text", "subtitle_text", "speech_text", "audio"}


class AuditError(Exception):
    pass


def _normalise(value):
    """Make a value canonical-JSON safe: no floats, timestamps as ISO-8601 UTC."""
    if isinstance(value, float):
        raise AuditError("floats are not allowed in audit details; use strings or integers")
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, dict):
        return {str(k): _normalise(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise(v) for v in value]
    return value


def canonical_json(data):
    """Sorted keys, UTF-8, no whitespace (ADR 0007)."""
    return json.dumps(_normalise(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_payload(rec):
    """The fields covered by the hash, in a fixed shape."""
    return {
        "seq": rec.seq,
        "actor_id": rec.actor_id,
        "actor_label": rec.actor_label,
        "action": rec.action,
        "entity_type": rec.entity_type,
        "entity_id": rec.entity_id,
        "project_id": rec.project_id,
        "scene_id": rec.scene_id,
        "consent_version": rec.consent_version,
        "timestamp": rec.timestamp,
        "details": rec.details,
    }


def compute_hash(prev_hash, rec):
    return hashlib.sha256((prev_hash + canonical_json(record_payload(rec))).encode("utf-8")).hexdigest()


def _check_details(details):
    for key in details:
        if key in FORBIDDEN_DETAIL_KEYS:
            raise AuditError(f"audit details must not contain raw content ({key!r})")


def record(*, actor, action, entity, project_id=None, scene_id=None, consent_version="", details=None):
    """Append one audit record. `actor` is a User or None (system).

    `entity` is a model instance, or a (type, id) tuple.
    """
    if not connection.in_atomic_block:
        raise AuditError("audit.record() must run inside the action's transaction")
    details = _normalise(details or {})
    _check_details(details)
    if isinstance(entity, tuple):
        entity_type, entity_id = entity
    else:
        entity_type, entity_id = entity._meta.label, entity.pk
    head, _ = AuditChainHead.objects.select_for_update().get_or_create(pk=1)
    rec = AuditRecord(
        seq=head.seq + 1,
        actor=actor if getattr(actor, "pk", None) else None,
        actor_label=actor.get_username() if getattr(actor, "pk", None) else "system",
        action=action,
        entity_type=str(entity_type),
        entity_id=str(entity_id),
        project_id=project_id,
        scene_id=scene_id,
        consent_version=str(consent_version or ""),
        timestamp=datetime.now(timezone.utc),
        details=details,
        prev_hash=head.hash,
    )
    rec.hash = compute_hash(head.hash, rec)
    rec.save()
    head.seq = rec.seq
    head.hash = rec.hash
    head.save(update_fields=["seq", "hash"])
    return rec


def chain_head():
    head = AuditChainHead.objects.filter(pk=1).first()
    if head is None:
        return {"seq": 0, "hash": GENESIS_HASH}
    last = AuditRecord.objects.filter(seq=head.seq).first()
    return {"seq": head.seq, "hash": head.hash, "timestamp": last.timestamp if last else None}


def verify_chain():
    """Recompute the chain. Returns (ok, checked_count, first_bad_seq or None, message)."""
    prev = GENESIS_HASH
    expected_seq = 1
    count = 0
    for rec in AuditRecord.objects.order_by("seq").iterator():
        if rec.seq != expected_seq:
            return False, count, rec.seq, f"gap: expected seq {expected_seq}, found {rec.seq}"
        if rec.prev_hash != prev:
            return False, count, rec.seq, "prev_hash does not match the previous record"
        # Reload JSON exactly as stored, so verification does not depend on Python objects.
        if compute_hash(prev, rec) != rec.hash:
            return False, count, rec.seq, "hash mismatch (record content changed)"
        prev = rec.hash
        expected_seq += 1
        count += 1
    head = AuditChainHead.objects.filter(pk=1).first()
    if head and (head.seq != count or head.hash != prev):
        return False, count, None, "chain head does not match the last record"
    return True, count, None, "ok"


@transaction.atomic
def record_standalone(**kwargs):
    """For events with no surrounding action transaction (e.g. a refusal)."""
    return record(**kwargs)
