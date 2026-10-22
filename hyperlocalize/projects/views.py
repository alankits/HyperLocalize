"""Project pages: list, create, workflow dashboard, upload, members, audience, glossary, speakers."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from hyperlocalize.accounts.models import Role
from hyperlocalize.accounts.permissions import require_member, roles_for
from hyperlocalize.identity.models import IdentityOwner
from hyperlocalize.localization.models import Localization, Scene, SegmentTranslation
from hyperlocalize.pipeline.models import Job

from . import services
from .models import Project, SpeakerTrack
from .storage import get_storage

STAGES = ["Project", "Source", "Analysis", "Localization", "Preview", "Review", "Approve", "Export"]


def _error_text(exc):
    if isinstance(exc, ValidationError):
        return " ".join(exc.messages)
    return str(exc)


def workflow_state(project):
    """Which workflow stages are complete (for the stepper). Derived from real state, never stored."""
    video = project.videos.first()
    loc = Localization.objects.filter(project=project).first()
    scenes = Scene.objects.filter(video__project=project)
    done = {"Project": True}
    done["Source"] = video is not None
    done["Analysis"] = bool(video and video.status == "ANALYZED")
    done["Localization"] = done["Analysis"] and scenes.exists() and not scenes.filter(status="PENDING").exists()
    done["Preview"] = done["Localization"] and not scenes.filter(status__in=["PENDING", "TRANSLATED"]).exists()
    done["Review"] = done["Preview"] and not scenes.exclude(status="ACCEPTED").exists()
    done["Approve"] = bool(loc and loc.status in ("APPROVED", "EXPORTED"))
    done["Export"] = bool(loc and loc.status == "EXPORTED")
    current = next((s for s in STAGES if not done.get(s)), None)
    return [{"name": s, "done": done.get(s, False), "current": s == current} for s in STAGES]


@login_required
def project_list(request):
    projects = Project.objects.filter(memberships__user=request.user).distinct().order_by("-created_at")
    return render(request, "projects/list.html", {"projects": projects})


@login_required
def project_create(request):
    if request.method == "POST":
        try:
            project = services.create_project(
                request.user, name=request.POST.get("name", ""), source_language=request.POST.get("source_language", "en"),
                target_locale=request.POST.get("target_locale", ""), domain=request.POST.get("domain", ""),
                data_classification=request.POST.get("data_classification", "PERSONAL"),
                formality=request.POST.get("formality", "neutral"), reading_level=request.POST.get("reading_level", "general"),
                cultural_notes=request.POST.get("cultural_notes", ""),
                source_url=request.POST.get("source_url", ""), source_licence=request.POST.get("source_licence", ""),
                source_attribution=request.POST.get("source_attribution", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _error_text(exc))
            return render(request, "projects/create.html", {"form": request.POST})
        messages.success(request, "Project created. You are its Localization Manager.")
        return redirect("projects:detail", pk=project.pk)
    return render(request, "projects/create.html", {"form": {}})


def _project_for(request, pk):
    project = get_object_or_404(Project, pk=pk)
    require_member(request.user, project)
    return project


@login_required
def project_detail(request, pk):
    from hyperlocalize.rendering import services as rendering
    from hyperlocalize.review import services as review

    project = _project_for(request, pk)
    loc = Localization.objects.get(project=project)
    video = project.videos.first()
    scenes = []
    for scene in Scene.objects.filter(video__project=project).order_by("index").prefetch_related("segments"):
        render_ = rendering.latest_render(scene, loc)
        from hyperlocalize.localization.services import blocking_checks, latest_translations

        latest = latest_translations(loc, list(scene.segments.all()))
        scenes.append({
            "scene": scene, "render": render_, "open_checks": len(blocking_checks(loc, [scene])),
            "mock": any(t.is_mock for t in latest.values()) or bool(render_ and render_.is_mock),
            "modes": sorted({v["mode"] for v in (render_.rendering_modes.values() if render_ else [])}),
        })
    roles = roles_for(request.user, project)
    approval_problems = review.approval_problems(request.user, loc) if loc.status in ("DRAFT", "IN_REVIEW") and scenes else []
    from hyperlocalize.exports.models import Export

    return render(request, "projects/detail.html", {
        "project": project, "loc": loc, "video": video, "scenes": scenes, "steps": workflow_state(project),
        "roles": roles, "is_manager": Role.LOCALIZATION_MANAGER in roles,
        "can_upload": bool(roles & {Role.MEDIA_OPERATOR, Role.LOCALIZATION_MANAGER}),
        "approval_problems": approval_problems,
        "approval": loc.approvals.order_by("-pk").first(),
        "exports": Export.objects.filter(approval__localization=loc).order_by("-pk"),
        "speakers": SpeakerTrack.objects.filter(video__project=project).select_related("identity_owner"),
        "owners": IdentityOwner.objects.filter(withdrawn_at__isnull=True).order_by("name"),
        "glossary": project.glossary.order_by("source_term"),
        "members": project.memberships.select_related("user").order_by("role", "user__username"),
        "role_choices": Role.choices,
        "jobs_active": Job.objects.filter(project=project, status__in=["QUEUED", "RUNNING"]).exists(),
        "human_versions": SegmentTranslation.objects.filter(localization=loc, origin="HUMAN").count(),
    })


@login_required
def project_jobs(request, pk):
    """htmx partial: recent jobs, polled every 2 s while any is active (ADR 0010)."""
    project = _project_for(request, pk)
    recent = Job.objects.filter(Q(project=project)).order_by("-pk")[:12]
    active = Job.objects.filter(project=project, status__in=("QUEUED", "RUNNING")).exists()
    response = render(request, "projects/_jobs.html", {"project": project, "jobs": recent, "active": active})
    if request.GET.get("polling") == "1" and not active:
        # The jobs we were watching have all finished: reload the whole page so the scenes, status and
        # approval panels show the results (htmx full refresh). The reloaded page does not poll again.
        response["HX-Refresh"] = "true"
    return response


@login_required
@require_POST
def upload(request, pk):
    project = _project_for(request, pk)
    if "video" not in request.FILES:
        messages.error(request, "Choose a video file.")
        return redirect("projects:detail", pk=pk)
    try:
        services.upload_video(request.user, project, request.FILES["video"], request.FILES.get("transcript"))
        messages.success(request, "Video accepted. Analysis is queued; this page updates as jobs finish.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _error_text(exc))
    return redirect("projects:detail", pk=pk)


@login_required
@require_POST
def add_member(request, pk):
    project = _project_for(request, pk)
    try:
        services.add_member(request.user, project, request.POST.get("username", "").strip(), request.POST.get("role", ""))
        messages.success(request, "Member added.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _error_text(exc))
    return redirect("projects:detail", pk=pk)


@login_required
@require_POST
def update_audience(request, pk):
    project = _project_for(request, pk)
    try:
        services.update_audience(request.user, project, formality=request.POST.get("formality", "neutral"),
                                 reading_level=request.POST.get("reading_level", "general"),
                                 cultural_notes=request.POST.get("cultural_notes", ""))
        messages.success(request, "Audience profile saved. It is used for new drafts and regenerations.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _error_text(exc))
    return redirect("projects:detail", pk=pk)


@login_required
@require_POST
def add_glossary(request, pk):
    project = _project_for(request, pk)
    try:
        services.add_glossary_term(
            request.user, project, source_term=request.POST.get("source_term", ""),
            target_term=request.POST.get("target_term", ""),
            accepted_forms=request.POST.get("accepted_forms", "").split(","),
            do_not_translate=request.POST.get("do_not_translate") == "on", note=request.POST.get("note", ""),
        )
        messages.success(request, "Glossary term added.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _error_text(exc))
    return redirect("projects:detail", pk=pk)


@login_required
@require_POST
def assign_speaker(request, pk, track_id):
    project = _project_for(request, pk)
    track = get_object_or_404(SpeakerTrack, pk=track_id, video__project=project)
    owner_id = request.POST.get("identity_owner") or None
    owner = get_object_or_404(IdentityOwner, pk=owner_id) if owner_id else None
    try:
        services.assign_speaker(request.user, track, owner)
        messages.success(request, "Speaker updated. Rendering modes are re-resolved from consent at the next preview.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _error_text(exc))
    return redirect("projects:detail", pk=pk)


@login_required
def source_video(request, pk):
    project = _project_for(request, pk)
    video = project.videos.first()
    if video is None:
        raise Http404()
    return FileResponse(get_storage().open(video.storage_key), content_type="video/mp4")
