#!/usr/bin/env python3
"""Deterministic reference renderer for engine-managed faces (ADR-009).

Composes the COMMITTED generated watchface.xml + committed res/ bytes at a
pinned state from the face's visual contract (visual/states.toml).

Usage:
  render_reference.py <face> --state <name> [--out out.png]
  render_reference.py <face> --goldens [--out-dir DIR]     # render both goldens
  render_reference.py <face> --goldens --check             # gate: byte-match
  render_reference.py <face> --make-default-masks
  render_reference.py <face> --selftest                    # render twice, compare

Determinism: two runs of the same command produce byte-identical PNGs
(--selftest proves it). Golden metadata records the Pillow version and all
input hashes; --strict fails when the environment differs from the pin.

WFF behaviors deliberately NOT reproduced (device comparisons use the
calibrated perceptual profile instead): ambient transition animation, panel
color response/dimming, One UI overlays, exact runtime resampling kernels.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visuallib as V  # noqa: E402


def golden_dir(face: str, version: str) -> Path:
    return V.REPO / "watchfaces" / face / "visual" / "goldens" / version


def render_goldens(face: str, out_dir: Path, strict: bool) -> dict:
    contract = V.VisualContract.load(face)
    warn = V.check_pillow_pin(contract, strict)
    if warn:
        print(f"WARN: {warn}", file=sys.stderr)
    scene = V.Scene.load(face)
    g = contract.golden_states()
    result = {"face": face, "visual_version": g["version"],
              "pillow": V.pillow_version(),
              "xml_sha256": scene.xml_sha256, "renders": {}}
    for kind in ("normal", "aod"):
        img = V.render_state(scene, contract, g[kind])
        sha = V.save_png_deterministic(img, out_dir / f"{kind}.png")
        result["renders"][kind] = {"state": g[kind], "sha256": sha}
        print(f"{kind}: state={g[kind]} sha256={sha}")
    return result


def _proposed_reference(face: str, contract) -> tuple[Path, str] | None:
    """When states.toml sets goldens.proposed_version, the deterministic
    re-render gate targets candidates/<version>/ bound to a `proposed`
    approval record (ADR-009 candidate lifecycle). Approved goldens stay
    frozen until promotion."""
    version = contract.raw["goldens"].get("proposed_version")
    if not version:
        return None
    cdir = (V.REPO / "watchfaces" / face / "visual" / "candidates" /
            version)
    return cdir, version


def cmd_goldens(face: str, check: bool, strict: bool) -> int:
    contract = V.VisualContract.load(face)
    proposed = _proposed_reference(face, contract)
    if proposed:
        ref_dir, version = proposed
        label = f"proposed candidate {version}"
    else:
        version = contract.golden_states()["version"]
        ref_dir = golden_dir(face, version)
        label = f"approved golden {version}"
    if not check:
        meta = render_goldens(face, ref_dir, strict)
        meta["status"] = "proposed" if proposed else "approved"
        V.dump_json_deterministic(meta, ref_dir / "METADATA.json")
        print(f"{label} renders written to {ref_dir}")
        return 0
    # check mode: render to temp, byte-compare against the committed
    # reference set (proposed candidates take precedence while declared)
    import json
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        render_goldens(face, Path(td), strict)
        ok = True
        for kind in ("normal", "aod"):
            committed = ref_dir / f"{kind}.png"
            fresh = Path(td) / f"{kind}.png"
            if not committed.exists():
                print(f"FAIL: missing committed reference {committed}")
                ok = False
                continue
            if committed.read_bytes() != fresh.read_bytes():
                print(f"FAIL: {kind} {label} drifted from deterministic "
                      f"re-render ({committed})")
                ok = False
            else:
                print(f"OK: {kind} reproduces byte-identically ({label})")
        if ok and proposed:
            # the proposed reference must be bound to a proposed record
            recs = (V.REPO / "watchfaces" / face / "visual" /
                    "approvals").glob("*.json")
            bound = False
            for rp in recs:
                rec = json.loads(rp.read_text(encoding="utf-8"))
                if (rec.get("visual_version") == version
                        and rec.get("owner", {}).get("status")
                        in ("proposed", "approved")):
                    hashes = rec.get("proposed_goldens", {})
                    if all(hashes.get(k) == V.sha256_file(ref_dir
                           / f"{k}.png") for k in ("normal", "aod")):
                        bound = True
                        print(f"OK: candidate bound to {rec['approval_id']}"
                              f" ({rec['owner']['status']})")
            if not bound:
                print(f"FAIL: proposed candidate {version} has no approval "
                      f"record binding its exact hashes")
                ok = False
        return 0 if ok else 1


def cmd_state(face: str, state: str, out: Path, strict: bool) -> int:
    contract = V.VisualContract.load(face)
    warn = V.check_pillow_pin(contract, strict)
    if warn:
        print(f"WARN: {warn}", file=sys.stderr)
    scene = V.Scene.load(face)
    img = V.render_state(scene, contract, state)
    sha = V.save_png_deterministic(img, out)
    print(f"{out} sha256={sha}")
    return 0


def cmd_selftest(face: str) -> int:
    """Render every contract state twice; byte-identical output required."""
    import tempfile
    contract = V.VisualContract.load(face)
    scene = V.Scene.load(face)
    failures = 0
    with tempfile.TemporaryDirectory() as td:
        for name in contract.raw["states"]:
            shas = []
            for run in (1, 2):
                img = V.render_state(scene, contract, name)
                p = Path(td) / f"{name}.{run}.png"
                shas.append(V.save_png_deterministic(img, p))
            status = "OK" if shas[0] == shas[1] else "FAIL"
            if status == "FAIL":
                failures += 1
            print(f"{status}: state {name} deterministic "
                  f"({shas[0][:16]}…)")
    return 1 if failures else 0


def cmd_make_masks(face: str) -> int:
    """Deterministic default mask: exclude the top-center system indicator
    area One UI can overlay on device captures (charging bolt)."""
    from PIL import Image, ImageDraw
    mask = Image.new("L", (480, 480), 255)
    d = ImageDraw.Draw(mask)
    d.ellipse((240 - 26, 10, 240 + 26, 62), fill=0)
    out = (V.REPO / "watchfaces" / face / "visual" / "masks" /
           "device_status_overlay.png")
    sha = V.save_png_deterministic(mask, out)
    print(f"{out} sha256={sha}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("face")
    ap.add_argument("--state")
    ap.add_argument("--out", type=Path, default=Path("reference.png"))
    ap.add_argument("--goldens", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="fail (not warn) on Pillow version pin mismatch")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--make-default-masks", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return cmd_selftest(a.face)
    if a.make_default_masks:
        return cmd_make_masks(a.face)
    if a.goldens:
        return cmd_goldens(a.face, a.check, a.strict)
    if not a.state:
        ap.error("--state, --goldens, --selftest or --make-default-masks required")
    return cmd_state(a.face, a.state, a.out, a.strict)


if __name__ == "__main__":
    raise SystemExit(main())
