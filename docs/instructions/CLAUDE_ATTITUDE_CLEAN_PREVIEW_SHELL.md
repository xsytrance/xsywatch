# Claude Next Task — ATTITUDE Clean Motion Preview Shell

Repository: `xsytrance/xsywatch`

Branch: `preview/attitude-motion-shell`

This branch was created from the accepted spike branch after the phone-mediated preview clarification. Do not require exact HEAD equality because this instruction file is itself the first commit on the preview branch.

Read first:

- `docs/reports/ATTITUDE_HORIZON_DEVICE_READINESS_FINAL_REVIEW.md`
- `docs/instructions/CLAUDE_ATTITUDE_PHONE_MEDIATED_INSTALL_OPTION.md`
- `spikes/attitude-horizon/generate_spike.py`
- `spikes/attitude-horizon/SPIKE_MANIFEST.json`

## Purpose

Build a separate, clean, preview-only watch-face shell that lets the owner judge the motion behavior on the wrist without the deliberately ugly disposable-spike artwork contaminating the impression.

The current spike APKs are correct engineering artifacts. Their source intentionally says the visuals are crude and must not be mistaken for product. The owner has now seen them on-device and understandably found the block text, placeholder hands and visual hierarchy confusing.

This task does **not** replace, modify or invalidate the accepted spike APKs or the formal device harness.

The clean shell is only for a phone-mediated subjective preview. It is not formal evidence and must never be fed into the accepted harness as though it were one of the validated spike packages.

## Hard separation

Create the preview implementation under a new isolated root such as:

`previews/attitude-motion-shell/`

Do not modify any file under:

- `spikes/attitude-horizon/app/`
- `spikes/attitude-horizon/build/`
- `spikes/attitude-horizon/device_harness.py`
- the accepted spike APK output locations;
- the shared WFF engine;
- Aurelius;
- production ATTITUDE or MERIDIAN paths;
- release, signing or store paths.

The three accepted spike APKs must remain byte-identical:

- DAMPED: `c1121f3433e8b453f1ddfe64c6576adddae8271fab54e6ae4a67540ae60fbea6`
- PROPOSED: `c38e04493841d4bb3d015dfe76ed42cd7001fc5c140c115993d56b764ce31b00`
- ASSERTIVE: `99a3150e2c2a505ae0084d91e3fe9f3d775b04449ba791f4698a6669e5f2c03b`

After the preview build, clean-rebuild the accepted spike artifacts and prove those hashes are unchanged.

## Motion contract — exact copy, no interpretation

The clean preview shell must use the exact same motion formulas, clamps and gains as the accepted spike.

Shared input clamps:

- wrist roll clamp: ±45°;
- wrist pitch clamp: ±40°;
- roll direction uses the same negative-gain behavior as the spike;
- neutral input maps exactly to zero;
- no smoothing, easing, interpolation, filtering or hysteresis;
- AOD forces neutral roll and neutral pitch.

Profiles:

### DAMPED

- displayed roll: ±14°;
- displayed pitch: ±14 px.

### PROPOSED

- displayed roll: ±22°;
- displayed pitch: ±26 px.

### ASSERTIVE

- displayed roll: ±30°;
- displayed pitch: ±34 px.

Tests must compare the preview expressions and evaluated endpoints against the accepted spike generator, not merely duplicate expected numbers in two places.

## Package and coexistence contract

Create three distinct preview packages that can coexist with each other and with all accepted spike packages:

- `com.xsytrance.attitude.preview.damped`
- `com.xsytrance.attitude.preview.proposed`
- `com.xsytrance.attitude.preview.assertive`

Use clear watch-face names:

- `ATTITUDE Preview — DAMPED`
- `ATTITUDE Preview — PROPOSED`
- `ATTITUDE Preview — ASSERTIVE`

Version name should clearly include `preview`, not `spike`, `rc`, `release` or `production`.

No signing setup beyond the ordinary local debug build. No AAB.

## Visual goal

Create a clean, calm, modern aviation-instrument shell that makes the horizon motion easy to judge without pretending to be final MERIDIAN artwork.

It should look intentional and pleasant enough to wear briefly, but still clearly be a preview instrument rather than a luxury production face.

### Required normal-mode hierarchy

Use the same 480×480 round canvas and the same SEXTANT-like rounded-letterbox aperture geometry as the formal spike so the apparent motion scale remains comparable:

- aperture center: `(240, 252)`;
- half-width: `156`;
- half-height: `74`;
- corner radius: `42`.

Outside the aperture:

- matte black or very dark graphite field;
- extremely restrained concentric or radial detailing;
- no decorative fake screws, fake tourbillon, fake branding or product-polish claims;
- no giant analog hands crossing the aperture;
- no confusing glyph alphabet;
- no unreadable rasterized text.

Inside the aperture:

- deep desaturated aviation blue sky;
- warm restrained umber/bronze ground;
- crisp neutral horizon line;
- sparse, thin pitch ladder;
- small fixed center aircraft datum or wing index that remains stationary;
- moving horizon field beneath the fixed datum;
- enough contrast to judge roll and pitch without glowing neon.

Typography:

- actual readable text using a standard WFF/system-supported font or another clearly licensed, repository-safe method;
- no custom block alphabet;
- no pseudo-digital characters.

Display only:

- real current time in a simple digital format near the top, outside the aperture;
- exact profile label near the bottom: `DAMPED`, `PROPOSED` or `ASSERTIVE`;
- small `MOTION PREVIEW` or `PREVIEW ONLY` line;
- optional tiny `ATTITUDE` title if it remains visually quiet.

Do not add date, steps, heart rate, battery, complications, seconds, animations unrelated to the horizon, or production branding. This is a motion-comparison instrument, not a feature demo.

### AOD

AOD must:

- force the horizon to neutral roll and neutral pitch;
- use a much darker simplified shell;
- retain only the time, fixed datum and a very faint neutral horizon if useful;
- remove pitch ladder clutter where possible;
- retain a small readable profile label so the owner knows which preview is selected;
- avoid large bright regions.

This is not WO-P7 compliance evidence. Label any AOD metrics as concept-only.

## No analog hands

Do not include analog hour or minute hands in the preview shell. They obstructed the aperture in the disposable spike and made it harder to understand what was being tested.

Use a simple real digital time display instead.

## Visual review artifacts

Before sending APKs to the owner, generate and commit review pixels under:

`previews/attitude-motion-shell/review/`

At minimum:

1. `NORMAL_DAMPED.png`
2. `NORMAL_PROPOSED.png`
3. `NORMAL_ASSERTIVE.png`
4. `AOD_DAMPED.png`
5. `AOD_PROPOSED.png`
6. `AOD_ASSERTIVE.png`
7. `NORMAL_COMPARISON.png`
8. `AOD_COMPARISON.png`
9. `MOTION_STATES_PROPOSED.png`

The three normal renders should be visually identical except for the profile label. The three AOD renders should likewise be identical except for label. Motion states should show neutral and representative negative/positive roll and pitch extremes.

Record dimensions and SHA-256 values in a machine-readable review manifest.

Do not claim visual approval from hashes. The owner and ChatGPT must see actual pixels.

## Build outputs

Produce three debug APKs with unambiguous filenames:

- `attitude-preview-damped-debug.apk`
- `attitude-preview-proposed-debug.apk`
- `attitude-preview-assertive-debug.apk`

Record for each:

- package ID;
- app/watch-face label;
- full path;
- SHA-256;
- byte size;
- version name/code;
- motion profile values;
- debug certificate identity;
- confirmation that no permissions were added.

The preview APKs may be sent to the owner after the committed review renders are available for inspection. Do not install them and do not contact the Watch7.

## Preview disclaimer

Include a short README and machine-readable manifest that state:

- `PREVIEW_ONLY: true`;
- `FORMAL_EVIDENCE_ALLOWED: false`;
- `PRODUCTION_ASSET: false`;
- `RELEASE_CANDIDATE: false`;
- `OWNER_PIXEL_APPROVED: false`;
- accepted spike/harness results remain authoritative for formal testing;
- subjective preview impressions must be disclosed before later formal owner observations;
- phone-mediated installers may re-sign/repackage, so these preview packages are never substitutes for pullback-verified accepted spike builds.

## Tests and gates

Add isolated tests proving at minimum:

- exact package IDs and coexistence;
- exact motion expressions match the accepted spike for neutral, clamps and several intermediate points;
- no smoothing/easing/filtering tokens;
- exact aperture geometry matches the accepted spike;
- AOD transforms force neutral;
- readable literal profile names are present;
- no custom `_blocky` glyph renderer is used;
- no analog hand resources/elements exist;
- only approved preview paths changed;
- no permissions;
- WFF v4 validation passes;
- deterministic regeneration;
- review images and manifest hashes match;
- accepted spike APK hashes remain byte-identical;
- no production, Aurelius, shared-engine, release, signing, store or formal-harness files changed.

Include deliberate-failure tests for:

- altered motion gain;
- wrong roll sign;
- non-neutral AOD;
- package collision with a spike package;
- missing `PREVIEW_ONLY` disclosure;
- accidental analog hand element;
- unreadable/custom glyph path;
- changed accepted spike APK hash;
- production-path contamination.

## Execution and stop condition

1. Implement the isolated clean preview shell.
2. Generate all review PNGs and manifests.
3. Build all three debug preview APKs.
4. Run every preview test plus all existing spike gates needed to prove isolation.
5. Clean-rebuild and re-hash the accepted spike APKs.
6. Commit and push only the preview branch.
7. Report exact commit, changed files, tests, deliberate failures, review-image hashes and preview-APK hashes.
8. Stop for ChatGPT and owner pixel review.

Do not install anything. Do not contact the Watch7. Do not begin the formal evidence session. Do not begin MERIDIAN refinement. Do not merge.