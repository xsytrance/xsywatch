#!/usr/bin/env python3
"""Procedural window layers for the MERIDIAN PRO line.

WHAT THIS REPLACES, AND WHY IT MATTERS

The five existing faces draw their window as ONE generated picture — sky,
ground, aircraft symbol and pitch ladder all baked into a single image. Two
things follow from that, and both are why PRO exists:

  THE HORIZON CANNOT BANK. On a real attitude indicator the aircraft symbol
  is fixed to the airframe and the world rotates behind it. Rolling a single
  baked image swings the aeroplane and leaves the world level — the
  instrument read backwards. It was tried; high-pass separation of the
  furniture from the scene is not reliable enough to ship.

  EVERY WEATHER STATE COSTS A GENERATION. Seventeen states across four faces
  is 68 images, each an AI generation, each adding to the provenance debt
  that already blocks this collection from shipping.

Building the window from layers fixes both at once. The world becomes two
sprites that rotate together, so the horizon banks and the furniture — drawn
afterwards, never moved — stays put. And weather stops being pictures: it
becomes a tint on a sky, an alpha on a cloud bank, and a choice of
precipitation tile. Everything here is seeded arithmetic, so the window is
ORIGINAL BY CONSTRUCTION and carries no generated-art debt.

THE LAYER STACK, bottom to top

    sky        gradient, upper half. Rotates with roll.
    ground     gradient + horizon highlight, lower half. Rotates with roll.
    stars      night only, rotates with the world
    sun/moon   disc, placed by time of day, counter-parallaxes
    cloud far  slow scroll, small parallax
    cloud near faster scroll, larger parallax
    precip     scrolling tile — rain, snow, storm
    flash      lightning, storm only
    glass      droplets and frost. Counter-moves: it is ON the canopy, so it
               must NOT parallax with the view behind it.
    surround   the plate with the window punched out — the only mask WFF has
    furniture  aircraft symbol and pitch ladder. Fixed. Drawn last.

WHY SKY AND GROUND ARE SEPARATE SPRITES

Both are drawn WHITE, so that a single `tintColor` on each gives any weather
mood without a second asset. tintColor takes a literal hex or a bare source
token — it is NOT an arithmetic expression — so the colour is chosen per
state by a Condition branch rather than computed continuously. That is the
plan's own stated fallback and it costs nothing visible: a sky that steps
between twelve well-chosen colours does not read as stepped.

SIZING

Every world layer is drawn at WORLD px square, which is the window diagonal
plus the parallax travel. A layer that rotates must be at least its own
diagonal or the corners sweep into view; a layer that also shifts must carry
that travel too. Getting this wrong shows up as a black wedge at the window
edge on hard tilt, which is the most visible failure available.

Usage:
    python3 tools/make_pro_window.py --face commodore
    python3 tools/make_pro_window.py --face commodore --sheet   # contact sheet
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_weather_overlays import FACES as WX_FACES  # noqa: E402

SS = 3                      # supersample for everything drawn with primitives
SEED = 0x4D45524944          # "MERID", so every run is reproducible


def cfg(face: str) -> dict:
    """Window geometry, taken from the face that already exists rather than
    restated. Two copies of this drifted apart once already."""
    c = WX_FACES[face]
    (ox, oy), (bw, bh) = c["origin"], c["box"]
    return {
        "prefix": c["prefix"],
        "origin": (ox, oy),
        "box": (bw, bh),
        "centre": (ox + bw / 2.0, oy + bh / 2.0),
        "roll": c["roll"],
        "gyro": c["gyro"],
    }


def world_size(face: str) -> int:
    """Square side for any layer that rotates AND parallaxes."""
    c = cfg(face)
    bw, bh = c["box"]
    diag = math.hypot(bw, bh)
    travel = 2 * (c["gyro"] + PARALLAX_MAX)
    return int(math.ceil(diag + travel + 8))


PARALLAX_MAX = 14           # the largest per-layer parallax gain, in px


# ---------------------------------------------------------------------
# the world
# ---------------------------------------------------------------------

def sky(size: int) -> Image.Image:
    """Upper half, white, graded dark at the zenith so a flat tint still
    reads as a sky rather than a wash. Lower half transparent — the ground
    is its own sprite so the two can be tinted independently."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    horizon = S // 2
    for y in range(horizon):
        # 1.0 at the horizon, 0.55 at the zenith: real skies are darker
        # overhead, and that gradient is most of what sells it.
        t = y / max(1, horizon - 1)
        v = int(255 * (0.42 + 0.58 * t))
        for x in range(S):
            px[x, y] = (v, v, v, 255)
    return img.resize((size, size), Image.LANCZOS)


def ground(size: int) -> Image.Image:
    """Lower half, white, with a bright horizon edge. The edge is what the
    eye actually tracks when the world banks, so it is drawn explicitly
    rather than left to the tint boundary."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    horizon = S // 2
    for y in range(horizon, S):
        t = (y - horizon) / max(1, S - horizon - 1)
        # darkest at the bottom: ground falls away from the light
        v = int(255 * (1.0 - 0.62 * t))
        for x in range(S):
            px[x, y] = (v, v, v, 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, horizon - SS // 2, S, horizon + SS // 2],
                fill=(255, 255, 255, 210))
    return img.resize((size, size), Image.LANCZOS)


def stars(size: int) -> Image.Image:
    """Rotates with the world, so it is drawn over the full square."""
    rng = random.Random(SEED ^ 0x57A45)
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(150):
        x, y = rng.uniform(0, S), rng.uniform(0, S * 0.55)
        r = rng.choice([1, 1, 1, 2, 2, 3]) * SS * 0.5
        a = rng.randint(90, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    return img.resize((size, size), Image.LANCZOS)


def disc(size: int, win: int, glow: bool) -> Image.Image:
    """The sun, with a soft corona.

    Sized to the WINDOW, not to this world-sized sprite. Drawn at world scale
    it came out larger than the aperture itself and bleached the whole view —
    a sun that fills the sky is not a sun, it is a fog.
    """
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, r = S / 2.0, win * SS * 0.105
    if glow:
        for i in range(14, 0, -1):
            rr = r * (1 + i * 0.16)
            a = int(70 * (1 - i / 14.0) ** 2)
            d.ellipse([c - rr, c - rr, c + rr, c + rr],
                      fill=(255, 255, 255, a))
    d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, 255))
    return img.resize((size, size), Image.LANCZOS)


def moon(size: int, win: int) -> Image.Image:
    """A gibbous moon: the disc with a second disc subtracted from one side.
    MOON_PHASE_POSITION exists as a source and nothing in the collection uses
    it, but a per-phase sprite set is eight more assets — so the phase is
    baked at roughly three-quarters, which is what a moon looks like most
    nights, and the source is left for a later pass."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, r = S / 2.0, win * SS * 0.088
    d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, 255))
    cut = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(cut).ellipse([c - r * 1.55, c - r, c + r * 0.45, c + r],
                                fill=(255, 255, 255, 255))
    img.putalpha(ImageChops.subtract(img.getchannel("A"),
                                     cut.getchannel("A")))
    return img.resize((size, size), Image.LANCZOS)


def cloud_band(size: int, scale: float, cover: float, seed: int
               ) -> Image.Image:
    """A horizontally TILING band of soft cloud.

    Tiling matters: the layer scrolls by exactly its own width and wraps, so
    the left and right edges have to match or a seam crosses the window once
    a cycle. Blobs that overrun one edge are drawn again at the other.
    """
    rng = random.Random(seed)
    W, H = size * 2 * SS, size * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    n = int(46 * cover)
    for _ in range(n):
        cx = rng.uniform(0, W)
        cy = rng.uniform(H * 0.12, H * 0.52)
        rx = rng.uniform(0.16, 0.42) * size * SS * scale
        ry = rx * rng.uniform(0.34, 0.55)
        a = rng.randint(120, 235)
        for dx in (0, -W, W):          # wrap, so the tile is seamless
            if -rx < cx + dx < W + rx:
                d.ellipse([cx + dx - rx, cy - ry, cx + dx + rx, cy + ry],
                          fill=(255, 255, 255, a))
    img = img.filter(ImageFilter.GaussianBlur(size * SS * 0.035))
    return img.resize((size * 2, size), Image.LANCZOS)


# ---------------------------------------------------------------------
# on the glass, not in the world
# ---------------------------------------------------------------------

def droplets(size: int) -> Image.Image:
    """Rain on the canopy. These sit on the glass, so in the face they
    counter-move against the view rather than parallaxing with it."""
    rng = random.Random(SEED ^ 0xD40)
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(60):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        r = rng.uniform(0.008, 0.022) * S
        d.ellipse([x - r, y - r * 1.25, x + r, y + r * 1.25],
                  fill=(255, 255, 255, rng.randint(38, 92)))
        # the bright bead on the lit side is what makes it read as water
        d.ellipse([x - r * 0.35, y - r * 0.75, x + r * 0.1, y - r * 0.2],
                  fill=(255, 255, 255, 180))
    return img.resize((size, size), Image.LANCZOS)


def frost(size: int) -> Image.Image:
    """Creeps in from the edge, so the centre stays readable however cold it
    gets. Radial falloff, needles drawn inward from the rim."""
    rng = random.Random(SEED ^ 0xF205)
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2.0
    for _ in range(220):
        a = rng.uniform(0, math.tau)
        r0 = c * rng.uniform(0.72, 1.0)
        ln = c * rng.uniform(0.06, 0.26)
        x0, y0 = c + math.cos(a) * r0, c + math.sin(a) * r0
        x1, y1 = c + math.cos(a) * (r0 - ln), c + math.sin(a) * (r0 - ln)
        d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255,
                                           rng.randint(40, 130)),
               width=int(SS * rng.uniform(0.6, 1.8)))
    img = img.filter(ImageFilter.GaussianBlur(S * 0.006))
    # vignette so nothing bright survives in the middle
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    for i in range(40):
        t = i / 39.0
        rr = c * (0.55 + 0.45 * t)
        md.ellipse([c - rr, c - rr, c + rr, c + rr], outline=int(255 * t),
                   width=int(c * 0.02) + SS)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    return img.resize((size, size), Image.LANCZOS)


def furniture(size: int, win: int) -> Image.Image:
    """Aircraft symbol and pitch ladder. NEVER MOVES — this is the whole
    point of the exercise. Drawn last, over everything, fixed to the dial,
    so the world banks behind it the way a real attitude indicator reads."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2.0
    amber = (255, 186, 72, 255)

    # Scaled to the WINDOW, not to this sprite. The sprite is world-sized so
    # it can share a placement with the layers beneath, but an instrument
    # symbol sized to the world would sit lost in the middle of the aperture.
    W = win * SS

    # pitch ladder: short rungs above and below centre, longer at 10 deg
    for i in (-2, -1, 1, 2):
        y = c + i * W * 0.135
        half = W * (0.130 if abs(i) == 2 else 0.084)
        d.line([(c - half, y), (c + half, y)], fill=(236, 240, 245, 225),
               width=max(1, int(SS * 1.6)))

    # the aircraft: two wings and a centre dot, the standard symbol
    w, g = W * 0.31, W * 0.055
    lw = max(1, int(SS * 3.4))
    for x0, x1 in ((c - w, c - g), (c + g, c + w)):
        d.line([(x0, c), (x1, c)], fill=amber, width=lw)
    for x in (c - g, c + g):
        d.line([(x, c), (x, c + W * 0.048)], fill=amber, width=lw)
    r = SS * 2.6
    d.ellipse([c - r, c - r, c + r, c + r], fill=amber)
    return img.resize((size, size), Image.LANCZOS)


def surround(face: str) -> Image.Image:
    """The plate with the window punched out. WFF has no mask primitive —
    occlusion is the only mask — so everything above is cropped by putting
    this on top of it.

    The hole is the alpha of the face's OWN existing window layer, so the
    aperture and the plate cannot drift apart.
    """
    c = cfg(face)
    src = REPO / f"watchfaces/{face}/app/src/main/res/drawable"
    plate = Image.open(src / f"{c['prefix']}_dial.png").convert("RGBA")
    win = Image.open(src / f"{c['prefix']}_wx_clear.png").convert("RGBA")
    hole = win.getchannel("A")
    # erode a little so the surround overlaps the window edge rather than
    # leaving a seam — a bright line on a dark dial is the worst failure.
    hole = hole.filter(ImageFilter.MaxFilter(5))
    out = plate.copy()
    out.putalpha(ImageChops.invert(hole))
    return out


LAYERS = {
    "sky": lambda n, f: sky(n),
    "ground": lambda n, f: ground(n),
    "stars": lambda n, f: stars(n),
    "sun": lambda n, f: disc(n, min(cfg(f)["box"]), True),
    "moon": lambda n, f: moon(n, min(cfg(f)["box"])),
    "cloud_far": lambda n, f: cloud_band(n, 1.35, 0.75, SEED ^ 0xFA4),
    "cloud_near": lambda n, f: cloud_band(n, 0.85, 1.0, SEED ^ 0x4EA5),
    "glass": lambda n, f: droplets(n),
    "frost": lambda n, f: frost(n),
    "furn": lambda n, f: furniture(n, min(cfg(f)["box"])),
}


def build(face: str, out: Path) -> dict[str, tuple[int, int]]:
    n = world_size(face)
    out.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for name, fn in LAYERS.items():
        img = fn(n, face)
        img.save(out / f"pw_{name}.png", optimize=True)
        sizes[name] = img.size
    s = surround(face)
    s.save(out / "pw_surround.png", optimize=True)
    sizes["surround"] = s.size
    return sizes


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--face", default="commodore", choices=list(WX_FACES))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    out = Path(a.out) if a.out else (
        REPO / f"watchfaces/{a.face}-pro/app/src/main/res/drawable")
    sizes = build(a.face, out)
    c = cfg(a.face)
    print(f"  window {c['box']} at {c['origin']}, centre {c['centre']}, "
          f"world {world_size(a.face)}px")
    for k, v in sizes.items():
        print(f"    pw_{k:<10} {v[0]}x{v[1]}")
    print(f"  -> {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
