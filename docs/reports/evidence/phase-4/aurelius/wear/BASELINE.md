# Wear-test baseline — objective facts known before wearing

Pre-populated from Phase 3 evidence only. **No subjective judgement here is
the owner's** — every experiential field in `WEAR_LOG.md` is empty until
AGENOR records a session. Phase-4 scope forbids inventing owner
observations.

## What is being worn

| Field | Value | Source |
|---|---|---|
| visual version | `field-tourbillon-mk2-r2` | APPROVAL-0004 |
| APK SHA-256 | `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a` | Phase-3 final review |
| package / version | `com.xsytrance.aurelius` 1.0 (versionCode 1) | `app/build.gradle` |
| device | Galaxy Watch7 44 mm, SM-L310, Android 16 / API 36 | Phase-2 device session |
| signing | debug / sideload | `docs/KNOWN_LIMITATIONS.md` |

## Objective behaviour already established

These are measured or observed facts, not opinions. They exist so the owner
can distinguish "this is how it is designed" from "this is a problem".

### Rendering and layout

- Normal and AOD goldens reproduce byte-for-byte; hero state is 10:09:35,
  day 24, battery 80%, HR 72.
- Date aperture is 40.2 × 30.1 px inner opening at px(322, 300). Every day
  `1..31` clears the frame by ≥ 2 px in both normal and ambient; 62
  deterministic renders, 0 violations, worst margin 3.07 px.
- The aperture measures 40 × 30 px on the physical device, matching the
  reference render.
- The lower `FIELD TOURBILLON Mk II` engraving was removed in r2. The
  restrained `AURELIUS` signature is the only face marking. Physical
  comparison confirmed the removal reads as intentional negative space.
- 60 runtime resources; resource inventory clean.

### Motion

| Layer | Rate | Note |
|---|---|---|
| `z10_gl` gear L | 40 °/s | continuous |
| `z11_gr` gear R | 24 °/s | continuous |
| `z22_cage` seconds cage | 6 °/s | one revolution per minute |
| `z40_sheen` | parallax ±40 px X, ±14 px Y | driven by `ACCELEROMETER_ANGLE_*` |

In ambient, sub-minute sources stop updating and the seconds cage parks at
12 (observed Watch7 behaviour, encoded in `states.toml`).

### Data behaviour

- Heart rate: readings ≤ 30 bpm fall back to a safe 70 bpm value
  (`clamp((HEART_RATE < 30 ? 70 : HEART_RATE), 40, 200)`).
- Reserve gauge: needle sweeps 292.5°–337.5° across 0–100% battery.
- Declared permissions: `BODY_SENSORS`, `ACTIVITY_RECOGNITION`.

### Known device qualifications (not defects)

- **Direct AOD screencapture is unavailable** through the Watch7 doze
  pipeline — repeated captures produce the same black artifact. AOD look
  can only be judged by eye, which is precisely why the wear log asks for
  it.
- **Exact device-screenshot comparison is not a valid gate** for this face:
  continuously rotating layers and accelerometer-driven full-screen sheen
  cannot be pinned at capture time (ADR-009 §6a).
- Reinstalling with `install -r` causes One UI to deactivate the active
  face — documented behaviour, not a fault.
- Battery impact per face is anecdotal, not measured
  (`docs/KNOWN_LIMITATIONS.md`).
- Tested on one device only (Galaxy Watch7 44 mm).

### Phase-3 device matrix result

The r2 candidate passed the physical Watch7 matrix: intended pixels live on
the panel, dynamic date via imported glyphs, concentric pivots, no
fringing, install/upgrade continuity, picker and activation, AOD cycling,
stability. The installed APK was pulled back and hashed, and `bg.png`,
`bg_aod.png` and `res/raw/watchface.xml` extracted from it match repository
source bytes.

The one sub-item the Phase-2/3 record flags as worth an owner wear-day
confirmation: **the 10-minute continuous smoothness row was PASSed on
sampled recordings rather than sustained observation.** That is a good
thing to watch for in the first session.

## Open questions the wear log is meant to answer

Recorded here as questions, not as answers:

1. Does the face still feel premium after days of ordinary use, or does the
   motion become wallpaper?
2. Is AOD bright enough to read at a glance, and dark enough not to annoy
   at night?
3. Is the reserve gauge actually usable as a battery indicator, or merely
   decorative?
4. Does the sheen parallax read as depth on the wrist, or as noise?
5. Does the continuous gear motion ever become distracting or cause
   perceived stutter over a long session?
6. Any accidental interactions, glare, or contrast failures outdoors?
