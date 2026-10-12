"""UC2 analysis (segments → scenes) and UC3 context-aware localization with checks (ADR 0008, ADR 0016).

The localization stage receives explicit context: a window of neighbouring source
segments, the speaker, the audience profile, the glossary, the timing budget, and
any reviewer instruction. Visual / scene context is NOT used yet (not implemented);
the request structure lets new context sources be added without changing callers.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from hyperlocalize.accounts.models import Role
from hyperlocalize.accounts.permissions import require_role
from hyperlocalize.audit import services as audit
from hyperlocalize.pipeline.providers.base import (
    CHAIN_FALLTHROUGH,
    LocalizationRequest,
    NoProviderAvailable,
    SegmentContext,
    run_chain,
)

from . import checks as rules
from .models import CheckResult, Localization, Scene, Segment, SegmentTranslation

WINDOW = 2  # neighbouring segments on each side passed as context
SCENE_GAP_MS = 1500  # [IMPLEMENTATION CHOICE] a pause this long starts a new scene
SCENE_MAX_MS = 30000  # [IMPLEMENTATION CHOICE] scenes are split before they exceed this


# --------------------------------------------------------------------------- scenes

def plan_scenes(segments, duration_ms, shot_cuts=()):
    """Group segments into contiguous scenes. A boundary goes between two segments when a shot cut
    falls in the gap, the pause is long, or the scene would grow too long. Boundaries sit at the cut,
    else at the middle of the pause; the first scene starts at 0 and the last ends at the video end.
    Returns [(start_ms, end_ms, [segment indexes])]."""
    if not segments:
        return []
    groups = [[0]]
    for i in range(1, len(segments)):
        prev, seg = segments[i - 1], segments[i]
        gap_cut = any(prev.end_ms <= c <= seg.start_ms for c in shot_cuts)
        long_pause = seg.start_ms - prev.end_ms >= SCENE_GAP_MS
        too_long = seg.end_ms - segments[groups[-1][0]].start_ms > SCENE_MAX_MS
        if gap_cut or long_pause or too_long:
            groups.append([i])
        else:
            groups[-1].append(i)
    scenes = []
    start = 0
    for gi, group in enumerate(groups):
        last = segments[group[-1]]
        if gi + 1 < len(groups):
            nxt = segments[groups[gi + 1][0]]
            cuts = [c for c in shot_cuts if last.end_ms <= c <= nxt.start_ms]
            end = cuts[0] if cuts else (last.end_ms + nxt.start_ms) // 2
        else:
            end = max(duration_ms, last.end_ms)
        scenes.append((start, end, group))
        start = end
    return scenes


@transaction.atomic
def save_analysis(video, transcript, shot_cuts):
    """Store speakers, segments and scenes from a transcript (run by the analyze job)."""
    from hyperlocalize.projects.models import SpeakerTrack

    speakers = {}
    for label in dict.fromkeys(s.speaker for s in transcript.segments):
        speakers[label] = SpeakerTrack.objects.create(video=video, label=label)
    planned = plan_scenes(transcript.segments, video.duration_ms, shot_cuts)
    for scene_index, (start, end, members) in enumerate(planned):
        scene = Scene.objects.create(video=video, index=scene_index, start_ms=start, end_ms=end)
        for i in members:
            seg = transcript.segments[i]
            Segment.objects.create(
                scene=scene, speaker_track=speakers[seg.speaker], index=i, start_ms=seg.start_ms,
                end_ms=seg.end_ms, source_text=seg.text, asr_confidence=seg.confidence,
            )
    return len(planned)


# --------------------------------------------------------------------------- localization

def latest_translations(localization, segments):
    """{segment_id: latest SegmentTranslation} for the given segments."""
    out = {}
    for t in SegmentTranslation.objects.filter(localization=localization, segment__in=segments).order_by("segment_id", "-version"):
        out.setdefault(t.segment_id, t)
    return out


def build_request(localization, scene, instruction=""):
    project = localization.project
    all_segments = list(Segment.objects.filter(scene__video=scene.video).order_by("index"))
    position = {s.pk: n for n, s in enumerate(all_segments)}
    contexts = []
    for seg in scene.segments.order_by("index"):
        n = position[seg.pk]
        contexts.append(SegmentContext(
            segment_id=seg.pk,
            source_text=seg.source_text,
            duration_ms=seg.duration_ms,
            speaker=seg.speaker_track.label if seg.speaker_track else "Speaker",
            previous_texts=[s.source_text for s in all_segments[max(0, n - WINDOW):n]],
            next_texts=[s.source_text for s in all_segments[n + 1:n + 1 + WINDOW]],
        ))
    audience = project.audience
    return LocalizationRequest(
        source_language=project.source_language,
        target_locale=localization.target_locale,
        segments=contexts,
        audience={"locale": audience.locale, "formality": audience.formality, "reading_level": audience.reading_level,
                  "cultural_notes": audience.cultural_notes, "unit_conversions": audience.unit_conversions},
        glossary=glossary_entries(project),
        instruction=instruction,
    )


def glossary_entries(project):
    return [
        {"source_term": g.source_term, "target_term": g.target_term, "accepted_forms": g.accepted_forms,
         "do_not_translate": g.do_not_translate}
        for g in project.glossary.all()
    ]


def _data_use_rule(project):
    """ADR 0005: free-tier hosted LLMs receive text only for team-authored scripted content."""
    def accept(adapter):
        if getattr(adapter, "requires_scripted_team", False) and project.data_classification != "SCRIPTED_TEAM":
            return "skipped: project is not marked as scripted, team-authored content (data-use rule)"
        return None
    return accept


def localize_scene(localization, scene, *, instruction="", actor=None, job_ctx=None):
    """Run the localization chain for one scene and save new AI versions with their checks."""
    project = localization.project
    request = build_request(localization, scene, instruction)
    if not request.segments:
        return []
    try:
        outcome = run_chain("localization", lambda a: a.localize(request), accept=_data_use_rule(project))
    except NoProviderAvailable as exc:
        with transaction.atomic():  # commit the reasons before the job fails
            _audit_skips(exc.skipped, "localization", project, entity=scene, scene_id=scene.pk)
        raise
    with transaction.atomic():
        _record_usage(outcome.adapter, "localization", project)
        _audit_chain_outcome(outcome, "localization", project, entity=scene, scene_id=scene.pk)
    by_id = {s.segment_id: s for s in outcome.result.segments}
    saved = []
    for ctx in request.segments:
        if job_ctx:
            job_ctx.checkpoint(f"checking segment {ctx.segment_id}")
        item = by_id.get(ctx.segment_id)
        if item is None:
            raise ValidationError(f"provider returned no output for segment {ctx.segment_id}")
        segment = Segment.objects.get(pk=ctx.segment_id)
        saved.append(save_translation(
            localization, segment, actor=None, origin=SegmentTranslation.Origin.AI,
            subtitle_text=item.subtitle_text, speech_text=item.speech_text, adaptation_type=item.adaptation_type,
            rationale=item.rationale, uncertainty_flags=item.uncertainty_flags, adapter=outcome.adapter.name,
            model=outcome.result.model, prompt_version=request.prompt_version, is_fallback=outcome.is_fallback,
            is_mock=outcome.adapter.is_mock,
            context_inputs=request.context_inputs if outcome.result.uses_context else [],
        ))
    with transaction.atomic():
        s = Scene.objects.select_for_update().get(pk=scene.pk)
        s.status = Scene.Status.TRANSLATED
        s.save(update_fields=["status"])
    return saved


def save_translation(localization, segment, *, actor, origin, subtitle_text, speech_text, adaptation_type,
                     rationale="", uncertainty_flags=(), adapter, model="", prompt_version="", is_fallback=False,
                     is_mock=False, context_inputs=()):
    """Append a new version and run its checks (hard rules + AI flags). Never edits an old version."""
    project = localization.project
    with transaction.atomic():
        Localization.objects.select_for_update().get(pk=localization.pk)  # lock order: Localization first
        Segment.objects.select_for_update().get(pk=segment.pk)  # serialise version numbers per segment
        version = (SegmentTranslation.objects.filter(segment=segment, localization=localization)
                   .aggregate(m=Max("version"))["m"] or 0) + 1
        t = SegmentTranslation.objects.create(
            segment=segment, localization=localization, version=version, subtitle_text=subtitle_text.strip(),
            speech_text=(speech_text or subtitle_text).strip(), adaptation_type=adaptation_type, rationale=rationale,
            uncertainty_flags=list(uncertainty_flags), origin=origin, adapter=adapter, model=model,
            prompt_version=prompt_version, is_fallback=is_fallback, is_mock=is_mock, context_inputs=list(context_inputs),
            created_by=actor,
        )
        _run_hard_checks(t, project)
        audit.record(actor=actor, action="TRANSLATION_SAVED", entity=t, project_id=project.pk, scene_id=segment.scene_id,
                     details={"segment_id": segment.pk, "version": version, "origin": origin, "adapter": adapter,
                              "is_mock": is_mock, "is_fallback": is_fallback})
        from hyperlocalize.review import services as review

        review.invalidate_if_approved(localization, reason=f"new translation version for segment {segment.pk}")
    _run_meaning_check(t, project)
    return t


# Skip reasons worth an audit record: the data-use rule, and provider failures, which run_chain
# formats as "<exception class>: <message>". "not configured" skips are not audited (ADR 0005).
_FAILURE_PREFIXES = tuple(f"{cls.__name__}:" for cls in CHAIN_FALLTHROUGH)


def _audit_skips(skipped, stage, project, *, entity, scene_id, segment_id=None):
    """Audit why real adapters were passed over. Call inside a transaction."""
    extra = {"segment_id": segment_id} if segment_id else {}
    for name, reason in skipped:
        if "data-use rule" in reason or reason.startswith(_FAILURE_PREFIXES):
            audit.record(actor=None, action="PROVIDER_SKIPPED", entity=entity, project_id=project.pk, scene_id=scene_id,
                         details={"stage": stage, "adapter": name, "reason": reason[:200], **extra})


def _audit_chain_outcome(outcome, stage, project, *, entity, scene_id, segment_id=None):
    """Audit skips and whether a fallback ran (with the names it ran after). Call inside a transaction."""
    _audit_skips(outcome.skipped, stage, project, entity=entity, scene_id=scene_id, segment_id=segment_id)
    if outcome.is_fallback:
        extra = {"segment_id": segment_id} if segment_id else {}
        audit.record(actor=None, action="PROVIDER_FALLBACK", entity=entity, project_id=project.pk, scene_id=scene_id,
                     details={"stage": stage, "adapter": outcome.adapter.name,
                              "after": [name for name, _ in outcome.skipped], **extra})


def _record_usage(adapter, stage, project):
    """Free-quota ledger (ADR 0005): one request per call; mocks are not counted."""
    if not adapter.is_mock:
        from hyperlocalize.pipeline.models import ProviderUsage

        ProviderUsage.objects.create(adapter=adapter.name, stage=stage, units=1, unit_type="requests", project=project)


def _run_hard_checks(t, project):
    seg = t.segment
    results = rules.run_hard_checks(
        seg.source_text, t.subtitle_text, source_lang=project.source_language, target_locale=t.localization.target_locale,
        glossary=glossary_entries(project), conversions=project.audience.unit_conversions, duration_ms=seg.duration_ms,
    )
    if t.speech_text != t.subtitle_text:  # ADR 0008: the number check runs on both scripts
        sp = rules.check_numbers(seg.source_text, t.speech_text, project.source_language,
                                 rules.language_of(t.localization.target_locale))
        results["numbers_speech"] = sp
    for check_type, (status, details) in results.items():
        CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.HARD, check_type=check_type,
                                   status=status, detail={"messages": details})


def _run_meaning_check(t, project):
    """AI flags are advisory: they need acknowledgement, and they are never called verification."""
    try:
        outcome = run_chain("meaning_check", lambda a: a.check(t.segment.source_text, t.subtitle_text,
                                                               project.source_language, t.localization.target_locale),
                            accept=_data_use_rule(project))
    except NoProviderAvailable as exc:
        with transaction.atomic():
            CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.AI_FLAG, check_type="meaning",
                                       status=CheckResult.Status.CHECK_UNAVAILABLE, detail={"messages": [str(exc)[:300]]})
            _audit_skips(exc.skipped, "meaning_check", project, entity=t, scene_id=t.segment.scene_id,
                         segment_id=t.segment_id)
        return
    flags = outcome.result.flags
    with transaction.atomic():
        _record_usage(outcome.adapter, "meaning_check", project)
        _audit_chain_outcome(outcome, "meaning_check", project, entity=t, scene_id=t.segment.scene_id,
                             segment_id=t.segment_id)
        if not flags:
            CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.AI_FLAG, check_type="meaning",
                                       status=CheckResult.Status.PASS,
                                       detail={"messages": [], "adapter": outcome.adapter.name, "is_mock": outcome.adapter.is_mock})
        for flag in flags:
            CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.AI_FLAG, check_type=flag.flag_type.lower(),
                                       status=CheckResult.Status.FLAGGED,
                                       detail={"messages": [flag.explanation], "adapter": outcome.adapter.name,
                                               "is_mock": outcome.adapter.is_mock})


# --------------------------------------------------------------------------- reviewer actions

def edit_translation(actor, segment, *, subtitle_text, speech_text=""):
    """A reviewer's edit creates a HUMAN version (UC5). The scene preview is re-rendered."""
    localization = segment.scene.video.project.localizations.get()
    require_role(actor, localization.project, Role.REVIEWER)
    if not subtitle_text.strip():
        raise ValidationError("The localized text cannot be empty.")
    previous = latest_translations(localization, [segment]).get(segment.pk)
    t = save_translation(
        localization, segment, actor=actor, origin=SegmentTranslation.Origin.HUMAN, subtitle_text=subtitle_text,
        speech_text=speech_text or subtitle_text,
        adaptation_type=previous.adaptation_type if previous else SegmentTranslation.AdaptationType.ADAPTED,
        rationale="Edited by a reviewer.", adapter="human_edit",
    )
    from hyperlocalize.rendering import services as rendering

    with transaction.atomic():
        scene = Scene.objects.select_for_update().get(pk=segment.scene_id)
        if scene.status == Scene.Status.ACCEPTED:
            scene.status = Scene.Status.IN_REVIEW
            scene.save(update_fields=["status"])
        rendering.enqueue_render(scene, localization, actor=actor, reason="translation edited")
    return t


@transaction.atomic
def resolve_check(actor, check, *, resolution, reason):
    """Override a hard check (with a written reason) or acknowledge an AI flag (ADR 0008). Audited."""
    project = check.segment_translation.localization.project
    require_role(actor, project, Role.REVIEWER)
    check = CheckResult.objects.select_for_update().get(pk=check.pk)
    if check.resolution:
        raise ValidationError("This check is already resolved.")
    if check.kind == CheckResult.Kind.HARD and resolution != CheckResult.Resolution.OVERRIDDEN:
        raise ValidationError("A failed rule check is resolved by fixing the text or by an override with a reason.")
    if check.kind == CheckResult.Kind.AI_FLAG and resolution != CheckResult.Resolution.ACKNOWLEDGED:
        raise ValidationError("An AI flag is resolved by acknowledging it after reading the segment.")
    if not reason.strip() or len(reason.strip()) < 5:
        raise ValidationError("A written reason is required.")
    latest = latest_translations(check.segment_translation.localization, [check.segment_translation.segment]).get(
        check.segment_translation.segment_id)
    if latest.pk != check.segment_translation_id:
        raise ValidationError("This check belongs to an older version of the segment.")
    check.resolution, check.resolved_by, check.reason, check.resolved_at = resolution, actor, reason.strip(), timezone.now()
    check.save(update_fields=["resolution", "resolved_by", "reason", "resolved_at"])
    audit.record(actor=actor, action=f"CHECK_{resolution}", entity=check, project_id=project.pk,
                 scene_id=check.segment_translation.segment.scene_id,
                 details={"check_type": check.check_type, "status": check.status, "translation_id": check.segment_translation_id,
                          "reason_length": len(check.reason)})
    return check


def blocking_checks(localization, scenes=None):
    """Unresolved blocking checks on the LATEST version of each segment (ADR 0014 invariant 5)."""
    segments = Segment.objects.filter(scene__video__project=localization.project)
    if scenes is not None:
        segments = segments.filter(scene__in=scenes)
    latest = latest_translations(localization, segments)
    out = []
    for t in latest.values():
        out.extend(c for c in t.checks.all() if c.is_blocking)
    return out


def mark_scenes(scene_ids, status):
    with transaction.atomic():
        for scene in Scene.objects.select_for_update().filter(pk__in=scene_ids).order_by("pk"):
            scene.status = status
            scene.save(update_fields=["status"])


def require_reviewable(actor, scene):
    project = scene.video.project
    require_role(actor, project, Role.REVIEWER)
    if project.status != "ACTIVE":
        raise PermissionDenied("This project is archived.")
    return project.localizations.get()


def localization_for(project):
    return Localization.objects.get(project=project)
