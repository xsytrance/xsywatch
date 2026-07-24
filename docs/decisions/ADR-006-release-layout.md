# ADR-006 — Versioned releases/ layout; tracked APKs stay; future binaries via GitHub Releases

**Status:** Accepted (Phase 1, 2026-07-24)
**Context:** Seven debug APKs lived at repo root with no metadata. Ledger §5
requires binaries in Releases or LFS "before history grows".
**Decision:**
1. Layout: `releases/<slug>/current/{<slug>.apk, preview.png, RELEASE.md}`
   plus machine-readable `releases/MANIFEST.json` (checksums, versions,
   original filenames for traceability). Superseded versions move to
   `releases/<slug>/vX.Y.Z/`.
2. The seven existing APKs (28 MB total) stay git-tracked — rewriting pushed
   history to LFS them is forbidden by the phase rules and unnecessary at
   this size.
3. From the next release onward, APKs are ALSO attached to versioned GitHub
   Releases; if tracked binary growth exceeds ~200 MB, new binaries move to
   Releases-only and the manifest keeps checksums.
**Consequences:** Full traceability now; history stays clone-friendly; no
force-push ever required.
