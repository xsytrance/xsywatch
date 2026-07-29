# MERIDIAN PRO — master plan

A second line alongside the five existing faces, not a replacement. HAYATE,
BALSA, COMMODORE, PURE and HOG-WILD stay exactly as they are at 1.4.0 /
1.3.0 / 1.2.0. PRO ships as separate packages (`com.xsytrance.<slug>.pro.dev`)
in `watchfaces/<slug>-pro/`, so both lines can sit on the wrist together and
be compared.

---

## 1. Three hard limits, verified against the schema

Checked in Google's validator XSDs for **every** format version 1–5, not
recalled.

**There is no compass, and there cannot be one.** `sourceType.xsd` contains no
magnetometer, bearing, azimuth, heading, orientation, latitude, longitude or
location source at any version. `sensorSourceType` declares exactly eight
tokens and all eight are accelerometer. This is not a gap in our engine — the
platform does not expose it.

It is also physics, not just API: an accelerometer measures gravity. Gravity
tells you roll and pitch. It cannot tell you which way you are *facing*,
because rotating about the gravity vector does not change what the sensor
reads. Even a perfect implementation could not recover heading. Section 7 is
what we can do instead, and one of the options is a genuine navigational
instrument rather than a decoration.

**There IS a weather forecast, and this document previously said there was
not.** An earlier revision of this section claimed no `HOURS.<n>` and no
`DAYS.<n>` family, and "corrected" `roadmap/RESUME_HERE.md` and the project
memory on that basis. **That correction was wrong and is withdrawn — the
original memory was right.**

The forecast sources are declared as `xs:pattern` entries, not
`xs:enumeration` tokens, which is exactly why a token search missed them.
`weatherSourceType` is a *union*:

```xml
<xs:simpleType name="weatherSourceType">
  <xs:union memberTypes="_weatherSourceEnums _weatherSourcePatterns"/>
</xs:simpleType>
```

`_weatherSourcePatterns` carries sixteen entries, present at **v4 and v5**
(and absent at v1–v3):

| Hourly — `WEATHER.HOURS.<n>.` | Daily — `WEATHER.DAYS.<n>.` |
|---|---|
| `IS_AVAILABLE` | `IS_AVAILABLE` |
| `CONDITION` | `CONDITION_DAY` / `CONDITION_NIGHT` |
| `CONDITION_NAME` | `CONDITION_DAY_NAME` / `CONDITION_NIGHT_NAME` |
| `IS_DAY` | `TEMPERATURE_HIGH` / `TEMPERATURE_LOW` |
| `TEMPERATURE` | `CHANCE_OF_PRECIPITATION` / `..._NIGHT` |
| `UV_INDEX` | `UV_INDEX` |

Three consequences, none of them small:

- A **genuine forecast instrument** is possible — a strip or sub-dial reading
  the next few hours, which is a far better use of a sub-dial than another
  decorative counter.
- The schema does not say **how many** indices are populated, nor what happens
  when you ask for one that is not. `IS_AVAILABLE` exists per index, which
  implies the answer is "ask it". Phase 0 measures this.
- Every one of these carries the same undecoded `CONDITION` integer, so the
  decode below pays for the forecast too.

**Two lessons worth keeping.**

*Grep the enumerations and the patterns.* A union type hides half of itself
from either search alone.

*A validator PASS is not evidence a source exists.* Tested directly: replacing
`[WEATHER.HOURS.0.CONDITION]` with `[WEATHER.HOURS.0.NONSENSE]` still passes
validation at v4. The validator schema-checks elements and attributes but does
not resolve source names inside expressions — `arithmeticExpressionType` is an
unconstrained string as far as expression *contents* go. So the probe's clean
validation run says nothing about the forecast, and neither would any other
face's. **The XSD declaring these sources tells us the format defines them; it
does not tell us the provider on the Watch 7 populates them.** Only wearing
the probe does. This is precisely why phase 0 is a wear task and not a
desk task.

**`WEATHER.CONDITION` is still undocumented at v5.** The source exists and
returns an integer; the schema documents none of its values. Branching on it
is guessing. Section 3 says how we stop guessing.

### One thing that got better

`WEATHER.UV_INDEX` and `WEATHER.LAST_UPDATED` are spelled
`WEATHER.WEATHER.UV_INDEX` and `WEATHER.WEATHER.LAST_UPDATED` in v4 — a
doubled prefix that looks like a schema typo and makes them awkward to trust.
**v5 fixes both.** These are the only two sources v5 adds over v4.

That is reason to author PRO at **watch face format v5** — but a weaker one
than it first looked, for two reasons. `WEATHER.HOURS.<n>.UV_INDEX` is spelled
*cleanly at v4*, so the doubled prefix afflicts only the current-conditions
reading and there is already a sane way to get a UV number out of v4. And
nothing in the collection has ever been built at v5, so **v5 is unproven on
the Watch 7** while v4 is on the wrist and working.

Ruling: **PROBE is authored at v4** — it has to run today, and it costs
nothing, since every source it needs exists at v4. It reads *both* UV
spellings side by side, so whether the doubled prefix actually resolves at
runtime becomes a measurement rather than a worry. PRO moves to v5 in phase 1
only once the probe has confirmed v5 installs and renders on the device.

---

## 2. Answering the standing question: is tilt in?

Yes, shipped and on the wrist now — but not evenly, and the reason matters
for PRO.

| Face | What responds to the wrist | Gain |
|---|---|---|
| HAYATE | the whole viewfinder — scene, weather and all | roll 24°, pitch 20px |
| BALSA / COMMODORE / PURE | the weather over the glass only | roll 7°, shift 6/8px |
| HOG-WILD | radar returns | roll 5°, shift 4/6px |

All of it goes through the format's `<Gyro>` element and every axis is
guarded by `ACCELEROMETER_IS_SUPPORTED`, so a watch without the sensor sits at
the neutral pose instead of being permanently offset.

**Why three of them barely move.** Their aircraft symbol and pitch ladder are
generated into the *same image* as the sky and ground. On a real attitude
indicator the symbol is fixed to the airframe and the horizon moves behind it,
so rolling that image as one layer swings the aeroplane and leaves the world
level — the instrument read backwards. High-pass separation of the two was
tried and is not reliable enough to ship.

**PRO fixes this by construction**, because it builds the window from separate
layers in the first place (section 4). That is the single strongest argument
for the new line: it is the only way those three ever get a horizon that
actually banks.

The engine also gained the raw `ACCELEROMETER_X/Y/Z` axes — the ones that
sense the watch being *moved* rather than tilted. Nothing uses them yet
because their units are undocumented and need a device check. PRO is where
they earn their place (section 6, "jolt").

---

## 3. The weather gamut, and how we get the whole of it

### The discriminators we actually have

`IS_DAY`, `CHANCE_OF_PRECIPITATION` (0–100), `TEMPERATURE`,
`TEMPERATURE_HIGH`/`LOW`, `UV_INDEX` (v5 spelling; v4 has it doubled), and
`CONDITION` (undecoded) — **plus the whole hourly and daily forecast family
at both v4 and v5**, which the previous revision of this plan wrongly denied.

Precipitation *chance* is not intensity, and that is worth being honest about:
a 95% chance of light drizzle reads the same to us as a 95% chance of a
downpour. Combining it with UV and temperature gets most of the way, and
`CONDITION` closes the gap once decoded.

### Phase 0 — decode `CONDITION` empirically

Before any art, build a throwaway dev face, **MERIDIAN PROBE**, that displays
raw `CONDITION`, `CONDITION_NAME`, temperature, precipitation chance, UV and
`IS_DAY` as plain text. Wear it. Note the integer that appears next to each
name over a couple of weeks of varied weather.

Because it is already an instrument, it answers three more questions for
free — each of which would otherwise be discovered the expensive way, halfway
through building a face on top of it:

- **Does the forecast return anything?** `HOURS.0` and `HOURS.3` are shown
  next to their `IS_AVAILABLE` flags, and `DAYS.1`'s day/night split beside
  its own. If the provider populates one index and not the next, the probe
  says so before a forecast dial is designed around it.
- **Does the v4 doubled prefix resolve?** `WEATHER.WEATHER.UV_INDEX` sits
  directly above `WEATHER.HOURS.0.UV_INDEX`. Two numbers, one glance.
- **Can a complication feed a needle at all?** Almost certainly not — see
  §7 — but the slot costs four lines, so the probe carries one and settles it.

`CONDITION_NAME` is a *string* source, so it cannot be branched on — but it
can be read off the wrist, which is precisely how we map the integers we
*can* branch on. This is the only honest route to fog, mist, thunder, hail and
sleet, none of which are derivable from the numeric sources.

Everything below is designed to work **without** the decode, and to get
sharper with it.

### The state ladder

Tested most-specific-first, since WFF renders the first matching `Compare`.

**Night** (`IS_DAY == 0`)

| # | State | Test |
|---|---|---|
| 1 | Clear night | precip < 15 |
| 2 | Cloudy night | precip 15–50 |
| 3 | Snow night | precip ≥ 50, temp ≤ 2 |
| 4 | Rain night | precip ≥ 50 |

**Day**

| # | State | Test |
|---|---|---|
| 5 | Scorching | temp ≥ 32 |
| 6 | Blazing | UV ≥ 8, precip < 15 |
| 7 | Sunny | precip < 12 |
| 8 | Hazy | precip 12–25 |
| 9 | Cloudy | precip 25–40 |
| 10 | Very cloudy | precip 40–55 |
| 11 | Overcast | precip 55–65 |
| 12 | Freezing | temp ≤ −5 |
| 13 | Light snow | precip 50–75, temp ≤ 2 |
| 14 | Heavy snow | precip > 75, temp ≤ 2 |
| 15 | Light rain | precip 65–80 |
| 16 | Heavy rain | precip 80–92 |
| 17 | Storm | precip ≥ 92 |

**Post-decode additions**: fog, mist, thunderstorm, hail, sleet, dust — all
gated on `CONDITION`, inserted above the numeric ladder, and simply absent
until the decode exists.

---

## 4. The technique: build the window, don't generate it

Seventeen states across four faces is 68 scenes. Generating them costs money,
takes a Kontext pass each, and — the real objection — **adds 68 new
AI-generated assets to a collection already blocked from shipping for exactly
that reason**.

So PRO composes its window from procedural layers instead:

```
  sky          one gradient sprite, TINTED by expression
  sun / moon   disc, positioned by time; moon phase from MOON_PHASE_POSITION
  far cloud    slow parallax layer
  near cloud   faster parallax layer
  terrain      silhouette, banks and pitches with the wrist
  precipitation scrolling tile (rain / snow / hail)
  glass        droplets, frost, condensation — stays put while the view moves
  furniture    reticle, pitch ladder, aircraft symbol — never moves
```

Three things follow, and each is worth having on its own:

**The window becomes provenance-clean.** Every layer is drawn from seeded
arithmetic. The window — the part of these faces that carries the most
character — stops being a blocker.

**The horizon can finally bank on all four faces**, because the furniture is a
separate layer from the world behind it.

**The weather stops being seventeen discrete pictures.** `tintColor` and
`extractColorFromWeightedColors(,,,)` are both in the v5 schema, so a single
sky sprite can be tinted *continuously* from a colour ramp driven by
temperature and time of day, with cloud density as layer alpha driven by
precipitation chance. The ladder in section 3 then selects *effects and
extra layers*, not whole images, and the transitions between states stop
being visible jumps.

Risk noted: `extractColorFromWeightedColors` needs a `ColorConfiguration`
element and its exact binding is unverified. Fallback is per-state tint
constants, which still works and still beats discrete art.

---

## 5. Per-state effects — the creative brief

Ordered by how much each is worth building.

**Scorching / heat.** The signature state. A bleached, washed-out sky; the sun
disc swollen and pulsing; a mirage band shimmering along the horizon, built as
thin horizontal slices scrolling at slightly different phases so the horizon
appears to wobble. No shader needed — the wobble is the phase offsets.

**Fog.** Three grey sheets at different depths, drifting at different speeds
and opacities, with the terrain layer fading toward invisible as fog thickens.
Parallax does the rest: the sheets separate as the wrist tilts, which is
exactly how real fog reads.

**Heavy rain / storm.** Existing streaks, denser and wind-slanted — and the
slant tied to wrist roll, so tilting the arm leans the rain. Above it a
*separate glass layer*: droplets that run down the inside of the canopy and
stay put while the view parallaxes behind them. Lightning flash, plus a brief
terrain silhouette reveal on the strike.

**Snow.** Existing flakes, plus accumulation building on the window sill —
static sprite, alpha driven by intensity — and a frost vignette creeping in
from the corners as temperature drops.

**Blazing / very sunny.** Sun disc with a lens flare that tracks *opposite*
the wrist tilt, the way a real flare moves against the optic. Slow-rotating
god rays. Bleached horizon.

**Cloudy → very cloudy → overcast.** The same two cloud layers throughout,
with density, darkness and speed ramped. Overcast flattens contrast and stops
the sun entirely.

**Clear night.** Star field, and a **moon rendered at its true phase** from
`MOON_PHASE_POSITION` — a real source nothing in the collection uses yet.
Cloudy night occludes the stars with drifting cloud rather than replacing the
scene.

**Freezing.** Frost crystals growing from the window edge, ice-blue cast, and
the precipitation layer switched to hard sleet.

---

## 6. Motion in PRO

Everything the current line does, plus:

- **The horizon banks on all four**, now that furniture is separable.
- **Layer-depth parallax**: near cloud moves more than far cloud, terrain
  least. That is what will sell the window as a window rather than a picture.
- **Flare and glass counter-move** against the view, as real optics do.
- **Jolt** (optional, off by default): raw `ACCELEROMETER_X/Y/Z` magnitude
  minus gravity gives "how hard is this being moved". Wired to rain
  turbulence and to a shake of the compass card. Stays opt-in until it is
  checked on hardware, because the raw axes' units are undocumented.

---

## 7. The compass — what is honestly possible

A magnetic compass is impossible (section 1). Three genuine instruments are
possible, and two of them are aviation-correct.

### First, the obvious workaround, and why it fails

The tempting escape is "let a *compass complication provider* supply the
heading". There is no magnetometer source, but there is `ComplicationSlot`,
`RANGED_VALUE` is a supported type, and third-party compass providers exist.

**It does not work, and the reason is structural: a face cannot read a
complication's value.** The provider renders inside its own slot; the format
exposes exactly two complication-derived expressions —
`COMPLICATION.RANGED_VALUE_COLOR_INTERPOLATE` and
`COMPLICATION.WEIGHTED_ELEMENTS_COLORS` — and both are *colour interpolation
weights consumed by `extractColorFromWeightedColors`*, not numbers. There is
no `COMPLICATION.RANGED_VALUE` to put in a `Transform target="angle"`. The
normalised value can tint a needle; it cannot turn one.

This is the same limitation already recorded in
`~/Android/WATCHFACE-DEV-MANUAL.md` §9 — that a complication's text cannot be
restyled into our own BitmapFont because the provider draws it. Same cause:
the slot is opaque to the face.

So a complication can put a heading *on the dial*, drawn in the system font in
a box we do not control. It cannot drive our instrument. The probe carries a
slot to confirm this on hardware, but the design should assume no.

### The three that do work

**A. Sun compass / solar azimuth dial.** A rotating card driven by solar hour
angle from `HOUR_0_23` + `MINUTE`. At local solar noon the sun bears due south
in the northern hemisphere; the card walks ~15° per hour either side. This is
a real navigational instrument — sun compasses were standard kit where
magnetic compasses were useless. Accurate to a few degrees at the equinoxes
and worse at the solstices, and it needs to know the hemisphere. **Looks and
behaves most like the compass you asked for.**

**B. Bank and slip indicator.** A turn-and-slip ball driven by the
accelerometer. This is *physically exact* — the sensor measures precisely what
the instrument displays — and it is a real aircraft instrument. Costs nothing
in accuracy claims and always tells the truth.

**C. Moon dial.** Phase and position from `MOON_PHASE_POSITION` /
`MOON_PHASE_TYPE`. Real data, currently unused anywhere in the collection.

**Recommendation:** **A on COMMODORE PRO and PURE PRO** (the navigational
faces — a sun compass suits a naval aircraft and a technical instrument), and
**B on HAYATE PRO** where a gunsight already implies attitude. HOG-WILD keeps
its radar. This satisfies "some, not all". Every one of them is labelled for
what it is — nothing on the dial will claim to point north.

---

## 8. HOG-WILD PRO — the radar

The centrepiece idea: **phosphor persistence**. On a real PPI scope the sweep
*paints* the returns and they fade behind it. Each return sprite gets its
alpha driven by a sawtooth phase-shifted to match the moment the sweep passes
its bearing — so returns flare as the sweep arrives and decay in its wake.
This is one expression per return and it is the single most authentic thing we
can do to that dial.

On top of that:

- **Returns coloured by type** — green for rain, amber cores for heavy,
  white-blue for snow, magenta for hail once `CONDITION` is decoded.
- **Intensity maps to range**: heavier weather paints nearer the centre, so
  the scope reads as "it is on top of you".
- **Storm cells drift** slowly across the scope on a fixed vector.
- **Lightning as transient crosses** during storm states.
- **A `WX` / `CLEAR` annunciator** that lights with the state.
- **Fix the painted sweep wedge and the four painted blips** in `wh_dial.png`
  first — the scope currently runs two sweeps at different angles and shows
  four fake returns in clear air, which no amount of real weather can compete
  with.

---

## 9. Which face gets what

| | HAYATE PRO | BALSA PRO | COMMODORE PRO | PURE PRO | HOG-WILD PRO |
|---|---|---|---|---|---|
| Full 17-state window | ✅ | ✅ | ✅ | ✅ | — |
| Banking horizon | ✅ | ✅ | ✅ | ✅ | — |
| Sun compass | — | — | ✅ | ✅ | — |
| Bank & slip | ✅ | — | — | — | — |
| Moon dial | — | ✅ | — | — | — |
| Radar weather | — | — | — | — | ✅ |
| Signature effect | mirage + flare | fog + rain-on-glass | storm | frost + freezing | phosphor radar |

---

## 10. Sequencing

| Phase | Work | Gate |
|---|---|---|
| 0 | MERIDIAN PROBE (v4); start the `CONDITION` decode; measure forecast, both UV spellings, complication cadence | on the wrist, logging |
| 1 | Move engine to v5 **if the probe shows v5 runs on the Watch 7**; `UV_INDEX` usable; new `sky_stack` component | validator passes + installs |
| 2 | Procedural window generator — sky, sun/moon, cloud, terrain, glass | contact sheet reviewed |
| 3 | The 17-state ladder + continuous tint | all states render |
| 4 | Effects: mirage, fog, rain-on-glass, frost, flare | per-effect review |
| 5 | Banking horizon + depth parallax on all four | on the wrist |
| 6 | Sun compass, bank & slip, moon dial | on the wrist |
| 7 | HOG-WILD PRO radar, plate cleanup first | on the wrist |
| 8 | Build, validate, memory footprint, install | five APKs |

Phases 1–5 are the bulk. Phase 0 runs in the background the whole time and
only *adds* states when it lands.

---

## 11. Open decisions for the owner

1. **Name**: PRO or ULTIMATE. Slug and package follow.
2. **Hemisphere for the sun compass** — northern assumed unless told
   otherwise. There is no location source to detect it.
3. **Does the procedural window replace the generated scenes, or sit beside
   them?** Replacing makes the window provenance-clean; keeping the option
   costs a config switch.
4. **How far to take the `CONDITION` decode** — it needs weeks of varied
   weather to be complete, and everything works without it.
5. **HOG-WILD plate cleanup** — the painted sweep and blips need removing
   before the radar work is worth doing.
6. **Does PRO get a forecast instrument?** New, and only open because the
   forecast family turned out to exist. The natural form is a short strip —
   next three or six hours, each hour a tick whose colour comes from its own
   `CONDITION` and whose height comes from its temperature — which is
   genuinely useful in a way a second decorative sub-dial is not. It costs one
   more component and a sub-dial's worth of real estate on faces that are
   already busy. **Recommendation: yes, on COMMODORE PRO only**, whose
   navigational character suits it and which has the emptiest lower third.
   Deferred until the probe confirms the provider actually populates it.
