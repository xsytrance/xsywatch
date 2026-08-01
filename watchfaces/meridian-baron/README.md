# MERIDIAN BARON

The warbird: red, black, silver and gold, with long turboprop propeller
blades for hands. A sibling product of MERIDIAN PRO built from the same
tooling (`tools/meridian_pro/`, `MP_VARIANT=baron`) — same layout
grammar, its own palette, identity, and blade family.

- Crimson riveted aircraft-skin ring inside a black anodized bezel with
  engraved gold minute numerals
- Two-level polished silver centre plate; wells, windows and wordmark
  plate in black lacquer
- Hands are slender turboprop blades (shared generator
  `tools/propeller.py`): black lacquer in a gold edge, lume spine, and a
  striped ivory/crimson warning tip that carries the AOD read
- Live: battery arc + %, steps ring, HR ring, date, military time, moon
  phase, sunrise/sunset windows — all WFF vectors and text, zero
  permissions

Build: `MP_VARIANT=baron python3 tools/meridian_pro/build.py`
Renders: `python3 tools/render_face_from_xml.py meridian-baron`
APK: `cd watchfaces/meridian-baron && ./gradlew assembleDebug`

Review images live in `review/`; `BARON4-layout.png` is the procedural
layout, `BARON4-kontext.png` the finished base (see PROVENANCE.md).
BARON1 (no gauge), BARON2 (applied gauge pod) and BARON3 (tight date
frame) are earlier iterations, kept for the record.

The battery readout sits in a gauge window punched into a turret of the
plate itself (no % sign); sub-dial numerals are sized to live inside
their wells; the date frame is taller with spread fields; no military
star.
