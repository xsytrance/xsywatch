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


def cmd_goldens(face: str, check: bool, strict: bool) -> int:
    contract = V.VisualContract.load(face)
    version = contract.golden_states()["version"]
    gdir = golden_dir(face, version)
    if not check:
        meta = render_goldens(face, gdir, strict)
        V.dump_json_deterministic(meta, gdir / "METADATA.json")
        print(f"goldens written to {gdir}")
        return 0
    # check mode: render to temp, byte-compare against committed goldens
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        render_goldens(face, Path(td), strict)
        ok = True
        for kind in ("normal", "aod"):
            committed = gdir / f"{kind}.png"
            fresh = Path(td) / f"{kind}.png"
            if not committed.exists():
                print(f"FAIL: missing committed golden {committed}")
                ok = False
                continue
            if committed.read_bytes() != fresh.read_bytes():
                print(f"FAIL: {kind} golden drifted from deterministic "
                      f"re-render ({committed})")
                ok = False
            else:
                print(f"OK: {kind} golden reproduces byte-identically")
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
