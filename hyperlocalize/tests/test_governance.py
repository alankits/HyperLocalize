"""User rule (CLAUDE.md §11 c2): agent-performed review, approval and export can be withdrawn, audited."""
import os

from django.core.management import call_command
from django.core.management.base import CommandError

from hyperlocalize.accounts.models import Policy
from hyperlocalize.audit import services as audit
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.exports import services as exports
from hyperlocalize.exports.models import Export
from hyperlocalize.localization import services as loc
from hyperlocalize.localization.models import CheckResult, Scene
from hyperlocalize.pipeline import jobs
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.review import services as review
from hyperlocalize.review.models import Approval

from .test_workflow import WorkflowBase


class WithdrawAgentReviewTests(WorkflowBase):
    def exported(self):
        Policy.objects.create(key="synthesis_allowed", value=False)
        self.upload_and_process()
        self.humanise_all()
        self.resolve_open_checks()
        self.accept_all()
        review.approve(self.users["manager"], self.localization)
        export = exports.request_export(self.users["manager"], self.localization)
        jobs.drain()
        export.refresh_from_db()
        self.assertEqual(export.status, Export.Status.ACTIVE, export.error)
        return export

    def test_withdrawal_undoes_every_governance_action_and_is_audited(self):
        export = self.exported()
        package = get_storage().local_path(export.package_key)
        self.assertTrue(os.path.exists(package))
        self.assertTrue(CheckResult.objects.exclude(resolution="").exists())

        with self.captureOnCommitCallbacks(execute=True):  # the file is deleted only after the commit
            call_command("withdraw_agent_review", self.project.pk, reason="NOT human-reviewed (agent test run)")

        export.refresh_from_db()
        self.assertEqual(export.status, Export.Status.PURGED)
        self.assertFalse(os.path.exists(package))
        self.assertFalse(exports.can_download(export)[0])
        self.assertFalse(Approval.objects.filter(localization=self.localization, status="VALID").exists())
        self.localization.refresh_from_db()
        self.assertEqual(self.localization.status, "IN_REVIEW")
        self.assertFalse(Scene.objects.filter(video__project=self.project, status="ACCEPTED").exists())
        self.assertFalse(CheckResult.objects.exclude(resolution="").exists())
        self.assertTrue(loc.blocking_checks(self.localization))  # a human must look again before approval
        self.project.refresh_from_db()
        self.assertTrue(self.project.name.startswith("[WITHDRAWN: agent test run, NOT human-reviewed]"))
        rec = AuditRecord.objects.get(action="AGENT_REVIEW_WITHDRAWN")
        self.assertEqual(rec.details["exports_purged"], [export.pk])
        self.assertEqual(rec.details["reason"], "NOT human-reviewed (agent test run)")
        self.assertTrue(rec.details["reopened"] and all(r["resolved_by"] == "reviewer" for r in rec.details["reopened"]))
        self.assertTrue(audit.verify_chain()[0])

    def test_reason_is_required(self):
        with self.assertRaises(CommandError):
            call_command("withdraw_agent_review", self.project.pk, reason="  ")
