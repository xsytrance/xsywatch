#!/usr/bin/env python3
"""Remove the gunsight reticle baked into HAYATE's moving weather field.

THE BUG THIS FIXES. HAYATE ships two reticles. One is etched on
hy_sight_glass.png, which is fixed to the instrument and correct. The other
was generated into the weather scenes themselves and so survived into
hy_fld_*.png, which is the layer that rolls and pitches with the wrist. On a
level wrist they sit on top of each other and the fault is invisible; tilt the
arm and the sight splits in two, one half sliding away across the view.

pipeline/hayate_viewfinder.py already warned about exactly this — "a reticle
that slides off the sight is worse than no reticle" — and guarded against it
by cropping the dome's rim out of the field. That removes furniture at the
edges, which is where a rim lives, and does nothing about a reticle in the
middle, which is where a reticle lives.

HOW IT COMES OUT. The reticle is drawn in a saturated red that nothing in a
sky-and-farmland scene comes close to, so a colour key finds it exactly
without touching the view. The hole it leaves is then filled by repeatedly
blurring the image and keeping the trusted pixels — with the marks being thin
and the surroundings smooth, that converges to what was behind them.

Idempotent: run it on an already-cleaned field and the key selects nothing.

Usage:
    python3 tools/strip_baked_reticle.py            # report only
    python3 tools/strip_baked_reticle.py --write
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
DRAWABLE = REPO / "watchfaces/hayate/app/src/main/res/drawable"
SCENES = ("clear", "overcast", "rain", "snow", "night")

# TWO THINGS HAVE TO GO, AND THEY NEED DIFFERENT TREATMENT.
#
# The mark itself is saturated red and comes out on a colour key. Around it
# is a soft bloom that is still reddish but nowhere near the key's threshold,
# and that bloom is what defeats the obvious approach: inpainting the mark
# fills it from its neighbours, and its neighbours are the bloom, so the ghost
# is reconstructed from the thing that should also have gone.
#
# So the mark is inpainted and the bloom is desaturated — red pulled down to
# whatever green and blue are already doing, over a much wider halo, feathered
# so the correction has no edge of its own. Desaturating leaves luminance
# alone, so nothing behind it is lost.
#
# The key is confined to a central disc. The reticle is drawn in the middle;
# the low sun in the clear scene is not, and it is the one piece of real
# content red enough to be mistaken for the target.
#
# NOT DONE BY CONSENSUS ACROSS THE FIVE SCENES, which would be the tidier
# trick: the scenes were generated separately, so their reticles do not
# register with each other. Intersecting them keeps 778 px of a ~2900 px mark.
RED_DOMINANCE = 1.14
RED_FLOOR = 45
DISC_FRACTION = 0.38          # of the sprite's half-width, from centre
GROW_PX = 3
FILL_PASSES = 34
HALO_PX = 13
HALO_FEATHER = 9.0


def _red_key(img: Image.Image) -> Image.Image:
    r, g, b = img.split()
    out = Image.new("L", img.size, 0)
    px_r, px_g, px_b, px_o = r.load(), g.load(), b.load(), out.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            rv = px_r[x, y]
            if rv >= RED_FLOOR and rv > max(px_g[x, y], px_b[x, y]) * RED_DOMINANCE:
                px_o[x, y] = 255
    return out


def reticle_mask(img: Image.Image) -> Image.Image:
    w, h = img.size
    disc = Image.new("L", (w, h), 0)
    f = DISC_FRACTION
    ImageDraw.Draw(disc).ellipse(
        [w * (0.5 - f), h * (0.5 - f), w * (0.5 + f), h * (0.5 + f)], fill=255)
    keyed = Image.composite(_red_key(img), Image.new("L", (w, h), 0), disc)
    return keyed.filter(ImageFilter.MaxFilter(GROW_PX * 2 + 1))


def _desaturate_red(img: Image.Image, region: Image.Image) -> Image.Image:
    """Pull red down to the green/blue level, weighted by the region mask."""
    r, g, b = img.split()
    nr = r.copy()
    px_r, px_g, px_b, px_n, px_m = r.load(), g.load(), b.load(), nr.load(), \
        region.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            m = px_m[x, y]
            if m > 8:
                other = max(px_g[x, y], px_b[x, y])
                if px_r[x, y] > other:
                    t = m / 255.0
                    px_n[x, y] = int(px_r[x, y] * (1 - t) + other * t)
    return Image.merge("RGB", (nr, g, b))


def strip(path: Path, write: bool) -> tuple[int, bool]:
    img = Image.open(path).convert("RGB")
    mask = reticle_mask(img)
    hit = sum(n for v, n in enumerate(mask.histogram()) if v > 127)
    if not hit:
        return 0, False

    cur = img
    for _ in range(FILL_PASSES):
        cur = Image.composite(cur.filter(ImageFilter.GaussianBlur(3)), cur, mask)
    halo = mask.filter(ImageFilter.MaxFilter(HALO_PX * 2 + 1)) \
               .filter(ImageFilter.GaussianBlur(HALO_FEATHER))
    cur = _desaturate_red(cur, halo)
    if write:
        cur.save(path)
    return hit, True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="rewrite the field sprites in place")
    args = ap.parse_args(argv)

    paths = [DRAWABLE / f"hy_fld_{s}.png" for s in SCENES]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print("missing: " + ", ".join(p.name for p in missing))
        paths = [p for p in paths if p.exists()]
    if not paths:
        return 1

    any_change = False
    for p in paths:
        hit, changed = strip(p, args.write)
        any_change |= changed
        state = ("rewritten" if args.write else "would change") if changed \
            else "clean"
        print(f"  {p.name:22s} {hit:6d} reticle px  {state}")
    if not any_change:
        print("\n  nothing red found — already stripped")
        return 0
    if not args.write:
        print("\nNothing written. Re-run with --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
