#!/usr/bin/env python3
"""Draw the animated weather overlays for the MERIDIAN faces.

These are the moving half of the weather: rain streaks, snow, a drifting
cloud bank, a star field, a lightning flash and radar precipitation returns.
The still half — the photographic scene behind them — is unchanged.

WHY THIS EXISTS AS A DRAWING TOOL AND NOT A KONTEXT PROMPT
    Every plate, hand and weather scene in this collection is AI-generated,
    which is what blocks it shipping under
    docs/reports/AIRCRAFT_WATCH_DISCOVERY.md. Everything this file emits is
    drawn from seeded arithmetic — original by construction — so the animation
    layer carries no provenance debt even where the scene under it still does.

WHY THE TEXTURES TILE
    Precipitation is animated by scrolling one sprite, not by playing frames.
    A frame sequence at 200x200 would cost twenty-odd PNGs per condition per
    face; a scrolling tile costs one, stays smooth at any refresh rate the
    watch decides to throttle to, and composes with the wrist-tilt Gyro on the
    enclosing group.

    The contract with the engine: a texture is periodic over `tile` pixels
    along its scroll axis, and the sprite is exactly `tile` longer than the
    box it fills. Scroll it by exactly `tile` and it returns to where it
    began, so the loop is invisible. Scroll it by anything else and the seam
    shows — which is why expressions.scroll_offset() takes the tile period in
    pixels rather than a speed.

Deterministic: every draw is seeded from (kind, prefix, size), so the same
arguments always produce byte-identical PNGs.

Usage:
    python3 tools/make_weather_overlays.py --face hayate
    python3 tools/make_weather_overlays.py --all
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent

# Per-face overlay geometry. `box` is the scene part's size — overlays share
# it so a single <Gyro> on the enclosing group moves scene and weather
# together. `tile` is the scroll period in pixels.
#
# HOG-WILD is the exception: it has no window. Its six o'clock is a PPI radar
# scope, so its precipitation is drawn as radar returns sized to the scope.
#   HAYATE's window is an aperture cut through the plate, so its overlays live
# below the plate in the 200x200 field box and the aperture crops them for
# free. The other three draw their window *over* an opaque plate, so their
# overlays are clipped by a generated surround sprite instead
# (tools/make_window_clips.py), which imports this table so the two cannot
# drift apart.
#
# HOW BIG A SURROUND HAS TO BE. A scrolling overlay is a sprite one tile
# longer than its box which then travels a whole tile, so it sweeps box + 2
# tiles — not box, and not box + 1 tile. Add the gyro travel on top, since
# wrist tilt shifts the same sprite again. Getting this wrong does not fail
# quietly: rain falls across the whole dial.
#
#   swept = rotated_bbox(box + tile) + 2*gyro   (per axis)
#
# The rotation term matters and is easy to miss: the same Gyro that shifts a
# layer also rolls it, and a rotated rectangle needs a bigger box than an
# upright one. At 6 degrees a 180px sprite grows by nearly 19px on the long
# axis — comfortably enough to push weather past a surround sized for
# translation alone.
#
# `gyro` and `roll` are the maximum wrist response the face may ask for. The
# engine refuses anything larger rather than let weather escape.
FACES = {
    "hayate":    {"prefix": "hy", "box": (200, 200), "tile": 100,
                  "origin": (140, 272), "gyro": 0, "roll": 0,
                  "aperture": True},
    "balsa":     {"prefix": "ba", "box": (140, 140), "tile": 40,
                  "origin": (170, 297), "gyro": 8, "roll": 7},
    "commodore": {"prefix": "cm", "box": (140, 140), "tile": 40,
                  "origin": (170, 293), "gyro": 8, "roll": 7},
    "pure":      {"prefix": "pu", "box": (140, 140), "tile": 40,
                  "origin": (170, 293), "gyro": 8, "roll": 7},
    "hogwild":   {"prefix": "wh", "box": (113, 113), "tile": 0,
                  "origin": (184, 305), "gyro": 6, "roll": 5,
                  "radar_only": True},
}

SAFETY_PX = 6
CANVAS = 480


def swept(face: str) -> tuple[int, int, int, int]:
    """The rectangle an animated overlay can occupy over a full cycle:
    (x, y, width, height). This is what a surround must cover.

    Computed about the window centre, since rotation pivots there.
    """
    c = FACES[face]
    (ox, oy), (bw, bh), t, g = c["origin"], c["box"], c["tile"], c["gyro"]
    cx, cy = ox + bw / 2.0, oy + bh / 2.0
    # Upper bound on any single part: a scroller is one tile longer, and
    # which axis that lands on depends on the overlay, so allow it on both.
    w, h = bw + t, bh + t
    r = math.radians(c["roll"])
    rw = w * math.cos(r) + h * math.sin(r)
    rh = w * math.sin(r) + h * math.cos(r)
    # Scroll travel is one tile, but only ever away from the origin corner;
    # centring the box means half of it counts on each side.
    span_w = rw + t + 2 * g + 2 * SAFETY_PX
    span_h = rh + t + 2 * g + 2 * SAFETY_PX
    x0 = cx - span_w / 2.0
    y0 = cy - span_h / 2.0
    # Clamp to the dial. These windows sit low, so the swept box runs off the
    # bottom edge — and a surround is only ever needed where something could
    # be seen. Off-canvas weather is already invisible, and a part reaching
    # past 480 is rejected by the face validator.
    x1 = min(CANVAS, math.ceil(x0 + span_w))
    y1 = min(CANVAS, math.ceil(y0 + span_h))
    x = max(0, int(math.floor(x0)))
    y = max(0, int(math.floor(y0)))
    return (x, y, int(x1 - x), int(y1 - y))


def _drawable(face: str) -> Path:
    return REPO / "watchfaces" / face / "app/src/main/res/drawable"


def _seeded(kind: str, prefix: str, w: int, h: int) -> random.Random:
    """A generator keyed to exactly what is being drawn, so reruns are
    byte-stable and two faces never receive the same rain."""
    return random.Random(f"meridian/{kind}/{prefix}/{w}x{h}")


def _wrapped(draw_one, rng_shapes, tile: int, axis: str = "y") -> None:
    """Draw each shape three times — at its position and one tile either side
    — so anything crossing the tile boundary appears whole on both edges.

    This is what makes the texture periodic. Drawing once leaves shapes
    clipped at the seam, and a clipped streak is exactly what the eye catches
    when the loop comes round."""
    for shape in rng_shapes:
        for k in (-1, 0, 1):
            draw_one(shape, k * tile if axis == "y" else 0,
                     k * tile if axis == "x" else 0)


def _blur_tiled(tile_img: Image.Image, radius: float,
                axis: str = "y") -> Image.Image:
    """Blur a tile so its two cut edges stay periodic.

    Blurring the finished sprite instead would darken its outermost rows,
    where the kernel has nothing to average against — and those rows are
    exactly the ones the scroll brings round to meet their opposite number.
    The error is only a few alpha levels, but it lands on the seam, which is
    the one place the eye is already looking. So: triple the tile, blur the
    middle where every pixel has real neighbours, and keep that.
    """
    if radius <= 0:
        return tile_img
    tw, th = tile_img.size
    if axis == "y":
        pad = Image.new("RGBA", (tw, th * 3), (0, 0, 0, 0))
        for k in range(3):
            pad.alpha_composite(tile_img, (0, k * th))
        return pad.filter(ImageFilter.GaussianBlur(radius)).crop(
            (0, th, tw, th * 2))
    pad = Image.new("RGBA", (tw * 3, th), (0, 0, 0, 0))
    for k in range(3):
        pad.alpha_composite(tile_img, (k * tw, 0))
    return pad.filter(ImageFilter.GaussianBlur(radius)).crop(
        (tw, 0, tw * 2, th))


def _stack(tile_img: Image.Image, w: int, h: int, axis: str = "y") -> Image.Image:
    """Repeat a tile to fill a w x h sprite."""
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    tw, th = tile_img.size
    if axis == "y":
        for y in range(0, h + th, th):
            out.alpha_composite(tile_img, (0, y))
    else:
        for x in range(0, w + tw, tw):
            out.alpha_composite(tile_img, (x, 0))
    return out.crop((0, 0, w, h))


# ---------------------------------------------------------------------------
# The overlays
# ---------------------------------------------------------------------------

def rain(w: int, h: int, tile: int, prefix: str, heavy: bool = False) -> Image.Image:
    """Near-vertical streaks. Slanted a few degrees so it reads as falling
    through moving air rather than dropping down a lift shaft."""
    rng = _seeded("rain-heavy" if heavy else "rain", prefix, w, h)
    count = int(w * tile / (900 if heavy else 1700))
    tile_img = Image.new("RGBA", (w, tile), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile_img)

    shapes = [(rng.randrange(-w // 4, w), rng.randrange(0, tile),
               rng.uniform(14, 30) * (1.25 if heavy else 1.0),
               rng.uniform(0.55, 1.0)) for _ in range(count)]

    def one(s, dx, dy):
        x, y, length, bright = s
        slant = length * 0.20
        a = int(150 * bright) if heavy else int(110 * bright)
        d.line([(x + dx, y + dy), (x + slant + dx, y + length + dy)],
               fill=(214, 226, 238, a), width=1)

    _wrapped(one, shapes, tile, "y")
    return _stack(_blur_tiled(tile_img, 0.4, "y"), w, h + tile, "y")


def snow(w: int, h: int, tile: int, prefix: str) -> Image.Image:
    """Flakes at three depths. The engine sways the whole layer sideways; the
    depth variation is what stops that sway looking like one rigid sheet."""
    rng = _seeded("snow", prefix, w, h)
    tile_img = Image.new("RGBA", (w, tile), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile_img)

    # Snow has to be dense and small. An earlier pass used ~34 flakes at up to
    # 2.4px across a 200x100 tile and it read as falling confetti: at that
    # size the eye resolves each one as a shape with edges, and a shape with
    # edges is a thing, not weather.
    # Tuned twice. At 2.4px and ~34 per tile it read as confetti — big enough
    # that the eye resolved each flake as a shape. Answering that with density
    # alone (220 per tile) just made a whiteout. Size was the actual fault:
    # small flakes at moderate density read as snow, and the sprite is stacked
    # three deep over the sprite height, so per-tile counts land at roughly
    # three times this in view.
    shapes = []
    for n, rad, alpha in ((int(w * tile / 1400), 1.5, 200),
                          (int(w * tile / 1000), 1.05, 150),
                          (int(w * tile / 700), 0.7, 105)):
        shapes += [(rng.randrange(0, w), rng.randrange(0, tile), rad, alpha)
                   for _ in range(n)]

    def one(s, dx, dy):
        x, y, r, a = s
        d.ellipse([x - r + dx, y - r + dy, x + r + dx, y + r + dy],
                  fill=(248, 250, 255, a))

    _wrapped(one, shapes, tile, "y")
    return _stack(_blur_tiled(tile_img, 0.35, "y"), w, h + tile, "y")


def cloud(w: int, h: int, tile: int, prefix: str) -> Image.Image:
    """A soft bank that drifts sideways. Horizontal tiling, so the sprite is
    wider than the box rather than taller."""
    rng = _seeded("cloud", prefix, w, h)
    tile_img = Image.new("RGBA", (tile, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile_img)

    shapes = [(rng.randrange(0, tile), rng.uniform(0.10, 0.62) * h,
               rng.uniform(18, 46), rng.uniform(0.35, 1.0))
              for _ in range(max(6, tile // 9))]

    def one(s, dx, dy):
        x, y, r, bright = s
        a = int(122 * bright)
        d.ellipse([x - r * 1.7 + dx, y - r * 0.5, x + r * 1.7 + dx, y + r * 0.5],
                  fill=(226, 230, 236, a))

    _wrapped(one, shapes, tile, "x")
    return _stack(_blur_tiled(tile_img, 7.0, "x"), w + tile, h, "x")


def stars(w: int, h: int, tile: int, prefix: str) -> Image.Image:
    """A drifting star field for the night branch. Deliberately sparse — the
    night scene under it already carries most of the light."""
    rng = _seeded("stars", prefix, w, h)
    tile_img = Image.new("RGBA", (w, tile), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile_img)

    shapes = [(rng.randrange(0, w), rng.randrange(0, tile),
               rng.choice((0.6, 0.8, 1.0, 1.4)),
               rng.randrange(90, 236)) for _ in range(max(10, w * tile // 2200))]

    def one(s, dx, dy):
        x, y, r, a = s
        d.ellipse([x - r + dx, y - r + dy, x + r + dx, y + r + dy],
                  fill=(236, 242, 255, a))

    _wrapped(one, shapes, tile, "y")
    return _stack(_blur_tiled(tile_img, 0.3, "y"), w, h + tile, "y")


def flash(w: int, h: int, prefix: str) -> Image.Image:
    """The lightning strike itself: a cold soft wash, brightest at the top.

    No tiling — the engine drives this one on alpha, not position. Keeping it
    formless is deliberate; a drawn fork would have to strike the same place
    every twelve seconds."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(h):
        t = 1.0 - (i / h)
        # The engine already drives this layer's alpha to a spike; a dense
        # sprite on top of that blanks the scene entirely at peak instead of
        # lighting it.
        a = int(148 * (t ** 1.7))
        if a:
            d.line([(0, i), (w, i)], fill=(206, 224, 255, a))
    return img.filter(ImageFilter.GaussianBlur(w / 24.0))


def radar_returns(size: int, prefix: str, heavy: bool = False) -> Image.Image:
    """Precipitation as a PPI radar paints it: cellular returns, brighter at
    the core, confined to the scope circle.

    HOG-WILD has no window to look out of. Showing it weather as radar echo is
    not a workaround for that — it is what the instrument on that dial is for.
    """
    rng = _seeded("radar-heavy" if heavy else "radar", prefix, size, size)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2.0
    usable = c * 0.86

    cells = 7 if heavy else 4
    for _ in range(cells):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(0.12, 0.80) * usable
        cx, cy = c + math.cos(ang) * dist, c + math.sin(ang) * dist
        core = rng.uniform(size * 0.06, size * 0.13) * (1.3 if heavy else 1.0)
        # Three concentric intensities, the way a real scope colours rain rate.
        for r, col in ((core * 2.1, (40, 190, 90, 46)),
                       (core * 1.35, (120, 220, 80, 78)),
                       (core * 0.7, (235, 214, 70, 108) if heavy
                        else (150, 232, 96, 96))):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    img = img.filter(ImageFilter.GaussianBlur(size / 42.0))

    # Clip to the scope. Anything outside the glass is a bug, not weather.
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([c - usable, c - usable, c + usable, c + usable],
                                 fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(size / 60.0))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


# ---------------------------------------------------------------------------

def build_face(face: str, verbose: bool = True) -> list[tuple[str, int]]:
    cfg = FACES[face]
    prefix, out = cfg["prefix"], _drawable(face)
    out.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int]] = []

    def save(name: str, img: Image.Image) -> None:
        p = out / f"{prefix}_{name}.png"
        img.save(p, optimize=True)
        written.append((p.name, p.stat().st_size))

    if cfg.get("radar_only"):
        size = cfg["box"][0]
        save("rdr_light", radar_returns(size, prefix, heavy=False))
        save("rdr_heavy", radar_returns(size, prefix, heavy=True))
    else:
        w, h = cfg["box"]
        tile = cfg["tile"]
        save("ov_rain", rain(w, h, tile, prefix, heavy=False))
        save("ov_storm", rain(w, h, tile, prefix, heavy=True))
        save("ov_snow", snow(w, h, tile, prefix))
        save("ov_cloud", cloud(w, h, tile, prefix))
        save("ov_stars", stars(w, h, tile, prefix))
        save("ov_flash", flash(w, h, prefix))

    if verbose:
        total = sum(s for _, s in written)
        for n, s in written:
            print(f"  {n:22s} {s / 1024:6.1f} KB")
        print(f"  {'':22s} {total / 1024:6.1f} KB total")
    return written


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--face", choices=sorted(FACES))
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)

    if not args.face and not args.all:
        ap.error("pass --face <name> or --all")

    targets = sorted(FACES) if args.all else [args.face]
    grand = 0
    for f in targets:
        print(f"{f}:")
        grand += sum(s for _, s in build_face(f))
    if len(targets) > 1:
        print(f"\n{grand / 1024:.1f} KB across {len(targets)} faces")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
