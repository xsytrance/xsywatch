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
- ~~Phase-1 claim that no TTF/OTF fonts are embedded~~ — **superseded
  (Phase-1 review):** 27 OFL-1.1 font files + 1 CC0 HDRI are tracked; full
  audit in `docs/asset-licenses.json` + `docs/LICENSING.md`. Validation now
  enforces the inventory.
- AI-model license check for commercial sale of generated artwork remains an
  open owner action (docs/LICENSING.md).
- CI workflow (.github/workflows/validate.yml) is committed but its first
  GitHub Actions run has not yet been observed — treat as unverified until
  green.

## Source projects

- `tools/*.py` asset-generation scripts reference **external donor images**
  (AI-generation intermediates under `~/AI/ComfyUI/output/`, not in the repo).
  Committed drawables are canonical; regeneration requires those local files.
  Provenance is documented per-face.
- All project-internal absolute paths in generator scripts were normalized
  to repo-relative; only external donor references (see above) remain, by
  design (ADR-007).
- No automated visual regression or on-device test harness yet.
- `bone-watch`: **archived/creative-rejected** (owner decision, Phase-1
  review); buildable, excluded from the commercial roadmap.
- `tripface`: **frozen** legacy WFF v2 (owner decision, Phase-1 review).
- `arcwright`, `chronova` remain experimental; they build, but have had no
  recent design attention.

## Engine

- ~~No shared engine layer yet~~ — **superseded (Phase 2):** `engine/wffgen`
  (0.1.0-experimental) generates Aurelius from `engine/face.toml` with
  parity regression tests. Remaining: only Aurelius is engine-managed; the
  other nine faces still hand-author XML (deliberate — ADR-008 no broad
  migration); engine APIs are experimental and may change when a second
  face migrates.
- Physical Galaxy Watch7 evidence for Phase 2 (baseline AND candidate) is
  **blocked** — no watch reachable from the build box (re-verified during
  the review-correction pass); disclosed in
  docs/reports/evidence/phase-2/aurelius/*/DEVICE_EVIDENCE_BLOCKER.md with
  the exact owner steps (DEVICE_TEST_MATRIX.md) to close it. This is
  Phase-2 re-review blocker 1 and the ONLY remaining blocker.
- The asset-handoff manifest has only a synthetic example entry; the first
  real studio export lands in Phase 3.

## Device/test

- Battery impact per face is anecdotal, not measured.
- Faces have been tested only on one device (Galaxy Watch7 44 mm).
