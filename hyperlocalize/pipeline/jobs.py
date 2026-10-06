"""Job queue services (ADR 0003).

States: QUEUED → RUNNING → SUCCEEDED | FAILED | CANCELLED; QUEUED → CANCELLED.
`cancel_requested` is a flag checked at checkpoints and in the 1-second wait loop.
Job state changes are audited; heartbeats are not.
Lock order (ADR 0003): IdentityOwner → Job → artefacts → AuditChainHead.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from hyperlocalize.audit import services as audit

from .models import Job, Lane

log = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=5)  # [PROPOSED] default (ADR 0003)
BACKOFF_SECONDS = (5, 30, 120)

# Job type → lane (ADR 0003).
LANES = {
    "analyze_video": Lane.DEFAULT,
    "localize": Lane.DEFAULT,
    "render_scene": Lane.SYNTHESIS,
    "build_export": Lane.DEFAULT,
    "purge_identity_data": Lane.DEFAULT,
    "consent_expiry_sweep": Lane.DEFAULT,
    "retention_sweep": Lane.DEFAULT,
}

PERIODIC = {"consent_expiry_sweep": timedelta(minutes=10), "retention_sweep": timedelta(hours=1)}


def enqueue_periodic(now=None):
    """Queue each periodic sweep if none is active and the last one is older than its interval."""
    now = now or timezone.now()
    queued = []
    for job_type, interval in PERIODIC.items():
        if active_jobs(type=job_type).exists():
            continue
        last = Job.objects.filter(type=job_type).order_by("-created_at").first()
        if last is None or last.created_at < now - interval:
            with transaction.atomic():
                queued.append(enqueue(job_type))
    return queued

HANDLERS = {}  # type → callable(job, ctx); filled by register_handler


class JobCancelled(Exception):
    """Raised at a checkpoint when cancellation was requested or consent no longer holds."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class TransientJobError(Exception):
    """A retryable failure (timeouts, rate limits, 5xx)."""


def register_handler(job_type, *, on_claim=None):
    def deco(fn):
        HANDLERS[job_type] = (fn, on_claim)
        return fn

    return deco


def _audit_state(job, actor=None, **details):
    audit.record(
        actor=actor,
        action=f"JOB_{job.status}",
        entity=job,
        project_id=job.project_id,
        scene_id=job.scene_id,
        details={"type": job.type, "attempts": job.attempts, **details},
    )


def enqueue(job_type, *, actor=None, payload=None, **targets):
    """Create a QUEUED job. Must run inside the caller's transaction."""
    job = Job.objects.create(type=job_type, lane=LANES[job_type], payload=payload or {}, **targets)
    _audit_state(job, actor)
    return job


def active_jobs(**filters):
    return Job.objects.filter(status__in=[Job.Status.QUEUED, Job.Status.RUNNING, Job.Status.DISPATCHED], **filters)


def request_cancel(job, reason, actor=None):
    """Flag a job for cancellation. A QUEUED job is cancelled at once. Caller holds any IdentityOwner lock."""
    job = Job.objects.select_for_update().get(pk=job.pk)
    if job.status == Job.Status.QUEUED:
        job.status = Job.Status.CANCELLED
        job.cancel_requested = True
        job.cancel_reason = reason
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "cancel_requested", "cancel_reason", "finished_at"])
        _audit_state(job, actor, reason=reason)
    elif job.status in (Job.Status.RUNNING, Job.Status.DISPATCHED) and not job.cancel_requested:
        job.cancel_requested = True
        job.cancel_reason = reason
        job.save(update_fields=["cancel_requested", "cancel_reason"])
    return job


def _next_candidates(lanes):
    now = timezone.now()
    qs = Job.objects.filter(status=Job.Status.QUEUED, lane__in=lanes).filter(
        models_q_run_after(now)
    )
    return list(qs.order_by("id").values_list("id", "identity_owner_id")[:20])


def models_q_run_after(now):
    from django.db.models import Q

    return Q(run_after__isnull=True) | Q(run_after__lte=now)


def claim(lanes):
    """Claim the next QUEUED job in these lanes, respecting the lock order. Returns a Job or None."""
    from hyperlocalize.identity.models import IdentityOwner

    for job_id, owner_id in _next_candidates(lanes):
        with transaction.atomic():
            if owner_id:
                IdentityOwner.objects.select_for_update().get(pk=owner_id)  # lock order: owner first
            job = Job.objects.select_for_update(skip_locked=True).filter(pk=job_id, status=Job.Status.QUEUED).first()
            if job is None:
                continue
            _fn, on_claim = HANDLERS.get(job.type, (None, None))
            if on_claim:
                refusal = on_claim(job)  # CP2: consent check in the same transaction (ADR 0006)
                if refusal:
                    job.status = Job.Status.CANCELLED
                    job.cancel_reason = refusal
                    job.finished_at = timezone.now()
                    job.save(update_fields=["status", "cancel_reason", "finished_at"])
                    _audit_state(job, reason=refusal, checkpoint="CP2")
                    continue
            job.status = Job.Status.RUNNING
            job.attempts += 1
            job.started_at = job.started_at or timezone.now()
            job.heartbeat_at = timezone.now()
            job.save(update_fields=["status", "attempts", "started_at", "heartbeat_at"])
            _audit_state(job)
            return job
    return None


class JobContext:
    """Passed to handlers: heartbeat, progress and cancellation checkpoints."""

    def __init__(self, job):
        self.job = job

    def heartbeat(self, progress=None):
        fields = {"heartbeat_at": timezone.now()}
        if progress is not None:
            fields["progress"] = progress[:200]
        Job.objects.filter(pk=self.job.pk).update(**fields)

    def cancel_requested(self):
        return Job.objects.filter(pk=self.job.pk, cancel_requested=True).exists()

    def checkpoint(self, progress=None):
        self.heartbeat(progress)
        if self.cancel_requested():
            reason = Job.objects.values_list("cancel_reason", flat=True).get(pk=self.job.pk)
            raise JobCancelled(reason or "CANCEL_REQUESTED")


def _finish(job, status, *, error="", reason=""):
    with transaction.atomic():
        job = Job.objects.select_for_update().get(pk=job.pk)
        job.status = status
        job.error = error[:4000]
        if reason:
            job.cancel_reason = reason
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error", "cancel_reason", "finished_at"])
        details = {"reason": reason} if reason else {}
        if error:
            details["error_type"] = error.split(":", 1)[0][:80]
        _audit_state(job, **details)
    return job


def run(job):
    """Run a claimed job to a final state. Never raises for handler errors."""
    fn, _ = HANDLERS[job.type]
    ctx = JobContext(job)
    try:
        fn(job, ctx)
    except JobCancelled as exc:
        return _finish(job, Job.Status.CANCELLED, reason=exc.reason)
    except TransientJobError as exc:
        if job.attempts < job.max_attempts:
            with transaction.atomic():
                j = Job.objects.select_for_update().get(pk=job.pk)
                j.status = Job.Status.QUEUED
                j.error = str(exc)[:4000]
                j.run_after = timezone.now() + timedelta(seconds=BACKOFF_SECONDS[min(j.attempts - 1, 2)])
                j.save(update_fields=["status", "error", "run_after"])
                _audit_state(j, retry=True)
            return j
        return _finish(job, Job.Status.FAILED, error=f"{type(exc).__name__}: {exc}")
    except Exception as exc:  # validation errors and bugs are terminal
        log.exception("job %s failed", job.pk)
        return _finish(job, Job.Status.FAILED, error=f"{type(exc).__name__}: {exc}")
    return _finish(job, Job.Status.SUCCEEDED)


def recover_stale():
    """RUNNING jobs with an old heartbeat go back to QUEUED (if attempts remain) or FAILED."""
    cutoff = timezone.now() - STALE_AFTER
    for job in Job.objects.filter(status=Job.Status.RUNNING, heartbeat_at__lt=cutoff):
        with transaction.atomic():
            j = Job.objects.select_for_update(skip_locked=True).filter(pk=job.pk, status=Job.Status.RUNNING).first()
            if not j:
                continue
            if j.attempts < j.max_attempts and not j.cancel_requested:
                j.status = Job.Status.QUEUED
            else:
                j.status = Job.Status.CANCELLED if j.cancel_requested else Job.Status.FAILED
                j.finished_at = timezone.now()
            j.error = "stale heartbeat (worker stopped?)"
            j.save(update_fields=["status", "error", "finished_at"])
            _audit_state(j, stale=True)


def work_once(lanes):
    """Claim and run one job. Returns the job, or None if nothing was queued."""
    from . import handlers  # noqa: F401  (registers handlers)

    job = claim(lanes)
    if job is None:
        return None
    return run(job)


def drain(lanes=("default", "synthesis"), limit=500):
    """Run jobs until the queue is empty (tests and the synchronous dev helper)."""
    done = []
    for _ in range(limit):
        job = work_once(list(lanes))
        if job is None:
            break
        done.append(job)
    return done
