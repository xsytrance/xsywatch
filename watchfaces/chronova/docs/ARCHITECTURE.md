# CHRONOVA architecture

Native **Watch Face Format v4** face (declarative XML, `hasCode=false`), package
`com.xsytrance.xenochronengine`, design space 480x480 (Galaxy Watch7 44mm native;
WFF scales to other rounds — verified at 384x384 on the Wear OS 6 emulator).

## Generation pipeline (single source of truth)

```
scripts/generate_assets.py   -> assets-source/** + res/drawable-nodpi/** + docs/ASSET_MAP.md
scripts/gen_watchface.py     -> res/raw/watchface.xml + docs/ANIMATION_MAP.md
gradle :app:assembleDebug    -> APK
```

Nothing in `res/drawable-nodpi` or `res/raw/watchface.xml` is hand-edited; change
the scripts and regenerate. All procedural art is seeded (2077) and deterministic.

## Layer stack (z-order, implemented)

00 backing plate -> 02 rear gear train -> 04 chassis + outer scale + glow arcs ->
05 indexing rings + quadrant gear clusters -> 07 pistons -> 08/09 conduits +
energy packets -> 10 turbine + reactor housing + bloom -> 11 counter-rotating
rings -> 12 plasma core + pulse + minute surge -> 13-15 display housings, energy
column, live time text.

Depth illusion comes from real independent layers: rear gears pass under chassis
cutouts and beneath the reactor; conduit ends sit under panel/housing edges so
tubes look socketed.

## Time correctness

- Hours: `TimeText format="hh" hourFormat="SYNC_TO_DEVICE"` (12/24h follows system)
- Minutes: `format="mm"`; Seconds: `format="ss"` (hidden in ambient)
- Typography: Orbitron TTF embedded at `res/font/orbitron.ttf` (WFF v4 accepts
  font-resource family names — verified on device)

## Hard rules learned on this project (do not relearn)

1. `<Compare expression>` must reference a **named** `<Expression>`; inline
   comparisons silently render nothing.
2. `<` inside expression attribute values must be `&lt;` — a raw one kills the
   entire face and crashes the DWF runtime process.
3. Emulator never feeds `[HEART_RATE]`/`[STEP_COUNT]`; verify health sources on
   the physical watch only.
4. Verify every element against the official XSDs:
   github.com/google/watchface `third_party/wff/specification/documents/<ver>/`.

## Slow-cycle clock source

Cycles longer than 60s use `[MINUTE]*60 + [SECOND] + [MILLISECOND]/1000` (`TH` in
the generator) — continuous across minute boundaries within an hour; the hour
wrap causes a single 360°-multiple jump which is visually invisible for the
rates used (integer-degree-per-hour multiples).
