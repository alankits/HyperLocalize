"""ADR 0008 rule checks and scene planning. Tamil target strings are test inputs written for the
checks only; they are not reference translations."""
from django.test import SimpleTestCase

from hyperlocalize.pipeline.providers.base import TranscriptSegment

from . import checks as c
from .services import plan_scenes


class NumberCheckTests(SimpleTestCase):
    def check(self, src, tgt):
        return c.check_numbers(src, tgt, "en", "ta")[0]

    def test_digits_match(self):
        self.assertEqual(self.check("Give 2 sachets", "2 பொட்டலங்கள்"), c.PASS)

    def test_number_words_in_source(self):
        self.assertEqual(self.check("Give two sachets twice a day", "2 பொட்டலங்கள் 2 முறை"), c.PASS)

    def test_changed_number_fails(self):
        self.assertEqual(self.check("Give 2 sachets", "3 பொட்டலங்கள்"), c.FAIL)

    def test_missing_number_fails(self):
        self.assertEqual(self.check("Give 2 sachets", "பொட்டலங்கள்"), c.FAIL)

    def test_tamil_digits_and_indian_grouping(self):
        self.assertEqual(self.check("1,00,000 people", "௧,௦௦,௦௦௦ மக்கள்"), c.PASS)

    def test_tamil_number_word_is_unverifiable_fail_safe(self):
        self.assertEqual(self.check("Give 2 sachets", "இரண்டு பொட்டலங்கள்"), c.UNVERIFIABLE)

    def test_unknown_language_pair_is_never_a_silent_pass(self):
        self.assertEqual(c.check_numbers("Give 2", "Donnez 2", "en", "fr")[0], c.UNVERIFIABLE)


class UnitGlossaryStructureTests(SimpleTestCase):
    def test_unit_kept_in_latin_passes(self):
        self.assertEqual(c.check_units("Mix in 1 litre", "1 L தண்ணீரில்", "en", "ta")[0], c.PASS)

    def test_unit_missing_fails(self):
        self.assertEqual(c.check_units("Mix in 1 litre", "1 தண்ணீரில்", "en", "ta")[0], c.FAIL)

    def test_declared_conversion_is_unverifiable(self):
        status, _ = c.check_units("Take 1 teaspoon", "1 ஸ்பூன்", "en", "ta", conversions=[{"from": "teaspoonful", "to": "ml"}])
        self.assertEqual(status, c.UNVERIFIABLE)

    def test_glossary_term_without_forms_is_unverifiable(self):
        gl = [{"source_term": "ORS", "target_term": "", "accepted_forms": [], "do_not_translate": False}]
        self.assertEqual(c.check_glossary("Give ORS", "ஓ.ஆர்.எஸ்", gl, "ta")[0], c.UNVERIFIABLE)

    def test_glossary_inflected_form_by_prefix(self):
        gl = [{"source_term": "sachet", "target_term": "பொட்டலம்", "accepted_forms": ["பொட்டல"], "do_not_translate": False}]
        self.assertEqual(c.check_glossary("one sachet", "ஒரு பொட்டலத்தை", gl, "ta")[0], c.PASS)

    def test_do_not_translate_term(self):
        gl = [{"source_term": "ORS", "target_term": "", "accepted_forms": [], "do_not_translate": True}]
        self.assertEqual(c.check_glossary("Give ORS", "ORS கொடுங்கள்", gl, "ta")[0], c.PASS)
        self.assertEqual(c.check_glossary("Give ORS", "கொடுங்கள்", gl, "ta")[0], c.FAIL)

    def test_untranslated_and_latin_script(self):
        self.assertEqual(c.check_structure("Give ORS", "Give ORS", "ta")[0], c.FAIL)
        self.assertEqual(c.check_structure("Give ORS", "[MOCK] Give ORS now", "ta")[0], c.FAIL)
        self.assertEqual(c.check_structure("Give ORS", "", "ta")[0], c.FAIL)

    def test_timing_budget(self):
        self.assertEqual(c.check_structure("Hi", "வணக்கம் " * 20, "ta", duration_ms=1000)[0], c.FAIL)


class ScenePlanTests(SimpleTestCase):
    def segs(self, *ranges):
        return [TranscriptSegment(a, b, "x") for a, b in ranges]

    def test_cut_in_gap_splits_and_scenes_are_contiguous(self):
        scenes = plan_scenes(self.segs((500, 2500), (3000, 5000), (7000, 9000)), 12000, shot_cuts=[6000])
        self.assertEqual([(s, e) for s, e, _ in scenes], [(0, 6000), (6000, 12000)])

    def test_long_pause_splits_at_midpoint(self):
        scenes = plan_scenes(self.segs((0, 1000), (3000, 4000)), 5000)
        self.assertEqual([(s, e) for s, e, _ in scenes], [(0, 2000), (2000, 5000)])

    def test_no_segments(self):
        self.assertEqual(plan_scenes([], 1000), [])
