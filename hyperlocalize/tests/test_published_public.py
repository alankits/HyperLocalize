"""ADR 0021: published public content (provenance required, hosted LLM allowed, provenance in the export
evidence), the MMS-TTS Tamil stock voice (text preparation, stock tier only) and the jobs-panel refresh."""
import json
import os
import tempfile
import unittest
import zipfile
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from hyperlocalize.accounts.models import Policy, ProjectMembership, Role
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.exports import services as exports
from hyperlocalize.exports.models import Export
from hyperlocalize.localization import services as loc
from hyperlocalize.localization.models import Localization
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.providers import mms_tts
from hyperlocalize.pipeline.providers.base import Unavailable, chain_for, get_adapter
from hyperlocalize.projects import services as projects
from hyperlocalize.projects.models import Project
from hyperlocalize.projects.storage import get_storage
from hyperlocalize.review import services as review
from hyperlocalize.testing import MediaRootMixin, make_project, make_users

from .test_workflow import WorkflowBase

SOURCE = {"source_url": "https://commons.wikimedia.org/wiki/File:Example.webm", "source_licence": "CC BY 3.0",
          "source_attribution": "Example Government Television"}


def published_project(users, **overrides):
    fields = dict(SOURCE, **overrides)
    project = projects.create_project(users["manager"], name="Published clip", source_language="en", target_locale="ta-IN",
                                      data_classification="PUBLISHED_PUBLIC", **fields)
    for name, role in [("manager2", Role.LOCALIZATION_MANAGER), ("reviewer", Role.REVIEWER),
                       ("operator", Role.MEDIA_OPERATOR), ("auditor", Role.AUDITOR)]:
        ProjectMembership.objects.create(user=users[name], project=project, role=role)
    return project


class ProvenanceTests(TestCase):
    def setUp(self):
        self.users = make_users()

    def test_published_public_requires_url_and_licence(self):
        for missing in ("source_url", "source_licence"):
            with self.subTest(missing=missing), self.assertRaises(ValidationError):
                published_project(self.users, **{missing: ""})

    def test_source_url_must_be_http(self):
        for bad in ("javascript:alert(1)", "ftp://example.org/x.webm", "commons.wikimedia.org/x"):
            with self.subTest(url=bad), self.assertRaises(ValidationError):
                published_project(self.users, source_url=bad)

    def test_unknown_classification_is_refused(self):
        with self.assertRaises(ValidationError):
            projects.create_project(self.users["manager"], name="x", source_language="en", target_locale="ta-IN",
                                    data_classification="ANYTHING")

    def test_provenance_is_stored_and_audited(self):
        project = published_project(self.users)
        self.assertEqual((project.source_url, project.source_licence, project.source_attribution),
                         (SOURCE["source_url"], SOURCE["source_licence"], SOURCE["source_attribution"]))
        details = AuditRecord.objects.get(action="PROJECT_CREATED", project_id=project.pk).details
        self.assertEqual(details["source_url"], SOURCE["source_url"])
        self.assertEqual(details["source_licence"], "CC BY 3.0")

    def test_other_classifications_do_not_keep_provenance(self):
        project = projects.create_project(self.users["manager"], name="p", source_language="en", target_locale="ta-IN",
                                          data_classification="PERSONAL", **SOURCE)
        self.assertEqual((project.source_url, project.source_licence), ("", ""))

    def test_hosted_llm_rule(self):
        published = published_project(self.users)
        personal = make_project(self.users, scripted=False)
        scripted = make_project(self.users, scripted=True)
        self.assertTrue(loc.hosted_llm_allowed(published))
        self.assertTrue(loc.hosted_llm_allowed(scripted))
        self.assertFalse(loc.hosted_llm_allowed(personal))
        # Provenance is a precondition, even if a row somehow lacks it.
        Project.objects.filter(pk=published.pk).update(source_licence="")
        published.refresh_from_db()
        self.assertFalse(loc.hosted_llm_allowed(published))

    def test_data_use_rule_skips_hosted_adapter_only_when_not_allowed(self):
        class Hosted:
            requires_hosted_llm_permission = True

        self.assertIsNone(loc._data_use_rule(published_project(self.users))(Hosted()))
        self.assertIn("data-use rule", loc._data_use_rule(make_project(self.users, scripted=False))(Hosted()))

    def test_no_derivatives_licence_is_refused(self):
        for lic in ("CC BY-ND 4.0", "CC BY-NC-ND 3.0", "NoDerivatives"):
            with self.subTest(licence=lic), self.assertRaisesRegex(ValidationError, "NoDerivatives"):
                published_project(self.users, source_licence=lic)

    def test_cc_by_requires_attribution(self):
        with self.assertRaisesRegex(ValidationError, "attribution"):
            published_project(self.users, source_attribution="")
        published_project(self.users, source_licence="Public domain (US federal work)", source_attribution="")

    def test_overlong_fields_are_a_form_error_not_a_crash(self):
        with self.assertRaisesRegex(ValidationError, "too long"):
            published_project(self.users, source_url="https://example.org/" + "a" * 600)

    def test_rule_fails_closed_for_undeclared_adapters(self):
        class Undeclared:
            pass

        self.assertIn("data-use rule", loc._data_use_rule(make_project(self.users, scripted=False))(Undeclared()))

    def test_every_localization_and_meaning_adapter_declares_the_flag(self):
        from hyperlocalize.pipeline.providers.base import registered

        for adapter in registered():
            if adapter.stage in ("localization", "meaning_check"):
                with self.subTest(adapter=adapter.name):
                    self.assertTrue(any("requires_hosted_llm_permission" in vars(c) for c in type(adapter).__mro__))

    def test_create_form_posts_provenance(self):
        self.client.force_login(self.users["manager"])
        r = self.client.post(reverse("projects:create"), dict(SOURCE, name="Form project", source_language="en",
                                                                target_locale="ta-IN", data_classification="PUBLISHED_PUBLIC"))
        project = Project.objects.get(name="Form project")
        self.assertRedirects(r, reverse("projects:detail", args=[project.pk]))
        self.assertEqual(project.source_licence, "CC BY 3.0")
        page = self.client.get(reverse("projects:detail", args=[project.pk]))
        self.assertNotContains(page, "Published source")  # shown with the video panel once a video exists

    def test_create_form_without_licence_shows_error_and_keeps_input(self):
        self.client.force_login(self.users["manager"])
        r = self.client.post(reverse("projects:create"), {"name": "No licence", "source_language": "en", "target_locale": "ta-IN",
                                                         "data_classification": "PUBLISHED_PUBLIC",
                                                         "source_url": SOURCE["source_url"]})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "licence or reuse permission")
        self.assertContains(r, SOURCE["source_url"])
        self.assertFalse(Project.objects.filter(name="No licence").exists())


class PublishedExportTests(WorkflowBase):
    def setUp(self):
        self.users = make_users()
        self.project = published_project(self.users)
        self.localization = Localization.objects.get(project=self.project)

    def test_export_evidence_includes_source_and_licence(self):
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
        with zipfile.ZipFile(get_storage().local_path(export.package_key)) as z:
            manifest = json.loads(z.read("evidence_manifest.json"))
        self.assertEqual(manifest["content_source"], {
            "data_classification": "PUBLISHED_PUBLIC", "source_url": SOURCE["source_url"],
            "licence_or_reuse_permission": "CC BY 3.0", "attribution": SOURCE["source_attribution"],
            "verified_by_system": False})
        with zipfile.ZipFile(get_storage().local_path(export.package_key)) as z:
            report = json.loads(z.read("quality_report.json"))
        meaning = [r for r in report if r["check_type"] == "meaning"]
        self.assertTrue(meaning)
        self.assertTrue(all(r["adapter"] == "mock_meaning_check" and r["is_mock"] for r in meaning))


class MmsTextTests(TestCase):
    VOCAB = set("அஆஇஈஉஊஎஏஐஒஓகஙசஜஞடணதநனபமயரறலளழவஷஸஹாிீுூெேைொோௌ் '")

    def test_tamil_text_passes_and_punctuation_becomes_space(self):
        self.assertEqual(mms_tts.prepare_text("கைகளை கழுவுங்கள். நன்றி!", self.VOCAB), "கைகளை கழுவுங்கள் நன்றி")

    def test_digits_are_refused_never_dropped(self):
        with self.assertRaisesRegex(mms_tts.UnspeakableText, "1 digit"):
            mms_tts.prepare_text("2 முறை", self.VOCAB)

    def test_latin_letters_are_refused(self):
        with self.assertRaisesRegex(mms_tts.UnspeakableText, "3 Latin"):
            mms_tts.prepare_text("ORS கரைசல்", self.VOCAB)

    def test_error_never_contains_the_text(self):
        with self.assertRaises(mms_tts.UnspeakableText) as cm:
            mms_tts.prepare_text("CDC 25", self.VOCAB)
        self.assertNotIn("CDC", str(cm.exception))
        self.assertNotIn("25", str(cm.exception))

    def test_aytham_is_the_only_documented_approximation(self):
        self.assertEqual(mms_tts.prepare_text("எஃப்", self.VOCAB), "எப்")
        with self.assertRaisesRegex(mms_tts.UnspeakableText, "1 other"):
            mms_tts.prepare_text("ஶ்ரீ", self.VOCAB)  # any other missing letter is still refused

    def test_empty_is_refused(self):
        with self.assertRaises(mms_tts.UnspeakableText):
            mms_tts.prepare_text(" ... ", self.VOCAB)


class SpeakableCheckTests(WorkflowBase):
    """The review-time hard check runs only when MMS-TTS is the stock voice that will run."""

    VOCAB = MmsTextTests.VOCAB

    def test_unspeakable_speech_script_is_a_blocking_hard_check(self):
        with mock.patch.object(mms_tts.MmsTtsTamilStockVoiceProvider, "available", return_value=True), \
                mock.patch.object(mms_tts, "vocabulary", return_value=self.VOCAB):
            from hyperlocalize.localization.models import CheckResult
            from hyperlocalize.pipeline.models import Job
            from hyperlocalize.testing import transcript_upload, video_upload

            projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
            jobs.drain()
            checks = CheckResult.objects.filter(check_type="speech_speakable")
            self.assertTrue(checks.exists())
            # MOCK translations are English text, which the Tamil voice cannot read: blocked at review time ...
            self.assertTrue(all(c.status == "FAIL" and c.kind == "HARD" for c in checks))
            self.assertTrue(any(c.check_type == "speech_speakable" for c in loc.blocking_checks(self.localization)))
            # ... and if a render is attempted anyway, it fails loudly and names the segment (nothing is dropped).
            failed = Job.objects.filter(type="render_scene", status="FAILED")
            if failed.exists():  # only when the real model is downloaded on this machine
                self.assertTrue(all(j.error.startswith("InferenceError: segment ") for j in failed))

    def test_no_check_when_mms_is_not_the_stock_voice(self):
        self.upload_and_process()
        from hyperlocalize.localization.models import CheckResult
        self.assertFalse(CheckResult.objects.filter(check_type="speech_speakable").exists())


class MmsAdapterTests(TestCase):
    def test_stock_tier_only(self):
        adapter = get_adapter("mms_tts_tamil")
        self.assertFalse(adapter.supports_cloning)
        self.assertIn("mms_tts_tamil", chain_for("speech_stock"))
        self.assertNotIn("mms_tts_tamil", chain_for("speech_cloned"))
        with self.assertRaises(Unavailable):
            adapter.synthesize("வணக்கம்", "ta", "/nonexistent.wav", reference_clip="/some/clip.wav")

    def test_tamil_only(self):
        with self.assertRaises(Unavailable):
            get_adapter("mms_tts_tamil").synthesize("hello", "hi", "/nonexistent.wav")

    def test_disabled_in_test_mode_by_default(self):
        if os.environ.get("HL_TEST_MMS") == "1":
            self.skipTest("real-model mode")
        self.assertFalse(get_adapter("mms_tts_tamil").available())


@unittest.skipUnless(os.environ.get("HL_TEST_MMS") == "1", "set HL_TEST_MMS=1 with the model downloaded")
class MmsRealModelTests(TestCase):
    def test_synthesises_tamil_speech_deterministically(self):
        adapter = get_adapter("mms_tts_tamil")
        self.assertTrue(adapter.available())
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
            ra = adapter.synthesize("உங்கள் கைகளை சோப்பு கொண்டு கழுவுங்கள்", "ta", a)
            adapter.synthesize("உங்கள் கைகளை சோப்பு கொண்டு கழுவுங்கள்", "ta", b)
            self.assertGreater(ra.duration_ms, 500)
            self.assertEqual(open(a, "rb").read(), open(b, "rb").read())


class JobsRefreshTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)
        self.client.force_login(self.users["manager"])
        self.url = reverse("projects:jobs", args=[self.project.pk])

    def test_polling_after_last_job_finishes_reloads_the_page(self):
        r = self.client.get(self.url + "?polling=1")
        self.assertEqual(r.headers.get("HX-Refresh"), "true")

    def test_first_load_does_not_reload(self):
        self.assertNotIn("HX-Refresh", self.client.get(self.url).headers)

    def test_no_reload_while_jobs_are_active(self):
        jobs.enqueue("retention_sweep", project=self.project)
        r = self.client.get(self.url + "?polling=1")
        self.assertNotIn("HX-Refresh", r.headers)
        self.assertContains(r, "polling=1")
