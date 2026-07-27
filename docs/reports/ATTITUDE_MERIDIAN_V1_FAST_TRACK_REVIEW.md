# ATTITUDE — MERIDIAN V1 Fast-Track Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `feature/attitude-meridian-fast-track`  
**Consumer implementation reviewed:** `b79df235ba63ac908db131704c0b1ff0de4cf2e1`  
**Studio authority reviewed:** `xsytrance/AGENOR-Horology` `phase-2/attitude-meridian-fast-track` at `2da909ac51c22c6f742d68a72c4544bf2253556b`  
**Verdict:** **OFFLINE IMPLEMENTATION ACCEPTED FOR IMMEDIATE OWNER WRIST TRIAL; NOT YET OWNER PIXEL APPROVED OR RELEASE-READY**

## What is accepted

MERIDIAN V1 is a complete development watch face, not another interaction shell.

Accepted architecture and scope:

- unique development package `com.xsytrance.attitude.meridian.dev`;
- Watch Face Format v4 analog face;
- studio-controlled, hash-recorded asset import;
- broad hour/minute hands, normal-only seconds hand and separate AOD hand resources;
- live `[DAY]`, `[BATTERY_PERCENT]`, `[STEP_COUNT]` and `[HEART_RATE]` bindings with no invented fallback values;
- integrated battery/reserve needle;
- low circular reactive artificial-horizon aperture;
- provisional PROPOSED motion profile, isolated to one component;
- DAMPED, ASSERTIVE, roll-only and static alternatives preserved in the design contract;
- structural AOD neutrality through a separate frozen horizon layer;
- separate normal and AOD dial compositions;
- minimal general engine additions for a reactive horizon field and normal/AOD layer swapping;
- no production signing, AAB, store state, release candidate, publication or merge.

The committed XML confirms that the moving horizon alone carries accelerometer transforms, while the ambient horizon is a separate transform-free image. It also confirms that normal and ambient hands are separate resources and that the four readouts bind live WFF sources.

The studio import binds the consumer face to the exact studio commit and records hashes for the imported resources. The aperture chamfer note is accepted: the visible opening being approximately two pixels smaller than the conservative geometric opening is intentional artwork behavior, not a coverage defect.

## Engine ruling

The shared-engine changes are accepted for this development branch.

No prior component produced the required simultaneous accelerometer-driven counter-rotation and vertical translation. Adding a general `horizon_field` component is preferable to bypassing the repository's consumer architecture with face-local handwritten XML.

The reported Aurelius byte-identical drift result is accepted as submitted. The GitHub connector can inspect the committed implementation and tests but cannot independently execute the local Android, image-rendering or WFF validation suites.

## Immediate device authorization

The owner may install and select the exact development APK already supplied:

- path: `watchfaces/attitude-meridian/app/build/outputs/apk/debug/app-debug.apk`;
- package: `com.xsytrance.attitude.meridian.dev`;
- version: `0.1.0-dev` (`versionCode 1`);
- reported SHA-256: `9ec178add0b7233a285a43a5727a1bcc842a1b93d3b4af489e85a2c3fd41f8ea`;
- reported bytes: `2,802,909`;
- debug certificate subject: `CN=Android Debug, O=Android, C=US`.

Phone-mediated manual installation is acceptable. No formal 45–60 minute evidence session is required before the first wrist reaction.

The first wrist trial should answer practical product questions quickly:

1. Does the complete dial look premium at actual Watch7 size?
2. Are the time hands immediately readable?
3. Does the horizon feel integrated rather than pasted into the dial?
4. Does PROPOSED motion feel deliberate or distracting?
5. Are date, battery, steps and heart rate legible?
6. Does AOD remain clean and readable?
7. Is the 3:15 date crossing objectionable on the real wrist?

Owner-uploaded on-wrist photos or video are required before final pixel approval. Repository hashes and render prose are not substitutes for seeing the actual Watch7 display.

## Non-blocking audit correction

The implementation commit does not currently contain a committed build record binding the exact development APK identity to the source commit. The APK hash, size and certificate are present in Claude's report but not in a repository evidence file.

Add:

`watchfaces/attitude-meridian/BUILD_RECORD.json`

It should record at minimum:

- schema and development-only status;
- consumer commit and studio commit;
- package, version name and version code;
- APK path, SHA-256 and byte count;
- certificate subject and certificate SHA-256;
- clean-rebuild byte-identity result;
- WFF validation result;
- test totals and repository-validation result;
- AOD metric method and consumer-render result;
- explicit false values for release candidate, AAB, production signing, store state and merge authorization.

This is a documentation/evidence correction only. It does **not** block installation of the exact APK already supplied and must not trigger an unnecessary visual or motion redesign.

## Current boundaries

Do not yet:

- call the face owner pixel approved;
- select the final motion profile;
- merge into main;
- create an AAB or release candidate;
- add production signing or store metadata;
- alter Aurelius;
- begin publication work.

After the first wrist photos/video and owner reaction, make one consolidated correction pass rather than returning to another long planning cycle.
