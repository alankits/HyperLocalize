"""UC5 Review and Regenerate a Scene; UC6 approval gate (ADR 0008, ADR 0011, ADR 0014).

Human review is mandatory: there is no automatic acceptance or approval anywhere.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from hyperlocalize.accounts.models import Policy, Role
from hyperlocalize.accounts.permissions import require_role
from hyperlocalize.audit import services as audit
from hyperlocalize.identity import services as consent
from hyperlocalize.identity.models import Consent, Use
from hyperlocalize.localization import services as loc_services
from hyperlocalize.localization.models import Localization, Scene, Segment, SegmentTranslation
from hyperlocalize.pipeline import jobs

from .models import Approval, RegenerationRequest, Review


class ApprovalBlocked(ValidationError):
    def __init__(self, reasons):
        super().__init__("Approval is blocked: " + " ".join(reasons))
        self.reasons = reasons


def _render_state(scene, localization):
    from hyperlocalize.rendering import services as rendering

    render = rendering.latest_render(scene, localization)
    return render, rendering.render_is_current(render, localization, scene)


@transaction.atomic
def accept_scene(actor, scene, *, comment="", issues=()):
    localization = loc_services.require_reviewable(actor, scene)
    scene = Scene.objects.select_for_update().get(pk=scene.pk)
    if scene.status != Scene.Status.IN_REVIEW:
        raise ValidationError(f"Only a scene in review can be accepted (this one is {scene.get_status_display()}).")
    blocking = loc_services.blocking_checks(localization, [scene])
    if blocking:
        raise ValidationError(f"Resolve the {len(blocking)} open check(s) in this scene first.")
    render, current = _render_state(scene, localization)
    if not current:
        raise ValidationError("The preview is out of date or missing. Regenerate the preview first.")
    latest = loc_services.latest_translations(localization, list(scene.segments.all()))
    Review.objects.create(scene=scene, localization=localization, reviewer=actor, decision=Review.Decision.ACCEPT,
                          issues=list(issues), comment=comment,
                          reviewed_versions={"translations": sorted(t.pk for t in latest.values()), "render": render.pk})
    scene.status = Scene.Status.ACCEPTED
    scene.save(update_fields=["status"])
    audit.record(actor=actor, action="SCENE_ACCEPTED", entity=scene, project_id=localization.project_id, scene_id=scene.pk,
                 details={"render_id": render.pk, "issues": len(issues)})
    return scene


def request_changes(actor, scene, *, target, reason, instruction=""):
    """Reviewer asks for this scene only to be regenerated: SCRIPT (re-localize with an instruction,
    UC3) or PREVIEW (re-render, UC4). Other scenes are untouched."""
    localization = loc_services.require_reviewable(actor, scene)
    if target not in RegenerationRequest.Target.values:
        raise ValidationError("Choose what to regenerate.")
    if not reason.strip():
        raise ValidationError("Give a reason for the regeneration.")
    with transaction.atomic():
        Localization.objects.select_for_update().get(pk=localization.pk)  # lock order: Localization → Scene → Job
        scene = Scene.objects.select_for_update().get(pk=scene.pk)
        if scene.status in (Scene.Status.PENDING, Scene.Status.REGENERATING):
            raise ValidationError("This scene is still being generated.")
        Review.objects.create(scene=scene, localization=localization, reviewer=actor,
                              decision=Review.Decision.CHANGES_REQUESTED, comment=reason.strip())
        scene.status = Scene.Status.CHANGES_REQUESTED
        scene.save(update_fields=["status"])
        if target == RegenerationRequest.Target.SCRIPT:
            job = jobs.enqueue("localize", actor=actor, project=localization.project, localization=localization,
                               scene=scene, payload={"instruction": instruction.strip()[:2000], "regeneration": True})
        else:
            from hyperlocalize.rendering import services as rendering

            job = rendering.enqueue_render(scene, localization, actor=actor, reason="regeneration requested")
        req = RegenerationRequest.objects.create(scene=scene, requested_by=actor, target=target, reason=reason.strip()[:300],
                                                 instruction=instruction.strip(), job=job)
        audit.record(actor=actor, action="REGENERATION_REQUESTED", entity=req, project_id=localization.project_id,
                     scene_id=scene.pk, details={"target": target, "job_id": job.pk, "has_instruction": bool(instruction.strip())})
        invalidate_if_approved(localization, reason=f"regeneration requested for scene {scene.pk}")
    return req


def approval_problems(actor, localization):
    """Every reason approval would be refused right now (empty list = approvable)."""
    project = localization.project
    problems = []
    scenes = list(Scene.objects.filter(video__project=project).order_by("index"))
    if not scenes:
        return ["There are no scenes yet."]
    not_accepted = [s for s in scenes if s.status != Scene.Status.ACCEPTED]
    if not_accepted:
        problems.append(f"{len(not_accepted)} scene(s) are not accepted by a reviewer.")
    blocking = loc_services.blocking_checks(localization)
    if blocking:
        problems.append(f"{len(blocking)} blocking check(s) are unresolved.")
    unchecked = loc_services.missing_meaning_checks(localization)
    if unchecked:
        problems.append(f"{len(unchecked)} line(s) have no meaning check yet: use 'Retry translation and meaning checks'.")
    stale = [s for s in scenes if not _render_state(s, localization)[1]]
    if stale:
        problems.append(f"{len(stale)} scene preview(s) are missing or out of date.")
    # CP8: every consent version used must still be the latest and pass the full gate.
    language = localization.target_locale.split("-")[0]
    for c in _consent_versions_in(localization, scenes):
        cons = Consent.objects.select_related("identity_owner").get(pk=c["consent_id"])
        check, reason = consent.evaluate(cons.identity_owner, Use.VOICE_SYNTHESIS, project, language)
        if check is None:
            # Identifier only: names never go into the append-only log (review #11).
            problems.append(f"Consent for identity owner #{cons.identity_owner_id} is no longer valid ({reason}).")
    if Policy.get("separation_of_duties") and actor is not None:
        editors = set(_last_editors(localization, scenes))
        if actor.pk in editors:
            problems.append("Separation of duties: you edited a segment in this version, so another manager must approve.")
    return problems


def _consent_versions_in(localization, scenes):
    out = []
    for s in scenes:
        render, _ = _render_state(s, localization)
        if render:
            out.extend(render.consent_versions)
    return out


def _last_editors(localization, scenes):
    latest = loc_services.latest_translations(localization, Segment.objects.filter(scene__in=scenes))
    return [t.created_by_id for t in latest.values() if t.origin == SegmentTranslation.Origin.HUMAN and t.created_by_id]


def approve(actor, localization):
    """The approval gate (UC6). Freezes an immutable snapshot of the exact versions."""
    require_role(actor, localization.project, Role.LOCALIZATION_MANAGER)
    with transaction.atomic():
        from hyperlocalize.identity.models import IdentityOwner

        scenes = list(Scene.objects.filter(video__project=localization.project).order_by("index"))
        owner_ids = sorted({Consent.objects.get(pk=c["consent_id"]).identity_owner_id
                            for c in _consent_versions_in(localization, scenes)})
        for oid in owner_ids:
            IdentityOwner.objects.select_for_update().get(pk=oid)  # lock order: owners first
        localization = Localization.objects.select_for_update().get(pk=localization.pk)
        if localization.status not in (Localization.Status.IN_REVIEW, Localization.Status.DRAFT):
            raise ValidationError(f"This localization is already {localization.get_status_display()}.")
        problems = approval_problems(actor, localization)
        if not problems:
            approval = _create_approval(actor, localization, scenes)
    if problems:
        # A refusal has no action transaction to share, so it is recorded in its own (ADR 0020 §7 pattern).
        audit.record_standalone(actor=actor, action="APPROVAL_REFUSED", entity=localization,
                                project_id=localization.project_id, details={"reasons": problems})
        raise ApprovalBlocked(problems)
    return approval


def _create_approval(actor, localization, scenes):
    snapshot = {"scenes": []}
    for s in scenes:
        render, _ = _render_state(s, localization)
        latest = loc_services.latest_translations(localization, list(s.segments.all()))
        snapshot["scenes"].append({
            "scene_id": s.pk, "render_id": render.pk,
            "translation_ids": sorted(t.pk for t in latest.values()),
            "synthesised_segment_ids": sorted(render.synthesised_segments.values_list("pk", flat=True)),
            "consent_versions": render.consent_versions,
        })
    approval = Approval.objects.create(localization=localization, approver=actor, snapshot=snapshot)
    localization.status = Localization.Status.APPROVED
    localization.save(update_fields=["status"])
    audit.record(actor=actor, action="APPROVED", entity=approval, project_id=localization.project_id,
                 consent_version=",".join(f"{c['consent_id']}:v{c['version']}" for sc in snapshot["scenes"] for c in sc["consent_versions"]),
                 details={"scenes": len(scenes), "renders": [sc["render_id"] for sc in snapshot["scenes"]]})
    return approval


def invalidate_if_approved(localization, *, reason):
    """ADR 0014 invariant 3: any new version for an approved localization invalidates its approval."""
    loc = Localization.objects.select_for_update().get(pk=localization.pk)
    changed = 0
    for approval in Approval.objects.select_for_update().filter(localization=loc, status=Approval.Status.VALID):
        approval.status = Approval.Status.INVALIDATED
        approval.invalidated_reason = reason[:300]
        approval.save(update_fields=["status", "invalidated_reason"])
        audit.record(actor=None, action="APPROVAL_INVALIDATED", entity=approval, project_id=loc.project_id,
                     details={"reason": reason[:200]})
        changed += 1
    if changed or loc.status in (Localization.Status.APPROVED, Localization.Status.EXPORTED):
        loc.status = Localization.Status.IN_REVIEW
        loc.save(update_fields=["status"])
    return changed


def on_identity_revoked(localization, owner, affected_scene_ids, *, reason):
    """Part of the revocation cascade (ADR 0006 §5, scoped by ADR 0020): invalidate an approval and block
    exports ONLY if they contain this owner's identity (or an affected scene). Caller holds the owner lock
    and the Localization lock. Fallback renders are queued by the caller after commit."""
    from hyperlocalize.exports import services as exports

    owner_consent_ids = set(Consent.objects.filter(identity_owner=owner).values_list("pk", flat=True))
    uses_owner = any(
        c["consent_id"] in owner_consent_ids or sc["scene_id"] in affected_scene_ids
        for a in Approval.objects.filter(localization=localization, status=Approval.Status.VALID)
        for sc in a.snapshot["scenes"] for c in (sc["consent_versions"] or [{"consent_id": None}])
    )
    if affected_scene_ids or uses_owner:
        invalidate_if_approved(localization, reason=f"consent revoked ({reason})")
    exports.mark_consent_revoked(localization, owner_consent_ids)


def require_manager(actor, project):
    if not actor.is_authenticated:
        raise PermissionDenied()
    require_role(actor, project, Role.LOCALIZATION_MANAGER)
