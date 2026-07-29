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
| `hy_ov_rain/storm/snow/cloud/stars/flash.png` | procedural — seeded drawing, `tools/make_weather_overlays.py` | **yes** |
| `hy_fld_*.png` | Flux Kontext Max, cropped and scaled; baked reticle removed by `tools/strip_baked_reticle.py` | **No** |

`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md` requires every pixel to be
original studio construction. This build exists to get the design onto a
wrist for judgement. Package stays `.dev`, debug signing only, not for
submission.

Replacement route: the Blender instrument kit described in the studio's
`roadmap/DESIGN_LANGUAGE.md`. The layout that drove these generations is
deterministic and lives at `pipeline/hayate_layout.py` in the studio repo.

## The animated weather layer is clean

Everything added for animated weather is drawn from seeded arithmetic by
`tools/make_weather_overlays.py` — no model, no prompt, no external image. It
is original by construction and can ship as it stands. That does not unblock
this face: the plate, the hands and the weather scenes behind the animation
are unchanged and still generated. It does mean the motion work will not have
to be redone when they are rebuilt.
