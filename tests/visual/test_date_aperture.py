"""Date-aperture containment tests (Phase-3 r1 review, revision r2).

The plate art draws a framed date window; the live BitmapFont date renders
into it. Revision r1 shipped an opening only 14.5 px tall for a 24 px text
presentation, so the digits overhung the frame. These tests make that class
of defect impossible to reintroduce silently: every valid day 1..31 must
keep the mandated clear margin from the inner frame, in normal AND ambient.

Run: python3 -m unittest discover -s tests/visual
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import visuallib as V              # noqa: E402
import date_aperture_proof as DAP  # noqa: E402

FACE = "aurelius"


class DateApertureContainmentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = DAP.evaluate(FACE)
        cls.contract = V.VisualContract.load(FACE)

    # -- the requirement itself ----------------------------------------

    def test_every_day_1_to_31_fits_with_clear_margin(self):
        need = self.data["min_clear_margin_px"]
        bad = [(r["day"], "AOD" if r["ambient"] else "normal", r["margins"])
               for r in self.data["results"] if r["worst_margin"] < need]
        self.assertEqual(bad, [], f"days violating the {need}px clear "
                                  f"margin: {bad}")

    def test_covers_all_days_both_modes(self):
        seen = {(r["day"], r["ambient"]) for r in self.data["results"]}
        expected = {(d, a) for d in range(1, 32) for a in (False, True)}
        self.assertEqual(seen, expected)
        self.assertEqual(self.data["renders_checked"], 62)

    def test_no_glyph_touches_or_crosses_the_frame(self):
        for r in self.data["results"]:
            with self.subTest(day=r["day"], ambient=r["ambient"]):
                for side, m in r["margins"].items():
                    self.assertGreater(
                        m, 0, f"day {r['day']} ink crosses the inner frame "
                              f"on the {side}")

    def test_single_digit_days_are_optically_centred(self):
        """A lone digit must not drift to one side of the window."""
        for r in self.data["results"]:
            if r["day"] >= 10:
                continue
            with self.subTest(day=r["day"], ambient=r["ambient"]):
                lo, ro = r["margins"]["left"], r["margins"]["right"]
                tol = self.contract.raw["date_aperture"][
                    "max_center_offset_px"]
                self.assertLessEqual(
                    abs(lo - ro) / 2, tol,
                    f"day {r['day']} is off-centre by "
                    f"{abs(lo - ro) / 2:.2f} px: left {lo}, right {ro}")

    # -- contract integrity --------------------------------------------

    def test_contract_declares_the_aperture(self):
        ap = self.contract.raw["date_aperture"]
        x0, y0, x1, y1 = DAP.inner_bounds(ap)
        self.assertGreater(x1 - x0, 0)
        self.assertGreater(y1 - y0, 0)
        self.assertGreaterEqual(ap["min_clear_margin_px"], 2.0)
        for day in (1, 8, 11, 22, 28, 31):
            self.assertIn(day, ap["proof_days"])

    def test_inner_bounds_derive_from_centre_and_size(self):
        ap = self.contract.raw["date_aperture"]
        x0, y0, x1, y1 = DAP.inner_bounds(ap)
        w, h = ap["inner_size_px"]
        cx, cy = ap["center_px"]
        self.assertAlmostEqual(x1 - x0, w, places=6)
        self.assertAlmostEqual(y1 - y0, h, places=6)
        self.assertAlmostEqual((x0 + x1) / 2, cx, places=6)
        self.assertAlmostEqual((y0 + y1) / 2, cy, places=6)
        self.assertNotIn("inner_bounds_px", ap,
                         "bounds must be derived, not declared twice")

    def test_committed_proof_artifacts_are_current(self):
        pdir = REPO / "watchfaces" / FACE / "visual/proofs"
        sheet = pdir / "date_aperture_r2.png"
        bounds = pdir / "date_aperture_r2.json"
        self.assertTrue(sheet.exists(), "proof sheet must be committed")
        self.assertTrue(bounds.exists(), "bounds json must be committed")
        committed = json.loads(bounds.read_text(encoding="utf-8"))
        self.assertEqual(committed["renders_checked"], 62)
        self.assertEqual(committed["violations"], [])
        self.assertAlmostEqual(committed["worst_margin_px"],
                               self.data["worst_margin_px"], places=2,
                               msg="committed proof is stale — rerun "
                                   "tools/date_aperture_proof.py")

    # -- deliberate failure: the gate must actually bite ---------------

    def test_gate_catches_an_undersized_aperture(self):
        """Reproduces the r1 defect: shrink the declared opening to the r1
        geometry and the proof must report violations."""
        contract = V.VisualContract.load(FACE)
        scene = V.Scene.load(FACE)
        # r1 inner opening was 31.3 x 14.5 px about the same centre
        cx, cy = contract.raw["date_aperture"]["center_px"]
        r1 = [cx - 15.65, cy - 7.25, cx + 15.65, cy + 7.25]
        need = 2.0
        violations = 0
        for day in (1, 11, 28, 30):
            m = DAP.measure_day(scene, contract, day, ambient=False)
            bx0, by0, bx1, by1 = m["bounds"]
            worst = min(bx0 - r1[0], by0 - r1[1], r1[2] - bx1, r1[3] - by1)
            if worst < need:
                violations += 1
        self.assertEqual(violations, 4,
                         "the r1 aperture geometry must fail the clear-margin "
                         "requirement for every sampled day")

    def test_gate_catches_an_oversized_glyph_set(self):
        """If a future typeface inks wider cells, containment must fail."""
        contract = V.VisualContract.load(FACE)
        scene = V.Scene.load(FACE)
        ap = contract.raw["date_aperture"]
        x0, y0, x1, y1 = DAP.inner_bounds(ap)
        m = DAP.measure_day(scene, contract, 30, ambient=False)
        ink_w = m["ink_size"][0]
        # a hypothetical 25% wider typeface at the same cell height
        grown = ink_w * 1.25
        centre = (x0 + x1) / 2
        margin = (centre - grown / 2) - x0
        self.assertLess(margin, ap["min_clear_margin_px"],
                        "a 25% wider typeface should breach the margin, "
                        "proving the check is sensitive to ink growth")


if __name__ == "__main__":
    unittest.main()
