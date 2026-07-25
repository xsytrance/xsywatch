# Phase 2 Final Architecture Review

**Branch reviewed:** `phase-2/aurelius-reference-engine`  
**Reviewed head:** `b25fce97adaf24fe38c66d796eb8a3899d7e5602`  
**Review date:** 2026-07-24  
**Verdict:** **APPROVED FOR MERGE TO `main`**

## Executive verdict

Phase 2 now satisfies the approved architecture brief and the re-review acceptance criteria.

The deterministic build-time WFF engine is real, tested, and grounded in a ten-face audit. Aurelius is generated from an authoritative TOML specification, its structural behavior is parity-tested, the historical release remains immutable, the handoff contract is enforceable, WFF-version drift is gated, the public ratio helper is mathematically correct, and the physical Galaxy Watch7 baseline-versus-candidate matrix has now been executed.

Most importantly, the physical test found a critical defect that every static gate missed: the repository's Aurelius XML described Field Tourbillon while most of its PNG resources were unreleased WARBIRD artwork. The defect was preserved honestly in evidence, traced to the Phase-1 source import, corrected from the immutable APK's authoritative resource bytes, and re-tested on-device. This validates the review decision not to waive physical evidence.

## Acceptance results

### Engine and repository

- Ten-face audit completed with reproducible machine-readable and human-readable reports.
- `engine/wffgen` 0.1.0-experimental implemented with deterministic committed output.
- Aurelius generated from `watchfaces/aurelius/engine/face.toml`.
- Generation drift check passes.
- Engine test suite reported at 68/68 passing.
- Phase-1 release workflow reported at 10/10 passing.
- All ten watchface projects reported building successfully.
- Repository validation reports zero errors.
- CI is reported green on the reviewed branch.

### Review corrections

- `ratio(expr, lo, hi)` correctly normalizes arbitrary ranges and rejects invalid ranges while retaining the exact zero-based Aurelius battery expression.
- Asset-handoff validation enforces the documented standard-library schema contract, including dimensions, pivots, timing, enums, checksums, traversal rejection, and consuming-face resource containment.
- The engine specification's WFF version is resolved through the Android manifest/resource chain and cross-checked during generation.
- Source-lineage documentation was corrected and then strengthened by actual APK extraction evidence.

### Physical Galaxy Watch7 validation

The physical session used a Samsung Galaxy Watch7 44 mm (`SM-L310`) running Android 16 / API 36.

- Immutable Phase-1 APK SHA-256 remained:
  `844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2`
- Baseline device matrix: all 14 rows reported PASS.
- First candidate SHA-256:
  `cb3557bd9b4902e23409e17ba3b93374f8b0b794c81908c1683520ceacdc54ae`
- First candidate correctly failed the product-level visual test by rendering WARBIRD; this regression remains documented rather than hidden.
- Corrected candidate SHA-256:
  `b01015c87eea1e9b23859d98ebcae56ce808be4db7e066b3d25bc682724cc43e`
- Corrected candidate device matrix: all 14 rows reported PASS, with the documented capture qualifications below.
- Baseline-to-candidate `adb install -r` continuity succeeded.
- Explicit regression conclusion after correction: no material visual or behavioral regression.

## Accepted qualifications

These do not block Phase 2 merge:

1. A direct candidate AOD screencap returned a black frame because the active doze display path was not capturable during that window. AOD entry/exit was exercised for ten cycles, transition evidence exists, the corrected AOD resource bytes match the baseline release resources, and the ambient XML behavior remains parity-determined.
2. Smoothness was evaluated through continuous minute-scale recordings and a longer interactive session rather than a single uninterrupted ten-minute recording. A wear-day owner observation remains useful but is not required for this engineering-extraction phase.
3. Reinstalling the active face causes One UI Watch to fall back to another face until Aurelius is re-selected. Installation continuity and signature compatibility still succeeded; this is documented platform behavior, not a package failure.

## Architectural consequence for Phase 3

The WARBIRD incident changes the risk model. XML parity, schema validation, Gradle success, WFF validation, and memory checks are necessary but cannot prove that the intended pixels are shipping.

Before the first premium/studio asset migration is approved, Phase 3 must add a visual/resource-lineage gate that includes at least:

- real handoff-manifest entries for every new studio export, with exact source commit and imported-byte checksum;
- release/candidate resource inventory reports;
- committed golden normal and AOD reference renders for each engine-managed face;
- automated pixel or perceptual comparison with documented thresholds and masks for dynamic regions;
- an explicit approval path for intentional visual changes so the gate detects accidental substitutions without freezing design evolution;
- physical-device evidence for the first premium Aurelius candidate.

Exact byte equality to the Phase-1 release should not remain a permanent rule after intentional Phase-3 redesign begins. The durable rule is traceable asset provenance plus reviewed visual deltas.

## Documentation housekeeping

Two stale historical statements remain in `docs/reports/PHASE_2_AURELIUS_REFERENCE_ENGINE.md`:

- the technical-debt section still mentions a device-evidence gap;
- the Phase-3 recommendation still says the device gap must be closed first.

They are clearly superseded by Section 24 and the current evidence, so they do not invalidate the phase. Correct them in a small documentation-only commit before or immediately after the merge; no further architecture re-review is required.

## Verification boundary

This review inspected the branch history, diffs, engine implementation, tests, specifications, validation logic, textual device matrices, lineage report, committed evidence inventory, and documentation through the GitHub connector. The connector confirmed that the screenshot and recording artifacts are committed, but this review did not independently replay every MP4 or execute the local Android/ADB commands. Execution results are accepted as reported and supported by the committed evidence record.

## Final decision

**Phase 2 is approved for a normal non-squashed merge into `main`.** Preserve the complete audit, review, correction, failed-candidate, and device-evidence history. Do not erase the WARBIRD regression from the record; it is a high-value architecture finding and the justification for Phase 3 visual-lineage enforcement.
