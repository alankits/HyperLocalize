"""End-to-end workflow tests: Project → Upload → Analyze → Localize → Preview → Review →
Regenerate → Approve → Export, with the safety gates. Uses MOCK providers and synthetic media."""
import json
import zipfile

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from hyperlocalize.accounts.models import Policy
from hyperlocalize.audit import services as audit
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.exports import services as exports
from hyperlocalize.exports.models import Export
from hyperlocalize.localization import services as loc
from hyperlocalize.localization.models import CheckResult, Localization, Scene, Segment
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.models import Job
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.rendering.models import RenderedScene
from hyperlocalize.review import services as review
from hyperlocalize.testing import MediaRootMixin, make_project, make_users, transcript_upload, video_upload

# Reviewer's human translations for the four transcript segments (keeps every number and unit).
HUMAN = [
    "ஒவ்வொரு நாளும் 2 ORS பொட்டலங்கள் கொடுங்கள்.",
    "கலவையை கொதிக்க வைக்க வேண்டாம்.",
    "ஒரு பொட்டலத்தை 1 L சுத்தமான தண்ணீரில் கலக்கவும்.",
    "உதவிக்கு ஒரு சுகாதார பணியாளரிடம் கேளுங்கள்.",
]


class WorkflowBase(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)
        self.localization = Localization.objects.get(project=self.project)

    def upload_and_process(self, transcript=True):
        video = projects.upload_video(self.users["operator"], self.project, video_upload(),
                                      transcript_upload() if transcript else None)
        done = jobs.drain()
        failed = [j for j in done if j.status != Job.Status.SUCCEEDED]
        self.assertFalse(failed, [(j.type, j.error) for j in failed])
        return video

    def humanise_all(self):
        for seg, text in zip(Segment.objects.filter(scene__video__project=self.project).order_by("index"), HUMAN):
            loc.edit_translation(self.users["reviewer"], seg, subtitle_text=text)
        jobs.drain()

    def resolve_open_checks(self):
        for check in loc.blocking_checks(self.localization):
            resolution = "OVERRIDDEN" if check.kind == "HARD" else "ACKNOWLEDGED"
            loc.resolve_check(self.users["reviewer"], check, resolution=resolution, reason="Checked by the reviewer against the source.")

    def accept_all(self):
        for scene in Scene.objects.filter(video__project=self.project):
            review.accept_scene(self.users["reviewer"], scene)


class AnalysisTests(WorkflowBase):
    def test_human_transcript_builds_segments_and_scenes(self):
        video = self.upload_and_process()
        video.refresh_from_db()
        self.assertEqual(video.status, "ANALYZED")
        self.assertEqual(video.transcript_adapter, "manual_transcript")
        self.assertFalse(video.transcript_is_mock)
        self.assertEqual(Segment.objects.filter(scene__video=video).count(), 4)
        # The shot cut at 6.0 s separates the scenes.
        scenes = list(Scene.objects.filter(video=video).order_by("index"))
        self.assertEqual(len(scenes), 2)
        self.assertEqual(scenes[0].end_ms, 6000)
        self.assertEqual(scenes[-1].end_ms, video.duration_ms)

    def test_localization_records_context_and_mock_provenance(self):
        self.upload_and_process()
        t = loc.latest_translations(self.localization, Segment.objects.all())
        first = next(iter(t.values()))
        self.assertTrue(first.is_mock)
        self.assertTrue(first.subtitle_text.startswith("[MOCK"))
        self.assertIn("audience_profile", first.context_inputs)
        self.assertIn("source_window", first.context_inputs)

    def test_previews_rendered_for_every_scene(self):
        self.upload_and_process()
        for scene in Scene.objects.all():
            self.assertEqual(scene.status, "IN_REVIEW")
            render = RenderedScene.objects.get(scene=scene)
            self.assertTrue(get_storage().exists(render.video_key))
            self.assertTrue(render.is_mock)  # mock speech and mock text

    def test_invalid_upload_rejected_and_nothing_stored(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        with self.assertRaises(ValidationError):
            projects.upload_video(self.users["operator"], self.project, SimpleUploadedFile("x.mp4", b"not a video"))
        self.assertFalse(self.project.videos.exists())

    def test_unauthorised_role_cannot_upload(self):
        with self.assertRaises(PermissionDenied):
            projects.upload_video(self.users["reviewer"], self.project, video_upload())
        with self.assertRaises(PermissionDenied):
            projects.upload_video(self.users["outsider"], self.project, video_upload())


class ChecksAndReviewTests(WorkflowBase):
    def setUp(self):
        super().setUp()
        self.upload_and_process()

    def test_mock_output_fails_hard_checks(self):
        # Mock "translations" are the source text: the untranslated rule must catch them.
        blocking = loc.blocking_checks(self.localization)
        self.assertTrue(any(c.check_type == "structure" for c in blocking))

    def test_scene_cannot_be_accepted_with_open_checks(self):
        scene = Scene.objects.first()
        with self.assertRaises(ValidationError):
            review.accept_scene(self.users["reviewer"], scene)

    def test_override_needs_a_reason_and_reviewer_role(self):
        check = loc.blocking_checks(self.localization)[0]
        with self.assertRaises(ValidationError):
            loc.resolve_check(self.users["reviewer"], check, resolution="OVERRIDDEN", reason="")
        with self.assertRaises(PermissionDenied):
            loc.resolve_check(self.users["manager"], check, resolution="OVERRIDDEN", reason="looks fine to me")

    def test_number_mismatch_blocks(self):
        seg = Segment.objects.order_by("index").first()
        loc.edit_translation(self.users["reviewer"], seg, subtitle_text="ஒவ்வொரு நாளும் 3 ORS பொட்டலங்கள் கொடுங்கள்.")
        latest = loc.latest_translations(self.localization, [seg])[seg.pk]
        numbers = latest.checks.get(check_type="numbers")
        self.assertEqual(numbers.status, CheckResult.Status.FAIL)
        self.assertTrue(numbers.is_blocking)

    def test_ai_flag_needs_acknowledgement(self):
        seg = Segment.objects.order_by("index")[1]  # "Do not boil the mixture."
        t = loc.latest_translations(self.localization, [seg])[seg.pk]
        flag = t.checks.get(kind="AI_FLAG", check_type="negation")
        self.assertTrue(flag.is_blocking)
        with self.assertRaises(ValidationError):
            loc.resolve_check(self.users["reviewer"], flag, resolution="OVERRIDDEN", reason="Not appropriate here")

    def test_regenerate_one_scene_only(self):
        scenes = list(Scene.objects.order_by("index"))
        before = {s.pk: loc.latest_translations(self.localization, list(s.segments.all())) for s in scenes}
        review.request_changes(self.users["reviewer"], scenes[0], target="SCRIPT", reason="Too literal",
                               instruction="Use simpler words for a general audience.")
        jobs.drain()
        after0 = loc.latest_translations(self.localization, list(scenes[0].segments.all()))
        after1 = loc.latest_translations(self.localization, list(scenes[1].segments.all()))
        self.assertTrue(all(after0[k].version == before[scenes[0].pk][k].version + 1 for k in after0))
        self.assertEqual({k: v.pk for k, v in after1.items()}, {k: v.pk for k, v in before[scenes[1].pk].items()})
        self.assertIn("reviewer_instruction", next(iter(after0.values())).context_inputs)
        scenes[0].refresh_from_db()
        self.assertEqual(scenes[0].status, "IN_REVIEW")
        self.assertTrue(AuditRecord.objects.filter(action="REGENERATION_REQUESTED").exists())


class ApprovalAndExportTests(WorkflowBase):
    def setUp(self):
        super().setUp()
        self.upload_and_process()

    def test_approval_blocked_until_review_complete(self):
        with self.assertRaises(review.ApprovalBlocked) as cm:
            review.approve(self.users["manager"], self.localization)
        self.assertTrue(any("not accepted" in r for r in cm.exception.reasons))
        self.assertTrue(AuditRecord.objects.filter(action="APPROVAL_REFUSED").exists())

    def test_reviewer_cannot_approve(self):
        with self.assertRaises(PermissionDenied):
            review.approve(self.users["reviewer"], self.localization)

    def test_mock_output_can_never_be_exported(self):
        self.resolve_open_checks()
        self.accept_all()
        review.approve(self.users["manager"], self.localization)
        with self.assertRaises(exports.ExportRefused) as cm:
            exports.request_export(self.users["manager"], self.localization)
        self.assertIn("MOCK", str(cm.exception))
        self.assertTrue(AuditRecord.objects.filter(action="EXPORT_REFUSED").exists())

    def test_unapproved_project_cannot_export(self):
        with self.assertRaises(exports.ExportRefused):
            exports.request_export(self.users["manager"], self.localization)

    def test_separation_of_duties(self):
        Policy.objects.create(key="synthesis_allowed", value=False)
        self.humanise_all()
        self.resolve_open_checks()
        self.accept_all()
        from hyperlocalize.accounts.models import ProjectMembership

        # The reviewer is also made a manager: they edited, so they may not approve.
        ProjectMembership.objects.create(user=self.users["reviewer"], project=self.project, role="LOCALIZATION_MANAGER")
        with self.assertRaises(review.ApprovalBlocked) as cm:
            review.approve(self.users["reviewer"], self.localization)
        self.assertTrue(any("Separation of duties" in r for r in cm.exception.reasons))

    def test_full_path_to_export_with_human_text_and_subtitles_only(self):
        # Subtitles-only policy (ADR 0015) + human transcript + human translations: nothing is a mock.
        Policy.objects.create(key="synthesis_allowed", value=False)
        self.humanise_all()
        self.resolve_open_checks()
        self.accept_all()
        approval = review.approve(self.users["manager"], self.localization)
        export = exports.request_export(self.users["manager"], self.localization)
        jobs.drain()
        export.refresh_from_db()
        self.assertEqual(export.status, Export.Status.ACTIVE, export.error)
        with zipfile.ZipFile(get_storage().local_path(export.package_key)) as z:
            names = set(z.namelist())
            manifest = json.loads(z.read("evidence_manifest.json"))
        self.assertTrue({"localized_video.mp4", "subtitles.srt", "subtitles.vtt", "script.json",
                         "quality_report.json", "evidence_manifest.json"} <= names)
        self.assertEqual(manifest["approval"]["id"], approval.pk)
        self.assertIn("audit_chain_head", manifest)
        self.assertTrue(AuditRecord.objects.filter(action="EXPORT_CREATED").exists())
        self.assertTrue(audit.verify_chain()[0])
        self.localization.refresh_from_db()
        self.assertEqual(self.localization.status, "EXPORTED")

    def test_edit_after_approval_invalidates_it(self):
        Policy.objects.create(key="synthesis_allowed", value=False)
        self.humanise_all()
        self.resolve_open_checks()
        self.accept_all()
        approval = review.approve(self.users["manager"], self.localization)
        seg = Segment.objects.order_by("index").first()
        loc.edit_translation(self.users["reviewer"], seg, subtitle_text=HUMAN[0] + " ")
        approval.refresh_from_db()
        self.assertEqual(approval.status, "INVALIDATED")
        with self.assertRaises(exports.ExportRefused):
            exports.request_export(self.users["manager"], self.localization)
