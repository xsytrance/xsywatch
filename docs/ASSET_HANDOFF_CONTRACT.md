# Asset Handoff Contract — AGENOR-Horology → xsywatch

How rendered/exported assets travel from the 3D asset repository
(`xsytrance/AGENOR-Horology`: Blender, Material Maker, Inkscape masters)
into watchface resources here — with full provenance, checksums, and
lifecycle state. No submodule, subtree, or copied git history (ADR-005/008).

## The manifest

Every engine-managed face that consumes studio exports keeps a manifest at:

```
watchfaces/<slug>/engine/handoff.json
```

validated by `tools/validate.py` against `docs/asset-handoff.schema.json`.
One entry per imported export:

| Field | Meaning |
|---|---|
| `asset_id` | stable identifier, `<class>/<PartName>` as in the asset repo (e.g. `gears/GearSpur_M020_z60`) |
| `source_repo` | always `xsytrance/AGENOR-Horology` |
| `source_commit` | full 40-char SHA of the asset-repo commit the export was produced from |
| `source_paths` | repo-relative paths of the producing sources (`.blend`, `.ptex`, `.svg`) |
| `spec_path` | the asset's `SPEC.md` in the asset repo |
| `export_type` | `static-image` \| `sprite-strip` \| `sprite-grid` \| `mask` \| `font-glyphs` |
| `destination` | repo-relative path of the imported file under `app/src/main/res/` |
| `dimensions` | `[w, h]` pixels of the export (per frame for strips) |
| `color_space` | `srgb` (display) — record it, don't assume it |
| `alpha` | `straight` \| `premultiplied` \| `none` |
| `pivot` | `[x, y]` normalized 0..1 rotation origin baked into the art |
| `frames` | frame count (1 for static) |
| `frame_seconds` | seconds per frame at intended playback (null for static) |
| `loop` | `perfect` (frame N+1 ≡ frame 1) \| `pingpong` \| `none` |
| `aod_safe` | boolean — may this art appear in ambient mode within OLED limits |
| `license` | provenance record: `original` or an entry in `docs/asset-licenses.json` |
| `sha256` | SHA-256 of the imported export file — validation recomputes it |
| `lifecycle` | `experimental` \| `candidate` \| `approved` \| `deprecated` |
| `consumer_component` | engine component instance using it (e.g. `z22_cage`) |
| `regenerate` | exact command in the asset repo that reproduces the export |

## Rules

1. **Approved-only for releases.** A face may only *release* with
   `approved` assets; `experimental`/`candidate` entries are development
   states (release gating lands with the first real studio import, Phase 3).
2. **Checksums are binding.** If the file's bytes change, the manifest entry
   must be updated with a new `source_commit` + `sha256` — validation fails
   otherwise.
3. **Regeneration is documented, not required.** The committed export is
   canonical (same rule as generator donor images).
4. **Lifecycle transitions are commits.** Promoting `candidate → approved`
   is a reviewed manifest change, per the asset lifecycle in the asset
   repo's docs.
5. **Legacy art.** Existing Phase-1 face art predates this contract; it is
   NOT retroactively manifested. Only new studio imports use the manifest.

## Example (synthetic, labeled non-approved)

`watchfaces/aurelius/engine/handoff.json` ships with a synthetic example
entry (`lifecycle: experimental`, `example: true`) describing the future
tourbillon-cage sprite handoff. It references no real file yet
(`destination: null`) and exists so the schema, validator, and review
workflow are exercised before Phase 3 delivers real exports.
