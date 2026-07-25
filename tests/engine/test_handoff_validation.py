"""Negative tests for asset-handoff manifest validation (Phase-2 review
blocker 3): every schema constraint documented in
docs/asset-handoff.schema.json must be enforced by tools/validate.py.

Each case builds a temp repo root containing one manifest, runs
check_handoff, and asserts the expected ERROR is (or is not) reported.
"""

import copy
import hashlib
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
validate = importlib.import_module("validate")

GOOD = {
    "asset_id": "gears/GearSpur_M020_z60",
    "source_repo": "xsytrance/AGENOR-Horology",
    "source_commit": "2376d686d6af5933fec13fa48487fa52fb035b36",
    "source_paths": ["assets/models/gears/GearSpur_M020_z60.blend"],
    "spec_path": "assets/models/gears/SPEC.md",
    "export_type": "sprite-strip",
    "destination": "watchfaces/testface/app/src/main/res/drawable-nodpi/gear_strip.png",
    "dimensions": [220, 220],
    "color_space": "srgb",
    "alpha": "straight",
    "pivot": [0.5, 0.5],
    "frames": 60,
    "frame_seconds": 1.0,
    "loop": "perfect",
    "aod_safe": False,
    "license": "original",
    "sha256": None,  # filled in by harness after writing the file
    "lifecycle": "candidate",
    "consumer_component": "z10_gear",
    "regenerate": "scripts/spritepack.py renders/gear out.png --cols 60",
}


def run_check(entry: dict, write_dest: bool = True) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        eng = root / "watchfaces/testface/engine"
        eng.mkdir(parents=True)
        dest = entry.get("destination")
        if write_dest and isinstance(dest, str) and ".." not in dest:
            p = root / dest
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"sprite-bytes")
            if entry.get("sha256") == "AUTO":
                entry["sha256"] = hashlib.sha256(b"sprite-bytes").hexdigest()
        (eng / "handoff.json").write_text(json.dumps(
            {"contract": "docs/ASSET_HANDOFF_CONTRACT.md", "assets": [entry]}))
        validate.issues.clear()
        validate.check_handoff(root)
        problems = [m for s, m in validate.issues if s == "ERROR"]
        validate.issues.clear()
        return problems


def variant(**overrides) -> dict:
    e = copy.deepcopy(GOOD)
    e.update(overrides)
    return e


class TestHandoffPositive(unittest.TestCase):
    def test_valid_entry_passes(self):
        self.assertEqual(run_check(variant(sha256="AUTO")), [])

    def test_example_null_destination_passes(self):
        e = variant(destination=None, sha256=None, example=True)
        self.assertEqual(run_check(e), [])


class TestHandoffNegative(unittest.TestCase):
    def expect(self, entry, fragment, **kw):
        problems = run_check(entry, **kw)
        self.assertTrue(any(fragment in p for p in problems),
                        f"expected {fragment!r} in {problems}")

    def test_malformed_asset_id(self):
        self.expect(variant(sha256="AUTO", asset_id="Bad Asset!"), "asset_id")

    def test_empty_source_paths(self):
        self.expect(variant(sha256="AUTO", source_paths=[]), "source_paths")

    def test_short_source_commit(self):
        self.expect(variant(sha256="AUTO", source_commit="abc123"), "40-char")

    def test_bad_dimensions_length(self):
        self.expect(variant(sha256="AUTO", dimensions=[220]), "dimensions")

    def test_bad_dimensions_type(self):
        self.expect(variant(sha256="AUTO", dimensions=[220.5, 220]),
                    "dimensions")

    def test_nonpositive_dimensions(self):
        self.expect(variant(sha256="AUTO", dimensions=[0, 220]), "dimensions")

    def test_pivot_out_of_range(self):
        self.expect(variant(sha256="AUTO", pivot=[0.5, 1.5]), "pivot")

    def test_pivot_wrong_arity(self):
        self.expect(variant(sha256="AUTO", pivot=[0.5]), "pivot")

    def test_zero_frames(self):
        self.expect(variant(sha256="AUTO", frames=0), "frames")

    def test_animated_without_frame_seconds(self):
        self.expect(variant(sha256="AUTO", frame_seconds=None),
                    "requires frame_seconds")

    def test_negative_frame_seconds(self):
        self.expect(variant(sha256="AUTO", frame_seconds=-1), "frame_seconds")

    def test_bad_color_space(self):
        self.expect(variant(sha256="AUTO", color_space="rec2020"),
                    "color_space")

    def test_bad_alpha_enum(self):
        self.expect(variant(sha256="AUTO", alpha="matted"), "alpha")

    def test_bad_loop_enum(self):
        self.expect(variant(sha256="AUTO", loop="forever"), "loop")

    def test_bad_lifecycle_enum(self):
        self.expect(variant(sha256="AUTO", lifecycle="shipped"), "lifecycle")

    def test_nonboolean_aod_safe(self):
        self.expect(variant(sha256="AUTO", aod_safe="yes"), "aod_safe")

    def test_empty_license(self):
        self.expect(variant(sha256="AUTO", license=""), "license")

    def test_bad_sha_format(self):
        self.expect(variant(sha256="ZZZZ"), "64 lowercase hex")

    def test_missing_sha_on_real_destination(self):
        self.expect(variant(sha256=None), "requires a sha256")

    def test_sha_mismatch(self):
        self.expect(variant(sha256="0" * 64), "sha256 mismatch")

    def test_path_traversal(self):
        self.expect(variant(
            sha256="AUTO",
            destination="watchfaces/testface/app/src/main/res/../../../../secrets.png"),
            "traversal")

    def test_destination_outside_face_res(self):
        self.expect(variant(
            sha256="AUTO",
            destination="watchfaces/otherface/app/src/main/res/drawable/x.png"),
            "outside")

    def test_null_destination_without_example(self):
        self.expect(variant(destination=None, sha256=None),
                    "non-example")

    def test_missing_required_field(self):
        e = variant(sha256="AUTO")
        del e["regenerate"]
        self.expect(e, "missing field regenerate")


if __name__ == "__main__":
    unittest.main()
