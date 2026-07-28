# PROVENANCE — MERIDIAN HAYATE

**Generated assets in this project cannot ship.**

| Asset | Origin | Ships? |
|---|---|---|
| `hy_dial.png`, `hy_dial_aod.png` | Flux Kontext Pro over a procedural layout | **No** |
| `hy_hour.png`, `hy_minute.png` | Flux Kontext Pro, chroma-keyed and re-registered | **No** |
| `hy_canopy.png` | Flux Kontext Pro, keyed and masked to the aperture | **No** |
| `hy_disc.png` | derived — a motion blur of the generated shell | **No** (derived from generated) |
| `hy_hub`, needles, `m_*` glyphs | procedural | yes |
| `watchface.xml` | generated from `engine/face.toml` | yes |

`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md` requires every pixel to be
original studio construction. This build exists to get the design onto a
wrist for judgement. Package stays `.dev`, debug signing only, not for
submission.

Replacement route: the Blender instrument kit described in the studio's
`roadmap/DESIGN_LANGUAGE.md`. The layout that drove these generations is
deterministic and lives at `pipeline/hayate_layout.py` in the studio repo.
