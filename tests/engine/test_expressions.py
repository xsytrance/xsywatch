"""Expression builders must emit the exact strings proven on-device by the
Phase-1 Aurelius release (baseline watchface.xml, SHA recorded in
docs/reports/evidence/phase-2/aurelius/baseline/)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))

from wffgen import expressions as X


class TestAureliusBaselineParity(unittest.TestCase):
    """Each expected string below is copied verbatim from the baseline XML."""

    def test_hour_angle(self):
        self.assertEqual(X.hour_angle(), "([HOUR_0_11] + [MINUTE] / 60) * 30")

    def test_minute_angle(self):
        self.assertEqual(X.minute_angle(), "([MINUTE] + [SECOND] / 60) * 6")

    def test_seconds_cage_angle(self):
        self.assertEqual(X.seconds_angle(),
                         "([SECOND] + [MILLISECOND] / 1000) * 6")

    def test_gear_forward(self):
        self.assertEqual(
            X.rotation_continuous(40),
            "(([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000) * 40) % 360")

    def test_gear_reverse(self):
        self.assertEqual(
            X.rotation_continuous(24, reverse=True),
            "360 - ((([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000) * 24) % 360)")

    def test_hr_oscillator(self):
        self.assertEqual(
            X.hr_oscillator_angle(180, 35),
            "180 + 35 * sin(([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)"
            " * (clamp(([HEART_RATE] < 30 ? 70 : [HEART_RATE]), 40, 200))"
            " * 0.10472)")

    def test_battery_gauge(self):
        self.assertEqual(
            X.gauge_angle(292.5, 45.0),
            "292.5 + 45.0 * clamp([BATTERY_PERCENT], 0, 100) / 100")

    def test_parallax(self):
        self.assertEqual(
            X.parallax_offset(0, 3, "X"),
            "0 + 3 * clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45")
        self.assertEqual(
            X.parallax_offset(0, 14, "Y"),
            "0 + 14 * clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45")

    def test_sheen_breathing(self):
        self.assertEqual(
            X.breathing_alpha(150, 60, 0.45),
            "150 + 60*sin(([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)*0.45)")


class TestExpressionSafety(unittest.TestCase):
    def test_parallax_rejects_bad_axis(self):
        with self.assertRaises(ValueError):
            X.parallax_offset(0, 3, "Z")

    def test_hr_always_clamped(self):
        self.assertIn("clamp", X.heart_rate_bpm())

    def test_num_determinism(self):
        self.assertEqual(X.num(6), "6")
        self.assertEqual(X.num(6.0), "6.0")
        self.assertEqual(X.num(0.10472), "0.10472")
        self.assertEqual(X.num("45.0"), "45.0")


class TestRatioNormalization(unittest.TestCase):
    """Merge blocker 2 (Phase-2 review): ratio() over arbitrary [lo, hi]."""

    def test_zero_based_fast_path_is_aurelius_battery_string(self):
        self.assertEqual(X.ratio("[BATTERY_PERCENT]", 0, 100),
                         "clamp([BATTERY_PERCENT], 0, 100) / 100")

    def test_nonzero_based_normalizes_correctly(self):
        # 40..200: value 40 must map to 0, 200 to 1.
        self.assertEqual(
            X.ratio("[HEART_RATE]", 40, 200),
            "(clamp([HEART_RATE], 40, 200) - 40) / 160")

    def test_nonzero_float_range(self):
        self.assertEqual(
            X.ratio("[ACCELEROMETER_ANGLE_X]", -45, 45),
            "(clamp([ACCELEROMETER_ANGLE_X], -45, 45) - -45) / 90")

    def test_invalid_ranges_rejected(self):
        with self.assertRaises(ValueError):
            X.ratio("[HEART_RATE]", 200, 40)
        with self.assertRaises(ValueError):
            X.ratio("[HEART_RATE]", 100, 100)

    def test_battery_gauge_parity_preserved(self):
        self.assertEqual(
            X.gauge_angle(292.5, 45.0),
            "292.5 + 45.0 * clamp([BATTERY_PERCENT], 0, 100) / 100")


if __name__ == "__main__":
    unittest.main()
