#!/usr/bin/env python3
"""Date-aperture proof for engine-managed faces (Phase-3 r1 review).

The plate art draws a framed date window; the live BitmapFont date renders
into it. This tool measures, for every valid day 1..31, the alpha bounds of
the rendered date text and checks them against the inner aperture declared
in the face's visual contract, requiring a minimum clear margin on every
side.

It is the executable half of the aperture contract: the studio authors the
opening, this proves the live presentation actually fits it.

Usage:
  date_aperture_proof.py <face>                 # measure + report
  date_aperture_proof.py <face> --check         # exit 1 on any violation
  date_aperture_proof.py <face> --sheet OUT.png # committed proof sheet
  date_aperture_proof.py <face> --json OUT.json # machine-readable bounds

The proof sheet shows the contract days in both normal and AOD treatment,
each crop annotated with the measured margins.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visuallib as V  # noqa: E402


def inner_bounds(ap: dict) -> tuple[float, float, float, float]:
    """Derive the inner-opening bounds from centre + size (single source of
    truth in the contract)."""
    cx, cy = ap["center_px"]
    w, h = ap["inner_size_px"]
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def date_layer(scene: V.Scene):
    for lay in scene.layers:
        if lay.kind == "text" and lay.text:
            return lay
    raise SystemExit("face has no text layer")


def measure_day(scene: V.Scene, contract: V.VisualContract, day: int,
                ambient: bool) -> dict:
    """Render the date text for `day` and return its alpha bounds in
    480x480 face coordinates."""
    from PIL import Image

    state = contract.state("aod" if ambient else "normal_hero")
    pinned = dict(state["pinned"])
    pinned["DAY"] = float(day)
    lay = date_layer(scene)
    tile = V._render_text(scene, lay, pinned)
    alpha = tile.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise SystemExit(f"day {day}: text rendered empty")
    x0, y0, x1, y1 = bbox
    return {
        "day": day,
        "ambient": ambient,
        # tile is placed at the layer box origin; convert to face coords
        "bounds": [lay.x + x0, lay.y + y0, lay.x + x1 - 1, lay.y + y1 - 1],
        "ink_size": [x1 - x0, y1 - y0],
        "tile": tile,
    }


def evaluate(face: str) -> dict:
    scene = V.Scene.load(face)
    contract = V.VisualContract.load(face)
    ap = contract.raw.get("date_aperture")
    if not ap:
        raise SystemExit(f"{face}: no [date_aperture] in the visual contract")
    ix0, iy0, ix1, iy1 = inner_bounds(ap)
    need = float(ap["min_clear_margin_px"])

    results, violations = [], []
    for day in range(1, 32):
        for ambient in (False, True):
            m = measure_day(scene, contract, day, ambient)
            bx0, by0, bx1, by1 = m["bounds"]
            margins = {"left": bx0 - ix0, "top": by0 - iy0,
                       "right": ix1 - bx1, "bottom": iy1 - by1}
            worst = min(margins.values())
            rec = {k: m[k] for k in ("day", "ambient", "bounds", "ink_size")}
            rec["margins"] = {k: round(v, 2) for k, v in margins.items()}
            rec["worst_margin"] = round(worst, 2)
            rec["ok"] = worst >= need
            results.append(rec)
            if not rec["ok"]:
                violations.append(rec)
    return {"face": face, "inner_bounds_px": [ix0, iy0, ix1, iy1],
            "min_clear_margin_px": need, "days_checked": 31,
            "renders_checked": len(results),
            "worst_margin_px": round(min(r["worst_margin"] for r in results), 2),
            "violations": violations, "results": results}


def build_sheet(face: str, out: Path) -> None:
    from PIL import Image, ImageDraw

    scene = V.Scene.load(face)
    contract = V.VisualContract.load(face)
    ap = contract.raw["date_aperture"]
    days = ap["proof_days"]
    ix0, iy0, ix1, iy1 = inner_bounds(ap)
    pad, scale = 8, 4
    crop = (int(ix0) - 12, int(iy0) - 12, int(ix1) + 13, int(iy1) + 13)
    cw, ch = (crop[2] - crop[0]) * scale, (crop[3] - crop[1]) * scale
    sheet = Image.new("RGB", (len(days) * (cw + pad) + pad,
                              2 * (ch + 26) + pad), (18, 18, 20))
    draw = ImageDraw.Draw(sheet)

    for row, ambient in enumerate((False, True)):
        state = contract.state("aod" if ambient else "normal_hero")
        for col, day in enumerate(days):
            pinned = dict(state["pinned"])
            pinned["DAY"] = float(day)
            # full-face render with the day pinned
            name = f"_proof_{day}_{int(ambient)}"
            contract.raw["states"][name] = dict(state["raw"])
            contract.raw["states"][name]["day"] = day
            img = V.render_state(scene, contract, name)
            tile = img.crop(crop).resize((cw, ch), Image.NEAREST)
            x = pad + col * (cw + pad)
            y = pad + row * (ch + 26)
            sheet.paste(tile, (x, y))
            # inner-aperture guide
            gx0 = (ix0 - crop[0]) * scale
            gy0 = (iy0 - crop[1]) * scale
            gx1 = (ix1 - crop[0]) * scale
            gy1 = (iy1 - crop[1]) * scale
            draw.rectangle([x + gx0, y + gy0, x + gx1, y + gy1],
                           outline=(0, 220, 120), width=1)
            draw.text((x + 2, y + ch + 6),
                      f"{'AOD ' if ambient else 'NRM '}{day}",
                      fill=(210, 210, 215))
    V.save_png_deterministic(sheet.convert("RGBA"), out)
    print(f"proof sheet -> {out}")


def main() -> int:
    ap_ = argparse.ArgumentParser(description=__doc__)
    ap_.add_argument("face")
    ap_.add_argument("--check", action="store_true")
    ap_.add_argument("--sheet", type=Path)
    ap_.add_argument("--json", type=Path)
    a = ap_.parse_args()

    data = evaluate(a.face)
    print(f"aperture inner bounds : {data['inner_bounds_px']}")
    print(f"required clear margin : {data['min_clear_margin_px']} px")
    print(f"renders checked       : {data['renders_checked']} "
          f"(days 1..31, normal + AOD)")
    print(f"worst margin observed : {data['worst_margin_px']} px")
    for v in data["violations"]:
        print(f"  FAIL day {v['day']} "
              f"{'AOD' if v['ambient'] else 'normal'}: margins {v['margins']}")
    if a.json:
        V.dump_json_deterministic(
            {k: v for k, v in data.items() if k != "results"} |
            {"results": data["results"]}, a.json)
        print(f"bounds json -> {a.json}")
    if a.sheet:
        build_sheet(a.face, a.sheet)
    if data["violations"]:
        print(f"FAIL: {len(data['violations'])} render(s) violate the "
              f"clear-margin requirement")
        return 1
    print("OK: every day 1..31 fits the aperture in normal and AOD")
    return 0 if not a.check or not data["violations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
