#!/usr/bin/env python3
"""Side-by-side close-up comparison of two visual generations.

Crops the same regions from both reference renders and lays them out
baseline | candidate | difference so a finishing change can be inspected
at a useful scale instead of at 480 px.

    python3 tools/closeup_compare.py aurelius \
        --a field-tourbillon-mk2-r2 --b field-tourbillon-mk2-rc1

Reads the approved golden for --a and the proposed candidate for --b (or
the golden, if that version has been promoted). Writes into
watchfaces/<face>/visual/candidates/<b>/closeups/.

The difference panel is an absolute per-channel delta, amplified 4x so a
restrained finishing change is visible at all; it is an inspection aid,
not a metric. The metrics come from tools/compare_visuals.py.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]

# (name, box in 480-px canvas coords, what it shows)
REGIONS = [
    ("cage", (168, 285, 320, 437),
     "tourbillon cage, balance, jewel cup, cage rim"),
    ("bridge", (120, 85, 336, 165),
     "upper bridge, AURELIUS signature, bridge screws"),
    ("date_gear", (272, 168, 400, 344),
     "date aperture frame, gear R teeth, arbor, jewel"),
    ("reserve", (52, 52, 196, 196),
     "reserve-gauge arc, tick markings, needle"),
    ("case_bezel", (0, 0, 200, 200),
     "octagonal case flank, bezel screw, satin brushing"),
]

ZOOM = 3
DIFF_GAIN = 4


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def font(size: int):
    for c in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


def resolve(face: str, version: str, kind: str) -> Path:
    base = REPO / "watchfaces" / face / "visual"
    for sub in ("goldens", "candidates"):
        p = base / sub / version / f"{kind}.png"
        if p.exists():
            return p
    raise SystemExit(f"no {kind}.png for {version}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("face")
    ap.add_argument("--a", required=True, help="baseline visual version")
    ap.add_argument("--b", required=True, help="candidate visual version")
    ap.add_argument("--kinds", default="normal,aod")
    args = ap.parse_args()

    out_dir = (REPO / "watchfaces" / args.face / "visual" / "candidates"
               / args.b / "closeups")
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for kind in args.kinds.split(","):
        kind = kind.strip()
        pa, pb = resolve(args.face, args.a, kind), resolve(args.face, args.b,
                                                           kind)
        ia = Image.open(pa).convert("RGB")
        ib = Image.open(pb).convert("RGB")
        if ia.size != ib.size:
            raise SystemExit(f"{kind}: size mismatch {ia.size} vs {ib.size}")

        for name, box, desc in REGIONS:
            ca, cb = ia.crop(box), ib.crop(box)
            diff = ImageChops.difference(ca, cb).point(
                lambda v: min(255, v * DIFF_GAIN))
            w, h = ca.size
            zw, zh = w * ZOOM, h * ZOOM
            panels = [p.resize((zw, zh), Image.NEAREST)
                      for p in (ca, cb, diff)]
            labels = [f"{args.a}  (baseline)", f"{args.b}  (candidate)",
                      f"|delta| x{DIFF_GAIN}"]
            pad, top, cap = 14, 56, 34
            W = pad + 3 * (zw + pad)
            H = top + zh + cap + pad
            sheet = Image.new("RGB", (W, H), (14, 14, 16))
            d = ImageDraw.Draw(sheet)
            d.text((pad, 12), f"{args.face} · {kind} · {name} — {desc}",
                   font=font(20), fill=(226, 222, 210))
            d.text((pad, 34), f"region {box} in the 480px canvas, {ZOOM}x",
                   font=font(14), fill=(150, 148, 142))
            for i, (panel, lab) in enumerate(zip(panels, labels)):
                x = pad + i * (zw + pad)
                sheet.paste(panel, (x, top))
                d.text((x, top + zh + 8), lab, font=font(15),
                       fill=(196, 192, 182))
            out = out_dir / f"{kind}_{name}.png"
            sheet.save(out, format="PNG", optimize=False)
            written.append(out)
            print(f"wrote {out.relative_to(REPO)}")

    manifest = out_dir / "CHECKSUMS.sha256"
    manifest.write_text(
        "\n".join(f"{sha256(p)}  {p.name}" for p in sorted(written)) + "\n",
        encoding="utf-8")
    print(f"{len(written)} close-ups, checksums in "
          f"{manifest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
