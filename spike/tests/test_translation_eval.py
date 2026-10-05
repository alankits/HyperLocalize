import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from hlspike import translation_eval as te
from hlspike.agreement import binary_summary, cohen_kappa, linear_weighted_kappa
from hlspike.chrf import corpus_chrf, sentence_chrf
from hlspike.rules import rule3
from tests.fixtures import checkset

try:
    from sacrebleu.metrics import CHRF  # optional: only for the cross-check below
except ImportError:
    CHRF = None

SOURCE = {"S01": "Mix one sachet in 1 litre of water.", "S02": "Give 5 ml after each loose stool."}
SYSTEMS = {
    "T0": {"S01": "ஒரு பொட்டலத்தை 1 லிட்டர் தண்ணீரில் கலக்கவும்.", "S02": "ஐந்து மில்லி கொடுக்கவும்."},
    "T2-G": {"S01": "ஒரு பொட்டலத்தை 1 லிட்டர் நீரில் கலக்கவும்.", "S02": "5 மில்லி கொடுக்கவும்."},
}
TERMS = {"T0": {"trains_on_data": False}, "T1-G": {"trains_on_data": True}, "T2-G": {"trains_on_data": True},
         "T1-Q": {"trains_on_data": False}, "T2-Q": {"trains_on_data": False}}


class ChrfTest(unittest.TestCase):
    # Expected values produced by sacreBLEU 2.6.0 (CHRF() defaults) on 2026-10-05.
    def test_matches_sacrebleu_values(self):
        self.assertAlmostEqual(sentence_chrf("The cat sat on the mat.", "The cat is on the mat."), 67.172735, places=5)
        self.assertAlmostEqual(sentence_chrf("5 நாட்கள்", "ஐந்து நாட்கள்"), 49.83462, places=5)
        self.assertAlmostEqual(sentence_chrf("ab", "abcdefgh"), 23.404255, places=5)

    def test_edges(self):
        self.assertEqual(sentence_chrf("same text", "same text"), 100.0)
        self.assertEqual(sentence_chrf("", "abc"), 0.0)
        self.assertEqual(sentence_chrf("xyz", "abc"), 0.0)

    def test_nfc_makes_two_spellings_equal(self):
        composed, decomposed = "கொடு", "கொடு"  # ொ as one code point vs two
        self.assertNotEqual(composed, decomposed)
        self.assertEqual(sentence_chrf(decomposed, composed), 100.0)

    def test_corpus_is_not_mean_of_sentences(self):
        hyps, refs = ["The cat sat on the mat.", "ab"], ["The cat is on the mat.", "abcdefgh"]
        mean = sum(sentence_chrf(h, r) for h, r in zip(hyps, refs)) / 2
        self.assertNotAlmostEqual(corpus_chrf(hyps, refs), mean, places=2)

    @unittest.skipIf(CHRF is None, "sacrebleu not installed (optional cross-check)")
    def test_live_cross_check(self):
        metric = CHRF()
        for hyp, ref in [("ஒரு லிட்டர் தண்ணீர்", "ஒரு லிட்டர் குடிநீர்"), ("abc def", "abd cef")]:
            self.assertAlmostEqual(sentence_chrf(hyp, ref), metric.sentence_score(hyp, [ref]).score, places=9)


class AgreementTest(unittest.TestCase):
    def test_kappa_hand_computed(self):
        # po = 3/4; pe = 0.5*0.75 + 0.5*0.25 = 0.5; kappa = (0.75 - 0.5) / (1 - 0.5) = 0.5
        self.assertAlmostEqual(cohen_kappa([1, 1, 0, 0], [1, 1, 0, 1]), 0.5)

    def test_rare_label_high_agreement_low_kappa(self):
        a = [False] * 19 + [True]
        b = [False] * 18 + [True, False]
        s = binary_summary(a, b)
        self.assertAlmostEqual(s["raw_agreement"], 0.9)
        self.assertAlmostEqual(s["prevalence"], 0.05)
        self.assertLess(s["kappa"], 0)  # why the plan wants raw agreement and prevalence too

    def test_kappa_undefined_when_all_one_label(self):
        self.assertIsNone(cohen_kappa(["x", "x"], ["x", "x"]))

    def test_weighted_kappa(self):
        self.assertAlmostEqual(linear_weighted_kappa([0, 1, 2, 3], [0, 1, 2, 3], 4), 1.0)
        # One-step disagreements score better than three-step ones.
        near = linear_weighted_kappa([0, 1, 2, 3], [1, 1, 2, 3], 4)
        far = linear_weighted_kappa([0, 1, 2, 3], [3, 1, 2, 3], 4)
        self.assertGreater(near, far)


class Rule3Test(unittest.TestCase):
    def test_clear_winner(self):
        r = rule3({"T0": 20, "T2-G": 10, "T2-Q": 16}, {"T0": False, "T2-G": True, "T2-Q": False}, {"T0": 1, "T2-G": 1, "T2-Q": 1})
        self.assertEqual((r["winner"], r["decided_by"]), ("T2-G", "mqm_points"))

    def test_tie_margin_is_inclusive_and_data_terms_break_it(self):
        r = rule3({"T2-G": 10, "T2-Q": 15}, {"T2-G": True, "T2-Q": False}, {"T2-G": 1, "T2-Q": 0})
        self.assertEqual(r["tied_on_mqm"], ["T2-G", "T2-Q"])
        self.assertEqual((r["winner"], r["decided_by"]), ("T2-Q", "data_terms"))

    def test_hard_checks_then_escalate(self):
        r = rule3({"T0": 10, "T2-Q": 12}, {"T0": False, "T2-Q": False}, {"T0": 0.8, "T2-Q": 0.9})
        self.assertEqual((r["winner"], r["decided_by"]), ("T2-Q", "hard_check_pass_rate"))
        r = rule3({"T0": 10, "T2-Q": 12}, {"T0": False, "T2-Q": False}, {"T0": 0.9, "T2-Q": 0.9})
        self.assertIsNone(r["winner"])
        self.assertEqual(r["decided_by"], "unresolved_tie_escalate")


class PrepareTest(unittest.TestCase):
    def test_sheet_is_blind_complete_and_reproducible(self):
        rows, key = te.prepare_mqm(SOURCE, SYSTEMS, seed=7)
        self.assertEqual(len(rows), 4)
        self.assertEqual(set(rows[0]), set(te.SHEET_FIELDS))  # no system column
        self.assertEqual({(i["seg_id"], i["system"]) for i in key["items"].values()},
                         {(s, n) for s in SOURCE for n in SYSTEMS})
        self.assertEqual(te.prepare_mqm(SOURCE, SYSTEMS, seed=7), (rows, key))

    def test_missing_output_is_rejected(self):
        with self.assertRaises(ValueError):
            te.prepare_mqm(SOURCE, {"T0": {"S01": "x"}}, seed=1)

    def test_pairs_undo_left_right_order(self):
        rows, key = te.prepare_pairs(SOURCE, SYSTEMS, [("T2-G", "T0")], seed=3)
        choices = {pid: ("1" if p["output_1"] == "T2-G" else "2") for pid, p in key["pairs"].items()}
        self.assertEqual(te.pair_tally(choices, key), {"T2-G vs T0": {"n": 2, "same": 0, "wins": {"T2-G": 2}}})
        self.assertEqual(set(rows[0]), set(te.PAIR_SHEET_FIELDS))


class AnnotationTest(unittest.TestCase):
    def setUp(self):
        _, self.key = te.prepare_mqm(SOURCE, SYSTEMS, seed=7)
        self.ids = set(self.key["items"])

    def _rows(self, overrides=None):
        rows = [{"item_id": i, "category": "", "severity": "none"} for i in sorted(self.ids)]
        return rows + (overrides or [])

    def test_unrated_item_is_an_error(self):
        with self.assertRaises(ValueError):
            te.load_annotations(self._rows()[1:], self.ids, "r1")

    def test_none_plus_error_is_an_error(self):
        first = sorted(self.ids)[0]
        with self.assertRaises(ValueError):
            te.load_annotations(self._rows([{"item_id": first, "category": "accuracy", "severity": "major"}]), self.ids, "r1")

    def test_bad_category_and_severity(self):
        rows = [{"item_id": i, "category": "accuracy", "severity": "minor"} for i in self.ids]
        rows[0]["category"] = "grammar"
        with self.assertRaises(ValueError):
            te.load_annotations(rows, self.ids, "r1")
        rows[0].update(category="fluency/grammar", severity="huge")
        with self.assertRaises(ValueError):
            te.load_annotations(rows, self.ids, "r1")

    def test_points_per_100_words(self):
        t0_items = sorted(i for i, v in self.key["items"].items() if v["system"] == "T0")
        rows = [{"item_id": i, "category": "", "severity": "none"} for i in sorted(self.ids) if i not in t0_items]
        rows += [{"item_id": t0_items[0], "category": "accuracy/mistranslation", "severity": "major"},
                 {"item_id": t0_items[0], "category": "fluency", "severity": "minor"},
                 {"item_id": t0_items[1], "category": "", "severity": "none"}]
        mqm = te.mqm_by_system(te.load_annotations(rows, self.ids, "r1"), self.key, SOURCE)
        words = sum(len(t.split()) for t in SOURCE.values())  # 8 + 7 = 15
        self.assertEqual(mqm["T0"]["points"], 6)
        self.assertAlmostEqual(mqm["T0"]["points_per_100_words"], 600 / words)
        self.assertEqual(mqm["T0"]["errors"], {"accuracy:major": 1, "fluency:minor": 1})
        self.assertEqual(mqm["T2-G"]["points"], 0)

    def test_changed_output_after_rating_is_rejected(self):
        changed = {"T0": dict(SYSTEMS["T0"], S01="வேறு"), "T2-G": SYSTEMS["T2-G"]}
        with self.assertRaises(ValueError):
            te.verify_key(self.key, SOURCE, changed)


class TallyTest(unittest.TestCase):
    def test_digit_compliance(self):
        dc = te.digit_compliance(SOURCE, SYSTEMS)
        # S01 has "one" and 1 (one sachet in 1 litre); S02 has 5.
        self.assertEqual(dc["T0"]["numbers_in_source"], 3)
        self.assertEqual(dc["T0"]["found_as_digits"], 1)  # only "1"; "five" written as a word
        self.assertEqual(dc["T2-G"]["found_as_digits"], 2)

    def test_end_to_end_with_decision(self):
        _, key = te.prepare_mqm(SOURCE, SYSTEMS, seed=7)
        ids = set(key["items"])
        t0_s02 = next(i for i, v in key["items"].items() if v["system"] == "T0" and v["seg_id"] == "S02")
        clean = [{"item_id": i, "category": "", "severity": "none"} for i in sorted(ids - {t0_s02})]
        r1 = te.load_annotations(clean + [{"item_id": t0_s02, "category": "accuracy", "severity": "major"}], ids, "r1")
        r2 = te.load_annotations(clean + [{"item_id": t0_s02, "category": "accuracy", "severity": "minor"}], ids, "r2")
        report = te.tally(SOURCE, SYSTEMS["T2-G"], SYSTEMS, key, r1, r2, r1, checkset(), TERMS)
        self.assertEqual(report["agreement_before_discussion"]["has_major_or_critical"]["raw_agreement"], 0.75)
        self.assertEqual(report["chrf_vs_r1_reference_supporting_only"]["T2-G"]["corpus_chrf"], 100.0)
        # T0: 5 points / 15 words = 33.3 per 100; T2-G: 0. Beyond the tie margin.
        self.assertEqual(report["decision"]["rule3"]["winner"], "T2-G")
        self.assertTrue(report["decision"]["better_t2_beats_t0_beyond_tie_margin"])
        self.assertEqual(report["decision"]["suggested_pairs"], [["T2-G", "T0"]])

    def test_no_decision_without_agreed_labels(self):
        _, key = te.prepare_mqm(SOURCE, SYSTEMS, seed=7)
        ids = set(key["items"])
        r = te.load_annotations([{"item_id": i, "category": "", "severity": "none"} for i in ids], ids, "r1")
        report = te.tally(SOURCE, SYSTEMS["T0"], SYSTEMS, key, r, r, None, checkset(), TERMS)
        self.assertIsInstance(report["decision"], str)


class CliTest(unittest.TestCase):
    def test_prepare_then_tally(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "src.jsonl").write_text("".join(json.dumps({"id": k, "text": v}) + "\n" for k, v in SOURCE.items()), encoding="utf-8")
            specs = []
            for name, targets in SYSTEMS.items():
                path = d / f"{name}.jsonl"
                path.write_text("".join(json.dumps({"id": k, "target": v}, ensure_ascii=False) + "\n" for k, v in targets.items()), encoding="utf-8")
                specs += ["--system", f"{name}={path}"]
            with contextlib.redirect_stdout(io.StringIO()):
                te.main(["prepare-mqm", "--source", str(d / "src.jsonl"), *specs, "--out-dir", str(d / "m2"), "--seed", "1"])
            with (d / "m2" / "mqm_sheet.csv").open(encoding="utf-8-sig") as f:
                sheet = list(csv.DictReader(f))
            self.assertNotIn("T0", (d / "m2" / "mqm_sheet.csv").read_text(encoding="utf-8-sig"))
            ratings = d / "r.csv"
            te._write_csv(ratings, te.ANNOTATION_FIELDS, [{"item_id": r["item_id"], "severity": "none"} for r in sheet])
            with contextlib.redirect_stdout(io.StringIO()):
                te.main(["tally", "--source", str(d / "src.jsonl"), "--reference", str(d / "T2-G.jsonl"), *specs,
                         "--mqm-key", str(d / "m2" / "mqm_key.json"), "--r1", str(ratings), "--r2", str(ratings),
                         "--agreed", str(ratings), "--out", str(d / "report.json")])
            report = json.loads((d / "report.json").read_text(encoding="utf-8"))
            # Equal MQM points (a tie); only T0 has no-training terms, so it wins on data terms.
            self.assertEqual(report["decision"]["rule3"]["decided_by"], "data_terms")
            self.assertIn("hard_check_rules_frozen", report)


if __name__ == "__main__":
    unittest.main()
