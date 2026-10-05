import json
import tempfile
import unittest
from pathlib import Path

from hlspike.asr_score import align, boundary_errors_ms, critical_token_errors, load_rules, normalise_words, read_hypothesis, score, wer
from hlspike.script_export import read_segments

RULES = load_rules()
SCRIPT = "\n".join(s["text"] for s in read_segments())


class NormalisationTest(unittest.TestCase):
    def test_numbers_spelling_and_abbreviations(self):
        self.assertEqual(normalise_words("Give FIFTY to one hundred mL of O.R.S.", RULES),
                         ["give", "50", "to", "100", "millilitres", "of", "ors"])
        self.assertEqual(normalise_words("Diarrhea: 1 liter, 1,000 people", RULES),
                         ["diarrhoea", "1", "litre", "1000", "people"])


class WerTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(wer(["a", "b", "c"], ["a", "b", "c"]), 0)
        self.assertAlmostEqual(wer(["a", "b", "c"], ["a", "x", "c", "d"]), 2 / 3)
        ops = [op[0] for op in align(["a", "b"], ["b"]).ops]
        self.assertEqual(ops, ["del", "equal"])


class CriticalTokensTest(unittest.TestCase):
    def test_script_against_itself(self):
        result = score(SCRIPT, SCRIPT, RULES)
        self.assertEqual(result["wer"], 0)
        self.assertEqual(result["critical_errors"], 0)
        # 19 number tokens, plus units, glossary terms and "once a day".
        self.assertGreater(result["critical_total"], 19)

    def test_wrong_number_and_dropped_term_are_errors(self):
        hyp = SCRIPT.replace("100 to 200", "100 to 250").replace("Ask a health worker about zinc.", "Ask about zinc.")
        result = critical_token_errors(SCRIPT, hyp, RULES)
        self.assertEqual(result["critical_errors"], 2)
        self.assertEqual({e["ref"] for e in result["errors"]}, {"200", "health_worker"})

    def test_us_spelling_and_number_words_are_not_errors(self):
        hyp = SCRIPT.replace("Diarrhoea", "Diarrhea").replace("1 litre", "one liter").replace("50 to 100 millilitres", "fifty to one hundred ml")
        self.assertEqual(critical_token_errors(SCRIPT, hyp, RULES)["critical_errors"], 0)

    def test_inserted_number_is_reported_separately(self):
        result = critical_token_errors("give it slowly", "give 5 it slowly", RULES)
        self.assertEqual(result["inserted_critical"], ["5"])


class BoundaryAndInputTest(unittest.TestCase):
    def test_nearest_boundary(self):
        result = boundary_errors_ms([0.0, 2.0, 4.0], [0.1, 2.0, 4.5])
        self.assertAlmostEqual(result["median_ms"], 100)
        self.assertAlmostEqual(result["max_ms"], 500)

    def test_json_hypothesis(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hyp.json"
            path.write_text(json.dumps({"segments": [{"start": 0, "end": 1.5, "text": "Wash"}, {"start": 1.5, "end": 3, "text": "hands."}]}))
            text, points = read_hypothesis(path)
        self.assertEqual(text, "Wash hands.")
        self.assertEqual(points, [0.0, 1.5, 3.0])


if __name__ == "__main__":
    unittest.main()
