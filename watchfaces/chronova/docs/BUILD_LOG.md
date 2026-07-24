# CHRONOVA build log

## 2026-07-13 — Session 1 (Phases 0-4 core)

- **P0 environment**: Java 25 (mise), Gradle 9.6.1, AGP 9.2.1, FFmpeg 8.0.1,
  Pillow + numpy in session venv. **Blender: not installed** — procedural pass
  done in PIL/numpy instead; Blender remains the upgrade path for photoreal
  layers. No `cwebp` binary (FFmpeg covers WebP later). ADB: Wear OS 6 emulator
  `emulator-5554` (API 36, 384x384 @320dpi). Physical Watch7 44mm (480x480) is
  with the owner, remote — sideload path is Termux + wireless ADB on ULTRON.
- **P1 skeleton**: WFF **version 4** accepted by runtime; custom TTF (Orbitron)
  renders via `Font family="orbitron"`. Live hh/mm/ss in reference layout
  verified on emulator.
- **P2 art**: 35 deterministic procedural assets (gears with real involute-ish
  teeth, brushed plates, bolted reactor rings, glass conduits, display panels,
  exact 60-position outer scale — reference's AI-garbled numbering corrected by
  construction). One fix: core lattice filaments clipped to orb.
- **P3 motion**: 27 independently animated groups (see ANIMATION_MAP.md):
  meshed counter-rotation with tooth-ratio speeds, 1/sec stepped ratchet,
  eccentric cam (pivot 0.42), antiphase piston pair, pause-reverse-resume
  hunting gear, hour/minute indexing rings, staggered conduit packets, turbine.
  Verified by frame pixel-diff (mean ~3.5 across mechanical area).
- **P4 reactor**: 4s breathing bloom+core, counter-rotating containment rings
  (60s CW / 40s CCW), 6s outward pulse ring, sub-1s minute-boundary surge.
- **Ambient**: pass-1 variant dimming — glows/packets/conduits/seconds hidden,
  structure at alpha 45, hh/mm readable. Designed AOD still to come (P8).
- **Validation**: XML well-formed; no DWF errors in logcat (only benign
  FrameTimer resets); install + activation broadcast OK; ambient verified.
- **Known cosmetic debts**: conduit strands still slightly wavy at small sizes;
  reactor interior shows rear-gear brass through ring gaps (kept — reads as
  depth); glints layer not yet built.

### Failures hit and fixed this session
- (from sibling project, applied preemptively) `&lt;` escaping in expressions;
  Compare-must-name-Expression. No new red builds in this session.

## 2026-07-13 — Session 1b (photoreal pass, owner-authorized tooling install)

- Installed **Blender 4.5.11 LTS** portable to `~/Android/blender/` (user-owned,
  no system packages touched; 4.5 LTS chosen over 5.x for bpy API stability).
  Headless Cycles CPU smoke test passed.
- `scripts/render_blender_layers.py`: 17 metal components rebuilt as real 3D —
  gear outlines extruded+beveled from the same tooth math as the PIL pass,
  boolean spoke cutouts, torus bearings, brass screw rings with slots, 3-area-
  light rig, anisotropic metal with machining-mark bump, transparent ortho
  renders at 2x, auto-copied over the PIL baselines.
- **Iteration 1 failures (fixed):** chassis bridges rendered as diamond
  lozenges (4-vert cylinder ≠ cube) and 2x too wide; fan blades floated off
  the hub; ratchet teeth too aggressive; ring-bump texture caused moire
  banding on large flats; scene too bright/silver vs reference.
- **Materials v2:** bump 0.35→0.08 + finer scale + noise break-up (moire gone),
  world 0.6→0.25 + key 900→520 (void-black restored), bridge width corrected.
  Full 17-asset re-render, rebuilt, emulator-verified.
- Result: photoreal metal pass live; emissive layers intentionally remain
  procedural PIL (glow needs no photorealism). APK rebuilt and shipped.

## 2026-07-13 — Session 1c (digit centering fix, owner-reported)

- Owner spotted hh/mm digits sitting low in their glass windows. Pixel-measured
  from screenshot: digits ~21px low (text-box center y=271 vs window center
  248.6) — WFF TimeText centers vertically within its box, boxes were misplaced.
  Moved hh/mm boxes y 238->216, sec y 398->388. Post-fix measurement: centered
  within 1px on both axes. Lesson: position TimeText boxes so box center ==
  target center; verify with pixel measurement, not eyeballing.

## 2026-07-13 — Session 2 (P5: gyro parallax + tap surge + ignite)

- **Interrupted by a workstation freeze** right after the APK build; this entry
  written on recovery. All work products survived intact on disk (verified:
  17 photoreal metals pixel-identical to HEAD, WebPs valid, APK XML in sync).
- **Gyro parallax**: `plane=` param on `img()`/`rot()` adds wrist-tilt x/y
  offsets from `clamp([ACCELEROMETER_ANGLE_X/Y], -45, 45) / 45`. Depth ladder:
  plate 2, rear gears 3, chassis/ring60 5, quadrant gears/conduits/sleeves 7,
  turbine/reactor housing/outer ring 8, inner ring/core/bloom 9, new
  foreground `glints.png` 14. Verified on emulator by driving the virtual
  accelerometer ±45°: plane-7 sleeve shifted 12px (expected 11.2 at 0.8
  screen scale), plane-8 turbine 13px (expected 12.8), plane-0 displays 0px.
- **Frame-sequence effects** (`scripts/build_webp_sequences.py`, FFmpeg
  libwebp yuva420p): `surge.webp` (18f @ 12fps, TAP trigger — rings contract,
  core fires 6 spokes) and `ignite.webp` (same timing, ON_VISIBLE — ring
  sweep-in, core ignition). Emitted as `PartAnimatedImage` +
  `AnimationController play="TAP|ON_VISIBLE" beforePlaying/afterPlaying=HIDE`.
  Both verified playing on emulator (tap capture + wake capture).
- **Schema validation**: full watchface.xml now validates 0-errors against the
  official WFF v4 XSD (google/watchface, XSD 1.1 via python `xmlschema`;
  libxml2/xmllint can't parse these schemas). PartAnimatedImage,
  AnimationController attrs, TAP/ON_VISIBLE triggers, WEBP format and
  ACCELEROMETER_ANGLE_X/Y sources all confirmed against the spec — no
  invented tags. Fixed the one pre-existing violation: `name` attribute is
  not allowed on `DigitalClock` (dropped from generator; runtime tolerated
  it, but now schema-clean).
- 30 animated groups total (was 27). Ambient re-verified: dim variants + SEC
  hidden; parallax freezes in ambient (accelerometer stops updating) which
  reads as intended static AOD behavior — revisit only if P8 designed AOD
  changes the story.
- Docs regression fixed: `generate_assets.py` rewrites ASSET_MAP.md and had
  erased the hand-added photoreal-overrides note; the script now emits that
  section (plus the WebP table) itself.

## 2026-07-13 — Session 3 (electrical pass, owner-requested)

- Owner feedback on v0.2: "more electrical, especially the 4 diagonal waves."
- **Lightning arcs**: 4 new sprites (`bolt_{blue,magenta}_{a,b}`, 150x46,
  jagged 16-elbow path + forked branches + white-hot core) overlaid on the
  diagonal conduits. Burst logic in expressions only: phase `(T+off) % per`
  opens a 0.55s window (periods 2.3/2.9/3.4/3.7s so corners never sync),
  shapes A/B alternate at 10Hz via `floor(ph*10) % 2`, brightness jitters
  with `rand(0, 105)` — rand and `%` confirmed in the v4 XSD grammar and
  accepted by the runtime.
- **Diagonal sparks**: 4 packet() runs zip outward along the diagonals
  (0.7-0.85s travel, faster than the display packets = electric feel).
- **Neon arc hum**: side arcs' alpha now beats with products of
  incommensurate sines (8.3x2.9 / 7.1x3.3 rad/s) — irregular electrical
  shimmer instead of static glow.
- 40 animated groups (was 30). watchface.xml still validates 0-errors vs the
  v4 XSD. Emulator-verified via 8-frame capture: bolts change shape between
  frames, bursts stagger per corner, sparks caught mid-flight. Bolt art
  iteration 1 was too chunky (thick zigzag tube); fixed with thinner strokes,
  more elbows, alternating jag polarity, brighter core.
