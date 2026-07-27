# Claude Next Task — ATTITUDE Spike Final Source-of-Truth Patch

Pull:

- repository: `xsytrance/xsywatch`
- branch: `spike/attitude-horizon-watch7`
- branch must contain review commit: `1108c89b0e4fee4fcdf16c7c86e7ed038f01be8d`

Do not compare HEAD to the commit above as an exact equality: this instruction file is committed after that review, so the branch head containing this file is necessarily one commit later. This is intentional and avoids another self-reference problem.

Read first:

- `docs/reports/ATTITUDE_HORIZON_FINALIZATION_INTEGRITY_REREVIEW.md`
- `docs/reports/ATTITUDE_HORIZON_HARNESS_FINALIZATION_CHATGPT_REVIEW.md`
- `docs/instructions/CLAUDE_ATTITUDE_SPIKE_FINALIZATION_JUDGMENT_CALLS.md`

The original finalization loophole is closed. This assignment is a narrow final source-of-truth correction before device testing.

Nothing may be installed or contacted during this assignment.

## Preserve accepted artifacts

Before editing, record all three APK hashes and sizes from `BUILD_RECORD.json`.

After the patch, clean-build all three. They must remain byte-identical:

- DAMPED: `com.xsytrance.attitude.spike.damped`
- PROPOSED: `com.xsytrance.attitude.spike.proposed`
- ASSERTIVE: `com.xsytrance.attitude.spike.assertive`

If any APK changes, stop and explain the exact cause. Do not update accepted hashes silently.

Do not modify:

- watchface XML;
- spike artwork;
- package IDs;
- motion profiles;
- shared WFF engine;
- Aurelius;
- release/signing/store paths;
- production ATTITUDE paths.

## 1. Recompute duration and extraction truth

`verify_frame_manifest()` must not trust derived fields merely because they are present.

From primitive manifest facts, independently recompute and compare:

- `expected_frame_count_from_media = round(actual_media_duration_s * extraction_fps)`;
- extraction tolerance using the authoritative greater-of-two-frames-or-1% rule;
- extraction frame delta;
- extraction disposition;
- `duration_ratio = actual_media_duration_s / intended_duration_s`;
- capture-duration disposition using PASS ≥95%, PARTIAL ≥80% and BLOCKED <80%;
- actual listed frame count;
- `ffmpeg_returncode == 0`.

Reject:

- missing, non-numeric, NaN, infinite, zero or negative durations/FPS;
- zero/negative intended duration;
- mismatched derived values;
- nonzero ffmpeg return code;
- extraction disposition other than PASS;
- PARTIAL or BLOCKED capture duration.

Do not trust the session index's duplicated duration fields. Compare them with the verified manifest if they remain present, or remove them from the index if they serve no authoritative purpose.

## 2. Replace the contradictory happy fixture

The current fixture records approximately 1.33 seconds of actual media for 40 frames at 30 fps while claiming a 30-second intended recording and ratio 1.0.

Make fixture evidence semantically coherent.

Preferred approach for fast tests:

- use a short test-only intended duration equal to `nframes / extraction_fps`;
- compute every derived field through the same production helper used by real extraction;
- never type duration ratio, disposition, expected count, tolerance or delta independently in the fixture.

Add a direct regression proving the old contradictory combination fails finalization.

## 3. Make verified analysis files authoritative

Refactor analysis verification to return the parsed, hash-verified analysis document together with structured findings.

Use that verified document—not `SESSION.json` index copies—as the source for:

- `status`;
- `mask_scan`;
- measured metrics;
- binding fields;
- final machine-result summaries.

The session index may locate the file and store its hash, but must not override the file's contents.

Add deliberate tests:

- analysis file says clipping exposed, index says clean → `MACHINE_ISSUE`;
- analysis file says clean, index says exposed → either integrity mismatch or verified file wins, under a documented rule;
- analysis file and index status disagree → fail closed;
- final `machine_measured_results` comes from verified analysis files, not mutable index summaries.

## 4. Revalidate installed, built and source bytes

At finalization, independently resolve and hash:

- installed pullback path from `installed_verification.pullback_path`;
- built APK path from the session binding;
- `SPIKE_MANIFEST.json` from the recorded source-manifest binding.

Require:

- all files exist;
- installed pullback hash equals the recorded installed hash;
- installed pullback hash equals the accepted built APK hash;
- built APK hash equals the session binding;
- source manifest hash equals the session binding;
- package/variant identity remains coherent.

Add deliberate failures for missing and modified pullback, built APK and source manifest.

## 5. Verify analysis-code binding

`analysis_code_sha256` must be compared, not merely present.

For this spike use the fail-closed policy:

- analysis is valid only when its recorded code hash equals the current authoritative analysis implementation hash;
- if harness analysis code changes after capture, block until analysis is rerun and rebound deliberately.

Record the policy in the result schema and tests.

Add failures for missing and mismatched code hash.

## 6. Fix the real CLI extraction path

The CLI currently prints `expected_frame_count`, but the manifest now uses `expected_frame_count_from_media`.

Fix the output and add a CLI-level regression test that exercises the successful `extract-frames` dispatch and proves:

- no `KeyError`;
- exit code 0;
- output reports actual count and media-derived expected count;
- the evidence files remain written.

Do not test only the helper function; test `main()` or an equivalent real command dispatch.

## 7. Use real path ancestry

Replace string prefix/substring containment with resolved path ancestry via `Path.is_relative_to()` or an equivalent parent traversal.

Apply it to:

- permitted evidence roots;
- session-only frame containment;
- analysis files;
- raw captures;
- frame manifests;
- installed pullback.

Add sibling-prefix escape tests such as a path under `SESSION-evil` when the valid session is `SESSION`.

## 8. Verify optional AOD evidence when present

Rules:

- absent AOD screenshot is allowed only under the existing protocol disposition;
- `NOT_OBTAINABLE` is acceptable only for the documented doze/display-pipeline reason;
- a present screenshot claiming PASS must have a real file, matching hash/size and correct capture ID;
- a black or missing present PASS screenshot fails closed.

Do not allow arbitrary reasons to use `NOT_OBTAINABLE` as an escape hatch.

## 9. Manifest and finding consistency

Strengthen frame-manifest verification to require and validate:

- ffprobe version and command;
- ffmpeg version and command;
- ffmpeg return code;
- actual media duration;
- intended duration;
- extraction FPS;
- expected media-derived count;
- tolerance;
- delta;
- extraction disposition;
- capture-duration disposition;
- listed frame count and every frame hash.

Unknown, missing, malformed or contradictory values are `BLOCKED_INTEGRITY`.

Trustworthy adverse findings remain `MACHINE_ISSUE`.

Owner answers never waive either state.

## 10. Tests

Keep all existing tests and add targeted failures for at least:

1. contradictory actual/intended duration ratio;
2. incorrect duration disposition;
3. incorrect expected frame count;
4. incorrect extraction tolerance;
5. incorrect extraction delta;
6. nonzero ffmpeg return code;
7. non-PASS extraction disposition;
8. clipping hidden by a clean session index;
9. analysis/index status disagreement;
10. missing pullback file;
11. pullback hash drift;
12. built APK missing or drifted;
13. source manifest missing or drifted;
14. analysis-code hash missing;
15. analysis-code hash mismatch;
16. successful CLI extraction dispatch;
17. sibling-prefix path escape;
18. present AOD PASS screenshot missing;
19. present AOD PASS screenshot hash drift;
20. arbitrary NOT_OBTAINABLE AOD reason.

The genuine happy path must use real coherent fixture files and reach `PENDING_OWNER_REVIEW`, never by placeholder indexes or manually contradictory derived fields.

## Final validation

Run:

- all spike tests;
- all existing engine and visual suites;
- WFF v4 validation for all variants;
- deterministic spike generation;
- full clean APK rebuild and byte comparison;
- Python syntax checks;
- `git diff --check`;
- path isolation gates.

Confirm explicitly:

- no installation;
- no physical device contact;
- no adb device command executed outside fake tests;
- no XML/art/package/profile change;
- no AAB/signing/release/store change;
- no shared-engine/Aurelius/production ATTITUDE change.

## Report and stop

Commit and push.

Report:

- prior and new heads;
- exact APK hashes/sizes before and after;
- duration/extraction recomputation rules;
- verified analysis source-of-truth behavior;
- installed/built/source/code revalidation behavior;
- CLI regression result;
- path-containment implementation;
- AOD optional-evidence rules;
- total tests and deliberate-failure count;
- every preserved boundary.

STOP for ChatGPT re-review. Do not install or contact the Watch7.
