"""Rendering: determinism, banner, spec round-trip via TOML."""

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))

from wffgen import ENGINE_VERSION
from wffgen.render import render_face
from wffgen.spec import load_spec

MINI_SPEC = """
[face]
slug = "mini"
width = 480
height = 480
wff_version = 4
clock_type = "ANALOG"
preview_time = "10:09:35"
background_color = "#FF000000"

[identity]
package = "com.example.mini"
version_code = 1
version_name = "1.0"

[[fonts]]
name = "f"
height = 40
[fonts.characters]
"0" = ["g_0", 28]
"1" = ["g_1", 22]

[[components]]
type = "background_pair"
normal = "bg"
aod_resource = "bg_aod"
parallax = [3, 3]

[[components]]
type = "rotating_image"
name = "z10_gear"
resource = "gear"
box = {x = 78, y = 208, width = 120, height = 120}
speed = 40
aod = {alpha = 90, duration = 0.4, offset = 0.1}

[[components]]
type = "analog_hand"
name = "z50_hour"
resource = "hour_hand"
which = "hour"
aod = {alpha = 190, duration = 0.5, interpolation = "EASE_OUT"}
"""


class TestRender(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".toml",
                                               delete=False)
        self.tmp.write(MINI_SPEC)
        self.tmp.close()
        self.spec = load_spec(self.tmp.name)

    def test_deterministic_bytes(self):
        self.assertEqual(render_face(self.spec), render_face(self.spec))

    def test_reload_deterministic(self):
        again = load_spec(self.tmp.name)
        self.assertEqual(render_face(self.spec), render_face(again))

    def test_banner_names_spec_and_engine(self):
        xml = render_face(self.spec)
        self.assertIn("watchfaces/mini/engine/face.toml", xml)
        self.assertIn(ENGINE_VERSION, xml)
        self.assertIn("GENERATED FILE", xml)

    def test_parses_and_structure(self):
        root = ET.fromstring(render_face(self.spec))
        self.assertEqual(root.tag, "WatchFace")
        names = [e.get("name") for e in root.iter()
                 if e.tag == "PartImage"]
        self.assertEqual(names, ["z00_bg", "z00_aod", "z10_gear", "z50_hour"])
        chars = root.findall(".//Character")
        self.assertEqual(len(chars), 2)

    def test_component_order_is_document_order(self):
        xml = render_face(self.spec)
        self.assertLess(xml.index("z10_gear"), xml.index("z50_hour"))


if __name__ == "__main__":
    unittest.main()
