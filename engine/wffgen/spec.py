"""Face-specification loading: TOML -> Component list.

The spec is data (TOML, stdlib tomllib); components are instantiated through
an explicit registry so the set of engine capabilities is enumerable and a
typo'd component type is an immediate error.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import components as C
from .profiles import AmbientPolicy, dim


@dataclass
class FaceSpec:
    slug: str
    width: int
    height: int
    wff_version: int
    clock_type: str
    preview_time: str
    background_color: str
    identity: dict
    fonts: list[dict] = field(default_factory=list)
    components: list[C.Component] = field(default_factory=list)


def _aod(d: dict) -> AmbientPolicy:
    return dim(int(d["alpha"]), float(d.get("duration", 0.4)),
               float(d.get("offset", 0.0)),
               d.get("interpolation", "LINEAR"))


def _box(d: dict) -> dict:
    return {"x": int(d["x"]), "y": int(d["y"]),
            "width": int(d["width"]), "height": int(d["height"])}


def _build(entry: dict) -> list[C.Component]:
    kind = entry["type"]
    if kind == "background_pair":
        parallax = tuple(entry["parallax"]) if "parallax" in entry else None
        return C.background_pair(entry["normal"], entry["aod_resource"],
                                 parallax, float(entry.get("fade", 0.6)))
    if kind == "rotating_image":
        return [C.rotating_image(entry["name"], entry["resource"],
                                 _box(entry["box"]), entry["speed"],
                                 _aod(entry["aod"]),
                                 bool(entry.get("reverse", False)),
                                 entry.get("ratio_note", ""))]
    if kind == "seconds_rotor":
        return [C.seconds_rotor(entry["name"], entry["resource"],
                                _box(entry["box"]), _aod(entry["aod"]))]
    if kind == "hr_balance":
        return [C.hr_balance(entry["name"], entry["resource"],
                             _box(entry["box"]), _aod(entry["aod"]),
                             entry.get("center", 180),
                             entry.get("amplitude", 35),
                             int(entry.get("fallback", 70)),
                             int(entry.get("clamp_lo", 40)),
                             int(entry.get("clamp_hi", 200)),
                             entry.get("rad_per_beat", 0.10472))]
    if kind == "battery_needle":
        return [C.battery_needle(entry["name"], entry["resource"],
                                 _aod(entry["aod"]), entry["start_deg"],
                                 entry["sweep_deg"],
                                 _box(entry["box"]) if "box" in entry else None)]
    if kind == "date_text":
        return [C.date_text(entry["name"], _box(entry["box"]),
                            _aod(entry["aod"]), entry["font"],
                            int(entry["size"]), entry["color"],
                            entry.get("template", "%d"),
                            entry.get("expression", "[DAY]"))]
    if kind == "sheen":
        parallax = tuple(entry["parallax"]) if "parallax" in entry else None
        return [C.sheen(entry["name"], entry["resource"], _aod(entry["aod"]),
                        entry["alpha_base"], entry["alpha_amp"],
                        entry["alpha_rad_per_sec"], parallax)]
    if kind == "analog_hand":
        return [C.analog_hand(entry["name"], entry["resource"],
                              _aod(entry["aod"]), entry["which"])]
    if kind == "static_image":
        return [C.static_image(entry["name"], entry["resource"],
                               _box(entry["box"]), _aod(entry["aod"]))]
    if kind == "text_line":
        return [C.text_line(entry["name"], _box(entry["box"]),
                            _aod(entry["aod"]), entry["font"],
                            int(entry["size"]), entry["color"],
                            entry["template"], list(entry["expressions"]),
                            entry.get("align", "CENTER"))]
    raise ValueError(f"unknown component type {kind!r} — registry: "
                     "background_pair, rotating_image, seconds_rotor, "
                     "hr_balance, battery_needle, date_text, sheen, "
                     "analog_hand, static_image, text_line")


def load_spec(path: Path | str) -> FaceSpec:
    data = tomllib.loads(Path(path).read_text())
    face = data["face"]
    fonts = []
    for f in data.get("fonts", []):
        chars = [{"name": name, "resource": v[0], "width": int(v[1]),
                  "height": int(f["height"])}
                 for name, v in f["characters"].items()]
        fonts.append({"name": f["name"], "characters": chars})
    comps: list[C.Component] = []
    for entry in data.get("components", []):
        comps.extend(_build(entry))
    return FaceSpec(
        slug=face["slug"], width=int(face["width"]),
        height=int(face["height"]), wff_version=int(face["wff_version"]),
        clock_type=face["clock_type"], preview_time=face["preview_time"],
        background_color=face["background_color"],
        identity=dict(data.get("identity", {})),
        fonts=fonts, components=comps,
    )
