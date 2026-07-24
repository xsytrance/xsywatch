# ADR-005 — AGENOR-Horology stays a sibling repository; no empty engine/ scaffold

**Status:** Accepted — RATIFIED by owner (Phase-1 review, 2026-07-24)
**Context:** The 3D asset pipeline (Blender/Material Maker library, render &
sprite tooling, AlienMilitary spec) already exists as the pushed repository
`xsytrance/AGENOR-Horology`. The architecture ledger and Phase-1 brief both
propose an `engine/` tree inside `xsywatch`.
**Decision:**
1. `AGENOR-Horology` remains a sibling repo (design/3D pipeline); `xsywatch`
   is the WFF source + release repo. Cross-references documented in both.
2. No `engine/` directory is created in `xsywatch` until Phase 2 actually
   extracts shared code (per ledger ADR-003: reference face first). Empty
   scaffolding misrepresents repository maturity.
**Consequences:** Sprite sheets/renders produced by the asset repo are copied
into a face's `res/` as versioned artifacts with provenance notes. If the two
repos later need atomic commits, merging AGENOR-Horology in as a subtree is
the documented migration path (its history is preserved either way).
