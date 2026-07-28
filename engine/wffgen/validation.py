"""Structural validation of engine-generated faces.

Raises SpecError with every problem found (not just the first). These are
engine-level guarantees; the official WFF XSD validator remains a separate,
additional gate (docs/BUILD_AND_RELEASE.md).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from . import KNOWN_SOURCES
from .spec import FaceSpec

SOURCE_RE = re.compile(r"\[([A-Z_0-9.]+)\]")   # dots: WEATHER.IS_DAY


class SpecError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("face spec validation failed:\n  - "
                         + "\n  - ".join(problems))


def validate_face(spec: FaceSpec, xml_text: str,
                  available_resources: set[str] | None = None) -> None:
    problems: list[str] = []
    root = ET.fromstring(xml_text)

    # Unique, deterministic part names in z-order.
    names = [e.get("name") for e in root.iter()
             if e.tag.startswith(("Part", "Group")) and e.get("name")]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        problems.append(f"duplicate element names: {sorted(dupes)}")
    z_names = [n for n in names if re.match(r"z\d\d_", n)]
    if z_names != sorted(z_names):
        problems.append(f"z-prefixed names out of z-order: {z_names}")
    bad_names = [n for n in names if not re.match(r"z\d\d_[a-z0-9_]+$", n)]
    if bad_names:
        problems.append(f"names outside naming convention zNN_slug: {bad_names}")

    # Every angle transform needs an explicit pivot.
    for part in root.iter():
        if not part.tag.startswith("Part"):
            continue
        has_angle = any(c.tag == "Transform" and c.get("target") == "angle"
                        for c in part)
        if has_angle and not (part.get("pivotX") and part.get("pivotY")):
            problems.append(f"{part.get('name')}: angle transform without pivot")

    # Static geometry stays inside the face canvas.
    W, H = spec.width, spec.height
    for part in root.iter():
        if not part.tag.startswith(("Part", "Group")):
            continue
        try:
            x, y = int(part.get("x", 0)), int(part.get("y", 0))
            w, h = int(part.get("width", 0)), int(part.get("height", 0))
        except ValueError:
            continue
        if x < 0 or y < 0 or x + w > W or y + h > H:
            problems.append(f"{part.get('name')}: box ({x},{y},{w},{h}) "
                            f"outside {W}x{H} canvas")

    # Data sources must be known WFF v4 tokens.
    for e in root.iter():
        for attr in ("value", "expression"):
            v = e.get(attr)
            if not v:
                continue
            for src in SOURCE_RE.findall(v):
                if src not in KNOWN_SOURCES:
                    problems.append(f"unknown data source [{src}] in {attr}={v[:50]!r}")

    # Alpha attributes and ambient variants in range.
    for e in root.iter():
        for attr in ("alpha",):
            v = e.get(attr)
            if v is not None and not (v.isdigit() and 0 <= int(v) <= 255):
                problems.append(f"{e.get('name') or e.tag}: alpha {v!r} not 0..255")

    # Referenced resources exist (when the caller supplies the set).
    if available_resources is not None:
        referenced = {e.get("resource") for e in root.iter()
                      if e.get("resource")}
        missing = sorted(referenced - available_resources)
        if missing:
            problems.append(f"referenced resources missing from res/: {missing}")

    # Component metadata contract: every component declares motion + AOD.
    for comp in spec.components:
        if comp.motion_class is None or comp.aod is None:
            problems.append(f"component {comp.name}: undeclared motion/AOD")

    # Expected identity is present in the spec (checked against Gradle by
    # tools/generate_face.py; here we require the declaration itself).
    for key in ("package", "version_code", "version_name"):
        if not spec.identity.get(key):
            problems.append(f"spec identity missing {key}")

    if problems:
        raise SpecError(problems)
