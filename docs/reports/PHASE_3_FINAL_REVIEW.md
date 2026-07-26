# Phase 3 Final Architecture and Pixel Review

**Consumer repository:** `xsytrance/xsywatch`  
**Branch reviewed:** `phase-3/premium-aurelius-visual-lineage`  
**Consumer head reviewed:** `a56f73e14bedefd9fe5aa57e5e8cde056b37a063`  
**Paired studio repository:** `xsytrance/AGENOR-Horology`  
**Studio head reviewed:** `d44714c99598b99cd201b1bb0c4c707d501326a1`  
**Review date:** 2026-07-26  
**Verdict:** **APPROVED FOR PROMOTION AND MERGE**

## Final product-owner decision

**APPROVAL-0004 / `field-tourbillon-mk2-r2` is accepted as rendered in normal and AOD modes.**

The approved product direction is the owner-selected Olive Instrument design tuned with Black Titanium Command restraint, using the audited OFL-1.1 Rajdhani Bold glyph and engraving source. Revision r2 is the first premium Aurelius visual generation approved to replace `field-tourbillon-v1` as the repository's active golden baseline.

The following earlier candidates remain intentionally unapproved historical evidence:

- `field-tourbillon-mk2` / APPROVAL-0002 — Bfont-derived proposed candidate;
- `field-tourbillon-mk2-r1` / APPROVAL-0003 — OFL correction with disclosed plate-composition defects.

They must not be deleted, rewritten, or promoted.

## Accepted r2 visual corrections

### Date aperture

The date aperture is accepted.

- deterministic proof covers all days `1..31` in normal and AOD modes;
- 62 renders produced zero violations;
- worst deterministic clear margin is 3.07 px against the 2 px contract;
- the physical Watch7 shows the live day fully inside the frame;
- the aperture measures 40 × 30 px on device and in the reference render;
- the frame is integrated at actual watch scale and does not collide with adjacent mechanics.

The qualified 2 px device measurement is accepted as corroborating evidence. The deterministic domain proof remains authoritative, consistent with ADR-009's `qualitative-behavioral-lineage` policy.

### Lower engraving

Removal of `FIELD TOURBILLON Mk II` from the plate is accepted.

The physical comparison confirms that the removal leaves intentional negative space rather than an unfinished void. The restrained `AURELIUS` signature remains clean and legible. The complete model name remains available in metadata, picker copy, documentation, and future release material.

## Architecture acceptance

Phase 3's architecture is approved in full:

- deterministic resource inventory and reference rendering;
- exact visual-change records and supersession history;
- normal/AOD candidate and golden separation;
- permanent same-name/wrong-art WARBIRD regression fixtures;
- commit-snapshot and LFS-aware studio provenance;
- committed-metadata binding;
- two-phase asset import with rollback;
- exact handoff asset and changed-resource coverage;
- derived-asset provenance and notice enforcement;
- OFL Rajdhani substitution with exact font checksum;
- full-domain aperture proof and regression tests;
- dynamic/parallax-aware physical-device validation policy;
- immutable historical release enforcement.

The installed-device chain is stronger than the original Phase 3 requirement: the candidate APK was pulled back from the Watch7 and hashed, and `bg.png`, `bg_aod.png`, and `res/raw/watchface.xml` extracted from that installed APK match repository source bytes. The verified chain is therefore:

`studio source → producing commit → metadata commit → handoff manifest → imported resources → inventory → candidate APK → installed APK → physical panel`.

## Accepted qualifications

The following are accepted and non-blocking:

- direct AOD screencapture remains unavailable through the Watch7 doze pipeline; repeated captures produce the same black artifact;
- exact device-screenshot comparison is not a valid hard gate for Aurelius because continuously rotating layers and accelerometer-driven full-screen sheen cannot be pinned at capture time;
- physical validation for this face is therefore visual, behavioral, and byte-lineage based, while deterministic committed-reference comparison remains exact.

These qualifications are now accurately encoded in ADR-009 and `states.toml` rather than being informal exceptions.

## Final artifact bindings

- r2 candidate APK: `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a`
- r2 inventory: `b76f9ceb01b555a4915448bb8408e8d008937c484913b033491f5c9e3875c269`
- r2 normal reference: `7fd2cf63607e2aa6ef53d0443c44e16885284705d5f4336602aa3ce2526a556e`
- r2 AOD reference: `2f2be0e91b7473b5bb492cdc55094777d570a268f36e751d109be56888f1e936`
- studio producing commit: `c8c29dc`
- studio metadata-stamping commit before promotion: `5cf8f04`
- immutable Phase 1 release: `844b9c43…` — unchanged

## Required promotion sequence

No further architecture re-review is required if the promotion is mechanical and all gates remain green.

1. Promote the studio handoff metadata from `candidate` to `approved` without changing export bytes or producing-source attribution.
2. Commit that metadata-only studio promotion.
3. Merge `phase-3/aurelius-studio-slice` into `AGENOR-Horology/main` with a normal non-squashed `--no-ff` merge and push it.
4. In `xsywatch`, re-import or synchronize the now-approved studio metadata through the hardened importer so the consumer manifest records the final metadata commit and `approved` lifecycles.
5. Update APPROVAL-0004:
   - `owner.status = "approved"`;
   - identify AGENOR as the approving owner and record 2026-07-26;
   - `architecture_review.status = "approved"`;
   - reference this final-review commit.
6. Promote r2 references to `visual/goldens/field-tourbillon-mk2-r2/` while preserving every candidate and earlier golden as history.
7. Set `approved_version = "field-tourbillon-mk2-r2"` and remove/clear `proposed_version`.
8. Preserve APPROVAL-0001 through APPROVAL-0003, all prior inventory snapshots, all prior device evidence, and the complete WARBIRD/Bfont investigations.
9. Do not change `releases/aurelius/current/`, package a production release, or create signing keys.
10. Run all engine, visual, aperture, handoff, release, build, WFF, memory, repository, whitespace, and CI gates.
11. Merge `phase-3/premium-aurelius-visual-lineage` into `xsywatch/main` with a normal non-squashed `--no-ff` merge and push it.
12. Verify both branches are fully contained in their corresponding `main` histories and both working trees are clean.

## Merge-history requirement

Preserve the complete Phase 3 history, including:

- initial visual-lineage gate and concept checkpoint;
- WARBIRD-class fixtures;
- original Mk II candidate;
- review findings and corrections;
- Bfont investigation;
- Rajdhani r1 revision;
- r1 physical findings;
- r2 composition correction;
- installed-device byte-lineage evidence;
- this final approval.

Do not squash, rebase, rewrite, or force-push.

## Final verdict

**Phase 3 is complete. Aurelius Field Tourbillon Mk II r2 is approved as the first premium visual golden and the two Phase 3 branches are approved for promotion and merge in studio-first order.**

## Verification boundary

This review inspected repository history, source and metadata diffs, approval records, visual contracts, validation tools, test coverage, provenance records, reports, and the committed textual/device artifacts available through GitHub. It did not independently rerun Blender, Gradle, ADB, or video analysis. Reported local and physical-device results are accepted where they are checksum-bound and internally consistent.
