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


def speech_room_ms(segment, scene, scene_segments):
    """Time the speech for `segment` may use: until the next segment of the same scene starts, or the scene
    ends (speech is mixed per scene and cut at its end). Used for the length budget and the overrun check."""
    later = [s.start_ms for s in scene_segments if s.start_ms > segment.start_ms]
    end = min(later) if later else scene.end_ms
    return max(end - segment.start_ms, 1)


def speech_budget(localization):
    """Characters per second the stock voice speaks at its normal rate, or None (no voice will speak, or its
    rate is unknown). ADR 0022: the budget uses the normal rate; the 1.2× cap is headroom for slower lines."""
    from hyperlocalize.accounts.models import Policy
    from hyperlocalize.pipeline.providers.base import chain_for, get_adapter

    if not Policy.get("synthesis_allowed"):
        return None
    language = rules.language_of(localization.target_locale)
    for name in chain_for("speech_stock"):
        adapter = get_adapter(name)
        if adapter and adapter.available():
            rate = getattr(adapter, "chars_per_second", None)
            if rate and language in getattr(adapter, "languages", ()):
                return rate
            return None
    return None


def build_request(localization, scenes, instruction=""):
    """One request for the segments of `scenes` (a scene or a list), with context from the whole video."""
    scenes = [scenes] if isinstance(scenes, Scene) else list(scenes)
    project = localization.project
    all_segments = list(Segment.objects.filter(scene__video=scenes[0].video).order_by("index")) if scenes else []
    position = {s.pk: n for n, s in enumerate(all_segments)}
    budget = speech_budget(localization)
    contexts = []
    for scene in scenes:
        scene_segments = list(scene.segments.order_by("index"))
        for seg in scene_segments:
            n = position[seg.pk]
            room = speech_room_ms(seg, scene, scene_segments)
            max_chars = max(1, int(room / 1000 * budget)) if budget else None
            contexts.append(SegmentContext(
                segment_id=seg.pk,
                source_text=seg.source_text,
                duration_ms=seg.duration_ms,
                speaker=seg.speaker_track.label if seg.speaker_track else "Speaker",
                previous_texts=[s.source_text for s in all_segments[max(0, n - WINDOW):n]],
                next_texts=[s.source_text for s in all_segments[n + 1:n + 1 + WINDOW]],
                room_ms=room,
                max_speech_chars=max_chars,
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


def hosted_llm_allowed(project):
    from hyperlocalize.projects.models import Project

    if project.data_classification == Project.DataClassification.PUBLISHED_PUBLIC:
        return bool(project.source_url and project.source_licence)  # provenance is a precondition (ADR 0021)
    return project.data_classification in Project.HOSTED_LLM_ALLOWED


def _data_use_rule(project):
    """ADR 0005 as amended by ADR 0021: free-tier hosted LLMs receive text only for team-authored scripted
    content or for published public content whose source and licence are recorded. Fails closed: an adapter
    that does not declare `requires_hosted_llm_permission` is treated as hosted."""
    def accept(adapter):
        if getattr(adapter, "requires_hosted_llm_permission", True) and not hosted_llm_allowed(project):  # fail closed
            return "skipped: project is not scripted team content or recorded published public content (data-use rule)"
        return None
    return accept


class TranslationPending(Exception):
    """A real translation provider failed (quota, rate limit, outage, bad output). Nothing was translated by
    a mock; the job is retried and the project page shows "translation pending" (ADR 0022)."""


# ADR 0022: one request per clip when it fits (the free tier allows about 20 requests a day per model).
BATCH_MAX_SEGMENTS = 80  # [IMPLEMENTATION CHOICE] a 5-minute clip has about 40–80 segments
BATCH_MAX_SOURCE_CHARS = 12000  # [IMPLEMENTATION CHOICE] keeps the reply well inside the model's output limit


def plan_batches(scenes):
    """Group consecutive scenes into as few requests as the limits allow; a scene is never split."""
    batches, current, segs, chars = [], [], 0, 0
    for scene in scenes:
        texts = list(scene.segments.values_list("source_text", flat=True))
        n, c = len(texts), sum(len(t) for t in texts)
        if current and (segs + n > BATCH_MAX_SEGMENTS or chars + c > BATCH_MAX_SOURCE_CHARS):
            batches.append(current)
            current, segs, chars = [], 0, 0
        current.append(scene)
        segs, chars = segs + n, chars + c
    if current:
        batches.append(current)
    return batches


def localize_scenes(localization, scenes, *, instruction="", actor=None, job_ctx=None):
    """Localize `scenes` in as few provider calls as possible, then run ONE batched meaning check.
    Returns {scene_id: [translations]} for the scenes that were translated. Raises TranslationPending
    (after saving the batches that succeeded) when a real provider failed."""
    done = {}
    for batch in plan_batches(scenes):
        if job_ctx:
            job_ctx.checkpoint(f"localizing scenes {batch[0].index + 1}–{batch[-1].index + 1}")
        try:
            saved = _localize_batch(localization, batch, instruction=instruction, job_ctx=job_ctx)
        except TranslationPending as exc:
            # A daily quota is shared by the meaning check: record CHECK_UNAVAILABLE without a doomed call.
            known = str(exc) if "QuotaExhausted" in str(exc) else ""
            run_meaning_checks([t for ts in done.values() for t in ts], localization, known_failure=known)
            raise
        for t in saved:
            done.setdefault(t.segment.scene_id, []).append(t)
    run_meaning_checks([t for ts in done.values() for t in ts], localization)
    return done


def localize_scene(localization, scene, *, instruction="", actor=None, job_ctx=None):
    """One scene (e.g. a reviewer's regeneration request)."""
    return localize_scenes(localization, [scene], instruction=instruction, actor=actor, job_ctx=job_ctx).get(scene.pk, [])


def _localize_batch(localization, scenes, *, instruction="", job_ctx=None):
    project = localization.project
    request = build_request(localization, scenes, instruction)
    if not request.segments:
        return []
    scene_id = scenes[0].pk if len(scenes) == 1 else None
    entity = scenes[0] if len(scenes) == 1 else localization
    try:
        outcome = run_chain("localization", lambda a: a.localize(request), accept=_data_use_rule(project))
    except NoProviderAvailable as exc:
        with transaction.atomic():  # commit the reasons before the job fails or retries
            _audit_skips(exc.skipped, "localization", project, entity=entity, scene_id=scene_id)
        if exc.provider_failed:
            reasons = "; ".join(f"{n}: {r}" for n, r in exc.skipped if r.startswith(_FAILURE_PREFIXES))
            raise TranslationPending(reasons[:500] or str(exc)[:500]) from None
        raise
    with transaction.atomic():
        _record_usage(outcome.adapter, "localization", project)
        _audit_chain_outcome(outcome, "localization", project, entity=entity, scene_id=scene_id)
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
            meaning_check=False,  # run once for the whole batch afterwards (ADR 0022)
        ))
    with transaction.atomic():
        for scene in scenes:
            s = Scene.objects.select_for_update().get(pk=scene.pk)
            s.status = Scene.Status.TRANSLATED
            s.save(update_fields=["status"])
    return saved


def save_translation(localization, segment, *, actor, origin, subtitle_text, speech_text, adaptation_type,
                     rationale="", uncertainty_flags=(), adapter, model="", prompt_version="", is_fallback=False,
                     is_mock=False, context_inputs=(), meaning_check=True):
    """Append a new version and run its checks (hard rules + AI flags). Never edits an old version.
    With meaning_check=False the caller runs one batched meaning check later (ADR 0022)."""
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
    if meaning_check:
        run_meaning_checks([t], localization)
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


def _speakable_check(t):
    """ADR 0021: catch a speech script the Tamil stock voice would refuse BEFORE rendering, as a blocking
    hard check. Runs only when MMS-TTS is the first available stock voice for a Tamil target."""
    from hyperlocalize.pipeline.providers import mms_tts
    from hyperlocalize.pipeline.providers.base import chain_for, get_adapter

    if rules.language_of(t.localization.target_locale) != "ta":
        return None
    first = next((n for n in chain_for("speech_stock") if get_adapter(n) and get_adapter(n).available()), None)
    if first != mms_tts.MmsTtsTamilStockVoiceProvider.name:
        return None
    problem = mms_tts.speakability_problem(t.speech_text)
    return (CheckResult.Status.FAIL, [problem]) if problem else (CheckResult.Status.PASS, [])


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
    speakable = _speakable_check(t)
    if speakable is not None:
        results["speech_speakable"] = speakable
    for check_type, (status, details) in results.items():
        CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.HARD, check_type=check_type,
                                   status=status, detail={"messages": details})


def run_meaning_checks(translations, localization, *, replacing=None, known_failure=""):
    """AI flags are advisory: they need acknowledgement, and they are never called verification.
    ONE provider call for all `translations` (ADR 0022). If a real provider fails, every segment without a
    result gets CHECK_UNAVAILABLE (blocking until re-run or acknowledged), never a mock PASS.
    `replacing`: earlier CHECK_UNAVAILABLE rows, deleted only in the transaction that writes the new results.
    `known_failure`: the provider is known to be out of quota; record CHECK_UNAVAILABLE without calling it."""
    if not translations:
        return
    project = localization.project
    items = [(t.pk, t.segment.source_text, t.subtitle_text) for t in translations]
    scene_ids = {t.segment.scene_id for t in translations}
    scene_id = next(iter(scene_ids)) if len(scene_ids) == 1 else None
    outcome, failure = None, None
    if known_failure:
        failure = NoProviderAvailable(f"No meaning_check provider called: {known_failure}", [], provider_failed=True)
    else:
        try:
            outcome = run_chain("meaning_check",
                                lambda a: a.check_batch(items, project.source_language, localization.target_locale),
                                accept=_data_use_rule(project))
        except NoProviderAvailable as exc:
            failure = exc
    with transaction.atomic():
        if failure is not None:
            already = set(replacing.values_list("segment_translation_id", flat=True)) if replacing is not None else set()
            for t in translations:
                if t.pk in already:
                    continue  # its CHECK_UNAVAILABLE row stays: nothing is deleted before a new result exists
                CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.AI_FLAG, check_type="meaning",
                                           status=CheckResult.Status.CHECK_UNAVAILABLE,
                                           detail={"messages": [str(failure)[:300]], "provider_failed": failure.provider_failed})
            _audit_skips(failure.skipped, "meaning_check", project, entity=localization, scene_id=scene_id)
            return
        if replacing is not None:
            replaced = list(replacing.values_list("pk", flat=True))
            replacing.delete()
            audit.record(actor=None, action="MEANING_CHECK_RETRIED", entity=localization, project_id=project.pk,
                         details={"translations": [t.pk for t in translations], "replaced_unavailable_results": replaced})
        _record_usage(outcome.adapter, "meaning_check", project)
        _audit_chain_outcome(outcome, "meaning_check", project, entity=localization, scene_id=scene_id)
        for t in translations:
            _save_meaning_result(t, outcome.result[t.pk], outcome.adapter)


def _save_meaning_result(t, result, adapter):
    meta = {"adapter": adapter.name, "is_mock": adapter.is_mock}
    if not result.flags:
        CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.AI_FLAG, check_type="meaning",
                                   status=CheckResult.Status.PASS, detail={"messages": [], **meta})
    for flag in result.flags:
        CheckResult.objects.create(segment_translation=t, kind=CheckResult.Kind.AI_FLAG, check_type=flag.flag_type.lower(),
                                   status=CheckResult.Status.FLAGGED, detail={"messages": [flag.explanation], **meta})


def missing_meaning_checks(localization, scenes=None):
    """Latest translations with NO meaning-check result at all (e.g. a crash between saving a batch and checking
    it). They block approval (ADR 0022 review #1): a line is never approved without its meaning check."""
    segments = Segment.objects.filter(scene__video__project=localization.project)
    if scenes is not None:
        segments = segments.filter(scene__in=scenes)
    current = latest_translations(localization, segments)
    checked = set(CheckResult.objects.filter(segment_translation__in=current.values(), kind=CheckResult.Kind.AI_FLAG)
                  .values_list("segment_translation_id", flat=True))
    return [t for t in current.values() if t.pk not in checked]


def retry_unavailable_meaning_checks(localization):
    """Re-run meaning checks for current versions whose check is CHECK_UNAVAILABLE (unresolved) or missing.
    The old unavailable rows are replaced only if the new call succeeds (same transaction)."""
    segments = Segment.objects.filter(scene__video__project=localization.project)
    current = latest_translations(localization, segments)
    stale = CheckResult.objects.filter(segment_translation__in=current.values(), check_type="meaning",
                                       status=CheckResult.Status.CHECK_UNAVAILABLE, resolution="")
    targets = {c.segment_translation_id for c in stale} | {t.pk for t in missing_meaning_checks(localization)}
    translations = sorted((t for t in current.values() if t.pk in targets), key=lambda t: t.pk)
    if translations:
        run_meaning_checks(translations, localization, replacing=stale)
    return len(translations)


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
