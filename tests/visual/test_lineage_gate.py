"""Deliberate-failure fixtures for the visual/resource-lineage gate.

Phase-3 brief §6.6: every test here proves the gate CATCHES a specific
failure class. The star fixture reproduces the Phase-2 WARBIRD incident:
same filenames, valid XML/package/dimensions/resource names — wrong art.

Run: python3 -m unittest discover -s tests/visual
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import visuallib as V                    # noqa: E402
import compare_visuals as CV             # noqa: E402
import inventory_resources as IR         # noqa: E402
import validate as VAL                   # noqa: E402

from PIL import Image, ImageDraw        # noqa: E402

FACE = "aurelius"
GOLDEN_DIR = REPO / "watchfaces" / FACE / "visual/goldens"


def reference_dir(root: Path) -> Path:
    """Resolve the deterministic-render reference: the proposed candidate
    set while states.toml declares one (ADR-009 candidate lifecycle),
    otherwise the approved goldens."""
    import tomllib
    with open(root / "watchfaces" / FACE / "visual/states.toml",
              "rb") as fh:
        contract = tomllib.load(fh)
    g = contract["goldens"]
    if g.get("proposed_version"):
        return (root / "watchfaces" / FACE / "visual/candidates" /
                g["proposed_version"])
    return (root / "watchfaces" / FACE / "visual/goldens" /
            g["approved_version"])


def synthetic_warbird(size: tuple[int, int]) -> Image.Image:
    """Clearly-different synthetic stand-in for the WARBIRD class: olive
    fuselage plate with a shark-mouth wedge. Deliberately NOT the
    proprietary WARBIRD art (brief §6.6 allows a synthetic fixture)."""
    img = Image.new("RGBA", size, (74, 82, 64, 255))
    d = ImageDraw.Draw(img)
    w, h = size
    d.polygon([(w * 0.15, h * 0.75), (w * 0.85, h * 0.75),
               (w * 0.5, h * 0.95)], fill=(240, 235, 225, 255))
    for i in range(6):
        x0 = w * (0.2 + i * 0.1)
        d.polygon([(x0, h * 0.75), (x0 + w * 0.05, h * 0.75),
                   (x0 + w * 0.025, h * 0.88)], fill=(120, 20, 25, 255))
    d.ellipse((w * 0.25, h * 0.2, w * 0.45, h * 0.35),
              fill=(20, 20, 22, 255))
    return img


def synthetic_hand(size: tuple[int, int]) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w, h = size
    d.rectangle((w / 2 - 4, h * 0.1, w / 2 + 4, h / 2), fill=(255, 140, 0, 255))
    return img


class Sandbox:
    """Copy of the face inside a temp repo root; visuallib retargeted."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "watchfaces").mkdir()
        shutil.copytree(REPO / "watchfaces" / FACE,
                        self.root / "watchfaces" / FACE)
        self._old_repo = V.REPO
        V.REPO = self.root

    def path(self, rel: str) -> Path:
        return self.root / "watchfaces" / FACE / rel

    def res(self, name: str) -> Path:
        return self.path(f"app/src/main/res/drawable-nodpi/{name}")

    def close(self):
        V.REPO = self._old_repo
        self.tmp.cleanup()


class LineageGateTests(unittest.TestCase):

    def setUp(self):
        self.sb = Sandbox()
        self.addCleanup(self.sb.close)
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out, True)

    # -- helpers -----------------------------------------------------------

    def render(self, state: str) -> Path:
        scene = V.Scene.load(FACE)
        contract = V.VisualContract.load(FACE)
        img = V.render_state(scene, contract, state)
        p = self.out / f"{state}.png"
        V.save_png_deterministic(img, p)
        return p

    def compare_to_golden(self, rendered: Path, kind: str) -> int:
        ref = reference_dir(self.sb.root) / f"{kind}.png"
        return CV.compare(ref, rendered, "exact", None, FACE, None)

    def run_check_visual(self) -> list[str]:
        VAL.issues.clear()
        VAL.check_visual(self.sb.root)
        errs = [m for s, m in VAL.issues if s == "ERROR"]
        VAL.issues.clear()
        return errs

    def substitute(self, resource_png: str, maker) -> None:
        target = self.sb.res(resource_png)
        with Image.open(target) as im:
            size = im.size
        maker(size).save(target, format="PNG")

    # -- 0. positive control: clean sandbox passes everything --------------

    def test_clean_sandbox_passes(self):
        p = self.render("normal_hero")
        self.assertEqual(self.compare_to_golden(p, "normal"), 0)
        inv = IR.build_inventory(FACE)
        committed = json.loads(
            self.sb.path("visual/inventories/inventory.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(inv, committed)
        self.assertFalse(any(inv["problems"].values()))
        self.assertEqual(self.run_check_visual(), [])

    # -- 1. WARBIRD class: same-filename background substitution -----------

    def test_warbird_class_background_substitution(self):
        """XML valid, package metadata valid, dimensions valid, resource
        names valid — background bytes are a different design. Must fail
        BOTH the pixel gate and the inventory gate."""
        self.substitute("bg.png", synthetic_warbird)
        p = self.render("normal_hero")
        self.assertEqual(self.compare_to_golden(p, "normal"), 1,
                         "wrong-art background must fail the visual gate")
        inv = IR.build_inventory(FACE)
        committed = json.loads(
            self.sb.path("visual/inventories/inventory.json")
            .read_text(encoding="utf-8"))
        self.assertNotEqual(inv, committed,
                            "inventory --check must detect byte drift")
        errs = self.run_check_visual()
        self.assertTrue(any("WARBIRD failure class" in e for e in errs),
                        f"validate.py must catch same-name/wrong-bytes "
                        f"directly: {errs}")

    # -- 2. same-filename hand substitution ---------------------------------

    def test_hand_substitution(self):
        self.substitute("min_hand.png", synthetic_hand)
        p = self.render("normal_hero")
        self.assertEqual(self.compare_to_golden(p, "normal"), 1)

    # -- 3. same-filename font-glyph substitution ---------------------------

    def test_glyph_substitution(self):
        # DAY is pinned to 24: corrupting g_2 changes the date aperture.
        def maker(size):
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rectangle((2, 2, size[0] - 2, size[1] - 2),
                        outline=(255, 0, 255, 255), width=3)
            return img
        self.substitute("g_2.png", maker)
        p = self.render("normal_hero")
        self.assertEqual(self.compare_to_golden(p, "normal"), 1)

    # -- 4. unexpected extra runtime drawable -------------------------------

    def test_unexpected_extra_drawable(self):
        rogue = self.sb.res("rogue_overlay.png")
        Image.new("RGBA", (480, 480), (255, 0, 0, 64)).save(rogue, "PNG")
        inv = IR.build_inventory(FACE)
        self.assertIn("app/src/main/res/drawable-nodpi/rogue_overlay.png",
                      inv["problems"]["unreferenced"])

    # -- 5. studio-classified bytes without a covering record ---------------

    def test_unmanifested_studio_bytes(self):
        """A studio-style import that changes runtime bytes with no handoff
        entry and no approval record must fail the approval binding."""
        self.substitute("gear_l.png", synthetic_hand)
        IR_inv = IR.build_inventory(FACE)
        V.dump_json_deterministic(
            IR_inv, self.sb.path("visual/inventories/inventory.json"))
        errs = self.run_check_visual()
        self.assertTrue(any("not bound to any approval record" in e
                            for e in errs), errs)

    # -- 6. changed golden without an approval record ------------------------

    def test_unapproved_golden_change(self):
        golden = self.sb.path("visual/goldens/field-tourbillon-v1/normal.png")
        synthetic_warbird((480, 480)).save(golden, "PNG")
        errs = self.run_check_visual()
        self.assertTrue(any("does not match approved record" in e
                            for e in errs), errs)

    # -- 7. approval record hash that matches nothing ------------------------

    def test_approval_record_hash_mismatch(self):
        rec_path = self.sb.path(
            "visual/approvals/APPROVAL-0001-field-tourbillon-v1.json")
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        rec["proposed_goldens"]["aod"] = "0" * 64
        rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        errs = self.run_check_visual()
        self.assertTrue(any("does not match approved record" in e
                            for e in errs), errs)

    # -- 7b. superseded goldens stay frozen after promotion -----------------

    def test_superseded_golden_change(self):
        """Promotion supersedes a generation but does not release its
        bytes. After field-tourbillon-mk2-r2 became the approved version,
        the v1 goldens are historical evidence (ADR-009 §5) — tampering
        with them must still fail even though they are no longer active.

        Fixtures 6 and 7 above happen to exercise this too, because v1 is
        now superseded; this one states the requirement directly so it
        cannot be lost the next time approved_version moves."""
        import tomllib
        with open(self.sb.path("visual/states.toml"), "rb") as fh:
            approved = tomllib.load(fh)["goldens"]["approved_version"]
        superseded = sorted(
            p.name for p in self.sb.path("visual/goldens").iterdir()
            if p.is_dir() and p.name != approved)
        self.assertTrue(superseded, "expected at least one superseded "
                                    "golden set to be preserved")
        for version in superseded:
            with self.subTest(version=version):
                target = self.sb.path(
                    f"visual/goldens/{version}/normal.png")
                original = target.read_bytes()
                try:
                    synthetic_warbird((480, 480)).save(target, "PNG")
                    errs = self.run_check_visual()
                    self.assertTrue(
                        any("does not match approved record" in e
                            for e in errs),
                        f"tampering with superseded goldens/{version} "
                        f"was not caught: {errs}")
                finally:
                    target.write_bytes(original)

    # -- 8. over-broad mask ---------------------------------------------------

    def test_overbroad_mask_rejected(self):
        mask = self.out / "overbroad.png"
        m = Image.new("L", (480, 480), 0)
        d = ImageDraw.Draw(m)
        d.ellipse((200, 200, 280, 280), fill=255)   # keeps ~2% of the disc
        m.save(mask, "PNG")
        a = self.render("normal_hero")
        rc = CV.compare(a, a, "device", mask, FACE, None)
        self.assertEqual(rc, 2, "a mask hiding most of the face must be "
                                "rejected even when pixels match")

    # -- 9. inventory path/checksum mismatch ----------------------------------

    def test_inventory_checksum_tamper(self):
        inv_path = self.sb.path("visual/inventories/inventory.json")
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        inv["resources"][0]["sha256"] = "f" * 64
        inv_path.write_text(json.dumps(inv, indent=2, sort_keys=True),
                            encoding="utf-8")
        live = IR.build_inventory(FACE)
        committed = json.loads(inv_path.read_text(encoding="utf-8"))
        self.assertNotEqual(live, committed)
        errs = self.run_check_visual()
        self.assertTrue(any("not bound to any approval record" in e
                            for e in errs), errs)

    # -- determinism regression ------------------------------------------------

    def test_reference_render_deterministic(self):
        a = self.render("normal_hero")
        b_img = V.render_state(V.Scene.load(FACE),
                               V.VisualContract.load(FACE), "normal_hero")
        b = self.out / "normal_hero_2.png"
        V.save_png_deterministic(b_img, b)
        self.assertEqual(a.read_bytes(), b.read_bytes())

    # -- committed goldens reproduce from the real tree -------------------------

    def test_committed_reference_reproduces(self):
        self.sb.close()  # leave sandbox: verify the REAL repo reference set
        scene = V.Scene.load(FACE)
        contract = V.VisualContract.load(FACE)
        g = contract.golden_states()
        ref = reference_dir(REPO)
        for kind in ("normal", "aod"):
            img = V.render_state(scene, contract, g[kind])
            p = self.out / f"ref_{kind}.png"
            V.save_png_deterministic(img, p)
            committed = ref / f"{kind}.png"
            self.assertEqual(p.read_bytes(), committed.read_bytes(),
                             f"{kind} reference ({ref.name}) must "
                             f"reproduce byte-identically")
        self.sb = Sandbox()  # so addCleanup close() has something to close


APPROVAL_2 = "visual/approvals/APPROVAL-0002-field-tourbillon-mk2.json"


class ApprovalDeltaBindingTests(unittest.TestCase):
    """Blocker-1 fixtures (Phase-3 review): APPROVAL-0002 must bind the
    EXACT changed resources and handoff asset ids, and validation must
    reject prose summaries, wildcards, omissions, duplicates, unknown ids,
    and resources that did not actually change."""

    def setUp(self):
        self.sb = Sandbox()
        self.addCleanup(self.sb.close)

    def rec(self) -> dict:
        return json.loads(self.sb.path(APPROVAL_2).read_text(encoding="utf-8"))

    def write(self, rec: dict) -> None:
        self.sb.path(APPROVAL_2).write_text(json.dumps(rec, indent=2),
                                            encoding="utf-8")

    def errors(self) -> list[str]:
        VAL.issues.clear()
        VAL.check_visual(self.sb.root)
        errs = [m for s, m in VAL.issues if s == "ERROR"]
        VAL.issues.clear()
        return errs

    def assert_error(self, needle: str, errs: list[str]) -> None:
        self.assertTrue(any(needle in e for e in errs),
                        f"expected an error containing {needle!r}; got {errs}")

    # -- positive control ---------------------------------------------

    def test_item_level_record_validates(self):
        rec = self.rec()
        self.assertEqual(len(rec["changed_resources"]), 49)
        self.assertEqual(len(rec["handoff_asset_ids"]), 50)
        self.assertEqual(self.errors(), [])

    # -- 1. omitted handoff id ----------------------------------------

    def test_omitted_handoff_id_fails(self):
        rec = self.rec()
        rec["handoff_asset_ids"].remove("gears/AureliusMk2_GearL_z24")
        self.write(rec)
        self.assert_error("is not listed in handoff_asset_ids", self.errors())

    # -- 2. unknown handoff id ----------------------------------------

    def test_unknown_handoff_id_fails(self):
        rec = self.rec()
        rec["handoff_asset_ids"].append("gears/NotARealAsset")
        self.write(rec)
        self.assert_error("not in engine/handoff.json", self.errors())

    # -- 3. duplicate handoff id --------------------------------------

    def test_duplicate_handoff_id_fails(self):
        rec = self.rec()
        rec["handoff_asset_ids"].append("gears/AureliusMk2_GearL_z24")
        self.write(rec)
        self.assert_error("duplicate entries", self.errors())

    # -- 4. prose wildcard summary (the exact pre-review defect) -------

    def test_prose_wildcard_ids_fail(self):
        rec = self.rec()
        rec["handoff_asset_ids"] = [
            "ALL 50 entries of watchfaces/aurelius/engine/handoff.json"]
        self.write(rec)
        self.assert_error("wildcards are rejected", self.errors())

    def test_prose_wildcard_changed_resources_fail(self):
        rec = self.rec()
        rec["changed_resources"] = [
            "50 runtime resources under app/src/main/res/drawable-nodpi/"]
        self.write(rec)
        self.assert_error("wildcards are rejected", self.errors())

    # -- 5. omitted changed resource ----------------------------------

    def test_omitted_changed_resource_fails(self):
        rec = self.rec()
        rec["changed_resources"].remove(
            "watchfaces/aurelius/app/src/main/res/drawable-nodpi/bg.png")
        self.write(rec)
        self.assert_error("not listed in the approval record", self.errors())

    # -- 6. extra / unchanged resource claimed as changed --------------

    def test_extra_unchanged_resource_fails(self):
        rec = self.rec()
        rec["changed_resources"].append(
            "watchfaces/aurelius/app/src/main/res/drawable-nodpi/g_space.png")
        self.write(rec)
        self.assert_error("bytes are identical", self.errors())

    # -- supporting invariants -----------------------------------------

    def test_inventory_snapshot_must_match_record_hash(self):
        snap = self.sb.path(
            "visual/inventories/versions/field-tourbillon-mk2.json")
        data = json.loads(snap.read_text(encoding="utf-8"))
        data["resource_count"] = 999
        snap.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.assert_error("not bound to its inventory", self.errors())

    def test_generated_preview_cannot_be_a_handoff_destination(self):
        rec = self.rec()
        rec["generated_consumer_resources"].append({
            "path": ("watchfaces/aurelius/app/src/main/res/drawable-nodpi/"
                     "bg.png"),
            "origin": "bogus"})
        self.write(rec)
        self.assert_error("IS a studio handoff destination", self.errors())

    def test_unchanged_asset_must_be_declared(self):
        rec = self.rec()
        rec["unchanged_handoff_assets"] = []
        self.write(rec)
        self.assert_error("declare it in unchanged_handoff_assets",
                          self.errors())


class ExpressionEvaluatorTests(unittest.TestCase):
    ST = {"MINUTE": 9, "SECOND": 35, "MILLISECOND": 0, "HOUR_0_11": 10,
          "DAY": 24, "BATTERY_PERCENT": 80, "HEART_RATE": 72,
          "ACCELEROMETER_ANGLE_X": 0, "ACCELEROMETER_ANGLE_Y": 0}

    def test_seconds_angle(self):
        self.assertAlmostEqual(
            V.evaluate("([SECOND] + [MILLISECOND] / 1000) * 6", self.ST), 210)

    def test_ternary_fallback(self):
        expr = "clamp(([HEART_RATE] < 30 ? 70 : [HEART_RATE]), 40, 200)"
        self.assertEqual(V.evaluate(expr, {**self.ST, "HEART_RATE": 0}), 70)
        self.assertEqual(V.evaluate(expr, {**self.ST, "HEART_RATE": 150}), 150)
        self.assertEqual(V.evaluate(expr, {**self.ST, "HEART_RATE": 300}), 200)

    def test_modulo_normalization(self):
        expr = "360 - ((([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000) * 24) % 360)"
        v = V.evaluate(expr, self.ST)
        self.assertTrue(0 <= v <= 360)

    def test_gauge(self):
        expr = "292.5 + 45.0 * clamp([BATTERY_PERCENT], 0, 100) / 100"
        self.assertAlmostEqual(V.evaluate(expr, self.ST), 328.5)

    def test_unpinned_source_raises(self):
        with self.assertRaises(KeyError):
            V.evaluate("[STEP_COUNT] * 2", self.ST)


if __name__ == "__main__":
    unittest.main()
