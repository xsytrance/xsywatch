# Phase 4 — Aurelius Commercial Release Readiness

**Status:** Approved scope; implementation not started  
**Product:** AURELIUS — Field Tourbillon Mk II  
**Consumer repository:** `xsytrance/xsywatch`  
**Paired studio repository:** `xsytrance/AGENOR-Horology`  
**Primary device:** Samsung Galaxy Watch7 44 mm  
**Architecture owner:** ChatGPT  
**Product owner / creative director:** AGENOR / xsytrance  
**Implementation partner:** Claude Code  
**Governing decisions:** ADR-008, ADR-009, ADR-010

## 1. Phase purpose

Phase 3 proved the approved Aurelius pixels, resource lineage, engine behavior, and physical Watch7 result. Phase 4 turns that approved premium visual generation into a **commercially credible release candidate**.

This phase must answer a different question:

> Can Aurelius be rebuilt, worn, evaluated, packaged, documented, presented, and handed off for a later controlled launch without relying on undocumented knowledge, unverified claims, mutable evidence, or committed secrets?

Phase 4 is not a public launch. It ends with a release candidate and a complete launch packet returned for owner and architecture review.

## 2. Starting baseline

The authoritative starting point is:

- approved visual generation: `field-tourbillon-mk2-r2`;
- approved normal golden: `7fd2cf63607e2aa6ef53d0443c44e16885284705d5f4336602aa3ce2526a556e`;
- approved AOD golden: `2f2be0e91b7473b5bb492cdc55094777d570a268f36e751d109be56888f1e936`;
- approved inventory: `b76f9ceb01b555a4915448bb8408e8d008937c484913b033491f5c9e3875c269`;
- tested Phase 3 APK: `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a`;
- immutable historical release: `844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2`;
- package: `com.xsytrance.aurelius`;
- current source identity: versionCode `1`, versionName `1.0`;
- current historical release signing: debug / sideload only.

Phase 4 must preserve all Phase 1–3 evidence and every approved or superseded visual generation.

## 3. Target outcome

The target is an owner-approved release candidate with:

1. ordinary wear evidence;
2. a restrained final craftsmanship pass;
3. a new reviewed visual generation derived from r2;
4. a versioned release-candidate package;
5. reproducible build and checksum evidence;
6. a current official distribution-policy audit;
7. a signing/custody plan with no committed secrets;
8. complete licensing and provenance material;
9. commercial screenshots, motion media, copy, and support material;
10. final physical-device and wear validation;
11. a release-candidate manifest tying all evidence together.

The provisional identities are:

- visual version: `field-tourbillon-mk2-rc1`;
- package versionCode: `2`;
- package versionName: `2.0.0-rc1`;
- candidate channel: `releases/aurelius/candidates/2.0.0-rc1/`.

These values may change only if the dated official-policy audit identifies a concrete requirement. Any change must be documented before package implementation.

## 4. Non-goals and hard boundaries

Phase 4 must not:

- publish Aurelius;
- replace or modify `releases/aurelius/current/`;
- delete or rewrite v1, Mk II, r1, or r2 evidence;
- create or commit production signing keys, passwords, tokens, recovery codes, or keystores;
- create a public store listing;
- collect money;
- promise a launch date;
- begin WARBIRD, AlienMilitary, Ares, Pinball, or another product;
- upgrade to WFF v5;
- add new complications merely to create novelty;
- add new continuously animated layers without a demonstrated product need and performance review;
- redesign the approved layout or abandon the Olive Instrument / Black Titanium restraint identity;
- make unsupported health, battery, accuracy, luxury-material, or mechanical-watch claims;
- call a candidate a published release.

## 5. Branches

Create:

```text
xsywatch:
phase-4/aurelius-release-readiness

AGENOR-Horology:
phase-4/aurelius-craftsmanship-release-assets
```

Both branches must start from clean, current `main` branches containing the Phase 3 post-merge review and the Phase 4 scope commits.

Neither branch may be merged before final owner and ChatGPT review.

## 6. Execution model and checkpoints

Phase 4 intentionally contains two owner checkpoints.

### Checkpoint A — wear findings and craftsmanship directions

Before changing production runtime assets, return:

- baseline audit;
- owner wear-test packet and accumulated observations;
- three restrained craftsmanship proposals;
- normal and AOD previews;
- projected resource delta;
- any release-policy or packaging constraints that affect design.

Stop production refinement until AGENOR selects or combines a direction.

### Checkpoint B — release-candidate acceptance

After implementation and physical validation, return:

- the exact proposed visual/golden change;
- release-candidate package and manifest;
- commercial presentation packet;
- signing and policy documents;
- full static, device, and wear evidence;
- both unmerged branches.

Publication remains blocked after Checkpoint B until a later explicit launch decision.

## 7. Workstream 1 — baseline and release audit

Before altering any approved visual or package metadata:

1. Verify both repositories are clean and synchronized.
2. Reproduce the Phase 3 approved normal/AOD goldens byte-for-byte.
3. Rebuild the Phase 3 approved APK and verify its expected checksum where the established toolchain permits exact reproduction.
4. Run all current engine, visual, aperture, handoff, release, build, WFF, memory, repository, and whitespace gates.
5. Inventory current package/version metadata, release directories, signing state, Gradle configuration, manifest properties, previews, licenses, and product copy.
6. Confirm `releases/aurelius/current/` and its checksum are untouched.
7. Create a Phase 4 baseline report containing exact commands, toolchain versions, hashes, and observed warnings.
8. Implement the two non-blocking validator hardening items from `PHASE_3_POST_MERGE_REVIEW.md`:
   - every committed golden requires both owner and architecture approval;
   - every committed `visual_version` may have exactly one authoritative approved record.
9. Add deliberate-failure tests for owner-only approval, architecture-only approval, and duplicate approved records.

This validator hardening must not alter current approved resources or goldens.

## 8. Workstream 2 — ordinary wear evaluation

Scripted matrices remain necessary but are not sufficient for a commercial candidate.

Create a structured owner wear log under a Phase 4 evidence path. It should capture at least:

- date and approximate wear duration;
- environment: office, indoor home, outdoor daylight, low light, transit, exercise, or other relevant context;
- normal-mode readability;
- AOD readability and perceived brightness;
- date and reserve-gauge usability;
- motion smoothness and whether motion becomes distracting;
- parallax impression;
- picker/activation behavior;
- charging and wake/sleep behavior;
- battery start/end and contextual caveats;
- any missing data or stale data behavior;
- accidental taps or interaction surprises;
- whether the face still feels premium after repeated use;
- specific annoyance, clipping, glare, contrast, or hierarchy observations;
- owner disposition: keep, investigate, or change.

Target evidence should include multiple ordinary wear sessions rather than one scripted dock test, ideally covering:

- a normal workday;
- outdoor/daylight exposure;
- a low-light or evening period;
- sustained AOD use;
- at least one charging transition.

Battery observations are experiential unless the test method controls confounders. Do not convert an informal observation into a quantified efficiency claim.

The wear log may continue while the studio prepares non-destructive concept previews.

## 9. Workstream 3 — craftsmanship proposal checkpoint

The studio must produce three tightly controlled finishing directions based on the approved r2 geometry and layout.

### Direction A — Command Satin

- deepest and most restrained;
- improved blackened-metal and charcoal microtexture;
- selective satin brushing;
- subtle polished bevels only where they clarify depth;
- refined screw slots and jewel cups;
- minimal decorative patterning.

### Direction B — Atelier Stripe

- same dark military identity;
- one restrained Geneva-stripe or linear finishing treatment on a selected bridge or plate region;
- no broad decorative striping across the whole dial;
- selective anglage and edge highlights;
- warm accents remain sparse.

### Direction C — Precision Instrument

- no Geneva stripes;
- stronger machining hierarchy through bead blast, radial/brushed transitions, gear-edge definition, jewel settings, and reserve markings;
- crispest field-instrument character;
- premium through precision rather than ornament.

Each proposal must include:

- deterministic normal hero preview;
- deterministic AOD preview;
- two or more close-up crops showing the actual finishing differences;
- material and finishing change list;
- predicted affected exported resources;
- expected AOD and performance impact;
- rationale explaining why it improves sustained premium perception;
- reproducible studio source.

The proposals must preserve:

- muted olive identity;
- charcoal/black-titanium dominance;
- sparse warm-metal hierarchy;
- hand and date readability;
- approved aperture geometry;
- the single restrained `AURELIUS` signature;
- current mechanical layout and motion grammar;
- no WARBIRD, AlienMilitary, bronze-dominant, neon, or novelty tactical motifs.

Production assets must not be promoted or imported before owner selection.

## 10. Workstream 4 — selected craftsmanship implementation

After AGENOR selects or combines a direction:

1. Commit an owner-selection record in the studio repository.
2. Create a new studio generation derived from the approved r2 source.
3. Apply only the selected finishing changes.
4. Retain editable source and deterministic generation paths.
5. Preserve all r2 exports and metadata as historical approved evidence.
6. Generate exact handoff metadata tied to producing and stamping commits.
7. Import through the hardened commit-snapshot/LFS-aware importer.
8. Create a new proposed visual version, provisionally `field-tourbillon-mk2-rc1`.
9. Create a new approval record superseding APPROVAL-0004 without rewriting it.
10. Generate proposed normal/AOD references, inventory snapshot, visual diffs, heat maps, and close-up comparisons.
11. Prove that every changed resource is intentional and every unchanged resource remains byte-identical.
12. Preserve zero XML/spec delta unless a wear finding requires an explicitly reviewed behavior correction.

### Craftsmanship constraints

The pass should prioritize:

- subtle bridge finishing;
- controlled anglage highlights;
- believable screw and jewel detail;
- refined gear teeth/edge response;
- improved metallic microtexture;
- restrained reserve markings where they improve usability;
- richer depth without higher clutter;
- tasteful crystal/sheen tuning.

It must not use finishing as an excuse to redesign the product.

## 11. Workstream 5 — package and version release candidate

After the owner approves the proposed craftsmanship pixels:

1. Update the package identity to versionCode `2`, versionName `2.0.0-rc1`, unless the official-policy audit documents a necessary alternative.
2. Keep package name `com.xsytrance.aurelius` unless a verified distribution constraint requires a separately approved ADR.
3. Regenerate and verify WFF XML and Android metadata consistency.
4. Create a versioned release-candidate directory outside `current/`.
5. Produce a debug-signed sideload APK for device testing.
6. Produce the appropriate unsigned or non-public distribution candidate artifacts identified by the policy audit.
7. Record all artifact hashes, sizes, package metadata, source commits, build commands, and signing states.
8. Perform two clean builds from a documented environment and compare outputs.
9. Require exact reproducibility where the current toolchain supports it; otherwise identify the differing bytes, explain the cause, and bind the canonical artifact explicitly.
10. Ensure no secret or key material enters Git history, build logs, CI artifacts, screenshots, or reports.

## 12. Workstream 6 — current official distribution-policy audit

Create a dated report based on current official/primary sources. It must cover, as applicable:

- accepted package/artifact format;
- Wear OS / Watch Face Format eligibility;
- target SDK and API requirements;
- versioning constraints;
- signing and app-signing workflow;
- listing metadata and required declarations;
- privacy/data-safety requirements;
- health/heart-rate disclosure considerations;
- screenshots, preview, icon, and media requirements;
- testing/review-track options;
- paid-product and merchant prerequisites;
- update and package-name continuity;
- regional or device-support constraints;
- any current deadlines or policy transitions.

For every item, record:

- requirement or finding;
- official source;
- date checked;
- applicability to Aurelius;
- repository action;
- unresolved owner decision.

Do not treat blogs, memory, or old screenshots as authoritative policy.

## 13. Workstream 7 — signing and release custody plan

Create a release-signing policy without generating or committing production secrets.

The plan must cover:

- owner of the commercial signing identity;
- development/debug signing versus upload/distribution signing;
- secure key-generation procedure;
- offline or protected storage location;
- encrypted backup and recovery verification;
- access-control and least-privilege rules;
- passphrase handling;
- key rotation and compromise response;
- disaster recovery;
- release-approval ceremony/checklist;
- secret scanning and repository exclusions;
- what evidence may be committed and what must never be committed.

Phase 4 may validate tooling with disposable non-production material outside Git, but must not create the final production identity without a separate explicit owner instruction.

## 14. Workstream 8 — commercial presentation packet

Produce a complete draft launch packet, kept non-public during Phase 4.

### Required visual media

- primary product hero image;
- normal-mode watchface image;
- AOD image;
- normal/AOD comparison;
- two or more close-up craftsmanship images;
- watch-on-wrist or device-context image without misleading scale or materials;
- picker preview and app icon/source master;
- short clean motion video showing gear train, cage, hands, reserve needle, and parallax;
- optional feature graphic and vertical promotional cut.

Exports must be generated from committed source, checksum-bound, and labeled by intended channel/size after the official-policy audit.

### Required copy

- final product name;
- one-line positioning statement;
- short listing description;
- long description;
- factual feature list;
- compatibility statement;
- AOD and battery-language disclaimer;
- data/heart-rate behavior disclosure;
- support contact/process draft;
- privacy statement or confirmation that no data leaves the device, if verified;
- license and attribution notice;
- release notes;
- known limitations;
- proposed price positioning for owner decision.

### Truthfulness rules

Do not claim:

- a physical tourbillon exists in the smartwatch;
- guaranteed battery duration without controlled evidence;
- medical or diagnostic capability;
- impossible material composition;
- chronometer or mechanical accuracy certification;
- universal compatibility not tested or documented.

## 15. Workstream 9 — release-candidate validation

The final candidate must pass:

### Static and repository gates

- all engine tests;
- all visual and lineage tests;
- all historical-golden immutability tests;
- exact owner+architecture approval enforcement;
- duplicate-approved-record rejection;
- date-aperture domain proof;
- handoff/import lineage tests;
- release-workflow fixtures;
- deterministic generation;
- resource inventory validation;
- reference rendering and proposed/approved golden checks;
- all-ten build regression;
- official WFF validation;
- memory evaluation;
- repository validation;
- asset-license/provenance validation;
- candidate-manifest validation;
- secret scanning;
- `git diff --check`;
- green CI.

### Physical Watch7 matrix

At minimum:

- clean install and upgrade from the approved Phase 3 development candidate where signatures allow;
- picker preview and activation;
- normal rendering at actual scale;
- AOD behavior and repeated cycles;
- time/date/data correctness;
- date aperture for representative one- and two-digit days;
- reserve gauge across meaningful battery changes;
- cage and gear timing/direction;
- hands and legibility;
- parallax and sheen restraint;
- touch behavior;
- stability and crash/ANR review;
- sustained motion capture;
- installed-APK pullback and hash verification;
- installed resource byte-chain verification;
- explicit comparison against the approved r2 baseline.

Use the Aurelius `qualitative-behavioral-lineage` mode rather than pretending a dynamic/parallax device screenshot can be an exact pixel gate.

### Ordinary release-candidate wear

After scripted testing, the owner should wear the exact candidate artifact during ordinary use and record a final disposition. The wear artifact must be bound to the candidate APK hash and package version.

## 16. Release-candidate manifest

Create a machine-readable candidate manifest under the versioned candidate directory. It must identify:

- product and channel;
- package and version;
- publication status `not-published`;
- visual version and approval record;
- normal/AOD golden hashes;
- inventory hash;
- consumer and studio commits;
- producing and metadata commits;
- APK/bundle artifact hashes and signing states;
- immutable prior-release checksum;
- toolchain versions;
- build commands;
- reproducibility result;
- official-policy audit path/date;
- signing-policy path;
- device and wear evidence;
- commercial-media manifest;
- copy/support/privacy documents;
- license/provenance snapshot;
- known limitations;
- final review status.

Validation must fail if the manifest references missing evidence, drifting hashes, a published state without release approval, or production signing material inside the repository.

## 17. Required reports

### xsywatch

Create:

```text
docs/reports/PHASE_4_AURELIUS_RELEASE_READINESS.md
```

The report must include:

- baseline and policy audit;
- wear findings;
- selected craftsmanship direction;
- visual lineage and approval history;
- package/version changes;
- candidate manifest and artifacts;
- reproducibility evidence;
- signing plan;
- commercial packet;
- validation results;
- device and final wear evidence;
- unresolved launch decisions;
- exact commit history.

### AGENOR-Horology

Create:

```text
docs/reports/PHASE_4_AURELIUS_CRAFTSMANSHIP_RELEASE_ASSETS.md
```

The report must include:

- concept directions;
- owner selection;
- source and finishing changes;
- exact changed/unchanged exports;
- material and rendering rationale;
- handoff lineage;
- commercial source-media exports;
- verification and limitations;
- exact commit history.

## 18. Expected commit sequence

### xsywatch

1. Phase 4 baseline, validator governance hardening, wear log, and policy-audit scaffolding.
2. Release-candidate tooling, manifests, signing policy, and secret gates.
3. Selected studio handoff import, proposed visual version, and visual evidence.
4. Package/version candidate and reproducibility evidence.
5. Commercial packet and physical/wear evidence.
6. Phase report and handoff for review.

### AGENOR-Horology

1. Phase 4 studio audit and three craftsmanship proposals.
2. Owner-selection record.
3. Selected finishing source and reusable asset refinements.
4. Production exports and metadata-stamping commit.
5. Commercial media source/exports and studio report.

Do not squash after architecture review begins.

## 19. Acceptance criteria

Phase 4 is complete only when:

1. The owner wear log is committed and findings are resolved or explicitly accepted.
2. AGENOR selected the craftsmanship direction.
3. A new proposed visual generation is fully lineage-bound and owner-approved.
4. Historical r2 and earlier generations remain immutable and validated.
5. The candidate package/version is distinct from v1 and internally consistent.
6. Candidate artifacts are reproducibly built or canonicalized with explained differences.
7. The current official distribution-policy audit is complete.
8. The signing/custody plan is complete and no production secret exists in Git.
9. All licensing and provenance requirements are resolved.
10. The commercial presentation packet is complete and truthful.
11. The full static, physical-device, and candidate wear gates pass.
12. `releases/aurelius/current/` and checksum `844b9c43…` remain untouched.
13. The versioned candidate manifest validates.
14. Both repositories are returned unmerged for owner and ChatGPT review.
15. Publication status remains `not-published`.

## 20. Post-Phase 4 sequence

After Phase 4 approval, the owner may authorize a separate controlled launch operation covering production signing, public listing, price, distribution, support readiness, and promotion from candidate to published/current.

Only after Aurelius has a deliberate release decision should the next product phase begin. WARBIRD is the recommended next distinct watchface product because it already has a recognizable identity and preserved historical context, but it is outside this phase.