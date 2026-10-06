"""Web layer: pages render, protected actions are refused over HTTP for the wrong role, and media
is served only through authorised, consent-checked views."""
from django.test import TestCase, override_settings
from django.urls import reverse

from hyperlocalize.identity import services as identity
from hyperlocalize.localization.models import Localization, Scene, Segment
from hyperlocalize.pipeline import jobs
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.models import SpeakerTrack
from hyperlocalize.rendering import services as rendering
from hyperlocalize.rendering.models import RenderedScene
from hyperlocalize.testing import MediaRootMixin, make_owner_with_consent, make_project, make_users, transcript_upload, video_upload

from .test_identity_workflow import reference_clip


class ViewTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)
        projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
        jobs.drain()
        self.scene = Scene.objects.order_by("index").first()

    def login(self, name):
        self.client.force_login(self.users[name])

    def test_anonymous_is_redirected_to_login(self):
        r = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("accounts:login"), r["Location"])

    def test_pages_render_for_members(self):
        for name in ("manager", "reviewer", "operator", "auditor"):
            self.login(name)
            for url in (reverse("projects:list"), reverse("projects:detail", args=[self.project.pk]),
                        reverse("projects:jobs", args=[self.project.pk]), reverse("review:scene", args=[self.scene.pk])):
                self.assertEqual(self.client.get(url).status_code, 200, (name, url))
        self.login("auditor")
        r = self.client.get(reverse("audit:project", args=[self.project.pk]) + "?verify=1")
        self.assertContains(r, "verified")

    def test_mock_badges_shown(self):
        self.login("reviewer")
        self.assertContains(self.client.get(reverse("review:scene", args=[self.scene.pk])), "MOCK")

    def test_outsider_gets_403(self):
        self.login("outsider")
        self.assertEqual(self.client.get(reverse("projects:detail", args=[self.project.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("review:scene", args=[self.scene.pk])).status_code, 403)

    def test_wrong_role_cannot_act_over_http(self):
        seg = Segment.objects.first()
        self.login("auditor")
        self.client.post(reverse("review:edit", args=[seg.pk]), {"subtitle_text": "x"})
        self.assertEqual(seg.translations.count(), 1)  # refused: still only the AI draft
        self.client.post(reverse("review:approve", args=[self.project.pk]))
        self.assertEqual(Localization.objects.get(project=self.project).approvals.count(), 0)
        self.assertEqual(self.client.get(reverse("audit:project", args=[self.project.pk])).status_code, 200)
        self.login("reviewer")
        self.assertEqual(self.client.get(reverse("audit:project", args=[self.project.pk])).status_code, 403)

    def test_reviewer_edit_over_http(self):
        seg = Segment.objects.first()
        self.login("reviewer")
        self.client.post(reverse("review:edit", args=[seg.pk]), {"subtitle_text": "ஒவ்வொரு நாளும் 2 ORS பொட்டலங்கள்."})
        self.assertEqual(seg.translations.count(), 2)
        self.assertEqual(seg.translations.order_by("-version").first().origin, "HUMAN")

    def test_preview_served_to_members_only(self):
        r = RenderedScene.objects.filter(scene=self.scene).first()
        self.login("reviewer")
        resp = self.client.get(reverse("review:preview_video", args=[r.pk]))
        self.assertEqual(resp.status_code, 200)
        b"".join(resp.streaming_content)
        self.login("outsider")
        self.assertEqual(self.client.get(reverse("review:preview_video", args=[r.pk])).status_code, 403)

    def test_cp10_revoked_preview_not_served(self):
        owner = make_owner_with_consent(self.users, self.project)
        identity.create_voice_profile(self.users["speaker"], owner, self.project, reference_clip(),
                                      transcript="reference words", language="ta")
        projects.assign_speaker(self.users["operator"], SpeakerTrack.objects.get(), owner)
        rendering.enqueue_render(self.scene, Localization.objects.get(project=self.project))
        jobs.drain()
        cloned = RenderedScene.objects.filter(scene=self.scene).order_by("-version").first()
        self.assertTrue(cloned.consent_versions)
        self.login("reviewer")
        ok = self.client.get(reverse("review:preview_video", args=[cloned.pk]))
        self.assertEqual(ok.status_code, 200)
        b"".join(ok.streaming_content)
        identity.revoke_project_consent(self.users["speaker"], owner, self.project)
        self.assertEqual(self.client.get(reverse("review:preview_video", args=[cloned.pk])).status_code, 410)

    def test_identity_owner_page_and_no_project_access(self):
        make_owner_with_consent(self.users, self.project)
        self.login("speaker")
        self.assertEqual(self.client.get(reverse("identity:consent")).status_code, 200)
        self.assertEqual(self.client.get(reverse("projects:detail", args=[self.project.pk])).status_code, 403)

    def test_policies_page_admin_only(self):
        self.login("manager")
        self.assertEqual(self.client.get(reverse("accounts:policies")).status_code, 403)
        self.login("admin")
        self.assertEqual(self.client.get(reverse("accounts:policies")).status_code, 200)


@override_settings(HL_LOGIN_MAX_FAILURES=3)
class LoginRateLimitTests(TestCase):
    def test_lockout_after_failures(self):
        make_users()
        url = reverse("accounts:login")
        for _ in range(3):
            self.client.post(url, {"username": "manager", "password": "wrong"})
        r = self.client.post(url, {"username": "manager", "password": "Test-pass-12345"})
        self.assertEqual(r.status_code, 429)


class AdminAndSweepTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)

    def test_only_manager_or_admin_invites_identity_owner(self):
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            identity.create_identity_owner(self.users["reviewer"], user=self.users["speaker"], name="X")
        owner = identity.create_identity_owner(self.users["manager"], user=self.users["speaker"], name="Speaker")
        self.assertFalse(owner.consents.exists())  # inviting grants nothing

    def test_periodic_sweeps_are_queued_once(self):
        first = jobs.enqueue_periodic()
        self.assertEqual({j.type for j in first}, {"consent_expiry_sweep", "retention_sweep"})
        self.assertEqual(jobs.enqueue_periodic(), [])
        self.assertTrue(all(j.status == "SUCCEEDED" for j in jobs.drain()))

    def test_retention_sweep_deletes_old_previews(self):
        from datetime import timedelta

        from django.utils import timezone

        projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
        jobs.drain()
        r = RenderedScene.objects.first()
        RenderedScene.objects.filter(pk=r.pk).update(created_at=timezone.now() - timedelta(days=31))
        from django.db import transaction

        with transaction.atomic():
            jobs.enqueue("retention_sweep")
        jobs.drain()
        r.refresh_from_db()
        self.assertEqual(r.status, "PURGED")
