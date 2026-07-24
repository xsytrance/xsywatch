# Known Limitations

Verified state, 2026-07-24 (Phase 1). Anything fixed later should be struck
through with a pointer to the fixing commit.

## Release artifacts

- All APKs are **debug-signed** — sideload only, not store-distributable.
  No release keystore exists yet (deliberate; see BUILD_AND_RELEASE.md).
- 4 of 7 released faces have **no preview image** in `releases/`
  (ares-wargod, bone-watch, hellforge, pinball). Source previews exist in
  each project's `res/drawable*/preview.png`; release-grade previews should be
  regenerated at release time.
- Release metadata for the 7 existing APKs is partially reconstructed:
  exact build dates are file-mtime approximations and the producing source
  commit predates this repository's source import (fields marked accordingly
  in each `RELEASE.md`).

## Source projects

- `tools/*.py` asset-generation scripts reference **external donor images**
  (AI-generation intermediates under `~/AI/ComfyUI/output/`, not in the repo).
  Committed drawables are canonical; regeneration requires those local files.
  Provenance is documented per-face.
- Some generator scripts remain hard-coded to absolute paths (documented
  per-face); only the project-ROOT paths were normalized in Phase 1.
- No automated visual regression or on-device test harness yet.
- `bone-watch` was creatively **rejected** by the owner; source retained for
  parts reuse.
- Unreleased faces (`arcwright`, `chronova`, `tripface`) are experimental;
  they build, but have had no recent design attention.

## Engine

- No shared engine layer yet — each face duplicates common patterns
  (chapter rings, AOD handling, HR bindings). Extraction is Phase 2 (ADR-003:
  prove one reference face first).

## Device/test

- Battery impact per face is anecdotal, not measured.
- Faces have been tested only on one device (Galaxy Watch7 44 mm).
