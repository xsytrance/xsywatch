"""Component factories: structure, metadata contract, and validation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))

from wffgen import components as C
from wffgen.model import document, Elem
from wffgen.profiles import AmbientPolicy, MotionClass, dim
from wffgen.spec import FaceSpec
from wffgen.validation import SpecError, validate_face

BOX = {"x": 100, "y": 100, "width": 80, "height": 80}
AOD = dim(90, 0.4, 0.1)


def wrap(components, width=480, height=480):
    spec = FaceSpec("test", width, height, 4, "ANALOG", "10:09:35",
                    "#FF000000",
                    {"package": "p", "version_code": 1, "version_name": "1"},
                    [], list(components))
    root = Elem("WatchFace", {"width": str(width), "height": str(height)})
    scene = Elem("Scene", {"backgroundColor": "#FF000000"})
    for comp in spec.components:
        for e in comp.elems:
            scene.child(e)
    root.child(scene)
    return spec, document(root)


class TestComponentContract(unittest.TestCase):
    def test_every_factory_declares_motion_and_aod(self):
        comps = [
            *C.background_pair("bg", "bg_aod", (3, 3)),
            C.rotating_image("z10_a", "gear", BOX, 40, AOD),
            C.seconds_rotor("z22_b", "cage", BOX, AOD),
            C.hr_balance("z21_c", "bal", BOX, AOD),
            C.battery_needle("z31_d", "needle", AOD, 292.5, 45.0),
            C.date_text("z30_e", BOX, AOD, "f", 24, "#FFFFFF"),
            C.sheen("z40_f", "sheen", AOD, 150, 60, 0.45, (40, 14)),
            C.analog_hand("z50_g", "hh", AOD, "hour"),
            C.static_image("z52_h", "hub", BOX, AOD),
            C.text_line("z60_i", BOX, AOD, "f", 24, "#FFFFFF",
                        "%02d:%02d", ["[HOUR_0_23]", "[MINUTE]"]),
        ]
        for comp in comps:
            self.assertIsInstance(comp.motion_class, MotionClass, comp.name)
            self.assertIsInstance(comp.aod, AmbientPolicy, comp.name)
            self.assertTrue(comp.elems, comp.name)

    def test_rotating_image_records_direction(self):
        cw = C.rotating_image("z10_a", "g", BOX, 40, AOD)
        ccw = C.rotating_image("z11_b", "g", BOX, 24, AOD, reverse=True)
        self.assertIn("CW", cw.notes)
        self.assertIn("CCW", ccw.notes)
        self.assertIn("360 - ", ccw.elems[0].children[1].attrs["value"])

    def test_rotating_parts_get_pivot(self):
        comp = C.rotating_image("z10_a", "g", BOX, 40, AOD)
        self.assertEqual(comp.elems[0].attrs["pivotX"], "0.5")

    def test_analog_hand_rejects_unknown(self):
        with self.assertRaises(ValueError):
            C.analog_hand("z50_x", "r", AOD, "seconds-ish")

    def test_date_text_inline_template(self):
        comp = C.date_text("z30_date", BOX, AOD, "aur", 24, "#FFFFFF")
        _, xml = wrap([comp])
        self.assertIn(
            '<Text align="CENTER"><BitmapFont family="aur" size="24" '
            'color="#FFFFFF"><Template>%d<Parameter expression="[DAY]" />'
            "</Template></BitmapFont></Text>", xml)


class TestValidation(unittest.TestCase):
    def test_clean_face_passes(self):
        spec, xml = wrap([
            C.rotating_image("z10_a", "gear", BOX, 40, AOD),
            C.static_image("z52_h", "hub", BOX, AOD),
        ])
        validate_face(spec, xml, {"gear", "hub"})  # no raise

    def test_duplicate_names_fail(self):
        spec, xml = wrap([
            C.static_image("z52_h", "hub", BOX, AOD),
            C.static_image("z52_h", "hub", BOX, AOD),
        ])
        with self.assertRaises(SpecError) as cm:
            validate_face(spec, xml, {"hub"})
        self.assertTrue(any("duplicate" in p for p in cm.exception.problems))

    def test_z_order_violation_fails(self):
        spec, xml = wrap([
            C.static_image("z52_h", "hub", BOX, AOD),
            C.static_image("z10_a", "gear", BOX, AOD),
        ])
        with self.assertRaises(SpecError) as cm:
            validate_face(spec, xml, {"hub", "gear"})
        self.assertTrue(any("z-order" in p for p in cm.exception.problems))

    def test_missing_resource_fails(self):
        spec, xml = wrap([C.static_image("z52_h", "hub", BOX, AOD)])
        with self.assertRaises(SpecError) as cm:
            validate_face(spec, xml, {"other"})
        self.assertTrue(any("missing" in p for p in cm.exception.problems))

    def test_out_of_canvas_fails(self):
        bad = {"x": 460, "y": 0, "width": 80, "height": 80}
        spec, xml = wrap([C.static_image("z52_h", "hub", bad, AOD)])
        with self.assertRaises(SpecError) as cm:
            validate_face(spec, xml, {"hub"})
        self.assertTrue(any("canvas" in p for p in cm.exception.problems))

    def test_bad_name_convention_fails(self):
        spec, xml = wrap([C.static_image("Hub Layer", "hub", BOX, AOD)])
        with self.assertRaises(SpecError):
            validate_face(spec, xml, {"hub"})

    def test_ambient_alpha_bounds(self):
        with self.assertRaises(ValueError):
            AmbientPolicy(300)
        with self.assertRaises(ValueError):
            AmbientPolicy(100, interpolation="BOUNCE")


if __name__ == "__main__":
    unittest.main()
