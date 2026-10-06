"""UC9 Inspect Quality, Audit and Evidence (read-only)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from hyperlocalize.accounts.models import Role
from hyperlocalize.accounts.permissions import require_role
from hyperlocalize.localization.models import CheckResult
from hyperlocalize.projects.models import Project

from . import services
from .models import AuditRecord


@login_required
def project_audit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    require_role(request.user, project, Role.AUDITOR, Role.LOCALIZATION_MANAGER)
    action = request.GET.get("action", "")
    records = AuditRecord.objects.filter(project_id=project.pk).select_related("actor")
    hide_jobs = request.GET.get("jobs") != "1"
    if hide_jobs:
        records = records.exclude(action__startswith="JOB_")
    if action:
        records = records.filter(action=action)
    actions = sorted(set(AuditRecord.objects.filter(project_id=project.pk).values_list("action", flat=True)))
    ok, count, bad, message = services.verify_chain() if request.GET.get("verify") == "1" else (None, None, None, None)
    checks = CheckResult.objects.filter(segment_translation__localization__project=project)
    return render(request, "audit/project.html", {
        "project": project, "records": records.order_by("-seq")[:300], "actions": actions, "action": action,
        "hide_jobs": hide_jobs, "verify": {"ok": ok, "count": count, "bad": bad, "message": message},
        "head": services.chain_head(),
        "overrides": checks.filter(resolution="OVERRIDDEN").select_related("segment_translation__segment", "resolved_by"),
        "acks": checks.filter(resolution="ACKNOWLEDGED").count(),
    })
