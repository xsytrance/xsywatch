# ADR-007 — Commit Gradle wrappers; normalize only project-ROOT paths in Phase 1

**Status:** Accepted (Phase 1, 2026-07-24)
**Context:** Local projects had no gradlew (relied on a machine-local Gradle
9.6.1) and asset scripts hard-code two kinds of absolute paths:
(a) the project ROOT, (b) external AI donor images under ~/AI/.
**Decision:**
1. Generate and commit the Gradle 9.6.1 wrapper in every imported face so a
   clean clone builds with only JDK 21 + Android SDK.
2. Normalize only (a) — ROOT derived from the script's own location — as a
   mechanical, py_compile-verified change. External donor paths (b) remain
   as-is and are documented as provenance: committed drawables are canonical,
   so builds never require them.
**Consequences:** Reproducible builds without risky rewrites of generator
scripts; full generator portability deferred (tracked in KNOWN_LIMITATIONS).
