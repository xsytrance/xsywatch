# Claude Clarification — Phone-Mediated ATTITUDE Installation Away From Home

This supplements `docs/instructions/CLAUDE_ATTITUDE_WATCH7_DEVICE_SESSION.md`.

## The owner does not need to be physically home

The controlling condition is not the owner's location. The controlling conditions are:

1. the Watch7 is physically with the owner;
2. the owner explicitly chooses what activity should begin;
3. the accepted APK bytes are preserved;
4. the formal evidence harness is used only when the machine running it can actually reach the Watch7 over the approved wireless-ADB path.

Do not treat “I am not home” as an automatic blocker.

## Two distinct modes

### Mode A — Phone-mediated manual installation / visual preview

The owner may receive an accepted APK on the Android phone and install it onto the Watch7 using an owner-controlled Wear OS phone-side installer that communicates with the watch over wireless ADB.

This qualifies as manual installation outside the harness. The harness must not invoke or automate it.

Requirements:

- use only the accepted APK bytes and exact package IDs;
- show the owner the exact profile, filename, package ID, full SHA-256, and byte size before transfer;
- do not rename or rebuild the APK in a way that changes its bytes;
- transfer through an owner-approved channel;
- the owner performs the phone-to-watch installation;
- record which APK was installed and when;
- do not claim installed-byte verification until the formal harness later pulls the installed APK back and hashes it;
- label any immediate viewing as `PREVIEW_ONLY` and non-evidentiary;
- do not collect, grade, or finalize formal device evidence in this mode;
- do not infer motion approval from casual preview use.

The three distinct package IDs may coexist on the watch.

Accepted artifacts:

- DAMPED
  - package: `com.xsytrance.attitude.spike.damped`
  - SHA-256: `c1121f3433e8b453f1ddfe64c6576adddae8271fab54e6ae4a67540ae60fbea6`
  - bytes: `2483983`
- PROPOSED
  - package: `com.xsytrance.attitude.spike.proposed`
  - SHA-256: `c38e04493841d4bb3d015dfe76ed42cd7001fc5c140c115993d56b764ce31b00`
  - bytes: `2484015`
- ASSERTIVE
  - package: `com.xsytrance.attitude.spike.assertive`
  - SHA-256: `99a3150e2c2a505ae0084d91e3fe9f3d775b04449ba791f4698a6669e5f2c03b`
  - bytes: `2484031`

### Mode B — Formal controlled evidence session

The formal session still requires the validated harness environment to reach the Watch7 over wireless ADB.

Being away from home is acceptable only when that harness host has a real, owner-approved network path to the watch and all normal pairing, serial, pullback, capture, extraction, analysis, and finalization requirements can be satisfied.

Do not improvise an unreviewed Termux port, tunnel, relay, VPN exposure, remote ADB bridge, or modified harness merely to avoid waiting. Such a change would require a new offline review.

An APK installed earlier through Mode A may remain installed. At the later formal session:

1. initialize the profile session normally;
2. run `verify-installed`;
3. require the pulled-back installed APK to match the accepted built APK exactly;
4. proceed only after `VERIFIED`.

If the pullback hash matches, reinstallation is not inherently required.

## Owner-gate interpretation

The owner may explicitly choose either:

- “Send me the APKs for a phone-mediated preview only.”
- “Start the formal Watch7 evidence session.”

These are different authorizations.

A request for phone-mediated preview does not authorize formal captures, finalization, production motion selection, MERIDIAN refinement, release work, signing, packaging, store preparation, or merge.

## Immediate Claude behavior

When the owner says they have the Watch7 but are away from home:

1. explain the two modes above;
2. ask which mode they want;
3. if they choose preview, prepare the accepted APKs for owner transfer without contacting the watch or changing the files;
4. if they choose formal testing, confirm the harness host can actually reach the watch before any device action;
5. never equate physical location with readiness.
