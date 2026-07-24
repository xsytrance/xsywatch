# AGENOR Horology Engine — Architecture Ledger

**Repository:** `xsytrance/xsywatch`  
**Primary device:** Samsung Galaxy Watch7 44 mm  
**Primary platform:** Wear OS / Watch Face Format (WFF)  
**Document owner:** ChatGPT, acting as architecture and design-review partner  
**Implementation partner:** Claude Code  
**Product owner / creative director:** AGENOR / xsytrance  
**Status:** Living document — update after every meaningful phase, architectural decision, or release

---

## 1. Purpose of this document

This file is the durable architectural memory for the AGENOR watch ecosystem. It exists so that design intent, technical constraints, quality standards, decisions, and follow-up work do not disappear between coding sessions.

Claude Code should read this document before starting a new phase. After implementation, the relevant status, decisions, risks, and evidence should be updated in the repository rather than preserved only in chat logs.

This is not a generic roadmap. It is the control document for building a reusable horology platform capable of producing premium mechanical, military, mythological, cybernetic, alien, and experimental watch faces without rebuilding the entire pipeline for every design.

---

## 2. Current repository reality

### Verified state on 2026-07-24

The repository currently contains release artifacts rather than the complete watch-engine source tree.

#### APK artifacts detected

- `ares-wargod.apk`
- `aurelius.apk`
- `bone-watch.apk`
- `hellforge.apk`
- `pinball.apk`
- `pulseface.apk`
- `xsywatch-bushido.apk`

#### Preview artifacts detected

- `aurelius-preview.png`
- `pulseface-preview.png`
- `xsywatch-bushido.jpg`

#### Latest verified commit

- Commit: `d8ed43bfefe2eaf947b3f3993bc8aa15ebe90534`
- Message: `Add watch face APK releases and previews`

### Immediate discrepancy

The commit description states that eight Galaxy Watch7 faces were added, but the committed file list contains seven APKs. This must be reconciled by identifying the missing eighth watch face or correcting the release description.

### Architectural implication

This repository is currently suitable as a distribution shelf, but it is not yet sufficient for reproducible engineering, review, automated validation, or collaborative source development. The source project, build scripts, WFF/XML definitions, reusable assets, and documentation must also be pushed.

---

## 3. North-star product vision

Build an **AGENOR Horology Engine**, not merely a folder of unrelated watch faces.

The engine should let the team combine reusable components and art-direction systems to create distinct products quickly while preserving premium craftsmanship, device compatibility, performance discipline, and visual identity.

A mature workflow should support:

1. Parametric mechanical components such as gears, screws, bridges, bezels, hands, jewels, tourbillon assemblies, apertures, and decorative plates.
2. Reusable material systems including polished steel, brushed titanium, blackened metal, ceramic, enamel, marble, bone, glass, luminous compounds, alien alloys, and emissive circuitry.
3. Multiple design languages built on the same technical foundation.
4. Controlled animation with deterministic timing, believable mechanical relationships, and battery-aware fallbacks.
5. Automated export and validation for Samsung Galaxy Watch7 and future Wear OS devices.
6. A clean separation between source assets, generated artifacts, previews, signed releases, and experimental work.
7. A commercial-quality release pipeline suitable for products that can eventually be sold.

---

## 4. Core architectural principles

### 4.1 Reproducibility over one-off success

A face is not considered complete merely because an APK exists. The repository must contain enough source, configuration, and documentation to rebuild it from a clean environment.

### 4.2 Parametric assets over destructive copies

Whenever practical, components should expose dimensions, tooth count, thickness, bevel, material, emission, speed, and placement as parameters. Avoid duplicating nearly identical assets without a documented reason.

### 4.3 Visual ambition with hardware restraint

The watch should look complex, expensive, and alive without wasting battery or exceeding device limits. Visual richness should come from hierarchy, material response, layered motion, and intentional composition—not from uncontrolled element count.

### 4.4 One source of truth

Source files and generator definitions are authoritative. APKs, renders, thumbnails, and exported bundles are derived artifacts.

### 4.5 Design systems, not themes pasted on top

Military, alien, mythological, marble, cybernetic, and traditional horology faces should each have coherent geometry, typography, materials, motion grammar, complication styling, and color behavior.

### 4.6 Evidence-backed completion

Every phase should include build output, validation results, preview evidence, device-test notes, known limitations, and a commit reference.

---

## 5. Recommended repository structure

The target structure below should be adapted to the actual local project rather than copied blindly. Existing working paths should be migrated carefully, with a documented map.

```text
xsywatch/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── docs/
│   ├── CHATGPT_ARCHITECT.md
│   ├── PRODUCT_VISION.md
│   ├── BUILD_AND_RELEASE.md
│   ├── DEVICE_TEST_MATRIX.md
│   ├── ASSET_STANDARDS.md
│   ├── MATERIAL_SYSTEM.md
│   ├── ANIMATION_SYSTEM.md
│   ├── MILITARY_STYLE_GUIDE.md
│   ├── ALIEN_STYLE_GUIDE.md
│   ├── MYTHOLOGICAL_STYLE_GUIDE.md
│   └── decisions/
├── watchfaces/
│   ├── ares-wargod/
│   ├── aurelius/
│   ├── bone-watch/
│   ├── hellforge/
│   ├── pinball/
│   ├── pulseface/
│   └── bushido/
├── engine/
│   ├── geometry/
│   ├── materials/
│   ├── animation/
│   ├── complications/
│   ├── typography/
│   ├── validation/
│   └── export/
├── assets/
│   ├── source/
│   ├── generated/
│   ├── shared/
│   └── fonts/
├── tools/
│   ├── build/
│   ├── render/
│   ├── validate/
│   └── release/
├── tests/
│   ├── structural/
│   ├── visual/
│   ├── performance/
│   └── device/
├── previews/
│   ├── approved/
│   └── candidates/
└── releases/
    └── manifests/
```

### Important release policy

Large APK binaries should normally be attached to versioned GitHub Releases rather than accumulated indefinitely in the repository root. Small manifests, checksums, screenshots, and release notes should remain in Git. If binaries remain tracked, Git LFS should be evaluated before history grows.

---

## 6. Asset-system standards

Every reusable asset should have:

- A stable identifier.
- A semantic name rather than a purely visual nickname.
- Defined scale and coordinate conventions.
- An origin and pivot appropriate for animation.
- A source format and export format.
- Material-slot conventions.
- Parameter documentation.
- Polygon or complexity budget where relevant.
- Preview render.
- Approval status.
- License or provenance information.

### Proposed lifecycle

`experimental → candidate → approved → deprecated`

Only approved assets should be used in commercial release builds unless a face-specific exception is documented.

### Mechanical asset families

Initial reusable families should include:

- Spur gears and ring gears.
- Pinions.
- Screws and jewel settings.
- Bridges and plates.
- Ratchets and winding components.
- Balance-wheel and escapement-inspired assemblies.
- Tourbillon-inspired cages.
- Hands and central pinions.
- Chapter rings and bezels.
- Windows for date, battery, steps, health, and other complications.

The visuals may be fantastical, but rotational relationships and pivots should remain internally believable unless deliberate surrealism is part of the design language.

---

## 7. Material-system standards

Materials should be reusable, parameterized, and grouped into coherent families.

### Baseline material families

- Polished steel.
- Brushed steel.
- Titanium.
- Gunmetal / blackened steel.
- Brass and aged brass.
- Rose gold and yellow gold.
- Ceramic.
- Sapphire or watch crystal.
- Marble and carved stone.
- Bone or ivory-like synthetic material.
- Enamel.
- Luminous paint.
- Smoked glass.
- Alien alloy.
- Emissive circuitry.
- Heat-stressed or scorched metal.

### Required controls

At minimum, expose useful controls for roughness, metallic response, anisotropy where supported, tint, wear, edge variation, patina, emission intensity, emission color, normal strength, and environment response.

Avoid baked-in lighting that prevents the same component from being reused across different faces.

---

## 8. Animation architecture

Animation must be centralized and declarative wherever possible.

### Motion classes

1. **Time-critical motion** — hour, minute, second, and complication indicators.
2. **Mechanically coupled motion** — gears, pinions, cages, and linked assemblies.
3. **Ambient motion** — pulses, breathing light, slow energy circulation, drifting smoke, subtle parallax.
4. **Event motion** — wake transitions, taps, state changes, low-battery warnings, goal completion.
5. **Always-on behavior** — heavily reduced or static presentation optimized for power use.

### Animation rules

- Do not assign arbitrary independent speeds to visibly meshed gears.
- Document direction, ratio, period, and power cost.
- Provide reduced-motion and battery-conscious behavior.
- Prevent motion from compromising time readability.
- Avoid visual loops whose reset is obvious.
- Prefer a small number of strong motions over many noisy motions.

---

## 9. Design-language framework

Each design language should define the following before implementation:

- Emotional target.
- Silhouette and composition.
- Material palette.
- Lighting behavior.
- Typography.
- Numeral system.
- Hands and indicators.
- Complication treatment.
- Motion grammar.
- Color limits.
- Always-on treatment.
- Forbidden clichés.

### 9.1 Traditional high horology

Precision, restraint, depth, exquisite finishing, layered bridges, believable mechanisms, and selective reveal. Expensive should come from finishing and composition, not gratuitous gold.

### 9.2 Military / tactical

Legibility, rugged geometry, functional hierarchy, instrument-panel logic, restrained color, durable finishes, and purposeful complications. Avoid generic camouflage overlays and novelty stencil typography unless the concept genuinely requires them.

### 9.3 Alien / cybernetic

Nonhuman engineering logic, unusual energy circulation, asymmetry with balance, deep layered mechanisms, controlled emissive systems, and motion that feels purposeful but difficult to fully understand. Avoid reducing the concept to random neon wires.

### 9.4 Mythological / sculptural

Monumental composition, carved material language, symbolic complications, disciplined ornamentation, and respectful integration of numerals and health data. The interface must feel sculpted into the artifact rather than pasted over artwork.

---

## 10. Watch-face product contract

Every releasable watch face should define:

- Product name and internal slug.
- Version.
- Target devices and WFF version.
- Design language.
- Time display method.
- Supported complications.
- User-customizable options.
- Animation classes used.
- Always-on mode.
- Battery strategy.
- Accessibility considerations.
- Preview set.
- Build command.
- APK or bundle checksum.
- Device-test result.
- Known limitations.

A face without this metadata is a prototype, not a formal release.

---

## 11. Quality gates

A release candidate must pass the following gates.

### Structural

- Source files exist in the repository.
- Build is reproducible from documented steps.
- No accidental secrets or signing material are committed.
- Naming and version metadata are consistent.
- Release manifest matches generated artifacts.

### Visual

- Time is readable at a glance.
- Numerals and indices are not cramped.
- Complications appear physically integrated.
- No clipping at the circular display boundary.
- Visual hierarchy survives reduced brightness.
- Preview image matches the release build.

### Device and performance

- Installs on the target Galaxy Watch7 configuration.
- Normal and always-on modes behave correctly.
- Complications update correctly.
- Touch targets work where applicable.
- Animation does not create obvious stutter.
- Battery impact is measured or at least documented through repeatable observation.

### Release

- Version is unique.
- Changelog entry exists.
- Checksums are recorded.
- Release notes identify device requirements and known issues.
- APK count and release description agree.

---

## 12. Collaboration protocol

### Product owner / creative director

- Defines the emotional target and commercial ambition.
- Approves final visual direction.
- Chooses which concepts advance to production.

### Claude Code

- Implements features and tooling.
- Preserves repository hygiene.
- Produces phase reports with commands, tests, evidence, and commit references.
- Updates source documentation when implementation changes behavior.

### ChatGPT architecture role

- Reviews repository state and commits.
- Maintains this architecture ledger.
- Identifies inconsistencies, technical debt, and design-system opportunities.
- Converts broad creative goals into enforceable product and engineering constraints.
- Proposes phase boundaries and acceptance criteria.

### Required handoff format after each Claude phase

1. Summary of work completed.
2. Files added, modified, and removed.
3. Commands run.
4. Tests and validation results.
5. Generated artifacts and preview locations.
6. Known issues or deferred items.
7. Commit SHA and branch.
8. Recommended next phase.

---

## 13. Immediate prioritized backlog

### P0 — Repository integrity

- [ ] Push the complete source project and build tooling, not only APKs.
- [ ] Reconcile the stated eight-face release with the seven APK files currently present.
- [ ] Add a root `README.md` explaining the project, installation, and source/build status.
- [ ] Decide whether APKs belong in GitHub Releases, Git LFS, or the tracked repository.
- [ ] Add checksums and a release manifest for existing APKs.
- [ ] Confirm that signing keys and credentials are excluded.

### P1 — Reproducible build foundation

- [ ] Document exact Linux toolchain versions.
- [ ] Add one canonical build command per face.
- [ ] Add validation scripts for WFF/XML structure and package metadata.
- [ ] Add a device installation/test script or checklist.
- [ ] Establish naming and semantic-versioning rules.

### P2 — Engine extraction

- [ ] Identify common components across the existing faces.
- [ ] Extract shared complication, typography, color, and animation definitions.
- [ ] Establish the asset approval lifecycle.
- [ ] Build the first parametric mechanical-component library.
- [ ] Build the first reusable material library.

### P3 — Premium reference face

- [ ] Select one face as the engineering reference implementation.
- [ ] Rebuild it entirely from documented, reusable source.
- [ ] Demonstrate normal mode, always-on mode, complications, animation, and reproducible packaging.
- [ ] Use it as the template for future commercial faces.

---

## 14. Recommended next implementation phase

### Phase 1: Repository normalization and reproducible source import

**Goal:** Transform `xsywatch` from an artifact-only repository into a reproducible engineering repository without breaking the existing APK distribution.

#### Acceptance criteria

- All source required to rebuild at least one existing watch face is committed.
- Root README documents project status and install/build workflow.
- Existing APKs are inventoried in a machine-readable release manifest.
- The seven-versus-eight discrepancy is resolved.
- Signing secrets are verified absent.
- A clean checkout can execute validation and build steps using documented commands.
- Existing release artifacts remain available to the product owner.

#### Non-goals

- Do not redesign all existing faces during repository normalization.
- Do not prematurely build a massive generalized SDK before one reproducible reference face is proven.
- Do not destroy or rename release artifacts without preserving traceability.

---

## 15. Decision log

### ADR-001 — Build an engine, not isolated faces

**Status:** Accepted  
**Decision:** Shared geometry, materials, animation, complications, validation, and release tooling will be extracted into a reusable engine layer.  
**Reason:** The product vision includes many stylistically distinct premium faces; duplication would slow iteration and create inconsistent quality.

### ADR-002 — Source is authoritative; APKs are derived artifacts

**Status:** Accepted  
**Decision:** Reproducible source and configuration are the authoritative project state. APKs alone do not constitute a complete implementation.  
**Reason:** Review, maintenance, commercial release, and future device support require source traceability.

### ADR-003 — Prove one reference face before broad abstraction

**Status:** Accepted  
**Decision:** The shared engine should be extracted against one complete reference face before large-scale generalized framework development.  
**Reason:** This keeps abstractions grounded in real WFF and device constraints.

### ADR-004 — Linux-first open toolchain

**Status:** Accepted with platform caveat  
**Decision:** Prefer Blender, GIMP, Inkscape, Krita, Material Maker, Android Studio, command-line validation, and WFF/XML workflows that function on Linux. Samsung Watch Face Studio may be used only through a separately documented supported environment when necessary.  
**Reason:** The primary workstation is Linux-based, and the project must remain automatable by Claude Code.

---

## 16. Review notes

### 2026-07-24 — Initial architecture review

**Positive findings**

- GitHub access and push permissions are operational.
- Existing APKs are now centrally accessible.
- Several distinct product directions already exist, demonstrating strong creative breadth.
- Commit metadata preserves Claude collaboration context.

**Concerns**

- Repository lacks visible source and build documentation.
- Binaries are stored directly at the repository root.
- Only three preview images accompany seven APKs.
- Release description and actual APK count do not match.
- No machine-readable manifest, checksums, versioning information, or compatibility table is present.

**Architectural judgment**

The project has valid released artifacts but is not yet in a maintainable engineering state. Repository normalization is the correct next phase before expanding the asset generator or creating more products.

---

## 17. Update discipline

Whenever this document changes, preserve historical decisions unless they are explicitly superseded. Mark obsolete decisions as superseded rather than silently deleting them. Add dated review notes after major commits, and keep the immediate backlog synchronized with repository reality.
