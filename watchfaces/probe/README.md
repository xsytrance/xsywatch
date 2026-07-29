# MERIDIAN PROBE

A measuring instrument, not a design. Phase 0 of
[`docs/plans/MERIDIAN_PRO_MASTER_PLAN.md`](../../docs/plans/MERIDIAN_PRO_MASTER_PLAN.md).

It exists to be worn while numbers are written down. Everything on it is a raw
source printed as an integer, because the point is to find out what the
platform actually returns — not to look like anything.

```
python3 tools/make_probe_assets.py     # assets + watchface.xml
tools/build_face.sh probe              # debug APK
```

`tools/make_probe_assets.py --check` verifies the committed XML and glyphs
still match the generator. The generator owns both, because the bitmap font is
proportional and every `<Character>` has to declare the width of the glyph
that was actually rendered — splitting that across a generator and a
hand-written spec is how the widths drift.

## What each row is asking

| Row | Reads | The question |
|---|---|---|
| `WX` | `IS_AVAILABLE`, `ERR:IS_ERROR` | is there any weather data at all |
| `COND` | `CONDITION`, `DAY:IS_DAY` | **the integer under decode** |
| — | `CONDITION_NAME` | **the word that names that integer** |
| `TEMP` | `TEMPERATURE`, `HI`, `LO` | today's range |
| `RAIN` | `CHANCE_OF_PRECIPITATION` | the discriminator the collection uses now |
| `UV` | `V4:` doubled prefix, `H0:` forecast spelling | does the doubled prefix resolve |
| `H+0` | `HOURS.0` avail / cond / temp | does the hourly forecast populate |
| `H+3` | `HOURS.3` avail / cond / temp | does it populate *more than one* index |
| `D+1` | `DAYS.1` avail / day cond / night cond | does the daily forecast populate |
| `D+1` | `DAYS.1` hi / lo / precip | and does it carry numbers with it |
| `MOON` | `MOON_PHASE_POSITION` as % | a real source nothing else uses |
| | `SEC:SECOND` | a clock to time any readout's update cadence against |

The needle is a **sun compass** — solar azimuth, 180° at local solar noon,
walking ~15°/hour either side, northern hemisphere assumed. It is the plan's
§7A recommendation, running, so that wearing this answers whether it reads as
an instrument or as a decoration. Clock time stands in for solar time; there
is no longitude source to correct it with, and how wrong that feels is part of
what is being measured.

The complication slot below the hairline is expected to **fail** its purpose.
A face cannot read a complication's value — the format exposes only
`COMPLICATION.RANGED_VALUE_COLOR_INTERPOLATE` and
`COMPLICATION.WEIGHTED_ELEMENTS_COLORS`, both colour weights rather than
numbers — so no provider can drive that needle. The slot is carried to settle
it on hardware. It defaults to `WATCH_BATTERY` as a `RANGED_VALUE` so that a
populated box proves the slot works and an empty one means something else is
wrong.

## Recording what it says

Write observations into [`CONDITION_LOG.md`](CONDITION_LOG.md). One line per
distinct `CONDITION_NAME` seen. The decode is done when the interesting
weather has been seen at least once each; it does not need to be complete for
any of the rest of MERIDIAN PRO to proceed.

## Caveats worth keeping

- **A validator PASS is not evidence a source exists.** Verified directly:
  swapping `[WEATHER.HOURS.0.CONDITION]` for `[WEATHER.HOURS.0.NONSENSE]`
  still passes validation at v4. The validator schema-checks elements and
  attributes and does not resolve source names inside expressions. So this
  face validating cleanly says nothing about the forecast — only wearing it
  does.
- **Authored at v4, not v5.** Every source it needs exists at v4, and v4 is
  proven on the Watch 7 while v5 is not. Confirming v5 installs and renders
  is a separate probe and a phase 1 gate.
- **Zero permissions.** It reads weather, moon phase and the clock, all of
  which the runtime supplies without one, and deliberately displays no heart
  rate or step count.
- **AOD is a single dim clock.** This face is meant to be worn for weeks, and
  a screen of static bright text at fixed positions is a burn-in pattern.
