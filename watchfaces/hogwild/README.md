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
| **Radar returns** | `[WEATHER.CHANCE_OF_PRECIPITATION]` painted as PPI echoes, plus a printed percentage on the glass, gated on `[WEATHER.IS_AVAILABLE]` |
| Wheel bank (3h) | `[HEART_RATE]` — the RPM needle carries the rhythm, the wheels carry the number; a green lume twin takes over in ambient |
| Wheel bank (9h) | `[STEP_COUNT]`, in the sub-dial that used to be painted furniture |
| Wheel bank (date) | `[DAY]`, in the old odometer barrel — two wheels, which is what the window has room for |

Each needle sits on a sprite sized to its own sub-dial, so WFF pivots it about
that gauge's centre rather than the dial centre. That is why the boxes in
`engine/face.toml` look arbitrary — they are the 1024-canvas layout anchors
scaled by 480/1024.

## Ambient

A photoreal dial is the worst case for ambient: burn-in and power. So ambient
does not dim the plate, it **replaces** it — the dial goes black and only
engraved outlines and lume survive. On theme, too: night flying by instrument
light.

Steps, date, radar, the needles and the second hand all go dark. Hour,
minute and the heart-rate LCD remain.

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

Verified: WFF v4 validator PASSED (1.3.0-dev).

## 1.3.0 — the readability pass

Three findings from wearing 1.2.0, fixed together
(`tools/hogwild_readability.py` reworks the plates; `engine/face.toml`
rebinds the data):

- **The scope shipped with a painted sweep.** The "hands-free" plate kept a
  frozen sweep wedge and frozen return blips baked into both the day and
  ambient plates, so the live sweep rotated over its own ghost — the HAYATE
  reticle incident, wearing green. The glass is now rebuilt procedurally
  (gradient, range rings, crosshair, seeded grain), and the wedge's spill
  onto the bezel is colour-keyed out and blur-filled, per
  `strip_baked_reticle.py`.
- **The step count was 16px of squint.** The nine-o'clock sub-dial — concept
  furniture with a painted needle bound to nothing — now carries the dial's
  own LCD aperture art and a size-20 step total. The odometer barrel it
  replaced becomes a date window: two digits, which is what it had room for.
- **Heart rate had motion but no number.** The three-o'clock LCD used to
  repeat the time in digits, which the hands already state; it now reads the
  pulse. The RPM needle still shivers at the same rate.

## 1.3.1 — wheels, not phosphor

The 1.3.0 readouts arrived as LCD phosphor: a screen, on a dial whose
design language says instrumentation, never a widget. 1.3.1 replaces the
digits with the `wheel` bitmap font (`tools/make_wheel_font.py`): every
glyph is one wheel of a combination lock — knurled flanks, a
cylindrically-lit drum face, an engraved numeral — so a reading composes
into a wheel bank, per the odometer drum the design language always
specified. Bitmap fonts are alpha masks, so the wheel ships as relief in
the glyph's alpha channel and the steel is the component colour. The scope
percentage stays phosphor: it is printed on a CRT, not machined into one.
WFF cannot roll a drum on a text element — the rotation is a look, not an
animation. In ambient the steel goes dark with the plate and a green lume
twin carries the heart rate.
