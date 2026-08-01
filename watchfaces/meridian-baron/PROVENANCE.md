# Provenance — MERIDIAN BARON

The warbird colourway of the MERIDIAN family: crimson lacquered aircraft
skin, black anodized bezel, polished silver plates, gold trim, and long
turboprop blades for hands.

**Base art.** The dial layout is drawn procedurally by
`tools/meridian_pro/` (geometry.py + plate.py, `MP_VARIANT=baron`) from
original geometry — no third-party image or design asset enters the
chain. That render (`review/BARON4-layout.png`) is then finished with a
Flux Kontext Pro **img2img pass over our own render**
(`tools/meridian_pro/kontext_pass.py`), so the only source the generator
sees is our own work. The pass is verified afterwards against
geometry.py (9 positional anchors, wells/plates + the battery gauge
pod); labels, numerals and icons are baked
post-generation by `plate.dress_base` so the model never typesets.

**Hands.** Blade sprites come from the shared generator
`tools/propeller.py` (turboprop family), drawn with Pillow primitives
from parameters in `geometry.HANDS`. The reference for the silhouette
was a photograph of a real aircraft used for shape study only — nothing
from it was sampled, traced, or processed.

**Live layers.** Arcs, sub-dial rings, readouts, moon, and hands are
Watch Face Format vectors, text, and PartImages rendered by the watch at
runtime. The APK compiles no code and requests zero permissions.

Rebuild everything: `MP_VARIANT=baron python3 tools/meridian_pro/build.py`
