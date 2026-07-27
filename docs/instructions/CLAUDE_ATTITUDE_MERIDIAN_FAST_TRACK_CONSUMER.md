# Claude Task — ATTITUDE MERIDIAN Fast-Track Consumer Build

## Purpose

Build the first complete installable ATTITUDE — MERIDIAN development watch face now.

This is not another motion shell and not another disposable engineering face. The owner has explicitly asked to move faster and wants the actual watch face.

Work on branch:

`feature/attitude-meridian-fast-track`

This branch was created from the clean consumer base, separate from the disposable spike and preview branches.

Coordinate with studio branch:

- repository: `xsytrance/AGENOR-Horology`
- branch: `phase-2/attitude-meridian-fast-track`
- instruction: `docs/instructions/CLAUDE_ATTITUDE_MERIDIAN_FAST_TRACK_STUDIO.md`

## Fast-track rule

Build a complete development APK in the same work cycle as the studio V1.

Do not stop for another architecture packet, provisional shell, or preliminary approval round. Use the studio exports, build the face, generate review renders, run tests, and provide the APK for owner installation.

The owner may install this development build immediately after successful local validation. It is still not a release candidate.

## Development identity

Product name:

`ATTITUDE — MERIDIAN DEV`

Use a development-only package ID that cannot collide with the spike or preview packages, for example:

`com.xsytrance.attitude.meridian.dev`

Do not use any existing Aurelius, spike, or preview package ID.

Use:

- debug signing only;
- no release signing block;
- no AAB;
- no store metadata;
- no permissions unless a required WFF declaration already exists and is justified.

## Actual full watch-face requirements

Implement the complete MERIDIAN V1 supplied by the studio branch, including:

- analog hour and minute hands;
- refined center pinion;
- seconds indication if supported without harming battery/readability;
- applied hour indices;
- low circular artificial-horizon aperture;
- date;
- battery percentage or integrated battery arc;
- step count;
- heart rate;
- restrained AGENOR/ATTITUDE/MERIDIAN branding;
- separate AOD resources and behavior.

This must look and behave like a real watch face, not a diagnostic screen.

## Data behavior

Use live WFF data sources supported by the existing engine/toolchain for:

- date;
- battery;
- steps;
- heart rate.

Where a value is unavailable or permission-dependent, use the project’s established fail-safe display behavior rather than inventing data.

Do not hard-code fake health values in the installable face.

For static review renders, clearly label any representative sample values as render-only fixtures.

## Motion module

The horizon motion must be isolated from the visual composition.

Support named development configurations:

- `damped`: ±14° roll, ±14 px pitch;
- `proposed`: ±22° roll, ±26 px pitch;
- `assertive`: ±30° roll, ±34 px pitch;
- `roll-only`;
- `static`.

Use **PROPOSED** as the initial development default.

Keep the motion contract in one obvious configuration/generator location so the later formal Watch7 result changes constants or mode without requiring artwork or layout reconstruction.

Do not import production code from the disposable spike. Reuse the accepted mathematical contract accurately, but keep product implementation in the normal consumer architecture.

AOD must force neutral roll and pitch.

## AOD

Implement the separate studio AOD design:

- neutral horizon;
- no sensor motion;
- hands brightest;
- highly reduced annulus;
- no dominant filled bright sky/ground field;
- reduced data;
- no seconds animation;
- no decorative reflections.

Run the project’s available AOD metrics and report them honestly as development metrics, not WO-P7 certification.

## Review and owner iteration

Generate:

- normal 480 × 480 render;
- AOD 480 × 480 render;
- hand-position comparison sheet;
- motion-state sheet;
- at least one watch-sized presentation image suitable for direct owner review.

Do not require a separate preliminary review before producing the APK.

After all local gates pass, provide the exact development APK to the owner with:

- full path;
- package ID;
- SHA-256;
- byte count;
- debug certificate identity;
- explicit statement that it is a development build, not a release candidate.

Do not install it automatically and do not contact the Watch7. The owner will transfer/install it manually.

## Testing

Add focused tests for:

- package isolation;
- live-data expressions exist and are not fake constants;
- motion profiles and default selection;
- AOD neutral motion;
- asset hashes match studio export manifest;
- no analog-hand collision failures at 10:09, 12:00, 3:15, 6:30, and 8:40;
- no uncovered horizon pixels at the supported PROPOSED extremes;
- debug-only build configuration;
- no AAB/release/signing/store state;
- no changes to accepted spike APKs/harness;
- no Aurelius changes.

Run all relevant existing engine and visual tests.

## Speed and judgment

Do not spend another cycle proving that every internal document references every other document. Keep the evidence sufficient and content-addressed, but prioritize a functioning, visually complete build.

Fix obvious defects directly. Report them afterward.

If a non-critical decorative decision is ambiguous, choose the stronger premium-watch option and continue.

## Boundaries

Authorized:

- full MERIDIAN development implementation;
- installable debug APK;
- live date/battery/steps/heart-rate data;
- provisional PROPOSED motion default;
- owner manual installation and informal wrist feedback.

Not authorized:

- release candidate designation;
- final motion selection;
- AAB;
- production signing;
- store preparation;
- merge to main;
- shared-engine changes unless absolutely necessary and separately justified;
- Aurelius changes;
- changes to the accepted disposable spike or its evidence harness.

## Completion report

Push the branch and report:

- commit SHA;
- studio export commit and manifest hash consumed;
- package ID;
- APK path, SHA-256, byte count, and certificate;
- selected provisional motion profile;
- data expressions used;
- normal/AOD/motion review image paths and hashes;
- AOD metrics;
- test totals;
- confirmation that no device was contacted and nothing was installed automatically.

Then send the development APK to the owner. Do not wait for another infrastructure review unless a genuine blocker appears.