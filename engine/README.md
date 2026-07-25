# AGENOR WFF Engine (`wffgen`) — 0.1.0-experimental

Deterministic **build-time** Watch Face Format generation and validation
(ADR-008). WFF packages are declarative, resource-only apps — there is no
runtime shared-code layer — so reuse happens here: authoritative face specs
generate the committed `watchface.xml`.

## What the engine owns / does not own

| Engine owns | Face owns |
|---|---|
| expression builders (time, parallax, HR oscillator, gauges) | artwork, resource files |
| component structure + naming/z-order conventions | layout coordinates, palette |
| ambient (AOD) policies + motion-class metadata | design identity, typography choice |
| deterministic serialization + structural validation | its `engine/face.toml` spec |

## Workflow

```bash
python3 tools/generate_face.py aurelius           # regenerate committed XML
python3 tools/generate_face.py aurelius --check   # fail on drift (CI gate)
python3 -m unittest discover -s tests/engine -v   # engine unit tests
```

Generated files carry a banner comment naming the spec, command, and engine
version. Edit `watchfaces/<slug>/engine/face.toml`, never the generated XML.

## Component registry (extraction basis: `docs/reports/PHASE_2_COMPONENT_AUDIT.md`)

| Type | Behavior | Audit evidence |
|---|---|---|
| `background_pair` | normal/AOD crossfade + parallax | AOD variants in 10/10, parallax 9/10 |
| `rotating_image` | continuous mechanical rotation, direction+speed metadata | 7 faces rotate parts |
| `seconds_rotor` | 360°/minute (tourbillon cage, seconds) | 4 faces |
| `hr_balance` | HR-frequency oscillator, fallback+clamp | aurelius; HR bound in 7 faces |
| `battery_needle` | gauge needle over battery % | battery bound in 7 faces |
| `date_text` | bitmap-font date aperture | `[DAY]` in 7 faces |
| `sheen` | breathing alpha + strong parallax | sin-alpha pattern in 3 faces |
| `analog_hand` | smoothed hour/minute hands | hand angles in 4–5 faces |
| `static_image` | static layer with AOD policy | universal |
| `text_line` | generic bitmap-font data line | generalization for fixtures |

Every component declares a **motion class** (ledger §8) and an **AOD
policy**; `validation.py` refuses undeclared components, duplicate/ill-formed
names, missing pivots on rotating parts, out-of-canvas boxes, unknown data
sources, and missing resources.

## Determinism contract

Same spec + same engine version → byte-identical XML. Guarantees: fixed
attribute order per tag, fixed number formatting (`expressions.num`), no
timestamps, sorted iteration everywhere. `--check` + CI enforce it.

## API stability

Everything is **experimental** at 0.1.0. Components proven only by Aurelius
may change when a second production face migrates (Phase 3+). Additions
require: audit evidence, unit tests, and a fixture exercising the component
outside Aurelius naming.
