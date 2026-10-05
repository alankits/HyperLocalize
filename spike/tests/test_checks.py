import json
import tempfile
import unittest
from pathlib import Path

from hlspike import checks
from hlspike.checks import CheckSet, check_segment, check_structure
from hlspike.numbers import FAIL, PASS, UNVERIFIABLE
from tests.fixtures import checkset


class StructureTest(unittest.TestCase):
    def test_structural_failures(self):
        self.assertEqual(check_structure("Stir well.", "  ")[0], FAIL)
        self.assertEqual(check_structure("Stir well.", "stir   well.")[0], FAIL)
        self.assertEqual(check_structure("Stir well.", "Stir it well நன்கு")[0], FAIL)  # mostly Latin
        self.assertEqual(check_structure("Stir.", "நன்றாகக் கலக்கவும்.", max_chars=5)[0], FAIL)

    def test_tamil_with_a_latin_abbreviation_passes(self):
        self.assertEqual(check_structure("Give 100 ml.", "100 ml கொடுங்கள்."), (PASS, []))


class SegmentTest(unittest.TestCase):
    def test_overall_pass(self):
        report = check_segment("S13", "Give 50 to 100 ml of zinc.", "50 முதல் 100 மில்லி துத்தநாகம் கொடுங்கள்.", checkset())
        self.assertEqual(report.overall, PASS, report.checks)

    def test_fail_outranks_unverifiable(self):
        # 150 is wrong (FAIL); "sachet" has no Tamil forms (UNVERIFIABLE).
        report = check_segment("X", "Give 1 sachet in 100 ml.", "1 பொட்டலம் 150 மில்லி", checkset())
        self.assertEqual(report.checks["glossary"]["status"], UNVERIFIABLE)
        self.assertEqual(report.overall, FAIL)

    def test_real_data_files_load(self):
        real = CheckSet.load()
        self.assertGreater(len(real.units), 0)
        self.assertGreater(len(real.glossary), 0)
        self.assertGreater(len(real.stems), 0)
        # Real glossary has no Tamil forms yet, so a term gives UNVERIFIABLE, never PASS.
        self.assertEqual(check_segment("S20", "Ask a health worker about zinc.", "ஒரு சுகாதார பணியாளரிடம் கேளுங்கள்.", real).overall, UNVERIFIABLE)

    def test_cli_writes_one_result_per_segment(self):
        with tempfile.TemporaryDirectory() as tmp:
            segs, out = Path(tmp) / "segs.jsonl", Path(tmp) / "out.jsonl"
            segs.write_text(json.dumps({"id": "S08", "source": "Do not add sugar or salt.", "target": "சர்க்கரை அல்லது உப்பு சேர்க்க வேண்டாம்."}) + "\n", encoding="utf-8")
            checks.main(["--segments", str(segs), "--out", str(out)])
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["id"] for r in rows], ["S08"])
        self.assertEqual(rows[0]["overall"], PASS)


if __name__ == "__main__":
    unittest.main()
