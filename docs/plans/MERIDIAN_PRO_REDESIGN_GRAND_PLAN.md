# MERIDIAN PRO — the redesign. Grand plan.

Supersedes the layered-window plan as the **primary direction**, from the
owner's concept sheet of 2026-07-29 (`previews/MERIDIAN_PRO_CONCEPT.png`).

The concept is a **machined instrument panel**: bezel with lume indices,
milled centre plate, a battery power arc, two ringed sub-dials, a framed
three-field date, moon phase, and five colour themes.

---

## 0. Why this pivot is worth making, beyond looking better

The whole collection is blocked from shipping because its art is AI-generated
(`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md`). Every previous attempt to fix
that meant *redoing* work.

**This concept is drawable.** There is no photograph in it and nothing that
needs a model — it is metal, arcs, type and shadow. Built the way section 1
describes, **MERIDIAN PRO is original by construction from the first commit**,
and the provenance problem stops being a debt to pay off and becomes a
property of the design.

That is the strategic argument. The visual argument is that it is simply the
better watch.

---

## 1. The discovery that makes it possible: `PartDraw`

Checked in the validator XSDs, not recalled. **Watch Face Format can draw
vector shapes natively**, at v3, v4 and v5:

| Shapes | Styles | Gradients |
|---|---|---|
| `Arc`, `Ellipse`, `Line`, `Rectangle`, `RoundRectangle` | `Stroke`, `WeightedStroke`, `Fill` | `LinearGradient`, `RadialGradient`, **`SweepGradient`** |

Two attributes matter more than the rest.

**`WeightedStroke` takes a list of colours and a list of weights** —
`colors="#2F7A66 #C89A3C #B8402F" weights="5.0 3.0 2.0"` — and draws them as
proportions along the stroke. That is *exactly* the green/amber/red zone ring
in the concept, in one element, with no artwork at all.

**`Arc` accepts `<Transform>` children**, and `Transform`'s value is an
arithmetic expression. So `target="endAngle"` driven by `[BATTERY_PERCENT]`
gives a **progress arc that sweeps with live data**.

Verified by composing them and validating:

```xml
<PartDraw name="progress" x="0" y="0" width="480" height="480">
  <Arc centerX="240" centerY="240" width="170" height="170"
       startAngle="-120" endAngle="120">
    <Stroke color="#EBC468" thickness="8" cap="ROUND" />
    <Transform target="endAngle"
               value="-120 + 240 * clamp([BATTERY_PERCENT], 0, 100) / 100" />
  </Arc>
</PartDraw>
```

→ **PASSED at v4.** (Caveat, as always in this repo: the validator checks
elements and attributes properly, unlike source names inside expressions —
so this is real structural evidence, but it still needs one device check
before the plan leans its whole weight on it. That is phase 1.)

### What follows from it

- **Every ring, arc and zone in the concept is vector.** No sprite sheets, no
  pre-rendered arcs, no per-value frames.
- **Provenance-clean by construction.** Nothing generated, nothing traced.
- **Resolution-independent** — 480 and 432 from one source.
- **Theming becomes trivial**: a colour is an attribute, so five themes are
  five values, not five asset sets.
- **Smaller and cheaper.** The current PRO APK is 3.6 MB, most of it PNG.

This is the single biggest capability this project has found, and nothing in
the collection uses it.

---

## 2. Feature audit — what the concept promises, and what the platform allows

Every row checked against the schema. **The honest ones first: three features
as drawn cannot be built.**

### 2a. Cannot be done as drawn

**Sunrise / sunset (`5:42 AM` / `8:12 PM`)** — there is **no sunrise, sunset,
dawn, dusk, latitude, longitude or location source at any format version**.
Nor can it be computed: solar times need a position, and the platform exposes
none. The only route is the `SUNRISE_SUNSET` *complication*, which the
provider renders inside its slot in the system font — and a complication's
value cannot be read by the face (§7 of the earlier plan). So those two
beautifully framed windows cannot contain real sunrise and sunset in our own
type.

> **Recommendation: replace them, do not fake them.** The same two windows
> can hold things we genuinely have and the concept lacks: **`WEATHER`
> temperature and precipitation chance**, or **`BATTERY_TEMPERATURE_CELSIUS`
> and a charge-time estimate**. Same frames, same balance, real data. See
> decision 1.

**Tap to cycle metrics (Steps → Floors → Cal → Active Time)** — a face ships
`hasCode="false"` and the format has **no persistent state**. `AnimationController
play="TAP"` can run an animation on touch; it cannot latch a mode that
survives the next frame. So a tap cannot change what a dial displays.

> The achievable version is `UserConfiguration` — the wearer picks the metric
> **once, in the watch face editor**, and it stays. Not a tap, but it is real
> customisation and it is what the format is built for.

**Floors, Calories, Active Time** — the only health sources that exist are
`STEP_COUNT`, `STEP_GOAL`, `STEP_PERCENT`, `HEART_RATE`, `HEART_RATE_Z`.
There is no calorie, floor, distance or active-minutes source. Those need
complications, with the styling loss that implies.

### 2b. Achievable, and two are better than the concept knew

| Concept feature | Mechanism | Notes |
|---|---|---|
| Power arc, zones, smooth sweep | `Arc` + `WeightedStroke` + `Transform endAngle` | native vector |
| **Charging indicator** | **`BATTERY_CHARGING_STATUS`** | real source — the bolt can genuinely light on charge |
| Battery % large | `BATTERY_PERCENT` | |
| Steps ring + `/10000` | `STEP_PERCENT`, `STEP_COUNT`, **`STEP_GOAL`** | **`STEP_GOAL` is a real source: the goal shown is the wearer's own, not a hardcoded 10000** |
| Heart rate + zone colour | `HEART_RATE` driving `WeightedStroke` | zones as in the AN grammar |
| Date `WED 27 MAY` | `DAY_OF_WEEK_S` + `DAY` + `MONTH_S` | all three are real sources; no compromise |
| Military 24H time | `HOUR_0_23` | |
| Moon phase + day/night | `MOON_PHASE_POSITION`, `MOON_PHASE_TYPE` | first use in the collection |
| Applied indices with lume | procedural sprites | |
| Multi-layer machined depth | procedural sprites + vector | the provenance win |
| Colour themes ×5 | `ColorConfiguration` + `ListConfiguration` + `Flavor` | `Flavor` bundles a whole preset |
| Ambient + AOD modes | `Variant mode="AMBIENT"` | already the house pattern |
| Battery efficient | vector over bitmap | fewer, smaller assets |

**Bonus the concept does not mention, and should have:** `BATTERY_IS_LOW`. A
fuel gauge that turns its own warning on is better than one that just points
at a red band.

---

## 3. What carries over from the work already done

The pivot does not discard the last two days.

- **The AN instrument grammar** (`docs/plans/AIRCRAFT_INSTRUMENT_GRAMMAR.md`)
  is the design language for every dial in the concept — graduations, zone
  arcs, spade and blade pointers, luminous index, counter windows. The
  concept is that grammar, drawn better.
- **The two-pass halo readout** — numbers drawn as four diagonal passes plus
  a cast shadow, because a BitmapFont is tinted flat and a single `PartText`
  cannot have depth. Still true, still needed.
- **`shade()`** — translucent work must be composited, never stamped, because
  `ImageDraw` replaces alpha. Every procedural sprite depends on this.
- **Barlow Condensed** and the sampled palette.
- **The renderer**, now that it honours `tintColor`, evaluates `Condition`
  branches and applies `<Gyro>`. It will need `PartDraw` support next.
- **The procedural window layers** — the banking horizon is a candidate for
  the moon-phase well or a future ATTITUDE variant of this face.

What is retired: nothing is deleted. COMMODORE PRO 0.8.0 stays as the last
build of the layered-window line, for comparison on the wrist.

---

## 4. Architecture

```
tools/
  meridian_pro/
    __init__.py
    geometry.py     one source of truth for every centre, radius and box
    plate.py        procedural sprites: bezel, indices, milled centre, wells
    vector.py       the PartDraw layer — arcs, rings, gradients
    typography.py   Barlow glyph sets + the halo readout emitter
    themes.py       the five palettes and the UserConfiguration block
    build.py        assembles watchface.xml and the drawables
watchfaces/meridian-pro/
```

Three rules, each of which has already been learned the hard way here:

1. **`geometry.py` is the only place a coordinate is written.** Every drift
   bug this week came from two copies of a number.
2. **Measure the art, never the bounding box.** The 61px sub-dials and the
   off-centre date both came from trusting a rectangle.
3. **One unproven construct per build.** A face that fails to inflate is a
   black screen with no error.

---

## 5. Phases

| # | Work | Gate |
|---|---|---|
| **0** | **`PartDraw` device probe** — one tiny face: a weighted-stroke zone arc, a `Transform endAngle` progress arc, a sweep gradient. Nothing else. | **renders on the Watch 7** |
| 1 | `geometry.py` + the bezel: ring, minute numerals, applied indices, lume | contact sheet |
| 2 | Milled centre plate, wells, screws, layered shadow | contact sheet |
| 3 | The vector layer: power arc, steps ring, HR ring, all live | validator + render |
| 4 | Readouts: battery, steps + goal, BPM, three-field date, 24H | legibility review at 1× |
| 5 | Moon phase well, and whatever replaces sunrise/sunset (decision 1) | render |
| 6 | Hands, centre boss, lume, AOD + Ambient variants | on the wrist |
| 7 | Five themes via `Flavor` + `ColorConfiguration` | all five in the editor |
| 8 | Renderer gains `PartDraw`; review gate; footprint; APK | five-mode sheet |

**Phase 0 is not optional and is half a day.** The entire plan rests on
`PartDraw` rendering on this hardware, and the probe went black once already
by carrying a dozen unknowns at once. One construct, one build, one answer.

---

## 6. Decisions for the owner

Three, in the order they block work. Recommendations given so none of these
needs more than a yes.

**1. The two small windows — what goes in them?** Sunrise/sunset is
impossible (§2a). *Recommendation: weather — temperature and precipitation
chance.* It is live, it is already wired on five faces, and it keeps the
frames exactly as drawn.

**2. Does the metric dial stay steps-only, or become configurable?** Tapping
cannot cycle it. *Recommendation: steps only for v1*, since `STEP_GOAL` makes
it genuinely good, and add a `ListConfiguration` later if it is missed.

**3. Is this a new face or COMMODORE PRO's next version?** *Recommendation: a
new face, `meridian-pro`.* It shares no artwork with COMMODORE, it is
provenance-clean where COMMODORE is not, and keeping COMMODORE PRO installable
is the only way to judge the pivot on the wrist.
