"""The Speaker / Identity Owner's consent page (UC7 and "Record Consent"). Owners see and change only
their own consent; they have no access to project content (ADR 0011)."""
from datetime import datetime, time, timezone as dt_tz

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from hyperlocalize.projects.models import Project
from hyperlocalize.rendering.models import SynthesisedSegment

from . import services
from .models import Consent, CopyKind, IdentityOwner, Purpose, Use, VoiceProfile


def _owner(request):
    try:
        return request.user.identity_owner
    except IdentityOwner.DoesNotExist:
        raise Http404("Your account is not linked to an identity owner.") from None


def _err(exc):
    return " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)


def _date_end(value):
    d = datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.combine(d, time(23, 59, 59), tzinfo=dt_tz.utc)


@login_required
def consent_page(request):
    owner = _owner(request)
    standing = services.latest_standing(owner)
    project_ids = set(owner.speaker_tracks.values_list("video__project_id", flat=True)) | set(
        owner.consents.filter(kind="PROJECT").values_list("project_id", flat=True))
    rows = []
    for project in Project.objects.filter(pk__in=project_ids).order_by("name"):
        pc = services.latest_project_consent(owner, project)
        uses = SynthesisedSegment.objects.filter(consent__identity_owner=owner, consent__project=project)
        rows.append({"project": project, "consent": pc,
                     "check": services.evaluate(owner, Use.VOICE_SYNTHESIS, project, (pc.languages[0] if pc and pc.languages else "")),
                     "profiles": VoiceProfile.objects.filter(identity_owner=owner, consent__project=project).order_by("-pk"),
                     "uses_count": uses.count(), "active_uses": uses.filter(status="ACTIVE").count()})
    return render(request, "identity/consent.html", {
        "owner": owner, "standing": standing, "rows": rows,
        "history": owner.consents.order_by("-created_at")[:15],
        "uses": Use.choices, "purposes": Purpose.choices, "copy_kinds": CopyKind.choices,
        "projects_available": Project.objects.exclude(pk__in=[r["project"].pk for r in rows]).filter(
            videos__speakers__identity_owner=owner).distinct(),
    })


@login_required
@require_POST
def grant_standing(request):
    owner = _owner(request)
    try:
        services.grant_standing_consent(
            request.user, owner, uses=request.POST.getlist("uses"), permitted_purposes=request.POST.getlist("purposes"),
            permitted_copy_kinds=request.POST.getlist("copy_kinds"),
            languages=[x.strip() for x in request.POST.get("languages", "").split(",") if x.strip()],
            processors=[x.strip() for x in request.POST.get("processors", "").split(",") if x.strip()],
            expires_at=_date_end(request.POST.get("expires_on", "")), evidence_ref=request.POST.get("evidence_ref", ""),
        )
        messages.success(request, "Standing consent recorded.")
    except (ValidationError, PermissionDenied, ValueError) as exc:
        messages.error(request, _err(exc))
    return redirect("identity:consent")


@login_required
@require_POST
def grant_project(request, project_id):
    owner = _owner(request)
    project = get_object_or_404(Project, pk=project_id)
    st = services.latest_standing(owner)
    try:
        if st is None:
            raise ValidationError("Record your standing consent first.")
        expires = min(_date_end(request.POST["expires_on"]), st.expires_at) if request.POST.get("expires_on") else st.expires_at
        services.grant_project_consent(request.user, owner, project, uses=request.POST.getlist("uses") or [Use.VOICE_SYNTHESIS],
                                       languages=[x.strip() for x in request.POST.get("languages", "").split(",") if x.strip()],
                                       processors=[], expires_at=expires)
        messages.success(request, f"Consent granted for {project.name}.")
    except (ValidationError, PermissionDenied, ValueError) as exc:
        messages.error(request, _err(exc))
    return redirect("identity:consent")


@login_required
@require_POST
def revoke_project(request, project_id):
    owner = _owner(request)
    project = get_object_or_404(Project, pk=project_id)
    try:
        services.revoke_project_consent(request.user, owner, project)
        if project.purpose == Purpose.DEMO_REHEARSAL:
            messages.success(request, "Revoked in this rehearsal project only (a demonstration). To withdraw for real, use Withdraw.")
        else:
            messages.success(request, "Revoked for this project. Running jobs were stopped and your cloned audio is being deleted.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("identity:consent")


@login_required
@require_POST
def narrow(request):
    owner = _owner(request)
    remove = {f: request.POST.getlist(f) for f in ("uses", "permitted_purposes", "permitted_copy_kinds") if request.POST.getlist(f)}
    langs = [x.strip() for x in request.POST.get("languages", "").split(",") if x.strip()]
    if langs:
        remove["languages"] = langs
    try:
        services.narrow_standing_consent(request.user, owner, remove=remove)
        messages.success(request, "Standing consent narrowed. Affected projects were updated.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("identity:consent")


@login_required
@require_POST
def withdraw(request):
    owner = _owner(request)
    if request.POST.get("confirm") != "WITHDRAW":
        messages.error(request, "Type WITHDRAW to confirm. Withdrawal is final.")
        return redirect("identity:consent")
    try:
        services.withdraw(request.user, owner)
        messages.success(request, "Withdrawn. All your consents are revoked and your registered voice copies are being deleted.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("identity:consent")


@login_required
@require_POST
def upload_profile(request, project_id):
    owner = _owner(request)
    project = get_object_or_404(Project, pk=project_id)
    try:
        if "clip" not in request.FILES:
            raise ValidationError("Choose a reference clip.")
        services.create_voice_profile(request.user, owner, project, request.FILES["clip"],
                                      transcript=request.POST.get("transcript", ""), language=request.POST.get("language", ""))
        messages.success(request, "Reference clip stored for this project.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("identity:consent")
