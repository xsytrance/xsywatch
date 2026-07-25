# Phase 3 — Premium Aurelius Mk II and Visual/Resource-Lineage Gate

**Status:** Approved architecture scope; implementation not started  
**Date:** 2026-07-25  
**Canonical repository:** `xsytrance/xsywatch`  
**Studio repository:** `xsytrance/AGENOR-Horology`  
**Decision:** `docs/decisions/ADR-009-visual-resource-lineage-and-reviewed-deltas.md`

## 1. Mission

Build the first genuinely premium, commercially credible AGENOR watchface
candidate while making the WARBIRD class of failure mechanically difficult to
repeat.

Phase 3 has two inseparable outcomes:

1. **Aurelius “Field Tourbillon Mk II”** — a photoreal military-haute-horlogerie
   evolution of the existing Aurelius product, built from the first real
   reusable studio assets produced in `AGENOR-Horology`.
2. **A visual/resource-lineage gate** — deterministic inventories, golden
   normal/AOD references, visual-diff tooling, reviewed intentional-change
   records, and physical-device evidence that prove the intended pixels are in
   the candidate.

The visual gate must exist and deliberately catch a same-name/wrong-art fixture
**before** any new studio asset is allowed to replace an Aurelius runtime
resource.

## 2. Why this phase exists

Phase 2 produced a deterministic WFF engine and passed every structural gate,
but the first physical candidate rendered WARBIRD because most Aurelius PNGs
contained the wrong artwork under valid Field Tourbillon filenames. The device
matrix exposed what XML parity, resource-name checks, WFF validation, memory
validation, Gradle, and CI could not.

Phase 3 therefore does not treat visual QA as the last manual glance. Visual
identity, resource provenance, and intentional visual deltas become explicit,
tested engineering contracts.

## 3. Product direction — AURELIUS “Field Tourbillon Mk II”

### 3.1 Emotional target

A hand-finished military instrument elevated into expensive independent
horology: rugged, disciplined, mechanical, and believable, but unmistakably
luxurious when viewed closely.

The face should feel like a limited-production field tourbillon commissioned
for an elite aviation or reconnaissance unit—not a toy tactical skin and not a
fantasy dashboard.

### 3.2 Visual language

Use the existing Aurelius mechanical layout as the behavioral foundation:

- analog hour and minute hands;
- tourbillon/seconds cage near 6 o’clock;
- live-HR balance-wheel motion;
- left/right mechanically coupled gear train;
- date aperture;
- battery power-reserve needle;
- sapphire/crystal sheen and restrained parallax;
- reduced, readable AOD presentation.

Premium art direction:

- blackened or DLC-like titanium;
- bead-blasted olive or charcoal field-instrument surfaces;
- brushed and polished steel edge contrast;
- restrained aged brass, warm gold, or bronze accents used only where they
  improve hierarchy;
- ruby jewel accents where mechanically plausible;
- sapphire crystal response and subtle depth;
- engraved markings, chamfers, countersinks, screws, and bridge finishing;
- visible but controlled wear, machining, and micro-surface variation;
- realistic shadows and occlusion that create depth without hiding time.

### 3.3 Explicit exclusions

Do not introduce:

- WARBIRD shark mouths, painted eyes, kill tallies, propeller/fuselage motifs,
  or aircraft nose art;
- AlienMilitary emissive circuitry or nonhuman technology in this product;
- generic camouflage overlays;
- random neon;
- novelty stencil fonts used only to signal “military”;
- giant AGENOR branding;
- gratuitous gold plating;
- decorative moving parts with no documented relationship;
- visual density that compromises the hands, date, or reserve gauge.

WARBIRD and AlienMilitary remain separate future product directions.

### 3.4 Owner concept checkpoint

Before production-quality asset replacement begins, create three clearly
separated concept directions using the same mechanical layout:

- **A — Black Titanium Command:** darkest, most restrained, highest-contrast
  finishing;
- **B — Olive Instrument:** bead-blasted olive/charcoal field-watch identity
  with warm metal accents;
- **C — Expedition Bronze:** aged bronze/brass hierarchy with blackened steel
  mechanics.

Each direction must include a normal-mode hero still, an AOD proposal, material
palette, and one-sentence rationale. AGENOR selects or combines a direction.
The selected direction and owner decision must be committed before final asset
production. Claude may build lightweight concept scenes and temporary renders,
but must not promote new assets to `approved` before this checkpoint.

## 4. Hard invariants

Throughout Phase 3:

- `releases/aurelius/current/aurelius.apk` remains byte-identical and pinned.
- Package remains `com.xsytrance.aurelius`.
- WFF remains v4 / API 36 unless a superseding ADR is approved.
- The current mechanical/data behavior remains available: time, date, battery,
  HR fallback/clamp, gear ratios, seconds cage, parallax, hands, AOD.
- The existing Phase 2 engine remains the WFF generation path.
- New art enters `xsywatch` only through real handoff-manifest entries.
- No production keystore is created or committed.
- No Google Play publication or release promotion occurs.
- Bone Watch remains archived and TripFace remains frozen.
- The failed WARBIRD candidate and Phase 2 evidence remain untouched.

## 5. Two-repository branch plan

Create dedicated branches from current `main` in both repositories:

```text
xsytrance/xsywatch
  phase-3/premium-aurelius-visual-lineage

xsytrance/AGENOR-Horology
  phase-3/aurelius-studio-slice
```

Do not merge either branch independently. The final reports must record the
exact paired heads and every handoff entry must point to the exact studio commit
that produced it.

## 6. Workstream A — Visual/resource-lineage gate in `xsywatch`

This workstream must be implemented and proven before Workstream C imports any
new production asset.

### 6.1 Face-local visual contract

Create a maintainable Aurelius structure, adapting names if implementation
evidence supports something better:

```text
watchfaces/aurelius/visual/
  states.toml
  masks/
  goldens/
    field-tourbillon-v1/
      normal.png
      aod.png
  candidates/
    field-tourbillon-mk2/
  inventories/
  approvals/
```

The Phase 2 corrected Field Tourbillon assets and evidence establish the legacy
reference generation. Goldens must be generated reproducibly rather than copied
without explanation.

### 6.2 Fixed visual states

Define deterministic states for at least:

- normal hero state;
- AOD state;
- low-battery state;
- high-battery state;
- valid-heart-rate state;
- HR-fallback state;
- parallax-neutral state.

The normal and AOD golden states must pin all dynamic inputs, including time,
date, battery, HR, accelerometer values, motion phase, and ambient mode.
Suggested canonical hero values may be refined, but once accepted they must be
machine-readable and stable.

### 6.3 Reference renderer

Add repository-native tooling such as:

```text
tools/render_reference.py
tools/compare_visuals.py
tools/inventory_resources.py
```

A better structure is acceptable if documented.

The reference renderer must:

- read the authoritative face spec and fixed state;
- compose the exact runtime resources in z-order;
- evaluate the Aurelius expression subset required for the pinned state;
- reproduce pivots, rotation, alpha, AOD variants, and parallax-neutral
  placement;
- produce deterministic PNG output;
- clearly disclose any WFF rendering behavior it cannot reproduce;
- remain development tooling, not APK runtime code.

Pillow may be introduced as a pinned development dependency. Additional image
or metric libraries require justification, version pinning, and license review.
Do not add a heavy framework when a small deterministic implementation suffices.

### 6.4 Resource inventory

Generate deterministic JSON and readable Markdown inventories for Aurelius.
Each used runtime asset must include:

- path and Android resource identifier;
- dimensions, color mode/alpha, size, and SHA-256;
- legacy/face-owned/studio/generated/third-party classification;
- handoff asset ID when applicable;
- consuming component(s);
- whether it appears in normal, AOD, or both;
- whether it is expected to differ from the prior approved visual version.

Also report:

- unused drawable resources;
- resources referenced but missing;
- same bytes under multiple names;
- unexpected new assets;
- assets that changed without a visual approval or handoff record.

### 6.5 Visual comparison

The comparison tool must emit:

- pass/fail exit status;
- changed-pixel count and percentage;
- maximum and mean channel delta;
- a diff/heat-map image;
- optional perceptual metric with documented interpretation;
- threshold and mask configuration used;
- paths and SHA-256 of compared images.

Exact comparison should be used for deterministic reference-render reruns.
Perceptual thresholds and masks may be used for device screenshots or known
renderer variation, but thresholds must be calibrated from evidence and cannot
be so broad that a WARBIRD-style substitution passes.

### 6.6 Mandatory deliberate-failure fixtures

At minimum, prove the gate detects:

1. a same-filename background substitution;
2. a same-filename hand substitution;
3. a same-filename font-glyph substitution;
4. an unexpected extra runtime drawable;
5. a missing handoff entry for a studio-classified asset;
6. a changed candidate/golden without an approval record;
7. a changed golden hash that does not match the approval record;
8. a mask or threshold so broad that the configured meaningful-region coverage
   falls below policy;
9. a path or checksum mismatch in the resource inventory.

One fixture must intentionally reproduce the Phase 2 failure class by replacing
Field Tourbillon art with a clearly different synthetic or preserved
WARBIRD-like test image under the same resource name. Do not use proprietary
WARBIRD art if a synthetic fixture proves the behavior cleanly.

### 6.7 Intentional visual-change approval

Define a machine-readable visual approval record and validator. It must bind:

- face and proposed visual version;
- previous approved visual version;
- previous and proposed normal/AOD golden hashes;
- candidate inventory hash;
- changed resources and handoff asset IDs;
- diff metrics and preview paths;
- rationale;
- owner status: `proposed`, `approved`, or `rejected`;
- owner approval date/identifier;
- architecture-review status;
- physical-device evidence path where required.

Validation must forbid approved-golden replacement without a matching approved
record. Candidate previews may exist in a `proposed` state without replacing
approved goldens.

## 7. Workstream B — First real studio slice in `AGENOR-Horology`

The companion studio repository must implement actual reusable source, not only
documentation or flattened renders.

### 7.1 Studio foundation

Create and document a repeatable watchface-rendering foundation:

- orthographic or otherwise calibrated 480×480 watchface camera rig;
- reusable normal and AOD lighting setups;
- color-management settings;
- transparent-film and alpha rules;
- render presets for preview, final static layer, and AOD;
- deterministic naming and output directories;
- a scene validation script or checklist;
- render metadata output recording Blender version, engine, samples, camera,
  color management, and source commit.

### 7.2 Initial reusable materials

Deliver production-quality first versions of at least:

- blackened/DLC titanium;
- bead-blasted olive or charcoal titanium;
- brushed steel;
- polished steel edge/chamfer treatment;
- restrained aged brass/bronze or warm-gold accent;
- ruby jewel;
- sapphire/crystal response.

Every material must have a stable ID, preview sphere/part render, source file,
parameters, license/provenance, and `SPEC.md` or equivalent documentation.

### 7.3 Initial mechanical assets

Produce reusable source for the minimum premium Aurelius slice:

- left and right gear-train assets with documented teeth/ratio/direction;
- tourbillon/seconds cage or cage assembly;
- balance wheel;
- hour hand, minute hand, reserve needle, and hub family;
- screws/jewel settings or bridge fasteners visible in the hero composition;
- dial/bridge/base assembly capable of producing normal and AOD plates.

Use meaningful pivots and scale. Gears should be parametric where practical,
with tooth count/module/thickness/bevel documented. Static exports may be used
for WFF rotation; Phase 3 does not require sprite animation when deterministic
WFF transforms are cheaper and sufficient.

### 7.4 Aurelius Mk II assembly and exports

The studio assembly must render a coordinated resource set using one camera and
lighting system. Expected imported layers include, at minimum:

- normal base plate/background;
- AOD base plate/background;
- left gear;
- right gear;
- balance wheel;
- tourbillon/seconds cage;
- reserve needle;
- hour hand;
- minute hand;
- hub;
- crystal/sheen layer where retained.

The exact split may change to improve quality or device performance, but the
handoff report must explain the layer strategy and runtime cost.

All exports must use stable names, correct alpha, documented pivots, dimensions,
and deterministic destinations. Render larger than device resolution and use a
reviewed downsample process.

### 7.5 Studio evidence

Create a Phase 3 studio report containing:

- source files and asset IDs;
- material IDs;
- camera/light/render configuration;
- concept checkpoint and owner-selected direction;
- render commands;
- output dimensions and checksums;
- performance-oriented layer decisions;
- known Blender/render nondeterminism;
- exact studio branch and commits consumed by `xsywatch`.

## 8. Workstream C — Real handoff and premium candidate integration

Only begin production import after Workstream A’s deliberate-failure fixtures
pass.

### 8.1 Real manifests

Replace or supplement the synthetic Phase 2 example with real non-example
entries for every imported studio export. Each entry must pass the existing
handoff schema and validation, including:

- exact `AGENOR-Horology` source commit;
- real source paths and specification path;
- real destination;
- dimensions, color space, alpha, pivot;
- frame/loop fields where applicable;
- lifecycle (`candidate` until approved);
- source and imported SHA-256;
- consuming component;
- regeneration command.

Do not use a single vague manifest entry for a multi-file export set unless the
contract is deliberately extended and tested to represent every file
unambiguously.

### 8.2 Candidate integration

Integrate the selected premium resources through the existing Aurelius engine
spec. Preserve mechanics and data behavior unless a visual requirement needs a
small layout/pivot change.

Any XML/spec behavior change must be:

- isolated from pure asset changes;
- documented with rationale;
- tested independently;
- reflected in the visual approval and device matrix;
- kept compatible with WFF v4.

The current release APK remains unchanged. The branch may produce a debug
candidate but must not update `releases/aurelius/current/`.

### 8.3 AOD discipline

The premium AOD must be designed rather than automatically darkened. It must:

- retain immediate time readability;
- remove or suppress crystal sheen and decorative highlights;
- minimize bright pixel coverage;
- preserve only meaningful mechanical silhouettes;
- avoid burn-in-prone large static bright areas;
- pass the official WFF and memory checks;
- receive owner visual approval and physical-device evidence.

## 9. Physical Galaxy Watch7 validation

Run the existing device matrix on the first integrated premium candidate and
add premium-specific checks:

- intended Mk II art appears—not legacy Field Tourbillon, WARBIRD, or mixed
  resources;
- normal-mode finishing and depth remain legible at actual watch scale;
- hands remain readable over the premium mechanism;
- date and reserve gauge feel physically integrated;
- gear/cage/balance pivots align with rendered arbors;
- no halo, matte fringe, clipped shadow, or alpha-premultiplication artifact;
- parallax/sheens do not expose layer edges;
- AOD is restrained and readable;
- no obvious stutter or resource disappearance;
- battery behavior receives at least a repeatable observation note.

Capture normal, AOD where capturable, transition, motion, parallax, and close-up
photos/screenshots. Record the exact candidate APK and visual inventory hashes.

## 10. CI and validation requirements

Phase 3 CI must run at minimum:

- existing Python/shell syntax checks;
- all engine tests;
- deterministic WFF generation check;
- existing repository and release validation;
- visual-contract/schema tests;
- resource-inventory generation/check;
- deterministic reference-render check;
- visual comparison against approved goldens;
- deliberate substitution/failure fixtures;
- handoff validation for all real imports;
- approved-golden/approval-record consistency checks.

Also evaluate bringing the official WFF validator into CI from a pinned upstream
revision. Do not commit an unlicensed third-party binary. If full CI integration
is impractical, document the exact blocker and retain reproducible local
commands/evidence.

The merge-commit whitespace issue seen after Phases 1 and 2 must be addressed:
CI should compare changed files appropriately on merge commits rather than
assuming `HEAD~1..HEAD` is always the intended range. Add a test or documented
strategy for merge-parent diffs and EOF whitespace.

## 11. Required deliverables

### In `xsywatch`

At minimum:

```text
docs/decisions/ADR-009-visual-resource-lineage-and-reviewed-deltas.md
docs/phases/PHASE_3_PREMIUM_AURELIUS_VISUAL_LINEAGE.md
docs/reports/PHASE_3_PREMIUM_AURELIUS_VISUAL_LINEAGE.md
watchfaces/aurelius/visual/<real contract, states, goldens, candidates, inventories, approvals>
tools/<visual renderer, inventory, comparison, validation commands>
tests/<visual and lineage tests, including deliberate substitution>
watchfaces/aurelius/engine/handoff.json  # real entries
updated Aurelius runtime resources and documentation
physical-device evidence under docs/reports/evidence/phase-3/aurelius/
```

### In `AGENOR-Horology`

At minimum:

```text
docs/phases/PHASE_3_AURELIUS_STUDIO_SLICE.md
docs/reports/PHASE_3_AURELIUS_STUDIO_SLICE.md
reusable camera/lighting/material source
reusable mechanical-part source and SPEC files
Aurelius Mk II studio assembly
normal/AOD and moving-layer exports
render metadata/checksum inventory
concept alternatives and owner-selection record
```

Adapt paths to verified repository conventions; do not create empty scaffolding.

## 12. Acceptance criteria

Phase 3 is ready for architecture review only when all are true.

### Visual-lineage gate

- [ ] Gate implementation precedes production asset replacement in history.
- [ ] Legacy Aurelius resource inventory is committed and deterministic.
- [ ] Legacy normal/AOD goldens and fixed states are committed.
- [ ] Repeated reference rendering is byte-identical.
- [ ] Visual comparison produces metrics and diff images.
- [ ] Same-name wrong-background, hand, and glyph substitutions fail.
- [ ] Unexpected/missing resources fail.
- [ ] Unapproved golden changes fail.
- [ ] Approved intentional visual changes pass only with exact bound records.
- [ ] Masks/thresholds are documented and cannot hide most of the face.

### Studio source and handoff

- [ ] Owner-selected Mk II concept is committed.
- [ ] Real Blender/material/camera/lighting source exists.
- [ ] Initial reusable material and mechanical assets have stable IDs/specs.
- [ ] Every imported export has a real non-example handoff entry.
- [ ] Imported bytes match handoff checksums.
- [ ] Studio commit/source paths/regeneration commands are valid and recorded.
- [ ] No unmanifested studio-classified runtime resource exists.

### Premium candidate

- [ ] Candidate visibly matches the owner-selected concept.
- [ ] Package and WFF baseline remain unchanged.
- [ ] Existing mechanics/data behaviors remain correct or approved deltas are
      documented.
- [ ] Normal and AOD candidate renders are committed.
- [ ] Visual change record is owner-approved before approved goldens move.
- [ ] Official WFF validation passes.
- [ ] Memory-footprint evaluation passes.
- [ ] All ten watchface projects still build.
- [ ] Existing 68+ engine tests and Phase 1 release fixtures remain green.
- [ ] Repository validation reports zero errors.
- [ ] CI is green on both relevant branches where CI exists.
- [ ] Immutable Phase 1 Aurelius release checksum remains unchanged.

### Physical device

- [ ] Premium candidate installs on the Galaxy Watch7.
- [ ] Device evidence binds to exact APK and resource-inventory hashes.
- [ ] Intended Mk II pixels are confirmed on-device.
- [ ] Time/date/reserve/HR/gear/cage behavior passes.
- [ ] AOD, transitions, parallax, clipping, alpha, stability, and smoothness are
      tested and documented.
- [ ] Owner gives an explicit visual acceptance or rejection.

### Documentation and history

- [ ] Both repository reports include exact branches and commits.
- [ ] Architecture ledger, known limitations, Aurelius README, and handoff docs
      are updated accurately.
- [ ] Failed concepts and failed candidates remain documented rather than erased.
- [ ] Branches are pushed but not merged before ChatGPT architecture review.

## 13. Non-goals

Phase 3 must not:

- release or sell the new face;
- create or commit a production keystore;
- publish to Google Play;
- migrate every face to the engine;
- redesign WARBIRD or AlienMilitary;
- upgrade to WFF v5;
- build the entire future horology asset library;
- add user customization merely for scope inflation;
- erase the legacy Field Tourbillon or WARBIRD evidence;
- use unrestricted AI-generated donor assets without recorded provenance and
  commercial-use review.

## 14. Recommended commit sequence

### `xsywatch`

1. `phase-3: establish legacy visual contract and inventories`
2. `phase-3: add deterministic renderer comparison and regression fixtures`
3. `phase-3: add intentional visual approval workflow`
4. `phase-3: import real Aurelius studio assets through handoff`
5. `phase-3: integrate premium Aurelius candidate`
6. `phase-3: add device evidence CI and final report`

### `AGENOR-Horology`

1. `phase-3: audit studio baseline and record concept directions`
2. `phase-3: add calibrated camera lighting and material foundation`
3. `phase-3: add Aurelius mechanical asset slice`
4. `phase-3: render approved Mk II layer set and handoff metadata`
5. `phase-3: add studio validation and phase report`

Use focused commits. Do not squash, rebase, or rewrite after review begins.

## 15. Required end-of-phase reports

Create:

```text
xsywatch/docs/reports/PHASE_3_PREMIUM_AURELIUS_VISUAL_LINEAGE.md
AGENOR-Horology/docs/reports/PHASE_3_AURELIUS_STUDIO_SLICE.md
```

The `xsywatch` report must include:

1. executive summary;
2. branch bases and commit lists for both repositories;
3. Warbird-derived risk model;
4. visual contract and state format;
5. reference renderer architecture;
6. comparison metrics, masks, and thresholds;
7. deliberate-failure fixture results;
8. legacy resource inventory and golden hashes;
9. intentional visual approval workflow;
10. owner-selected concept direction;
11. studio assets and real handoff entries consumed;
12. premium candidate resource inventory;
13. WFF/spec changes, if any;
14. visual diff results and approval record;
15. all-ten build, engine-test, release-fixture, validator, WFF, and memory results;
16. physical Watch7 evidence and exact APK/inventory hashes;
17. normal/AOD/performance findings;
18. immutable release preservation;
19. licensing and AI-donor commercial-use findings;
20. deviations, risks, technical debt, and recommended next phase.

The studio report must include source assets, materials, camera/lighting,
concepts, owner selection, render commands, exports, checksums, regeneration,
known nondeterminism, and the exact commit handed to `xsywatch`.

## 16. Completion handoff

Claude’s completion message must report:

- both branches and heads;
- commit lists;
- owner-selected concept;
- visual tooling and test counts;
- deliberate Warbird-style failure result;
- legacy and candidate golden/inventory hashes;
- real handoff asset IDs and source commit;
- premium candidate APK checksum;
- all-ten build and validator results;
- WFF/memory results;
- physical-device result;
- CI result;
- immutable release checksum;
- exact files ChatGPT should review;
- any decisions still requiring AGENOR approval.

Do not merge either branch. Return both to ChatGPT for architecture and visual
lineage review.
