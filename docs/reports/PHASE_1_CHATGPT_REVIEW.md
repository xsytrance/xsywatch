# Phase 1 ChatGPT Architecture Review

**Branch reviewed:** `phase-1/repository-normalization`  
**Reviewed head:** `38facac`  
**Review date:** 2026-07-24  
**Verdict:** **CHANGES REQUESTED — do not merge to `main` yet**

## Executive assessment

Phase 1 is a substantial and well-structured normalization effort. The branch is five commits ahead of `main`, preserves the seven original APKs, imports ten editable source projects, establishes useful documentation, and introduces a credible baseline build/validation toolchain.

The repository is materially better than its original artifact-only state. The source import, release relocation, per-face project structure, Gradle wrappers, architecture ledger update, and audit report are all directionally approved.

However, two areas currently contradict the branch's own claims and acceptance criteria:

1. The licensing audit says no TTF/OTF files exist and that validation enforces this, but tracked font files do exist and the validator does not check them.
2. The release pipeline is not yet safe for the documented `current` plus versioned-channel model, and validation does not inspect actual APK metadata.

These must be corrected before merge because the project intends to support commercial releases and reproducible release traceability.

## What is approved

- Ten complete source projects are organized under `watchfaces/<slug>/`.
- The seven original APKs are preserved under `releases/<slug>/current/` rather than deleted.
- The seven-vs-eight discrepancy is adequately resolved as a commit-message miscount.
- The five-commit phase structure is reviewable and coherent.
- Keeping `AGENOR-Horology` as a sibling repository is architecturally sound for now; ADR-005 is recommended for owner ratification.
- Deferring an empty `engine/` scaffold is correct. Shared extraction should follow evidence from a reference face.
- Debug signing is clearly disclosed rather than misrepresented as production-ready.
- `tripface` is correctly identified as the lone WFF v2 divergence.

## Merge blocker 1 — licensing audit and validator are inaccurate

### Evidence

`docs/LICENSING.md` and the Phase 1 report state that the scan found no embedded TTF/OTF files and that validation checks this condition.

The branch contains at least these two tracked font paths, with the same blob SHA:

- `watchfaces/arcwright/app/src/main/res/font/orbitron.ttf`
- `watchfaces/arcwright/assets-source/fonts/orbitron.ttf`

`tools/validate.py` does not scan `.ttf` or `.otf` files for licensing metadata; its extension set is limited to source/document text formats, and its secret pattern is unrelated to font licensing.

The branch also contains source assets such as an HDRI under Arcwright. Any externally sourced font, HDRI, donor image, texture, or model-derived asset needs explicit provenance and redistribution/commercial-use status.

### Required correction

1. Inventory every tracked `.ttf`, `.otf`, `.hdr`, `.exr`, and other externally sourced asset format.
2. Record for each asset:
   - source/name,
   - upstream URL or origin when known,
   - author/provider,
   - license identifier,
   - whether redistribution is permitted,
   - whether commercial use is permitted,
   - where the required license/notice text is stored.
3. Add required license text files or attribution notices to the repository.
4. Correct `docs/LICENSING.md`, the Phase 1 report, and any per-face README claims.
5. Extend validation so a font or declared third-party asset without a corresponding license/provenance record is an ERROR, not an undocumented pass.
6. Do not assume that a familiar filename implies a particular license; verify the actual source of the committed bytes.
7. Consider deduplicating identical source/runtime copies only if doing so does not harm build reproducibility.

## Merge blocker 2 — release tooling conflicts with ADR-006 and can lose traceability

### Evidence

ADR-006 defines:

- `releases/<slug>/current/`
- archived immutable versions under `releases/<slug>/vX.Y.Z/`

But `tools/package_release.sh` simply copies a new debug APK into `current/<slug>.apk`. It does not archive the existing `current` release first, does not require a version, and can overwrite the only retained copy of the prior release.

`tools/gen_release_manifest.py` emits one manifest entry for every APK path, including both `current` and future version directories. `tools/validate.py` then converts the manifest to a dictionary keyed only by `slug`. Once both `current` and `vX.Y.Z` entries exist for the same face, one entry overwrites the other in memory. Validation will compare the current APK against an arbitrary same-slug channel entry and the release model will become ambiguous or fail.

The validator's documentation also claims that APK package metadata is checked, but `tools/validate.py` does not call `aapt2`; it compares Gradle metadata only against the values already written in `MANIFEST.json`. It does not independently verify the APK package, versionCode, versionName, or targetSdk.

### Required correction

1. Redesign manifest identity around at least `(slug, channel)` or use a nested schema such as face → channels.
2. Enforce uniqueness for each `(slug, channel)` pair.
3. Make the validator inspect every APK directly with `aapt2` and compare actual APK metadata against:
   - manifest metadata,
   - source `applicationId`,
   - source versionCode/versionName,
   - expected targetSdk/WFF metadata where applicable.
4. Make packaging preserve the existing `current` artifact under its immutable semantic-version directory before replacing it.
5. Refuse to overwrite an existing immutable version unless an explicit, documented override is supplied.
6. Require or derive the new semantic version and verify that it matches source/APK metadata.
7. Search supported preview locations (`drawable*`, expected extensions), detect ambiguity, and do not silently retain a stale preview.
8. Add a temporary-fixture/self-test proving this sequence works:
   - package initial release,
   - package next release,
   - prior release remains under `vX.Y.Z`,
   - new release becomes `current`,
   - manifest contains both unambiguously,
   - validation passes,
   - tampering with APK/package/version/checksum causes validation failure.

## Required documentation updates

After correcting the blockers, update:

- `docs/reports/PHASE_1_REPOSITORY_NORMALIZATION.md`
- `docs/LICENSING.md`
- `docs/BUILD_AND_RELEASE.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/CHATGPT_ARCHITECT.md`
- ADR-006 if the manifest/release layout changes materially
- this review file with a resolution section and fixing commit hashes

Do not preserve inaccurate statements as current facts. Historical mistakes may remain only when clearly labeled as superseded.

## Non-blocking recommendations

1. Add GitHub Actions after the blockers are fixed. At minimum run Python compilation, shell syntax checks, `git diff --check`, and `tools/validate.py`. Add Android builds when runner cost and SDK setup are acceptable.
2. Clarify the root README opening sentence as “primarily WFF v4” because `tripface` remains WFF v2.
3. Make `check_prereqs.sh` verify the exact tools used by release generation and validation, including executable `aapt2`.
4. Prefer repository-local temporary/log directories or collision-safe `mktemp` paths instead of fixed `/tmp/agenor-build-<slug>.log` names.
5. Add automated tests for `tools/validate.py` rather than relying only on a successful run against the current repository state.
6. Record actual on-device test evidence separately from successful Gradle assembly. A build pass is not equivalent to device behavior, AOD correctness, complication updates, or battery acceptability.

## Owner decisions recommended

- **ADR-005:** approve. Keep `AGENOR-Horology` as a sibling asset/pipeline repository until atomic cross-repository changes become a real problem.
- **Repository license:** keep proprietary/all-rights-reserved for now. Add explicit third-party notices and asset licenses; do not open-source commercial artwork by accident.
- **Release signing:** defer store signing implementation until the release workflow is corrected, then create a production keystore outside Git and document secure backup/recovery. Never commit it.
- **Bone Watch:** retain source but mark it `archived/creative-rejected`; keep it buildable for parts reuse and exclude it from the active commercial roadmap.
- **TripFace:** freeze as a legacy experimental WFF v2 face. Do not spend Phase 2 engine-extraction time upgrading it unless it is selected for revival/release.

## Re-review acceptance criteria

Phase 1 may be approved for merge when:

- licensing documentation accurately accounts for all tracked fonts and third-party assets;
- licensing/provenance validation is implemented and passes;
- the versioned release workflow preserves existing releases without overwrite;
- manifest entries are channel-safe and unique;
- validation reads actual APK metadata and detects deliberate mismatch fixtures;
- all ten source projects still build;
- repository validation passes;
- the Phase 1 report and ledger are corrected;
- the branch is pushed with a concise correction report and commit hashes.

## Verification limitation

This review inspected the GitHub branch, its five-commit comparison, documentation, manifest, and tooling through the GitHub connector. It did not independently execute the local ten-project build or install the APKs on the physical watch. Those results remain accepted as reported pending CI and device-test evidence.

---

# Resolution (Claude Code, 2026-07-24)

All required corrections are implemented on this branch. Verdict requested:
**re-review**. The branch has NOT been merged.

## Fixing commits

| Commit | Scope |
|---|---|
| `9400394` | Merge blocker 1 — licensing audit correction: verified byte-level font/HDRI inventory (`docs/asset-licenses.json`, 27 OFL-1.1 fonts / 8 upstream projects + 1 CC0 HDRI), OFL notices in `THIRD_PARTY_NOTICES/fonts/`, proprietary `LICENSE`, `docs/LICENSING.md` rewritten with the false claim labeled superseded |
| `652535c` | Merge blocker 2 — schema-2 channel-safe manifest ((slug,channel) identity), `package_release.py` with archive-before-replace + immutability guards + preview-ambiguity abort, `validate.py` reading real APK metadata via aapt2 vs manifest AND source, 10-fixture `test_release_workflow.py` (all PASS), aapt2 prereq check, mktemp build logs |
| (docs commit, see log) | Documentation updates, owner decisions applied, CI workflow |

## Acceptance criteria status

- Licensing documentation accounts for all tracked fonts/assets — **done, byte-verified**
- Licensing/provenance validation implemented and passing — **done** (negative-tested: fixtures T8/T9)
- Versioned release workflow preserves existing releases — **done** (T2/T3: same-version refusal; archive byte-identical)
- Manifest entries channel-safe and unique — **done** (schema 2; duplicate identity = generator/validator error)
- Validation reads actual APK metadata and detects deliberate mismatch fixtures — **done** (aapt2; T5/T6/T7)
- All ten source projects still build — **done** (build_all 10/10 PASS after corrections)
- Repository validation passes — **done** (0 errors, warnings documented)
- Phase 1 report and ledger corrected — **done** (report §14 corrected + §21 added; ledger review note)
- Branch pushed with correction report and hashes — **done** (this section)

## Owner decisions applied as approved

ADR-005 ratified · repository proprietary (`LICENSE`) · bone-watch
archived/creative-rejected · tripface frozen (legacy WFF v2) · no production
keystore created.

## Non-blocking recommendations status

1. CI: `.github/workflows/validate.yml` added (py_compile, bash -n,
   diff --check, validate.py with aapt2). **First Actions run not yet
   observed — unverified until green.**
2. README reworded to "primarily WFF v4". **Done.**
3. `check_prereqs.sh` verifies executable aapt2. **Done.**
4. Build logs via `mktemp`. **Done.**
5. Automated validator tests: partially — the 10-fixture workflow test covers
   the validator's release/licensing paths; broader unit tests deferred.
6. On-device evidence: still outstanding (tracked in KNOWN_LIMITATIONS).
