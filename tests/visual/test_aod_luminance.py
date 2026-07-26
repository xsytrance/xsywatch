"""Deliberate-failure fixtures for the official WO-P7 AOD luminance gate.

WO-P7 allows an average luminance of at most 15% across the watch face,
sampled at ~10-minute intervals across a whole day. These tests prove the
gate measures the right quantity and actually rejects an over-limit face —
a gate that only ever passes proves nothing.

Run: python3 -m unittest discover -s tests/visual
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import aod_luminance as AL                       # noqa: E402

from PIL import Image, ImageDraw                 # noqa: E402

FACE = "aurelius"
LIMIT = 15.0


def disc(fill, size=(480, 480)):
    """A face-sized image filled uniformly.

    The whole square is filled rather than an inscribed ellipse: PIL's
    ellipse spans 0..479, i.e. radius 239.5, so a one-pixel rim inside the
    r=240 disc the metric measures would stay black and a "pure white
    face" would read 99.956% instead of 100%. That is a fixture artifact,
    not a metric error — the disc region selects the disc either way."""
    return Image.new("RGB", size, fill)


def disc_with_black_corners(fill, size=(480, 480)):
    """Bright disc, black corners — for the region-selection test."""
    im = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size[0] - 1, size[1] - 1), fill=fill)
    return im


class MetricTests(unittest.TestCase):
    """The metric must match the requirement's own anchors: an opaque
    white pixel is 100%, a black pixel is 0%."""

    def test_white_disc_is_100_percent(self):
        v = AL.luminance_variants(disc((255, 255, 255)), "disc")
        for k in ("channel_mean_srgb", "rec709_srgb", "rec709_linear"):
            self.assertAlmostEqual(v[k], 100.0, places=3,
                                   msg=f"{k} on pure white")

    def test_black_face_is_0_percent(self):
        v = AL.luminance_variants(disc((0, 0, 0)), "disc")
        self.assertAlmostEqual(v["max"], 0.0, places=6)

    def test_mid_grey_interpolates_linearly_on_encoded_values(self):
        """'RGB colors are interpolated linearly between these two values'
        — on encoded sRGB, 128/255 is ~50.2%."""
        v = AL.luminance_variants(disc((128, 128, 128)), "disc")
        self.assertAlmostEqual(v["channel_mean_srgb"], 100 * 128 / 255,
                               places=3)
        self.assertAlmostEqual(v["rec709_srgb"], 100 * 128 / 255, places=3)

    def test_gate_uses_the_strictest_reading(self):
        v = AL.luminance_variants(disc((128, 128, 128)), "disc")
        self.assertEqual(
            v["max"], max(v["channel_mean_srgb"], v["rec709_srgb"],
                          v["rec709_linear"]),
            "the gate must report the largest of the three readings")

    def test_disc_region_excludes_the_black_corners(self):
        """Excluding guaranteed-black corners RAISES the average, so the
        disc is the stricter region. If this ever inverts, the gate has
        become more permissive than intended."""
        im = disc_with_black_corners((200, 200, 200))
        d = AL.luminance_variants(im, "disc")["max"]
        f = AL.luminance_variants(im, "full")["max"]
        self.assertGreater(d, f)

    def test_disc_pixel_count_is_the_display_area(self):
        v = AL.luminance_variants(disc((255, 255, 255)), "disc")
        import math
        expected = math.pi * AL.DISC_R ** 2
        self.assertLess(abs(v["pixels"] - expected) / expected, 0.01)


class OverLimitRejectionTests(unittest.TestCase):
    """Deliberate failures: a face above 15% must be rejected."""

    def test_uniform_face_just_over_the_limit_fails(self):
        # 16% of 255 = 40.8 -> use 41 so every reading lands above 15
        v = AL.luminance_variants(disc((41, 41, 41)), "disc")
        self.assertGreater(v["channel_mean_srgb"], LIMIT)
        self.assertGreater(v["max"], LIMIT,
                           "a 16% uniform face must be over the limit")

    def test_uniform_face_just_under_the_limit_passes(self):
        v = AL.luminance_variants(disc((35, 35, 35)), "disc")
        self.assertLess(v["max"], LIMIT)

    def test_bright_region_over_the_limit_fails(self):
        """A face that is mostly black but has a large bright area — the
        realistic way an AOD design goes over budget."""
        im = disc((0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((120, 120, 360, 360), fill=(255, 255, 255))
        v = AL.luminance_variants(im, "disc")
        self.assertGreater(v["max"], LIMIT,
                           f"a 240x240 white block should exceed 15%, "
                           f"got {v['max']:.2f}%")

    def test_a_small_bright_accent_stays_under(self):
        im = disc((0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((220, 220, 260, 260), fill=(255, 255, 255))
        self.assertLess(AL.luminance_variants(im, "disc")["max"], LIMIT)

    def test_gate_verdict_flips_at_the_limit(self):
        """Drive the pass/fail decision the tool itself makes."""
        for level, expect_pass in ((30, True), (35, True), (41, False),
                                   (60, False), (128, False)):
            with self.subTest(level=level):
                v = AL.luminance_variants(disc((level,) * 3), "disc")
                self.assertEqual(v["max"] <= LIMIT, expect_pass,
                                 f"level {level} -> {v['max']:.2f}%")


class CommittedEvidenceTests(unittest.TestCase):
    """The committed WO-P7 evidence must be real, complete and passing."""

    EV = (REPO / "docs/reports/evidence/phase-4/aurelius/aod"
          / "wo_p7_luminance.json")

    def setUp(self):
        if not self.EV.exists():
            self.skipTest("no committed WO-P7 evidence yet")
        self.data = json.loads(self.EV.read_text(encoding="utf-8"))

    def test_sampling_covers_a_whole_day_at_ten_minute_intervals(self):
        s = self.data["sampling"]
        self.assertLessEqual(s["interval_minutes"], 10,
                             "WO-P7 requires ~10-minute intervals")
        self.assertEqual(s["samples"], 1440 // s["interval_minutes"])
        mins = [x["minute_of_day"] for x in self.data["samples"]]
        self.assertEqual(mins, sorted(mins))
        self.assertEqual(mins[0], 0)
        self.assertEqual(mins[-1], 1440 - s["interval_minutes"])

    def test_every_sample_is_under_the_limit(self):
        limit = self.data["limit_pct"]
        for s in self.data["samples"]:
            self.assertLessEqual(s["gate_value_pct"], limit, s["time"])
        for s in self.data["sensitivity"]:
            self.assertLessEqual(s["gate_value_pct"], limit, s["vary"])

    def test_reported_max_matches_the_samples(self):
        vals = ([s["gate_value_pct"] for s in self.data["samples"]]
                + [s["gate_value_pct"] for s in self.data["sensitivity"]])
        self.assertAlmostEqual(self.data["max_pct"], max(vals), places=9)

    def test_evidence_declares_pass_only_when_it_passes(self):
        self.assertEqual(self.data["pass"],
                         self.data["max_pct"] <= self.data["limit_pct"])

    def test_evidence_is_bound_to_the_current_visual_version(self):
        import tomllib
        with open(REPO / "watchfaces" / FACE / "visual/states.toml",
                  "rb") as fh:
            g = tomllib.load(fh)["goldens"]
        current = g.get("proposed_version") or g["approved_version"]
        self.assertEqual(
            self.data["visual_version"], current,
            "the committed WO-P7 evidence is for a different visual "
            "version than the one the contract currently points at")

    def test_sensitivity_covers_non_time_inputs(self):
        varied = " ".join(s["vary"] for s in self.data["sensitivity"])
        for token in ("day=", "battery=", "heart_rate="):
            self.assertIn(token, varied,
                          f"sensitivity sweep does not vary {token}")


if __name__ == "__main__":
    unittest.main()
