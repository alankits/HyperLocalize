"""Demo reset by rebuild, and the offline-copy register (ADR 0020 §3–§4).

- `build_demo_seed` copies the owner's reference clip into media/offline/ and registers it.
- `demo_reset` builds a NEW DEMO_REHEARSAL project from a source project's latest valid approval and
  the registered seed. It never overwrites the database, deletes rows or restores files; it only appends.
- `register_offline_copy` registers a screen recording made outside the system.
Each command locks the IdentityOwner first and makes every check under that lock (ADR 0020 N1).

IMPLEMENTATION CHOICE: the seed's script and translations are read from the source project's latest
VALID approval at reset time (they are text, not identity data); only identity files are copied into
media/offline/. Importing pre-rendered cloned audio into the seed is NOT IMPLEMENTED yet: a rehearsal
renders its previews with the configured voice provider instead.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from hyperlocalize.accounts.models import ProjectMembership
from hyperlocalize.audit import services as audit

from . import services
from .models import REMOTE_VOICE_PROCESSORS, Consent, CopyKind, OfflineCopy, Purpose, Use, VoiceProfile


class DemoRefused(ValidationError):
    pass


def _require_admin(actor):
    if not getattr(actor, "is_administrator", False):
        raise PermissionDenied("Only an Administrator runs the demo commands (ADR 0011 as amended by ADR 0020).")


def _standing_problems(owner, language):
    st = services.latest_standing(owner)
    if owner.withdrawn_at:
        return ["the identity owner has withdrawn"]
    if st is None or st.status != Consent.Status.ACTIVE:
        return ["no active standing consent"]
    problems = []
    if st.expires_at <= timezone.now():
        problems.append("the standing consent has expired")
    if not {Purpose.STANDARD, Purpose.DEMO_REHEARSAL} <= set(st.permitted_purposes):
        problems.append("the standing consent does not permit both STANDARD and DEMO_REHEARSAL projects")
    if Use.VOICE_SYNTHESIS not in st.uses:
        problems.append("the standing consent does not include voice_synthesis")
    if language not in st.languages:
        problems.append(f"the standing consent does not include the seed language '{language}'")
    return problems


def _refuse(actor, action, owner, problems, project_id=None):
    audit.record_standalone(actor=actor, action=action, entity=owner, project_id=project_id, details={"reasons": problems})
    raise DemoRefused("Refused: " + "; ".join(problems) + ".")


def build_demo_seed(actor, source_project, owner):
    from hyperlocalize.projects.storage import get_storage

    _require_admin(actor)
    localization = source_project.localizations.get()
    language = localization.target_locale.split("-")[0]
    storage = get_storage()
    problems = []
    with transaction.atomic():
        owner = services.lock_owner(owner.pk)
        problems += _standing_problems(owner, language)
        check, reason = services.evaluate(owner, Use.VOICE_SYNTHESIS, source_project, language)
        if check is None:
            problems.append(f"the source project's consent scope fails the gate ({reason})")
        profile = (VoiceProfile.objects.filter(identity_owner=owner, consent__project=source_project,
                                               status=VoiceProfile.Status.ACTIVE).order_by("-pk").first())
        if profile is None or not storage.exists(profile.storage_key):
            problems.append("no active reference clip in the source project")
        if not localization.approvals.filter(status="VALID").exists():
            problems.append("the source project has no valid approval to rebuild from")
        if not problems:
            st = services.latest_standing(owner)
            key, sha = storage.save_offline_file(storage.local_path(profile.storage_key), ".wav")
            copy = OfflineCopy.objects.create(identity_owner=owner, consent_version=st, kind=CopyKind.DEMO_SEED_REFERENCE,
                                              storage_key=key, language=language, sha256=sha)
            audit.record(actor=actor, action="OFFLINE_COPY_REGISTERED", entity=copy, consent_version=f"{st.pk}:v{st.version}",
                         details={"kind": copy.kind, "sha256": sha})
            audit.record(actor=actor, action="SEED_BUILT", entity=copy, project_id=source_project.pk,
                         consent_version=f"{st.pk}:v{st.version}",
                         details={"source_project_id": source_project.pk, "reference_copy_id": copy.pk,
                                  "reference_text_from_profile": profile.pk})
            return copy
    _refuse(actor, "SEED_BUILD_REFUSED", owner, problems, source_project.pk)


def _seed_copy(owner):
    return (OfflineCopy.objects.filter(identity_owner=owner, kind=CopyKind.DEMO_SEED_REFERENCE)
            .order_by("-pk").first())


def demo_reset(actor, source_project, owner):
    """Build a fresh rehearsal project. Returns the new project, or raises DemoRefused (audited)."""
    from hyperlocalize.projects.storage import get_storage

    _require_admin(actor)
    storage = get_storage()
    source_loc = source_project.localizations.get()
    language = source_loc.target_locale.split("-")[0]
    problems = []
    try:
        return _demo_reset_locked(actor, source_project, owner, source_loc, language, storage, problems)
    except services.ConsentDenied as exc:  # review #10: an unexpected gate refusal becomes an audited refusal
        problems.append(f"consent gate refused ({exc.reason})")
    _refuse(actor, "DEMO_RESET_REFUSED", owner, problems, source_project.pk)


def _demo_reset_locked(actor, source_project, owner, source_loc, language, storage, problems):
    from hyperlocalize.localization import services as loc
    from hyperlocalize.localization.models import Localization, Scene, Segment, SegmentTranslation
    from hyperlocalize.projects.models import AudienceProfile, GlossaryTerm, Project, SpeakerTrack, Video

    with transaction.atomic():
        owner = services.lock_owner(owner.pk)
        problems += _standing_problems(owner, language)
        seed = _seed_copy(owner)
        if seed is None:
            problems.append("no registered seed reference clip (run build_demo_seed)")
        elif seed.status != OfflineCopy.Status.PRESENT:
            problems.append(f"the seed reference clip is {seed.status}")
        elif not storage.exists(seed.storage_key) or storage.sha256(seed.storage_key) != seed.sha256:
            problems.append("the seed file is missing or its SHA-256 does not match the register (accidental drift)")
        approval = source_loc.approvals.filter(status="VALID").order_by("-pk").first()
        if approval is None:
            problems.append("the source project has no valid approval to rebuild from")
        if not problems:
            st = services.latest_standing(owner)
            stamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            project = Project.objects.create(name=f"Demo (reset {stamp})", source_language=source_project.source_language,
                                             domain=source_project.domain, data_classification=source_project.data_classification,
                                             created_by=actor, purpose=Purpose.DEMO_REHEARSAL)
            a = source_project.audience
            AudienceProfile.objects.create(project=project, locale=a.locale, formality=a.formality, reading_level=a.reading_level,
                                           unit_conversions=a.unit_conversions, cultural_notes=a.cultural_notes)
            new_loc = Localization.objects.create(project=project, target_locale=source_loc.target_locale)
            for m in ProjectMembership.objects.filter(project=source_project):
                ProjectMembership.objects.create(user=m.user, project=project, role=m.role)
            for g in GlossaryTerm.objects.filter(project=source_project):
                GlossaryTerm.objects.create(project=project, source_term=g.source_term, target_term=g.target_term,
                                            accepted_forms=g.accepted_forms, do_not_translate=g.do_not_translate, note=g.note)
            src_video = source_project.videos.get()
            v_key, v_sha = storage.save_file(storage.local_path(src_video.storage_key), ".mp4")
            video = Video.objects.create(
                project=project, original_name=src_video.original_name, storage_key=v_key, sha256=v_sha,
                duration_ms=src_video.duration_ms, container=src_video.container, codecs=src_video.codecs, size=src_video.size,
                status=Video.Status.ANALYZED, transcript_adapter=src_video.transcript_adapter,
                transcript_model=src_video.transcript_model, transcript_is_mock=src_video.transcript_is_mock,
                uploaded_by=actor)
            approved_ids = {i for sc in approval.snapshot["scenes"] for i in sc["translation_ids"]}
            approved = {t.segment_id: t for t in SegmentTranslation.objects.filter(pk__in=approved_ids)}
            tracks = {}
            for scene in Scene.objects.filter(video=src_video).order_by("index"):
                new_scene = Scene.objects.create(video=video, index=scene.index, start_ms=scene.start_ms, end_ms=scene.end_ms)
                for seg in scene.segments.order_by("index"):
                    label = seg.speaker_track.label if seg.speaker_track else "Speaker 1"
                    if label not in tracks:
                        # Only this owner's own speaker keeps the identity link (review #6).
                        src_owner = seg.speaker_track.identity_owner_id if seg.speaker_track else None
                        tracks[label] = SpeakerTrack.objects.create(video=video, label=label,
                                                                    identity_owner=owner if src_owner == owner.pk else None,
                                                                    assigned_by=actor)
                    new_seg = Segment.objects.create(scene=new_scene, speaker_track=tracks[label], index=seg.index,
                                                     start_ms=seg.start_ms, end_ms=seg.end_ms, source_text=seg.source_text,
                                                     asr_confidence=seg.asr_confidence)
                    t = approved.get(seg.pk)
                    if t:
                        loc.save_translation(new_loc, new_seg, actor=t.created_by, origin=t.origin, subtitle_text=t.subtitle_text,
                                             speech_text=t.speech_text, adaptation_type=t.adaptation_type, rationale=t.rationale,
                                             adapter=t.adapter, model=t.model, prompt_version=t.prompt_version,
                                             is_fallback=t.is_fallback, is_mock=t.is_mock, context_inputs=t.context_inputs)
                Scene.objects.filter(pk=new_scene.pk).update(status=Scene.Status.TRANSLATED)
            # Derived consent: never wider than the parent, and never remote (ADR 0020 §3, B1).
            pc = services.grant_project_consent(
                actor, owner, project, uses=[u for u in st.uses if u == Use.VOICE_SYNTHESIS], languages=[language],
                processors=[p for p in st.processors if p not in REMOTE_VOICE_PROCESSORS], expires_at=st.expires_at,
                reason=Consent.GrantReason.DEMO_RESET)
            check = services.require_active_consent(owner, Use.VOICE_SYNTHESIS, project, language, checkpoint="CP1-reset")
            source_profile = (VoiceProfile.objects.filter(identity_owner=owner, consent__project=source_project)
                              .order_by("-pk").first())
            clip_key, clip_sha = storage.save_file(storage.local_path(seed.storage_key), ".wav")
            profile = VoiceProfile.objects.create(identity_owner=owner, consent_id=check.consent_id, storage_key=clip_key,
                                                  transcript=source_profile.transcript if source_profile else "", language=language,
                                                  sha256=clip_sha, duration_ms=source_profile.duration_ms if source_profile else 0)
            audit.record(actor=actor, action="DEMO_RESET", entity=project, project_id=project.pk,
                         consent_version=f"{pc.pk}:v{pc.version}",
                         details={"source_project_id": source_project.pk, "approval_id": approval.pk, "seed_copy_id": seed.pk,
                                  "voice_profile_id": profile.pk, "triggered_by": actor.get_username()})
            for scene in Scene.objects.filter(video=video):
                transaction.on_commit(lambda s=scene: _render_later(s, new_loc))
            return project
    _refuse(actor, "DEMO_RESET_REFUSED", owner, problems, source_project.pk)


def _render_later(scene, localization):
    from hyperlocalize.rendering import services as rendering

    rendering.enqueue_render(scene, localization, reason="demo reset")


def register_offline_copy(actor, owner, file_path, *, kind=CopyKind.SCREEN_RECORDING, language=""):
    from hyperlocalize.projects.storage import get_storage

    _require_admin(actor)
    problems = []
    with transaction.atomic():
        owner = services.lock_owner(owner.pk)
        st = services.latest_standing(owner)
        if owner.withdrawn_at or st is None or st.status != Consent.Status.ACTIVE:
            problems.append("no active standing consent")
        else:
            if st.expires_at <= timezone.now():
                problems.append("the standing consent has expired")
            if Use.VOICE_SYNTHESIS not in st.uses:
                problems.append("the standing consent does not include voice_synthesis")
            if kind not in st.permitted_copy_kinds:
                problems.append(f"the standing consent does not permit {kind} copies")
        if not problems:
            key, sha = get_storage().save_offline_file(file_path, "." + str(file_path).rsplit(".", 1)[-1][:8])
            copy = OfflineCopy.objects.create(identity_owner=owner, consent_version=st, kind=kind, storage_key=key,
                                              language=language, sha256=sha)
            audit.record(actor=actor, action="OFFLINE_COPY_REGISTERED", entity=copy, consent_version=f"{st.pk}:v{st.version}",
                         details={"kind": kind, "sha256": sha})
            return copy
    _refuse(actor, "OFFLINE_COPY_REFUSED", owner, problems)
