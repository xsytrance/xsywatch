# Codex restart handoff — 2026-07-30

## Current device state

- Device: Samsung Galaxy Watch 7, `SM-L310`, 480×480
- Last working wireless-debugging endpoint: `192.168.1.183:36949`
- Active face: **MERIDIAN NIGHTGLASS**
- Nightglass package: `com.xsytrance.meridian.nightglass.dev`
- Meridian Pro remains installed separately as
  `com.xsytrance.meridianpro.dev`

Wireless-debugging ports can change. If `36949` fails, ask for the current
port shown on the watch.

## MERIDIAN NIGHTGLASS

Nightglass is a new, original face built during this session. It is installed,
activated, and verified on the physical Watch 7.

Features:

- Smoked-ceramic night-flight design
- Artificial-horizon center
- Live battery, steps, heart rate, Zulu hour, date, temperature, and rain
- Five editor themes: Sapphire, Radar, Amber, Ice, Stealth
- Battery, Calendar, and heart-rate shortcuts
- Sparse AOD
- Zero permissions and no executable code
- Fully deterministic original raster assets; no AI or external donor art

Important paths:

- Generator: `tools/nightglass/build.py`
- Project: `watchfaces/meridian-nightglass/`
- XML: `watchfaces/meridian-nightglass/app/src/main/res/raw/watchface.xml`
- APK: `watchfaces/meridian-nightglass/app/build/outputs/apk/debug/app-debug.apk`
- Render: `watchfaces/meridian-nightglass/review/FACE_NORMAL.png`
- Tests: `tests/engine/test_meridian_nightglass.py`
- Provenance: `watchfaces/meridian-nightglass/PROVENANCE.md`

Validation completed:

- Official WFF v4 validator: PASS
- Nightglass plus focused engine tests: PASS
- APK metadata:
  - package `com.xsytrance.meridian.nightglass.dev`
  - version `0.1.0-dev`, code 1
  - min SDK 34, target/compile SDK 36
- APK SHA-256 at build time:
  `94327f70259e14067a0b178a32fc53a7212563ec044e59d64de08c71f1fc0067`
- Physical-device normal rendering: PASS
- Five-theme editor exposure: PASS

Activation command used successfully:

```bash
adb -s 192.168.1.183:36949 shell am broadcast \
  -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface \
  --es watchFaceId com.xsytrance.meridian.nightglass.dev
```

The broadcast returned:

`Favorite Id=[48] Runtime=[2]`

## MERIDIAN PRO

Meridian Pro was comprehensively rebuilt earlier in the session and installed.
It now has:

- Flux Kontext Pro finished slate-titanium base
- Corrected moon/subdial and lower-window containment
- Slimmer hands
- Five themes
- Battery, Calendar, and heart-rate shortcuts
- Updated renderer support for configuration colors

Important sources:

- `tools/meridian_pro/build.py`
- `tools/meridian_pro/geometry.py`
- `tools/meridian_pro/plate.py`
- `tools/meridian_pro/typography.py`
- `tools/meridian_pro/kontext_pass.py`
- `tools/render_face_from_xml.py`

Flux artifacts:

- `watchfaces/meridian-pro/review/PRO3-layout.png`
- `watchfaces/meridian-pro/review/PRO3-kontext.png`

## Working-tree caution

The repository already contained unrelated untracked files before this work,
including `assets/`, `previews/attitude-motion-shell/`, and several preview
PNGs. Preserve them. Do not clean or reset the worktree.

The Meridian Pro edits and all Nightglass files are currently local working
tree changes. No commit or push was requested or performed.

Repo-wide validation reports three pre-existing missing-README errors for
`commodore-pro`, `meridian-pro`, and `vector-probe`, plus unrelated warnings.
Nightglass itself introduced no repo-validator error.

## Suggested next action

No work is required to restore the user's current experience: Nightglass is
already active. On restart, inspect this file and `git status` before editing.
If continuing product work, the next meaningful phase is wear testing and
release hardening—not another visual redesign.
