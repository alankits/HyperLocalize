"""ADR 0005: when a real adapter is passed over, the audit trail says which one and why, for the
localization stage (per scene) and the meaning check (per segment). Found by the live Gemini trial
(docs/trials/2026-10-12-gemini-live-trial.md): a 404 left only a bare PROVIDER_FALLBACK, and
meaning-check fallbacks left nothing. The Gemini adapters are patched to fail; no network call is made."""
from unittest import mock

from django.test import TestCase, override_settings

from hyperlocalize.audit import services as audit
from hyperlocalize.audit.models import AuditRecord
from hyperlocalize.localization.models import CheckResult, Segment
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.models import Job
from hyperlocalize.pipeline.providers import base, gemini
from hyperlocalize.projects import services as projects
from hyperlocalize.testing import MediaRootMixin, make_project, make_users, transcript_upload, video_upload


def records(action, stage):
    return [r for r in AuditRecord.objects.filter(action=action).order_by("seq") if r.details.get("stage") == stage]


class ProviderAuditTests(MediaRootMixin, TestCase):
    def process(self, *, scripted=True):
        users = make_users()
        project = make_project(users, scripted=scripted)
        projects.upload_video(users["operator"], project, video_upload(), transcript_upload())
        jobs.drain()
        return project

    @override_settings(HL_GEMINI_API_KEY="test-key")
    def test_provider_failures_are_audited_with_their_reason(self):
        with mock.patch.object(gemini.GeminiLocalizationProvider, "localize",
                               side_effect=base.Unavailable("HTTP 404 from Gemini (check the key and model name)")), \
             mock.patch.object(gemini.GeminiMeaningCheckProvider, "check",
                               side_effect=base.QuotaExhausted("HTTP 429 from Gemini (daily quota used up)")):
            project = self.process()
        segments = Segment.objects.filter(scene__video__project=project).count()

        skipped = records("PROVIDER_SKIPPED", "localization")
        self.assertTrue(skipped)
        self.assertEqual(skipped[0].details["adapter"], "gemini_localization")
        self.assertTrue(skipped[0].details["reason"].startswith("Unavailable: HTTP 404"))
        self.assertEqual(len(records("PROVIDER_FALLBACK", "localization")), len(skipped))

        meaning_skipped = records("PROVIDER_SKIPPED", "meaning_check")
        self.assertEqual(len(meaning_skipped), segments)
        self.assertTrue(all(r.details["reason"].startswith("QuotaExhausted: HTTP 429") for r in meaning_skipped))
        self.assertTrue(all(r.details.get("segment_id") for r in meaning_skipped))
        fallbacks = records("PROVIDER_FALLBACK", "meaning_check")
        self.assertEqual(len(fallbacks), segments)
        self.assertEqual({r.details["adapter"] for r in fallbacks}, {"mock_meaning_check"})
        self.assertEqual(fallbacks[0].details["after"], ["gemini_meaning_check"])
        self.assertTrue(audit.verify_chain()[0])

    @override_settings(HL_GEMINI_API_KEY="")
    def test_unconfigured_adapter_is_not_a_skip_record_but_fallback_is(self):
        # "not configured" is the normal state without a key: only the fallback itself is audited.
        self.process()
        self.assertEqual(AuditRecord.objects.filter(action="PROVIDER_SKIPPED").count(), 0)
        self.assertTrue(records("PROVIDER_FALLBACK", "localization"))
        self.assertTrue(records("PROVIDER_FALLBACK", "meaning_check"))

    @override_settings(HL_GEMINI_API_KEY="test-key")
    def test_data_use_rule_skip_is_audited_for_both_stages(self):
        with mock.patch.object(gemini, "_post") as post:
            self.process(scripted=False)
        post.assert_not_called()  # personal-data project: nothing is sent to the free-tier LLM
        for stage in ("localization", "meaning_check"):
            skipped = records("PROVIDER_SKIPPED", stage)
            self.assertTrue(skipped, stage)
            self.assertTrue(all("data-use rule" in r.details["reason"] for r in skipped))


def fake_localize(req):
    return base.LocalizationResult([base.LocalizedSegment(s.segment_id, "சோதனை", "", "LITERAL") for s in req.segments],
                                   model="fake")


@override_settings(HYPERLOCALIZE_MODE="demo", HL_GEMINI_API_KEY="test-key")
class DemoModeProviderAuditTests(MediaRootMixin, TestCase):
    """Demo mode has no mocks, so a failing real adapter ends the chain (NoProviderAvailable).
    The skip reasons must still reach the audit log, not only the job error or the CheckResult."""

    def process(self, *, scripted=True):
        users = make_users()
        project = make_project(users, scripted=scripted)
        projects.upload_video(users["operator"], project, video_upload(), transcript_upload())
        return project, jobs.drain()

    def test_localization_chain_failure_audits_the_reason(self):
        with mock.patch.object(gemini.GeminiLocalizationProvider, "localize",
                               side_effect=base.QuotaExhausted("HTTP 429 from Gemini (daily quota used up)")):
            _, done = self.process()
        self.assertIn(Job.Status.FAILED, [j.status for j in done if j.type == "localize"])
        skipped = records("PROVIDER_SKIPPED", "localization")
        self.assertTrue(skipped)
        self.assertTrue(skipped[0].details["reason"].startswith("QuotaExhausted: HTTP 429"))
        self.assertTrue(audit.verify_chain()[0])

    def test_meaning_check_chain_failure_audits_the_reason(self):
        with mock.patch.object(gemini.GeminiLocalizationProvider, "localize", side_effect=fake_localize), \
             mock.patch.object(gemini.GeminiMeaningCheckProvider, "check",
                               side_effect=base.Unavailable("HTTP 503 from Gemini")):
            project, _ = self.process()
        unavailable = CheckResult.objects.filter(status=CheckResult.Status.CHECK_UNAVAILABLE).count()
        self.assertEqual(unavailable, Segment.objects.filter(scene__video__project=project).count())
        skipped = records("PROVIDER_SKIPPED", "meaning_check")
        self.assertEqual(len(skipped), unavailable)
        self.assertTrue(all(r.details["reason"].startswith("Unavailable: HTTP 503") for r in skipped))

    def test_data_use_rule_is_audited_when_nothing_else_can_run(self):
        with mock.patch.object(gemini, "_post") as post:
            self.process(scripted=False)
        post.assert_not_called()
        skipped = records("PROVIDER_SKIPPED", "localization")
        self.assertTrue(skipped)
        self.assertIn("data-use rule", skipped[0].details["reason"])
