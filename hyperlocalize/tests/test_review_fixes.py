"""Regression tests for the independent code review of 2026-10-06 (consent / identity / audit).
Each test names the finding it pins down. MOCK voices only."""
import os
import threading
import time
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from hyperlocalize.accounts.models import Policy
from hyperlocalize.exports import services as exports
from hyperlocalize.identity import demo
from hyperlocalize.identity import services as identity
from hyperlocalize.identity.models import IdentityOwner, VoiceProfile
from hyperlocalize.localization import services as loc
from hyperlocalize.localization.models import Localization, Scene, Segment
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.models import Job
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.models import SpeakerTrack
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.rendering import services as rendering
from hyperlocalize.rendering.models import RenderedScene, SynthesisedSegment
from hyperlocalize.review import services as review
from hyperlocalize.testing import (
    AuditSafeTransactionTestCase,
    MediaRootMixin,
    make_owner_with_consent,
    make_project,
    make_users,
    transcript_upload,
    video_upload,
)

from .test_identity_workflow import reference_clip
from .test_workflow import HUMAN

TWO_SPEAKERS = """WEBVTT

00:00:00.500 --> 00:00:02.500
Asha: Give 2 sachets of ORS every day.

00:00:03.000 --> 00:00:05.000
Ravi: Do not boil the mixture.

00:00:07.000 --> 00:00:09.500
Asha: Mix one packet in 1 litre of clean water.

00:00:10.000 --> 00:00:11.500
Ravi: Ask a health worker for help.
"""


class Base(MediaRootMixin):
    def build(self, transcript=None, purposes=("STANDARD",)):
        self.users = make_users()
        self.project = make_project(self.users)
        self.loc = Localization.objects.get(project=self.project)
        projects.upload_video(self.users["operator"], self.project, video_upload(),
                              transcript_upload(transcript) if transcript else transcript_upload())
        jobs.drain()
        self.owner = make_owner_with_consent(self.users, self.project, purposes=purposes)
        identity.create_voice_profile(self.users["speaker"], self.owner, self.project, reference_clip(),
                                      transcript="reference words", language="ta")

    def link_and_render(self, track_label=None):
        tracks = SpeakerTrack.objects.filter(video__project=self.project)
        for t in tracks:
            if track_label is None or t.label == track_label:
                projects.assign_speaker(self.users["operator"], t, self.owner)
        for scene in Scene.objects.filter(video__project=self.project):
            rendering.enqueue_render(scene, self.loc)
        jobs.drain()


class GrantPathTests(Base, TestCase):
    def setUp(self):
        self.build()

    def test_1_regrant_cannot_narrow_standing_consent(self):
        st = identity.latest_standing(self.owner)
        with self.assertRaises(ValidationError):
            identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=[],
                                            processors=[], expires_at=st.expires_at, evidence_ref="FORM-9")
        with self.assertRaises(ValidationError):
            identity.grant_standing_consent(self.users["speaker"], self.owner, uses=["voice_synthesis"],
                                            permitted_purposes=["STANDARD"], permitted_copy_kinds=[], languages=["ta"],
                                            processors=[], expires_at=st.expires_at - timedelta(days=1), evidence_ref="FORM-9")

    def test_1_regrant_cannot_narrow_project_consent(self):
        pc = identity.latest_project_consent(self.owner, self.project)
        with self.assertRaises(ValidationError):
            identity.grant_project_consent(self.users["speaker"], self.owner, self.project, uses=["voice_synthesis"],
                                           languages=["ta"], processors=[], expires_at=pc.expires_at - timedelta(days=1))


class CascadeTests(Base, TestCase):
    def setUp(self):
        self.build()
        self.link_and_render()

    def test_2_purge_is_not_cancelled_by_a_later_narrowing(self):
        identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
        purge = Job.objects.get(type="purge_identity_data", status="QUEUED")
        st = identity.latest_standing(self.owner)
        identity.narrow_standing_consent(self.users["speaker"], self.owner, expires_at=st.expires_at - timedelta(days=1))
        purge.refresh_from_db()
        self.assertEqual(purge.status, "QUEUED")

    def test_3_profile_decided_at_revocation_not_reused_after_regrant(self):
        old = VoiceProfile.objects.get(identity_owner=self.owner)
        identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
        old.refresh_from_db()
        self.assertEqual(old.status, "DELETED")  # decided inside the revocation transaction
        st = identity.latest_standing(self.owner)
        identity.grant_project_consent(self.users["speaker"], self.owner, self.project, uses=["voice_synthesis"],
                                       languages=["ta"], processors=[], expires_at=st.expires_at)
        mode, profile, _check, note = rendering.resolve_mode(SpeakerTrack.objects.get(), self.project, "ta")
        self.assertEqual(mode, "STOCK_VOICE")
        self.assertIn("no active voice profile", note)
        jobs.drain()
        self.assertFalse(get_storage().exists(old.storage_key))

    def test_4_harmless_narrowing_keeps_work_valid(self):
        render = RenderedScene.objects.filter(rendering_modes__isnull=False).exclude(consent_versions=[]).first()
        st = identity.latest_standing(self.owner)
        identity.narrow_standing_consent(self.users["speaker"], self.owner, expires_at=st.expires_at - timedelta(days=1))
        render.refresh_from_db()
        self.assertEqual(render.status, "ACTIVE")
        self.assertFalse(Job.objects.filter(type="render_scene", cancel_reason="CONSENT_REVOKED").exists())
        self.client.force_login(self.users["reviewer"])
        resp = self.client.get(reverse("review:preview_video", args=[render.pk]))
        self.assertEqual(resp.status_code, 200)
        b"".join(resp.streaming_content)
        self.assertFalse(any("Consent" in p for p in review.approval_problems(self.users["manager"], self.loc)))

    def test_8_expiry_sweep_skips_a_consent_that_is_not_expired(self):
        st = identity.latest_standing(self.owner)
        same = identity.narrow_standing_consent(None, self.owner, reason="EXPIRED")
        self.assertEqual(same.pk, st.pk)
        self.assertEqual(identity.latest_standing(self.owner).status, "ACTIVE")


class ScopeTests(Base, TestCase):
    def test_7_revocation_does_not_touch_exports_without_that_voice(self):
        self.users = make_users()
        self.project = make_project(self.users)
        self.loc = Localization.objects.get(project=self.project)
        Policy.objects.create(key="synthesis_allowed", value=False)
        projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
        jobs.drain()
        for seg, text in zip(Segment.objects.order_by("index"), HUMAN):
            loc.edit_translation(self.users["reviewer"], seg, subtitle_text=text)
        jobs.drain()
        for check in loc.blocking_checks(self.loc):
            loc.resolve_check(self.users["reviewer"], check, resolution="OVERRIDDEN" if check.kind == "HARD" else "ACKNOWLEDGED",
                              reason="checked against the source")
        for scene in Scene.objects.all():
            review.accept_scene(self.users["reviewer"], scene)
        review.approve(self.users["manager"], self.loc)
        export = exports.request_export(self.users["manager"], self.loc)
        jobs.drain()
        export.refresh_from_db()
        self.assertEqual(export.status, "ACTIVE")
        owner = make_owner_with_consent(self.users, self.project)  # an owner whose voice is in no export
        identity.revoke_project_consent(self.users["speaker"], owner, self.project)
        jobs.drain()
        export.refresh_from_db()
        self.assertEqual(export.status, "ACTIVE")
        self.assertTrue(get_storage().exists(export.package_key))

    def test_12_other_project_revocation_after_drain(self):
        self.build()
        self.link_and_render()
        other = projects.create_project(self.users["manager"], name="Other", source_language="en", target_locale="ta-IN")
        identity.grant_project_consent(self.users["speaker"], self.owner, other, uses=["voice_synthesis"], languages=["ta"],
                                       processors=[], expires_at=identity.latest_standing(self.owner).expires_at)
        identity.revoke_project_consent(self.users["speaker"], self.owner, other)
        jobs.drain()  # let the purge run
        self.assertEqual(VoiceProfile.objects.get(consent__project=self.project).status, "ACTIVE")
        self.assertFalse(SynthesisedSegment.objects.exclude(status="ACTIVE").exists())


class DemoSpeakerTests(Base, TestCase):
    def test_6_reset_links_only_the_owners_own_speaker(self):
        self.build(transcript=TWO_SPEAKERS, purposes=("STANDARD", "DEMO_REHEARSAL"))
        self.link_and_render(track_label="Asha")
        for check in loc.blocking_checks(self.loc):
            loc.resolve_check(self.users["reviewer"], check, resolution="OVERRIDDEN" if check.kind == "HARD" else "ACKNOWLEDGED",
                              reason="checked for the test")
        for scene in Scene.objects.filter(video__project=self.project):
            review.accept_scene(self.users["reviewer"], scene)
        review.approve(self.users["manager"], self.loc)
        demo.build_demo_seed(self.users["admin"], self.project, self.owner)
        new = demo.demo_reset(self.users["admin"], self.project, self.owner)
        links = dict(SpeakerTrack.objects.filter(video__project=new).values_list("label", "identity_owner_id"))
        self.assertEqual(links, {"Asha": self.owner.pk, "Ravi": None})
        jobs.drain()
        self.assertEqual(VoiceProfile.objects.get(consent__project=self.project).status, "ACTIVE")  # source untouched


class ConcurrencyTests(Base, AuditSafeTransactionTestCase):
    def test_12_two_owner_scene_job_is_stopped(self):
        """The job carries no single identity_owner, so only the scene-level cancel and CP4 can stop it."""
        self.build(transcript=TWO_SPEAKERS)
        other_user = self.users["outsider"]
        ravi = IdentityOwner.objects.create(name="Ravi (test)", user=other_user)
        st_exp = timezone.now() + timedelta(days=30)
        identity.grant_standing_consent(other_user, ravi, uses=["voice_synthesis"], permitted_purposes=["STANDARD"],
                                        permitted_copy_kinds=[], languages=["ta"], processors=[], expires_at=st_exp,
                                        evidence_ref="FORM-R")
        identity.grant_project_consent(other_user, ravi, self.project, uses=["voice_synthesis"], languages=["ta"],
                                       processors=[], expires_at=st_exp)
        identity.create_voice_profile(other_user, ravi, self.project, reference_clip(), transcript="ravi words", language="ta")
        for t in SpeakerTrack.objects.filter(video__project=self.project):
            projects.assign_speaker(self.users["operator"], t, self.owner if t.label == "Asha" else ravi)
        scene = Scene.objects.order_by("index").first()
        job = rendering.enqueue_render(scene, self.loc)
        self.assertIsNone(job.identity_owner_id)
        os.environ["HL_MOCK_SYNTH_DELAY_MS"] = "4000"
        result = {}
        try:
            def worker():
                try:
                    result["job"] = jobs.work_once(["synthesis"])
                finally:
                    connection.close()

            thread = threading.Thread(target=worker)
            thread.start()
            deadline = time.monotonic() + 30
            while not Job.objects.filter(pk=job.pk, status="RUNNING").exists():
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.2)
            time.sleep(1.0)
            identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
            thread.join(timeout=40)
        finally:
            os.environ.pop("HL_MOCK_SYNTH_DELAY_MS", None)
        self.assertEqual(result["job"].status, "CANCELLED")
        self.assertFalse(SynthesisedSegment.objects.filter(consent__identity_owner=self.owner, status="ACTIVE").exists())

    def test_12_withdraw_while_reset_waits_for_the_lock(self):
        """ADR 0020 N1, order 1: a reset that waits for the owner lock behind a withdrawal must refuse."""
        from django.db import transaction

        self.build(purposes=("STANDARD", "DEMO_REHEARSAL"))
        self.link_and_render()
        for check in loc.blocking_checks(self.loc):
            loc.resolve_check(self.users["reviewer"], check, resolution="OVERRIDDEN" if check.kind == "HARD" else "ACKNOWLEDGED",
                              reason="checked for the test")
        for s in Scene.objects.filter(video__project=self.project):
            review.accept_scene(self.users["reviewer"], s)
        review.approve(self.users["manager"], self.loc)
        demo.build_demo_seed(self.users["admin"], self.project, self.owner)
        outcome = {}

        def reset():
            try:
                demo.demo_reset(self.users["admin"], self.project, self.owner)
                outcome["result"] = "created"
            except demo.DemoRefused:
                outcome["result"] = "refused"
            finally:
                connection.close()

        with transaction.atomic():
            identity.lock_owner(self.owner.pk)
            thread = threading.Thread(target=reset)
            thread.start()
            time.sleep(1.0)  # the reset is now blocked on the owner lock
            identity.withdraw(self.users["speaker"], self.owner)
        thread.join(timeout=30)
        self.assertEqual(outcome["result"], "refused")

    def test_12_reset_then_withdraw_leaves_no_live_copy(self):
        """ADR 0020 N1, order 2: a reset that commits first is fully purged by the later withdrawal."""
        self.build(purposes=("STANDARD", "DEMO_REHEARSAL"))
        self.link_and_render()
        for check in loc.blocking_checks(self.loc):
            loc.resolve_check(self.users["reviewer"], check, resolution="OVERRIDDEN" if check.kind == "HARD" else "ACKNOWLEDGED",
                              reason="checked for the test")
        for s in Scene.objects.filter(video__project=self.project):
            review.accept_scene(self.users["reviewer"], s)
        review.approve(self.users["manager"], self.loc)
        demo.build_demo_seed(self.users["admin"], self.project, self.owner)
        demo.demo_reset(self.users["admin"], self.project, self.owner)
        identity.withdraw(self.users["speaker"], self.owner)
        jobs.drain()
        storage = get_storage()
        self.assertFalse(VoiceProfile.objects.filter(identity_owner=self.owner, status="ACTIVE").exists())
        self.assertFalse(any(storage.exists(k) for k in VoiceProfile.objects.values_list("storage_key", flat=True)))
        self.assertFalse(SynthesisedSegment.objects.filter(consent__identity_owner=self.owner, status="ACTIVE").exists())
