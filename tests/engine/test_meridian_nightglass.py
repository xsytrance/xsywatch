"""Contract tests for the MERIDIAN NIGHTGLASS source generator."""

from pathlib import Path
import subprocess
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
FACE = ROOT / "watchfaces/meridian-nightglass"
XML = FACE / "app/src/main/res/raw/watchface.xml"


class NightglassContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            ["python3", "tools/nightglass/build.py"],
            cwd=ROOT, check=True, capture_output=True, text=True)
        cls.root = ET.parse(XML).getroot()

    def test_unique_development_identity(self):
        gradle = (FACE / "app/build.gradle.kts").read_text()
        self.assertIn(
            'applicationId = "com.xsytrance.meridian.nightglass.dev"',
            gradle)

    def test_five_editor_lighting_options(self):
        options = self.root.findall(
            "./UserConfigurations/ColorConfiguration/ColorOption")
        self.assertEqual(
            ["sapphire", "radar", "amber", "ice", "stealth"],
            [node.get("id") for node in options])

    def test_native_shortcuts_are_present(self):
        targets = {node.get("target") for node in self.root.iter("Launch")}
        self.assertTrue(
            {"BATTERY_STATUS", "CALENDAR", "HEALTH_HEART_RATE"} <= targets)

    def test_aod_removes_seconds_and_static_dial(self):
        second = next(node for node in self.root.iter("PartImage")
                      if node.get("name") == "second_hand")
        self.assertEqual(
            "0", second.find("Variant[@mode='AMBIENT']").get("value"))
        base = next(node for node in self.root.iter("PartImage")
                    if node.get("name") == "base")
        self.assertEqual(
            "0", base.find("Variant[@mode='AMBIENT']").get("value"))

    def test_required_live_sources_remain_bound(self):
        xml = XML.read_text()
        for source in (
                "BATTERY_PERCENT", "STEP_COUNT", "STEP_PERCENT", "STEP_GOAL",
                "HEART_RATE", "HOUR_0_23", "DAY_OF_WEEK_S", "DAY", "MONTH_S",
                "WEATHER.TEMPERATURE", "WEATHER.CHANCE_OF_PRECIPITATION"):
            self.assertIn(f"[{source}]", xml)


if __name__ == "__main__":
    unittest.main()
