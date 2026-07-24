# Phase 2 ChatGPT Architecture Review

**Branch reviewed:** `phase-2/aurelius-reference-engine`  
**Reviewed head:** `9288f18ba0d92e0c0c9cd657eef9dbfedb0600e6`  
**Review date:** 2026-07-24  
**Verdict:** **CHANGES REQUESTED — do not merge to `main` yet**

## Executive assessment

Phase 2 is a strong implementation of the approved architecture. The branch is five coherent commits ahead of `main`, the ten-face audit is substantive, `engine/wffgen` is real implementation rather than scaffolding, Aurelius generation is deterministic, the imported source baseline is protected by parity tests, both generality fixtures exist, the immutable release APK is pinned, CI is green, and the asset-repository boundary remains intact.

The implementation is close to approval. Four narrow issues must be resolved before merge because Phase 3 will rely directly on this API, handoff contract, and device baseline.

## What is approved

- Five-commit phase history and repository scope.
- Deterministic build-time WFF architecture under ADR-008.
- Aurelius as the first reference face.
- Ten-face component audit and evidence-backed extraction decisions.
- TOML authoritative face specification and committed generated XML.
- Aurelius element/attribute/expression parity against the frozen imported source baseline.
- Analog and digital non-proprietary fixtures.
- Official WFF validation and memory-footprint evidence as reported.
- All-ten build result and Phase-1 release-workflow regression result as reported.
- Immutable current Aurelius APK checksum pin.
- Keeping `AGENOR-Horology` as the sibling studio/asset repository.
- Deferring the premium Aurelius redesign and first real studio export to Phase 3.

## Merge blocker 1 — physical Watch7 evidence must be completed

The physical-device requirement should not be waived or deferred into the premium rebuild.

The immutable Phase-1 APK still exists at:

`releases/aurelius/current/aurelius.apk`

Therefore the baseline is still testable now:

1. pair the Galaxy Watch7 over wireless ADB;
2. install and activate the immutable Phase-1 APK;
3. execute the full baseline matrix and capture normal, AOD, and transition/motion evidence;
4. build the engine-generated candidate and record its APK checksum;
5. install the candidate with `adb install -r` and record whether upgrade continuity succeeds;
6. execute the same candidate matrix;
7. compare baseline and candidate evidence explicitly.

If signature mismatch prevents `adb install -r`, record that as an upgrade-continuity failure, then perform a clean candidate install so the remaining matrix can still run.

The baseline source snapshot is useful, but it is not a substitute for running the preserved release artifact. Phase 1 explicitly records that the producing source commit of the historical APK predates the repository source import. The current test/report wording that calls `watchface_baseline.xml` “the exact file inside the immutable Phase-1 release” is not proven and must be corrected. Android resource XML is compiled into the APK, and no evidence currently establishes byte-for-byte source lineage.

Required evidence:

- physical device model, software/API context, test date/time;
- baseline APK SHA-256 and candidate APK SHA-256;
- normal screenshots for both builds;
- AOD screenshots for both builds;
- transition/motion recordings for both builds;
- pass/fail notes for every row in `docs/DEVICE_TEST_MATRIX.md`;
- observed date, battery, and heart-rate values;
- explicit baseline-versus-candidate regression conclusion.

## Merge blocker 2 — `ratio(expr, lo, hi)` is mathematically incorrect

`engine/wffgen/expressions.py` documents `ratio()` as a normalized 0..1 value over `[lo, hi]`, but currently emits:

`clamp(expr, lo, hi) / hi`

That is correct only when `lo == 0`. For example, a 40..200 range maps 40 to 0.2 rather than 0.

Correct behavior is:

`(clamp(expr, lo, hi) - lo) / (hi - lo)`

Required correction:

1. correct the implementation;
2. reject `hi <= lo` clearly;
3. add tests for zero-based and nonzero-based ranges plus invalid ranges;
4. preserve Aurelius expression parity. A zero-based fast path may retain the current exact `clamp(..., 0, 100) / 100` string, or the battery gauge may use an explicitly named zero-based helper.

This is a public initial engine API and should not enter `main` with known incorrect semantics.

## Merge blocker 3 — handoff validation does not actually enforce its schema

`docs/ASSET_HANDOFF_CONTRACT.md` says each manifest is “validated by `tools/validate.py` against `docs/asset-handoff.schema.json`.” The validator does not load or evaluate that schema. Its manual checks currently enforce only required-field presence, source repository, source SHA format, export type, lifecycle, destination existence, and destination checksum when provided.

The following schema constraints are currently unenforced:

- `asset_id` pattern;
- nonempty string `source_paths`;
- `spec_path` type/content;
- dimensions length, integer type, and positive values;
- `color_space` enum;
- alpha enum;
- pivot length, numeric type, and 0..1 range;
- frame count and frame timing rules;
- loop enum;
- boolean `aod_safe`;
- license field validity;
- SHA-256 format and requiredness for non-example destinations;
- consumer component and regeneration command content;
- destination containment under the consuming face’s `app/src/main/res/` tree.

Required correction:

- either validate the JSON Schema directly, or implement the complete relevant schema contract with standard-library validation and change the documentation so it describes the mechanism accurately;
- add negative tests for malformed dimensions, pivot, animation timing, enum fields, checksum shape/requiredness, and path traversal/out-of-face destinations;
- keep the synthetic example exception explicit and narrow.

Approved-only release gating may remain a Phase-3 addition as already documented, but the Phase-2 schema claim must be true before the first real asset handoff.

## Merge blocker 4 — WFF version in the face spec is not cross-checked

`face.toml` declares `wff_version = 4`, but `tools/generate_face.py` verifies only package, versionCode, and versionName against Gradle. It does not resolve and compare the Android manifest’s watch-face format property (`@integer/wff_version`) with the engine spec.

Required correction:

1. resolve the manifest WFF property, including the current `@integer/wff_version` resource form;
2. fail generation/check when it differs from `FaceSpec.wff_version`;
3. add a deliberate mismatch test;
4. keep Aurelius at WFF v4.

This closes the brief’s engine/version-mismatch requirement and makes the WFF baseline an enforceable invariant rather than a comment and unit-test expectation.

## Required documentation corrections

Update the Phase 2 report, parity-test docstring, baseline/candidate blocker notes, architecture ledger, and known limitations so that:

- `watchface_baseline.xml` is described as the frozen imported source baseline, not as proven exact source extracted from the historical APK;
- physical baseline and candidate evidence are recorded rather than left blocked;
- the ratio correction and tests are reported;
- the handoff validation mechanism is described truthfully;
- WFF-version cross-checking is documented;
- this review file receives a resolution section with fixing commits and acceptance results.

## Re-review acceptance criteria

Phase 2 may be approved when:

- the full physical baseline and candidate Watch7 matrix is committed and passes, or any genuine observed failures are documented for architectural judgment;
- baseline-versus-candidate evidence identifies no material regression;
- `ratio()` is corrected and negatively/positively tested;
- handoff validation enforces the documented schema contract;
- WFF version is cross-checked between engine spec and Android resources;
- all 10 projects still build;
- all engine tests and Phase-1 release fixtures pass;
- official WFF and memory evidence remains valid after corrections;
- `tools/validate.py` reports zero errors;
- CI is green;
- the immutable release APK remains unchanged;
- branch history remains unsquashed and the branch is returned for re-review.

## Verification limitation

This review inspected the branch comparison, engine source, specifications, tests, validation, reports, evidence records, and CI configuration through the GitHub connector. It did not independently execute the local Android builds, external validator jars, memory evaluator, or physical-watch tests. Those execution results remain accepted as reported pending the required device evidence and final CI run.
