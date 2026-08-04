#!/usr/bin/env python3
"""HOG-WILD readability pass: live data gets real apertures.

WHAT THIS FIXES, AND WHY IN THE ART.

1. THE SCOPE SHIPPED WITH A PAINTED SWEEP. The concept plate was regenerated
   "hands-free", but the radar scope kept a frozen sweep wedge and a scatter
   of frozen return blips baked into wh_dial.png (and a pale twin of the
   wedge in wh_dial_aod.png). The live sweep overlay then rotates over its
   own ghost: on the wrist the scope reads two sweeps, one of them stuck at
   eleven o'clock, and blips that never move — precisely the fault
   strip_baked_reticle.py fixed on HAYATE, wearing green. The glass is
   rebuilt here procedurally: phosphor gradient, range rings, crosshair,
   seeded grain. Original by construction, nothing baked that also moves.

2. THE DEAD SUB-DIAL EARNS ITS SEAT. The nine o'clock sub-dial was concept
   furniture: a painted needle pointing at nothing, bound to nothing. The
   needle goes, the face is redrawn clean, and the dial's own LCD aperture
   art (copied from the plate at three o'clock, so the bezel language
   matches exactly) is inset at its centre. The engine then paints STEP_COUNT
   there at size 20 — the reading the old 16px odometer squint never managed.

3. THE ODOMETER BARREL BECOMES A DATE WINDOW. Five segmented cells ~11px
   wide were never going to carry five digits legibly, and after (2) they
   would carry them twice. A clean small aperture takes their place and the
   engine paints the day-of-month there: two digits, which is exactly what
   the window has room for.

Deterministic and idempotent: every repaint is a pure function of geometry
and seed, so a second run reproduces the same bytes.

Usage:
    python3 tools/hogwild_readability.py            # report planned edits
    python3 tools/hogwild_readability.py --write
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
DRAWABLE = REPO / "watchfaces/hogwild/app/src/main/res/drawable"

# Geometry, measured off the shipped plate (480x480).
SCOPE_C = (240.5, 361.5)     # PPI scope centre (from the z09/z10 sprite box)
SCOPE_R = 53                 # glass radius inside the bezel
SUBDIAL_C = (122, 248)       # nine-o'clock sub-dial centre
SUBDIAL_FACE_R = 43          # inner face, ticks redrawn inside this
LCD_SRC = (314, 217, 405, 254)   # the plate's own LCD aperture art
BARREL = (133, 340)          # odometer window centre (steps gauge)
BARREL_SIZE = (70, 24)       # date aperture pasted over the old barrel


def _seeded(tag: str) -> random.Random:
    return random.Random(f"hogwild-readability/{tag}")


def strip_wedge_overspill(img: Image.Image) -> None:
    """The baked sweep ran past the glass onto the bezel (out to r≈67).

    Inside the glass the rebuild simply paints over it; on the bezel there is
    machined metal to preserve, so the wedge comes out the HAYATE way: a
    colour key finds the saturated green nothing on a grey bezel comes close
    to, and repeated blur-fill from the trusted neighbours closes the hole.
    """
    cx, cy = SCOPE_C
    px = img.load()
    mask = Image.new("L", img.size, 0)
    mpx = mask.load()
    n = 0
    for y in range(288, 434):
        for x in range(170, 314):
            r2 = (x - cx) ** 2 + (y - cy) ** 2
            if r2 < (SCOPE_R - 4) ** 2 or r2 > 72 ** 2:
                continue
            p = px[x, y]
            if p[1] > p[0] + 12 and p[1] > p[2] + 12:
                mpx[x, y] = 255
                n += 1
    mask = mask.filter(ImageFilter.MaxFilter(5))  # take the bloom too
    for _ in range(48):
        blurred = img.filter(ImageFilter.GaussianBlur(3))
        img.paste(blurred, (0, 0), mask)
    # the fill converges from neighbours that include glass shadow, which
    # leaves a green cast on metal; the bezel is grey, so cap green at the
    # grey implied by the other two channels
    px = img.load()
    mpx = mask.load()
    for y in range(288, 434):
        for x in range(170, 314):
            if mpx[x, y]:
                p = px[x, y]
                g_cap = (p[0] + p[2]) // 2 + 4
                if p[1] > g_cap:
                    px[x, y] = (p[0], g_cap, p[2])


def rebuild_scope(img: Image.Image) -> None:
    """Replace the scope glass wholesale: gradient, rings, crosshair, grain."""
    cx, cy = SCOPE_C
    r = SCOPE_R
    size = 4 * r  # supersample x2
    glass = Image.new("RGB", (size, size), (0, 0, 0))
    g = ImageDraw.Draw(glass)
    gc = size / 2
    # phosphor gradient, brighter at centre the way a CRT pools
    for rr in range(2 * r, 0, -1):
        t = rr / (2 * r)
        col = (int(16 - 6 * t + 2), int(58 - 22 * t), int(24 - 10 * t))
        g.ellipse([gc - rr, gc - rr, gc + rr, gc + rr], fill=col)
    ring = (44, 96, 54)
    for ring_r in (r * 2 // 3, r * 4 // 3):
        g.ellipse([gc - ring_r, gc - ring_r, gc + ring_r, gc + ring_r],
                  outline=ring, width=2)
    g.line([gc - 2 * r, gc, gc + 2 * r, gc], fill=(34, 76, 42), width=2)
    g.line([gc, gc - 2 * r, gc, gc + 2 * r], fill=(34, 76, 42), width=2)
    # seeded phosphor grain
    rng = _seeded("glass")
    px = glass.load()
    for _ in range(1400):
        x = rng.randrange(size)
        y = rng.randrange(size)
        if (x - gc) ** 2 + (y - gc) ** 2 < (2 * r) ** 2:
            p = px[x, y]
            dv = rng.randint(-5, 7)
            px[x, y] = (max(0, p[0] + dv // 2), max(0, p[1] + dv),
                        max(0, p[2] + dv // 2))
    glass = glass.resize((2 * r, 2 * r), Image.LANCZOS)
    # rim shadow so the glass sits behind the bezel, not on it
    shade = Image.new("L", (2 * r, 2 * r), 0)
    sd = ImageDraw.Draw(shade)
    for i in range(6):
        a = 90 - i * 15
        sd.ellipse([i, i, 2 * r - 1 - i, 2 * r - 1 - i], outline=a, width=1)
    glass = Image.composite(Image.new("RGB", glass.size, (2, 10, 4)),
                            glass, shade.point(lambda v: v))
    mask = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.7))
    img.paste(glass, (int(cx) - r, int(cy) - r), mask)


def rebuild_scope_aod(img: Image.Image) -> None:
    """AOD scope: black glass, lume range rings, no frozen sweep.

    The blackout disc runs to r=65, not the glass radius: the baked wedge
    spilled onto the bezel here exactly as it did on the day plate, and in
    line-art there is no metal to preserve — the nearest legitimate lume
    stroke starts at r≈67.
    """
    cx, cy = SCOPE_C
    wipe = 65
    patch = Image.new("RGBA", (2 * wipe, 2 * wipe), (0, 0, 0, 255))
    d = ImageDraw.Draw(patch)
    lume = (118, 139, 120, 150)
    r = SCOPE_R - 1
    for ring_r in (r // 3, 2 * r // 3):
        d.ellipse([wipe - ring_r, wipe - ring_r, wipe + ring_r,
                   wipe + ring_r], outline=lume, width=1)
    mask = Image.new("L", (2 * wipe, 2 * wipe), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * wipe - 1, 2 * wipe - 1],
                                 fill=255)
    img.paste(patch, (int(cx) - wipe, int(cy) - wipe), mask)


def rebuild_subdial(img: Image.Image) -> None:
    """Clean face for the nine-o'clock sub-dial and inset the LCD aperture."""
    cx, cy = SUBDIAL_C
    r = SUBDIAL_FACE_R
    face = Image.new("RGB", (2 * r, 2 * r), (0, 0, 0))
    f = ImageDraw.Draw(face)
    for rr in range(r, 0, -1):
        v = int(120 + 18 * (1 - rr / r))
        f.ellipse([r - rr, r - rr, r + rr, r + rr], fill=(v, v, v))
    rng = _seeded("subdial")
    px = face.load()
    for _ in range(900):
        x = rng.randrange(2 * r)
        y = rng.randrange(2 * r)
        if (x - r) ** 2 + (y - r) ** 2 < r * r:
            p = px[x, y]
            dv = rng.randint(-4, 4)
            px[x, y] = (p[0] + dv, p[1] + dv, p[2] + dv)
    # twelve fresh ticks, engraved dark on the brushed face
    for i in range(12):
        a = math.radians(i * 30)
        x0 = r + (r - 4) * math.sin(a)
        y0 = r - (r - 4) * math.cos(a)
        x1 = r + (r - 16) * math.sin(a)
        y1 = r - (r - 16) * math.cos(a)
        f.line([x0, y0, x1, y1], fill=(58, 58, 58), width=3)
    mask = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    img.paste(face, (int(cx) - r, int(cy) - r), mask)
    # the dial's own LCD aperture, transplanted so the language matches
    lcd = img.crop(LCD_SRC)
    img.paste(lcd, (int(cx) - lcd.width // 2, int(cy) - lcd.height // 2))


def date_window(img: Image.Image) -> None:
    """Replace the segmented odometer barrel with a clean date aperture."""
    lcd = img.crop(LCD_SRC).resize(BARREL_SIZE, Image.LANCZOS)
    img.paste(lcd, (BARREL[0] - BARREL_SIZE[0] // 2,
                    BARREL[1] - BARREL_SIZE[1] // 2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    dial_p = DRAWABLE / "wh_dial.png"
    aod_p = DRAWABLE / "wh_dial_aod.png"
    dial = Image.open(dial_p).convert("RGB")
    aod = Image.open(aod_p).convert("RGBA")

    strip_wedge_overspill(dial)
    rebuild_scope(dial)
    rebuild_subdial(dial)
    date_window(dial)
    rebuild_scope_aod(aod)

    if not args.write:
        print("dry run — would rewrite:")
        print(f"  {dial_p.relative_to(REPO)}  (scope glass, 9h sub-dial, "
              "date aperture)")
        print(f"  {aod_p.relative_to(REPO)}  (scope glass)")
        return 0

    dial.save(dial_p)
    aod.save(aod_p)
    print(f"wrote {dial_p.relative_to(REPO)}")
    print(f"wrote {aod_p.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
