# Claude Next Task — ATTITUDE Spike Finalization Integrity

Pull:

- repository: `xsytrance/xsywatch`
- branch: `spike/attitude-horizon-watch7`
- expected head: `040166b122deb26a6fe0c207dd9c928f08cfa991`

Read first:

- `docs/reports/ATTITUDE_HORIZON_HARNESS_FINALIZATION_CHATGPT_REVIEW.md`
- `docs/instructions/CLAUDE_NEXT_TASK_ATTITUDE_SPIKE_HARNESS.md`

The harness architecture is accepted. The physical device session remains blocked because `finalize` currently trusts the presence of evidence indexes rather than independently proving that the referenced evidence is valid and successful.

Nothing may be installed or contacted during this assignment.

## Preserve accepted artifacts

Before editing, record the three accepted debug APK hashes and sizes from `BUILD_RECORD.json`.

After the patch, perform a full clean rebuild. All three APKs must remain byte-identical:

- DAMPED: `com.xsytrance.attitude.spike.damped`
- PROPOSED: `com.xsytrance.attitude.spike.proposed`
- ASSERTIVE: `com.xsytrance.attitude.spike.assertive`

If any APK changes, stop and explain why. Do not silently replace the accepted hashes.

Do not modify:

- any spike watchface XML;
- any spike artwork;
- package IDs;
- motion profiles;
- shared WFF engine;
- Aurelius;
- release/signing/store paths;
- production ATTITUDE paths.

## 1. Define explicit machine dispositions

Create one authoritative set of machine-evidence dispositions. Use clear names such as:

- `MEASURED`
- `PASS`
- `CLEAN`
- `NOT_OBTAINABLE`
- `ISSUE`
- `BLOCKED`
- `PARTIAL`

Define which dispositions are acceptable for each evidence type.

Examples:

- mandatory motion analysis must be `MEASURED` and satisfy its integrity checks;
- crash/ANR evidence must be `CLEAN` to be machine-complete;
- AOD cycle evidence must execute and stage all ten cycles, otherwise it is `PARTIAL` or `ISSUE` and blocks completion;
- normal screenshot must be captured successfully;
- AOD screenshot may be `NOT_OBTAINABLE` only for the documented doze/display-pipeline limitation;
- owner observations remain separate and may stay `PENDING` after machine evidence is complete.

Unknown, missing, malformed or contradictory dispositions fail closed.

## 2. Add reusable evidence-verification functions

Implement small verification functions used by `finalize`, rather than one large permissive loop.

At minimum provide functions equivalent to:

- verify raw-capture record;
- verify frame-manifest record;
- verify every frame entry;
- verify analysis record;
- verify capture-specific disposition;
- verify machine findings.

Each function must return structured findings or raise a fail-closed error. Avoid boolean-only results with no reason.

## 3. Revalidate mandatory raw captures at finalization

For every mandatory capture:

- resolve each recorded file path;
- require the file to exist when the record claims successful capture;
- recompute SHA-256;
- compare with the stored hash;
- compare byte count where recorded;
- require the capture ID in the record to match the session key;
- reject path escape outside the session or explicitly permitted evidence root;
- reject duplicate or contradictory capture records.

A stored SHA field without an existing matching file is not evidence.

Normal screenshot rules:

- `screenshot_normal` is mandatory and must contain a real captured PNG;
- missing, empty, black, malformed or `NOT_OBTAINABLE` normal screenshots block finalization.

AOD screenshot rules:

- `screenshot_aod` remains optional;
- an entirely black doze screencap may be `NOT_OBTAINABLE` with the existing documented reason;
- no non-obtainable AOD screenshot may be represented as PASS.

## 4. Revalidate frame manifests and frames

For each mandatory video capture:

- require a frame-manifest index in the session;
- resolve the manifest file;
- require it to exist;
- recompute and compare its SHA-256;
- parse it;
- require its capture ID to match;
- require its source-video hash to equal the verified raw-video hash;
- require extraction FPS, ffmpeg version and exact command;
- require actual frame count to equal the number of listed frame entries;
- require every listed frame to exist and match its SHA-256;
- reject duplicate frame paths;
- reject paths outside the session frame directory;
- require a nonzero frame count.

Record frame-count quality explicitly. A materially incomplete extraction must not quietly pass merely because some frames exist.

Choose and document a reasonable tolerance for actual frame count versus capture duration at 30 fps. Distinguish minor encoder timing variance from a clearly truncated capture. Add tests at the boundaries.

## 5. Harden `extract-frames`

The extraction command must:

- inspect `ffmpeg` return code;
- preserve stdout/stderr or a deterministic error excerpt in failure evidence;
- block on nonzero return code;
- block on zero extracted frames;
- record expected count, actual count, ratio and disposition;
- never delete or overwrite the raw recording;
- continue recording ffmpeg version and exact command.

Add deliberate failures for nonzero ffmpeg return and zero output.

## 6. Revalidate analysis files at finalization

For every mandatory video analysis:

- require the session analysis index;
- resolve the analysis JSON;
- require it to exist;
- recompute and compare its SHA-256;
- parse it;
- require matching capture ID;
- require `status == MEASURED` for mandatory motion/rest evidence;
- reject `BLOCKED`, `PARTIAL`, missing, unknown or malformed status;
- verify raw-capture hash against the raw evidence;
- verify frame-manifest hash against the verified manifest;
- verify analysis-code hash against the current accepted harness code or a clearly recorded session code hash;
- verify variant, built APK hash, installed pullback hash, model, Android version and API against the session;
- require `smoothing_applied == false`.

The known loophole must receive a direct regression test:

> A mandatory resting analysis with `status: BLOCKED` because too few frames were measurable must cause finalization status `BLOCKED`, never `PENDING_OWNER_REVIEW`.

Replace the existing machine-complete fixture that uses fake placeholder paths/hashes with real deterministic fixture files that survive every integrity check.

## 7. Validate findings, not only record presence

Finalization must evaluate machine findings:

- any mandatory rest or sweep analysis with blocked status blocks;
- any mask-edge exposure is an `ISSUE` and blocks machine completion;
- crash/ANR findings are an `ISSUE` and block machine completion;
- fewer than ten successfully staged AOD cycles is `PARTIAL` or `ISSUE` and blocks machine completion;
- required raw or derived evidence with integrity drift blocks;
- unknown dispositions block.

Keep separate arrays in `DEVICE_RESULT.json`, for example:

- `blocking_integrity_problems`;
- `machine_issues`;
- `not_obtainable`;
- `pending_owner_observations`.

Suggested final statuses:

- `BLOCKED_INTEGRITY`
- `MACHINE_ISSUE`
- `PENDING_OWNER_REVIEW`
- `COMPLETE`

Exact names may differ, but a machine issue must never be represented as owner-pending success.

## 8. Scan motion evidence for clipping across time

Current analysis checks mask-edge exposure on only the midpoint frame. That can miss clipping at the actual pitch/roll extreme.

For motion captures, inspect the full relevant frame set or use a deterministic, documented sampling strategy that necessarily includes:

- first and last frames;
- minimum measured angle frame;
- maximum measured angle frame;
- minimum measured pitch/displacement frame;
- maximum measured pitch/displacement frame;
- each held extreme in `extremes_combined`.

The safest option is an efficient full-frame aperture scan. Optimize the implementation if needed, but do not hide or smooth results.

Record:

- frames checked;
- frames with exposure;
- worst exposed-pixel count and percentage;
- paths/hashes of offending frames.

Any exposure is an `ISSUE`.

Add a fixture where only a non-midpoint extreme frame is uncovered and prove it is detected.

## 9. AOD evidence rules

Keep the static WFF proof that ambient angle and displacement are constants.

For physical evidence:

- preserve ten cycle telemetry;
- require exactly ten cycles;
- record each sleep and wake state;
- classify partial staging honestly;
- analyze any obtainable AOD screenshot or samples;
- allow physical AOD imagery to remain `NOT_OBTAINABLE` only for the known pipeline limitation;
- never convert non-obtainable imagery into a visual PASS.

Owner observation of whether the visible watch face remains neutral stays separate and PENDING until explicitly answered.

## 10. Tests

Use fake adb and deterministic fixture files. No physical device command may execute.

Add deliberate-failure coverage for at least:

1. mandatory analysis exists but has `status: BLOCKED`;
2. analysis JSON file missing;
3. analysis JSON hash mismatch;
4. analysis binding disagrees with session variant;
5. analysis raw hash disagrees with capture;
6. analysis frame-manifest hash disagrees;
7. mandatory raw file missing;
8. mandatory raw hash drift;
9. frame manifest file missing;
10. frame manifest hash drift;
11. source-video hash mismatch;
12. listed frame missing;
13. listed frame hash drift;
14. zero frames;
15. materially truncated extraction;
16. ffmpeg nonzero return code;
17. normal screenshot `NOT_OBTAINABLE`;
18. partial AOD cycles;
19. crash or ANR findings;
20. mask exposure only at a non-midpoint extreme;
21. unknown evidence status;
22. placeholder analysis index whose referenced file does not exist;
23. owner answers cannot override a machine issue;
24. no installation command is reachable;
25. no real adb or physical-device contact occurs in tests.

Also prove the successful path with real deterministic fixture files and exact bindings, resulting in `PENDING_OWNER_REVIEW` while owner answers remain pending.

## 11. Validation

Run:

- all spike harness tests;
- all existing spike gates;
- clean rebuild of all three APKs;
- official WFF validation for all variants;
- APK hash/size comparison before and after;
- Python syntax checks;
- `git diff --check`;
- changed-path isolation checks.

## 12. Final report

Commit and push the branch, then report:

- prior head;
- new head;
- files changed;
- exact final status model;
- raw-evidence verification behavior;
- frame-manifest/frame verification behavior;
- analysis verification behavior;
- clipping scan behavior;
- ffmpeg failure and frame-count handling;
- total tests and deliberate-failure count;
- successful deterministic fixture result;
- three APK hashes and sizes before/after;
- confirmation APKs are byte-identical;
- confirmation no installation occurred;
- confirmation no device was contacted;
- confirmation no watchface XML/artwork/package ID changed;
- confirmation no AAB, signing, release, store, shared-engine, Aurelius or production ATTITUDE path changed.

STOP after the finalization-integrity patch and offline validation.

Do not install anything. Do not begin the physical device session until ChatGPT re-reviews this patch and the owner explicitly says they are home and ready.
