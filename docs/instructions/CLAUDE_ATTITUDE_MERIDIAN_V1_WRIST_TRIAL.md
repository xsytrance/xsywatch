# Claude Next Task — ATTITUDE MERIDIAN V1 Wrist Trial

Pull:

- repository: `xsytrance/xsywatch`;
- branch: `feature/attitude-meridian-fast-track`;
- branch must contain review commit `43b38fe3f3a8e296202e86761b731eeae7eccd7d`.

Read first:

- `docs/reports/ATTITUDE_MERIDIAN_V1_FAST_TRACK_REVIEW.md`;
- `watchfaces/attitude-meridian/README.md`;
- `watchfaces/attitude-meridian/engine/face.toml`.

## Priority

Do not start another design or validation cycle before the owner sees MERIDIAN V1 on the Watch7.

The exact development APK already supplied is authorized for immediate manual installation. The owner may install it from the phone. Do not install anything automatically and do not contact the Watch7 until the owner explicitly starts or asks for help.

Accepted APK identity from the submitted report:

- package: `com.xsytrance.attitude.meridian.dev`;
- version: `0.1.0-dev` (`versionCode 1`);
- SHA-256: `9ec178add0b7233a285a43a5727a1bcc842a1b93d3b4af489e85a2c3fd41f8ea`;
- bytes: `2,802,909`;
- certificate subject: `CN=Android Debug, O=Android, C=US`.

Do not rebuild or replace the already-sent APK merely to perform this follow-up.

## Parallel audit correction

Create:

`watchfaces/attitude-meridian/BUILD_RECORD.json`

Bind the exact already-built development artifact to:

- consumer source commit `b79df235ba63ac908db131704c0b1ff0de4cf2e1`;
- studio source commit `2da909ac51c22c6f742d68a72c4544bf2253556b`;
- package, version name and version code;
- APK path, full SHA-256 and byte count;
- certificate subject and full certificate SHA-256;
- clean-rebuild byte-identity result;
- WFF v4 result;
- engine and visual test totals;
- repository validation result;
- generation-drift result for Aurelius and MERIDIAN;
- consumer-render AOD metric, with exact method and an explicit non-WO-P7 statement;
- `release_candidate: false`;
- `aab_created: false`;
- `production_signing: false`;
- `store_state: false`;
- `merge_authorized: false`;
- `owner_pixel_approved: false`.

Use the existing artifact and existing recorded results. Do not alter watchface XML, resources, motion values, engine behavior or package identity for this evidence-only patch.

Add focused validation proving the build record agrees with the actual existing APK when that artifact is present locally. If the local output has been deleted, do not silently rebuild and claim it is the same artifact; report that limitation and preserve the submitted identity separately.

Commit and push the build-record patch, but do not make the owner wait for that commit before installing the already-supplied APK.

## Owner wrist trial

Once the owner confirms installation, ask for a fast first-pass review rather than launching the formal spike harness.

Request:

1. one straight-on normal-mode wrist photo;
2. one tilted-wrist photo or short video showing horizon motion;
3. one AOD photo;
4. one photo around 3:15 if practical, to evaluate date occlusion;
5. a brief reaction covering premium feel, time readability, motion feel, data readability and anything obviously wrong.

If a health or activity field shows `0`, first determine whether the relevant watch permission is granted. Do not replace it with a fabricated fallback value.

Do not infer pixel approval from render hashes or prose. The owner should upload the Watch7 photos/video directly to ChatGPT.

## After feedback

Stop after the build-record patch and the first wrist-trial report.

Do not independently redesign the face. ChatGPT will consolidate the actual wrist findings into one correction pass.

Do not:

- merge;
- select a final motion profile;
- create an AAB or release candidate;
- add production signing or store metadata;
- modify Aurelius;
- begin publication work.
