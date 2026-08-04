#!/usr/bin/env python3
"""Combination-lock wheel digits for HOG-WILD: the `wheel` bitmap font.

The 1.3.0 readability pass put the live numbers in honest apertures, but it
painted them as LCD phosphor — a screen, on a dial whose design language
says instrumentation, never a widget. A cockpit counter is a drum: this
draws every digit as one wheel of a combination lock seen through its slot.

ANATOMY OF A CELL. Each glyph is a complete wheel column, so a multi-digit
reading composes into a wheel bank with no extra layout work:

- knurled flanks: horizontal ridge serrations at both edges — the grip you
  would thumb to spin the wheel, and the visual seam between adjacent
  wheels when cells sit flush;
- drum face: brushed steel with a cylindrical vertical falloff — bright at
  the equator, rolling off dark at top and bottom, with detent shadow lines
  where the neighbouring digit positions turn away;
- numeral: engraved, not printed — dark fill, shadowed upper edge, lit
  lower lip, per roadmap/DESIGN_LANGUAGE.md.

BITMAP FONTS ARE ALPHA MASKS. The format's text pipeline keeps a glyph's
alpha channel and replaces its colour wholesale with the BitmapFont colour
attribute (tools/render_face_from_xml.py `tint()` models this). A glyph
therefore cannot ship colour — it ships RELIEF: the wheel is drawn in
luminance and the luminance becomes alpha, so the declared steel tint reads
at full strength on the drum's lit equator, thins toward the rolled-away
edges, and vanishes in the engraved digit cut, where the aperture's own
darkness does the ink's job. WFF cannot roll a drum on a text element —
the rotation is sold by shading, not animation.

Deterministic: pure function of geometry; no seeds, no timestamps.

Usage:
    python3 tools/make_wheel_font.py            # report
    python3 tools/make_wheel_font.py --write
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
DRAWABLE = REPO / "watchfaces/hogwild/app/src/main/res/drawable"
FONT_TTF = Path.home() / ".local/share/fonts/BarlowCondensed-Bold.ttf"

SS = 4                       # supersample factor
CELL_W, CELL_H = 34, 46      # shipped glyph size (declared in face.toml)
FLANK_W = 5                  # knurled strip width per side, shipped px


def drum_shade(y: float, h: float) -> float:
    """Cylinder illumination for a horizontal-axis drum: 1.0 at the
    equator, rolling off with the cosine of the wrap angle."""
    t = abs(y - h / 2) / (h / 2)         # 0 centre -> 1 edge
    return max(0.18, math.cos(t * 1.25))


def draw_wheel(digit: str) -> Image.Image:
    w, h = CELL_W * SS, CELL_H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    flank = FLANK_W * SS

    # ---- drum face: brushed steel under cylindrical light ----
    face_x0, face_x1 = flank, w - flank
    for y in range(h):
        s = drum_shade(y, h)
        base = 168 * s
        # fine vertical brushing: a deterministic per-column jitter
        for x in range(face_x0, face_x1):
            b = base + 14 * math.sin(x * 1.7 + (x % 5)) * 0.5
            v = int(max(12, min(236, b)))
            d.point((x, y), (v, v, min(255, v + 4), 255))

    # detent shadows where the neighbour digit positions turn away
    for yy in (int(h * 0.06), int(h * 0.94)):
        d.line([(face_x0, yy), (face_x1, yy)], fill=(10, 10, 12, 255),
               width=SS)

    # ---- knurled flanks: horizontal ridges, darker than the face ----
    ridge_p = 3 * SS                     # ridge period
    for side_x0 in (0, w - flank):
        for y in range(h):
            s = drum_shade(y, h) * 0.62
            phase = (y % ridge_p) / ridge_p
            ridge = 0.55 + 0.45 * math.cos(phase * 2 * math.pi)
            v = int(max(6, min(190, 150 * s * ridge)))
            d.line([(side_x0, y), (side_x0 + flank - 1, y)],
                   fill=(v, v, v, 255))
        # seam between flank and face
        seam_x = side_x0 + (flank - SS if side_x0 == 0 else 0)
        d.rectangle([seam_x, 0, seam_x + SS - 1, h], fill=(8, 8, 9, 255))

    # ---- the numeral: engraved into the drum ----
    fnt = ImageFont.truetype(str(FONT_TTF), int(h * 0.62))
    bbox = d.textbbox((0, 0), digit, font=fnt)
    tx = (face_x0 + face_x1) / 2 - (bbox[0] + bbox[2]) / 2
    ty = h / 2 - (bbox[1] + bbox[3]) / 2
    # lit lower lip first, then the dark cut over it
    d.text((tx, ty + SS), digit, font=fnt, fill=(228, 230, 234, 200))
    d.text((tx, ty - SS // 2), digit, font=fnt, fill=(24, 25, 28, 255))

    img = img.resize((CELL_W, CELL_H), Image.LANCZOS)

    # luminance -> alpha (boosted so lit steel renders near-solid), colour
    # discarded: the BitmapFont tint supplies it at render time
    lum = img.convert("L").point(lambda v: min(255, int(v * 1.35)))
    out = Image.new("RGBA", img.size, (255, 255, 255, 0))
    out.putalpha(lum)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not FONT_TTF.exists():
        print(f"missing numeral typeface: {FONT_TTF}", file=sys.stderr)
        return 1

    for n in range(10):
        glyph = draw_wheel(str(n))
        out = DRAWABLE / f"w_{n}.png"
        if args.write:
            glyph.save(out)
            print(f"wrote {out.relative_to(REPO)}")
        else:
            print(f"would write {out.relative_to(REPO)}  "
                  f"({CELL_W}x{CELL_H})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
