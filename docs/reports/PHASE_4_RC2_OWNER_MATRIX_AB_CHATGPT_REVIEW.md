# Phase 4 rc2 owner matrix — Groups A and B ChatGPT review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `phase-4/aurelius-release-readiness`  
**Head reviewed:** `c9f7d51edad521dd9a234c751829c023198094dd`  
**Review date:** 2026-07-27  
**Verdict:** **EVIDENCE ACCEPTED; rc2 REMAINS BLOCKED AND IS NOT ACCEPTABLE AS-IS**

## Accepted evidence

The following work is accepted:

- Groups A and B were inspected on the physical Galaxy Watch7.
- The measured matrix remains distinct from owner-scored rows.
- Owner answers now live in `OWNER_OBSERVATIONS.json` rather than the regenerated Markdown report.
- Observations are bound to the exact rc2 APK SHA-256.
- Missing observations remain pending; unknown result values fail; observations for another artifact are ignored.
- The corrected matrix separates normal time readability from date readability.
- The clean on-wrist normal still replaces the One UI charging-overlay still.
- The 60-second motion evidence remains usable because the overlay was not present in that recording.
- The 130 bpm owner reading was not paired with the earlier 104.1 bpm face measurement because they were not simultaneous.
- `device-validated` correctly remains blocked and readiness correctly remains non-publishable.

## Date finding

The owner-reported date issue is a real release-blocking defect, not a subjective preference that can be waived by citing WCAG.

Two independent findings agree:

1. **Glance contrast:** the measured 4.53:1 normal-mode contrast narrowly clears a desktop text threshold but does not provide sufficient wrist-at-a-glance separation for this product. The physical-panel owner verdict controls.
2. **Placement:** deterministic rendering reproduces the misalignment. The current aperture proof only asserts containment and minimum margin, so it was incapable of detecting centring drift. The text is systematically high and can drift left by up to 3 px for narrow dates.

Therefore:

- rc2 cannot receive owner pixel approval;
- rc2 cannot close `device-validated`;
- the defect must not be converted to PASS through a waiver or threshold argument;
- a shipping correction requires a new package candidate and a new visual approval generation.

## Small report-accounting defect

`DEVICE_TEST_RESULTS.md` states that 17 of 26 owner rows are observed, which means 9 remain pending. Its summary table currently reports `PENDING — owner (not scored): 26`.

Correct the generated summary to report the actual result counts. Also make the scope explicit:

- Groups A and B: 15 PASS, 1 ISSUE;
- Group C permission row: 1 additional PASS;
- total observed owner rows: 16 PASS, 1 ISSUE;
- remaining owner rows: 9 PENDING.

Add a test asserting that summary counts equal the row-level counts so this cannot drift again.

## Sequence ruling

The three Group C heart-rate rows may be completed on rc2 because they validate WFF behavior that is independent of the date treatment.

Do **not** spend the final release-grade wear-session requirement on rc2. rc2 is already known to be unacceptable and any formal session is bound to its obsolete APK hash. Wearing rc2 may still be used as exploratory product research to discover additional defects, but the final Checkpoint B wear evidence must be recorded against the corrected candidate.

After the Group C rows and exploratory use are complete, the architecture recommendation is to fix the date rather than waive it.

## Required rc3 date contract

Preserve rc2, its artifacts, hashes, observations, and APPROVAL-0005 as unapproved historical evidence.

Create a new package candidate, provisionally `2.0.0-rc3`, and a new visual generation/approval record. Do not rewrite APPROVAL-0005 or reuse its visual-version identity for changed pixels.

The correction must satisfy all of the following:

### Contrast

- Establish a deterministic normal-mode composite contrast measurement using the glyph core and the actual aperture interior.
- Exclude anti-aliased fringe pixels from the core-glyph measurement.
- Adopt an internal normal-mode glance-readability target of at least **7.0:1**.
- The numerical result supplements rather than overrides physical-panel owner judgment.
- AOD must remain owner-legible and must re-pass WO-P7; it need not use the same normal-mode contrast target.

### Containment and centring

For every day 1–31 in normal and AOD:

- retain the existing minimum 2 px clear-margin containment requirement;
- calculate signed horizontal and vertical ink-centre offsets from the aperture centre;
- report both bounding-box centre and an alpha-weighted diagnostic centroid;
- require horizontal bounding-box-centre error no greater than 1 px;
- prohibit a systematic vertical bias: mean signed vertical offset must be within 0.25 px of zero;
- require no individual vertical bounding-box-centre error greater than 1 px;
- retain committed proof sheets and machine-readable per-day results;
- include deliberate-failure fixtures for horizontal drift, systematic vertical bias, insufficient contrast, and containment regression.

The alpha-weighted centroid is diagnostic rather than the sole pass/fail authority because numeral shapes are naturally asymmetric. Final optical judgment remains an owner panel check.

### Visual scope

Prefer the smallest coherent correction:

- correct the text placement/metrics rather than moving the entire complication area;
- improve normal-mode separation through the aperture treatment and/or date glyph treatment without turning it into a bright digital badge;
- preserve the restrained field-instrument hierarchy;
- preserve the approved date opening geometry unless evidence shows the opening itself must change;
- preserve all unrelated mechanics, motion, hands, reserve behavior, parallax and craftsmanship surfaces byte-for-byte where possible.

### rc3 revalidation

Because package and visual bytes will change, rc3 must receive:

- new consumer source/artifact/metadata lineage;
- new APK and AAB hashes;
- new inventory and visual delta;
- a new proposed approval record superseding APPROVAL-0005 without modifying it;
- all 62 date renders and new centring/contrast gates;
- deterministic render and diff evidence;
- WO-P7 rerun;
- clean build reproducibility;
- WFF, memory, release, readiness and repository gates;
- installed-APK pullback and installed-resource lineage;
- physical date judgment in normal and AOD;
- the final owner wear sessions bound to rc3;
- final owner pixel and disposition decisions.

## Current boundaries

Until rc3 and its final evidence are approved:

- do not merge;
- do not promote APPROVAL-0005;
- do not promote rc2 pixels or lifecycles;
- do not create production signing material;
- do not upload or publish;
- do not modify `releases/aurelius/current/`;
- do not begin another watchface.
