"""Consent gate, grants, revocation and withdrawal (ADR 0006 as amended by ADR 0020).

Only this module decides consent (ADR 0001). Every change inserts a new Consent
version under the IdentityOwner row lock (ADR 0006 §4), which is the first lock
in the global order (ADR 0003). Every grant, revocation and withdrawal writes an
audit record in the same transaction (ADR 0007).
"""
from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from hyperlocalize.audit import services as audit

from .models import REMOTE_VOICE_PROCESSORS, Consent, CopyKind, IdentityOwner, OfflineCopy, Purpose, Use


class ConsentDenied(PermissionDenied):
    def __init__(self, reason, message=None):
        super().__init__(message or f"Consent check failed: {reason}")
        self.reason = reason


@dataclass(frozen=True)
class ConsentCheck:
    """Proof that the gate passed. Identity-using methods require one (ADR 0005)."""

    consent_id: int
    version: int
    identity_owner_id: int
    project_id: int
    use: str
    language: str


# --------------------------------------------------------------------------- reading

def latest_project_consent(owner, project):
    return Consent.objects.filter(identity_owner=owner, kind=Consent.Kind.PROJECT, project=project).order_by("-version").first()


def latest_standing(owner):
    return Consent.objects.filter(identity_owner=owner, kind=Consent.Kind.STANDING).order_by("-version").first()


def purposes_needed(project):
    """A STANDARD project needs STANDARD; a DEMO_REHEARSAL project needs both (ADR 0020 §1)."""
    if project.purpose == Purpose.DEMO_REHEARSAL:
        return {Purpose.STANDARD, Purpose.DEMO_REHEARSAL}
    return {Purpose.STANDARD}


def _within(child, parent):
    return (
        set(child.uses) <= set(parent.uses)
        and set(child.languages) <= set(parent.languages)
        and set(child.processors) <= set(parent.processors)
        and child.expires_at <= parent.expires_at
    )


def evaluate(owner, use, project, language, job=None, now=None):
    """Return (ConsentCheck, None) if identity use is allowed, else (None, reason). No locks taken."""
    now = now or timezone.now()
    owner = IdentityOwner.objects.get(pk=owner.pk)
    if owner.withdrawn_at:
        return None, "WITHDRAWN"
    pc = latest_project_consent(owner, project)
    if pc is None:
        return None, "NO_CONSENT"
    if pc.status != Consent.Status.ACTIVE:
        return None, f"CONSENT_{pc.status}"
    if pc.expires_at <= now:
        return None, "CONSENT_EXPIRED"
    if use not in pc.uses:
        return None, "USE_NOT_GRANTED"
    if language not in pc.languages:
        return None, "LANGUAGE_NOT_GRANTED"
    if pc.parent_consent_id is None:
        return None, "NO_STANDING_PARENT"
    st = latest_standing(owner)
    if st is None:
        return None, "NO_STANDING_CONSENT"
    if st.status != Consent.Status.ACTIVE or st.expires_at <= now:
        return None, "STANDING_CONSENT_INACTIVE"
    if not purposes_needed(project) <= set(st.permitted_purposes):
        return None, "PURPOSE_NOT_PERMITTED"
    if not _within(pc, st):
        return None, "NARROWED_BY_STANDING_CONSENT"
    if use == Use.REMOTE_VOICE_PROCESSING and not (set(pc.processors) & REMOTE_VOICE_PROCESSORS):
        return None, "NO_REMOTE_PROCESSOR"
    if job is not None and type(job).objects.filter(pk=job.pk, cancel_requested=True).exists():
        return None, "JOB_CANCEL_REQUESTED"
    return ConsentCheck(pc.pk, pc.version, owner.pk, project.pk, use, language), None


def require_active_consent(owner, use, project, language, job=None, *, actor=None, checkpoint="CP1"):
    """The one consent gate (ADR 0006 §1). Raises ConsentDenied; audits a denial at CP1."""
    check, reason = evaluate(owner, use, project, language, job)
    if check is None:
        if checkpoint == "CP1":
            with transaction.atomic():
                audit.record(
                    actor=actor,
                    action="CONSENT_DENIED",
                    entity=("identity.IdentityOwner", owner.pk),
                    project_id=project.pk,
                    details={"use": use, "language": language, "reason": reason, "checkpoint": checkpoint},
                )
        raise ConsentDenied(reason)
    return check


def lock_owner(owner_id):
    """Lock the IdentityOwner row (first in the lock order). Call inside a transaction."""
    return IdentityOwner.objects.select_for_update().get(pk=owner_id)


def locked_save_allowed(check, project, job=None):
    """CP5/CP7/CP9 (ADR 0006 §4, ADR 0020 §1): with the owner row LOCKED by the caller, the
    latest project version must still be the job's version and pass the full gate."""
    current, _reason = evaluate(IdentityOwner(pk=check.identity_owner_id), check.use, project, check.language, job)
    return current is not None and current.consent_id == check.consent_id


# --------------------------------------------------------------------------- granting

def _next_version(owner, kind, project=None):
    agg = Consent.objects.filter(identity_owner=owner, kind=kind, project=project).aggregate(m=Max("version"))
    return (agg["m"] or 0) + 1


def _require_owner_user(actor, owner):
    if owner.user_id is None or actor.pk != owner.user_id:
        # ADR 0011: only the identity owner grants; the Administrator cannot grant on anyone's behalf.
        raise PermissionDenied("Only the identity owner can grant or widen their own consent.")


def _clean_list(values, allowed=None):
    out = sorted({str(v) for v in values if str(v).strip()})
    if allowed is not None:
        bad = set(out) - set(allowed)
        if bad:
            raise ValidationError(f"unknown values: {', '.join(sorted(bad))}")
    return out


@transaction.atomic
def grant_standing_consent(actor, owner, *, uses, permitted_purposes, permitted_copy_kinds, languages,
                           processors, expires_at, evidence_ref):
    """The owner's standing consent (ADR 0020 §1). Widening needs a new signed form ID."""
    owner = lock_owner(owner.pk)
    _require_owner_user(actor, owner)
    if owner.withdrawn_at:
        raise ConsentDenied("WITHDRAWN", "Withdrawal is final; a returning speaker needs a new identity record.")
    if not evidence_ref.strip():
        raise ValidationError("evidence (the signed form ID and version) is required")
    if expires_at <= timezone.now():
        raise ValidationError("expiry must be in the future")
    new = dict(
        uses=_clean_list(uses, Use.values),
        permitted_purposes=_clean_list(permitted_purposes, Purpose.values),
        permitted_copy_kinds=_clean_list(permitted_copy_kinds, CopyKind.values),
        languages=_clean_list(languages),
        processors=_clean_list(processors),
    )
    previous = latest_standing(owner)
    if previous is not None and previous.status == Consent.Status.ACTIVE:
        wider = any(set(new[f]) - set(getattr(previous, f)) for f in new) or expires_at > previous.expires_at
        if wider and evidence_ref.strip() == previous.evidence_ref:
            raise ValidationError("Widening a standing consent needs a new signed form ID as evidence.")
    consent = Consent.objects.create(
        identity_owner=owner, kind=Consent.Kind.STANDING, version=_next_version(owner, Consent.Kind.STANDING),
        expires_at=expires_at, evidence_ref=evidence_ref.strip(), granted_by=actor, **new,
    )
    audit.record(actor=actor, action="CONSENT_GRANTED", entity=consent, consent_version=f"{consent.pk}:v{consent.version}",
                 details={"kind": "STANDING", "evidence_ref": consent.evidence_ref, **new,
                          "expires_at": consent.expires_at})
    return consent


@transaction.atomic
def grant_project_consent(actor, owner, project, *, uses, languages, processors, expires_at,
                          reason=Consent.GrantReason.OWNER):
    """A project-scoped consent, derived from (and never wider than) the latest standing consent."""
    owner = lock_owner(owner.pk)
    if reason == Consent.GrantReason.OWNER:
        _require_owner_user(actor, owner)
    if owner.withdrawn_at:
        raise ConsentDenied("WITHDRAWN")
    st = latest_standing(owner)
    if st is None or st.status != Consent.Status.ACTIVE or st.expires_at <= timezone.now():
        raise ConsentDenied("NO_STANDING_CONSENT", "An active standing consent is needed first.")
    if not purposes_needed(project) <= set(st.permitted_purposes):
        raise ConsentDenied("PURPOSE_NOT_PERMITTED", "The standing consent does not permit this kind of project.")
    pc = Consent(
        identity_owner=owner, kind=Consent.Kind.PROJECT, project=project, parent_consent=st,
        uses=_clean_list(uses, Use.values), languages=_clean_list(languages), processors=_clean_list(processors),
        expires_at=expires_at, evidence_ref=st.evidence_ref, grant_reason=reason,
        granted_by=actor if reason == Consent.GrantReason.OWNER else None,
    )
    if not pc.uses:
        raise ValidationError("at least one use is required")
    if not _within(pc, st):
        raise ConsentDenied("WIDER_THAN_STANDING", "A project consent cannot be wider than the standing consent.")
    pc.version = _next_version(owner, Consent.Kind.PROJECT, project)
    pc.save()
    details = {"kind": "PROJECT", "uses": pc.uses, "languages": pc.languages, "processors": pc.processors,
               "expires_at": pc.expires_at, "parent_consent_id": st.pk, "reason": reason}
    if reason == Consent.GrantReason.DEMO_RESET:
        details["triggered_by"] = actor.get_username() if actor else "system"
    audit.record(actor=actor if reason == Consent.GrantReason.OWNER else None, action="CONSENT_GRANTED", entity=pc,
                 project_id=project.pk, consent_version=f"{pc.pk}:v{pc.version}", details=details)
    return pc


# --------------------------------------------------------------------------- revoking

def _new_project_version(pc, *, uses, languages, processors, expires_at, actor, revoke):
    v = Consent.objects.create(
        identity_owner=pc.identity_owner, kind=Consent.Kind.PROJECT, project=pc.project,
        version=pc.version + 1, parent_consent=pc.parent_consent, uses=uses, languages=languages,
        processors=processors, expires_at=expires_at, evidence_ref=pc.evidence_ref, grant_reason=pc.grant_reason,
        granted_by=pc.granted_by,
        status=Consent.Status.REVOKED if revoke else Consent.Status.ACTIVE,
        revoked_at=timezone.now() if revoke else None, revoked_by=actor if revoke else None,
    )
    return v


def _cascade(owner, project, actor, reason, *, identity_removed):
    """ADR 0006 §5 (amended): affects only this owner's artefacts in this project."""
    from hyperlocalize.pipeline import jobs as job_services
    from hyperlocalize.rendering import services as rendering
    from hyperlocalize.review import services as review

    for job in job_services.active_jobs(identity_owner=owner, project=project):
        job_services.request_cancel(job, "CONSENT_REVOKED", actor)
    if not identity_removed:
        return []
    affected = rendering.quarantine_identity_artefacts(owner, project)
    review.on_identity_revoked(project, affected, reason=reason)
    job_services.enqueue("purge_identity_data", identity_owner=owner, project=project,
                         payload={"reason": reason})
    return affected


def _apply_project_narrowing(pc, *, uses, languages, processors, expires_at, actor, reason):
    """Insert the narrowed (or REVOKED) project version and run the cascade if identity use ended."""
    revoke = not uses
    new = _new_project_version(pc, uses=uses, languages=languages, processors=processors,
                               expires_at=expires_at, actor=actor, revoke=revoke)
    removed = {
        "uses": sorted(set(pc.uses) - set(uses)),
        "languages": sorted(set(pc.languages) - set(languages)),
        "processors": sorted(set(pc.processors) - set(processors)),
    }
    removed = {k: v for k, v in removed.items() if v}
    identity_removed = revoke or Use.VOICE_SYNTHESIS in removed.get("uses", []) or bool(removed.get("languages"))
    affected = _cascade(pc.identity_owner, pc.project, actor, reason, identity_removed=identity_removed)
    audit.record(actor=actor, action="CONSENT_REVOKED", entity=new, project_id=pc.project_id,
                 consent_version=f"{new.pk}:v{new.version}",
                 details={"kind": "PROJECT", "removed": removed, "status": new.status, "reason": reason,
                          "affected_scenes": [s for s in affected]})
    return new


@transaction.atomic
def revoke_project_consent(actor, owner, project, uses=None):
    """The owner revokes some or all uses in one project (UC7). Real, unless the project is a
    DEMO_REHEARSAL project, where it is a demonstration (ADR 0020 §5)."""
    owner = lock_owner(owner.pk)
    _require_owner_user(actor, owner)
    pc = latest_project_consent(owner, project)
    if pc is None or pc.status != Consent.Status.ACTIVE:
        raise ValidationError("There is no active consent to revoke in this project.")
    keep = [] if uses is None else [u for u in pc.uses if u not in set(uses)]
    reason = "DEMO_REVOCATION" if project.purpose == Purpose.DEMO_REHEARSAL else "OWNER_REVOCATION"
    return _apply_project_narrowing(pc, uses=keep, languages=pc.languages, processors=pc.processors,
                                    expires_at=pc.expires_at, actor=actor, reason=reason)


def _require_owner_or_recorded_request(actor, owner, request_ref):
    if owner.user_id and actor.pk == owner.user_id:
        return
    if getattr(actor, "is_administrator", False) and request_ref.strip():
        return  # records a decision the owner made through the §8 channel; never widens
    raise PermissionDenied("Only the owner, or an Administrator recording the owner's request, can do this.")


@transaction.atomic
def narrow_standing_consent(actor, owner, *, remove=None, expires_at=None, request_ref="", withdraw=False,
                            reason="OWNER_NARROWING"):
    """The single narrowing path (ADR 0020 §5): removing uses, purposes, copy kinds, languages or
    processors, an earlier expiry, or a full withdrawal."""
    owner = lock_owner(owner.pk)
    if reason != "EXPIRED":
        _require_owner_or_recorded_request(actor, owner, request_ref)
    st = latest_standing(owner)
    if st is None:
        raise ValidationError("There is no standing consent.")
    remove = {k: set(v) for k, v in (remove or {}).items()}
    fields = ["uses", "permitted_purposes", "permitted_copy_kinds", "languages", "processors"]
    unknown = set(remove) - set(fields)
    if unknown:
        raise ValidationError(f"cannot narrow {', '.join(sorted(unknown))}")
    new_values = {f: sorted(set(getattr(st, f)) - remove.get(f, set())) for f in fields}
    new_expiry = min(st.expires_at, expires_at) if expires_at else st.expires_at
    revoke = withdraw or reason == "EXPIRED" or not new_values["uses"]
    if revoke:
        new_values = {f: [] for f in fields}
    new = Consent.objects.create(
        identity_owner=owner, kind=Consent.Kind.STANDING, version=st.version + 1, expires_at=new_expiry,
        evidence_ref=st.evidence_ref, granted_by=st.granted_by,
        status=(Consent.Status.EXPIRED if reason == "EXPIRED" else Consent.Status.REVOKED) if revoke else Consent.Status.ACTIVE,
        revoked_at=timezone.now() if revoke else None, revoked_by=actor if revoke and getattr(actor, "pk", None) else None,
        **new_values,
    )
    removed = {f: sorted(set(getattr(st, f)) - set(new_values[f])) for f in fields}
    removed = {k: v for k, v in removed.items() if v}
    if new_expiry != st.expires_at:
        removed["expires_at"] = {"old": st.expires_at, "new": new_expiry}

    # Step 2: every project scope that no longer passes is narrowed or revoked (with its cascade).
    revoked_versions = []
    project_ids = (Consent.objects.filter(identity_owner=owner, kind=Consent.Kind.PROJECT)
                   .values_list("project_id", flat=True).distinct())
    for project_id in project_ids:
        pc = Consent.objects.filter(identity_owner=owner, kind=Consent.Kind.PROJECT, project_id=project_id).order_by("-version").first()
        if pc.status != Consent.Status.ACTIVE:
            continue
        purpose_ok = (not revoke) and purposes_needed(pc.project) <= set(new.permitted_purposes)
        uses = [u for u in pc.uses if u in new.uses] if purpose_ok else []
        languages = [lang for lang in pc.languages if lang in new.languages]
        processors = [p for p in pc.processors if p in new.processors]
        if not languages:
            uses = []
        exp = min(pc.expires_at, new.expires_at)
        if (uses, languages, processors, exp) == (pc.uses, pc.languages, pc.processors, pc.expires_at):
            continue
        v = _apply_project_narrowing(pc, uses=uses, languages=languages, processors=processors, expires_at=exp,
                                     actor=actor, reason=reason)
        revoked_versions.append(f"{v.pk}:v{v.version}")

    # Step 3: offline copies for what was removed.
    _mark_offline_copies(owner, st, new, revoke)

    audit.record(actor=actor, action="CONSENT_EXPIRED" if reason == "EXPIRED" else "CONSENT_REVOKED", entity=new,
                 consent_version=f"{new.pk}:v{new.version}",
                 details={"kind": "STANDING", "removed": removed, "status": new.status, "reason": reason,
                          "request_ref": request_ref, "project_versions": revoked_versions})
    if withdraw:
        owner.withdrawn_at = timezone.now()
        owner.withdrawn_by = actor
        owner.withdrawal_evidence = request_ref or "owner, in the app"
        owner.save(update_fields=["withdrawn_at", "withdrawn_by", "withdrawal_evidence"])
        audit.record(actor=actor, action="IDENTITY_WITHDRAWN", entity=owner, consent_version=f"{new.pk}:v{new.version}",
                     details={"revoked_versions": revoked_versions, "request_ref": request_ref})
    if revoke or removed:
        from hyperlocalize.pipeline import jobs as job_services

        job_services.enqueue("purge_identity_data", identity_owner=owner, payload={"reason": reason, "offline": True})
    return new


def _mark_offline_copies(owner, old, new, revoke):
    qs = OfflineCopy.objects.filter(identity_owner=owner, status=OfflineCopy.Status.PRESENT)
    if revoke or Use.VOICE_SYNTHESIS not in new.uses:
        targets = qs
    else:
        ids = set()
        for kind in set(old.permitted_copy_kinds) - set(new.permitted_copy_kinds):
            ids |= set(qs.filter(kind=kind).values_list("id", flat=True))
        if not {Purpose.STANDARD, Purpose.DEMO_REHEARSAL} <= set(new.permitted_purposes):
            ids |= set(qs.filter(kind__in=[CopyKind.DEMO_SEED_REFERENCE, CopyKind.DEMO_SEED_CLONED_AUDIO]).values_list("id", flat=True))
        for lang in set(old.languages) - set(new.languages):
            ids |= set(qs.filter(language=lang).values_list("id", flat=True))
        targets = qs.filter(id__in=ids)
    targets.update(status=OfflineCopy.Status.DELETION_PENDING)


def withdraw(actor, owner, request_ref=""):
    """Owner-level withdrawal: final, cannot be undone (ADR 0020 §5)."""
    return narrow_standing_consent(actor, owner, withdraw=True, request_ref=request_ref, reason="WITHDRAWAL")


def expire_due(now=None):
    """Expiry sweep (ADR 0006 as amended): expired standing consents run the narrowing path;
    expired project consents run the cascade. Returns the number of scopes processed."""
    now = now or timezone.now()
    count = 0
    for owner in IdentityOwner.objects.filter(withdrawn_at__isnull=True):
        st = latest_standing(owner)
        if st and st.status == Consent.Status.ACTIVE and st.expires_at <= now:
            narrow_standing_consent(None, owner, reason="EXPIRED")
            count += 1
            continue
        project_ids = (Consent.objects.filter(identity_owner=owner, kind=Consent.Kind.PROJECT)
                       .values_list("project_id", flat=True).distinct())
        for pid in project_ids:
            with transaction.atomic():
                lock_owner(owner.pk)
                pc = Consent.objects.filter(identity_owner=owner, kind=Consent.Kind.PROJECT, project_id=pid).order_by("-version").first()
                if pc.status == Consent.Status.ACTIVE and pc.expires_at <= now:
                    _apply_project_narrowing(pc, uses=[], languages=pc.languages, processors=pc.processors,
                                             expires_at=pc.expires_at, actor=None, reason="EXPIRED")
                    count += 1
    return count


def consent_summary(owner, project):
    """For the UI: the current state of this owner's consent in a project."""
    pc = latest_project_consent(owner, project)
    st = latest_standing(owner)
    return {"project": pc, "standing": st, "withdrawn": bool(owner.withdrawn_at)}


def is_future(dt):
    return isinstance(dt, datetime) and dt > timezone.now()


def create_voice_profile(actor, owner, project, uploaded_audio, *, transcript, language):
    """The identity owner uploads their own reference clip for a project they consented to.
    CP1: the gate must pass for voice_synthesis before anything is stored."""
    import os
    import tempfile

    from django.conf import settings

    from hyperlocalize import media_tools
    from hyperlocalize.projects.storage import get_storage

    from .models import VoiceProfile

    _require_owner_user(actor, owner)
    check = require_active_consent(owner, Use.VOICE_SYNTHESIS, project, language, actor=actor)
    if not transcript.strip():
        raise ValidationError("The exact transcript of the reference clip is required.")
    tmp_dir = settings.HL_MEDIA_ROOT / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, raw = tempfile.mkstemp(dir=str(tmp_dir))
    with os.fdopen(fd, "wb") as f:
        size = 0
        for chunk in uploaded_audio.chunks():
            size += len(chunk)
            if size > 20 * 1024 * 1024:
                os.unlink(raw)
                raise ValidationError("The reference clip is too large (20 MB maximum).")
            f.write(chunk)
    wav = raw + ".wav"
    try:
        try:
            info = media_tools.probe(raw)
            if not info["audio_codec"] or not (3000 <= info["duration_ms"] <= 30000):
                raise ValidationError("The reference clip must be 3–30 seconds of audio.")
            media_tools.extract_audio(raw, wav)
        except media_tools.MediaError:
            raise ValidationError("The reference clip is not readable audio.") from None
        storage = get_storage()
        with transaction.atomic():
            lock_owner(owner.pk)
            if not locked_save_allowed(check, project):
                raise ConsentDenied("CONSENT_CHANGED")
            key, sha = storage.save_file(wav, ".wav")
            profile = VoiceProfile.objects.create(identity_owner=owner, consent_id=check.consent_id, storage_key=key,
                                                  transcript=transcript.strip(), language=language, sha256=sha,
                                                  duration_ms=info["duration_ms"])
            audit.record(actor=actor, action="VOICE_PROFILE_CREATED", entity=profile, project_id=project.pk,
                         consent_version=f"{check.consent_id}:v{check.version}",
                         details={"sha256": sha, "duration_ms": info["duration_ms"], "language": language})
        return profile
    finally:
        for p in (raw, wav):
            if os.path.exists(p):
                os.unlink(p)
