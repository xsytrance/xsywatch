# ADR-008 — Build-time WFF engine; Aurelius reference face; WFF v4 baseline

**Status:** Accepted  
**Date:** 2026-07-24  
**Scope:** `xsywatch` Phase 2 and later engine work

## Context

Watch Face Format applications are resource-only declarative packages. Their
`<application>` uses `android:hasCode="false"`; Wear OS parses the committed WFF
XML and renders it through the system renderer. This means the reusable AGENOR
"engine" cannot be a runtime Android library embedded in each face.

The repository now contains ten complete watchface projects. Their repeated
patterns include ambient-mode behavior, time and date presentation, battery and
heart-rate bindings, analog-hand stacks, rotating mechanical layers, parallax,
and validation/release conventions.

Aurelius is the strongest reference candidate because its current WFF v4 face
contains a compact but representative combination of:

- normal/AOD background transition;
- accelerometer parallax;
- mechanically rotating gear layers;
- heart-rate-driven balance-wheel oscillation with fallback/clamping;
- seconds-driven tourbillon cage;
- battery power-reserve needle;
- date aperture;
- analog hour/minute hand stack;
- layered sheen and ambient reductions.

Official WFF guidance recommends declaring the lowest format version that
supports the required features. WFF v4 already supports the Phase 2 feature
set, including ambient transitions and the `Reference` element for
single-sourcing transform configurations.

References:

- https://developer.android.com/training/wearables/wff/setup
- https://developer.android.com/training/wearables/wff
- https://developer.android.com/training/wearables/wff/release-notes

## Decision

1. **The AGENOR WFF engine is a deterministic build-time system.** It will
   generate, validate, and synchronize declarative WFF resources. It will not
   pretend that WFF supports a runtime shared-code layer.
2. **Generated `watchface.xml` remains committed.** Developers must be able to
   inspect and build a face without running a hidden service. A check mode must
   fail when the generated file drifts from its authoritative engine/spec input.
3. **Aurelius is the Phase 2 engineering reference face.** Engine abstractions
   must first reproduce Aurelius behavior before they are generalized broadly.
4. **WFF v4 / API 36 remains the Phase 2 baseline.** Phase 2 must not upgrade
   Aurelius or the repository baseline to WFF v5 unless a required capability
   cannot be implemented in v4 and the compatibility impact is documented in a
   superseding ADR.
5. **Reusable behavior belongs in `engine/`; product art remains face-owned.**
   The engine may own expression builders, component factories, naming/z-order
   rules, generation, structural validation, and reusable non-branded assets.
   Aurelius-specific artwork, typography choices, layout, and military design
   identity remain under `watchfaces/aurelius/`.
6. **The sibling repository boundary remains intact.** Blender, materials,
   geometry, lighting, and master render assets remain in
   `xsytrance/AGENOR-Horology`. `xsywatch` receives versioned exports through a
   documented handoff manifest; no submodule, subtree, or copied Git history is
   introduced in Phase 2.
7. **No broad migration in Phase 2.** Other production faces remain unchanged
   except for audit tooling, shared validation, or a deliberately isolated test
   fixture. Engine APIs that have not been proven by Aurelius remain
   experimental.

## Consequences

### Positive

- Reuse matches the actual WFF execution model.
- Engine changes remain reviewable and deterministic.
- Aurelius supplies a real behavioral test bed rather than hypothetical
  abstractions.
- WFF v4 compatibility is preserved while the engine is established.
- Product-specific artwork is not accidentally generalized or exposed.

### Costs and risks

- Generated XML adds a source/generated synchronization requirement.
- Build-time abstractions can become over-engineered; Phase 2 therefore limits
  extraction to components demonstrated by the audit and Aurelius.
- Cross-repository asset changes are not atomic; handoff manifests must record
  exact source commit hashes and checksums.
- Physical-device behavior still requires explicit Galaxy Watch7 evidence; XML
  generation and Gradle success are not sufficient proof.

## Supersession rule

A future move to WFF v5, a different reference face, or a merged repository
model requires a new ADR that explicitly supersedes the relevant part of this
decision.
