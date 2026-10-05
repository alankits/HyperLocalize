import unittest

from hlspike.english_numbers import parse_number_words


def read(text):
    return parse_number_words(text.split(), 0)


class EnglishNumbersTest(unittest.TestCase):
    def test_simple_and_compound(self):
        self.assertEqual(read("fifty"), (50, 1))
        self.assertEqual(read("twenty four hours"), (24, 2))
        self.assertEqual(read("one hundred and five"), (105, 4))
        self.assertEqual(read("two thousand five"), (2005, 3))
        self.assertEqual(read("three lakh"), (300000, 2))

    def test_two_separate_numbers_are_not_added(self):
        self.assertEqual(read("one two"), (1, 1))
        self.assertEqual(read("twenty ten"), (20, 1))

    def test_not_a_number(self):
        self.assertIsNone(read("and five"))
        self.assertIsNone(read("hundred"))
        self.assertIsNone(read("water"))

    def test_trailing_and_is_not_consumed(self):
        self.assertEqual(read("five and water"), (5, 1))


if __name__ == "__main__":
    unittest.main()
