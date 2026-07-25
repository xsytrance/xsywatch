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
- ~~Physical Galaxy Watch7 evidence for Phase 2 (baseline AND candidate)
  is **blocked**~~ — **superseded (2026-07-24 evening device session):**
  both matrices executed on the physical Watch7; results in
  docs/reports/evidence/phase-2/aurelius/*/DEVICE_TEST_RESULTS.md. The
  run caught and fixed a repo↔release asset divergence dating to the
  Phase-1 import (candidate/ASSET_DIVERGENCE_FINDING.md). Remaining
  device sub-items: the 10-minute continuous smoothness row was PASSed on
  sampled recordings (worth an owner wear-day confirmation), and no direct
  candidate doze screencap exists (non-capturable display pipeline; AOD
  behavior proven by cycling, render byte-determined vs baseline's capture).
- The resource-hash list in `BASELINE_CAPTURE.md` ("All Aurelius runtime
  resources") records the **pre-fix, warbird-contaminated** tree — it is
  a historical point-in-time capture, not the corrected state; the
  corrected assets byte-match the immutable release APK instead.
- ~~The asset-handoff manifest has only a synthetic example entry~~ —
  **superseded (Phase 3):** 50 real entries (Mk II layer set + glyphs)
  bound to AGENOR-Horology commit 1d51b58; lifecycle `candidate` until
  owner promotion.
- The Mk II candidate is `proposed` (APPROVAL-0002): approved goldens
  remain field-tourbillon-v1 until the owner's final pixel acceptance;
  the on-panel ambient frame remains uncapturable on this hardware
  (doze display-off off-wrist / charging screen docked) — on-wrist AOD
  look is part of the owner acceptance.
- Cycles studio re-renders are not byte-deterministic; committed export
  bytes are canonical and checksum-bound (documented in both Phase-3
  reports).

## Device/test

- Battery impact per face is anecdotal, not measured.
- Faces have been tested only on one device (Galaxy Watch7 44 mm).
