# ADR-009 — Visual/resource lineage and reviewed visual deltas

**Status:** Accepted  
**Date:** 2026-07-25  
**Scope:** `xsywatch` Phase 3 and every later engine-managed or commercial face

## Context

Phase 2 proved that structural correctness is not product correctness.

The Aurelius WFF XML, deterministic generator, parity tests, Gradle build, WFF
validator, memory evaluator, and CI all passed while 46 of 53 runtime PNGs in
the imported source tree belonged to the unreleased WARBIRD design. The first
physical Galaxy Watch7 candidate therefore rendered the wrong product with the
right mechanics. The device matrix caught the regression, the immutable
release APK supplied the authoritative Field Tourbillon resource bytes, and the
corrected candidate then passed.

The incident establishes a durable architectural fact:

> XML, package metadata, and valid resource names cannot prove that the intended
> pixels are shipping.

Phase 3 introduces intentional visual change, real Blender/studio exports, and
a cross-repository handoff. Without an enforceable visual and resource-lineage
system, those changes could repeat the same class of failure at greater scale.

## Decision

### 1. Visual correctness is a first-class release invariant

Every engine-managed face must have machine-readable evidence identifying:

- the exact runtime resources included in the candidate;
- where each new studio-derived resource came from;
- which normal and AOD renders are the approved references;
- whether a visual difference is accidental or intentionally approved;
- what physical-device evidence supports the candidate.

A successful Gradle/WFF build is necessary but never sufficient for visual
approval.

### 2. Every engine-managed face receives a visual contract

The repository will maintain a face-local visual contract under a structure
similar to:

```text
watchfaces/<slug>/visual/
  states.toml
  masks/
  goldens/
    <approved-visual-version>/
      normal.png
      aod.png
  candidates/
  inventories/
  approvals/
```

The exact structure may be refined by implementation, but it must separate:

- approved references;
- unapproved candidates;
- dynamic-region masks;
- resource inventories;
- intentional-change approvals.

### 3. Resource inventories are deterministic and checksum-bound

A repository-native tool must inventory the resources used by an
engine-managed face and record at least:

- repository-relative path;
- resource identifier;
- media type;
- dimensions and alpha mode where applicable;
- file size;
- SHA-256;
- source classification: legacy, face-owned, studio-handoff, generated, or
  third-party;
- handoff asset identifier when applicable;
- consuming engine component(s).

The inventory must fail on missing, unexpected, duplicate, or checksum-drifted
runtime resources. A deliberate WARBIRD-style substitution fixture must prove
that same-name/wrong-bytes changes are detected.

### 4. Deterministic reference renders and visual comparison are required

The build toolchain must produce deterministic normal and AOD reference renders
from fixed test state values. The canonical state must pin time, date, battery,
heart rate, accelerometer/parallax, and motion phase so repeated runs are
comparable.

Visual comparison must support:

- exact pixel comparison where deterministic;
- documented perceptual thresholds where renderer differences require them;
- masks for legitimate dynamic or non-capturable regions;
- useful diff images and metrics;
- nonzero exit on unapproved drift.

The reference renderer is a development/validation tool only. It is not runtime
code and does not change the WFF execution model established by ADR-008.

### 5. Intentional redesign uses reviewed-delta approval, not silent golden replacement

Approved visual references may change only through a machine-readable visual
change record that includes:

- change identifier and face/version;
- previous and proposed golden hashes;
- candidate resource-inventory hash;
- affected assets/components/regions;
- rationale;
- linked cross-repository source commits and handoff entries;
- diff metrics and preview paths;
- owner approval status and date;
- architecture-review status;
- physical-device evidence path when required.

Candidate images may be committed before approval, but they must remain under a
candidate lifecycle. Replacing approved goldens without a matching approved
change record is a validation failure.

### 6. New studio exports require real cross-repository handoff entries

Every new asset imported from `xsytrance/AGENOR-Horology` must have a real,
non-example handoff entry containing the exact source commit, source paths,
regeneration command, imported destination, lifecycle, and byte checksum.

The synthetic Phase 2 handoff entry is not production evidence. Phase 3 must
exercise the contract with real exports before approving the premium Aurelius
candidate.

### 6a. Device comparison is a quantitative gate only when state is controllable

*Added 2026-07-25 after the Phase-3 r1 review, on measured evidence.*

Deterministic **reference-to-committed-reference** comparison remains
exact and mandatory for every engine-managed face: a re-render must match
the committed reference byte-for-byte.

A **device screenshot** comparison is a different thing, and it is a
quantitative hard gate **only when every material motion phase and sensor
input can be controlled or safely masked** — "safely" meaning without
breaching the mask-coverage policy, i.e. without hiding most of the face.

Aurelius cannot satisfy that, and the r1 device evidence measured why:

- `z10_gl` and `z11_gr` rotate at 40°/s and 24°/s and the seconds cage at
  6°/s, so the capture instant cannot be pinned to any render state — a
  one-second error rotates a gear by 40°;
- `z40_sheen` is a full-screen layer parallaxed by up to ±40 px in X and
  ±14 px in Y from `[ACCELEROMETER_ANGLE_*]`, which cannot be held at zero
  on a worn or docked watch.

Rendering a reference at the device's *observed* time/battery/date still
left the **static** outer bezel annulus at mean channel delta 23.8
(`docs/reports/evidence/phase-3/aurelius/r1/DEVICE_TEST_RESULTS.md`).
Masking both dynamic sources would fall below `min_disc_coverage`.

Each face therefore declares a machine-readable device-validation mode in
its visual contract:

```toml
[device_validation]
mode = "qualitative-behavioral-lineage"   # or "threshold"
reason = "..."
required_evidence = [...]
```

- `threshold` — the generic profile in `[compare.device_profile]` applies
  and `compare_visuals.py --mode device` returns a pass/fail verdict.
  Retained for static or fully controllable faces.
- `qualitative-behavioral-lineage` — the device gate is **human visual
  inspection + behavioural validation + exact byte lineage** (studio
  export → handoff manifest sha → imported resource → inventory →
  packaged APK) + documented normal/AOD evidence with explicit
  qualifications. `compare_visuals.py --mode device` reports metrics and
  refuses to emit a verdict, so static-face thresholds can never appear to
  be gating a face they cannot gate.

This narrows a claim; it does not weaken the gate. The pixel-level
guarantee still comes from deterministic reference comparison and from
byte lineage into the packaged APK, both of which remain mandatory.

### 6b. Live-presentation containment must be proven, not eyeballed

*Added 2026-07-25 after the Phase-3 r1 review.*

Where plate artwork frames live runtime content — a date window, a gauge
scale, any aperture — the art and the live presentation are authored in
different repositories and can drift apart silently. Revision r1 shipped a
date opening 14.5 px tall for a 24 px text presentation, so the digits
overhung the frame; every static gate passed because nothing compared the
two.

Such a face must therefore declare the aperture geometry in its visual
contract and prove containment over the **full value domain**, not a
sample: `tools/date_aperture_proof.py` measures rendered glyph alpha
bounds for every valid day 1..31 in normal and ambient, a committed proof
sheet shows the contract days, and `tests/visual/test_date_aperture.py`
fails if any value comes within the mandated clear margin of the frame.

### 7. Physical-device evidence remains mandatory

The first candidate for each major visual generation must be tested on the
physical Galaxy Watch7. At minimum, evidence must cover normal rendering, AOD
behavior, transitions, clipping, legibility, motion, data indicators,
stability, and a baseline/candidate comparison.

For intentional redesigns, exact visual equality to the previous release is not
the goal. The goal is that the observed difference matches the approved visual
change and contains no accidental substitutions or regressions.

### 8. Historical releases remain immutable

The current Phase 1 Aurelius release APK remains checksum-pinned and unchanged.
Phase 3 may build candidates but must not replace or package a new `current`
release until the phase is approved and a separate release decision is made.

## Consequences

### Positive

- Same-name/wrong-pixel substitutions become detectable before merge.
- Studio exports remain traceable to reproducible source and reviewed bytes.
- Intentional art direction can evolve without weakening regression controls.
- Device evidence is connected to exact candidate artifacts and inventories.
- The Warbird incident becomes a permanent automated regression fixture rather
  than only a historical caution.

### Costs and risks

- Visual tooling introduces development dependencies such as Pillow and
  possibly a documented perceptual-metric library.
- Rendering and image comparison add CI time and require threshold calibration.
- Dynamic WFF behavior cannot be reduced to a single screenshot; masks, fixed
  states, and physical evidence remain necessary.
- Cross-repository changes cannot be atomic, so source commits and handoff
  checksums must be recorded carefully.
- Owner approval is intentionally required for major golden updates.

## Supersession rule

Any later decision to remove physical-device validation, permit unmanifested
studio imports, or replace reviewed visual deltas with unrestricted golden
updates requires a superseding ADR that explicitly addresses the WARBIRD
failure mode.
