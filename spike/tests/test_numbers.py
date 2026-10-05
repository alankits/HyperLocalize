import unittest
from collections import Counter
from decimal import Decimal as D

from hlspike.numbers import FAIL, PASS, UNVERIFIABLE, check_numbers, load_tamil_number_stems, source_numbers, target_numbers

STEMS = load_tamil_number_stems()


class SourceNumbersTest(unittest.TestCase):
    def test_range_counts_both_ends(self):
        self.assertEqual(source_numbers("give 50 to 100 millilitres"), Counter({D(50): 1, D(100): 1}))

    def test_words_frequency_grouping_decimal_time(self):
        self.assertEqual(source_numbers("once a day for ten to 14 days"), Counter({D(1): 1, D(10): 1, D(14): 1}))
        self.assertEqual(source_numbers("1,000 people, 2.5 mg at 10:30"), Counter({D(1000): 1, D("2.5"): 1, "10:30": 1}))

    def test_repeated_values_are_counted(self):
        self.assertEqual(source_numbers("Under 2 years, from 2 to 10"), Counter({D(2): 2, D(10): 1}))


class TargetNumbersTest(unittest.TestCase):
    def test_tamil_digits_and_indian_grouping(self):
        values, reasons = target_numbers("௫௦ மற்றும் 1,00,000", STEMS)
        self.assertEqual(values, Counter({D(50): 1, D(100000): 1}))
        self.assertEqual(reasons, [])

    def test_comma_list_is_not_grouping(self):
        values, _ = target_numbers("5,10", STEMS)
        self.assertEqual(values, Counter({D(5): 1, D(10): 1}))

    def test_number_word_and_non_positional_numeral_are_flagged(self):
        _, reasons = target_numbers("இருபத்தைந்து ௱", STEMS)
        self.assertEqual(len(reasons), 2)


class CheckNumbersTest(unittest.TestCase):
    source = "Give 50 to 100 millilitres."

    def test_pass(self):
        self.assertEqual(check_numbers(self.source, "50 முதல் 100 மில்லிலிட்டர் கொடுங்கள்.", STEMS), (PASS, []))

    def test_tamil_digits_pass(self):
        self.assertEqual(check_numbers(self.source, "௫௦ முதல் ௧௦௦ மில்லி", STEMS)[0], PASS)

    def test_wrong_number_fails(self):
        status, details = check_numbers(self.source, "50 முதல் 150 மில்லி", STEMS)
        self.assertEqual(status, FAIL)
        self.assertIn("150", details[0])

    def test_missing_number_fails(self):
        self.assertEqual(check_numbers(self.source, "50 மில்லி", STEMS)[0], FAIL)

    def test_number_as_word_is_unverifiable(self):
        self.assertEqual(check_numbers(self.source, "ஐம்பது முதல் 100 மில்லி", STEMS)[0], UNVERIFIABLE)

    def test_extra_digit_fails_even_with_number_word(self):
        self.assertEqual(check_numbers(self.source, "ஐம்பது முதல் 200 மில்லி", STEMS)[0], FAIL)


if __name__ == "__main__":
    unittest.main()
