# Claude Next Task — ATTITUDE Disposable Spike Harness Readiness

**Status:** AUTHORIZED OFFLINE HARNESS PATCH ONLY  
**Branch:** `spike/attitude-horizon-watch7`  
**Expected starting head:** `7b6ff12485867eb8c9275c9ebcbe10cd3fe052e3`

Read the ChatGPT offline review added at the expected starting head. Locate it with:

`git show --name-only 7b6ff12485867eb8c9275c9ebcbe10cd3fe052e3`

The current product ruling is:

- MERIDIAN is the selected future ATTITUDE visual direction.
- The spike must **not** be redesigned around MERIDIAN.
- The SEXTANT-like rounded letterbox remains the correct stress-test geometry because it exaggerates pitch travel and clipping risk.
- The three existing debug APKs are accepted and should remain byte-identical.
- No installation or physical-device command is authorized during this task.
- No production ATTITUDE implementation is authorized.

## 1. Preserve accepted APKs

Before editing, record exact APK hashes and sizes from `spikes/attitude-horizon/BUILD_RECORD.json`.

Expected identities:

- `com.xsytrance.attitude.spike.damped` — roll ±14°, pitch ±14 px;
- `com.xsytrance.attitude.spike.proposed` — roll ±22°, pitch ±26 px;
- `com.xsytrance.attitude.spike.assertive` — roll ±30°, pitch ±34 px.

Shared clamps:

- wrist roll ±45°;
- wrist pitch ±40°;
- neutral maps exactly to zero;
- AOD forces zero roll and zero pitch;
- no smoothing, filtering, or easing.

After the harness patch, perform a full clean rebuild. All three APKs should remain byte-identical because this task must not alter WFF XML or visual resources.

If any APK hash changes, stop, identify the exact source, and do not silently update expected hashes.

## 2. Implement a real fail-closed session model

Use session directories such as:

`spikes/attitude-horizon/device-evidence/sessions/<timestamp>-<variant>/`

Each session must contain or ultimately produce:

- `SESSION.json`;
- pulled installed APK;
- raw captures;
- raw-capture manifest;
- extracted-frame manifest;
- analysis results;
- final device result;
- session-specific owner-observation record.

Every session must bind to:

- selected variant;
- package ID;
- repository HEAD at session creation;
- spike source-manifest hash;
- built APK path and SHA-256;
- installed APK pullback SHA-256;
- device serial;
- manufacturer/model;
- Android version;
- API level;
- timestamp.

Missing binding blocks the session.

## 3. Installation remains manual

The harness must never invoke any install command, including:

- `adb install`;
- `adb install-multiple`;
- package-manager install commands;
- equivalent automatic installation mechanisms.

The harness may print the exact manual install command, but the owner performs it separately.

Add tests that capture every subprocess/adb command and prove no installation path is reachable through any CLI command.

## 4. Required executable CLI operations

Implement clear, separately invokable operations. Equivalent names are acceptable only if behavior remains explicit.

### `session-init`

Example:

`device_harness.py session-init --serial SERIAL --variant proposed`

Must:

- validate variant;
- validate built APK presence;
- hash the built APK;
- confirm device reachability;
- collect model/manufacturer, Android version, and API;
- create the session directory;
- write initial fail-closed `SESSION.json`;
- never install anything.

### `verify-installed`

Example:

`device_harness.py verify-installed --session SESSION_DIR`

Must:

- derive expected package from variant;
- call `adb shell pm path PACKAGE`;
- require one unambiguous base APK path;
- pull the installed APK;
- hash it;
- compare against the accepted built APK hash;
- block on mismatch;
- record package path, pullback path, and both hashes.

No capture may run before successful verification.

### `capture`

Example:

`device_harness.py capture --session SESSION_DIR --capture rest_surface_60s`

Implement exactly these capture IDs:

- `rest_surface_60s`;
- `rest_wrist_60s`;
- `sweep_roll_l_to_r`;
- `sweep_roll_r_to_l`;
- `sweep_pitch`;
- `extremes_combined`;
- `aod_cycles`;
- `screenshot_normal`;
- `screenshot_aod`;
- `logs_crash_anr`.

For video captures:

- use a declared adb screen-recording command;
- use fixed declared duration;
- preserve device-side filename in metadata;
- pull raw recording;
- hash it;
- remove the device temporary only after successful pull and hash.

For screenshots:

- capture lossless PNG;
- preserve and hash the raw file.

For AOD cycles:

- perform exactly ten sleep/wake cycles;
- record timestamps and wakefulness/power-state output;
- preserve command output;
- if AOD screenshot is unavailable, record `NOT_OBTAINABLE`, never PASS.

For logs:

- capture crash buffer;
- scan main/system buffers for fatal exceptions and ANRs;
- preserve raw logs.

Human-motion captures should print a countdown and exact movement instructions but must not alter evidence.

### `extract-frames`

Example:

`device_harness.py extract-frames --session SESSION_DIR --capture rest_surface_60s`

Use a deterministic declared extraction method, preferably fixed-rate `ffmpeg` extraction appropriate for jitter analysis.

Record:

- source-video SHA-256;
- ffmpeg version;
- exact command;
- extraction FPS;
- expected and actual frame counts;
- every frame path and SHA-256.

Never overwrite raw recordings.

### `analyze`

Example:

`device_harness.py analyze --session SESSION_DIR --capture rest_surface_60s`

Connect the existing raw, unsmoothed analysis functions to extracted frames.

For resting captures report:

- measurable and failed frames;
- median angle;
- p95 absolute angular deviation;
- maximum angular excursion;
- median vertical displacement;
- p95 absolute vertical deviation;
- maximum vertical excursion;
- maximum frame-to-frame angular step;
- oscillation/sign-change behavior.

For sweep captures report:

- response direction;
- monotonic fraction;
- observed minimum and maximum;
- observed clamp;
- discontinuities;
- mask-edge exposure.

For AOD report:

- whether a measurable horizon exists;
- measured angle and displacement;
- whether obtainable samples remain neutral;
- any detected movement.

No smoothing is permitted.

Every analysis record must bind to:

- raw-capture hash;
- frame-manifest hash;
- analysis-code hash;
- variant;
- built APK hash;
- installed pullback hash;
- device identity;
- timestamp.

### `finalize`

Example:

`device_harness.py finalize --session SESSION_DIR`

Must refuse completion if any mandatory binding or evidence is missing, including:

- installed pullback verification;
- built/pullback equality;
- device identity;
- required captures or explicit acceptable disposition;
- analysis;
- raw hashes;
- derived-to-raw bindings;
- crash/ANR evidence;
- required owner observations.

Separate:

- machine-measured results;
- non-obtainable results;
- owner observations;
- pending owner observations.

Final status remains `PENDING_OWNER_REVIEW` until owner answers are explicitly entered.

## 5. Session-specific owner observations

Instantiate a session-specific fail-closed owner record for the tested profile.

Do not mutate another profile's answers or infer answers from measurements.

After all three profiles are eventually tested, final comparison must ask:

- preferred profile;
- whether DAMPED is too weak;
- whether PROPOSED feels premium;
- whether ASSERTIVE feels excessive;
- whether pitch should remain;
- whether roll direction is intuitive;
- whether pitch direction is intuitive;
- final horizon choice: two-axis reactive, roll-only, reduced-motion, static, or rejected.

Every unanswered field remains `PENDING`.

## 6. Offline tests with fake adb/subprocess

No physical device may be used. Build a fake adb/subprocess layer and test both success and deliberate failure.

Required failure coverage includes:

- missing installed pullback hash;
- built/pullback mismatch;
- wrong installed package;
- ambiguous multiple package paths;
- missing model;
- missing Android/API;
- missing raw capture;
- raw hash drift;
- missing frame manifest;
- frame manifest not bound to raw video;
- too few measurable frames;
- moving AOD;
- uncovered aperture pixels;
- analysis missing raw hashes;
- finalize with incomplete mandatory evidence;
- accidental auto-install command;
- capture before installed verification;
- session variant/package mismatch;
- cross-profile owner-answer leakage.

Also prove a deterministic successful workflow using fixture captures.

## 7. Boundaries

Do not:

- install any APK;
- connect to or use the Watch7;
- execute physical captures;
- alter the three spike WFF XML files;
- alter spike artwork;
- modify the shared WFF engine;
- modify Aurelius or any Aurelius candidate/readiness/evidence file;
- start Aurelius rc3;
- create AAB, signing, release, store, or publishing state;
- begin production ATTITUDE implementation;
- refine MERIDIAN into production assets;
- merge into main.

## Validation and final report

Commit and push the branch.

Report:

- prior head and new head;
- APK hashes/sizes before and after;
- whether all APKs remained byte-identical;
- implemented CLI operations;
- session schema and fail-closed states;
- installed-pullback verification behavior;
- capture behavior;
- frame-extraction method and tool-version binding;
- analysis outputs and bindings;
- finalization rules;
- total tests and deliberate-failure count;
- confirmation that no adb installation or physical-device command occurred;
- confirmation that no WFF XML, artwork, AAB, signing, release, store, shared-engine, Aurelius, or production ATTITUDE file changed.

**STOP after pushing. Do not install anything.**