"""Scene review (UC5) and approval (UC6) pages, plus authorised preview serving (CP10)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from hyperlocalize.accounts.models import Role
from hyperlocalize.accounts.permissions import require_member, roles_for
from hyperlocalize.localization import services as loc_services
from hyperlocalize.localization.models import CheckResult, Localization, Scene, Segment
from hyperlocalize.projects.models import Project
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.rendering import services as rendering
from hyperlocalize.rendering.models import RenderedScene

from . import services


def _err(exc):
    return " ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)


def _scene_for(request, scene_id):
    scene = get_object_or_404(Scene.objects.select_related("video__project"), pk=scene_id)
    require_member(request.user, scene.video.project)
    return scene


@login_required
def scene_review(request, scene_id):
    scene = _scene_for(request, scene_id)
    project = scene.video.project
    loc = Localization.objects.get(project=project)
    segments = list(scene.segments.select_related("speaker_track").order_by("index"))
    latest = loc_services.latest_translations(loc, segments)
    rows = []
    for seg in segments:
        t = latest.get(seg.pk)
        history = list(seg.translations.filter(localization=loc).order_by("-version")[:5])
        rows.append({"segment": seg, "t": t, "checks": list(t.checks.order_by("kind", "check_type")) if t else [],
                     "history": history})
    render_ = rendering.latest_render(scene, loc)
    roles = roles_for(request.user, project)
    siblings = list(Scene.objects.filter(video=scene.video).order_by("index").values_list("pk", flat=True))
    i = siblings.index(scene.pk)
    return render(request, "review/scene.html", {
        "scene": scene, "project": project, "loc": loc, "rows": rows, "render": render_,
        "render_current": rendering.render_is_current(render_, loc, scene),
        "is_reviewer": Role.REVIEWER in roles, "open_checks": len(loc_services.blocking_checks(loc, [scene])),
        "prev_id": siblings[i - 1] if i > 0 else None, "next_id": siblings[i + 1] if i + 1 < len(siblings) else None,
        "reviews": scene.reviews.select_related("reviewer").order_by("-pk")[:5],
        "regenerations": scene.regenerations.select_related("requested_by", "job").order_by("-pk")[:5],
    })


@login_required
@require_POST
def edit_segment(request, segment_id):
    seg = get_object_or_404(Segment.objects.select_related("scene__video__project"), pk=segment_id)
    require_member(request.user, seg.scene.video.project)
    try:
        loc_services.edit_translation(request.user, seg, subtitle_text=request.POST.get("subtitle_text", ""),
                                      speech_text=request.POST.get("speech_text", ""))
        messages.success(request, "Saved as a new human version; checks re-ran and the preview is being regenerated.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("review:scene", seg.scene_id)


@login_required
@require_POST
def resolve_check(request, check_id):
    check = get_object_or_404(CheckResult.objects.select_related("segment_translation__segment"), pk=check_id)
    scene_id = check.segment_translation.segment.scene_id
    require_member(request.user, check.segment_translation.localization.project)
    try:
        loc_services.resolve_check(request.user, check, resolution=request.POST.get("resolution", ""),
                                   reason=request.POST.get("reason", ""))
        messages.success(request, "Check resolved and recorded in the audit trail.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("review:scene", scene_id)


@login_required
@require_POST
def accept(request, scene_id):
    scene = _scene_for(request, scene_id)
    try:
        services.accept_scene(request.user, scene, comment=request.POST.get("comment", ""))
        messages.success(request, f"Scene {scene.index + 1} accepted.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("review:scene", scene.pk)


@login_required
@require_POST
def request_changes(request, scene_id):
    scene = _scene_for(request, scene_id)
    try:
        services.request_changes(request.user, scene, target=request.POST.get("target", "SCRIPT"),
                                 reason=request.POST.get("reason", ""), instruction=request.POST.get("instruction", ""))
        messages.success(request, "Regeneration queued for this scene only.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("review:scene", scene.pk)


@login_required
@require_POST
def approve(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    require_member(request.user, project)
    try:
        services.approve(request.user, Localization.objects.get(project=project))
        messages.success(request, "Approved. The exact versions are frozen; any later change invalidates this approval.")
    except services.ApprovalBlocked as exc:
        messages.error(request, " ".join(exc.reasons))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _err(exc))
    return redirect("projects:detail", project.pk)


def _render_for(request, render_id):
    r = get_object_or_404(RenderedScene.objects.select_related("scene__video__project", "localization"), pk=render_id)
    require_member(request.user, r.scene.video.project)
    if r.status != "ACTIVE":
        # CP10: quarantined or purged previews are never served.
        raise Http404("This preview is no longer available.")
    language = r.localization.target_locale.split("-")[0]
    for c in r.consent_versions:
        if not rendering._recheck(c, r.scene.video.project, language):
            raise Http404("Consent for this preview is no longer valid.")
    return r


@login_required
def preview_video(request, render_id):
    r = _render_for(request, render_id)
    return FileResponse(get_storage().open(r.video_key), content_type="video/mp4")


@login_required
def preview_vtt(request, render_id):
    r = _render_for(request, render_id)
    return HttpResponse(r.subtitles_vtt, content_type="text/vtt; charset=utf-8")
