"""Shared visual-lineage library (ADR-009, Phase 3).

Three concerns, consumed by the thin CLIs `render_reference.py`,
`compare_visuals.py`, and `inventory_resources.py`:

1. a deterministic evaluator for the WFF arithmetic-expression subset the
   Aurelius engine emits (numbers, [SOURCES], + - * / %, unary -, parens,
   comparisons, ternary ?:, clamp(), sin());
2. a scene model parsed from the COMMITTED generated watchface.xml
   (PartImage/PartText, Variant AMBIENT alpha, Transforms, BitmapFont);
3. deterministic Pillow composition of that scene at a pinned state.

Determinism contract:
- expression math is IEEE-754 double via Python's `math`;
- Pillow ops are pinned (version recorded in states.toml [render] and in
  golden metadata; `--strict` fails on mismatch);
- PNG output is written without timestamps or ancillary chunks beyond
  Pillow's deterministic defaults, so reruns are byte-identical.

Known WFF-runtime behaviors this renderer does NOT reproduce (documented per
brief §6.3; they matter only for device-capture comparisons, which use the
calibrated perceptual profile, never for reference-vs-reference checks):
- ambient enter/exit animation (Variant duration/offset/interpolation) —
  states are end-states, not transitions;
- panel color response, dimming curves, and One UI system overlays;
- the runtime's exact resampling kernels for scaled/rotated drawables.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Expression evaluator
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"""
    \s*(?:
      (?P<num>\d+\.\d+|\.\d+|\d+)
    | (?P<src>\[[A-Z_0-9]+\])
    | (?P<name>[a-zA-Z_][a-zA-Z_0-9]*)
    | (?P<op><=|>=|==|!=|[-+*/%(),?:<>])
    )""", re.X)


def tokenize(expr: str) -> list[str]:
    pos, out = 0, []
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m or m.end() == pos:
            rest = expr[pos:].strip()
            if not rest:
                break
            raise ValueError(f"bad token at {expr[pos:pos+20]!r}")
        out.append(next(g for g in m.groups() if g is not None))
        pos = m.end()
    return out


class _Parser:
    """Recursive-descent parser for the engine's expression subset.

    Grammar (lowest to highest precedence):
      ternary   := compare ('?' ternary ':' ternary)?
      compare   := additive (('<'|'>'|'<='|'>='|'=='|'!=') additive)?
      additive  := multiplic (('+'|'-') multiplic)*
      multiplic := unary (('*'|'/'|'%') unary)*
      unary     := '-' unary | primary
      primary   := NUM | SRC | func '(' args ')' | '(' ternary ')'
    """

    def __init__(self, tokens: list[str], state: dict[str, float]):
        self.t = tokens
        self.i = 0
        self.state = state

    def peek(self) -> str | None:
        return self.t[self.i] if self.i < len(self.t) else None

    def eat(self, tok: str | None = None) -> str:
        cur = self.peek()
        if cur is None or (tok is not None and cur != tok):
            raise ValueError(f"expected {tok!r}, got {cur!r} at {self.i}")
        self.i += 1
        return cur

    def parse(self) -> float:
        v = self.ternary()
        if self.peek() is not None:
            raise ValueError(f"trailing tokens: {self.t[self.i:]}")
        return v

    def ternary(self) -> float:
        cond = self.compare()
        if self.peek() == "?":
            self.eat("?")
            a = self.ternary()
            self.eat(":")
            b = self.ternary()
            return a if cond != 0 else b
        return cond

    def compare(self) -> float:
        left = self.additive()
        op = self.peek()
        if op in ("<", ">", "<=", ">=", "==", "!="):
            self.eat(op)
            right = self.additive()
            return float({
                "<": left < right, ">": left > right,
                "<=": left <= right, ">=": left >= right,
                "==": left == right, "!=": left != right,
            }[op])
        return left

    def additive(self) -> float:
        v = self.multiplic()
        while self.peek() in ("+", "-"):
            op = self.eat()
            r = self.multiplic()
            v = v + r if op == "+" else v - r
        return v

    def multiplic(self) -> float:
        v = self.unary()
        while self.peek() in ("*", "/", "%"):
            op = self.eat()
            r = self.unary()
            if op == "*":
                v = v * r
            elif op == "/":
                v = v / r
            else:
                v = math.fmod(v, r)      # WFF % is C-style fmod
                if v < 0:
                    v += abs(r)          # normalized like device behavior
        return v

    def unary(self) -> float:
        if self.peek() == "-":
            self.eat("-")
            return -self.unary()
        return self.primary()

    def primary(self) -> float:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        if tok == "(":
            self.eat("(")
            v = self.ternary()
            self.eat(")")
            return v
        if tok.startswith("["):
            self.eat()
            key = tok[1:-1]
            if key not in self.state:
                raise KeyError(f"unpinned data source [{key}]")
            return float(self.state[key])
        if re.fullmatch(r"\d+\.\d+|\.\d+|\d+", tok):
            self.eat()
            return float(tok)
        # function call
        name = self.eat()
        self.eat("(")
        args = [self.ternary()]
        while self.peek() == ",":
            self.eat(",")
            args.append(self.ternary())
        self.eat(")")
        if name == "clamp" and len(args) == 3:
            return max(args[1], min(args[2], args[0]))
        if name == "sin" and len(args) == 1:
            return math.sin(args[0])
        if name == "cos" and len(args) == 1:
            return math.cos(args[0])
        raise ValueError(f"unsupported function {name}/{len(args)}")


def evaluate(expr: str, state: dict[str, float]) -> float:
    return _Parser(tokenize(expr), state).parse()


# --------------------------------------------------------------------------
# States
# --------------------------------------------------------------------------

_STATE_KEYS = {
    "hour_0_11": "HOUR_0_11", "minute": "MINUTE", "second": "SECOND",
    "millisecond": "MILLISECOND", "day": "DAY",
    "battery_percent": "BATTERY_PERCENT", "heart_rate": "HEART_RATE",
    "accelerometer_angle_x": "ACCELEROMETER_ANGLE_X",
    "accelerometer_angle_y": "ACCELEROMETER_ANGLE_Y",
}


@dataclass
class VisualContract:
    face: str
    path: Path
    raw: dict

    @classmethod
    def load(cls, face: str) -> "VisualContract":
        p = REPO / "watchfaces" / face / "visual" / "states.toml"
        with open(p, "rb") as fh:
            return cls(face, p, tomllib.load(fh))

    def state(self, name: str) -> dict:
        states = self.raw["states"]
        if name not in states:
            raise KeyError(f"unknown state {name!r}; have {sorted(states)}")
        chain, cur = [], name
        while cur is not None:
            chain.append(states[cur])
            cur = states[cur].get("inherit")
        merged: dict = {}
        for layer in reversed(chain):
            merged.update({k: v for k, v in layer.items() if k != "inherit"})
        ambient = bool(merged.get("ambient", False))
        if ambient:  # sub-minute sources stop in ambient (device-observed)
            merged["second"] = 0
            merged["millisecond"] = 0
        pinned = {wff: float(merged[k]) for k, wff in _STATE_KEYS.items()}
        return {"name": name, "ambient": ambient, "pinned": pinned,
                "raw": merged}

    def golden_states(self) -> dict:
        g = self.raw["goldens"]
        return {"normal": g["normal_state"], "aod": g["aod_state"],
                "version": g["approved_version"]}


# --------------------------------------------------------------------------
# Scene model from the committed generated XML
# --------------------------------------------------------------------------

@dataclass
class Layer:
    kind: str                      # image | text
    name: str
    x: float
    y: float
    width: float
    height: float
    alpha: int
    pivot: bool
    ambient_alpha: int | None
    transforms: dict[str, str] = field(default_factory=dict)
    resource: str | None = None
    text: dict | None = None       # template/params/font/size/color/align


@dataclass
class Scene:
    face: str
    width: int
    height: int
    fonts: dict                    # family -> {char: (resource, w, h)}
    layers: list[Layer]
    xml_path: Path
    xml_sha256: str

    @classmethod
    def load(cls, face: str) -> "Scene":
        xml_path = (REPO / "watchfaces" / face /
                    "app/src/main/res/raw/watchface.xml")
        data = xml_path.read_bytes()
        root = ET.fromstring(data)
        fonts: dict = {}
        for bf in root.iter("BitmapFont"):
            if "name" not in bf.attrib:      # scene <BitmapFont family=...>
                continue
            fam = bf.attrib["name"]
            fonts[fam] = {}
            for ch in bf.iter("Character"):
                fonts[fam][ch.attrib["name"]] = (
                    ch.attrib["resource"], int(ch.attrib["width"]),
                    int(ch.attrib["height"]))
        layers: list[Layer] = []
        scene = root.find("Scene")
        if scene is None:
            raise ValueError(f"{xml_path}: no <Scene>")
        for el in scene:
            if el.tag not in ("PartImage", "PartText"):
                continue
            amb = None
            for var in el.findall("Variant"):
                if (var.attrib.get("mode") == "AMBIENT"
                        and var.attrib.get("target") == "alpha"):
                    amb = int(var.attrib["value"])
            lay = Layer(
                kind="image" if el.tag == "PartImage" else "text",
                name=el.attrib.get("name", "?"),
                x=float(el.attrib.get("x", 0)),
                y=float(el.attrib.get("y", 0)),
                width=float(el.attrib.get("width", 0)),
                height=float(el.attrib.get("height", 0)),
                alpha=int(el.attrib.get("alpha", 255)),
                pivot="pivotX" in el.attrib,
                ambient_alpha=amb,
            )
            for tr in el.findall("Transform"):
                lay.transforms[tr.attrib["target"]] = tr.attrib["value"]
            img = el.find("Image")
            if img is not None:
                lay.resource = img.attrib["resource"]
            txt = el.find(".//Text")
            if txt is not None:
                bf = txt.find("BitmapFont")
                tmpl = bf.find("Template")
                params = [p.attrib["expression"]
                          for p in tmpl.findall("Parameter")]
                lay.text = {
                    "align": txt.attrib.get("align", "CENTER"),
                    "family": bf.attrib["family"],
                    "size": int(bf.attrib["size"]),
                    "color": bf.attrib["color"],
                    "template": (tmpl.text or ""),
                    "params": params,
                }
            layers.append(lay)
        w = int(root.attrib["width"])
        h = int(root.attrib["height"])
        return cls(face, w, h, fonts, layers, xml_path,
                   hashlib.sha256(data).hexdigest())


# --------------------------------------------------------------------------
# Composition
# --------------------------------------------------------------------------

BACKGROUND_COLOR = (6, 4, 3, 255)   # face.toml background_color #FF060403


def _res_path(face: str, resource: str) -> Path:
    return (REPO / "watchfaces" / face /
            "app/src/main/res/drawable-nodpi" / f"{resource}.png")


def render_state(scene: Scene, contract: VisualContract,
                 state_name: str):
    """Compose the scene at a pinned state; returns a PIL RGBA image."""
    from PIL import Image

    st = contract.state(state_name)
    pinned, ambient = st["pinned"], st["ambient"]
    canvas = Image.new("RGBA", (scene.width, scene.height), BACKGROUND_COLOR)

    for lay in scene.layers:
        alpha = lay.ambient_alpha if (ambient and lay.ambient_alpha
                                      is not None) else lay.alpha
        x, y = lay.x, lay.y
        angle = None
        for target, expr in lay.transforms.items():
            val = evaluate(expr, pinned)
            if target == "x":
                x = val
            elif target == "y":
                y = val
            elif target == "alpha":
                if not ambient:      # ambient Variant wins over transform
                    alpha = val
            elif target == "angle":
                angle = val
        alpha = max(0, min(255, int(round(alpha))))
        if alpha == 0:
            continue

        if lay.kind == "image":
            src = Image.open(_res_path(scene.face, lay.resource)).convert("RGBA")
            bw, bh = int(round(lay.width)), int(round(lay.height))
            if src.size != (bw, bh):
                src = src.resize((bw, bh), Image.LANCZOS)
            if angle is not None:
                # WFF angle is clockwise; Pillow rotate is counter-clockwise.
                src = src.rotate(-angle, resample=Image.BICUBIC,
                                 center=(bw / 2, bh / 2))
            tile = src
        else:
            tile = _render_text(scene, lay, pinned)
            bw, bh = tile.size

        if alpha < 255:
            a = tile.getchannel("A").point(lambda p: p * alpha // 255)
            tile.putalpha(a)
        canvas.alpha_composite(tile, (int(round(x)), int(round(y))))
    return canvas


def _render_text(scene: Scene, lay: Layer, pinned: dict):
    """Deterministic BitmapFont line composition (CENTER/LEFT/RIGHT)."""
    from PIL import Image

    spec = lay.text
    values = [evaluate(p, pinned) for p in spec["params"]]
    text = spec["template"]
    for v in values:                      # engine emits %d placeholders
        text = text.replace("%d", str(int(v)), 1)
    fam = scene.fonts[spec["family"]]
    native_h = next(iter(fam.values()))[2] if fam else spec["size"]
    scale = spec["size"] / native_h
    glyphs = []
    for ch in text:
        if ch not in fam:
            raise KeyError(f"glyph {ch!r} missing from font "
                           f"{spec['family']!r}")
        res, gw, gh = fam[ch]
        glyphs.append((res, gw * scale, spec["size"]))
    total_w = sum(g[1] for g in glyphs)
    box_w, box_h = int(round(lay.width)), int(round(lay.height))
    tile = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    if spec["align"] == "LEFT":
        cx = 0.0
    elif spec["align"] == "RIGHT":
        cx = box_w - total_w
    else:
        cx = (box_w - total_w) / 2
    cy = (box_h - spec["size"]) / 2
    for res, gw, gh in glyphs:
        img = Image.open(_res_path(scene.face, res)).convert("RGBA")
        img = img.resize((max(1, int(round(gw))), int(round(gh))),
                         Image.LANCZOS)
        tile.alpha_composite(img, (int(round(cx)), int(round(cy))))
        cx += gw
    return tile


def save_png_deterministic(img, path: Path) -> str:
    """Save without timestamps/ancillary chunks; return sha256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pillow_version() -> str:
    import PIL
    return PIL.__version__


def check_pillow_pin(contract: VisualContract, strict: bool) -> str | None:
    pin = contract.raw.get("render", {}).get("pillow_version")
    actual = pillow_version()
    if pin and actual != pin:
        msg = (f"Pillow {actual} != pinned {pin} "
               f"(states.toml [render].pillow_version)")
        if strict:
            raise RuntimeError(msg)
        return msg
    return None


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json_deterministic(obj, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()
