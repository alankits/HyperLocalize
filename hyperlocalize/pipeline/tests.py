import io
import json
import urllib.error
from unittest import mock

from django.test import TestCase, override_settings

from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.models import Job, ProviderConfig
from hyperlocalize.pipeline.providers import base, gemini
from hyperlocalize.pipeline.providers.base import LocalizationRequest, SegmentContext
from hyperlocalize.pipeline.providers.manual import parse_subtitles


def request():
    return LocalizationRequest("en", "ta-IN", [SegmentContext(7, "Give 2 sachets.", 2000, "Speaker 1", [], ["Next."])],
                               {"locale": "ta-IN"}, [{"source_term": "sachet", "target_term": "பொட்டலம்", "accepted_forms": [],
                                                      "do_not_translate": False}])


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_returning(text):
    payload = {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    return lambda req, timeout: FakeResponse(json.dumps(payload).encode())


def body_429(quota_id, retry_delay):
    """Shape of a real Gemini 429 body (captured 2026-10-12, trimmed; docs/trials/2026-10-12-gemini-live-trial.md).

    The PerDay quotaId was observed live. The PerMinute quotaId used below is by analogy, not observed.
    """
    return json.dumps({"error": {
        "code": 429, "status": "RESOURCE_EXHAUSTED",
        "message": "You exceeded your current quota, please check your plan and billing details.",
        "details": [
            {"@type": "type.googleapis.com/google.rpc.Help", "links": []},
            {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [
                {"quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
                 "quotaId": quota_id, "quotaValue": "20"}]},
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay},
        ]}}).encode()


def opener_429s(bodies, then=None):
    """An opener that answers HTTP 429 with each body in turn, then `then` (model text). Records call numbers."""
    calls = []

    def opener(req, timeout):
        calls.append(len(calls) + 1)
        if len(calls) <= len(bodies):
            raise urllib.error.HTTPError(req.full_url, 429, "Too many", {}, io.BytesIO(bodies[len(calls) - 1]))
        return opener_returning(then)(req, timeout)
    return opener, calls


class MockGatingTests(TestCase):
    @override_settings(HYPERLOCALIZE_MODE="demo")
    def test_mocks_are_never_available_in_demo_mode(self):
        self.assertIsNone(base.get_adapter("mock_localization"))
        self.assertFalse(any(a.is_mock for a in base.registered()))

    def test_mocks_available_in_test_mode(self):
        base.registered()
        self.assertTrue(base.get_adapter("mock_localization").is_mock)

    @override_settings(HYPERLOCALIZE_MODE="demo", HL_GEMINI_API_KEY="")
    def test_demo_mode_without_real_provider_fails_loudly(self):
        with self.assertRaises(base.NoProviderAvailable):
            base.run_chain("localization", lambda a: a.localize(request()))


class ChainTests(TestCase):
    def test_unconfigured_adapter_is_skipped_and_fallback_recorded(self):
        with override_settings(HL_GEMINI_API_KEY=""):
            outcome = base.run_chain("localization", lambda a: a.localize(request()))
        self.assertEqual(outcome.adapter.name, "mock_localization")
        self.assertTrue(outcome.is_fallback)
        self.assertEqual(outcome.skipped[0][0], "gemini_localization")

    def test_administrator_chain_order_is_used(self):
        ProviderConfig.objects.create(stage="localization", adapters=["mock_localization"])
        outcome = base.run_chain("localization", lambda a: a.localize(request()))
        self.assertFalse(outcome.is_fallback)

    def test_data_use_rule_skips_hosted_llm(self):
        with override_settings(HL_GEMINI_API_KEY="test-key"):
            outcome = base.run_chain("localization", lambda a: a.localize(request()),
                                     accept=lambda a: "data-use rule" if getattr(a, "requires_hosted_llm_permission", False) else None)
        self.assertEqual(outcome.adapter.name, "mock_localization")
        self.assertIn("data-use rule", outcome.skipped[0][1])

    def test_mock_localization_is_labelled(self):
        req = request()
        req.segments[0].source_text = "Give 1 sachet."
        result = base.get_adapter("mock_localization").localize(req)
        self.assertTrue(result.segments[0].subtitle_text.startswith("[MOCK ta-IN]"))
        self.assertIn("பொட்டலம்", result.segments[0].subtitle_text)


@override_settings(HL_GEMINI_API_KEY="test-key")
class GeminiAdapterTests(TestCase):
    """The real adapter is exercised against a FAKE HTTP layer. No network call is made."""

    def test_parses_structured_output(self):
        text = json.dumps({"segments": [{"id": 7, "subtitle_text": "2 பொட்டலங்கள் கொடுங்கள்.", "speech_text": "",
                                         "adaptation_type": "adapted", "rationale": "Imperative for a general audience.",
                                         "uncertainty_flags": []}]})
        result = gemini.GeminiLocalizationProvider().localize(request(), opener=opener_returning(text))
        seg = result.segments[0]
        self.assertEqual(seg.adaptation_type, "ADAPTED")
        self.assertEqual(seg.speech_text, seg.subtitle_text)

    def test_missing_segment_is_invalid_output(self):
        with self.assertRaises(base.ProviderOutputInvalid):
            gemini.GeminiLocalizationProvider().localize(request(), opener=opener_returning('{"segments": []}'))

    def test_unreadable_429_is_a_rate_limit_without_retry(self):
        opener, calls = opener_429s([b'{"error":"quota exceeded"}'])
        with mock.patch.object(gemini, "_sleep") as sleep, self.assertRaises(base.RateLimited):
            gemini.GeminiLocalizationProvider().localize(request(), opener=opener)
        sleep.assert_not_called()
        self.assertEqual(calls, [1])

    def test_daily_quota_429_is_quota_exhausted_without_retry(self):
        # Google's message says "quota" for every 429; only the quotaId says the DAILY limit was hit.
        opener, calls = opener_429s([body_429("GenerateRequestsPerDayPerProjectPerModel-FreeTier", "46032s")])
        with mock.patch.object(gemini, "_sleep") as sleep, self.assertRaises(base.QuotaExhausted) as ctx:
            gemini.GeminiLocalizationProvider().localize(request(), opener=opener)
        sleep.assert_not_called()
        self.assertEqual(calls, [1])
        self.assertIn("daily quota", str(ctx.exception))

    def test_short_rate_limit_waits_and_retries_once(self):
        ok = json.dumps({"segments": [{"id": 7, "subtitle_text": "2 பொட்டலங்கள் கொடுங்கள்."}]})
        opener, calls = opener_429s([body_429("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "7s")], then=ok)
        with mock.patch.object(gemini, "_sleep") as sleep:
            result = gemini.GeminiLocalizationProvider().localize(request(), opener=opener)
        sleep.assert_called_once_with(7.0)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(result.segments[0].segment_id, 7)

    def test_rate_limit_twice_falls_through_after_one_retry(self):
        body = body_429("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "3s")
        opener, calls = opener_429s([body, body])
        with mock.patch.object(gemini, "_sleep") as sleep, self.assertRaises(base.RateLimited):
            gemini.GeminiLocalizationProvider().localize(request(), opener=opener)
        self.assertEqual(sleep.call_count, 1)
        self.assertEqual(calls, [1, 2])

    def test_retry_skipped_when_it_would_exceed_the_time_budget(self):
        # The first attempt already took 70 s (a slow answer); waiting 7 s more would pass the 75 s budget.
        opener, calls = opener_429s([body_429("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "7s")])
        with mock.patch.object(gemini, "_sleep") as sleep, \
             mock.patch.object(gemini.time, "monotonic", side_effect=[0.0, 70.0]), \
             self.assertRaises(base.RateLimited):
            gemini.GeminiLocalizationProvider().localize(request(), opener=opener)
        sleep.assert_not_called()
        self.assertEqual(calls, [1])

    def test_long_rate_limit_wait_falls_through_without_sleeping(self):
        opener, _ = opener_429s([body_429("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "45s")])
        with mock.patch.object(gemini, "_sleep") as sleep, self.assertRaises(base.RateLimited):
            gemini.GeminiLocalizationProvider().localize(request(), opener=opener)
        sleep.assert_not_called()

    def test_api_key_sent_in_header_not_url(self):
        captured = {}

        def opener(req, timeout):
            captured["url"], captured["headers"] = req.full_url, dict(req.headers)
            return opener_returning('{"flags": []}')(req, timeout)

        gemini.GeminiMeaningCheckProvider().check("a", "b", "en", "ta-IN", opener=opener)
        self.assertNotIn("test-key", captured["url"])
        self.assertEqual(captured["headers"].get("X-goog-api-key"), "test-key")

    def test_meaning_flags_filtered_to_known_types(self):
        text = json.dumps({"flags": [{"type": "negation", "explanation": "dropped 'not'"}, {"type": "made-up"}]})
        result = gemini.GeminiMeaningCheckProvider().check("Do not boil", "boil", "en", "ta-IN", opener=opener_returning(text))
        self.assertEqual([f.flag_type for f in result.flags], ["NEGATION"])


class ManualTranscriptTests(TestCase):
    def test_parses_vtt_with_speakers(self):
        segs = parse_subtitles("WEBVTT\n\n00:00:01.000 --> 00:00:02.500\nAsha: Hello there.\n")
        self.assertEqual((segs[0].start_ms, segs[0].end_ms, segs[0].speaker, segs[0].text), (1000, 2500, "Asha", "Hello there."))

    def test_parses_srt(self):
        segs = parse_subtitles("1\n00:00:01,000 --> 00:00:02,000\nOne\n\n2\n00:00:03,000 --> 00:00:04,000\nTwo\n")
        self.assertEqual([s.text for s in segs], ["One", "Two"])

    def test_rejects_overlaps_and_garbage(self):
        with self.assertRaises(ValueError):
            parse_subtitles("garbage")
        with self.assertRaises(ValueError):
            parse_subtitles("1\n00:00:01,000 --> 00:00:03,000\nA\n\n2\n00:00:02,000 --> 00:00:04,000\nB\n")


class JobQueueTests(TestCase):
    def test_cancel_queued_job_immediately(self):
        from django.db import transaction

        with transaction.atomic():
            job = jobs.enqueue("consent_expiry_sweep")
            jobs.request_cancel(job, "TEST")
        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.CANCELLED)

    def test_claim_and_run(self):
        from django.db import transaction

        with transaction.atomic():
            jobs.enqueue("consent_expiry_sweep")
        done = jobs.drain()
        self.assertEqual([j.status for j in done], [Job.Status.SUCCEEDED])

    def test_transient_error_is_retried_then_fails(self):
        from django.db import transaction

        calls = []

        def flaky(job, ctx):
            calls.append(1)
            raise jobs.TransientJobError("timeout")

        jobs.HANDLERS["flaky_test"] = (flaky, None)
        jobs.LANES["flaky_test"] = "default"
        try:
            with transaction.atomic():
                job = jobs.enqueue("flaky_test")
            for _ in range(3):
                Job.objects.filter(pk=job.pk).update(run_after=None)
                jobs.drain()
            job.refresh_from_db()
            self.assertEqual(job.status, Job.Status.FAILED)
            self.assertEqual(len(calls), 3)
        finally:
            jobs.HANDLERS.pop("flaky_test")
            jobs.LANES.pop("flaky_test")


import os as _os
import unittest as _unittest


@_unittest.skipUnless(_os.environ.get("HL_TEST_WHISPER") == "1", "set HL_TEST_WHISPER=1 with the model downloaded")
class FasterWhisperSmokeTests(TestCase):
    """Optional: runs the real candidate model on synthetic non-speech audio (no real voice is used)."""

    def test_non_speech_gives_no_invented_text(self):
        import tempfile

        from hyperlocalize import media_tools
        from hyperlocalize.pipeline.providers.base import Unavailable, get_adapter

        base.registered()
        adapter = get_adapter("faster_whisper_transcription")
        self.assertTrue(adapter.available())
        with tempfile.TemporaryDirectory() as d:
            mp4, wav = _os.path.join(d, "t.mp4"), _os.path.join(d, "t.wav")
            media_tools.make_test_video(mp4, 6)
            media_tools.extract_audio(mp4, wav)
            with self.assertRaises(Unavailable):
                adapter.transcribe(wav, "en")
