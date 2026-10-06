"""Job handlers, registered by type (ADR 0003). Each handler calls the owning app's services."""
from django.db import transaction

from hyperlocalize import media_tools
from hyperlocalize.audit import services as audit

from .jobs import register_handler
from .providers.base import NoProviderAvailable, run_chain


@register_handler("analyze_video")
def analyze_video(job, ctx):
    """UC2: extract audio, transcribe (chain), detect shot cuts, build segments and scenes,
    then queue localization (UC3)."""
    from hyperlocalize.localization import services as loc
    from hyperlocalize.projects.models import Video
    from hyperlocalize.projects.storage import get_storage

    from . import jobs

    video = Video.objects.select_related("project").get(pk=job.video_id)
    storage = get_storage()
    Video.objects.filter(pk=video.pk).update(status=Video.Status.ANALYZING)
    try:
        ctx.checkpoint("extracting audio")
        audio_key, audio_path = storage.new_path(".wav")
        media_tools.extract_audio(storage.local_path(video.storage_key), audio_path)
        storage.finalise(audio_key)
        Video.objects.filter(pk=video.pk).update(audio_key=audio_key)
        video.audio_key = audio_key
        ctx.checkpoint("transcribing")
        outcome = run_chain("transcription", lambda a: a.transcribe(str(audio_path), video.project.source_language, video=video))
        ctx.checkpoint("finding scenes")
        cuts = media_tools.detect_shot_cuts(storage.local_path(video.storage_key))
        with transaction.atomic():
            scene_count = loc.save_analysis(video, outcome.result, cuts)
            Video.objects.filter(pk=video.pk).update(
                status=Video.Status.ANALYZED, transcript_adapter=outcome.adapter.name,
                transcript_model=outcome.result.model, transcript_is_mock=outcome.adapter.is_mock)
            audit.record(actor=None, action="VIDEO_ANALYZED", entity=video, project_id=video.project_id,
                         details={"segments": len(outcome.result.segments), "scenes": scene_count,
                                  "adapter": outcome.adapter.name, "is_mock": outcome.adapter.is_mock,
                                  "shot_cuts": len(cuts), "is_fallback": outcome.is_fallback})
            localization = video.project.localizations.get()
            jobs.enqueue("localize", project=video.project, localization=localization, video=video)
    except (NoProviderAvailable, media_tools.MediaError) as exc:
        Video.objects.filter(pk=video.pk).update(status=Video.Status.FAILED, error=str(exc)[:2000])
        raise


@register_handler("localize")
def localize(job, ctx):
    """UC3 for every scene (after analysis) or for one scene (regeneration), then queue previews (UC4)."""
    from hyperlocalize.localization import services as loc
    from hyperlocalize.localization.models import Scene
    from hyperlocalize.rendering import services as rendering

    localization = job.localization
    scenes = [job.scene] if job.scene_id else list(Scene.objects.filter(video__project=localization.project).order_by("index"))
    instruction = job.payload.get("instruction", "")
    for scene in scenes:
        ctx.checkpoint(f"localizing scene {scene.index + 1}")
        loc.localize_scene(localization, scene, instruction=instruction, job_ctx=ctx)
        with transaction.atomic():
            rendering.enqueue_render(scene, localization, reason="new localized draft")


@register_handler("render_scene")
def render_scene(job, ctx):
    from hyperlocalize.rendering import services as rendering

    rendering.render_scene(job, ctx)


def _render_claim(job):
    from hyperlocalize.rendering import services as rendering

    return rendering.cp2_on_claim(job)


from .jobs import HANDLERS  # noqa: E402

HANDLERS["render_scene"] = (render_scene, _render_claim)


@register_handler("build_export")
def build_export(job, ctx):
    from hyperlocalize.exports import services as exports

    exports.build_export(job, ctx)


@register_handler("purge_identity_data")
def purge_identity_data(job, ctx):
    """Runs immediately after revocation (ADR 0006 §5): deletes quarantined identity audio, render
    files, revoked export packages, voice-profile clips in the revoked scope, and pending offline copies."""
    from django.utils import timezone

    from hyperlocalize.exports import services as exports
    from hyperlocalize.identity.models import Consent, OfflineCopy, VoiceProfile
    from hyperlocalize.projects.storage import get_storage
    from hyperlocalize.rendering import services as rendering

    owner = job.identity_owner
    project = job.project
    storage = get_storage()
    purged = rendering.purge_quarantined(owner, project)
    exports_purged = exports.purge_revoked_exports(project) if project else []
    profiles = []
    for vp in VoiceProfile.objects.filter(identity_owner=owner, status=VoiceProfile.Status.ACTIVE).select_related("consent"):
        latest = Consent.objects.filter(identity_owner=owner, kind="PROJECT", project=vp.consent.project).order_by("-version").first()
        standing = Consent.objects.filter(identity_owner=owner, kind="STANDING").order_by("-version").first()
        in_scope = project is None or vp.consent.project_id == project.pk
        if in_scope and (latest is None or latest.status != "ACTIVE" or "voice_synthesis" not in latest.uses
                         or owner.withdrawn_at or (standing and standing.status != "ACTIVE")):
            storage.delete(vp.storage_key)
            VoiceProfile.objects.filter(pk=vp.pk).update(status=VoiceProfile.Status.DELETED, deleted_at=timezone.now())
            profiles.append(vp.pk)
    offline = []
    for copy in OfflineCopy.objects.filter(identity_owner=owner, status=OfflineCopy.Status.DELETION_PENDING):
        storage.delete(copy.storage_key)
        OfflineCopy.objects.filter(pk=copy.pk).update(status=OfflineCopy.Status.DELETED, deleted_at=timezone.now())
        offline.append(copy.pk)
        with transaction.atomic():
            audit.record(actor=None, action="OFFLINE_COPY_DELETED", entity=copy, details={"sha256": copy.sha256, "kind": copy.kind})
    with transaction.atomic():
        audit.record(actor=None, action="IDENTITY_DATA_PURGED", entity=("identity.IdentityOwner", owner.pk),
                     project_id=project.pk if project else None,
                     details={"synthesised_segments": purged["segments"], "renders": purged["renders"],
                              "exports": exports_purged, "voice_profiles": profiles, "offline_copies": offline})


@register_handler("consent_expiry_sweep")
def consent_expiry_sweep(job, ctx):
    from hyperlocalize.identity import services as identity

    identity.expire_due()
