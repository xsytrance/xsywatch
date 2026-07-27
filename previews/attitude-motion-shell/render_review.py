#!/usr/bin/env python3
"""Committed review pixels for the ATTITUDE motion-preview shell.

PREVIEW ONLY. These renders exist so the owner and ChatGPT can see actual
pixels before any APK is sent. Hashes are not approval.

    python3 previews/attitude-motion-shell/render_review.py
    python3 previews/attitude-motion-shell/render_review.py --check

The renders compose the SAME generated resources the watch face loads —
horizon, plate, aperture, datum — so they depict the real layering rather
than a separate drawing. Only the text is drawn here rather than by the
watch: the face uses WFF's `sans-serif` at runtime, and these previews use
DejaVu Sans (free licence, already on the build host) to stand in for it.
The glyph shapes will differ slightly from the device's system font; the
layout, size and hierarchy will not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
REVIEW = HERE / "review"
MANIFEST = REVIEW / "REVIEW_MANIFEST.json"

sys.path.insert(0, str(HERE))
import generate_preview as gp  # noqa: E402

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
FONT_NOTE = ("DejaVu Sans (free licence) stands in for the device's "
             "sans-serif at render time; the face itself uses WFF's "
             "standard system family")

SIZE = gp.SIZE
AP = gp.AP


def font(px: int):
    from PIL import ImageFont
    for c in FONT_CANDIDATES:
        if Path(c).exists():
            return ImageFont.truetype(c, px)
    return ImageFont.load_default()


def centred(d, cx, y, text, px, colour):
    f = font(px)
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=colour)


def compose(profile: str, roll_wrist=0.0, pitch_wrist=0.0, aod=False,
            clock="10:09"):
    """Layer exactly as the WFF scene does: horizon, then plate, then text."""
    from PIL import Image, ImageDraw

    res = HERE / "app/src/main/res/drawable-nodpi"
    horizon_p = res / ("horizon_aod.png" if aod else "horizon.png")
    plate_p = res / ("plate_aod.png" if aod else "plate.png")
    if not horizon_p.exists() or not plate_p.exists():
        raise SystemExit("ERROR resources missing; run generate_preview.py")

    img = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))

    roll = 0.0 if aod else gp.evaluate_roll(profile, roll_wrist)
    pitch = 0.0 if aod else gp.evaluate_pitch(profile, pitch_wrist)

    with Image.open(horizon_p) as h:
        field = h.convert("RGBA").rotate(roll, resample=Image.BICUBIC,
                                         expand=False)
    ox = int(AP["cx"] - field.width / 2)
    oy = int(AP["cy"] - field.height / 2 + pitch)
    img.paste(field, (ox, oy), field)

    with Image.open(plate_p) as pl:
        plate = pl.convert("RGBA")
    img.paste(plate, (0, 0), plate)

    d = ImageDraw.Draw(img)
    if aod:
        centred(d, SIZE / 2, 100, clock, 46, (168, 174, 180))
        centred(d, SIZE / 2, 356, profile.upper(), 22, (150, 122, 74))
    else:
        centred(d, SIZE / 2, 100, clock, 46, (226, 230, 234))
        centred(d, SIZE / 2, 160, "ATTITUDE", 14, (108, 117, 126))
        centred(d, SIZE / 2, 356, profile.upper(), 22, (214, 168, 92))
        centred(d, SIZE / 2, 390, "MOTION PREVIEW", 13, (120, 130, 139))
    return img


def label_strip(width: int, text: str, px=17, colour=(226, 230, 234)):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, px + 14), (10, 11, 12))
    centred(ImageDraw.Draw(img), width / 2, 4, text, px, colour)
    return img


def comparison(aod: bool):
    from PIL import Image, ImageDraw
    names = ["damped", "proposed", "assertive"]
    pad = 16
    W = pad + len(names) * (SIZE + pad)
    H = 58 + SIZE + 46
    sheet = Image.new("RGB", (W, H), (10, 11, 12))
    d = ImageDraw.Draw(sheet)
    centred(d, W / 2, 18,
            "ATTITUDE MOTION PREVIEW — " + ("AOD" if aod else "NORMAL MODE"),
            20, (226, 230, 234))
    for i, n in enumerate(names):
        sheet.paste(compose(n, aod=aod), (pad + i * (SIZE + pad), 58))
        centred(d, pad + i * (SIZE + pad) + SIZE / 2, 58 + SIZE + 10,
                n.upper(), 17, (214, 168, 92))
    centred(d, W / 2, H - 18,
            "identical except the profile label — motion differs, not the "
            "shell", 13, (120, 130, 139))
    return sheet


def motion_states(profile="proposed"):
    from PIL import Image, ImageDraw
    states = [
        ("neutral", 0, 0),
        ("roll left", -45, 0),
        ("roll right", 45, 0),
        ("pitch up", 0, 40),
        ("pitch down", 0, -40),
        ("extreme +", 45, 40),
    ]
    cell, pad, cols = 300, 16, 3
    rows = 2
    W = pad + cols * (cell + pad)
    H = 58 + rows * (cell + 40) + 30
    sheet = Image.new("RGB", (W, H), (10, 11, 12))
    d = ImageDraw.Draw(sheet)
    centred(d, W / 2, 18, f"MOTION STATES — {profile.upper()}", 20,
            (226, 230, 234))
    from PIL import Image as _I
    for i, (title, r, p) in enumerate(states):
        frame = compose(profile, roll_wrist=r, pitch_wrist=p).resize(
            (cell, cell), _I.LANCZOS)
        c, row = i % cols, i // cols
        x = pad + c * (cell + pad)
        y = 58 + row * (cell + 40)
        sheet.paste(frame, (x, y))
        centred(d, x + cell / 2, y + cell + 12, title.upper(), 14,
                (200, 206, 212))
    spec = gp.PROFILES[profile]
    centred(d, W / 2, H - 20,
            f"displayed roll ±{spec['roll_deg']:g}°   "
            f"pitch ±{spec['pitch_px']:g}px   fixed datum stays put, "
            f"horizon moves beneath it", 13, (120, 130, 139))
    return sheet


SHEETS = [
    ("NORMAL_DAMPED.png", lambda: compose("damped")),
    ("NORMAL_PROPOSED.png", lambda: compose("proposed")),
    ("NORMAL_ASSERTIVE.png", lambda: compose("assertive")),
    ("AOD_DAMPED.png", lambda: compose("damped", aod=True)),
    ("AOD_PROPOSED.png", lambda: compose("proposed", aod=True)),
    ("AOD_ASSERTIVE.png", lambda: compose("assertive", aod=True)),
    ("NORMAL_COMPARISON.png", lambda: comparison(False)),
    ("AOD_COMPARISON.png", lambda: comparison(True)),
    ("MOTION_STATES_PROPOSED.png", lambda: motion_states("proposed")),
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, fn in SHEETS:
        img = fn()
        p = out_dir / name
        img.save(p)
        records.append({"image": name, "path": str(p.relative_to(REPO))
                        if p.is_relative_to(REPO) else str(p),
                        "width_px": img.width, "height_px": img.height,
                        "sha256": sha256(p), "bytes": p.stat().st_size})
    res = HERE / "app/src/main/res/drawable-nodpi"
    return {
        "schema": "xsywatch.attitude-motion-preview-review/1",
        "PREVIEW_ONLY": True,
        "OWNER_PIXEL_APPROVED": False,
        "approval_note": ("Hashes are not approval. The owner and ChatGPT "
                          "must look at the actual pixels."),
        "generator": "previews/attitude-motion-shell/render_review.py",
        "render_font_note": FONT_NOTE,
        "layer_note": ("composed from the SAME generated resources the "
                       "watch face loads, so the layering is real; only "
                       "text is drawn here rather than by WFF"),
        "source_resources": {
            p.name: sha256(p) for p in sorted(res.glob("*.png"))},
        "image_count": len(records),
        "images": sorted(records, key=lambda r: r["image"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        if not MANIFEST.exists():
            print("ERROR no committed REVIEW_MANIFEST.json", file=sys.stderr)
            return 1
        committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
        bad = 0
        for rec in committed["images"]:
            p = REPO / rec["path"]
            if not p.exists():
                print(f"MISSING {rec['path']}")
                bad += 1
                continue
            if sha256(p) != rec["sha256"]:
                print(f"DRIFT   {rec['path']}")
                bad += 1
        if bad:
            return 1
        print(f"OK: all {len(committed['images'])} review images match")
        return 0

    man = build(REVIEW)
    MANIFEST.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    for r in man["images"]:
        print(f"  {r['image']:28s} {r['width_px']}x{r['height_px']:<5} "
              f"{r['bytes']:>8,} B  {r['sha256'][:16]}…")
    print(f"wrote {MANIFEST.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
