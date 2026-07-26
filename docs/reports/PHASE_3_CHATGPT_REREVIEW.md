# Phase 3 ChatGPT Architecture Re-review

**Consumer repository:** `xsytrance/xsywatch`  
**Consumer branch:** `phase-3/premium-aurelius-visual-lineage`  
**Consumer head reviewed:** `684ff51edffce941c1b56ebfb89329b26b370363`  
**Studio repository:** `xsytrance/AGENOR-Horology`  
**Studio branch:** `phase-3/aurelius-studio-slice`  
**Studio head reviewed:** `438f0885db511a495cc953d7c92f27966a5619fa`  
**Date:** 2026-07-25  
**Architecture verdict:** **CHANGES REQUESTED — one narrow lineage correction remains**  
**Recommended owner decision:** **APPROVE WITH CHANGES — preserve the selected Mk II design, substitute the Bfont-derived glyph/engraving masters with the audited OFL-1.1 Rajdhani Bold source, then perform final pixel acceptance.**

## Executive assessment

The original engineering blockers were addressed substantively rather than cosmetically.

- The visual approval record now binds exact resources and handoff IDs to computed per-version inventory deltas.
- The transparent spacer is explicitly represented as a manifested but byte-identical handoff asset.
- Export bytes are verified against the exact producing Git/LFS snapshot.
- Source and specification paths are verified at the producing commit.
- Import is staged and rollback-protected.
- Font provenance is now recorded accurately instead of claiming original authorship.
- Candidate and immutable-release bytes remain unchanged.

The visual-lineage architecture, item-level approval contract, source-snapshot verification, rollback design, and provenance registry are accepted in principle.

One small but real metadata-lineage hole remains in `tools/import_handoff.py`. It must be fixed before merge because the generated consumer manifest records `metadata_commit` as the provenance of metadata fields that are currently read from the studio working tree without proving those bytes exist at that commit.

## Original blocker 2 — exact approval binding: accepted

`APPROVAL-0002` now contains:

- 49 exact changed runtime-resource paths;
- 50 exact handoff asset IDs;
- `preview.png` separately classified as a generated consumer resource;
- one explicitly reasoned `unchanged_handoff_assets` entry for `g_space.png`;
- previous and proposed inventory snapshot paths whose bytes are SHA-bound to their records.

`check_visual_delta` computes the authoritative delta and rejects wildcard/prose entries, duplicates, missing/extra resources, unknown IDs, unchanged resources falsely listed as changed, generated resources posing as studio assets, and handoff assets whose destinations are not covered appropriately.

This closes the original approval-binding blocker.

## Original blocker 3 — source snapshot and atomic import: mostly accepted

The corrected importer now:

1. verifies every export at `<source_commit>:<export_file>`;
2. parses Git LFS pointer OIDs or hashes ordinary blobs;
3. verifies every producing source and specification path at that commit;
4. requires the producing commit to be an ancestor of the resolved metadata commit;
5. rejects dirty export bytes even when working-tree metadata is updated to match them;
6. stages every export before replacement;
7. restores all original consumer bytes and the manifest on a late replacement failure.

The new tests exercise the principal pre-review hole and rollback behavior successfully.

### Remaining blocker — metadata bytes are not bound to `metadata_commit`

The importer currently does this:

- reads `handoff_metadata.json` from the current studio working tree;
- resolves `metadata_commit` with `git log -1 -- <metadata path>`;
- checks ancestry;
- writes the working-tree metadata values into the consumer manifest.

It does **not** compare the current metadata file with `<metadata_commit>:<metadata path>`.

Therefore, after a valid metadata commit, an uncommitted edit to fields such as `license`, `lifecycle`, `pivot`, `dimensions`, `consumer_component`, `regenerate`, the export set, or generation identity may be imported while the resulting manifest still records the older `metadata_commit` as its provenance.

Required correction:

1. Read the metadata blob at `<metadata_commit>:<metadata_rel>`.
2. Require its bytes to equal the working-tree metadata bytes before parsing/importing, or parse the committed blob directly and treat it as authoritative.
3. Prefer parsing the committed blob directly; use the working tree only to obtain LFS-smudged export payloads after their committed OIDs are verified.
4. Add tests proving:
   - an uncommitted edit to an already-committed metadata file is rejected;
   - a dirty lifecycle/license/pivot field cannot reach `engine/handoff.json`;
   - a dirty metadata edit that removes one export cannot create a truncated manifest;
   - committed metadata continues to import successfully.

This is a narrow correction, but it is required for the claim that `metadata_commit` binds the manifest metadata.

## Original blocker 4 — font provenance: provenance fixed; commercial decision remains

The correction accurately identifies the source as Blender built-in `Bfont 001.001`, records the extracted program and producing toolchain hashes, adds notice/provenance records, marks the 39 glyph exports plus the two engraved plates as derived, and prevents `font-glyphs` from claiming `original`.

That closes the inaccurate-provenance blocker.

The official Blender manual states that Blender's GPL applies to the application and not to artwork created with it. The repository's decision to retain `commercial_use_resolved: false` for raster glyphs derived from the built-in font is consequently conservative rather than a demonstrated prohibition. This review does not make a legal determination.

For a product intended to be sold, the clean engineering and commercial decision is nevertheless to remove the ambiguity now. The candidate has not been promoted, so this is the lowest-cost point to substitute the existing audited `rajdhani_bold.ttf` under OFL-1.1.

## Recommended owner decision — approve with changes

Do not reject the owner-selected Olive Instrument / Black Titanium restraint direction. The mechanics, composition, device behavior, and visual generation should remain the Mk II design.

Approve the direction **with these precise corrections before final pixel acceptance**:

1. Replace Bfont for all 39 BitmapFont glyph masters with the committed/audited Rajdhani Bold source.
2. Replace the baked `AURELIUS` and `FIELD TOURBILLON Mk II` plate engravings with the same audited source, or another already-audited OFL-1.1 source selected consistently.
3. Regenerate the studio exports and handoff metadata through the corrected commit-bound process.
4. Produce a new proposed visual version rather than overwriting the current candidate silently, for example `field-tourbillon-mk2-r1`.
5. Preserve the current Mk II candidate, hashes, approval record, and device evidence as historical proposed evidence.
6. Generate a new approval record or explicitly supersede `APPROVAL-0002` according to ADR-009 without rewriting history.
7. Rebuild the APK, refresh normal/AOD references and preview, calculate exact visual deltas, and rerun the complete static and physical-device matrix.
8. Return the new candidate to the owner for the final normal/AOD pixel decision.

The font substitution is expected to be localized, but it changes packaged bytes and therefore requires new APK, reference, inventory, approval, and device-evidence hashes.

## Merge and promotion state

Until the metadata-binding fix and owner-directed font substitution are completed:

- do not merge either branch;
- do not set `owner.status` to `approved`;
- do not set `architecture_review.status` to `approved`;
- do not promote candidate references to goldens;
- do not clear `proposed_version`;
- do not promote the 50 handoff lifecycles;
- do not alter the immutable release.

After the fixes and explicit owner acceptance, return both branches for a final, narrow re-review. Merge order remains studio first, consumer second, using normal non-squashed merge commits.

## Verification boundary

This re-review inspected the correction commits, exact approval record, delta validator, importer implementation, importer tests, handoff manifest, provenance records, updated reports, and branch ancestry through the GitHub connector. The connector did not expose branch-push Actions check runs through its PR-filtered workflow endpoint, so the reported green CI and local execution counts were not independently replayed here. Blender renders, Android builds, ADB tests, and device recordings were not independently rerun.