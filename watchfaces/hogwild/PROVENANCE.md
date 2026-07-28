# PROVENANCE — read before doing anything with this face

**The dial plate in this project is AI-generated. It cannot ship.**

`app/src/main/res/drawable/wh_dial.png` and `wh_dial_aod.png` were produced
by Flux Kontext Pro (via aimlapi.com) from a procedurally-placed layout. They
are concept art committed so the design can be worn and judged, not release
assets.

`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md` in the studio repository requires
every pixel of an aircraft watch to be original studio construction. Generated
pixels do not satisfy that, and carry their own unresolved provenance
questions on top.

## What is and is not generated

| Asset | Origin | Ships? |
|---|---|---|
| `wh_dial.png`, `wh_dial_aod.png` | **Flux Kontext Pro** | **No — must be replaced** |
| `wh_hour/minute/second`, `_aod` variants | procedural, `hogwild_assets.py` | yes |
| `wh_hub.png` | procedural | yes |
| `wh_fuel_needle`, `wh_rpm_needle` | procedural | yes |
| `wh_sweep.png` | procedural | yes |
| `m_*.png` glyphs | procedural | yes |
| `watchface.xml` | generated from `engine/face.toml` | yes |

Only the plate is the problem. Everything that moves is already original.

## Replacing the plate before release

The layout that generated it is deterministic and lives in the studio at
`scratchpad`-authored `hogwild_layout.py` (see the studio roadmap). Two clean
routes:

1. **Blender.** Build the plate as real geometry — recessed instruments,
   engraved legends, applied markers, riveted skin — and render it with
   `CAM_StraightOn`. Original by construction, photoreal, and it gives the
   ambient variant for free as a second render of the same scene.
2. **Procedural raise.** Take the existing layout script and add the material
   passes it currently fakes: brushed metal, engraving relief, contact
   shadows, glass.

Route 1 is recommended and is the basis for the reusable instrument kit
described in the studio's `roadmap/DESIGN_LANGUAGE.md`.

## Until then

- Package stays `com.xsytrance.hogwild.dev`.
- Debug signing only. No release config, no bundle, no store metadata.
- Do not submit, publish or sell this build.
