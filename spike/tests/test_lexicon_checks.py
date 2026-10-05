import unittest

from hlspike.lexicon_checks import check_glossary, check_units
from hlspike.numbers import FAIL, PASS, UNVERIFIABLE
from tests.fixtures import GLOSSARY, UNITS


class UnitsTest(unittest.TestCase):
    def test_tamil_inflected_and_latin_forms_pass(self):
        self.assertEqual(check_units("100 ml", "100 மில்லிலிட்டர்", UNITS)[0], PASS)
        self.assertEqual(check_units("100 millilitres", "100 mL", UNITS)[0], PASS)

    def test_missing_unit_fails(self):
        status, details = check_units("20 milligrams", "20 கொடுங்கள்", UNITS)
        self.assertEqual(status, FAIL)
        self.assertIn("no Tamil forms yet", details[0])

    def test_wrong_unit_fails_both_ways(self):
        status, details = check_units("20 ml", "20 mg", UNITS)
        self.assertEqual(status, FAIL)
        self.assertEqual(len(details), 2)  # ml missing, mg added

    def test_single_letter_form_is_case_sensitive(self):
        self.assertEqual(check_units("1 litre", "1 L நீர்", UNITS)[0], PASS)
        self.assertEqual(check_units("1 litre", "1 l நீர்", UNITS)[0], FAIL)


class GlossaryTest(unittest.TestCase):
    def test_inflected_form_matches_stem(self):
        self.assertEqual(check_glossary("Ask about zinc.", "துத்தநாகத்தைப் பற்றி கேளுங்கள்.", GLOSSARY), (PASS, []))

    def test_missing_term_fails(self):
        self.assertEqual(check_glossary("Ask about zinc.", "மருந்து பற்றி கேளுங்கள்.", GLOSSARY)[0], FAIL)

    def test_do_not_translate_term_must_stay(self):
        self.assertEqual(check_glossary("Use ORS.", "ORS பயன்படுத்துங்கள்.", GLOSSARY)[0], PASS)
        self.assertEqual(check_glossary("Use ORS.", "கரைசல் பயன்படுத்துங்கள்.", GLOSSARY)[0], FAIL)

    def test_entry_without_tamil_forms_is_unverifiable_not_pass(self):
        self.assertEqual(check_glossary("Open 1 sachet.", "1 பொட்டலம்", GLOSSARY)[0], UNVERIFIABLE)

    def test_term_not_in_source_is_ignored(self):
        self.assertEqual(check_glossary("Wash your hands.", "கைகளைக் கழுவுங்கள்.", GLOSSARY), (PASS, []))


if __name__ == "__main__":
    unittest.main()
