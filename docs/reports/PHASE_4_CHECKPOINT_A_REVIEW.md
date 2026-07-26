# Phase 4 Checkpoint A — Owner and Architecture Review

**Repository:** `xsytrance/xsywatch`  
**Branch reviewed:** `phase-4/aurelius-release-readiness`  
**Consumer head reviewed:** `51ef862`  
**Paired studio head reviewed:** `AGENOR-Horology@87f6f7b`  
**Review date:** 2026-07-26  
**Verdict:** **CHECKPOINT A APPROVED — PROCEED TO THE SELECTED PRODUCTION LEG**

## Owner craftsmanship selection

The selected Phase 4 craftsmanship direction is:

> **A — Command Satin, with only C — Precision Instrument's reserve-tick treatment grafted in.**

This is a controlled combination rather than a new fourth aesthetic direction.

### Keep from Command Satin

- darker, tighter DLC and charcoal response;
- refined directional satin finishing;
- selective polished bevels;
- improved screw-slot, jewel-cup, arbor and gear-edge finishing;
- refined rather than noisier dial microtexture;
- no decorative patterning.

### Graft from Precision Instrument

- the crisper reserve-tick finishing only;
- preserve the current tick count, size, position, arc geometry, reserve needle and WFF behavior.

### Explicitly reject for this generation

- Atelier Stripe / Geneva striping;
- full Precision Instrument material hierarchy;
- lighter coarse-blasted dial treatment;
- new ornament, badges, engravings, complications, layers or motion.

The target remains an elite reconnaissance field tourbillon: premium through machining and finishing, not dress-watch ornament.

## Checkpoint A architecture acceptance

The following Checkpoint A work is accepted:

- exact Phase 3 golden, inventory and APK reproduction;
- full static baseline and clean release immutability check;
- dual owner/architecture golden authorization;
- unique authoritative approved record enforcement;
- the twelve deliberate-failure tests and ambiguity refusal;
- the structured wear-log tool and artifact binding;
- the official-policy audit's use of verified, unverified and blocked states;
- non-destructive A/B/C studio proposals;
- documentation of the linked-roughness no-op and non-idempotent AOD-crush defects.

The implementation correctly leaves package metadata, approved pixels, release artifacts and signing state unchanged.

## Release-readiness blockers and decisions

### TEST-1 — Play Console account status

The 12-tester / 14-consecutive-day production-access requirement applies to personal Play developer accounts created after 2023-11-13. The repository has no evidence identifying AGENOR's account type, creation date or existing production access.

This is an owner-supplied fact and must remain unresolved until AGENOR checks Play Console.

Required owner response:

- account type: personal or organization;
- approximate creation date;
- whether **Test and release → Production** is currently accessible;
- whether a prior app has already received production access.

This uncertainty does not block craftsmanship production, AAB implementation or internal testing preparation. It may impose a minimum fourteen-day calendar gate before public launch.

### AOD-1 — official luminance metric

The one-frame lit-pixel house metric is not WO-P7 compliance evidence. Before Checkpoint B, implement or run the official average-luminance-over-time method against the selected normal/AOD candidate and record the actual result. Do not describe the current approximately-seven-percent lit-pixel figure as official compliance.

### PKG-1 / FMT-2 — bundle and API floor

Before candidate packaging:

- add a reproducible Android App Bundle build path;
- set `minSdk` consistently with WFF v4 / API 36;
- retain `targetSdk` and `compileSdk` 36 unless the dated audit requires a later value;
- test the APK and AAB outputs without changing the package name.

### Signing

Phase 4 may document and validate the upload-key workflow with disposable non-production material outside Git. It must not generate or commit the final commercial upload key without a separate explicit owner instruction.

## Wear evidence requirement

The empty wear log does not invalidate concept selection, but Checkpoint B must not be approved without ordinary-use evidence.

Before Checkpoint B, AGENOR should record at least:

1. one normal workday or equivalent sustained-use session;
2. one outdoor/daylight plus low-light/evening session;
3. one session containing sustained AOD use and a charging transition.

Sessions may overlap when one real day covers multiple environments. Battery observations remain experiential, not efficiency claims.

## Production-leg authorization

Claude Code may now:

1. commit the owner selection record;
2. produce the Command Satin + reserve-tick studio generation;
3. generate production exports and exact handoff metadata;
4. import through the hardened lineage path;
5. create the proposed `field-tourbillon-mk2-rc1` visual generation and approval record;
6. run official AOD luminance analysis;
7. add the AAB and API-36-consistent package path;
8. create versioned non-public release-candidate artifacts;
9. prepare commercial media, truthful copy, privacy/data-safety drafts, signing plan and support packet;
10. return both unmerged branches for Checkpoint B review.

## Boundaries

Do not:

- promote rc1 to approved goldens;
- merge either branch;
- publish or create a public listing;
- modify `releases/aurelius/current/`;
- create or commit production signing secrets;
- begin another watchface;
- claim official AOD compliance until the real metric passes;
- represent TEST-1 as resolved without owner evidence.

## Verdict

**Checkpoint A is approved. Proceed with Command Satin plus Precision Instrument reserve ticks as the sole production direction, while collecting wear evidence and resolving the release-policy gates before Checkpoint B.**
