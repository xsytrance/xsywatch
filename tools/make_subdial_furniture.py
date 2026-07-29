#!/usr/bin/env python3
"""Give the sub-dials a scale, a label, and a pointer that means something.

WHAT WENT WRONG. The hero concepts put a labelled readout in each sub-dial: a
dark well with STEPS or BPM in small caps at the top and the value filling the
middle in large type. No needle — the number was the instrument.

What shipped instead has an empty well, a full-length needle sweeping an
unmarked rim, and the value shrunk to 16px and pushed down onto the bezel
where it half leaves the disc. So the number is hard to read and the needle
points at nothing: there is no scale under it to point at.

WHAT THIS DRAWS. Both halves, so the pointer earns its place:

  furniture  the label in small caps at the top of the well, a tick scale
             around the rim with numerals at zero, midpoint and full scale,
             and the well left clear in the middle for the value.
  pointer    a short wedge that lives out at the rim. The old needle ran the
             full radius and crossed the middle of the well, which is exactly
             where the value now sits.

The value itself is repositioned and enlarged by the face spec, not here.

Scale geometry matches the value_needle binding exactly — start 235 degrees,
sweeping 250 clockwise, which puts zero at lower left, full scale at lower
right and the gap at the bottom. If a face spec changes those, this must
change with it or the printed scale will lie about where the pointer is.

Drawn at 3x and downsampled: at this size a tick is barely more than a pixel,
and aliasing reads as grime on a dial that is meant to look machined.

Usage:
    python3 tools/make_subdial_furniture.py --all
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SS = 3                      # supersample factor
START_DEG = 235.0           # must match value_needle start_deg in the spec
SWEEP_DEG = 250.0           # must match value_needle sweep_deg

# ink   — label and numerals
# tick  — scale marks
# point — the pointer wedge
# GEOMETRY IS MEASURED, NOT ASSUMED. `steps`/`bpm` are the painted well's
# centre and inner radius, read off each plate by a radial brightness profile
# — the point where the dark well floor gives way to the bright bezel.
#
# The needle boxes in the face specs are NOT this. They were sized for pivot
# convenience and are up to twice the well across, so furniture built to them
# printed its scale out on the open dial instead of around the well.
#
# Worth knowing: these wells are also much smaller than the hero concepts
# showed — HAYATE's is 56px where the concept implies ~96px — because the
# plate was regenerated smaller. That is why the value cannot be as large as
# the concept's without a new plate.
FACES = {
    "hayate":    {"prefix": "hy", "steps": (135, 291, 28), "bpm": (329, 297, 30),
                  "ink": (226, 223, 206, 255), "tick": (176, 174, 158, 255),
                  "point": (214, 84, 62, 255)},
    "balsa":     {"prefix": "ba", "steps": (140, 307, 40), "bpm": (340, 307, 40),
                  "ink": (246, 240, 218, 255), "tick": (150, 142, 118, 255),
                  "point": (198, 66, 52, 255)},
    "commodore": {"prefix": "cm", "steps": (144, 301, 29), "bpm": (343, 303, 30),
                  "ink": (236, 188, 78, 255), "tick": (156, 174, 202, 255),
                  "point": (236, 188, 78, 255)},
    "pure":      {"prefix": "pu", "steps": (142, 304, 33), "bpm": (338, 304, 34),
                  "ink": (230, 230, 234, 255), "tick": (146, 146, 154, 255),
                  "point": (232, 116, 44, 255)},
}


def sprite_size(r_in: int) -> int:
    """Sprite big enough that its outermost tick lands on the well's inner
    edge. furniture() draws ticks out to 0.95 of the half-width."""
    return int(round(2 * r_in / 0.95))

# label, and the three numerals printed at 0 / half / full scale
GAUGES = {
    "steps": ("STEPS", ("0", "10", "20")),     # thousands
    "bpm":   ("BPM", ("0", "100", "200")),
}


def _drawable(face: str) -> Path:
    return REPO / "watchfaces" / face / "app/src/main/res/drawable"


def _at(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    """Polar to cartesian in WFF's convention: 0 is up, clockwise."""
    a = math.radians(deg - 90.0)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def furniture(size: int, label: str, numerals: tuple[str, str, str],
              ink, tick) -> Image.Image:
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2.0
    r_out = c * 0.95
    r_maj = c * 0.78
    r_min = c * 0.85

    # Ticks. Eleven majors across the sweep is one per tenth of full scale —
    # dense enough to read a value off, sparse enough not to become texture.
    for i in range(11):
        deg = START_DEG + SWEEP_DEG * i / 10.0
        w = max(1, int(1.6 * SS)) if i % 5 == 0 else max(1, int(0.9 * SS))
        inner = r_maj if i % 5 == 0 else r_min
        d.line([_at(c, c, inner, deg), _at(c, c, r_out, deg)],
               fill=tick if i % 5 else ink, width=w)

    try:
        f_num = ImageFont.truetype(FONT, max(5, int(size * 0.105)) * SS)
        f_lab = ImageFont.truetype(FONT, max(6, int(size * 0.115)) * SS)
    except OSError:
        f_num = f_lab = ImageFont.load_default()

    # ONLY the two end numerals, and they go in the gap at the bottom of the
    # sweep. A hundred-pixel well cannot hold a label, a four-digit value, a
    # tick ring AND numerals around it — the first attempt printed "10" and
    # "STEPS" on top of each other. The bottom gap is the one part of the
    # dial with nothing else competing for it, and the two ends are what a
    # reader actually needs to scale the pointer against.
    # Below about 70px the end numerals stop being letters and become dirt.
    for i, txt in (((0, numerals[0]), (10, numerals[2])) if size >= 70 else ()):
        deg = START_DEG + SWEEP_DEG * i / 10.0
        x, y = _at(c, c, c * 0.72, deg)
        d.text((x, y), txt, font=f_num, fill=tick, anchor="mm")

    # Label sits high in the well, clear of the value that goes in the middle.
    d.text((c, c * 0.46), label, font=f_lab, fill=ink, anchor="mm")

    return img.resize((size, size), Image.LANCZOS)


def pointer(size: int, colour) -> Image.Image:
    """A short wedge out at the rim, drawn pointing up so the spec's
    start/sweep rotation lands it on the printed scale."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2.0
    tip, tail, half = c * 0.86, c * 0.60, 2.1 * SS
    d.polygon([(c, c - tip), (c - half, c - tail), (c + half, c - tail)],
              fill=colour)
    # A dark seat under the tail stops the wedge floating on a light dial.
    d.ellipse([c - half * 1.5, c - tail - half, c + half * 1.5, c - tail + half],
              fill=(0, 0, 0, 90))
    return img.resize((size, size), Image.LANCZOS)


def build_face(face: str) -> list[tuple[str, int]]:
    cfg = FACES[face]
    out = _drawable(face)
    written = []

    def save(name: str, img: Image.Image) -> None:
        p = out / f"{cfg['prefix']}_{name}.png"
        img.save(p, optimize=True)
        written.append((p.name, p.stat().st_size))

    for key, (label, numerals) in GAUGES.items():
        cx, cy, r = cfg[key]
        sz = sprite_size(r)
        save(f"gauge_{key}", furniture(sz, label, numerals,
                                       cfg["ink"], cfg["tick"]))
        save(f"ptr_{key}", pointer(sz, cfg["point"]))
    return written


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--face", choices=sorted(FACES))
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)
    if not args.face and not args.all:
        ap.error("pass --face <name> or --all")
    for f in (sorted(FACES) if args.all else [args.face]):
        print(f"{f}:")
        for n, s in build_face(f):
            print(f"  {n:22s} {s / 1024:6.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
