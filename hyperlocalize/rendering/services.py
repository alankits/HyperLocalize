"""UC4 Generate Localized Preview: speech, timing fit, mixing, subtitles, scene preview.

The rendering mode of each speaker is resolved by the BACKEND from the current
consent state (ADR 0015): CLONED_VOICE only with valid consent and an active voice
profile; otherwise STOCK_VOICE; SUBTITLES_ONLY when policy forbids synthesis.
Consent is re-checked at every stage boundary (ADR 0006 §3): CP2 at claim, CP4 before
each cloned segment, CP5 on save (locked), CP6 before mixing, CP7 on save (locked).
"""
import os
import tempfile
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Max

from hyperlocalize import media_tools
from hyperlocalize.accounts.models import Policy
from hyperlocalize.audit import services as audit
from hyperlocalize.identity import services as consent
from hyperlocalize.identity.models import Use, VoiceProfile
from hyperlocalize.localization.models import Scene
from hyperlocalize.localization.services import latest_translations
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.inference import InferenceError, InferenceProcess
from hyperlocalize.pipeline.providers.base import chain_for, get_adapter
from hyperlocalize.projects.storage import get_storage

from .models import ArtefactStatus, RenderedScene, RenderingMode, SynthesisedSegment

MAX_TEMPO = Decimal("1.15")  # bounded tempo adjustment, ±15 % (SPIKE_PLAN M5; an assumed working threshold)


# --------------------------------------------------------------------------- queueing

@transaction.atomic
def enqueue_render(scene, localization, *, actor=None, reason=""):
    """Queue a preview render for one scene, replacing any render still queued for it."""
    for old in jobs.active_jobs(type="render_scene", scene=scene).filter(status="QUEUED"):
        jobs.request_cancel(old, "SUPERSEDED", actor)
    owners = {s.speaker_track.identity_owner_id for s in scene.segments.select_related("speaker_track")
              if s.speaker_track and s.speaker_track.identity_owner_id}
    owner_id = next(iter(owners)) if len(owners) == 1 else None
    return jobs.enqueue("render_scene", actor=actor, project=localization.project, scene=scene,
                        localization=localization, identity_owner_id=owner_id, payload={"reason": reason})


def cp2_on_claim(job):
    """CP2 (ADR 0006): at claim, in the same transaction. A render never fails for lack of consent:
    the mode is resolved per speaker inside the job, so CP2 only refuses a job flagged for cancel."""
    if job.cancel_requested:
        return job.cancel_reason or "CANCEL_REQUESTED"
    return None


# --------------------------------------------------------------------------- mode resolution

def resolve_mode(speaker_track, project, language):
    """Return (mode, voice_profile, consent_check, note)."""
    if not Policy.get("synthesis_allowed"):
        return RenderingMode.SUBTITLES_ONLY, None, None, "policy: speech synthesis is off"
    owner = speaker_track.identity_owner if speaker_track else None
    if owner is None:
        return RenderingMode.STOCK_VOICE, None, None, "no identity owner linked"
    if not Policy.get("cloning_allowed"):
        return RenderingMode.STOCK_VOICE, None, None, "policy: cloning is off"
    check, reason = consent.evaluate(owner, Use.VOICE_SYNTHESIS, project, language)
    if check is None:
        return RenderingMode.STOCK_VOICE, None, None, f"consent: {reason}"
    profile = (VoiceProfile.objects.filter(identity_owner=owner, consent__project=project, status=VoiceProfile.Status.ACTIVE)
               .order_by("-pk").first())
    if profile is None:
        return RenderingMode.STOCK_VOICE, None, None, "no active voice profile"
    if not any(get_adapter(n) and get_adapter(n).available() for n in chain_for("speech_cloned")):
        return RenderingMode.STOCK_VOICE, None, None, "no identity-preserving voice provider available"
    return RenderingMode.CLONED_VOICE, profile, check, "consent valid"


def _first_available(stage):
    for name in chain_for(stage):
        adapter = get_adapter(name)
        if adapter and adapter.available():
            return adapter
    return None


# --------------------------------------------------------------------------- the render job

def render_scene(job, ctx):
    scene = Scene.objects.select_related("video__project").get(pk=job.scene_id)
    localization = job.localization
    project = scene.video.project
    language = localization.target_locale.split("-")[0]
    storage = get_storage()
    segments = list(scene.segments.select_related("speaker_track__identity_owner").order_by("index"))
    translations = latest_translations(localization, segments)
    if len(translations) != len(segments):
        raise ValueError("every segment needs a localized draft before the preview can be rendered")
    with transaction.atomic():
        s = Scene.objects.select_for_update().get(pk=scene.pk)
        if s.status in (Scene.Status.CHANGES_REQUESTED,):
            s.status = Scene.Status.REGENERATING
            s.save(update_fields=["status"])

    workdir = tempfile.mkdtemp(prefix="hl-render-", dir=str(settings.HL_MEDIA_ROOT / "tmp"))
    inference = InferenceProcess()
    synthesised, placements, modes, consent_versions = [], [], {}, []
    try:
        for seg in segments:
            ctx.checkpoint(f"segment {seg.index + 1}")
            t = translations[seg.pk]
            mode, profile, check, note = resolve_mode(seg.speaker_track, project, language)
            label = seg.speaker_track.label if seg.speaker_track else "Speaker"
            modes[label] = {"mode": mode, "note": note}
            if mode == RenderingMode.SUBTITLES_ONLY:
                continue
            adapter = _first_available("speech_cloned" if mode == RenderingMode.CLONED_VOICE else "speech_stock")
            if adapter is None:
                modes[label] = {"mode": RenderingMode.SUBTITLES_ONLY, "note": "no speech provider available"}
                continue
            out_path = os.path.join(workdir, f"seg{seg.pk}.wav")
            request = {"adapter": adapter.name, "text": t.speech_text, "language": language, "out_path": out_path}

            def poll():
                ctx.checkpoint()
                if check is not None:  # CP4 while the cloned segment is being synthesised
                    again, reason = consent.evaluate(seg.speaker_track.identity_owner, Use.VOICE_SYNTHESIS, project, language, job)
                    if again is None:
                        raise jobs.JobCancelled("CONSENT_REVOKED")

            if check is not None:
                poll()  # CP4 before the segment starts
                request["reference_clip"] = str(storage.local_path(profile.storage_key))
                request["reference_text"] = profile.transcript
            try:
                result = inference.call(request, poll=poll)
            except InferenceError as exc:
                raise InferenceError(f"segment {seg.index + 1}: {exc}") from None
            syn = _save_synthesised(seg, t, localization, result, mode, adapter, check, project, out_path, job)
            if syn is None:  # CP5 refused: consent changed between synthesis and save
                raise jobs.JobCancelled("CONSENT_REVOKED")
            synthesised.append(syn)
            if check is not None:
                consent_versions.append({"consent_id": check.consent_id, "version": check.version})
            placements.append((storage.local_path(syn.audio_key), seg.start_ms - scene.start_ms, syn.tempo))
        ctx.checkpoint("mixing")
        for item in consent_versions:  # CP6 before render / mix
            owner_check = _recheck(item, project, language, job)
            if not owner_check:
                raise jobs.JobCancelled("CONSENT_REVOKED")
        speech_path = os.path.join(workdir, "speech.wav") if placements else None
        if speech_path:
            media_tools.build_speech_track(placements, scene.end_ms - scene.start_ms, speech_path)
        video_key, video_path = storage.new_path(".mp4")
        media_tools.render_scene_clip(storage.local_path(scene.video.storage_key), scene.start_ms, scene.end_ms,
                                      video_path, speech_track=speech_path)
        storage.finalise(video_key)
        vtt = scene_vtt(segments, translations, scene.start_ms)
        if not _save_render(scene, localization, video_key, vtt, synthesised, translations, consent_versions, modes, project, job):
            storage.delete(video_key)
            raise jobs.JobCancelled("CONSENT_REVOKED")
    except jobs.JobCancelled:
        owners = set()
        for syn in synthesised:  # segments saved earlier in this job are quarantined, then purged
            if _quarantine_synth(syn) and syn.consent_id:
                owners.add(syn.consent.identity_owner_id)
        with transaction.atomic():
            for owner_id in sorted(owners):
                jobs.enqueue("purge_identity_data", identity_owner_id=owner_id, project=project,
                             payload={"reason": "render cancelled"})
            # A cancelled regeneration must not leave the scene stuck in REGENERATING (review #4).
            Scene.objects.filter(pk=scene.pk, status=Scene.Status.REGENERATING).update(status=Scene.Status.CHANGES_REQUESTED)
        raise
    finally:
        inference.kill()
        for name in os.listdir(workdir):
            os.unlink(os.path.join(workdir, name))
        os.rmdir(workdir)


def _recheck(item, project, language, job=None):
    """The owner's LATEST consent in this project still passes the full gate (CP6–CP10).
    Artefacts made before a revocation are quarantined by the cascade, so they are refused by status."""
    from hyperlocalize.identity.models import Consent

    c = Consent.objects.get(pk=item["consent_id"])
    current, _ = consent.evaluate(c.identity_owner, Use.VOICE_SYNTHESIS, project, language, job)
    return current is not None


def _save_synthesised(seg, t, localization, result, mode, adapter, check, project, wav_path, job=None):
    storage = get_storage()
    slot = max(seg.duration_ms, 1)
    tempo = Decimal("1.000")
    if result["duration_ms"] > slot:
        tempo = min(MAX_TEMPO, (Decimal(result["duration_ms"]) / Decimal(slot)).quantize(Decimal("0.001")))
    with transaction.atomic():
        if check is not None:
            consent.lock_owner(check.identity_owner_id)  # CP5: lock the person, not the consent version
            if not consent.locked_save_allowed(check, project, job):
                os.unlink(wav_path)
                return None
        key, sha = storage.save_file(wav_path, ".wav")
        version = (SynthesisedSegment.objects.filter(segment=seg, localization=localization)
                   .aggregate(m=Max("version"))["m"] or 0) + 1
        syn = SynthesisedSegment.objects.create(
            segment=seg, localization=localization, translation=t, version=version, audio_key=key, sha256=sha,
            duration_ms=result["duration_ms"], rendering_mode=mode,
            consent_id=check.consent_id if check else None, consent_version=check.version if check else None,
            adapter=adapter.name, model=result.get("model", ""), tempo=tempo, is_mock=adapter.is_mock,
        )
        audit.record(actor=None, action="SPEECH_SYNTHESISED", entity=syn, project_id=project.pk, scene_id=seg.scene_id,
                     consent_version=f"{check.consent_id}:v{check.version}" if check else "",
                     details={"mode": mode, "adapter": adapter.name, "sha256": sha, "is_mock": adapter.is_mock,
                              "tempo": str(tempo)})
    return syn


def _save_render(scene, localization, video_key, vtt, synthesised, translations, consent_versions, modes, project, job=None):
    from hyperlocalize.localization.models import Localization

    storage = get_storage()
    with transaction.atomic():
        from hyperlocalize.identity.models import Consent

        owner_ids = sorted({Consent.objects.get(pk=c["consent_id"]).identity_owner_id for c in consent_versions})
        for oid in owner_ids:  # CP7: locked save, owners in ascending id order
            consent.lock_owner(oid)
        Localization.objects.select_for_update().get(pk=localization.pk)  # lock order: owners → Localization → Scene
        language = localization.target_locale.split("-")[0]
        for item in consent_versions:
            if not _recheck(item, project, language, job):
                return False
        if job is not None and type(job).objects.filter(pk=job.pk, cancel_requested=True).exists():
            return False
        version = (RenderedScene.objects.filter(scene=scene, localization=localization).aggregate(m=Max("version"))["m"] or 0) + 1
        render = RenderedScene.objects.create(
            scene=scene, localization=localization, version=version, video_key=video_key, subtitles_vtt=vtt,
            translation_ids=sorted(t.pk for t in translations.values()), consent_versions=consent_versions,
            rendering_modes=modes, is_mock=any(s.is_mock for s in synthesised) or any(t.is_mock for t in translations.values()),
        )
        render.synthesised_segments.set(synthesised)
        s = Scene.objects.select_for_update().get(pk=scene.pk)
        s.status = Scene.Status.IN_REVIEW
        s.save(update_fields=["status"])
        audit.record(actor=None, action="PREVIEW_RENDERED", entity=render, project_id=project.pk, scene_id=scene.pk,
                     details={"version": version, "modes": {k: v["mode"] for k, v in modes.items()},
                              "is_mock": render.is_mock, "sha256": storage.finalise(video_key)})
        from hyperlocalize.review import services as review

        review.invalidate_if_approved(localization, reason=f"new preview for scene {scene.pk}")
        _update_localization_status(localization)
    return True


def _update_localization_status(localization):
    from hyperlocalize.localization.models import Localization

    loc = Localization.objects.select_for_update().get(pk=localization.pk)
    scenes = Scene.objects.filter(video__project=loc.project)
    if loc.status == Localization.Status.DRAFT and scenes.exists() and not scenes.filter(
            status__in=[Scene.Status.PENDING, Scene.Status.TRANSLATED]).exists():
        loc.status = Localization.Status.IN_REVIEW
        loc.save(update_fields=["status"])


def _fmt(ms):
    h, rem = divmod(max(ms, 0), 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def scene_vtt(segments, translations, offset_ms=0):
    lines = ["WEBVTT", ""]
    for seg in segments:
        t = translations.get(seg.pk)
        if t is None:
            continue
        lines += [f"{_fmt(seg.start_ms - offset_ms)} --> {_fmt(seg.end_ms - offset_ms)}", t.subtitle_text, ""]
    return "\n".join(lines)


def latest_render(scene, localization):
    return RenderedScene.objects.filter(scene=scene, localization=localization).order_by("-version").first()


def render_is_current(render, localization, scene):
    """True if the render shows the latest translations of every segment in the scene."""
    if render is None or render.status != ArtefactStatus.ACTIVE:
        return False
    current = latest_translations(localization, list(scene.segments.all()))
    return sorted(t.pk for t in current.values()) == sorted(render.translation_ids)


# --------------------------------------------------------------------------- revocation

def _quarantine_synth(syn):
    storage = get_storage()
    if syn.status == ArtefactStatus.ACTIVE:
        storage.quarantine(syn.audio_key)
        SynthesisedSegment.objects.filter(pk=syn.pk).update(status=ArtefactStatus.QUARANTINED)
        return True
    return False


def identity_scene_ids(owner, project):
    """Scenes with ACTIVE identity artefacts of this owner in this project (read-only)."""
    syns = SynthesisedSegment.objects.filter(consent__identity_owner=owner, consent__project=project, status=ArtefactStatus.ACTIVE)
    ids = set(syns.values_list("segment__scene_id", flat=True))
    ids |= set(RenderedScene.objects.filter(synthesised_segments__in=syns, status=ArtefactStatus.ACTIVE).values_list("scene_id", flat=True))
    return sorted(ids)


def enqueue_fallback_renders(scene_ids, localization_id):
    """After a revocation commits: re-render affected scenes; the backend then resolves STOCK_VOICE."""
    from hyperlocalize.localization.models import Localization

    localization = Localization.objects.get(pk=localization_id)
    for scene in Scene.objects.filter(pk__in=scene_ids).order_by("pk"):
        enqueue_render(scene, localization, reason="fallback after consent revocation")


def quarantine_identity_artefacts(owner, project):
    """ADR 0006 §5 (amended by ADR 0020): only artefacts saved under this owner's consent in THIS project.
    Returns the affected scene ids. Caller holds the owner lock."""
    storage = get_storage()
    syns = SynthesisedSegment.objects.filter(consent__identity_owner=owner, consent__project=project,
                                             status=ArtefactStatus.ACTIVE)
    scene_ids = set(syns.values_list("segment__scene_id", flat=True))
    renders = RenderedScene.objects.filter(synthesised_segments__in=syns, status=ArtefactStatus.ACTIVE).distinct()
    for r in renders:
        if r.video_key:
            storage.quarantine(r.video_key)
        scene_ids.add(r.scene_id)
    RenderedScene.objects.filter(pk__in=[r.pk for r in renders]).update(status=ArtefactStatus.QUARANTINED)
    for syn in syns:
        storage.quarantine(syn.audio_key)
    syns.update(status=ArtefactStatus.QUARANTINED)
    return sorted(scene_ids)


def purge_quarantined(owner, project=None):
    """Delete quarantined identity audio and render files (ADR 0006 §5). Keeps hashes. Each item is marked
    PURGED only after its file is gone; failures stay QUARANTINED ("deletion pending") for the retry."""
    storage = get_storage()
    syns = SynthesisedSegment.objects.filter(consent__identity_owner=owner, status=ArtefactStatus.QUARANTINED)
    if project is not None:
        syns = syns.filter(consent__project=project)
    renders = RenderedScene.objects.filter(synthesised_segments__in=syns, status=ArtefactStatus.QUARANTINED).distinct()
    purged = {"segments": [], "renders": [], "pending": []}
    for r in list(renders):
        try:
            storage.delete(r.video_key)
        except OSError:
            purged["pending"].append(f"render:{r.pk}")
            continue
        RenderedScene.objects.filter(pk=r.pk).update(status=ArtefactStatus.PURGED)
        purged["renders"].append(r.pk)
    for syn in list(syns):
        try:
            storage.delete(syn.audio_key)
        except OSError:
            purged["pending"].append(f"segment:{syn.pk}")
            continue
        SynthesisedSegment.objects.filter(pk=syn.pk).update(status=ArtefactStatus.PURGED)
        purged["segments"].append(syn.pk)
    return purged
