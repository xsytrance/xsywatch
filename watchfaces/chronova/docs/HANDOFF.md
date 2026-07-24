# CHRONOVA handoff — what's done / what's next

## Done (2026-07-13)
Phases 0-4 core: buildable WFF v4 project, 35 procedural assets (17 metals
photoreal via Blender), reactor behaviors, live time (12/24h via system),
pass-1 ambient, verified on Wear OS 6 emulator. Debug APK ships to owner for
wrist testing.

P5 (Session 2): gyro parallax on 7 depth planes (plate 2 … foreground glints
14) via `plane=` in gen_watchface.py, emulator-verified with the virtual
accelerometer (per-plane pixel shifts match design); tap surge + startup
ignite as `PartAnimatedImage` WebP sequences (`scripts/build_webp_sequences.py`,
18f @ 12fps, TAP / ON_VISIBLE, HIDE when idle). 30 animated groups. Full
watchface.xml validates 0-errors against the official WFF v4 XSD (XSD 1.1 —
use python `xmlschema`, not xmllint). Parallax freezes (not disabled) in
ambient — acceptable until P8.

## Next phases (owner's spec, deferred deliberately)
- **P6 complications**: slots upper module / lower-left / lower-right; battery
  as containment-ring segments; steps as perimeter arc (owner-disableable).
- **P7 flavors**: 6 palettes via WFF Flavors (NEON FUSION default, HACKER
  MATRIX, BLOOD CIRCUIT, REACTOR AMBER, VOID SIGNAL, MONOCHROME TITANIUM).
  Conduits/packets/arcs/core need per-flavor asset sets or ColorConfiguration.
- **P8 designed AOD**: dedicated silhouette art, not alpha-dimming.
- **P9 performance**: package size budget, overdraw pass, official validator +
  memory-footprint tools from github.com/google/watchface play-validations.
- **P10 wrist QA**: the full test matrix from the spec run on the physical
  Watch7 (midnight rollover, single-digit hours, flavors, low battery, etc.).
- **Visual upgrade path**: replace procedural PIL assets with Blender-rendered
  or offline-generated photoreal layers, same filenames — the scene XML and
  animation system do not change.

## How to iterate
venv with Pillow+numpy -> `python scripts/generate_assets.py` ->
`~/Android/blender/.../blender -b -P scripts/render_blender_layers.py`
(ALWAYS after the PIL pass — it overwrites the 17 metals) ->
`python scripts/build_webp_sequences.py` (needs ffmpeg; only if effects
changed) -> `python scripts/gen_watchface.py` -> `gradle :app:assembleDebug` ->
`adb install -r` -> set-watchface broadcast
(`--es watchFaceId com.xsytrance.xenochronengine`).
