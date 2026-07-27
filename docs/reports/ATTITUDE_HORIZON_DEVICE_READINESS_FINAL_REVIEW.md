# ATTITUDE Horizon Spike — Final Device-Readiness Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `spike/attitude-horizon-watch7`  
**Commit reviewed:** `6f1098dcb8ad2f10dd6110ab96e458930b538cd5`  
**Verdict:** **OFFLINE HARNESS ACCEPTED; CONTROLLED WATCH7 DEVICE SESSION AUTHORIZED ONLY AFTER EXPLICIT OWNER START**

## Final ruling

The source-of-truth patch closes the six remaining findings from the prior re-review.

Accepted:

- duration and extraction derivations are recomputed from recorded primitive facts rather than trusted as typed dispositions;
- malformed, non-finite, non-positive and contradictory duration/extraction fields fail closed;
- the previously contradictory success fixture is replaced with semantically coherent evidence generated through the production helpers;
- parsed, hash-verified analysis files are authoritative for machine results and clipping findings;
- analysis/index disagreements fail closed;
- the installed APK pullback, accepted built APK and spike source manifest are resolved and rehashed from disk;
- analysis code identity is compared against the current harness under an explicit fail-closed code-drift policy;
- path containment uses resolved ancestry rather than textual prefix or substring checks;
- the successful `extract-frames` CLI path uses the current manifest key and is covered with a real locally generated video;
- a present AOD screenshot claiming PASS is revalidated, while NOT_OBTAINABLE is limited to the documented doze/display-pipeline condition;
- full-frame clipping analysis remains unsampled and non-waivable by owner preference;
- all three accepted APKs remain byte-identical.

The original finalization loophole and the later source-of-truth gaps are closed. No additional offline harness patch is required before attempting the controlled device experiment.

## Accepted debug artifacts

| Profile | Package | SHA-256 | Bytes |
|---|---|---|---:|
| DAMPED | `com.xsytrance.attitude.spike.damped` | `c1121f3433e8b453f1ddfe64c6576adddae8271fab54e6ae4a67540ae60fbea6` | 2,483,983 |
| PROPOSED | `com.xsytrance.attitude.spike.proposed` | `c38e04493841d4bb3d015dfe76ed42cd7001fc5c140c115993d56b764ce31b00` | 2,484,015 |
| ASSERTIVE | `com.xsytrance.attitude.spike.assertive` | `99a3150e2c2a505ae0084d91e3fe9f3d775b04449ba791f4698a6669e5f2c03b` | 2,484,031 |

These are disposable debug artifacts, not release candidates.

## Test evidence boundary

The submitted report records:

- 171 spike tests;
- 45 deliberate-failure cases;
- WFF v4 validation PASS for all three variants;
- deterministic generation and byte-identical clean rebuilds;
- no installation and no device contact;
- no watchface XML, artwork, package-ID, motion-profile, shared-engine, Aurelius, signing, release, store or production ATTITUDE change.

The repository connector can inspect the committed implementation and tests but cannot independently execute the local Android/ffmpeg suite. The local totals are therefore accepted as submitted, with the committed tests and exact artifact hashes providing the audit trail.

## Device-session authorization

The physical experiment may begin only when the owner explicitly tells Claude that the Watch7 is available and that the session should start.

Authorization is limited to:

1. owner-controlled Watch7 developer/wireless-debugging setup;
2. manual owner installation of the accepted debug APKs;
3. harness session initialization, installed-APK pullback verification, named captures, frame extraction, analysis and finalization;
4. explicit owner observations for each profile;
5. preservation of all raw evidence until ChatGPT review.

The harness must not install anything automatically. A failed integrity check, machine issue, crash/ANR, partial capture, code drift, hash mismatch, clipping finding or unsupported AOD result must be reported as recorded; it must never be hand-edited into a pass.

## Operational caveat

AOD screencapture behavior is platform-dependent. `NOT_OBTAINABLE` is acceptable only when the recorded reason is the documented doze/display-pipeline limitation. If the actual device produces a different failure mode, stop and report the raw behavior rather than changing the evidence manually.

## Required test order

Run profiles in this order to reduce expectation bias and preserve the planned progression:

1. DAMPED;
2. PROPOSED;
3. ASSERTIVE.

Complete and preserve one profile session before starting the next. Distinct package IDs allow all three artifacts to coexist, but the owner must visibly select the correct face before each profile capture.

## Stop condition

After all obtainable profile sessions are finalized, stop before:

- selecting the production motion contract;
- refining MERIDIAN;
- modifying the shared engine;
- creating a release candidate or AAB;
- signing, store preparation or merge.

ChatGPT must review the machine results, owner observations and representative visual evidence before ATTITUDE production work resumes.
