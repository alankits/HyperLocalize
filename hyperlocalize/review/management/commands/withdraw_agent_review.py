"""Withdraw governance actions an AI agent performed through user accounts (user rule, CLAUDE.md §11 c2).

For one project:
- every export becomes PURGED, and its package file is deleted;
- every VALID approval is invalidated;
- accepted scenes go back to IN_REVIEW;
- every resolved check is reopened;
- the project name is prefixed so nobody mistakes it for a reviewed project.

Earlier audit records are untouched (append-only, ADR 0007). One AGENT_REVIEW_WITHDRAWN record states what
was undone and why. Downloaded copies cannot be recalled (ADR 0006 §7).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from hyperlocalize.audit import services as audit
from hyperlocalize.exports.models import Export
from hyperlocalize.localization.models import CheckResult, Localization, Scene
from hyperlocalize.projects.models import Project
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.review import services as review

PREFIX = "[WITHDRAWN: agent test run, NOT human-reviewed] "


class Command(BaseCommand):
    help = "Withdraw agent-performed review, approval and export in one project (audited)."

    def add_arguments(self, parser):
        parser.add_argument("project_id", type=int)
        parser.add_argument("--reason", required=True)

    def handle(self, *args, project_id, reason, **options):
        reason = reason.strip()
        if not reason:
            raise CommandError("A reason is required.")
        storage = get_storage()
        with transaction.atomic():
            project = Project.objects.select_for_update().get(pk=project_id)
            purged = []
            for export in Export.objects.select_for_update().filter(approval__localization__project=project).order_by("pk"):
                if export.package_key and export.status != Export.Status.PURGED:
                    storage.delete(export.package_key)
                if export.status != Export.Status.PURGED:
                    export.status = Export.Status.PURGED
                    export.error = f"Withdrawn: {reason}"[:2000]
                    export.save(update_fields=["status", "error"])
                    purged.append(export.pk)
            invalidated = 0
            for loc in Localization.objects.filter(project=project):
                invalidated += review.invalidate_if_approved(loc, reason=f"Withdrawn: {reason}")
            scenes = Scene.objects.filter(video__project=project, status=Scene.Status.ACCEPTED).update(status=Scene.Status.IN_REVIEW)
            checks = (CheckResult.objects.filter(segment_translation__segment__scene__video__project=project)
                      .exclude(resolution="")
                      .update(resolution="", resolved_by=None, resolved_at=None, reason=""))
            if not project.name.startswith(PREFIX):
                project.name = (PREFIX + project.name)[:200]
                project.save(update_fields=["name"])
            audit.record(actor=None, action="AGENT_REVIEW_WITHDRAWN", entity=project, project_id=project.pk,
                         details={"reason": reason[:300], "exports_purged": purged, "approvals_invalidated": invalidated,
                                  "scenes_reopened": scenes, "checks_reopened": checks})
        self.stdout.write(self.style.SUCCESS(
            f"Project {project.pk}: exports purged {purged}, approvals invalidated {invalidated}, "
            f"scenes reopened {scenes}, checks reopened {checks}."))
