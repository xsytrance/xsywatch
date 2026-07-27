#!/usr/bin/env python3
"""Render MERIDIAN review images from the committed watchface.xml.

    python3 watchfaces/attitude-meridian/tools/render_from_xml.py
    python3 .../render_from_xml.py --check      # determinism, no writes

This deliberately renders from the SHIPPED artefacts — the generated
watchface.xml and the drawables that go into the APK — rather than from the
studio generator. The studio renders show what was designed; these show what
the face actually declares. If the two disagree, the XML is wrong, and that
is exactly the failure a design-side preview cannot catch.

It is an approximation of the device compositor, not a simulator: it honours
z-order, per-layer alpha, ambient variants, pivots, angle/x/y transforms,
and bitmap-font text. It does not model transition timing or antialiasing
differences.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FACE = Path(__file__).resolve().parents[1]
XML = FACE / "app/src/main/res/raw/watchface.xml"
DRAWABLE = FACE / "app/src/main/res/drawable"
REVIEW = FACE / "review"

# Sample environment for the review renders only. Nothing here is compiled
# into the APK; the face binds live sources.
FIXTURE_ENV = {
    "HOUR_0_11": 10, "MINUTE": 9, "SECOND": 30, "MILLISECOND": 0,
    "DAY": 27, "BATTERY_PERCENT": 78, "STEP_COUNT": 8420, "HEART_RATE": 72,
    "ACCELEROMETER_ANGLE_X": 0.0, "ACCELEROMETER_ANGLE_Y": 0.0,
}

SAFE = {"clamp": lambda v, lo, hi: max(lo, min(hi, v)), "sin": math.sin,
        "cos": math.cos, "round": round, "abs": abs, "min": min, "max": max}


def evaluate(expr: str, env: dict) -> float:
    """Evaluate one WFF arithmetic expression under a data environment."""
    def sub(m):
        token = m.group(1)
        if token not in env:
            raise KeyError(f"no value supplied for [{token}]")
        return repr(env[token])
    py = re.sub(r"\[([A-Z_0-9]+)\]", sub, expr)
    if re.search(r"[A-Za-z_]+", py.replace("clamp", "").replace("sin", "")
                 .replace("cos", "").replace("round", "")):
        raise ValueError(f"unresolved name in expression {expr!r}")
    return float(eval(py, {"__builtins__": {}}, SAFE))  # noqa: S307


def tint(img, color: str):
    from PIL import Image
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    solid = Image.new("RGBA", img.size, (r, g, b, 255))
    solid.putalpha(img.getchannel("A"))
    return solid


class Font:
    def __init__(self, root):
        self.families = {}
        for bf in root.iter("BitmapFont"):
            name = bf.get("name")
            if not name:
                continue
            self.families[name] = {
                c.get("name"): (c.get("resource"), int(c.get("width")),
                                int(c.get("height")))
                for c in bf.findall("Character")}

    def render(self, family, text, size, color):
        from PIL import Image
        glyphs = self.families[family]
        height = max(h for _, _, h in glyphs.values())
        scale = size / height
        imgs = []
        for ch in text:
            if ch not in glyphs:
                raise KeyError(f"font {family!r} has no glyph for {ch!r}")
            res, w, h = glyphs[ch]
            with Image.open(DRAWABLE / f"{res}.png") as g:
                g = g.convert("RGBA").resize(
                    (max(1, round(w * scale)), max(1, round(h * scale))),
                    Image.LANCZOS)
            imgs.append(g)
        if not imgs:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        out = Image.new("RGBA", (sum(i.width for i in imgs),
                                 max(i.height for i in imgs)), (0, 0, 0, 0))
        x = 0
        for i in imgs:
            out.alpha_composite(i, (x, 0))
            x += i.width
        return tint(out, color)


def format_template(node, env) -> str:
    """WFF <Template>text %d ...<Parameter/></Template> substitution."""
    text = node.text or ""
    values = [evaluate(p.get("expression"), env)
              for p in node.findall("Parameter")]
    out, vi, i = [], 0, 0
    while i < len(text):
        if text[i] == "%" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == "%":
                out.append("%")
                i += 2
                continue
            if nxt in "ds":
                v = values[vi]
                out.append(str(int(round(v))) if nxt == "d" else str(v))
                vi += 1
                i += 2
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def compose(root, font, env, ambient: bool, skip: set[str] | None = None):
    """`skip` omits named parts — used by the coverage gate to look at the
    horizon and plate alone, without hands crossing the aperture."""
    from PIL import Image
    scene = root.find("Scene")
    bg = scene.get("backgroundColor", "#FF000000")
    canvas = Image.new("RGBA", (int(root.get("width")), int(root.get("height"))),
                       (int(bg[3:5], 16), int(bg[5:7], 16), int(bg[7:9], 16),
                        255))
    for part in scene:
        if skip and part.get("name") in skip:
            continue
        variant = part.find("Variant")
        alpha = int(part.get("alpha", 255))
        if ambient and variant is not None and variant.get("target") == "alpha":
            alpha = int(variant.get("value"))
        if alpha == 0:
            continue
        transforms = {t.get("target"): t.get("value")
                      for t in part.findall("Transform")}
        x = evaluate(transforms["x"], env) if "x" in transforms \
            else float(part.get("x", 0))
        y = evaluate(transforms["y"], env) if "y" in transforms \
            else float(part.get("y", 0))
        w, h = int(part.get("width")), int(part.get("height"))

        if part.tag == "PartImage":
            res = part.find("Image").get("resource")
            with Image.open(DRAWABLE / f"{res}.png") as im:
                layer = im.convert("RGBA")
            if layer.size != (w, h):
                layer = layer.resize((w, h), Image.LANCZOS)
            if "angle" in transforms:
                angle = evaluate(transforms["angle"], env)
                px = float(part.get("pivotX", 0.5)) * w
                py = float(part.get("pivotY", 0.5)) * h
                layer = layer.rotate(-angle, resample=Image.BICUBIC,
                                     center=(px, py))
        elif part.tag == "PartText":
            bf = part.find(".//BitmapFont")
            tmpl = bf.find("Template")
            text = format_template(tmpl, env)
            glyphs = font.render(bf.get("family"), text,
                                 int(bf.get("size")), bf.get("color"))
            layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            align = part.find("Text").get("align", "CENTER")
            gx = {"START": 0, "CENTER": (w - glyphs.width) // 2,
                  "END": w - glyphs.width}[align]
            layer.alpha_composite(glyphs, (max(0, gx),
                                           max(0, (h - glyphs.height) // 2)))
        else:
            continue

        if alpha < 255:
            a = layer.getchannel("A").point(lambda v: v * alpha // 255)
            layer.putalpha(a)
        canvas.alpha_composite(layer, (round(x), round(y)))
    return canvas.convert("RGB")


def label(draw, x, y, text, size, color=(200, 206, 212)):
    from PIL import ImageFont
    for cand in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if Path(cand).exists():
            f = ImageFont.truetype(cand, size)
            break
    else:
        f = ImageFont.load_default()
    w = draw.textlength(text, font=f)
    draw.text((x - w / 2, y), text, font=f, fill=color)


HAND_POSITIONS = [(10, 9, 30), (12, 0, 0), (3, 15, 15), (6, 30, 45),
                  (8, 40, 20)]
MOTION_STATES = [("NEUTRAL", 0, 0), ("ROLL LEFT", -45, 0),
                 ("ROLL RIGHT", 45, 0), ("PITCH UP", 0, 40),
                 ("PITCH DOWN", 0, -40), ("EXTREME", 45, 40)]


def build(root, font):
    from PIL import Image, ImageDraw
    out = {}
    out["MERIDIAN_XML_NORMAL.png"] = compose(root, font, dict(FIXTURE_ENV),
                                             False)
    out["MERIDIAN_XML_AOD.png"] = compose(root, font, dict(FIXTURE_ENV), True)

    cell, pad = 300, 14
    W = pad + len(HAND_POSITIONS) * (cell + pad)
    sheet = Image.new("RGB", (W, 54 + cell + 44), (10, 11, 12))
    d = ImageDraw.Draw(sheet)
    label(d, W / 2, 16, "MERIDIAN — HAND POSITIONS RENDERED FROM watchface.xml",
          19, (222, 227, 232))
    for i, (hh, mm, ss) in enumerate(HAND_POSITIONS):
        env = dict(FIXTURE_ENV, HOUR_0_11=hh % 12, MINUTE=mm, SECOND=ss)
        sheet.paste(compose(root, font, env, False).resize((cell, cell),
                                                           Image.LANCZOS),
                    (pad + i * (cell + pad), 54))
        label(d, pad + i * (cell + pad) + cell / 2, 54 + cell + 12,
              f"{hh:02d}:{mm:02d}", 16, (198, 152, 74))
    out["MERIDIAN_XML_HAND_POSITIONS.png"] = sheet

    cols = 3
    W = pad + cols * (cell + pad)
    sheet = Image.new("RGB", (W, 54 + 2 * (cell + 40) + 30), (10, 11, 12))
    d = ImageDraw.Draw(sheet)
    label(d, W / 2, 16, "MERIDIAN — MOTION STATES (PROPOSED, PROVISIONAL)",
          19, (222, 227, 232))
    for i, (name, rx, ry) in enumerate(MOTION_STATES):
        env = dict(FIXTURE_ENV, ACCELEROMETER_ANGLE_X=float(rx),
                   ACCELEROMETER_ANGLE_Y=float(ry))
        c, row = i % cols, i // cols
        x, y = pad + c * (cell + pad), 54 + row * (cell + 40)
        sheet.paste(compose(root, font, env, False).resize((cell, cell),
                                                           Image.LANCZOS),
                    (x, y))
        label(d, x + cell / 2, y + cell + 10, name, 14)
    out["MERIDIAN_XML_MOTION_STATES.png"] = sheet

    # Owner presentation image: both modes at true watch size, nothing else.
    W, H = 480 * 2 + 60, 480 + 96
    pres = Image.new("RGB", (W, H), (12, 13, 15))
    d = ImageDraw.Draw(pres)
    label(d, W / 2, 20, "ATTITUDE — MERIDIAN", 26, (232, 236, 240))
    label(d, W / 2, 52, "development build — not a release candidate", 14,
          (140, 148, 156))
    pres.paste(out["MERIDIAN_XML_NORMAL.png"], (20, 84))
    pres.paste(out["MERIDIAN_XML_AOD.png"], (520, 84))
    label(d, 260, 570, "NORMAL", 15)
    label(d, 760, 570, "ALWAYS-ON", 15)
    out["MERIDIAN_PRESENTATION.png"] = pres
    return out


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    root = ET.fromstring(XML.read_text())
    images = build(root, Font(root))
    REVIEW.mkdir(parents=True, exist_ok=True)
    manifest_path = REVIEW / "REVIEW_MANIFEST.json"

    if args.check:
        before = json.loads(manifest_path.read_text())
        for name, img in images.items():
            p = REVIEW / name
            if not p.exists():
                print(f"ERROR missing {name}", file=sys.stderr)
                return 1
            if sha256(p) != before["images"][name]["sha256"]:
                print(f"ERROR {name} differs from its recorded hash",
                      file=sys.stderr)
                return 1
        print(f"OK: {len(images)} review images match their recorded hashes")
        return 0

    for name, img in images.items():
        img.save(REVIEW / name)
    manifest = {
        "schema": "agenor.meridian-consumer-review/1",
        "rendered_from": "app/src/main/res/raw/watchface.xml and res/drawable",
        "watchface_xml_sha256": sha256(XML),
        "fixture_environment": FIXTURE_ENV,
        "fixture_note": ("sample data for these images only; the face binds "
                         "live WFF sources and compiles no constants"),
        "images": {n: {"sha256": sha256(REVIEW / n),
                       "bytes": (REVIEW / n).stat().st_size,
                       "width": images[n].width, "height": images[n].height}
                   for n in images},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)
                             + "\n")
    for n in images:
        print(f"{n}  {manifest['images'][n]['sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
