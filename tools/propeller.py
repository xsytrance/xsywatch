"""Propeller-blade sprites, shared by every face that flies.

One parameterized implementation per blade family, importable by any face
tool — no face may keep a private copy (the owner's call, 2026-07-30:
"make every propeller reusable").

Families:
  point_blade     — MERIDIAN PRO's dauphine-propeller: narrow at the hub,
                    swelling wide through the middle, a POINT at 0.86L,
                    thin gold needle beyond. The exact v5 math, moved here.
  turboprop_blade — the long slender blade of a modern turboprop, per the
                    owner's reference photo: near-constant chord, gentle
                    scimitar sweep, rounded-square tip carrying warning
                    stripes that double as lume.

Blades draw pointing at 12 o'clock on the caller's supersampled canvas,
centred on `centre`; WFF rotates them at runtime, previews at paste time.

colors keys: gold, gold_hi, lume, fill (blade lacquer), stripe (tip bands;
turboprop only). All are RGB tuples from the calling face's palette.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw


def _shade(img, fn):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


def point_blade(img, centre, length, max_w, ss, colors,
                counter_l=26.0, lume_w=3.8):
    """PRO's blade, byte-for-byte: gold rim, lacquer core, wide lume
    spine, needle-and-arrow tip beyond the point."""
    cx, cy = centre
    d = ImageDraw.Draw(img)
    L = length * ss
    W = max_w * ss

    def profile(tt):          # width along the blade
        if tt < 0.45:
            return W * (0.35 + 0.65 * (tt / 0.45) ** 0.8)
        if tt < 0.86:
            return W * (1.0 - 0.98 * ((tt - 0.45) / 0.41) ** 1.15)
        return W * 0.02

    n = 26
    left, right = [], []
    for i in range(n + 1):
        tt = i / n
        y = cy - L * tt
        w2 = profile(tt) / 2 if tt < 0.995 else 0.5
        left.append((cx - w2, y)); right.append((cx + w2, y))
    body = left + right[::-1]
    for off, a in ((3 * ss, 60), (1.5 * ss, 90)):
        _shade(img, lambda dd, off=off, a=a: dd.polygon(
            [(x + off, y + off) for x, y in body], fill=(0, 0, 0, a)))
    # counter-blade
    cb = counter_l * ss
    d.polygon([(cx - W * 0.28, cy), (cx, cy + cb), (cx + W * 0.28, cy)],
              fill=(*colors["gold"], 255))
    d.polygon(body, fill=(*colors["gold"], 255))
    inner = []
    for i in range(n + 1):
        tt = i / n
        y = cy - L * tt
        w2 = max(0.5, profile(tt) / 2 - 4.0 * ss)
        inner.append((cx - w2, y))
    for i in range(n, -1, -1):
        tt = i / n
        y = cy - L * tt
        w2 = max(0.5, profile(tt) / 2 - 4.0 * ss)
        inner.append((cx + w2, y))
    d.polygon(inner, fill=(*colors["fill"], 255))
    # the gold needle tip beyond the blade point
    d.line([(cx, cy - L * 0.84), (cx, cy - L * 1.06)],
           fill=(*colors["gold"], 255), width=int(3 * ss))
    d.polygon([(cx, cy - L * 1.10), (cx - 2.5 * ss, cy - L * 1.04),
               (cx + 2.5 * ss, cy - L * 1.04)], fill=(*colors["gold_hi"], 255))
    # wide lume spine
    lw = lume_w * ss
    d.rounded_rectangle([cx - lw, cy - L * 0.80, cx + lw,
                         cy - L * 0.30], radius=3 * ss,
                        fill=(*colors["lume"], 255))
    d.line([(cx, cy - L * 0.28), (cx, cy + cb * 0.6)],
           fill=(255, 255, 255, 55), width=ss)
    return img


def turboprop_blade(img, centre, length, max_w, ss, colors,
                    counter_l=0.0, spine_w=3.2):
    """The reference blade: slender, near-constant chord, a gentle
    scimitar sweep, rounded-square tip. The tip is a lume band crossed by
    two stripes in the face's signal colour — the aviation warning tip,
    doubling as the night read."""
    cx, cy = centre
    d = ImageDraw.Draw(img)
    L = length * ss
    W = max_w * ss

    def half(tt):             # half-chord along the blade
        if tt < 0.22:
            w = 0.46 + 0.54 * (tt / 0.22) ** 0.9
        elif tt < 0.72:
            w = 1.0
        else:
            w = 1.0 - 0.26 * ((tt - 0.72) / 0.28) ** 1.4
        if tt > 0.96:         # rounded-square tip cap
            w *= math.sqrt(max(0.0, 1.0 - ((tt - 0.96) / 0.04) ** 2))
        return W / 2 * w

    def sway(tt):             # scimitar sweep, subtle
        return W * 0.16 * tt * tt

    n = 40

    def outline(inset=0.0, t0=0.0, t1=1.0):
        left, right = [], []
        for i in range(n + 1):
            tt = t0 + (t1 - t0) * i / n
            y = cy - L * tt
            xo = sway(tt)
            w2 = max(0.5, half(tt) - inset)
            left.append((cx + xo - w2, y))
            right.append((cx + xo + w2, y))
        return left + right[::-1]

    body = outline()
    for off, a in ((3 * ss, 60), (1.5 * ss, 90)):
        _shade(img, lambda dd, off=off, a=a: dd.polygon(
            [(x + off, y + off) for x, y in body], fill=(0, 0, 0, a)))
    # root counterweight, a short tapered paddle behind the boss
    if counter_l:
        cb = counter_l * ss
        d.polygon([(cx - W * 0.30, cy), (cx - W * 0.16, cy + cb),
                   (cx + W * 0.16, cy + cb), (cx + W * 0.30, cy)],
                  fill=(*colors["gold"], 255))
        d.polygon([(cx - W * 0.21, cy), (cx - W * 0.09, cy + cb - 3 * ss),
                   (cx + W * 0.09, cy + cb - 3 * ss), (cx + W * 0.21, cy)],
                  fill=(*colors["fill"], 255))
    d.polygon(body, fill=(*colors["gold"], 255))
    d.polygon(outline(inset=3.0 * ss), fill=(*colors["fill"], 255))
    # the warning tip: lume band with two signal stripes
    d.polygon(outline(inset=3.0 * ss, t0=0.815, t1=1.0),
              fill=(*colors["lume"], 255))
    for s0, s1 in ((0.845, 0.885), (0.925, 0.965)):
        d.polygon(outline(inset=3.0 * ss, t0=s0, t1=s1),
                  fill=(*colors["stripe"], 255))
    # slim lume spine for the night read, stopping short of the tip band
    sw = spine_w * ss
    d.rounded_rectangle([cx - sw, cy - L * 0.70, cx + sw, cy - L * 0.32],
                        radius=2.5 * ss, fill=(*colors["lume"], 255))
    return img
