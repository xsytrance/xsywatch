# Phase 2 — Aurelius Reference Engine Slice

**Repository:** `xsytrance/xsywatch`  
**Approved baseline:** `main` at `84145b20d537a9a77ae9d06b580ac81e13d7ecf4`  
**Implementation branch:** `phase-2/aurelius-reference-engine`  
**Reference face:** `watchfaces/aurelius`  
**Architecture decision:** `docs/decisions/ADR-008-build-time-wff-engine-and-aurelius-reference.md`  
**Status:** Approved for Claude Code implementation

---

## 1. Phase mission

Build the first real, reusable slice of the AGENOR Horology Engine by
extracting proven WFF behavior from Aurelius into a deterministic build-time
engine while preserving Aurelius's current appearance, package identity,
behavior, and released artifact.

This phase is successful only if the repository ends with:

1. evidence showing which patterns are genuinely shared across the ten faces;
2. a working engine implementation containing real reusable code rather than
   empty scaffolding;
3. Aurelius generated from that engine with no material visual or behavioral
   regression;
4. repeatable tests, validation, and physical Galaxy Watch7 evidence;
5. a clean contract for future assets exported from `AGENOR-Horology`.

Phase 2 is an **engineering extraction phase**, not the premium visual redesign
of Aurelius. The expensive photorealistic rebuild belongs to a later phase once
this foundation is proven.

---

## 2. Why Aurelius

Aurelius is compact enough to understand but rich enough to exercise the first
engine slice. Its current WFF v4 source contains:

- analog hour and minute hands;
- a seconds-driven tourbillon cage;
- two rotating mechanical gear layers with different direction/speed;
- a heart-rate-driven balance-wheel oscillator with a fallback value and clamp;
- a battery power-reserve needle;
- a date aperture;
- accelerometer-driven background and sheen parallax;
- normal/AOD background swapping and per-layer ambient reductions;
- bitmap-font definitions;
- staged ambient transitions.

These behaviors overlap meaningfully with patterns already visible in Bushido
and other imported faces, especially ambient visibility, data-bound indicators,
parallax, timing expressions, and layered animation.

---

## 3. Architectural constraint

WFF packages are declarative, resource-only applications. The engine therefore
must operate at **build time** by producing and validating XML/resources. It is
not a runtime Android code library.

Required properties:

- deterministic generation;
- readable committed output;
- no hidden service or network dependency;
- a `--check` mode that fails on drift;
- minimal dependencies, preferably Python standard library only;
- compatibility with the existing Linux workflow;
- no requirement for Samsung Watch Face Studio.

WFF v4 remains the target. Do not upgrade Aurelius to WFF v5 during this phase.
Evaluate WFF v4 `Reference`, `Group`, `Gyro`, and shared transform patterns, but
do not force their use when they make the generated XML harder to understand.

---

## 4. Required workstreams

### 4.1 Establish the Phase 2 baseline

Before modifying Aurelius:

1. Pull current `main` and verify the head is at or descended from `84145b2`.
2. Run and record:
   - `python3 tools/validate.py`;
   - `tools/build_all.sh`;
   - `git diff --check`;
   - the current CI status.
3. Record the SHA-256 of:
   - `releases/aurelius/current/aurelius.apk`;
   - current Aurelius `watchface.xml`;
   - every runtime resource referenced by Aurelius.
4. Capture current physical-device evidence before refactoring:
   - normal-mode screenshot;
   - AOD screenshot;
   - short screen recording showing wrist wake/AOD transition and motion;
   - current date, battery percentage, and heart-rate value visible in the
     evidence or recorded in an accompanying note.
5. Store baseline evidence under:

```text
 docs/reports/evidence/phase-2/aurelius/baseline/
```

Do not overwrite the released APK. It is the immutable Phase 1 reference.

### 4.2 Audit common WFF patterns across all ten faces

Create a repository-native analyzer, preferably:

```text
 tools/analyze_wff_patterns.py
```

It must parse all committed `watchface.xml` files and produce deterministic
machine-readable and human-readable reports, for example:

```text
 docs/reports/PHASE_2_COMPONENT_AUDIT.json
 docs/reports/PHASE_2_COMPONENT_AUDIT.md
```

At minimum, audit:

- WFF version;
- clock type;
- element/tag counts;
- normal/AOD `Variant` patterns;
- `Group` usage;
- `Reference` usage;
- data sources such as battery, heart rate, steps, weather, date, time, and
  accelerometer/gyro;
- repeated transform expressions after normalization;
- analog/digital hand or clock structures;
- rotating-image patterns;
- data-gauge patterns;
- bitmap-font declarations;
- resources referenced and resources unused;
- animation and transition parameters;
- repeated naming/z-order conventions.

The report must distinguish:

1. components suitable for immediate extraction;
2. patterns that look similar but should remain face-specific;
3. one-off patterns that are not worth abstracting;
4. unsafe or inconsistent patterns needing later cleanup.

Do not choose abstractions by intuition alone. Cite face paths and counts.

### 4.3 Implement the first build-time WFF engine

Create `engine/` only with real implementation and documentation. A reasonable
shape is:

```text
 engine/
   README.md
   wffgen/
     __init__.py
     model.py
     expressions.py
     components.py
     profiles.py
     render.py
     validation.py
 tests/
   engine/
     test_expressions.py
     test_components.py
     test_render.py
     fixtures/
 tools/
   generate_face.py
```

Adapt the exact structure if a better implementation emerges, but do not add
empty placeholder directories.

The engine must provide a stable initial API for the behaviors actually proven
by Aurelius and the audit. The first candidate set is:

1. **Time-expression helpers**
   - elapsed seconds with milliseconds;
   - analog hour angle;
   - analog minute angle;
   - seconds angle;
   - normalized/clamped ratios.
2. **Ambient profiles**
   - hide in AOD;
   - dim in AOD;
   - normal/AOD background crossfade;
   - transition timing configuration.
3. **Motion profiles**
   - rotating image with explicit direction and ratio;
   - mechanically coupled rotation metadata;
   - heart-rate oscillator with fallback, clamp, amplitude, and frequency;
   - parallax/gyro displacement;
   - subtle sheen/breathing behavior.
4. **Indicator components**
   - battery reserve needle;
   - date aperture text;
   - analog hand stack and hub;
   - seconds/tourbillon cage;
   - balance-wheel layer.
5. **Structural conventions**
   - deterministic element naming;
   - z-order/layer naming;
   - pivot and coordinate validation;
   - resource reference validation;
   - explicit component metadata describing motion class and AOD policy.

The engine must not own Aurelius art or branded layout. It owns behavior,
expressions, component structure, and validation.

### 4.4 Define the authoritative face specification

Create an authoritative Aurelius engine specification under the face, such as:

```text
 watchfaces/aurelius/engine/face.toml
```

or another clearly justified data-oriented form.

Prefer a data-driven specification using Python-standard-library-readable
formats such as TOML or JSON. A small face-local Python composition file is
acceptable only when a data file cannot express the required ordering or
structure cleanly; document that decision.

The specification must declare:

- face dimensions and WFF version;
- metadata;
- font/resource mappings;
- ordered component instances;
- coordinates, dimensions, pivots, and z-order;
- expression parameters;
- AOD policies;
- motion classes;
- component-specific documentation;
- expected package/version identity.

`tools/generate_face.py aurelius` must regenerate:

```text
 watchfaces/aurelius/app/src/main/res/raw/watchface.xml
```

The generated XML remains committed. The command:

```text
 python3 tools/generate_face.py aurelius --check
```

must exit nonzero when the committed XML differs from deterministic generated
output.

### 4.5 Migrate Aurelius without redesigning it

Reconstruct Aurelius using the engine/spec system while preserving current
product behavior.

Hard invariants:

- package remains `com.xsytrance.aurelius`;
- WFF remains v4;
- versionCode and versionName remain unchanged during this non-release phase;
- the existing current-release APK and its checksum remain unchanged;
- current runtime image/font resources remain available;
- time, date, battery, heart-rate, gears, cage, parallax, hands, AOD, and sheen
  remain functionally equivalent;
- no change is packaged into `releases/aurelius/current/`.

Allowed improvements:

- clearer grouping;
- validated pivots and bounds;
- deterministic names;
- WFF v4 `Reference` use where it materially reduces repeated transforms;
- documented mechanical ratios;
- removal of proven-unused runtime resources, but only with evidence and no
  loss of source assets;
- accessibility metadata or screen-reader descriptions if supported and
  demonstrably correct.

Forbidden in Phase 2:

- new visual theme;
- new premium art;
- package rename;
- WFF v5 migration;
- release version bump;
- store signing;
- replacing the current release APK;
- broad refactors of unrelated watchfaces.

### 4.6 Prove generality without migrating another product

Do not refactor a second production face in Phase 2. Instead, add engine test
fixtures that prove the extracted components are not hard-coded to Aurelius.

Required fixtures:

1. a minimal analog face using the hand stack, AOD profile, battery indicator,
   and rotating mechanical component;
2. a minimal digital/data face using AOD, battery, heart-rate, and parallax
   components without Aurelius resources or naming.

Both fixture XML outputs must be deterministic, parse correctly, pass the
available WFF validator for their declared version, and contain no proprietary
face art.

### 4.7 Establish the cross-repository asset handoff contract

Create:

```text
 docs/ASSET_HANDOFF_CONTRACT.md
```

The contract between `xsytrance/AGENOR-Horology` and `xsywatch` must define at
least:

- stable asset identifier;
- source repository and exact source commit;
- source `.blend` / Material Maker / vector path;
- source `SPEC.md` path;
- export type and destination;
- dimensions and color space;
- alpha/premultiplication rules;
- pivot/origin;
- frame count and timing for animation strips;
- loop semantics;
- AOD suitability;
- license/provenance record;
- SHA-256 of every imported export;
- lifecycle state: `experimental`, `candidate`, `approved`, `deprecated`;
- consuming face and engine component;
- regeneration command.

Add a schema or validator for the handoff manifest, plus at least one synthetic
or legacy example clearly labeled as non-approved. Do not change the sibling
repository in this phase unless required to verify a real field; do not add a
submodule or subtree.

### 4.8 Add engine and generated-source validation

Extend repository validation so it detects:

- missing engine/spec files for engine-managed faces;
- generated XML drift;
- nondeterministic generation;
- missing referenced resources;
- duplicate generated element names;
- invalid pivots or coordinates outside documented policy;
- undeclared motion classes;
- engine component/version mismatch;
- asset-handoff checksum mismatch;
- engine fixtures that no longer validate;
- accidental changes to the immutable current Aurelius release.

Add standard-library unit tests. External test frameworks may be introduced only
when justified and documented.

CI must run at minimum:

- Python compilation;
- engine unit tests;
- generation `--check`;
- fixture generation/validation;
- repository validation;
- whitespace/conflict-marker checks.

Upgrade `actions/checkout` from v4 to v5 during this phase unless a verified
compatibility problem prevents it.

### 4.9 Physical Galaxy Watch7 validation

After migration, build and install the Aurelius candidate on the physical
Galaxy Watch7 44 mm.

Record evidence under:

```text
 docs/reports/evidence/phase-2/aurelius/candidate/
```

Minimum test matrix:

- install/upgrade succeeds;
- face appears in picker and activates;
- analog time is correct;
- date is correct;
- battery needle corresponds plausibly to the device percentage;
- heart-rate oscillator responds to a real reading and behaves safely before a
  valid reading exists;
- tourbillon cage completes one rotation per minute;
- gear directions/speeds match their documented ratios;
- parallax behaves without clipping;
- normal→AOD and AOD→normal transitions work for at least ten cycles;
- AOD is readable and visually restrained;
- no obvious stutter during a ten-minute observation;
- no unexpected disappearance, resource failure, or crash;
- touch/launch behavior is checked if any is present.

Capture:

- normal screenshot;
- AOD screenshot;
- short transition/motion recording;
- device software/API/WFF context;
- test date/time;
- observed battery and heart-rate values;
- pass/fail notes per item.

Run the official WFF validator and memory-footprint evaluator where available.
Record exact commands and outputs. If a tool cannot run, disclose the blocker;
do not substitute Gradle success for memory/device evidence.

Establish a repeatable battery-observation protocol, but a definitive battery
benchmark is not required in Phase 2.

---

## 5. Deliverables

Required files include, at minimum:

```text
 docs/decisions/ADR-008-build-time-wff-engine-and-aurelius-reference.md
 docs/phases/PHASE_2_AURELIUS_REFERENCE_ENGINE.md
 docs/reports/PHASE_2_COMPONENT_AUDIT.md
 docs/reports/PHASE_2_COMPONENT_AUDIT.json
 docs/reports/PHASE_2_AURELIUS_REFERENCE_ENGINE.md
 docs/ASSET_HANDOFF_CONTRACT.md
 docs/DEVICE_TEST_MATRIX.md
 docs/reports/evidence/phase-2/aurelius/baseline/*
 docs/reports/evidence/phase-2/aurelius/candidate/*
 engine/README.md
 engine/<real implementation>
 tests/engine/<real tests and fixtures>
 tools/analyze_wff_patterns.py
 tools/generate_face.py
 watchfaces/aurelius/engine/<authoritative face specification>
```

Also update:

- `README.md`;
- `docs/CHATGPT_ARCHITECT.md`;
- `docs/KNOWN_LIMITATIONS.md`;
- `docs/WATCHFACE_INVENTORY.md`;
- `.github/workflows/validate.yml`;
- any affected Aurelius documentation.

---

## 6. Acceptance criteria

Phase 2 is ready for architecture review only when all of the following are
true:

### Repository and audit

- [ ] Branch starts from updated `main`; no unrelated work is included.
- [ ] Component audit covers all ten source faces and is reproducible.
- [ ] Extraction decisions cite concrete face/path evidence.
- [ ] No empty engine scaffolding exists.

### Engine

- [ ] A deterministic build-time engine is committed under `engine/`.
- [ ] Engine APIs are documented and versioned at an initial experimental
      version.
- [ ] Aurelius is generated through the engine/spec path.
- [ ] `generate_face.py aurelius --check` passes.
- [ ] Repeated generation produces byte-identical XML.
- [ ] Analog and digital non-proprietary fixtures validate.
- [ ] Engine unit tests pass.

### Aurelius parity

- [ ] Package, WFF version, versionCode, and versionName are unchanged.
- [ ] Current released APK bytes/checksum are unchanged.
- [ ] Gradle build succeeds from clean source.
- [ ] Official WFF validation passes.
- [ ] Memory-footprint result is recorded or an exact blocker is disclosed.
- [ ] Baseline and candidate evidence are present.
- [ ] Physical-device matrix passes or every failure is disclosed.
- [ ] No material visual or behavioral regression is identified.

### Repository-wide safety

- [ ] All ten face projects still build.
- [ ] `tools/validate.py` reports zero errors.
- [ ] License/provenance validation remains clean.
- [ ] Release workflow fixtures still pass.
- [ ] CI is green on the Phase 2 branch.
- [ ] Working tree is clean.

### Documentation

- [ ] Asset handoff contract and schema/validation exist.
- [ ] Phase report includes commands, results, evidence, risks, and commits.
- [ ] Architecture ledger is updated without deleting historical decisions.
- [ ] Remaining limitations and recommended Phase 3 are explicit.

---

## 7. Non-goals

Phase 2 must not:

- visually redesign Aurelius;
- build the full Blender/material/Geometry Nodes library;
- produce the final AlienMilitary watchface;
- migrate every existing face to the engine;
- upgrade the project baseline to WFF v5;
- create production signing keys;
- publish to Google Play;
- package a new Aurelius release;
- solve definitive battery benchmarking;
- merge `AGENOR-Horology` into this repository;
- delete archived Bone Watch or revive frozen TripFace.

---

## 8. Git workflow

1. Pull current `main`.
2. Create:

```text
 phase-2/aurelius-reference-engine
```

3. Use logical commits. Recommended sequence:

   1. `phase-2: capture baseline and audit WFF patterns`
   2. `phase-2: add deterministic WFF engine foundation`
   3. `phase-2: migrate Aurelius to engine-generated XML`
   4. `phase-2: add fixtures validation and asset handoff contract`
   5. `phase-2: add device evidence CI and phase report`

4. Do not squash or rewrite after review begins.
5. Push the branch but do not merge it.
6. Return it to ChatGPT for architecture review.

---

## 9. Required end-of-phase report

Create:

```text
 docs/reports/PHASE_2_AURELIUS_REFERENCE_ENGINE.md
```

It must include:

1. executive summary;
2. baseline commit and evidence;
3. ten-face component-audit findings;
4. extraction decisions and rejected abstractions;
5. final engine architecture;
6. engine API/component inventory;
7. authoritative Aurelius spec format;
8. generated-source workflow;
9. XML parity and deterministic-generation evidence;
10. test inventory and results;
11. fixture results;
12. all-ten build results;
13. repository validation and release-fixture results;
14. WFF validator and memory-evaluator results;
15. physical Watch7 test matrix and evidence paths;
16. current-release checksum preservation;
17. licensing/provenance impact;
18. asset-handoff contract implementation;
19. deviations from this brief;
20. technical debt and risks;
21. recommended Phase 3;
22. branch and commit hashes.

Claude's completion message must report:

- branch and head SHA;
- commit list;
- engine modules/components added;
- number of faces audited;
- Aurelius generation/check result;
- unit/fixture test counts;
- all-ten build result;
- validator result;
- WFF/memory-tool result;
- physical-device result;
- release checksum comparison;
- CI result;
- exact files ChatGPT should review;
- unresolved decisions requiring AGENOR approval.

---

## 10. Architect's expected Phase 3 boundary

Phase 3 should begin only after the build-time engine and Aurelius parity are
approved. The likely next phase is a **premium Aurelius rebuild plus first real
asset-studio integration**, coordinating:

- studio template, camera, and lighting infrastructure in `AGENOR-Horology`;
- first approved material families;
- first parametric gear/mechanical assets;
- versioned asset handoff into `xsywatch`;
- a visually upgraded Aurelius candidate built mostly from reusable assets.

That visual work is deliberately excluded from Phase 2 so the engine contract
is proven before expensive art production begins.
