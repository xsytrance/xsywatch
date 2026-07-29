#!/usr/bin/env python3
"""Render any engine face's review images from its committed watchface.xml.

    python3 tools/render_face_from_xml.py <slug> [<slug> ...]
    python3 tools/render_face_from_xml.py --all
    python3 tools/render_face_from_xml.py --all --check

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

REPO = Path(__file__).resolve().parents[1]
FACE = None          # set by main() per slug
XML = None
DRAWABLE = None
REVIEW = None


def select(slug):
    """Point the renderer at one face project."""
    global FACE, XML, DRAWABLE, REVIEW
    FACE = REPO / "watchfaces" / slug
    XML = FACE / "app/src/main/res/raw/watchface.xml"
    DRAWABLE = FACE / "app/src/main/res/drawable"
    REVIEW = FACE / "review"
    return FACE


def resource(name):
    """Resolve a WFF resource across every drawable bucket a face may use."""
    for d in sorted(FACE.glob("app/src/main/res/drawable*")):
        p = d / f"{name}.png"
        if p.exists():
            return p
    raise FileNotFoundError(f"resource {name!r} not found under {FACE.name}")

# Sample environment for the review renders only. Nothing here is compiled
# into the APK; the face binds live sources.
FIXTURE_ENV = {
    "HOUR_0_11": 10, "MINUTE": 9, "SECOND": 30, "MILLISECOND": 0,
    "DAY": 27, "BATTERY_PERCENT": 78, "STEP_COUNT": 8420, "HEART_RATE": 72,
    "ACCELEROMETER_ANGLE_X": 0.0, "ACCELEROMETER_ANGLE_Y": 0.0,
    "ACCELEROMETER_ANGLE_Z": 0.0, "ACCELEROMETER_ANGLE_XY": 0.0,
    "ACCELEROMETER_X": 0.0, "ACCELEROMETER_Y": 0.0, "ACCELEROMETER_Z": 9.81,
    "ACCELEROMETER_IS_SUPPORTED": 1,
    "WEATHER.IS_AVAILABLE": 1, "WEATHER.IS_ERROR": 0, "WEATHER.IS_DAY": 1,
    "WEATHER.TEMPERATURE": 14, "WEATHER.CHANCE_OF_PRECIPITATION": 0,
    # Current conditions the probe reads. CONDITION's integer is undecoded —
    # 3 is a placeholder for rendering, not a claim about what 3 means.
    "WEATHER.CONDITION": 3, "WEATHER.CONDITION_NAME": "Partly Cloudy",
    "WEATHER.TEMPERATURE_HIGH": 19, "WEATHER.TEMPERATURE_LOW": 8,
    "WEATHER.WEATHER.UV_INDEX": 4, "WEATHER.WEATHER.LAST_UPDATED": 0,
    "MOON_PHASE_POSITION": 0.42, "MOON_PHASE_TYPE": 3,
    "HOUR_0_23": 10,
    # Forecast. Declared by the schema at v4 and v5 as xs:pattern members of
    # weatherSourceType; whether a provider actually populates them is what
    # the probe is worn to find out. These values let the face be RENDERED,
    # and are not evidence about the device.
    "WEATHER.HOURS.0.IS_AVAILABLE": 1, "WEATHER.HOURS.0.CONDITION": 3,
    "WEATHER.HOURS.0.TEMPERATURE": 15, "WEATHER.HOURS.0.UV_INDEX": 4,
    "WEATHER.HOURS.3.IS_AVAILABLE": 1, "WEATHER.HOURS.3.CONDITION": 7,
    "WEATHER.HOURS.3.TEMPERATURE": 17,
    "WEATHER.DAYS.1.IS_AVAILABLE": 1, "WEATHER.DAYS.1.CONDITION_DAY": 5,
    "WEATHER.DAYS.1.CONDITION_NIGHT": 2,
    "WEATHER.DAYS.1.TEMPERATURE_HIGH": 21,
    "WEATHER.DAYS.1.TEMPERATURE_LOW": 9,
    "WEATHER.DAYS.1.CHANCE_OF_PRECIPITATION": 30,
}

# Exactly the functions arithmeticExpressionType declares, and no more.
# min() and max() are NOT in the format — only clamp(,,) is — and they were
# accepted here, so this renderer would have happily previewed an expression
# the watch cannot evaluate. A review tool that is more permissive than the
# device is the failure mode this repo keeps rediscovering, so the guard now
# errs the other way: an undeclared function reads as an unresolved name.
SAFE = {"clamp": lambda v, lo, hi: max(lo, min(hi, v)), "sin": math.sin,
        "cos": math.cos, "round": round, "abs": abs,
        "tan": math.tan, "asin": math.asin, "acos": math.acos,
        "atan": math.atan, "sqrt": math.sqrt, "cbrt": lambda v: v ** (1 / 3),
        "log": math.log, "log2": math.log2, "log10": math.log10,
        "exp": math.exp, "expm1": math.expm1, "pow": pow,
        "floor": math.floor, "ceil": math.ceil,
        "deg": math.degrees, "rad": math.radians,
        "fract": lambda v: v - math.floor(v)}

# Every function the format defines, so the unresolved-name guard below can
# tell a legitimate call from a data source nobody supplied a value for.
_FUNCS = tuple(SAFE)


def _deternary(py: str) -> str:
    """Rewrite WFF's `cond ? a : b` into Python's `a if cond else b`.

    Done by scanning rather than by regex: the branches contain parentheses of
    their own — `[ACCELEROMETER_IS_SUPPORTED] ? (0 - 24.0 * clamp(...) / 45)
    : 0` — and a pattern simple enough to be safe cannot see past them.

    Innermost first, so nested conditionals collapse from the inside out.
    """
    while "?" in py:
        i = py.rindex("?")
        depth, colon = 0, -1
        for j in range(i + 1, len(py)):
            c = py[j]
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    break
                depth -= 1
            elif c == ":" and depth == 0:
                colon = j
                break
        if colon < 0:
            raise ValueError(f"conditional with no ':' in {py!r}")
        depth, start = 0, 0
        for j in range(i - 1, -1, -1):
            c = py[j]
            if c == ")":
                depth += 1
            elif c == "(":
                if depth == 0:
                    start = j + 1
                    break
                depth -= 1
        depth, end = 0, len(py)
        for j in range(colon + 1, len(py)):
            c = py[j]
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    end = j
                    break
                depth -= 1
        cond, yes, no = py[start:i], py[i + 1:colon], py[colon + 1:end]
        py = f"{py[:start]}({yes}) if ({cond}) else ({no}){py[end:]}"
    return py


def evaluate(expr: str, env: dict):
    """Evaluate one WFF arithmetic expression under a data environment.

    Returns a float, except for a bare string source. WEATHER.CONDITION_NAME
    and MOON_PHASE_TYPE_STRING are text, and text is the whole point of them —
    a face cannot branch on a string, only print it. Such a source is only
    ever legal on its own, so anything more complex still goes down the
    arithmetic path and still fails loudly if it is not a number.
    """
    lone = re.fullmatch(r"\s*\[([A-Z_0-9.]+)\]\s*", expr)
    if lone and isinstance(env.get(lone.group(1)), str):
        return env[lone.group(1)]

    def sub(m):
        token = m.group(1)
        if token not in env:
            raise KeyError(f"no value supplied for [{token}]")
        return repr(env[token])
    # Source tokens may carry a dot — the whole WEATHER.* family does.
    py = re.sub(r"\[([A-Z_0-9.]+)\]", sub, expr)
    py = py.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    py = _deternary(py)
    bare = py
    for fn in _FUNCS + ("and", "or", "not", "if", "else", "True", "False"):
        bare = bare.replace(fn, "")
    if re.search(r"[A-Za-z_]+", bare):
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
            with Image.open(resource(res)) as g:
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
            if text[i + 1] == "%":
                out.append("%")
                i += 2
                continue
            # Accept a width/zero-pad flag: HOG-WILD's clock is "%d:%02d", and
            # skipping the flag left the "2" and the "d" to be drawn as text.
            m = re.match(r"%(0?\d*)([ds])", text[i:])
            if m:
                flag, kind = m.group(1), m.group(2)
                v = values[vi]
                s = str(int(round(v))) if kind == "d" else str(v)
                if flag:
                    width = int(flag.lstrip("0") or 0)
                    s = s.rjust(width, "0" if flag.startswith("0") else " ")
                out.append(s)
                vi += 1
                i += m.end()
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def expand(container, branch: str | None):
    """Flatten <Condition> blocks into a plain part list.

    The renderer draws a flat sequence of parts, but weather, and anything
    else that varies, arrives wrapped in Condition/Compare/Default. Without
    this the Condition element itself reaches the part loop and dies looking
    for a width attribute it was never going to have.

    `branch` names the Compare to take — the expression names are the
    engine's own (wx_rain, wx_storm, wx_night ...). Anything unmatched falls
    to Default, which is exactly what the watch does when weather is
    unavailable, so None renders the fair-weather face.
    """
    out = []
    for node in container:
        if node.tag != "Condition":
            out.append(node)
            continue
        chosen = None
        for cmp_ in node.findall("Compare"):
            if branch is not None and cmp_.get("expression") == branch:
                chosen = cmp_
                break
        if chosen is None:
            chosen = node.find("Default")
        if chosen is not None:
            out.extend(expand(chosen, branch))
    return out


def compose(root, font, env, ambient: bool, skip: set[str] | None = None,
            branch: str | None = None):
    """`skip` omits named parts — used by the coverage gate to look at the
    horizon and plate alone, without hands crossing the aperture."""
    from PIL import Image
    scene = root.find("Scene")
    bg = scene.get("backgroundColor", "#FF000000")
    canvas = Image.new("RGBA", (int(root.get("width")), int(root.get("height"))),
                       (int(bg[3:5], 16), int(bg[5:7], 16), int(bg[7:9], 16),
                        255))
    for part in expand(scene, branch):
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
            with Image.open(resource(res)) as im:
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
            # <Template> may be wrapped in <Upper>/<Lower>. A bitmap font only
            # renders the glyphs it declares, so a face printing a provider's
            # own casing folds it rather than dropping half the string.
            tmpl = bf.find(".//Template")
            text = format_template(tmpl, env)
            if bf.find("Upper") is not None:
                text = text.upper()
            elif bf.find("Lower") is not None:
                text = text.lower()
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


SLUG_LABEL = ""


def build(root, font):
    from PIL import Image, ImageDraw
    out = {}
    out["FACE_NORMAL.png"] = compose(root, font, dict(FIXTURE_ENV),
                                             False)
    out["FACE_AOD.png"] = compose(root, font, dict(FIXTURE_ENV), True)

    cell, pad = 300, 14
    W = pad + len(HAND_POSITIONS) * (cell + pad)
    sheet = Image.new("RGB", (W, 54 + cell + 44), (10, 11, 12))
    d = ImageDraw.Draw(sheet)
    label(d, W / 2, 16, f"{SLUG_LABEL} — HAND POSITIONS FROM watchface.xml",
          19, (222, 227, 232))
    for i, (hh, mm, ss) in enumerate(HAND_POSITIONS):
        env = dict(FIXTURE_ENV, HOUR_0_11=hh % 12, MINUTE=mm, SECOND=ss)
        sheet.paste(compose(root, font, env, False).resize((cell, cell),
                                                           Image.LANCZOS),
                    (pad + i * (cell + pad), 54))
        label(d, pad + i * (cell + pad) + cell / 2, 54 + cell + 12,
              f"{hh:02d}:{mm:02d}", 16, (198, 152, 74))
    out["FACE_HAND_POSITIONS.png"] = sheet

    cols = 3
    W = pad + cols * (cell + pad)
    sheet = Image.new("RGB", (W, 54 + 2 * (cell + 40) + 30), (10, 11, 12))
    d = ImageDraw.Draw(sheet)
    label(d, W / 2, 16, f"{SLUG_LABEL} — MOTION STATES (PROPOSED, PROVISIONAL)",
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
    out["FACE_MOTION_STATES.png"] = sheet

    # Owner presentation image: both modes at true watch size, nothing else.
    W, H = 480 * 2 + 60, 480 + 96
    pres = Image.new("RGB", (W, H), (12, 13, 15))
    d = ImageDraw.Draw(pres)
    label(d, W / 2, 20, SLUG_LABEL, 26, (232, 236, 240))
    label(d, W / 2, 52, "development build — not a release candidate", 14,
          (140, 148, 156))
    pres.paste(out["FACE_NORMAL.png"], (20, 84))
    pres.paste(out["FACE_AOD.png"], (520, 84))
    label(d, 260, 570, "NORMAL", 15)
    label(d, 760, 570, "ALWAYS-ON", 15)
    out["FACE_PRESENTATION.png"] = pres
    return out


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_for(slug, check):
    global SLUG_LABEL
    select(slug)
    SLUG_LABEL = slug.replace("squadron-", "MERIDIAN ").replace(
        "attitude-meridian", "ATTITUDE MERIDIAN").upper()
    root = ET.fromstring(XML.read_text())
    images = build(root, Font(root))
    REVIEW.mkdir(parents=True, exist_ok=True)
    mp = REVIEW / "REVIEW_MANIFEST.json"
    if check:
        before = json.loads(mp.read_text())
        for name in images:
            p = REVIEW / name
            if not p.exists() or sha256(p) != before["images"][name]["sha256"]:
                return f"{slug}: {name} differs from its recorded hash"
        return None
    for name, img in images.items():
        img.save(REVIEW / name)
    mp.write_text(json.dumps({
        "schema": "agenor.face-review-render/1",
        "slug": slug,
        "rendered_from": "app/src/main/res/raw/watchface.xml and res/drawable",
        "watchface_xml_sha256": sha256(XML),
        "fixture_environment": FIXTURE_ENV,
        "fixture_note": ("sample data for these images only; the face binds "
                         "live WFF sources and compiles no constants"),
        "images": {n: {"sha256": sha256(REVIEW / n),
                       "bytes": (REVIEW / n).stat().st_size,
                       "width": images[n].width, "height": images[n].height}
                   for n in images},
    }, indent=2, sort_keys=True) + "\n")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    slugs = args.slugs
    if args.all:
        slugs = sorted(p.parent.parent.name
                       for p in REPO.glob("watchfaces/*/engine/face.toml"))
    if not slugs:
        print("no faces selected", file=sys.stderr)
        return 2
    bad = []
    for slug in slugs:
        err = build_for(slug, args.check)
        if err:
            bad.append(err)
            print(f"ERROR {err}", file=sys.stderr)
        else:
            print(f"{'ok  ' if args.check else 'rendered'} {slug}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
