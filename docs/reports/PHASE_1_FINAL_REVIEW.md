# Phase 1 Final Architecture Review

**Branch:** `phase-1/repository-normalization`  
**Claude correction head reviewed:** `4ed6bee674546eca6ff03d8bbfffdceccf171a41`  
**Architect CI correction:** `af30ade0f6207ff00847be24ef99021e9e37c137`  
**Review date:** 2026-07-24  
**Verdict:** **APPROVED FOR MERGE TO `main`**

## Executive verdict

The two Phase 1 merge blockers identified in `PHASE_1_CHATGPT_REVIEW.md` are resolved. The branch now provides a credible reproducible-source baseline for the AGENOR watchface ecosystem, with channel-safe release preservation, direct APK metadata verification, SHA-bound third-party asset licensing enforcement, documented owner decisions, and a negative-tested release workflow.

No remaining finding blocks the Phase 1 merge.

## Acceptance criteria verification

### 1. Licensing inventory and enforcement — PASS

- `docs/asset-licenses.json` inventories 27 tracked font files and one HDRI with path, SHA-256, provenance, license identifier, redistribution permission, commercial-use permission, and notice location where required.
- Eight canonical SIL OFL 1.1 notice files are committed under `THIRD_PARTY_NOTICES/fonts/`.
- The proprietary repository `LICENSE` contains an explicit carve-out preserving third-party licenses.
- `tools/validate.py` fails on missing asset inventory entries, altered bytes, missing license identifiers/permission flags, missing OFL notices, and stale inventory entries.
- Negative fixtures T8 and T9 exercise missing-license and checksum-mismatch failures.

The prior Phase 1 statement that no fonts were tracked is correctly marked as superseded rather than silently erased.

### 2. Release preservation and manifest identity — PASS

- `tools/package_release.py` reads the built APK through `aapt2` and requires package/version metadata to match source Gradle metadata before packaging.
- A prior `current` release is moved to `v<oldVersion>` before the new release becomes `current`.
- Existing immutable version directories refuse overwrite unless an explicit destructive override is supplied.
- Same-version packaging refuses by default.
- Preview discovery searches supported `drawable*` locations and aborts on missing or distinct ambiguous previews unless a no-preview release is explicitly requested.
- Manifest schema 2 uses nested face/channel records, giving `(slug, channel)` stable identity.

### 3. Independent APK validation — PASS

`tools/validate.py` reads every release APK through `aapt2` and compares actual package, versionCode, versionName, targetSdk, and checksum against the manifest. It also compares package metadata to source for every channel and version metadata to source for `current`; immutable channel names must match their contained APK versionName.

### 4. Failure-fixture coverage — PASS

`tools/test_release_workflow.py` covers:

1. initial packaging;
2. same-version refusal;
3. byte-identical archive preservation and new-current promotion;
4. two-channel validation success;
5. corrupted APK detection;
6. manifest version tamper detection;
7. source/release drift detection;
8. unlicensed tracked font detection;
9. license-inventory checksum mismatch detection;
10. ambiguous preview refusal.

The reported result is 10/10 PASS. The test implementation was reviewed and exercises real packaging/validation code in a sandboxed Git repository, including a real Gradle rebuild for the bumped release.

### 5. Build and repository validation — PASS, accepted as reported

Claude reports all 10 imported watchface projects rebuilt successfully after the corrections and repository validation completed with 0 errors and 12 documented warnings. This connector review inspected source, manifests, tooling, documentation, and commit structure but did not independently execute the local Android builds or physical-device tests.

### 6. Documentation and owner decisions — PASS

The correction pass accurately updates the architecture ledger, Phase 1 report, licensing guide, build/release guide, known limitations, inventory, ADR-005, ADR-006, project README, and original review resolution.

Owner decisions are now explicit:

- ADR-005 ratified: `AGENOR-Horology` remains a sibling repository.
- `xsywatch` remains proprietary/all-rights-reserved.
- Bone Watch is archived/creative-rejected but retained as buildable source.
- TripFace is frozen as a legacy WFF v2 experiment.
- No production signing material was created or committed.

## Architect-side CI correction

During final review, `.github/workflows/validate.yml` contained `git diff --check HEAD~1 HEAD || true`, which made the check non-enforcing, while the default shallow checkout could omit `HEAD~1`.

Commit `af30ade0f6207ff00847be24ef99021e9e37c137` corrects this by:

- setting `actions/checkout` to `fetch-depth: 2`; and
- removing `|| true` so whitespace/conflict-marker failures fail CI.

This was a narrow CI-hygiene correction and does not change watchface source, release artifacts, licensing records, or packaging behavior.

## Remaining non-blocking limitations

- The first GitHub Actions result has not yet been verified green.
- Physical Galaxy Watch7 test evidence remains outstanding; successful assembly is not proof of AOD, complication, animation, sensor, or battery behavior.
- Commercial-use terms for the exact AI model checkpoints used to generate artwork remain an owner action before paid distribution.
- Broader validator unit tests and visual regression testing remain future work.
- Release APKs remain debug-signed and unsuitable for store distribution.

These limitations are accurately disclosed and are not Phase 1 merge blockers.

## Merge recommendation

Merge `phase-1/repository-normalization` into `main` using a normal merge or squash policy chosen by the owner. Because the existing commits are deliberately organized as an auditable phase history, a normal merge commit is preferred over squashing.

After merge:

1. verify the `validate` GitHub Actions workflow is green on `main`;
2. tag the repository baseline only if a clear non-product engineering tag is desired;
3. begin Phase 2 from the updated architecture ledger, using Aurelius as the recommended reference face unless the product owner selects another face.
