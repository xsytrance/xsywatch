# ATTITUDE — MERIDIAN (development)

A premium aviation instrument: satin titanium case, dark rhodium dial,
applied indices with lume, and a low circular artificial-horizon aperture
that reacts to the wrist.

**This is a development build, not a release candidate.** Debug signing only,
no bundle, no store metadata, no release channel. The application ID is
namespaced `.dev` so it cannot collide with or be mistaken for a shipped
package.

| | |
|---|---|
| Package | `com.xsytrance.attitude.meridian.dev` |
| Version | `0.1.0-dev` (versionCode 1) |
| Format | Watch Face Format v4, `ANALOG` |
| Canvas | 480 × 480 |
| Permissions | `BODY_SENSORS`, `ACTIVITY_RECOGNITION` |

## What is on the dial

Analog hour and minute baton hands over a refined pinion, with a slim
seconds hand in normal mode. Twelve applied indices — four cardinal, the
rest secondary — with the six o'clock position given over to the horizon
aperture. An integrated power-reserve arc in the upper annulus, a date
window at three, steps at eight and heart rate at four, and a restrained
AGENOR / MERIDIAN signature.

All four readouts bind live WFF sources: `[DAY]`, `[BATTERY_PERCENT]`,
`[STEP_COUNT]`, `[HEART_RATE]`. None of them substitutes a plausible number
when a sensor is absent or unpermitted — the reading simply shows 0, which
is the project's established fail-safe and the honest one.

## The artificial horizon

The horizon is an oversized field (252 px) drawn *below* the dial plate.
The plate is opaque everywhere except the aperture, so what you see is a
horizon through a porthole. WFF has no mask primitive for `PartImage`;
occlusion is the mechanism, and the plate's full-canvas opacity is load
bearing rather than incidental.

Roll gain is applied negated, so the field counter-rotates and the horizon
appears to stay level as the wrist turns. Pitch translates the field
vertically.

### Changing the motion profile

The motion contract lives in exactly one place — the `z00_horizon`
component in `engine/face.toml`:

| profile | roll | pitch |
|---|---|---|
| `damped` | ±14° | ±14 px |
| **`proposed`** | **±22°** | **±26 px** |
| `assertive` | ±30° | ±34 px |
| `roll-only` | ±22° | 0 px |
| `static` | 0° | 0 px |

`proposed` is the **provisional** development default. When the formal
Watch7 session settles the question, edit `roll_gain_deg` / `pitch_gain_px`
and regenerate. No artwork, layout or resource change is needed; a test
asserts that swapping profiles disturbs nothing but the horizon layer.

## Always-on

AOD is a genuinely separate composition, not a dimmed copy: outlined
indices, no reserve scale, no sub-dials, no machining or reflections, no
seconds animation, and only date and battery retained.

Neutral horizon behaviour in ambient is **structural**, not damped. The
moving field is hidden at ambient alpha 0 and a frozen field replaces it, so
there is no sensor-driven transform on any layer that ambient can see. A
hidden layer cannot move.

Development metric: 1.45 % bright pixels (BT.601 luma > 40) against the
Phase 1 MERIDIAN concept's 12.99 %. This is a development measurement, not a
WO-P7 certification claim.

## Working on it

```bash
# artwork authority is the studio repo; import and hash-record its export
python3 watchfaces/attitude-meridian/tools/import_studio_export.py

# regenerate the committed XML from the spec
python3 tools/generate_face.py attitude-meridian

# review images rendered from the committed XML and the real drawables
python3 watchfaces/attitude-meridian/tools/render_from_xml.py

# gates
tools/wff_validate.sh 4 watchfaces/attitude-meridian/app/src/main/res/raw/watchface.xml
python3 -m unittest tests.engine.test_attitude_meridian
tools/build_face.sh attitude-meridian
```

Do not hand-edit `res/drawable` or `res/raw/watchface.xml`. Both are
generated, and both are checked.
