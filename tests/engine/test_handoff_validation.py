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


# --------------------------------------------------------------------------
# Phase-3 review blocker 4: derived-artwork provenance (fonts)
# --------------------------------------------------------------------------

BFONT_RECORD = {
    "id": "blender-bfont-type1",
    "kind": "font",
    "name": "Bfont",
    "license": "GPL-3.0-or-later",
    "notice_file": "THIRD_PARTY_NOTICES/fonts/blender-bfont-NOTICE.txt",
}


def run_with_provenance(entry: dict, records=None,
                        write_notice: bool = True) -> list[str]:
    """check_handoff with a temp derived-asset-provenance registry."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        eng = root / "watchfaces/testface/engine"
        eng.mkdir(parents=True)
        dest = entry.get("destination")
        if isinstance(dest, str):
            p = root / dest
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"glyph-bytes")
            if entry.get("sha256") == "AUTO":
                entry["sha256"] = hashlib.sha256(b"glyph-bytes").hexdigest()
        if records is not None:
            (root / "docs").mkdir(parents=True, exist_ok=True)
            (root / "docs/derived-asset-provenance.json").write_text(
                json.dumps({"records": records}))
        if write_notice:
            n = root / BFONT_RECORD["notice_file"]
            n.parent.mkdir(parents=True, exist_ok=True)
            n.write_text("NOTICE\n")
        (eng / "handoff.json").write_text(json.dumps(
            {"contract": "docs/ASSET_HANDOFF_CONTRACT.md", "assets": [entry]}))
        validate.issues.clear()
        validate.load_derived_provenance(root)
        validate.check_handoff(root)
        problems = [m for s, m in validate.issues if s == "ERROR"]
        validate.issues.clear()
        return problems


def glyph_entry(**overrides) -> dict:
    e = variant(
        asset_id="numerals/Glyph_2", export_type="font-glyphs",
        destination=("watchfaces/testface/app/src/main/res/"
                     "drawable-nodpi/g_2.png"),
        dimensions=[27, 40], frames=1, frame_seconds=None, loop="none",
        aod_safe=True, sha256="AUTO", consumer_component="z30_date")
    e.update(overrides)
    return e


class TestDerivedFontProvenance(unittest.TestCase):
    """Rasterising a third-party/bundled font is not original authorship."""

    def expect(self, problems, fragment):
        self.assertTrue(any(fragment in p for p in problems),
                        f"expected {fragment!r} in {problems}")

    def test_font_glyphs_may_not_claim_original(self):
        problems = run_with_provenance(glyph_entry(license="original"),
                                       records=[BFONT_RECORD])
        self.expect(problems, "may not claim license 'original'")

    def test_font_glyphs_with_resolved_derived_record_passes(self):
        problems = run_with_provenance(
            glyph_entry(license="derived:blender-bfont-type1"),
            records=[BFONT_RECORD])
        self.assertEqual(problems, [])

    def test_derived_reference_must_resolve(self):
        problems = run_with_provenance(
            glyph_entry(license="derived:no-such-record"),
            records=[BFONT_RECORD])
        self.expect(problems, "does not resolve to a record")

    def test_derived_record_requires_existing_notice(self):
        problems = run_with_provenance(
            glyph_entry(license="derived:blender-bfont-type1"),
            records=[BFONT_RECORD], write_notice=False)
        self.expect(problems, "notice_file")

    def test_registry_record_missing_required_field(self):
        broken = {k: v for k, v in BFONT_RECORD.items() if k != "license"}
        problems = run_with_provenance(
            glyph_entry(license="derived:blender-bfont-type1"),
            records=[broken])
        self.expect(problems, "missing license")

    def test_static_image_may_still_claim_original(self):
        """Purely modelled artwork keeps 'original' — the rule is targeted,
        not a blanket ban."""
        problems = run_with_provenance(
            variant(sha256="AUTO", export_type="static-image",
                    license="original"),
            records=[BFONT_RECORD])
        self.assertEqual(problems, [])


class TestRealAureliusProvenance(unittest.TestCase):
    """Integration: the committed Aurelius manifest must not claim
    original authorship for any glyph export."""

    def test_committed_manifest_declares_font_provenance(self):
        man = json.loads((REPO / "watchfaces/aurelius/engine/handoff.json")
                         .read_text())
        glyphs = [a for a in man["assets"]
                  if a["export_type"] == "font-glyphs"]
        self.assertEqual(len(glyphs), 39)
        for a in glyphs:
            self.assertEqual(a["license"], "derived:blender-bfont-type1",
                             f"{a['asset_id']} must reference the font "
                             f"provenance record")
        plates = [a for a in man["assets"]
                  if a["asset_id"].startswith("plates/")]
        self.assertEqual(len(plates), 2)
        for a in plates:
            self.assertEqual(a["license"], "derived:blender-bfont-type1",
                             "plates carry baked engravings from the same "
                             "font")
        registry = json.loads((REPO / "docs/derived-asset-provenance.json")
                              .read_text())
        ids = {r["id"] for r in registry["records"]}
        self.assertIn("blender-bfont-type1", ids)
        rec = next(r for r in registry["records"]
                   if r["id"] == "blender-bfont-type1")
        self.assertTrue((REPO / rec["notice_file"]).exists())
        self.assertFalse(rec["commercial_use_resolved"],
                         "the GPL-font question is still open and must stay "
                         "flagged until legally resolved")
