# XSYTRANCE Trip — build log

Wear OS watchface (Watch Face Format v2, no code) for Galaxy Watch 7 / Wear OS 6.
Owner: xsytrance. Built with Claude Code, 2026-07-13, entirely while the owner was
remote — emulator loop on the workstation, sideloads via Termux + wireless ADB on
ULTRON (owner's phone).

## Versions

- **v1** — artwork background (vignette crop of the xsytrance character), plain-font
  digital clock, 13 sine-driven EQ bars, two counter-rotating psychedelic rings,
  AMOLED-safe ambient. Verified animating via frame pixel-diff.
- **v2** — clock digits rebuilt as equalizer-bar glyphs (0-9 sliced into vertical bar
  runs), pulsing colon, per-digit shimmer. First WFF `Condition` implementation.
- **v3** — biometrics: bottom EQ bars bounce at live `[HEART_RATE]` (70bpm fallback),
  pixel-LED heart flashes once per heartbeat beside a 3-digit BPM readout, steps as a
  5-digit LED odometer with `[STEP_PERCENT]` goal arc on the rim. Verified on the
  owner's physical Watch 7.
- **v3.1** — readouts recolored: heart rate red, steps amber (pendant hues); goal arc amber.
- **v3.2** — big digits gained the VU-meter gradient (green→yellow→orange→red with
  white peak glints); colon samples the gradient at its height.
- **v4 (current)** — big digits switched to LED dot-matrix cells (same language as the
  character's grin mask), VU gradient retained. Chosen by the owner from an 8-style
  font tasting sheet (`tools/font_tasting.py`).

## Hard-won facts

- `<Compare expression>` must NAME an `<Expression>`; inline comparisons silently
  render nothing (XSD keyref: google/watchface `third_party/wff/specification`).
- `<` inside expression attributes must be `&lt;` — a raw one kills the whole face
  ("not well-formed", runtime falls back to system face).
- Emulator never feeds `[HEART_RATE]`/`[STEP_COUNT]` (synthetic health providers don't
  reach the DWF runtime); real watch works after granting Sensors + Physical activity.
- Set active face: `adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE
  --es operation set-watchface --es watchFaceId com.xsytrance.tripface`.
- Screenshot loop: `KEYCODE_WAKEUP` immediately before `screencap`; face auto-ambients
  in ~15s regardless of `svc power stayon`.

## Banked for watchface #2

Abstract "time as music gear" concepts (owner's request, saved 2026-07-13):
808 sequencer pad grid with per-second playhead sweep, mixer faders, VU needle
meters. Mockups: `tools/concept_mocks.py`, `tools/concepts_sheet.png`.

## Regenerating

`tools/prep_assets.py` (background/rings) → `tools/gen_digits.py` (all digit/icon
PNGs) → `tools/gen_watchface.py` (res/raw/watchface.xml) → `gradle :app:assembleDebug`.
Python needs Pillow only.
