# MERIDIAN HAYATE

A Nakajima Ki-84 instrument panel. Olive doped fabric over riveted metal,
hinomaru, cannon-shell hands, and a gunsight canopy looking out at the world.

**Development build** — see [`PROVENANCE.md`](PROVENANCE.md).

| | |
|---|---|
| Package | `com.xsytrance.hayate.dev` |
| Version | `0.1.0-dev` |
| Format | WFF v4, 480×480, authored at native resolution |

## The signature

`z10_airscrew` is a motion-blurred three-blade propeller and it never stops.
Every hero render in the collection has one; this is the first face to carry
it. It is a **true motion blur** — the actual generated shell swept through a
full revolution at low per-pass opacity — not a painted effect.

That choice is also why it survives the hardware: a Wear OS face is throttled
hard when idle, so a crisply drawn propeller would strobe against the frame
rate. A blur has no features to alias, so it reads smooth at any refresh.

## What moves

| Layer | Bound to |
|---|---|
| Hour, minute | time — cannon shells with baked contact shadows |
| Airscrew disc | continuous, 1.2 s per revolution |
| Reserve needle | `[BATTERY_PERCENT]` across the painted arc at twelve |
| Steps needle + total | `[STEP_COUNT]` |
| BPM needle + value | `[HEART_RATE]` |
| Date | `[DAY]` |

**Nothing painted also moves.** The plate carries bare pivots and empty
apertures only — the lesson from HOG-WILD, which shipped with two fuel
needles and doubled text because the plate still had them printed on.

## The window on the world

The canopy scene is a separate sprite, not part of the plate. That is
deliberate: the planned live-weather feature swaps its contents without
touching anything else.

## Build

```bash
python3 tools/generate_face.py hayate
bash tools/wff_validate.sh 4 watchfaces/hayate/app/src/main/res/raw/watchface.xml
bash tools/build_face.sh hayate
```
