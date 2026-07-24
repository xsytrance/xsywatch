"""Render a loaded face specification into a WatchFace document string."""

from __future__ import annotations

from . import ENGINE_VERSION
from .model import Elem, document
from .spec import FaceSpec

GENERATED_BANNER = (
    "GENERATED FILE - do not edit by hand.\n"
    "  Authoritative source: watchfaces/{slug}/engine/face.toml\n"
    "  Regenerate: python3 tools/generate_face.py {slug}\n"
    "  Engine: wffgen {version}\n"
)


def render_face(spec: FaceSpec) -> str:
    root = Elem("WatchFace", {"width": str(spec.width),
                              "height": str(spec.height)})
    root.child(Elem("Metadata", {"key": "CLOCK_TYPE",
                                 "value": spec.clock_type}))
    root.child(Elem("Metadata", {"key": "PREVIEW_TIME",
                                 "value": spec.preview_time}))

    if spec.fonts:
        fonts = Elem("BitmapFonts")
        for font in spec.fonts:
            bf = Elem("BitmapFont", {"name": font["name"]})
            for ch in font["characters"]:
                bf.child(Elem("Character", {
                    "name": ch["name"], "resource": ch["resource"],
                    "width": str(ch["width"]), "height": str(ch["height"]),
                }))
            fonts.child(bf)
        root.child(fonts)

    scene = Elem("Scene", {"backgroundColor": spec.background_color})
    for comp in spec.components:
        for e in comp.elems:
            scene.child(e)
    root.child(scene)

    banner = GENERATED_BANNER.format(slug=spec.slug, version=ENGINE_VERSION)
    xml = document(root)
    # Banner as a comment directly after the XML declaration.
    decl, rest = xml.split("\n", 1)
    return f"{decl}\n<!--\n{banner}-->\n{rest}"
