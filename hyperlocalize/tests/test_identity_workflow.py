"""Identity and consent inside the workflow (ADR 0006, ADR 0015, ADR 0020). MOCK voices only:
the "cloned" voice is a tone that imitates no one."""
import os
import tempfile
import threading
import time
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase

from hyperlocalize import media_tools
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.identity import services as identity
from hyperlocalize.identity.models import VoiceProfile
from hyperlocalize.localization.models import Localization, Scene
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.models import Job
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.models import SpeakerTrack
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.rendering.models import RenderedScene, SynthesisedSegment
from hyperlocalize.testing import (
    AuditSafeTransactionTestCase,
    MediaRootMixin,
    make_owner_with_consent,
    make_project,
    make_users,
    transcript_upload,
    video_upload,
)


def reference_clip(seconds=5):
    d = tempfile.mkdtemp()
    path = Path(d) / "ref.wav"
    media_tools._run([media_tools.ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}",
                      "-ac", "1", "-ar", "16000", str(path)])
    data = path.read_bytes()
    path.unlink()
    os.rmdir(d)
    return SimpleUploadedFile("ref.wav", data, content_type="audio/wav")


class IdentitySetup:
    def build(self, *, with_consent=True, with_profile=True):
        self.users = make_users()
        self.project = make_project(self.users)
        self.localization = Localization.objects.get(project=self.project)
        projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
        jobs.drain()
        if with_consent:
            self.owner = make_owner_with_consent(self.users, self.project)
            if with_profile:
                identity.create_voice_profile(self.users["speaker"], self.owner, self.project, reference_clip(),
                                              transcript="This is my reference sentence.", language="ta")
        else:
            from hyperlocalize.identity.models import IdentityOwner

            self.owner = IdentityOwner.objects.create(name="Unconsented owner", user=self.users["speaker"])
        track = SpeakerTrack.objects.get(video__project=self.project)
        projects.assign_speaker(self.users["operator"], track, self.owner)
        for scene in Scene.objects.filter(video__project=self.project):
            from hyperlocalize.rendering import services as rendering

            rendering.enqueue_render(scene, self.localization, reason="speaker assigned")


class ClonedRenderTests(MediaRootMixin, IdentitySetup, TestCase):
    def test_consented_speaker_gets_identity_preserving_mode(self):
        self.build()
        jobs.drain()
        render = RenderedScene.objects.filter(scene__video__project=self.project).order_by("-version").first()
        modes = {v["mode"] for v in render.rendering_modes.values()}
        self.assertEqual(modes, {"CLONED_VOICE"})
        self.assertTrue(render.consent_versions)
        syn = SynthesisedSegment.objects.filter(rendering_mode="CLONED_VOICE").first()
        self.assertEqual(syn.adapter, "mock_cloned_voice")
        self.assertTrue(syn.is_mock)

    def test_no_consent_falls_back_to_stock_voice(self):
        self.build(with_consent=False)
        jobs.drain()
        render = RenderedScene.objects.filter(scene__video__project=self.project).order_by("-version").first()
        mode = next(iter(render.rendering_modes.values()))
        self.assertEqual(mode["mode"], "STOCK_VOICE")
        self.assertIn("NO_CONSENT", mode["note"])
        self.assertFalse(SynthesisedSegment.objects.filter(rendering_mode="CLONED_VOICE").exists())

    def test_voice_profile_needs_consent(self):
        self.users = make_users()
        self.project = make_project(self.users)
        from hyperlocalize.identity.models import IdentityOwner

        owner = IdentityOwner.objects.create(name="O", user=self.users["speaker"])
        with self.assertRaises(identity.ConsentDenied):
            identity.create_voice_profile(self.users["speaker"], owner, self.project, reference_clip(),
                                          transcript="x y z", language="ta")
        self.assertFalse(VoiceProfile.objects.exists())

    def test_revocation_cascade_quarantines_purges_and_falls_back(self):
        self.build()
        jobs.drain()
        cloned = list(SynthesisedSegment.objects.filter(rendering_mode="CLONED_VOICE"))
        self.assertTrue(cloned)
        keys = [s.audio_key for s in cloned]
        identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
        for s in cloned:
            s.refresh_from_db()
            self.assertEqual(s.status, "QUARANTINED")
        self.assertTrue(Scene.objects.filter(status="NEEDS_REGENERATION").exists())
        jobs.drain()  # purge + fallback renders
        storage = get_storage()
        self.assertFalse(any(storage.exists(k) for k in keys))
        self.assertEqual(SynthesisedSegment.objects.filter(pk__in=[s.pk for s in cloned], status="PURGED").count(), len(cloned))
        self.assertEqual(VoiceProfile.objects.get().status, "DELETED")
        for scene in Scene.objects.filter(video__project=self.project):
            latest = RenderedScene.objects.filter(scene=scene).order_by("-version").first()
            self.assertEqual({v["mode"] for v in latest.rendering_modes.values()}, {"STOCK_VOICE"})
            self.assertEqual(scene.status, "IN_REVIEW")  # the fallback must be reviewed again
        self.assertTrue(AuditRecord.objects.filter(action="IDENTITY_DATA_PURGED").exists())

    def test_revocation_in_another_project_does_not_touch_this_one(self):
        self.build()
        jobs.drain()
        other = projects.create_project(self.users["manager"], name="Other", source_language="en", target_locale="ta-IN")
        identity.grant_project_consent(self.users["speaker"], self.owner, other, uses=["voice_synthesis"], languages=["ta"],
                                       processors=[], expires_at=identity.latest_standing(self.owner).expires_at)
        identity.revoke_project_consent(self.users["speaker"], self.owner, other)
        self.assertFalse(SynthesisedSegment.objects.exclude(status="ACTIVE").exists())
        self.assertIsNotNone(identity.evaluate(self.owner, "voice_synthesis", self.project, "ta")[0])


class MidJobRevocationTests(MediaRootMixin, IdentitySetup, AuditSafeTransactionTestCase):
    """Revocation lands while a cloned-voice job is running: the subprocess is killed, the job ends
    CANCELLED (CONSENT_REVOKED), and nothing in the cloned voice remains active."""

    def test_running_job_is_stopped_within_seconds(self):
        self.build()
        os.environ["HL_MOCK_SYNTH_DELAY_MS"] = "4000"
        try:
            result = {}

            def worker():
                try:
                    result["job"] = jobs.work_once(["synthesis"])
                finally:
                    connection.close()

            thread = threading.Thread(target=worker)
            thread.start()
            deadline = time.monotonic() + 30
            while not Job.objects.filter(type="render_scene", status="RUNNING").exists():
                self.assertLess(time.monotonic(), deadline, "render job never started")
                time.sleep(0.2)
            time.sleep(1.0)  # inside the slow synthesis call
            revoked_at = time.monotonic()
            identity.revoke_project_consent(self.users["speaker"], self.owner, self.project)
            thread.join(timeout=30)
            stopped_after = time.monotonic() - revoked_at
        finally:
            os.environ.pop("HL_MOCK_SYNTH_DELAY_MS", None)
        job = result["job"]
        self.assertEqual(job.status, "CANCELLED")
        self.assertEqual(job.cancel_reason, "CONSENT_REVOKED")
        self.assertLess(stopped_after, 8, "worker did not stop promptly")  # TEST BOUND, not a measured result
        self.assertFalse(SynthesisedSegment.objects.filter(rendering_mode="CLONED_VOICE", status="ACTIVE").exists())
