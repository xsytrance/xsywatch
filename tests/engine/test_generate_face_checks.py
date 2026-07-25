"""End-to-end checks of tools/generate_face.py gating (Phase-2 review
blocker 4): the manifest WFF-format version must match FaceSpec.wff_version,
including resolution through @integer/wff_version.

Runs the real CLI against a synthetic mini face in a temp repo root.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

SPEC = """\
[face]
slug = "testface"
width = 480
height = 480
wff_version = {wff}
clock_type = "ANALOG"
preview_time = "10:09:35"
background_color = "#FF000000"

[identity]
package = "com.example.testface"
version_code = 1
version_name = "1.0"

[[components]]
type = "static_image"
name = "z00_plate"
resource = "plate"
box = {{x = 0, y = 0, width = 480, height = 480}}
aod = {{alpha = 100}}
"""

GRADLE = """\
android {
    defaultConfig {
        applicationId = "com.example.testface"
        versionCode = 1
        versionName = "1.0"
    }
}
"""

MANIFEST = """\
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <application android:hasCode="false">
    <meta-data
        android:name="com.google.wear.watchface.format.version"
        android:value="@integer/wff_version" />
  </application>
</manifest>
"""

INTEGERS = '<resources><integer name="wff_version">4</integer></resources>\n'


def make_face(root: Path, spec_wff: int) -> None:
    face = root / "watchfaces/testface"
    (face / "engine").mkdir(parents=True)
    (face / "app/src/main/res/values").mkdir(parents=True)
    (face / "app/src/main/res/raw").mkdir(parents=True)
    (face / "app/src/main/res/drawable-nodpi").mkdir(parents=True)
    (face / "engine/face.toml").write_text(SPEC.format(wff=spec_wff))
    (face / "app/build.gradle.kts").write_text(GRADLE)
    (face / "app/src/main/AndroidManifest.xml").write_text(MANIFEST)
    (face / "app/src/main/res/values/integers.xml").write_text(INTEGERS)
    (face / "app/src/main/res/drawable-nodpi/plate.png").write_bytes(b"png")


def run_generate(root: Path):
    return subprocess.run(
        [sys.executable, str(REPO / "tools/generate_face.py"), "testface",
         "--repo-root", str(root), "--stdout"],
        capture_output=True, text=True)


class TestWffVersionCrossCheck(unittest.TestCase):
    def test_matching_version_generates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_face(root, spec_wff=4)  # manifest resolves to 4
            r = run_generate(root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("<WatchFace", r.stdout)

    def test_deliberate_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_face(root, spec_wff=5)  # manifest still says 4
            r = run_generate(root)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("wff_version=5", r.stderr)
            self.assertIn("does not match", r.stderr)

    def test_unresolvable_manifest_version_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_face(root, spec_wff=4)
            (root / "watchfaces/testface/app/src/main/AndroidManifest.xml"
             ).write_text("<manifest/>")
            r = run_generate(root)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("could not resolve", r.stderr)


if __name__ == "__main__":
    unittest.main()
