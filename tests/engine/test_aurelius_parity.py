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
        spec = load_spec(SPEC)
        self.assertEqual(spec.identity["package"], "com.xsytrance.aurelius")
        self.assertEqual(str(spec.identity["version_code"]), "1")
        self.assertEqual(str(spec.identity["version_name"]), "1.0")
        self.assertEqual(spec.wff_version, 4)


if __name__ == "__main__":
    unittest.main()
