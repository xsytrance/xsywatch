"""Generality fixtures: the engine is not hard-coded to Aurelius.

Both fixtures generate deterministically, parse as XML, pass structural
validation with synthetic resource sets, and contain no Aurelius resource
names or art. Their generated XML is also written to build/ during the WFF
validator evidence run (tools/wff_validate.sh).
"""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine"))

from wffgen.render import render_face
from wffgen.spec import load_spec
from wffgen.validation import validate_face

FIXTURES = Path(__file__).parent / "fixtures"
AURELIUS_RESOURCES = {"bg", "bg_aod", "gear_l", "gear_r", "balance", "cage",
                      "resv_needle", "sheen", "hour_hand", "min_hand", "hub"}


def synthetic_resources(xml: str) -> set[str]:
    root = ET.fromstring(xml)
    return {e.get("resource") for e in root.iter() if e.get("resource")}


class TestFixtures(unittest.TestCase):
    def render(self, name: str) -> str:
        spec = load_spec(FIXTURES / name)
        a, b = render_face(spec), render_face(spec)
        self.assertEqual(a, b, "fixture generation must be deterministic")
        validate_face(spec, a, synthetic_resources(a))
        return a

    def test_analog_fixture(self):
        xml = self.render("fixture_analog.toml")
        root = ET.fromstring(xml)
        self.assertEqual(root.find("Metadata").get("value"), "ANALOG")
        names = [e.get("name") for e in root.iter() if e.get("name")]
        self.assertIn("z50_hh", names)
        self.assertIn("z30_fuel", names)

    def test_digital_fixture(self):
        xml = self.render("fixture_digital.toml")
        self.assertIn("[HOUR_0_23]", xml)
        self.assertIn("HEART_RATE", xml)
        self.assertIn("ACCELEROMETER_ANGLE_X", xml)
        self.assertIn("BATTERY_PERCENT", xml)

    def test_no_aurelius_leakage(self):
        for name in ("fixture_analog.toml", "fixture_digital.toml"):
            xml = self.render(name)
            used = synthetic_resources(xml)
            self.assertFalse(used & AURELIUS_RESOURCES,
                             f"{name} leaks Aurelius resources")
            self.assertNotIn("aurelius", xml.lower())


if __name__ == "__main__":
    unittest.main()
