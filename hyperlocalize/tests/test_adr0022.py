"""ADR 0022: batched provider calls, no silent MOCK after a real failure ("translation pending"), speech length
budget, 1.2× tempo cap and blocking overrun check, Tamil track tags, the intelligibility proxy in the evidence,
and Tamil number words in the numbers check."""
import io
import json
import os
import subprocess
import tempfile
import urllib.error
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from hyperlocalize import media_tools
from hyperlocalize.accounts.models import Policy
from hyperlocalize.localization import services as loc
from hyperlocalize.localization.checks import check_numbers
from hyperlocalize.localization.models import CheckResult, Localization, Scene, Segment, SegmentTranslation
from hyperlocalize.localization import tamil_numbers
from hyperlocalize.pipeline import jobs
from hyperlocalize.pipeline.models import Job
from hyperlocalize.pipeline.providers import base, gemini, mms_tts
from hyperlocalize.pipeline.providers.base import QuotaExhausted
from hyperlocalize.projects import services as projects
from hyperlocalize.rendering import services as rendering
from hyperlocalize.rendering.models import MAX_TEMPO, SynthesisedSegment
from hyperlocalize.testing import MediaRootMixin, make_project, make_users, transcript_upload, video_upload

from .test_workflow import WorkflowBase


def fake_gemini(calls):
    """A stand-in for gemini._post: answers localization and batched meaning-check prompts, counting calls."""
    def post(prompt, *, opener=None):
        data = json.loads(prompt)
        if "segments" in data:
            calls.append(("localize", len(data["segments"])))
            return json.dumps({"segments": [{"id": s["id"], "subtitle_text": "சோதனை வாக்கியம்",
                                             "speech_text": "சோதனை வாக்கியம்", "adaptation_type": "LITERAL",
                                             "rationale": "", "uncertainty_flags": []} for s in data["segments"]]})
        calls.append(("meaning", len(data["pairs"])))
        return json.dumps({"results": [{"id": p["id"], "flags": []} for p in data["pairs"]]})
    return post


def quota_exhausted(prompt, *, opener=None):
    raise QuotaExhausted("HTTP 429 from Gemini (daily quota used up)")


@override_settings(HL_GEMINI_API_KEY="test-key")
@mock.patch.object(gemini._GeminiBase, "available", lambda self: bool(settings.HL_GEMINI_API_KEY))  # with a fake _post: no network
class BatchingTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.users = make_users()
        self.project = make_project(self.users)  # scripted: the hosted LLM is allowed
        self.localization = Localization.objects.get(project=self.project)

    def test_whole_clip_is_one_localization_call_and_one_meaning_check_call(self):
        calls = []
        with mock.patch.object(gemini, "_post", fake_gemini(calls)):
            projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
            jobs.drain()
        scenes = Scene.objects.filter(video__project=self.project).count()
        segments = Segment.objects.filter(scene__video__project=self.project).count()
        self.assertGreaterEqual(scenes, 2)
        self.assertEqual(calls, [("localize", segments), ("meaning", segments)])
        self.assertFalse(SegmentTranslation.objects.filter(is_mock=True).exists())
        self.assertEqual(CheckResult.objects.filter(check_type="meaning", status="PASS").count(), segments)

    def test_batches_split_by_scene_when_the_clip_is_too_large(self):
        calls = []
        with mock.patch.object(loc, "BATCH_MAX_SEGMENTS", 1), mock.patch.object(gemini, "_post", fake_gemini(calls)):
            projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
            jobs.drain()
        localize_calls = [c for c in calls if c[0] == "localize"]
        self.assertEqual(len(localize_calls), Scene.objects.filter(video__project=self.project).count())
        self.assertEqual(len([c for c in calls if c[0] == "meaning"]), 1)  # still one meaning-check call

    def test_quota_failure_never_produces_mock_text_and_shows_pending(self):
        with mock.patch.object(gemini, "_post", quota_exhausted):
            projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
            jobs.drain()
        job = Job.objects.filter(project=self.project, type="localize").order_by("-pk").first()
        self.assertIn("TranslationPending", job.error)
        self.assertFalse(SegmentTranslation.objects.exists())  # no MOCK text, nothing at all
        self.assertTrue(all(s.status == "PENDING" for s in Scene.objects.filter(video__project=self.project)))
        self.client.force_login(self.users["manager"])
        page = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertContains(page, "Translation pending")
        self.assertContains(page, "Nothing was machine-translated by a MOCK")

    def test_retry_after_quota_translates_the_pending_scenes(self):
        with mock.patch.object(gemini, "_post", quota_exhausted):
            projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
            for _ in range(5):  # use up the automatic retries
                Job.objects.filter(status="QUEUED").update(run_after=None)
                jobs.drain()
        self.assertEqual(Job.objects.filter(project=self.project, type="localize").order_by("-pk").first().status, "FAILED")
        calls = []
        self.client.force_login(self.users["operator"])
        with mock.patch.object(gemini, "_post", fake_gemini(calls)):
            r = self.client.post(reverse("projects:retry_translation", args=[self.project.pk]))
            self.assertEqual(r.status_code, 302)
            jobs.drain()
        self.assertFalse(Scene.objects.filter(video__project=self.project, status="PENDING").exists())
        self.assertFalse(SegmentTranslation.objects.filter(is_mock=True).exists())

    def test_reviewer_cannot_trigger_a_retry(self):
        self.client.force_login(self.users["reviewer"])
        r = self.client.post(reverse("projects:retry_translation", args=[self.project.pk]))
        self.assertEqual(r.status_code, 403)

    def test_meaning_check_failure_is_unavailable_not_a_mock_pass(self):
        calls = []
        ok = fake_gemini(calls)

        def localize_ok_meaning_fails(prompt, *, opener=None):
            if "pairs" in json.loads(prompt):
                raise base.Unavailable("HTTP 503 from Gemini")
            return ok(prompt)

        with mock.patch.object(gemini, "_post", localize_ok_meaning_fails):
            projects.upload_video(self.users["operator"], self.project, video_upload(), transcript_upload())
            jobs.drain()
        meaning = CheckResult.objects.filter(check_type="meaning")
        self.assertTrue(meaning.exists())
        self.assertTrue(all(c.status == "CHECK_UNAVAILABLE" for c in meaning))
        self.assertTrue(any(c.check_type == "meaning" for c in loc.blocking_checks(self.localization)))
        # Retrying replaces the unavailable results with real ones.
        with mock.patch.object(gemini, "_post", fake_gemini([])):
            self.assertGreater(loc.retry_unavailable_meaning_checks(self.localization), 0)
        self.assertFalse(CheckResult.objects.filter(check_type="meaning", status="CHECK_UNAVAILABLE").exists())

    def test_personal_project_still_uses_the_labelled_mock(self):
        personal = make_project(self.users, scripted=False)
        calls = []
        with mock.patch.object(gemini, "_post", fake_gemini(calls)):
            projects.upload_video(self.users["operator"], personal, video_upload(), transcript_upload())
            jobs.drain()
        self.assertEqual(calls, [])  # the data-use rule skipped Gemini; no real provider failed
        self.assertTrue(SegmentTranslation.objects.filter(localization__project=personal, is_mock=True).exists())


class GeminiBatchAndRetryTests(TestCase):
    @override_settings(HL_GEMINI_API_KEY="test-key")
    def test_503_is_retried_once(self):
        attempts = []

        def opener(req, timeout):
            attempts.append(1)
            if len(attempts) == 1:
                raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", {}, io.BytesIO(b""))
            payload = {"candidates": [{"content": {"parts": [{"text": '{"results": []}'}]}}]}

            class R(io.BytesIO):
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False
            return R(json.dumps(payload).encode())

        with mock.patch.object(gemini, "_sleep") as sleep:
            self.assertEqual(gemini._post("{}", opener=opener), '{"results": []}')
        self.assertEqual(len(attempts), 2)
        sleep.assert_called_once()

    def test_batch_prompt_carries_the_length_budget_rule(self):
        request = base.LocalizationRequest("en", "ta-IN", [base.SegmentContext(1, "Hello", 2000, "S1", max_speech_chars=26)],
                                           {}, [])
        prompt = json.loads(gemini.localization_prompt(request))
        self.assertEqual(prompt["segments"][0]["max_speech_chars"], 26)
        self.assertTrue(any("max_speech_chars" in r for r in prompt["rules"]))
        self.assertEqual(request.prompt_version, "loc-v3")


class LengthBudgetTests(WorkflowBase):
    def test_budget_uses_the_voice_rate_and_the_tempo_cap(self):
        self.upload_and_process()
        scene = Scene.objects.filter(video__project=self.project).order_by("index").first()
        with mock.patch.object(mms_tts.MmsTtsTamilStockVoiceProvider, "available", return_value=True):
            request = loc.build_request(self.localization, scene)
        segs = list(scene.segments.order_by("index"))
        first = request.segments[0]
        room = loc.speech_room_ms(segs[0], scene, segs)
        self.assertEqual(first.max_speech_chars, int(room / 1000 * 11))  # normal rate; 1.2× stays as headroom
        self.assertEqual(first.room_ms, room)

    def test_no_budget_when_speech_is_off_or_no_rate_is_known(self):
        self.upload_and_process()
        scene = Scene.objects.filter(video__project=self.project).first()
        self.assertIsNone(loc.build_request(self.localization, scene).segments[0].max_speech_chars)  # mock voice: no rate
        Policy.objects.create(key="synthesis_allowed", value=False)
        with mock.patch.object(mms_tts.MmsTtsTamilStockVoiceProvider, "available", return_value=True):
            self.assertIsNone(loc.build_request(self.localization, scene).segments[0].max_speech_chars)


class OverrunCheckTests(WorkflowBase):
    def real_speech(self, duration_ms, tempo):
        """Pretend a real (non-mock) voice produced speech of this length for the first segment."""
        self.upload_and_process()
        scene = Scene.objects.filter(video__project=self.project).order_by("index").first()
        segs = list(scene.segments.order_by("index"))
        t = loc.latest_translations(self.localization, segs)[segs[0].pk]
        syn = SynthesisedSegment.objects.create(segment=segs[0], localization=self.localization, translation=t, version=99,
                                                duration_ms=duration_ms, rendering_mode="STOCK_VOICE", adapter="mms_tts_tamil",
                                                tempo=tempo, is_mock=False)
        return syn, scene, segs

    def test_tempo_cap_is_1_2(self):
        self.assertEqual(MAX_TEMPO, Decimal("1.20"))

    def test_speech_that_still_overruns_is_a_blocking_hard_check(self):
        syn, scene, segs = self.real_speech(duration_ms=60_000, tempo=Decimal("1.200"))
        rendering._speech_checks([syn], scene, segs, inference=None, workdir=tempfile.gettempdir())
        check = CheckResult.objects.get(segment_translation=syn.translation, check_type="speech_overrun")
        self.assertEqual((check.kind, check.status), ("HARD", "FAIL"))
        self.assertIn("shorten the speech script", check.detail["messages"][0])
        self.assertIn(check, loc.blocking_checks(self.localization))

    def test_speech_that_fits_passes(self):
        syn, scene, segs = self.real_speech(duration_ms=200, tempo=Decimal("1.000"))
        rendering._speech_checks([syn], scene, segs, inference=None, workdir=tempfile.gettempdir())
        self.assertEqual(CheckResult.objects.get(check_type="speech_overrun").status, "PASS")

    def test_mock_speech_gets_no_timing_check(self):
        syn, scene, segs = self.real_speech(duration_ms=60_000, tempo=Decimal("1.200"))
        SynthesisedSegment.objects.filter(pk=syn.pk).update(is_mock=True)
        syn.refresh_from_db()
        rendering._speech_checks([syn], scene, segs, inference=None, workdir=tempfile.gettempdir())
        self.assertFalse(CheckResult.objects.filter(check_type="speech_overrun").exists())


class TrackLanguageTests(TestCase):
    def test_dubbed_audio_and_subtitles_are_tagged_tamil(self):
        with tempfile.TemporaryDirectory() as d:
            src, srt, out, wav = (os.path.join(d, n) for n in ("v.mp4", "s.srt", "o.mp4", "a.wav"))
            media_tools.make_test_video(src, seconds=2)
            open(srt, "w", encoding="utf-8").write("1\n00:00:00,000 --> 00:00:01,000\nவணக்கம்\n")
            media_tools.build_speech_track([], 2000, wav)
            media_tools.mux_final(src, wav, srt, out, target_language="ta-IN", source_language="en")
            tags = subprocess.run([media_tools.ffprobe(), "-v", "error", "-show_entries", "stream=codec_type:stream_tags=language",
                                   "-of", "json", out], capture_output=True, text=True, check=True)
        langs = {s["codec_type"]: s.get("tags", {}).get("language") for s in json.loads(tags.stdout)["streams"]}
        self.assertEqual(langs["audio"], "tam")
        self.assertEqual(langs["subtitle"], "tam")

    def test_unknown_language_is_und(self):
        self.assertEqual(media_tools.language_tag("xx"), "und")


class IntelligibilityProxyTests(WorkflowBase):
    def test_cer(self):
        self.assertEqual(rendering.character_error_rate("வணக்கம்", "வணக்கம்"), 0)
        self.assertGreater(rendering.character_error_rate("வணக்கம்", "வணக"), 0)
        self.assertGreater(rendering.character_error_rate("கா", "கி"), 0)  # vowel signs count (review #2)
        self.assertEqual(rendering.character_error_rate("வணக்கம்!", "வணக்கம்"), 0)  # punctuation does not

    def test_summary_is_labelled_a_proxy(self):
        from hyperlocalize.exports.services import intelligibility_summary

        self.upload_and_process()
        segs = list(Segment.objects.filter(scene__video__project=self.project))
        t = loc.latest_translations(self.localization, segs)[segs[0].pk]
        SynthesisedSegment.objects.create(segment=segs[0], localization=self.localization, translation=t, version=9,
                                          duration_ms=1000, rendering_mode="STOCK_VOICE", adapter="mms_tts_tamil",
                                          intelligibility={"label": rendering.PROXY_LABEL, "cer": 0.2})
        summary = intelligibility_summary(SynthesisedSegment.objects.filter(version=9))
        self.assertIn("PROXY, not a listening test", summary["label"])
        self.assertEqual((summary["lines_measured"], summary["mean_cer"]), (1, 0.2))


class TamilNumberWordTests(TestCase):
    def test_compounds_and_inflections(self):
        cases = {"இருபத்தொன்று": 21, "இருபத்திரண்டு": 22, "இருபத்து மூன்று": 23, "இருபத்தைந்து": 25,
                 "முப்பத்தாறு": 36, "நாற்பத்தேழு": 47, "ஐம்பத்தெட்டு": 58, "அறுபத்தொன்பது": 69,
                 "தொண்ணூற்றொன்பது": 99, "எழுபத்தி நான்கு": 74, "இருபது": 20, "அறுபது": 60, "நூறு": 100,
                 "பதினைந்து": 15, "பன்னிரண்டு": 12, "பத்தொன்பது": 19, "இரண்டையும்": 2, "இருபத்து ஒன்று": 21,
                 "எழுபத்தி எட்டு": 78,
                 "இருபதுக்கு": 20, "பத்து": 10}
        for text, value in cases.items():
            with self.subTest(text=text):
                values, ambiguous, _ = tamil_numbers.parse(text)
                self.assertEqual(dict(values), {value: 1})
                self.assertEqual(ambiguous, [])

    def test_lookalikes_are_not_numbers_and_ambiguous_words_are_flagged(self):
        self.assertEqual(tamil_numbers.parse("பத்திரமாக")[:2], ({}, []))  # "safely", not 10
        for word, value in (("ஏழை", 7), ("ஒன்றாக", 1), ("ஒரு", 1), ("ஆறு", 6), ("அஞ்சு", 5), ("மூன்றாவது", 3)):
            with self.subTest(word=word):
                self.assertEqual(tamil_numbers.parse(word)[:2], ({}, [value]))

    def test_number_check_on_speech_scripts(self):
        self.assertEqual(check_numbers("Rub for at least 20 seconds.", "குறைந்தபட்சம் இருபது வினாடிகள் தேய்க்கவும்.", "en", "ta")[0], "PASS")
        status, details = check_numbers("Rub for at least 20 seconds.", "குறைந்தபட்சம் இரண்டு வினாடிகள் தேய்க்கவும்.", "en", "ta")
        self.assertEqual(status, "FAIL")  # the wrong number word is caught
        self.assertEqual(check_numbers("Step one, wash.", "படி ஒன்று, கழுவுங்கள்.", "en", "ta")[0], "PASS")
        self.assertEqual(check_numbers("Give 2 a day.", "ஒரு நாளைக்கு இரண்டு கொடுங்கள்.", "en", "ta")[0], "UNVERIFIABLE")
        self.assertEqual(check_numbers("Keep it safe.", "அதை பத்திரமாக வைக்கவும்.", "en", "ta")[0], "PASS")


class ReviewFixTests(WorkflowBase):
    """Independent review of ADR 0022 (2026-10-22): fixes #1, #6, #7, #8."""

    def test_missing_meaning_check_blocks_approval(self):
        from hyperlocalize.review import services as review

        self.upload_and_process()
        t = loc.latest_translations(self.localization, list(Segment.objects.filter(scene__video__project=self.project)))
        CheckResult.objects.filter(segment_translation=next(iter(t.values())), kind="AI_FLAG").delete()
        problems = review.approval_problems(self.users["manager"], self.localization)
        self.assertTrue(any("no meaning check" in p for p in problems))
        self.assertEqual(loc.retry_unavailable_meaning_checks(self.localization), 1)  # the retry fills the gap
        self.assertEqual(loc.missing_meaning_checks(self.localization), [])

    def test_retry_resends_a_failed_scene_regeneration_with_its_instruction(self):
        self.upload_and_process()
        scene = Scene.objects.filter(video__project=self.project).first()
        job = jobs.enqueue("localize", project=self.project, localization=self.localization, scene=scene,
                           payload={"instruction": "use simpler words", "regeneration": True})
        Job.objects.filter(pk=job.pk).update(status="FAILED", error="TransientJobError: TranslationPending: x")
        self.client.force_login(self.users["manager"])
        self.client.post(reverse("projects:retry_translation", args=[self.project.pk]))
        retry = Job.objects.filter(type="localize").order_by("-pk").first()
        self.assertEqual(retry.scene_id, scene.pk)
        self.assertEqual(retry.payload["instruction"], "use simpler words")

    def test_test_runner_is_always_test_mode(self):
        from django.conf import settings

        self.assertEqual(settings.HYPERLOCALIZE_MODE, "test")
        with self.assertRaises(base.Unavailable):
            gemini._post("{}")  # no injected transport in test mode: refused, nothing leaves the laptop

    @override_settings(HL_GEMINI_API_KEY="test-key")
    def test_bad_reply_and_dropped_connection_are_provider_failures(self):
        class NotJson(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with self.assertRaises(base.ProviderOutputInvalid):
            gemini._post("{}", opener=lambda req, timeout: NotJson(b"<html>busy</html>"))

        def dropped(req, timeout):
            raise ConnectionResetError("reset")

        with self.assertRaises(base.Unavailable):
            gemini._post("{}", opener=dropped)
