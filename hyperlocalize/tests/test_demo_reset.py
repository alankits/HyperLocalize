"""ADR 0020: demo reset by rebuild, the offline-copy register, and drift warnings. MOCK voices only."""
import tempfile

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from hyperlocalize.audit import services as audit
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.identity import demo
from hyperlocalize.identity import services as identity
from hyperlocalize.identity.models import Consent, OfflineCopy
from hyperlocalize.localization import services as loc
from hyperlocalize.localization.models import Localization, Scene
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.checks_report import drift_warnings
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.models import SpeakerTrack
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.rendering import services as rendering
from hyperlocalize.review import services as review
from hyperlocalize.testing import MediaRootMixin, make_owner_with_consent, make_project, make_users, transcript_upload, video_upload

from .test_identity_workflow import reference_clip


class DemoResetTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)
        self.loc = Localization.objects.get(project=self.project)
        projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
        jobs.drain()
        self.owner = make_owner_with_consent(self.users, self.project, purposes=("STANDARD", "DEMO_REHEARSAL"))
        identity.create_voice_profile(self.users["speaker"], self.owner, self.project, reference_clip(),
                                      transcript="reference words", language="ta")
        projects.assign_speaker(self.users["operator"], SpeakerTrack.objects.get(video__project=self.project), self.owner)
        for scene in Scene.objects.filter(video__project=self.project):
            rendering.enqueue_render(scene, self.loc)
        jobs.drain()
        for check in loc.blocking_checks(self.loc):
            loc.resolve_check(self.users["reviewer"], check, resolution="OVERRIDDEN" if check.kind == "HARD" else "ACKNOWLEDGED",
                              reason="checked for the demo test")
        for scene in Scene.objects.filter(video__project=self.project):
            review.accept_scene(self.users["reviewer"], scene)
        review.approve(self.users["manager"], self.loc)

    def seed(self):
        return demo.build_demo_seed(self.users["admin"], self.project, self.owner)

    def test_only_administrator_runs_demo_commands(self):
        with self.assertRaises(PermissionDenied):
            demo.build_demo_seed(self.users["manager"], self.project, self.owner)

    def test_reset_builds_new_rehearsal_project_and_only_appends(self):
        self.seed()
        before = audit.chain_head()
        new = demo.demo_reset(self.users["admin"], self.project, self.owner)
        self.assertEqual(new.purpose, "DEMO_REHEARSAL")
        self.assertTrue(audit.verify_chain()[0])
        self.assertGreater(audit.chain_head()["seq"], before["seq"])  # appended, nothing rewritten
        pc = identity.latest_project_consent(self.owner, new)
        self.assertEqual(pc.grant_reason, "DEMO_RESET")
        self.assertIsNone(pc.granted_by)
        self.assertNotIn("remote_voice_processing", pc.uses)  # test 17 (B1)
        self.assertIsNotNone(identity.evaluate(self.owner, "voice_synthesis", new, "ta")[0])
        self.assertTrue(AuditRecord.objects.filter(action="DEMO_RESET").exists())

    def test_reset_refuses_without_both_purposes(self):
        self.seed()
        identity.narrow_standing_consent(self.users["speaker"], self.owner, remove={"permitted_purposes": ["DEMO_REHEARSAL"]})
        with self.assertRaises(demo.DemoRefused):
            demo.demo_reset(self.users["admin"], self.project, self.owner)
        self.assertTrue(AuditRecord.objects.filter(action="DEMO_RESET_REFUSED").exists())  # written in its own transaction
        seed = OfflineCopy.objects.get(kind="DEMO_SEED_REFERENCE")
        self.assertEqual(seed.status, "DELETION_PENDING")  # the seed is useless without both purposes

    def test_reset_refuses_drifted_seed(self):
        copy = self.seed()
        with open(get_storage().local_path(copy.storage_key), "ab") as f:
            f.write(b"x")
        with self.assertRaises(demo.DemoRefused):
            demo.demo_reset(self.users["admin"], self.project, self.owner)

    def test_reset_refuses_withdrawn_owner_and_withdrawal_purges_seed(self):
        copy = self.seed()
        identity.withdraw(self.users["speaker"], self.owner)
        jobs.drain()
        copy.refresh_from_db()
        self.assertEqual(copy.status, "DELETED")
        self.assertFalse(get_storage().exists(copy.storage_key))
        with self.assertRaises(demo.DemoRefused):
            demo.demo_reset(self.users["admin"], self.project, self.owner)

    def test_rehearsal_revocation_leaves_source_and_seed_untouched(self):
        copy = self.seed()
        new = demo.demo_reset(self.users["admin"], self.project, self.owner)
        identity.revoke_project_consent(self.users["speaker"], self.owner, new)
        jobs.drain()
        copy.refresh_from_db()
        self.assertEqual(copy.status, "PRESENT")
        self.assertIsNotNone(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")[0])
        self.assertEqual(identity.latest_project_consent(self.owner, new).status, Consent.Status.REVOKED)
        again = demo.demo_reset(self.users["admin"], self.project, self.owner)  # the next reset derives a fresh grant
        self.assertNotEqual(again.pk, new.pk)

    def test_register_offline_copy_needs_permission(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            f.write(b"recording")
            f.flush()
            with self.assertRaises(demo.DemoRefused):
                demo.register_offline_copy(self.users["admin"], self.owner, f.name)

    def test_drift_warning_for_unregistered_offline_file(self):
        storage = get_storage()
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            f.write(b"stray")
            f.flush()
            storage.save_offline_file(f.name, ".wav")
        self.assertTrue(any("unregistered" in w for w in drift_warnings()))
