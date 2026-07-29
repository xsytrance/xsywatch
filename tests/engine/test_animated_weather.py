"""Guards for animated weather and the wrist-motion vocabulary.

Everything here is a failure mode that already happened once during the build
and would not have announced itself: a scroll that jumps on the hour, weather
that escapes its window, layers that roll about different centres, a Compare
with no children. None of them fail loudly — several look fine in a still.
"""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine"))
sys.path.insert(0, str(REPO / "tools"))

from wffgen import components as C           # noqa: E402
from wffgen import expressions as X          # noqa: E402
from wffgen.model import document            # noqa: E402
from wffgen.profiles import dim              # noqa: E402

AOD = dim(0, 0.4, 0.1, "EASE_OUT")
BOX = {"x": 170, "y": 297, "width": 140, "height": 140}
CLIP_BOX = {"x": 105, "y": 232, "width": 270, "height": 248}
OVERLAYS = {"wx_rain": "ba_ov_rain", "wx_storm": "ba_ov_storm",
            "wx_snow": "ba_ov_snow", "wx_dull": "ba_ov_cloud",
            "wx_night": "ba_ov_stars"}


class TestSeamlessLoops(unittest.TestCase):
    """A scroll period must divide the 3600s time base or the loop jumps once
    an hour — rare enough to pass review, obvious enough to ruin the effect."""

    def test_rejects_period_that_does_not_divide_an_hour(self):
        for bad in (7.0, 3.5, 11.0, 13.0):
            with self.assertRaises(ValueError, msg=f"{bad}s accepted"):
                X.scroll_offset(64, bad)

    def test_accepts_hour_dividing_periods(self):
        for good in (1.0, 1.2, 1.5, 2.4, 6.0, 24.0, 45.0):
            X.scroll_offset(64, good)

    def test_rejects_nonpositive_period(self):
        for bad in (0.0, -2.0):
            with self.assertRaises(ValueError):
                X.scroll_offset(64, bad)

    def test_scroll_spans_exactly_one_tile(self):
        # The distance must be the tile period: scrolling by anything else
        # lands the texture somewhere it does not repeat, and the seam shows.
        self.assertIn("64.0 * fract(", X.scroll_offset(64, 2.4))


class TestMotionVocabulary(unittest.TestCase):
    def test_negative_amplitude_folds_into_subtraction(self):
        # "+ -24.0 * ..." has no production in the format's operator list.
        got = X.tilt_shift(-24, "X", 45)
        self.assertTrue(got.startswith("0 - 24.0 *"), got)
        self.assertNotIn("-24.0", got)

    def test_positive_amplitude_is_bare(self):
        self.assertTrue(X.tilt_shift(20, "Y", 40).startswith("20.0 *"))

    def test_rejects_unknown_axis(self):
        with self.assertRaises(ValueError):
            X.tilt_shift(5, "Q")

    def test_accelerometer_guard_falls_back_to_neutral(self):
        got = X.if_accelerometer(X.tilt_shift(-24, "X", 45))
        self.assertIn("[ACCELEROMETER_IS_SUPPORTED] ?", got)
        self.assertTrue(got.rstrip().endswith(": 0)"), got)

    def test_flash_needs_a_spike_not_a_throb(self):
        with self.assertRaises(ValueError):
            X.flash_alpha(255, sharpness=1.0)

    def test_raw_axes_are_known_sources(self):
        from wffgen import KNOWN_SOURCES
        for src in ("ACCELEROMETER_X", "ACCELEROMETER_Y", "ACCELEROMETER_Z",
                    "ACCELEROMETER_ANGLE_Z", "ACCELEROMETER_ANGLE_XY",
                    "ACCELEROMETER_IS_SUPPORTED"):
            self.assertIn(src, KNOWN_SOURCES)


class TestAnimatedWeather(unittest.TestCase):
    def build(self, **kw):
        args = dict(scenes={}, overlays=OVERLAYS, tile=40,
                    periods={"wx_dull": 30.0, "wx_rain": 1.5},
                    roll_gain_deg=7.0, shift_x_px=6.0, shift_y_px=8.0,
                    clip="ba_wx_clip", clip_box=CLIP_BOX,
                    flash="ba_ov_flash")
        args.update(kw)
        return C.animated_weather("z03_wx", BOX, AOD, **args)

    def test_unclipped_overlays_are_refused(self):
        # An unclipped overlay does not fail subtly: it rains across the dial.
        with self.assertRaises(ValueError) as ctx:
            self.build(clip=None, clip_box=None)
        self.assertIn("escapes", str(ctx.exception))

    def test_aperture_stands_in_for_a_clip(self):
        self.build(clip=None, clip_box=None, aperture=True)

    def test_clip_without_box_is_refused(self):
        with self.assertRaises(ValueError):
            self.build(clip_box=None)

    def test_unknown_branch_is_refused(self):
        with self.assertRaises(ValueError):
            self.build(overlays={"wx_drizzle": "ba_ov_rain"})

    def test_part_names_stay_lexically_ordered(self):
        # The face validator compares z-names as strings, so an unpadded _10_
        # sorts before _2_ and trips the z-order check.
        root = ET.fromstring(document(self.build().elems[0]).split("?>", 1)[1])
        names = [p.get("name") for p in root.iter("PartImage")]
        self.assertGreater(len(names), 10)
        self.assertEqual(names, sorted(names))

    def test_clip_is_last_in_every_branch_and_never_moves(self):
        root = ET.fromstring(document(self.build().elems[0]).split("?>", 1)[1])
        branches = list(root.findall("Compare")) + list(root.findall("Default"))
        self.assertTrue(branches)
        for br in branches:
            kids = [p for p in br if p.tag == "PartImage"]
            self.assertTrue(kids[-1].get("name").endswith("_clip"),
                            f"clip not last in {br.get('expression')}")
            # A surround that tilts is a surround with a gap behind it.
            self.assertIsNone(kids[-1].find("Gyro"))

    def test_scene_and_overlay_roll_about_the_same_point(self):
        c = self.build(scenes={"wx_rain": "ba_wx_rain"},
                       overlays={"wx_rain": "ba_ov_rain"})
        root = ET.fromstring(document(c.elems[0]).split("?>", 1)[1])
        br = root.find("Compare[@expression='wx_rain']")
        centres = []
        for p in br.findall("PartImage"):
            if p.get("name").endswith("_clip"):
                continue
            centres.append((
                float(p.get("x")) + float(p.get("pivotX")) * float(p.get("width")),
                float(p.get("y")) + float(p.get("pivotY")) * float(p.get("height"))))
        self.assertEqual(len(centres), 2)
        self.assertAlmostEqual(centres[0][0], centres[1][0], places=3)
        self.assertAlmostEqual(centres[0][1], centres[1][1], places=3)

    def test_every_gyro_axis_is_guarded(self):
        root = ET.fromstring(document(self.build().elems[0]).split("?>", 1)[1])
        gyros = list(root.iter("Gyro"))
        self.assertTrue(gyros)
        for g in gyros:
            for attr, value in g.attrib.items():
                self.assertIn("[ACCELEROMETER_IS_SUPPORTED]", value,
                              f"unguarded Gyro {attr}")


class TestRadarWeather(unittest.TestCase):
    def build(self):
        return C.radar_weather("z09_returns",
                               {"x": 184, "y": 305, "width": 113,
                                "height": 113}, AOD,
                               "wh_rdr_light", "wh_rdr_heavy",
                               roll_gain_deg=5.0, shift_x_px=4.0,
                               shift_y_px=6.0)

    def test_no_empty_compare_and_no_empty_default(self):
        # conditionElement.xsd requires a Compare to have at least one child,
        # and the dry branches paint nothing, so they must not be emitted.
        root = ET.fromstring(document(self.build().elems[0]).split("?>", 1)[1])
        for cmp_ in root.findall("Compare"):
            self.assertTrue(len(cmp_), f"empty Compare {cmp_.get('expression')}")
        self.assertIsNone(root.find("Default"))

    def test_night_is_not_a_branch_so_wet_nights_still_paint(self):
        root = ET.fromstring(document(self.build().elems[0]).split("?>", 1)[1])
        names = {e.get("name") for e in root.iter("Expression")}
        self.assertNotIn("wx_night", names)
        self.assertIn("wx_rain", names)

    def test_every_declared_expression_is_used(self):
        # The schema keyrefs Compare/@expression to a declared Expression;
        # unused declarations are legal but signal a dropped branch.
        root = ET.fromstring(document(self.build().elems[0]).split("?>", 1)[1])
        declared = {e.get("name") for e in root.iter("Expression")}
        used = {c.get("expression") for c in root.findall("Compare")}
        self.assertEqual(declared, used)


class TestSurroundGeometry(unittest.TestCase):
    """The surround must cover the overlay's whole travel, on both axes,
    including the growth a roll adds to a rectangle's bounding box."""

    def test_swept_covers_scroll_and_gyro_and_roll(self):
        import math
        from make_weather_overlays import FACES, swept, SAFETY_PX, CANVAS
        for face, c in FACES.items():
            if c.get("radar_only"):
                continue
            sx, sy, sw, sh = swept(face)
            (ox, oy), (bw, bh) = c["origin"], c["box"]
            t, g, r = c["tile"], c["gyro"], math.radians(c["roll"])
            # Worst case: the taller scroller, rolled, shifted, at full travel.
            w, h = bw + t, bh + t
            rw = w * math.cos(r) + h * math.sin(r)
            rh = w * math.sin(r) + h * math.cos(r)
            cx, cy = ox + bw / 2.0, oy + bh / 2.0
            need_x0 = cx - rw / 2.0 - t / 2.0 - g
            need_x1 = cx + rw / 2.0 + t / 2.0 + g
            need_y0 = cy - rh / 2.0 - t / 2.0 - g
            need_y1 = cy + rh / 2.0 + t / 2.0 + g
            self.assertLessEqual(sx, need_x0 + SAFETY_PX, f"{face} left")
            self.assertLessEqual(need_y0 - SAFETY_PX, sy + SAFETY_PX,
                                 f"{face} top")
            # Clamped at the dial edge, where nothing is visible anyway.
            self.assertLessEqual(sx + sw, CANVAS, f"{face} right off-canvas")
            self.assertLessEqual(sy + sh, CANVAS, f"{face} bottom off-canvas")
            self.assertTrue(sx + sw >= min(need_x1, CANVAS) - SAFETY_PX,
                            f"{face} right short")
            self.assertTrue(sy + sh >= min(need_y1, CANVAS) - SAFETY_PX,
                            f"{face} bottom short")

    def test_face_specs_stay_within_their_motion_budget(self):
        # The surrounds were cut for these numbers. A spec that asks for more
        # wrist travel than its clip was sized for lets weather escape.
        import tomllib
        from make_weather_overlays import FACES
        for face, c in FACES.items():
            spec = REPO / "watchfaces" / face / "engine/face.toml"
            data = tomllib.loads(spec.read_text())
            for comp in data["components"]:
                if comp["type"] not in ("animated_weather", "radar_weather"):
                    continue
                self.assertLessEqual(comp.get("roll_gain_deg", 0.0),
                                     c["roll"] if c["roll"] else 90,
                                     f"{face} roll over budget")
                for axis in ("shift_x_px", "shift_y_px"):
                    self.assertLessEqual(comp.get(axis, 0.0),
                                         c["gyro"] if c["gyro"] else 90,
                                         f"{face} {axis} over budget")


if __name__ == "__main__":
    unittest.main()
