"""Semantic parity: engine-generated Aurelius vs the Phase-1 baseline XML.

The baseline snapshot (docs/reports/evidence/.../watchface_baseline.xml,
SHA-256 a8ce33ac...) is the FROZEN IMPORTED PHASE-1 SOURCE BASELINE — the
watchface.xml as imported from the local Aurelius project in Phase 1. It is
NOT claimed to be byte-extracted from the released APK (resource XML is
compiled at packaging; the producing source commit of the historical APK
predates the source import). The preserved APK plus the physical-device
baseline test are the authoritative release-behavior evidence.
Generation must be semantically identical to this source baseline:

  * same element sequence (document order = z-order);
  * same attributes, with numeric attributes compared numerically
    ("0" == "0.0") and everything else compared exactly — including every
    expression string;
  * `name` attributes are compared through a fixed, documented rename map
    (z00_aod -> z01_aod, engine naming convention; names are identifiers
    with no runtime behavior);
  * comments (the generated banner) ignored.
"""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine"))

from wffgen.render import render_face
from wffgen.spec import load_spec

BASELINE = (REPO / "docs/reports/evidence/phase-2/aurelius/baseline/"
                   "watchface_baseline.xml")
SPEC = REPO / "watchfaces/aurelius/engine/face.toml"

RENAMES = {"z00_aod": "z01_aod"}


def norm_attr(tag: str, key: str, value: str) -> str:
    if key == "name":
        return RENAMES.get(value, value)
    try:
        return repr(float(value))
    except ValueError:
        return value


def flatten(root: ET.Element):
    out = []
    for e in root.iter():
        if not isinstance(e.tag, str):  # skip comments
            continue
        attrs = {k: norm_attr(e.tag, k, v) for k, v in sorted(e.attrib.items())}
        out.append((e.tag, tuple(sorted(attrs.items())),
                    (e.text or "").strip()))
    return out


class TestAureliusSemanticParity(unittest.TestCase):
    def test_generated_matches_baseline(self):
        baseline = flatten(ET.parse(BASELINE).getroot())
        generated = flatten(ET.fromstring(render_face(load_spec(SPEC))))
        self.assertEqual(len(baseline), len(generated),
                         "element count differs from baseline")
        for i, (b, g) in enumerate(zip(baseline, generated)):
            self.assertEqual(b, g, f"element #{i} differs from baseline")

    def test_identity_pinned(self):
        """Identity may not drift silently.

        Phase 2 pinned this to 1 / "1.0" to prove the engine migration
        changed no identity field. Phase 4 moves the package deliberately:
        first to 2.0.0-rc1 (ADR-010 §3, minSdk raised to the WFF v4 API
        floor), then to 2.0.0-rc2 / versionCode 3 after the Checkpoint B
        review required packaging, dex-gate and manifest-permission
        corrections that change package bytes. The pin moves with each
        reviewed decision. Its job is unchanged: these values are edited
        here only alongside such a decision, never as a side effect.
        """
        spec = load_spec(SPEC)
        self.assertEqual(spec.identity["package"], "com.xsytrance.aurelius")
        self.assertEqual(str(spec.identity["version_code"]), "3")
        self.assertEqual(str(spec.identity["version_name"]), "2.0.0-rc2")
        self.assertEqual(spec.wff_version, 4)

    def test_package_name_never_changes(self):
        """The package name is the one identity field that must NEVER
        move: it is immutable once published and an update must keep it
        (ADR-010 §3). Stated separately so a future version bump cannot
        carry a rename along with it."""
        self.assertEqual(load_spec(SPEC).identity["package"],
                         "com.xsytrance.aurelius")

    def test_min_sdk_satisfies_the_wff_version_floor(self):
        """WFF v4 requires Wear OS 6 / API 36
        (developer.android.com/training/wearables/wff, checked
        2026-07-26). A face declaring a format its minSdk allows onto
        devices that cannot render it is the FMT-2 defect."""
        import re
        floors = {1: 33, 2: 34, 3: 35, 4: 36}
        spec = load_spec(SPEC)
        gradle = (SPEC.parent.parent / "app/build.gradle.kts").read_text()
        m = re.search(r"minSdk\s*=\s*(\d+)", gradle)
        self.assertIsNotNone(m, "minSdk not found in build.gradle.kts")
        self.assertGreaterEqual(int(m.group(1)), floors[spec.wff_version])


if __name__ == "__main__":
    unittest.main()
