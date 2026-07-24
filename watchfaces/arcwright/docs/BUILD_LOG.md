# ARCWRIGHT build log

## 2026-07-13 — Session 1 (P0 scaffold + P1 bitmap-font probe)

- **P0**: skeleton copied from Chronova (3 gradle files + manifest +
  watch_face_info.xml; hasCode=false). Identity carriers edited:
  rootProject.name, namespace/applicationId `com.xsytrance.arcwright`,
  label ARCWRIGHT. Coexistence verified on emulator: arcwright +
  xenochronengine + tripface all installed simultaneously, each selectable.
- **P1 probe findings (emulator, Wear OS 6 / API 36)** — BitmapFont runtime
  behavior, all confirmed with crude diagnostic glyphs:
  - `<BitmapFonts><BitmapFont name><Character/>` renders; referenced from
    TimeText via `<BitmapFont family size color/>`.
  - Per-place tokens `hh_10/hh_1/mm_10/mm_1/ss_10/ss_1` all work;
    **hh_10 zero-pads single-digit hours in 12h mode** (8pm → "08").
  - `size` attribute scales glyphs cleanly (68px Characters rendered at 34).
  - `ss_1` updates every second; DigitalClock-level
    `Variant AMBIENT alpha 0` hides seconds in ambient; large digits stay
    visible dimmed.
  - **GOTCHA: a character missing from the family is dropped SILENTLY**
    (combined `hh:mm` through a family with no ':' just omits the colon —
    no error, no logcat noise). Every family must carry every glyph its
    formats can emit.
  - `align` accepts START/CENTER/END (not LEFT/RIGHT) — XSD caught it.
- Schema validation: python xmlschema XMLSchema11 against the WFF v4 XSD
  (google/watchface clone) — same tooling discipline as Chronova.
- **Wrist check pending** — watch intermittently reachable over wireless ADB.
  CAUTION from this session: match the watch serial (RFGYC24YEVF) explicitly;
  a bare "first adb device" pick once grabbed the owner's Pixel over USB
  (probe APK was installed to the phone by mistake and uninstalled).
- Next: P1b render_glyphs.py (Blender engraved decals) — probe XML structure
  becomes the real generator's template.

## 2026-07-13 — Session 1 continued (P1b: engraved digits SHIPPED to emulator)

- Owner raised the ambition ceiling ("blow people's minds", buy-anything
  offer). Answer: Blender/Cycles is sufficient; maximalism addendum added to
  the plan (HDRI, tooth-period rotation, arc light-spill, tilt specular
  sweep, maker's mark). HDRI rig live: polyhaven studio_small_08 (CC0) at
  0.30 + single cool key — EVERY asset renders under this identical rig.
- Glyph approach journey (keep for posterity):
  1. cavity decal (extrude+flip): flat black — vertical walls edge-on.
  2. inset_region V-cut: broken geometry — inset returns unreliable on
     text-derived n-gon meshes; do NOT trust its 'faces' output.
  3. WINNER: displacement-engraved plate TILES — dense grid plane, negative
     displacement from a blurred glyph mask (blur width = chamfer slope),
     ColorRamp gates bright-cut steel to genuine slope, eroded mask marks
     the oil-dark floor. A dented lit plate needs no normal surgery.
- Physical insight that unlocked the look: engraving cuts through the bluing
  and exposes BRIGHT raw steel — chamfers are polished (rough 0.28 so the
  micro-faceted cut scatters the key), floor is dark fill.
- 22 glyphs (lg 52x68, sm 32x44) rendered 4x @192 samples, ~20 min
  background. Live on emulator: hh:mm engraved strip + ss small, ambient
  hides seconds. XSD 0-errors.
- NOTE: glyph tiles are OPAQUE plate tiles (not decals) — P2 display wells
  must be designed as flush plate areas matching tile finish.
- Owner clarified vision mid-session: next face (after ARCWRIGHT) = a
  machine that could actually be BUILT (CAD-grade logic, pistons/belts/
  imaginary tech, one fictional fuel source). Banked in memory. ARCWRIGHT
  continues unchanged.
- **Wrist check COMPLETE** (Watch7, 480x480 native): engraved bitmap digits
  render identically to emulator — chamfer glints, dark fill, colon tile,
  ss updates. Watch reconnection recipe that works: owner opens the
  Wireless-debugging screen on the watch (shows "xsyprime@prime currently
  connected"); a background poll loop catches the advertisement within
  seconds and fires install+activate. P1/P1b fully closed.

## 2026-07-14 — Session 2 (P2: full photoreal scene, autonomous overnight run)

- Owner away; instruction "keep cooking". P2 executed end-to-end.
- `scripts/render_layers.py`: 23-asset declarative REGISTRY (--only filter),
  materials v3 (Pointiness edge-wear, AO grime, machining+fine-noise premixed
  into one Bump), displacement engraving reused for bezel numerals, display
  labels, plate maker's mark ("ARCWRIGHT · No.001").
- Material iteration journal:
  1. camera 2x-zoom bug — render() dropped Chronova's radius*2 convention.
  2. brass rendered flat mustard: Pointiness ramp from 0.52 smears wear
     across flat faces (they sit at ~0.5) — ramp must start ~0.56.
  3. HDRI at 0.22-0.30 strength floods ambient (Chronova world was ~black);
     dropped to 0.06 — HDRI is for glints, not illumination.
  4. Softbox bigger than the part = flat metal; restored Chronova's proven
     key/fill/rim trio with a SMALL key (size 2) for crisp speculars.
  5. The unlock: RADIAL brushed tangent (ShaderNodeTangent RADIAL-Z) +
     aniso 0.85 + worn_brass albedo darkened to (0.19,0.115,0.038) —
     circular watch-part sheen appeared immediately.
- `scripts/gen_watchface.py`: Chronova infra carried over (img/rot/parallax
  planes/ANIM map), ARCWRIGHT scene body: 17 animated groups, engraved
  BitmapFont clocks seated in display wells (size 56 fits the 59.5px well),
  4 diagonal conduit housings (dark glass, unlit until P3), arc chamber dark.
- XSD 0-errors; APK 6.5MB; emulator composite verified (engraved bezel
  numerals legible, digits in wells, cohesive dark-industrial read);
  two-frame diff confirms gear + seconds motion.
- Known polish items for next pass: center chamber region muddled over the
  gear stack; display label strips barely legible at final scale; fan reads
  flat; consider per-asset exposure balance in composite.
