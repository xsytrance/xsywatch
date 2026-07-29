# PROVENANCE — MERIDIAN BALSA

**Generated assets in this project cannot ship.**

| Asset | Origin | Ships? |
|---|---|---|
| `ba_dial.png`, `ba_dial_aod.png` | Flux Kontext Pro over a procedural layout | **No** |
| `ba_hour.png`, `ba_minute.png` | Flux Kontext Pro, chroma-keyed and re-registered | **No** |
| `ba_canopy.png` | Flux Kontext Pro, keyed and masked to the aperture | **No** |
| `ba_disc.png` | derived — a motion blur of the generated shell | **No** (derived from generated) |
| `ba_hub`, needles, `m_*` glyphs | procedural | yes |
| `watchface.xml` | generated from `engine/face.toml` | yes |
| `ba_ov_rain/storm/snow/cloud/stars/flash.png` | procedural — seeded drawing, `tools/make_weather_overlays.py` | **yes** |
| `ba_wx_clip.png` | derived — `ba_dial.png` with the window silhouette punched out, `tools/make_window_clips.py` | **No** (derived from generated) |

`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md` requires every pixel to be
original studio construction. This build exists to get the design onto a
wrist for judgement. Package stays `.dev`, debug signing only, not for
submission.

Replacement route: the Blender instrument kit described in the studio's
`roadmap/DESIGN_LANGUAGE.md`. The layout that drove these generations is
deterministic and lives at `pipeline/balsa_layout.py` in the studio repo.

## The animated weather layer is clean

Everything added for animated weather is drawn from seeded arithmetic by
`tools/make_weather_overlays.py` — no model, no prompt, no external image. It
is original by construction and can ship as it stands. That does not unblock
this face: the plate, the hands and the weather scenes behind the animation
are unchanged and still generated. It does mean the motion work will not have
to be redone when they are rebuilt.
