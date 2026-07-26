#!/usr/bin/env python3
"""Build the private release-candidate presentation packet.

    python3 tools/build_media.py aurelius --version 2.0.0-rc1

Everything is derived from committed bytes — the rc1 reference renders and
the runtime resources — so nothing here is a hand-edited mock-up. Outputs
land in docs/commercial/<face>/<version>/media/ with a checksum manifest.

Play-facing assets follow the requirements the policy audit verified:

  * screenshots — 1:1, at least 384x384, showing ONLY the watch face, with
    no device frame and no added text, graphics or backgrounds
    (WO-G6, checked 2026-07-26);
  * listing icon — the face centred and scaled to touch the asset edges,
    with nothing added that is not part of the watch face (WO-G4).

The on-wrist composition is generated too, but it is written to a
clearly-separated `promotional_not_play/` directory: WO-G6 forbids device
frames in Play screenshots, so that image may only be used as other
promotional media.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import visuallib as V                                # noqa: E402


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(img: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=False)
    return path


def listing_icon(face_img: Image.Image, size: int = 512) -> Image.Image:
    """WO-G4: the watch face centred and scaled to touch the outer edges.

    The reference render is a square canvas with black corners around the
    round display, so the face occupies an inscribed circle. Cropping to
    that circle and scaling it to the full asset makes the face touch the
    edges instead of floating inside dead canvas.
    """
    im = face_img.convert("RGB")
    w, h = im.size
    cx, cy = w / 2.0, h / 2.0

    # The face is octagonal inside a square canvas, so simply taking the
    # square leaves black corners and the face does not touch the edges.
    # Crop to the tightest CENTRED square that still contains every
    # non-background pixel, then scale that to the asset.
    px = im.load()
    bg_max = 12                      # canvas backdrop is #060403
    reach = 0.0
    for y in range(h):
        for x in range(w):
            if max(px[x, y]) > bg_max:
                reach = max(reach, abs(x + 0.5 - cx), abs(y + 0.5 - cy))
    if reach <= 0:
        reach = min(w, h) / 2.0
    r = int(math.ceil(reach))
    box = (int(cx - r), int(cy - r), int(cx + r), int(cy + r))
    box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
    return im.crop(box).resize((size, size), Image.LANCZOS)


def comparison(normal: Image.Image, aod: Image.Image) -> Image.Image:
    pad, cap = 24, 0
    W = pad + 2 * (480 + pad)
    H = pad + 480 + pad + cap
    sheet = Image.new("RGB", (W, H), (10, 10, 12))
    sheet.paste(normal.convert("RGB"), (pad, pad))
    sheet.paste(aod.convert("RGB"), (pad * 2 + 480, pad))
    return sheet


def on_wrist(face_img: Image.Image) -> Image.Image:
    """Device-context composition.

    Deliberately abstract: a dark rounded body and a strap silhouette, no
    photographic materials and no brand hardware. It must not imply the
    watch is made of titanium, sapphire or gold — the face depicts those
    materials, the device does not contain them.
    """
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (16, 16, 18))
    d = ImageDraw.Draw(img)
    cx, cy, r = W // 2, H // 2, 340
    d.rounded_rectangle((cx - 190, 60, cx + 190, H - 60), radius=150,
                        fill=(28, 28, 31))                       # strap
    d.rounded_rectangle((cx - r - 26, cy - r - 26, cx + r + 26, cy + r + 26),
                        radius=120, fill=(40, 41, 44))           # case body
    face = face_img.convert("RGB").resize((2 * r, 2 * r), Image.LANCZOS)
    mask = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    img.paste(face, (cx - r, cy - r), mask)
    return img


def vertical_cut(face_img: Image.Image) -> Image.Image:
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (10, 10, 12))
    size = 900
    face = face_img.convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.paste(face, ((W - size) // 2, (H - size) // 2), mask)
    return img


def motion(face: str, out: Path, seconds: int = 8, fps: int = 15) -> Path:
    """Short motion presentation rendered from the committed resources.

    Frames come from the same deterministic reference renderer as the
    goldens, stepping real time so the gear train, cage, hands and reserve
    needle move exactly as the runtime drives them.
    """
    scene = V.Scene.load(face)
    contract = V.VisualContract.load(face)
    base = contract.state("normal_hero")["raw"]
    tmp = Path(tempfile.mkdtemp())
    try:
        n = seconds * fps
        for i in range(n):
            t = i / fps
            sec = base["second"] + t
            minute = base["minute"] + int(sec // 60)
            name = f"_motion_{i}"
            raw = dict(base)
            raw.update({"second": sec % 60,
                        "millisecond": int((sec % 1) * 1000),
                        "minute": minute % 60})
            contract.raw["states"][name] = raw
            img = V.render_state(scene, contract, name)
            contract.raw["states"].pop(name, None)
            img.convert("RGB").save(tmp / f"f{i:04d}.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
             "-i", str(tmp / "f%04d.png"), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-crf", "18", str(out)],
            check=True)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--version", required=True)
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args()

    vis = REPO / "watchfaces" / args.face / "visual"
    import tomllib
    with open(vis / "states.toml", "rb") as fh:
        g = tomllib.load(fh)["goldens"]
    version = g.get("proposed_version") or g["approved_version"]
    src = vis / ("candidates" if g.get("proposed_version") else "goldens") / version

    normal = Image.open(src / "normal.png")
    aod = Image.open(src / "aod.png")

    root = REPO / "docs/commercial" / args.face / args.version / "media"
    play = root / "play"
    promo = root / "promotional_not_play"
    written: list[Path] = []

    # --- Play-compatible: 1:1, >=384, face only, no frames --------------
    written.append(save(normal.convert("RGB"), play / "screenshot_1_normal.png"))
    written.append(save(aod.convert("RGB"), play / "screenshot_2_aod.png"))
    written.append(save(listing_icon(normal), play / "listing_icon_512.png"))

    # --- presentation ----------------------------------------------------
    written.append(save(normal.convert("RGB").resize((1080, 1080),
                                                     Image.LANCZOS),
                        root / "hero.png"))
    written.append(save(normal.convert("RGB"), root / "normal_480.png"))
    written.append(save(aod.convert("RGB"), root / "aod_480.png"))
    written.append(save(comparison(normal, aod), root / "normal_vs_aod.png"))

    closeups = src / "closeups"
    if closeups.is_dir():
        for name in ("normal_cage", "normal_bridge", "normal_reserve"):
            p = closeups / f"{name}.png"
            if p.exists():
                written.append(save(Image.open(p).convert("RGB"),
                                    root / f"craftsmanship_{name}.png"))

    # --- promotional, explicitly NOT Play screenshots -------------------
    written.append(save(on_wrist(normal), promo / "device_context.png"))
    written.append(save(vertical_cut(normal), promo / "vertical_1080x1920.png"))
    (promo / "README.md").write_text(
        "# Promotional media — NOT Play screenshots\n\n"
        "Wear OS quality requirement WO-G6 forbids device frames and any\n"
        "text, graphics or background that is not part of the app interface\n"
        "in a Play listing screenshot. Everything in this directory shows a\n"
        "device frame or added composition and therefore may **not** be\n"
        "uploaded as a screenshot. Play-compatible assets are in `../play/`.\n\n"
        "`device_context.png` is a deliberately abstract dark body and\n"
        "strap. It is not a photograph of any product and must not be used\n"
        "to imply the watch is made of titanium, sapphire or gold — the\n"
        "watch FACE depicts those materials; the device does not contain\n"
        "them.\n", encoding="utf-8")
    written.append(promo / "README.md")

    if not args.no_video:
        try:
            written.append(motion(args.face, root / "motion_8s.mp4"))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"WARN motion video skipped: {e}")

    manifest = {
        "face": args.face,
        "candidate_version": args.version,
        "visual_version": version,
        "source": ("derived from committed reference renders and runtime "
                   "resources; no hand-edited artwork"),
        "reproduce": (f"python3 tools/build_media.py {args.face} "
                      f"--version {args.version}"),
        "play_requirements": {
            "screenshots": ("WO-G6: 1:1, >=384x384, watch face only, no "
                            "device frames, no added text/graphics/background"),
            "icon": ("WO-G4: face centred and scaled to touch the asset "
                     "edges, nothing added"),
            "checked": "2026-07-26",
            "note": ("exact icon pixel dimensions could not be confirmed "
                     "from an official page; 512x512 is produced as the "
                     "common convention and MUST be confirmed before "
                     "submission — see PHASE_4_POLICY_AUDIT.md MEDIA-1"),
        },
        "files": {str(p.relative_to(root)): sha256(p)
                  for p in sorted(written) if p.is_file()},
    }
    (root / "MEDIA_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(f"{len(manifest['files'])} media files -> {root}")
    for f in sorted(manifest["files"]):
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
