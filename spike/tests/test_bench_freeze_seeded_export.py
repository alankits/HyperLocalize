import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hlspike import seeded_eval
from hlspike.bench import environment, run_once, summarise
from hlspike.freeze import changed_since_freeze, write_freeze
from hlspike.script_export import read_segments
from tests.fixtures import checkset


class BenchTest(unittest.TestCase):
    def test_run_once_records_time_memory_and_exit_code(self):
        ok = run_once([sys.executable, "-c", "x = bytearray(20_000_000)"])
        self.assertEqual(ok["exit_code"], 0)
        self.assertGreater(ok["wall_s"], 0)
        self.assertGreater(ok["peak_rss_mb"], 15)  # the child allocated about 20 MB
        self.assertEqual(run_once([sys.executable, "-c", "raise SystemExit(3)"])["exit_code"], 3)

    def test_summary_and_projection(self):
        runs = [{"wall_s": 9.0, "peak_rss_mb": 100, "exit_code": 0}, {"wall_s": 5.0, "peak_rss_mb": 120, "exit_code": 0}, {"wall_s": 6.0, "peak_rss_mb": 110, "exit_code": 0}]
        s = summarise(runs, project_segments=600)
        self.assertEqual((s["cold_wall_s"], s["median_wall_s"], s["max_wall_s"], s["peak_rss_mb"]), (9.0, 6.0, 9.0, 120))
        self.assertAlmostEqual(s["projected_hours_for_project"], 1.0)

    def test_environment_has_cpu_count(self):
        self.assertIn("cpu_count", environment())


class FreezeTest(unittest.TestCase):
    def test_detects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "rules.txt").write_text("v1")
            frozen = base / "FROZEN.json"
            self.assertIsNone(changed_since_freeze(base, frozen))
            write_freeze(base, frozen, ["rules.txt"])
            self.assertEqual(changed_since_freeze(base, frozen), [])
            (base / "rules.txt").write_text("v2")
            self.assertEqual(changed_since_freeze(base, frozen), ["rules.txt"])


class SeededEvalTest(unittest.TestCase):
    items = [
        {"id": "E1", "source": "Give 100 ml.", "target": "150 மில்லி கொடுங்கள்.", "error_type": "number_wrong_western", "expected": "FAIL"},
        {"id": "E2", "source": "Give 100 ml.", "target": "நூறு மில்லி கொடுங்கள்.", "error_type": "number_as_word", "expected": "UNVERIFIABLE"},
        {"id": "E3", "source": "Give 100 ml.", "target": "100 மில்லி கொடுங்கள்.", "error_type": "unit_wrong", "expected": "FAIL"},  # a miss
        {"id": "C1", "source": "Give 100 ml.", "target": "100 மில்லி கொடுங்கள்.", "error_type": "", "expected": "CLEAN"},
        {"id": "A1", "source": "Do not boil it.", "target": "அதைக் கொதிக்க வையுங்கள்.", "error_type": "reversal", "expected": "AI_FLAG"},
    ]

    def test_catch_rates(self):
        report = seeded_eval.evaluate(self.items, checkset())
        self.assertEqual(report["hard_check_catch_rate"]["numerator"], 2)
        self.assertEqual(report["hard_check_catch_rate"]["denominator"], 3)
        self.assertEqual(report["hard_check_catch_rate_excluding_unverifiable"]["numerator"], 1)
        self.assertEqual(report["by_error_type"]["unit_wrong"]["missed_ids"], ["E3"])
        self.assertEqual(report["false_alarm_rate"]["value"], 0)
        self.assertEqual(report["ai_flag_items"], {"n": 1, "incidentally_caught": 0})

    def test_refuses_when_rules_changed(self):
        with mock.patch.object(seeded_eval, "changed_since_freeze", return_value=["data/units.json"]):
            with self.assertRaises(SystemExit) as ctx:
                seeded_eval.main(["--seeded", "unused.jsonl"])
        self.assertIn("changed since the freeze", str(ctx.exception))


class ScriptExportTest(unittest.TestCase):
    def test_reads_the_27_segments_only(self):
        segments = read_segments()
        self.assertEqual(len(segments), 27)
        self.assertEqual((segments[0]["id"], segments[0]["scene"]), ("S01", 1))
        self.assertEqual((segments[-1]["id"], segments[-1]["scene"]), ("S27", 5))
        self.assertNotIn("C1", [s["id"] for s in segments])


if __name__ == "__main__":
    unittest.main()
