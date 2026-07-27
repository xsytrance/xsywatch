# ATTITUDE Horizon Spike — Finalization Integrity Re-review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `spike/attitude-horizon-watch7`  
**Commit reviewed:** `608ccd3c7b8c758e3b89cabe8d2181c007b0feaf`  
**Verdict:** **CORE FINALIZATION DEFECT CLOSED; DEVICE SESSION STILL BLOCKED ON A SMALL SOURCE-OF-TRUTH AND CLI CORRECTION**

## Accepted

The patch closes the original blocking defect:

- a mandatory analysis with `status: BLOCKED` no longer reaches owner review;
- finalization now distinguishes untrustworthy evidence from trustworthy adverse findings;
- raw captures, frame manifests, listed frames and analysis files are resolved and hash-checked;
- extraction uses measured media duration and checks ffmpeg failure and zero-frame output;
- clipping is scanned across every extracted motion frame without sampling;
- owner answers cannot waive clipping, crashes, partial cycling or other machine findings;
- the prior placeholder-only happy-path test was removed;
- the three debug APKs remain unchanged and no product/release boundary was crossed.

The disposition model and status ordering are directionally correct:

`BLOCKED_INTEGRITY` → `MACHINE_ISSUE` → `PENDING_OWNER_REVIEW` → `COMPLETE`.

## Remaining blocking findings

### 1. The success fixture is still semantically contradictory

`FixtureSession.add_video()` writes:

- `nframes = 40`;
- `actual_media_duration_s = 40 / 30`, approximately 1.33 seconds;
- `intended_duration_s = 30` seconds;
- caller-supplied `duration_ratio = 1.0`;
- caller-supplied `capture_duration_disposition = PASS`.

Those fields cannot all be true simultaneously. Finalization accepts them because `verify_frame_manifest()` checks the stored disposition but does not independently recompute:

- expected frame count from actual duration and FPS;
- extraction delta and tolerance;
- actual/intended duration ratio;
- duration disposition;
- extraction disposition;
- ffmpeg return code.

Therefore the replacement success test still proves that internally inconsistent duration evidence can pass. It is better than the old missing-file fixture, but it is not yet a genuine semantic happy path.

Finalization must recompute every derived extraction/duration value from the manifest's primitive facts and reject contradictions.

### 2. Clipping findings still come from the mutable session index

`verify_analysis()` resolves, hashes and parses the actual analysis JSON. However, `verify_machine_findings()` reads:

`SESSION.json → analysis[capture_id] → mask_scan`

instead of reading the `mask_scan` from the verified analysis document.

A session index can therefore say `exposed: false` while the hash-verified analysis file says `exposed: true`, allowing clipping to be omitted from `machine_issues`. This violates the explicit rule that finalization must independently revalidate evidence rather than trust indexes.

The parsed verified analysis document must be the source of truth. The session index should be checked against it or treated only as a locator.

### 3. Installed and analysis-code bytes are not revalidated

Finalization compares stored installed and built hash strings, but does not resolve and hash the pulled-back installed APK file again. A deleted or modified pullback can pass as long as the index strings remain unchanged.

Likewise, `verify_analysis()` requires `analysis_code_sha256` to be present but does not compare it with the actual harness source hash. Presence is not binding.

Finalization must verify:

- installed pullback file exists and matches its recorded and built hashes;
- accepted built APK exists and matches the session binding;
- spike source manifest exists and matches the session binding;
- analysis-code SHA-256 equals the authoritative analysis implementation used for the session, under an explicit policy for code drift after capture.

For this disposable spike, the safest policy is to block if the current harness hash differs from the recorded analysis-code hash, unless analysis is rerun and rebound deliberately.

### 4. The successful CLI extraction path references a removed key

After `cmd_extract_frames()` returns, the CLI prints:

`m['expected_frame_count']`

The new manifest records:

`expected_frame_count_from_media`

A successful `extract-frames` command therefore raises `KeyError` after writing the evidence. This path needs a direct CLI regression test.

### 5. Path containment must use path ancestry, not string containment

`_resolve()` uses string-prefix checks and `verify_frames()` uses string containment. Paths such as a sibling whose name begins with the session path can satisfy those textual checks without being descendants.

Use `Path.is_relative_to()` or an equivalent resolved-parent test for both permitted-root and session-only containment.

### 6. Present optional evidence must also be verified

An AOD screenshot may be absent or explicitly `NOT_OBTAINABLE` for the documented doze limitation. But when a screenshot is present and claims `PASS`, finalization should verify its raw file, hash and capture identity just like the mandatory normal screenshot.

## Required final patch

Before device contact:

1. Make manifest verification recompute all duration and extraction derivations from primitive recorded values.
2. Replace the contradictory success fixture with semantically coherent media-duration evidence.
3. Return the parsed verified analysis document from analysis verification and use it as the source of machine findings and final result summaries.
4. Revalidate installed pullback, built APK, source manifest and analysis-code hashes from actual files.
5. Fix the `expected_frame_count` CLI key regression and test the real CLI success path.
6. Replace string-based path containment with resolved ancestry checks.
7. Verify a present AOD screenshot's raw evidence; permit `NOT_OBTAINABLE` only under the documented limitation.
8. Keep the three APKs byte-identical and preserve every existing boundary.

## Current authorization

- Preserve all three debug APKs.
- Patch only harness/evidence/test code.
- Do not install or contact the Watch7.
- Do not modify watchface XML, artwork, package identities, motion profiles, shared engine, Aurelius, signing, release, store or production ATTITUDE paths.
- Device testing remains blocked until this narrow patch is completed and re-reviewed.
