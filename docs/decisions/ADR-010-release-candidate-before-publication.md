# ADR-010 — Release Candidate Before Publication

**Status:** Accepted  
**Date:** 2026-07-26  
**Scope:** Aurelius Phase 4 and every later commercial AGENOR watch-face release

## Context

Phase 3 produced and approved `field-tourbillon-mk2-r2` as the first premium Aurelius visual golden. It also established deterministic rendering, visual-delta approval, studio-to-device resource lineage, historical-golden immutability, and physical Watch7 validation.

An approved visual generation is not yet a commercial release. Publication adds a different class of responsibilities:

- ordinary wear quality rather than only scripted correctness;
- final craftsmanship and long-term legibility;
- package/version lineage;
- reproducible release artifacts;
- signing-key custody and recovery;
- current distribution-policy compliance;
- complete licensing, provenance, support, and marketing material;
- truthful product claims;
- a deliberate launch decision.

The existing immutable release at `releases/aurelius/current/` is version `1.0` / versionCode `1`, debug-signed, and preserved as historical evidence. It must not be silently replaced by Phase 4 work.

## Decision

### 1. Phase 4 produces a release candidate, not a public release

Phase 4 will produce a sale-ready **release candidate** for Aurelius, but it will not publish the product, create or commit production signing material, or replace `releases/aurelius/current/`.

Publication requires a separate owner decision after Phase 4 review.

### 2. Release state is separate from visual approval state

The repository distinguishes:

1. **approved visual golden** — intended pixels and behavior are approved;
2. **release candidate** — versioned package, release metadata, provenance, tests, and commercial presentation are complete;
3. **published release** — signed and distributed through an explicitly approved channel.

Passing one state does not imply the next.

### 3. Aurelius Mk II receives a new package version lineage

The planned first release-candidate identity is:

- package: `com.xsytrance.aurelius`;
- versionCode: `2`;
- versionName: `2.0.0-rc1`;
- visual generation: a new reviewed refinement derived from `field-tourbillon-mk2-r2`, provisionally `field-tourbillon-mk2-rc1`.

The package/version change occurs only after the owner approves the Phase 4 craftsmanship direction. If current official distribution requirements make a different candidate naming convention necessary, the policy audit must document and justify the change before implementation.

### 4. Candidate artifacts live outside the immutable current release

Phase 4 candidate artifacts belong under a versioned candidate location such as:

```text
releases/aurelius/candidates/2.0.0-rc1/
```

The candidate record must bind at least:

- source and studio commits;
- package/version metadata;
- artifact filenames and SHA-256 values;
- approved visual version and golden hashes;
- resource inventory hash;
- build environment and toolchain versions;
- signing state;
- validation and device-evidence paths;
- licensing/provenance snapshot;
- official-policy audit date and sources;
- known limitations;
- publication status.

`releases/aurelius/current/` remains unchanged until a later explicit release decision.

### 5. Signing is a controlled release operation

No private key, keystore, password, recovery secret, or production signing token may be committed.

Phase 4 must produce a documented signing and custody plan covering:

- key purpose and ownership;
- secure creation environment;
- backup and recovery;
- access control;
- rotation and compromise response;
- distinction between development/debug, upload, and distribution signing where applicable;
- evidence that repository and CI logs contain no secret material.

A debug-signed device-test APK may be produced. A production signing identity is created only under a later explicit owner-authorized operation.

### 6. Current platform requirements must be audited, not assumed

Distribution, target-SDK, packaging, signing, metadata, image, policy, and watch-face requirements can change. Phase 4 must record a dated audit using current primary/official sources before calling the candidate submission-ready.

The repository must distinguish verified requirements from assumptions and recommendations.

### 7. Wear evidence is a release input

Scripted tests prove correctness; ordinary use reveals product friction. Phase 4 requires owner wear evidence covering readability, AOD, battery impression, motion, data behavior, accidental annoyance, and sustained premium perception.

Wear findings may trigger a narrowly reviewed visual or behavioral revision. They must not be hidden in release copy or deferred without an explicit limitation.

### 8. Craftsmanship changes remain visual-lineage governed

Any final finishing pass must create a new proposed visual version and follow ADR-009:

- studio source and exact handoff provenance;
- proposed normal/AOD references;
- resource inventory;
- reviewed visual delta;
- owner approval;
- physical Watch7 evidence;
- preservation of `field-tourbillon-mk2-r2` and every earlier generation.

The craftsmanship pass must improve finishing without adding clutter, unreviewed complications, or unnecessary continuous animation.

### 9. Commercial presentation must be truthful

Marketing may describe Aurelius as an animated mechanical or tourbillon-inspired watch face and may use its product name, but it must not imply that the smartwatch contains a physical mechanical tourbillon or make unsupported battery, health, accuracy, material, or performance claims.

Every externally facing claim must be supported by the product or clearly presented as artistic design language.

### 10. Release approval is a separate final gate

Phase 4 ends with both branches returned for owner and architecture review. Even after merge, publication remains blocked until the owner separately authorizes:

- signing;
- distribution channel;
- price;
- public listing copy and media;
- support and update commitments;
- final release promotion from candidate to published/current.

## Consequences

### Positive

- Aurelius can become commercially credible without weakening historical evidence.
- Visual approval, package readiness, signing, and publication cannot be conflated.
- The first public AGENOR product receives a reproducible, auditable release lineage.
- Current platform requirements and commercial claims are explicitly verified.
- Production secrets stay outside Git.

### Costs

- Release readiness becomes a distinct phase with wear evidence, policy research, packaging, and commercial assets.
- Final finishing changes require another visual approval record and device pass.
- Publication remains a separate decision after Phase 4.

## Supersession rule

Any later decision to replace `releases/aurelius/current/`, create production signing material, or publish a product without an approved release-candidate record requires a superseding ADR that explicitly addresses provenance, signing custody, historical immutability, and the WARBIRD failure class.