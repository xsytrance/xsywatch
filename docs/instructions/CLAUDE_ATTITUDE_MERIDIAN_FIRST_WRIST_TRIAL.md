# Claude Next Task — ATTITUDE MERIDIAN First Wrist Trial

Pull:

- repository: `xsytrance/xsywatch`
- branch: `feature/attitude-meridian-fast-track`
- branch must contain `docs/reports/ATTITUDE_MERIDIAN_V1_FAST_TRACK_REVIEW.md`

Read that review first.

## Goal

Move directly to the real Watch7. Do not insert another planning, render-only or formal-harness phase before the owner sees the complete face on the wrist.

## Exact APK

Send the existing development APK without rebuilding or modifying it:

- path: `watchfaces/attitude-meridian/app/build/outputs/apk/debug/app-debug.apk`
- package: `com.xsytrance.attitude.meridian.dev`
- version: `0.1.0-dev` (`versionCode 1`)
- SHA-256: `9ec178add0b7233a285a43a5727a1bcc842a1b93d3b4af489e85a2c3fd41f8ea`
- bytes: `2,802,909`

Provide the file to the owner for phone-mediated manual installation. Do not install automatically and do not contact the watch yourself unless the owner explicitly starts a connected session.

## Owner trial

After the owner installs and selects the face, ask for only:

1. one clear awake-mode wrist photo;
2. one AOD wrist photo;
3. one short video or direct description while naturally rolling and pitching the wrist;
4. whether the complete dial feels premium at actual size;
5. whether the hands are immediately readable;
6. whether the horizon feels integrated or pasted on;
7. whether PROPOSED motion feels too weak, good, too aggressive or wrong-direction;
8. whether date, battery, steps and heart rate are readable and showing plausible live values;
9. whether the 3:15 hand/date crossing is objectionable in practice.

Do not require the formal 45–60 minute spike session before this trial. The spike remains useful for final motion evidence, not as a gate to rapid development iteration.

## Small evidence correction

Add `watchfaces/attitude-meridian/BUILD_RECORD.json` in the same branch, binding the already-built APK to the source commit and studio commit. This must be documentation only. Do not rebuild, redesign or delay sending the APK for it.

Record:

- development-only schema/status;
- source commit `b79df235ba63ac908db131704c0b1ff0de4cf2e1`;
- studio commit `2da909ac51c22c6f742d68a72c4544bf2253556b`;
- package/version/path/hash/bytes;
- debug certificate subject and reported certificate SHA-256;
- byte-identical clean-rebuild result;
- WFF/test/repository-validation totals;
- AOD metrics and method;
- release candidate/AAB/production signing/store/merge all false.

Commit and push the build record, but do not wait for another ChatGPT approval before sending the exact APK.

## Stop condition

After the APK is sent and the build record is pushed, wait for the owner's on-watch photos/video and reaction. Do not begin a second design pass until that evidence arrives.