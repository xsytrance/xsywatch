# Claude Next Task — ATTITUDE Watch7 Controlled Device Session

Pull:

- repository: `xsytrance/xsywatch`
- branch: `spike/attitude-horizon-watch7`
- branch must contain final review commit: `05d294c97b808bdff1f57c5809a21d21c2fda8f9`

Do not require exact HEAD equality: this instruction file is committed after the review it references.

Read first:

- `docs/reports/ATTITUDE_HORIZON_DEVICE_READINESS_FINAL_REVIEW.md`
- `docs/reports/ATTITUDE_HORIZON_FINALIZATION_INTEGRITY_REREVIEW.md`
- `spikes/attitude-horizon/device_harness.py`

## Owner gate

Do **nothing involving adb, installation or the Watch7** until the owner explicitly says they are ready, the watch is available, and the device session should begin.

Before that explicit message, only explain readiness and wait.

Once the owner explicitly starts the session:

- confirm the current branch contains this instruction and the final review;
- confirm the working tree is clean;
- confirm the three APK hashes exactly match the accepted values below;
- run the offline spike tests and gates before device contact;
- stop immediately if any offline check fails.

Accepted APKs:

- DAMPED: `c1121f3433e8b453f1ddfe64c6576adddae8271fab54e6ae4a67540ae60fbea6`
- PROPOSED: `c38e04493841d4bb3d015dfe76ed42cd7001fc5c140c115993d56b764ce31b00`
- ASSERTIVE: `99a3150e2c2a505ae0084d91e3fe9f3d775b04449ba791f4698a6669e5f2c03b`

The harness may contact the explicitly owner-approved serial after the owner starts the session, but it must never install an APK.

## Manual installation boundary

The owner performs every installation manually outside the harness.

For each package:

1. show the exact accepted APK path, package ID, full SHA-256 and manual `adb install -r` command;
2. pause;
3. require the owner to confirm that they manually executed the command;
4. then use `verify-installed` to pull back and compare the installed bytes.

Never execute an install command yourself. Never bypass pullback verification.

## Profile order

Run profiles in this order:

1. `damped`;
2. `proposed`;
3. `assertive`.

Do not start the next profile until the prior session is preserved and finalized.

For each profile, require the owner to select the matching watchface visibly on the Watch7 before captures begin. Confirm the expected package ID:

- `com.xsytrance.attitude.spike.damped`
- `com.xsytrance.attitude.spike.proposed`
- `com.xsytrance.attitude.spike.assertive`

## Per-profile workflow

Use the actual serial supplied or confirmed by the owner.

### 1. Initialize

Run the equivalent of:

```bash
python3 spikes/attitude-horizon/device_harness.py session-init \
  --serial <OWNER_CONFIRMED_SERIAL> \
  --variant <damped|proposed|assertive>
```

Record the created session path. Do not install automatically.

### 2. Owner manual install

Show the exact command. Wait for owner confirmation.

### 3. Verify installed bytes

```bash
python3 spikes/attitude-horizon/device_harness.py verify-installed \
  --session <SESSION_DIR>
```

Require `VERIFIED`. Any missing package, ambiguous path, pullback failure or hash mismatch stops that profile.

### 4. Confirm visible face

Ask the owner to select the correct ATTITUDE Horizon Spike profile from the Watch7 face picker and confirm that the correct profile is visible.

Do not infer this from package installation alone.

### 5. Capture exactly one named item at a time

Run all required captures:

- `rest_surface_60s`
- `rest_wrist_60s`
- `sweep_roll_l_to_r`
- `sweep_roll_r_to_l`
- `sweep_pitch`
- `extremes_combined`
- `aod_cycles`
- `screenshot_normal`
- `screenshot_aod`
- `logs_crash_anr`

Use:

```bash
python3 spikes/attitude-horizon/device_harness.py capture \
  --session <SESSION_DIR> \
  --capture <CAPTURE_ID>
```

Before each human-motion capture, repeat the harness instruction clearly and allow the owner to get into position.

Do not hide, retry over or replace a failed capture without preserving and reporting the original result. If a retry is needed, stop and ask for ChatGPT guidance unless the harness already defines an unambiguous safe retry procedure.

### 6. Extract every video

For each video capture:

```bash
python3 spikes/attitude-horizon/device_harness.py extract-frames \
  --session <SESSION_DIR> \
  --capture <CAPTURE_ID>
```

Require command exit `0`, measured media duration, PASS extraction integrity and PASS capture-duration disposition. Preserve raw video.

### 7. Analyze every required video

```bash
python3 spikes/attitude-horizon/device_harness.py analyze \
  --session <SESSION_DIR> \
  --capture <CAPTURE_ID>
```

Require raw unsmoothed output. Do not alter metrics. Do not waive clipping.

### 8. Owner observations

Ask the owner the session-specific questions and write only their explicit answers into that profile's `OWNER_OBSERVATION.json`.

Do not copy answers between profiles. Do not infer answers from measurements or silence.

At minimum capture explicit judgments on:

- stability at rest;
- roll direction;
- pitch direction;
- strength/aggressiveness;
- premium versus gimmicky feel;
- excessive pitch travel;
- visible mask edges or empty pixels;
- AOD neutrality.

### 9. Finalize

```bash
python3 spikes/attitude-horizon/device_harness.py finalize \
  --session <SESSION_DIR>
```

Interpret status exactly:

- `BLOCKED_INTEGRITY`: stop; evidence cannot be trusted;
- `MACHINE_ISSUE`: stop that profile and preserve everything;
- `PENDING_OWNER_REVIEW`: machine evidence is complete but owner answers remain;
- `COMPLETE`: machine evidence is complete and profile answers are explicit.

Never edit evidence to change status.

## Cross-profile comparison

After all obtainable sessions are complete, ask the owner explicitly:

- preferred profile;
- whether DAMPED is too weak;
- whether PROPOSED feels premium;
- whether ASSERTIVE feels excessive;
- whether pitch should remain;
- whether roll direction is intuitive;
- whether pitch direction is intuitive;
- final horizon preference: two-axis reactive, roll-only, reduced-motion, static or rejected.

Record unanswered items as `PENDING`.

## Evidence preservation and report

Preserve all local session directories and raw evidence. Do not delete, overwrite, normalize or recompress raw captures.

Do not commit large raw videos or full frame sets automatically.

After the sessions, report to the owner and ChatGPT:

- branch HEAD;
- device serial, manufacturer/model, Android version and API level;
- per-profile package, built APK hash and installed pullback hash;
- each session directory;
- every capture disposition;
- extraction duration/count/tolerance results;
- stability and sweep metrics;
- full-frame clipping results;
- AOD outcomes;
- crash/ANR findings;
- final session statuses;
- explicit owner observations and final comparison;
- exact files that should be uploaded for visual review.

If representative screenshots are needed, ask the owner to upload them directly to ChatGPT. Do not claim pixel approval from hashes or prose.

## Boundaries

Do not:

- alter the harness during a session;
- change watchface XML, artwork, package IDs or motion profiles;
- modify the shared engine or Aurelius;
- begin MERIDIAN refinement;
- create an AAB or release candidate;
- add signing or store state;
- merge the branch;
- delete raw evidence.

Stop after reporting the physical evidence. ChatGPT must review the results before any production ATTITUDE work begins.
