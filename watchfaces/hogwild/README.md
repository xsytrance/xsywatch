# MERIDIAN HOG-WILD

An A-10 Thunderbolt II cockpit panel. Machined titanium, engraved legends,
recessed aircraft instruments, and a green radar scope.

**Development build.** Debug signing, package namespaced `.dev`, no release
configuration. The dial plate is AI-generated concept art — see
[`PROVENANCE.md`](PROVENANCE.md) before doing anything with this.

| | |
|---|---|
| Package | `com.xsytrance.hogwild.dev` |
| Version | `0.1.0-dev` (versionCode 1) |
| Aircraft | Fairchild Republic A-10 Thunderbolt II |
| Dial mark | A-10 WARTHOG / "HOG-WILD" / MERIDIAN |
| Format | WFF v4, 480×480 |

## What moves

The concept image had every needle and hand painted into the picture. A watch
face cannot do that, so the plate was regenerated **hands-free** and each
moving part became its own layer:

| Layer | Bound to |
|---|---|
| Hour, minute | time — each carries a baked drop shadow, because WFF cannot cast one and a hand with no shadow is the strongest tell that a dial is fake |
| Second | time |
| **Fuel gauge needle** | `[BATTERY_PERCENT]`, sweeping E→F across the gauge's 250° |
| **RPM needle** | `[HEART_RATE]`, oscillating |
| **Radar sweep** | elapsed time, four seconds per revolution |
| LCD aperture | live digital time |
| Odometer aperture | `[STEP_COUNT]` |

Each needle sits on a sprite sized to its own sub-dial, so WFF pivots it about
that gauge's centre rather than the dial centre. That is why the boxes in
`engine/face.toml` look arbitrary — they are the 1024-canvas layout anchors
scaled by 480/1024.

## Ambient

A photoreal dial is the worst case for ambient: burn-in and power. So ambient
does not dim the plate, it **replaces** it — the dial goes black and only
engraved outlines and lume survive. On theme, too: night flying by instrument
light.

Steps, radar, the needles and the second hand all go dark. Hour, minute and
the digital time remain.

## Design rules this face follows

From the studio's `roadmap/DESIGN_LANGUAGE.md`:

- The dial is the aircraft's skin, not a picture of an aircraft.
- **Nothing floats.** Every legend is engraved into the metal with a shadowed
  upper edge and a lit lower lip. The odometer is a slot cut through the gauge
  face with a metal lip and drum-curved digits. Markers are applied and cast
  contact shadows.
- **Data is instrumentation, never a widget.** Battery is a fuel gauge, steps
  a counter dial, heart rate a tachometer. Never a pill.

## Build

```bash
python3 tools/generate_face.py hogwild
bash tools/wff_validate.sh 4 watchfaces/hogwild/app/src/main/res/raw/watchface.xml
bash tools/build_face.sh hogwild
```

Verified: WFF v4 validator PASSED, APK 3,238,009 bytes,
`sha256 8c59c1323747dda46c2b369f93a6dc0e4c9a1459d81ab239c8bd1985c045b19d`.
