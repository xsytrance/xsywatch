#!/usr/bin/env python3
"""Cut the clip sprites that keep animated weather inside its window.

WFF HAS NO MASK PRIMITIVE for a PartImage — occlusion is the only mask. A
layer is confined by putting something opaque on top of it with a hole in the
right place, and this tool cuts those holes.

TWO ARCHITECTURES, BECAUSE THE COLLECTION HAS TWO
    HAYATE's plate carries a real aperture: its window is a hole through the
    dial and its viewfinder sits *below*, so the plate already crops anything
    in the field box and nothing here is needed.

    BALSA, COMMODORE and PURE draw their window as a layer *over* an opaque
    plate — dial mode RGB, no alpha channel at all, the window painted black
    beneath. Nothing above them crops anything, so scrolling rain would run
    out across the dial. This emits a surround: a small tile of the plate with
    the window silhouette punched out of it, to sit above the weather.

WHERE THE SILHOUETTE COMES FROM
    Not measured by hand and not guessed — it is the alpha channel of the
    face's own wx layer, which is by definition exactly the region the window
    occupies. Deriving it means the hole and the window cannot drift apart.

    It is then eroded a little so the surround overlaps the window edge by a
    pixel or two. Erring the other way leaves a bright seam between the two
    layers, which on a dark dial is the most visible failure available.

WHY THE INSTRUMENT DOES NOT TILT ON THESE THREE
    Their scenes have the aircraft symbol and pitch ladder baked into the same
    image as the sky and ground. On a real attitude indicator the symbol is
    fixed to the airframe and the horizon moves behind it, so tilting that
    image as one layer would swing the aeroplane instead of the world — the
    instrument read backwards. Until the scenes are regenerated with the
    furniture on its own layer, the scene stays put and the weather over the
    glass carries the wrist response.

Usage:
    python3 tools/make_window_clips.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

REPO = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_weather_overlays import FACES as OVERLAY_FACES, swept  # noqa: E402

# THE CLIP COVERS THE PART'S WHOLE TRAVEL, NOT THE WINDOW. That geometry is
# owned by make_weather_overlays.swept() and imported rather than restated —
# two copies of it drifted apart once already, and the failure mode is rain
# falling across the entire dial.
FACES = {k: v for k, v in OVERLAY_FACES.items()
         if not v.get("aperture") and not v.get("radar_only")}

ERODE_PX = 2


def _drawable(face: str) -> Path:
    return REPO / "watchfaces" / face / "app/src/main/res/drawable"


def window_mask(face: str, prefix: str) -> Image.Image:
    """The union of every weather scene's alpha — the window, exactly.

    Union rather than any single scene: the conditions were generated
    separately and a snow dome that sits one pixel proud of the clear one
    would otherwise poke out from behind the surround.
    """
    d = _drawable(face)
    acc = None
    for scene in ("clear", "overcast", "rain", "snow", "night"):
        p = d / f"{prefix}_wx_{scene}.png"
        if not p.exists():
            continue
        a = Image.open(p).convert("RGBA").getchannel("A")
        acc = a if acc is None else ImageChops.lighter(acc, a)
    if acc is None:
        raise FileNotFoundError(f"{face}: no {prefix}_wx_*.png to derive a "
                                f"window silhouette from")
    solid = acc.point(lambda v: 255 if v > 24 else 0)
    # Erode: shrink the hole so the surround laps over the window edge.
    return solid.filter(ImageFilter.MinFilter(ERODE_PX * 2 + 1))


def build_face(face: str) -> tuple[str, int]:
    cfg = FACES[face]
    prefix = cfg["prefix"]
    cx, cy, bw, bh = swept(face)
    d = _drawable(face)

    plate = Image.open(d / f"{prefix}_dial.png").convert("RGBA")
    mask = window_mask(face, prefix)

    # Everything outside the window keeps the plate; inside it goes clear.
    clip = plate.copy()
    clip.putalpha(ImageChops.invert(mask))
    clip = clip.crop((cx, cy, cx + bw, cy + bh))

    out = d / f"{prefix}_wx_clip.png"
    clip.save(out, optimize=True)

    # A surround that covers everything is a surround that hides the window.
    # Guards against the silhouette missing the box entirely, which would
    # yield a solid surround that hides the window it exists to frame. The
    # bar is low on purpose: the swept box is clamped at the dial edge, so the
    # hole's share of it varies with how near the bottom the window sits.
    alpha = clip.getchannel("A")
    hole = sum(n for v, n in enumerate(alpha.histogram()) if v < 8)
    if hole < (bw * bh) * 0.06:
        raise ValueError(
            f"{face}: clip sprite is {100 * hole / (bw * bh):.1f}% open — the "
            f"window silhouette did not land inside the overlay box at "
            f"{cfg['origin']}. Check origin/box against make_weather_overlays.")
    return out.name, out.stat().st_size, (cx, cy, bw, bh)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--face", choices=sorted(FACES))
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)
    if not args.face and not args.all:
        ap.error("pass --face <name> or --all")

    for f in (sorted(FACES) if args.all else [args.face]):
        name, size, geo = build_face(f)
        print(f"  {f:10s} {name:18s} {size / 1024:6.1f} KB   "
              f"place at x={geo[0]} y={geo[1]} {geo[2]}x{geo[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
