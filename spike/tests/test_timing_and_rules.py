import tempfile
import unittest
import wave
from pathlib import Path

from hlspike.rules import rule6
from hlspike.timing_fit import residual_after_tempo, summarise, wav_duration_s


class TimingFitTest(unittest.TestCase):
    def test_tempo_residual(self):
        self.assertAlmostEqual(residual_after_tempo(1.10), 1.0)
        self.assertAlmostEqual(residual_after_tempo(1.30), 1.30 / 1.15)
        self.assertAlmostEqual(residual_after_tempo(0.50), 0.50 / 0.85)

    def test_summary(self):
        s = summarise({"S01": 1.0, "S02": 1.2, "S03": 1.4})
        self.assertAlmostEqual(s["pct_within_tolerance_at_1x"], 100 / 3)
        self.assertAlmostEqual(s["pct_within_tolerance_with_tempo"], 200 / 3)  # 1.4/1.15 = 1.217 is outside
        self.assertEqual(s["not_fitting_with_tempo"], ["S03"])

    def test_wav_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one_second.wav"
            with wave.open(str(path), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(b"\x00\x00" * 16000)
            self.assertAlmostEqual(wav_duration_s(path), 1.0)


class Rule6Test(unittest.TestCase):
    def test_plans(self):
        self.assertEqual(rule6(20, 60, 700, 1000, 2, False)["demo_plan"], "A")  # limits are inclusive
        self.assertEqual(rule6(25, 60, 700, 1000, 8, False)["demo_plan"], "C")
        self.assertEqual(rule6(25, 80, 900, 1000, 9, True)["demo_plan"], "B")
        self.assertEqual(rule6(25, 80, 900, 1000, 9, False)["demo_plan"], "D")

    def test_ram_limit_alone_blocks_live(self):
        result = rule6(10, 30, 701, 1000, 1, False)
        self.assertFalse(result["6a_cpu_live_capable"])
        self.assertFalse(result["adopt_kaggle"])


if __name__ == "__main__":
    unittest.main()
