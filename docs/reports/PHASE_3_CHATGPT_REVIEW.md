# Phase 3 ChatGPT Architecture Review

**Consumer repository:** `xsytrance/xsywatch`  
**Consumer branch reviewed:** `phase-3/premium-aurelius-visual-lineage`  
**Consumer head reviewed:** `8b70d36d5853e52cf097c381bd4e5877a7e769c1`  
**Studio repository:** `xsytrance/AGENOR-Horology`  
**Studio branch reviewed:** `phase-3/aurelius-studio-slice`  
**Studio head reviewed:** `412514817be1e3546061808eb3e4c0fccecd8cb8`  
**Review date:** 2026-07-25  
**Verdict:** **CHANGES REQUESTED — do not merge either branch and do not promote APPROVAL-0002 yet**

## Executive assessment

Phase 3 is a major architectural success. The visual/resource-lineage gate was implemented before production import, the permanent synthetic WARBIRD-class fixture fails both visual comparison and repository validation, deterministic candidate references are checksum-bound, 50 real studio exports reached the consumer without an XML/spec delta, the immutable release remains untouched, and the premium candidate passed the reported Galaxy Watch7 matrix.

The central architecture is approved. Four narrow closure items remain before the two branches can be merged as a completed Phase 3. These items matter because they sit precisely at the trust boundaries introduced by ADR-009: owner approval, machine-readable delta binding, exact cross-repository commit lineage, and commercial asset provenance.

## Approved findings

- Gate-before-import history and focused phase commits.
- Deterministic reference renderer and seven pinned visual states.
- Exact reference-render comparison plus constrained device thresholds/masks.
- Seventeen visual tests covering all nine mandatory deliberate failures.
- Permanent same-name/wrong-art regression fixture.
- Legacy v1 goldens and inventory preserved under APPROVAL-0001.
- Proposed-candidate lifecycle that leaves approved v1 goldens frozen.
- Fifty checksum-bound studio exports and real handoff entries.
- Zero WFF XML/spec delta for the Mk II candidate.
- Reported 68/68 engine tests, 10/10 release fixtures, 10/10 builds, WFF validation, memory evaluation, repository validation, and green CI.
- Physical Watch7 evidence binding the intended Mk II pixels to candidate APK `d734abc8…`.
- Immutable release APK `844b9c43…` remains unchanged.
- Cycles render nondeterminism is disclosed; committed export bytes are treated as canonical.
- The direct AOD screencap limitation remains an accepted hardware qualification, provided the owner completes the required on-wrist visual judgment.

## Merge blocker 1 — explicit owner pixel acceptance is still missing

The approved Phase 3 brief requires both:

- an owner-approved visual-change record before approved goldens move; and
- an explicit owner visual acceptance or rejection after physical-device review.

`APPROVAL-0002` correctly remains `owner.status = proposed`, and `states.toml` correctly leaves `field-tourbillon-v1` as the approved version while gating deterministic Mk II candidate renders. That is the right interim state, but it is not a completed Phase 3 acceptance state.

The owner must inspect the normal face and the actual on-wrist AOD presentation and explicitly choose one of:

1. **Approve Mk II as rendered**;
2. **Approve with precisely documented minor corrections**; or
3. **Reject and request another proposed visual version**.

Architecture review is not a substitute for the product owner's aesthetic decision. The report itself notes that the studio surfaces are still “parametric-primitive quality” and defers hero-grade anglage, Geneva stripes, and engraved-scale refinement. That may be an acceptable Phase 3 foundation or may be below the owner's desired commercial bar; only the owner can decide.

Do not promote the candidate, move goldens, or set asset lifecycle to `approved` until the owner gives that explicit decision.

## Merge blocker 2 — APPROVAL-0002 does not bind exact changed resources and handoff IDs

ADR-009 requires a **machine-readable** reviewed visual delta. The current record contains:

- one prose `changed_resources` entry summarizing “50 runtime resources ...”; and
- one prose `handoff_asset_ids` entry saying “ALL 50 entries ...”.

Those are human-readable summaries, not enforceable item-level bindings. The validator checks that these fields exist but does not prove that the approval record names the exact resources and exact handoff assets involved.

Required correction:

1. Replace the summary strings with exact repository-relative changed-resource paths.
2. Enumerate all exact handoff `asset_id` values.
3. Record `preview.png` separately as a generated consumer preview, not a studio handoff asset.
4. Extend validation so it proves:
   - every listed handoff ID exists exactly once in `engine/handoff.json`;
   - every studio-handoff runtime resource changed from the previous approved inventory is represented;
   - every listed changed resource exists in the proposed inventory;
   - no missing, duplicate, wildcard, or unknown entries are accepted;
   - the record's inventory hash matches the candidate inventory;
   - approved promotion cannot proceed with incomplete delta coverage.
5. Add positive and deliberate-failure tests for missing one ID, adding an unknown ID, duplicate IDs, using a prose wildcard, and omitting a changed resource.

## Merge blocker 3 — import_handoff verifies the working tree, not the declared source commit snapshot

`tools/import_handoff.py` verifies that `source_commit` exists, then hashes files from the **current studio working tree**. It does not prove that those exact bytes are contained at the declared source commit.

The current Phase 3 data appears internally consistent: the export-producing commit exists, and sampled LFS object IDs match the metadata hashes. But the tool's guarantee is weaker than the contract. A dirty studio checkout or later modified export could be imported while still being attributed to an older commit, provided metadata and working-tree bytes agree.

Required correction:

1. Verify each export against the exact `source_commit` snapshot.
   - For Git LFS files, read the pointer at `<commit>:<path>` and require its `oid sha256:` to equal the handoff SHA-256.
   - For ordinary Git blobs, hash the blob bytes from `<commit>:<path>`.
2. Verify every `source_paths` entry and `spec_path` exists at that commit.
3. Verify metadata itself is tied to a documented later stamping commit or redesign the metadata workflow so the relationship is unambiguous.
4. Make import two-phase and fail-safe:
   - validate every entry first;
   - stage copies in a temporary area;
   - replace runtime files and write the manifest only after the entire set passes.
   The current loop can partially copy earlier files before a later failure even though it declines to write the manifest.
5. Add tests for:
   - dirty/current working-tree bytes differing from the declared commit;
   - valid metadata pointing to the wrong historical commit;
   - missing source/spec paths at the commit;
   - a later-entry failure leaving the consumer tree completely unchanged;
   - LFS pointer OID mismatch.

## Merge blocker 4 — glyph exports are mislabeled as original

The studio report states that engravings and glyph masters use Blender's bundled DejaVu-derived font. However, the 39 `font-glyphs` handoff entries currently say:

`"license": "original"`

Rasterizing a third-party font does not make the glyph design original. The likely license may permit this use, but the provenance record must be accurate before this project is described as commercially credible.

Required correction:

1. Identify the exact bundled font used by the pinned Blender version.
2. Record its exact name, source/bundled path or Blender asset identity, SHA-256 where obtainable, license identifier, and authoritative license/notice text.
3. Add the required notice/provenance record in the studio repository and the consumer repository where the derived glyph exports are inventoried.
4. Change all derived glyph handoff entries from `original` to a precise license/provenance reference.
5. Ensure the license reference is machine-validated and resolves to an existing record/notice.
6. Update both Phase 3 reports' licensing sections.
7. Add a validation fixture proving `font-glyphs` entries cannot claim `original` when their declared source is a third-party bundled font.

This is a provenance correction, not an assertion that commercial use is forbidden.

## Required promotion sequence after the blockers are fixed

After engineering corrections and explicit owner approval:

1. Update `APPROVAL-0002` with exact resource paths and handoff IDs.
2. Set the owner status, identity, date, and decision accurately.
3. Return both branches for ChatGPT re-review.
4. After architecture approval, set `architecture_review.status = approved` with the review commit reference.
5. Run the validated promotion procedure:
   - move/copy proposed Mk II references to the approved golden location;
   - set `approved_version = field-tourbillon-mk2`;
   - clear `proposed_version`;
   - promote the 50 applicable handoff lifecycles from `candidate` to `approved`;
   - preserve APPROVAL-0001 and v1 goldens as historical evidence;
   - do not change `releases/aurelius/current/`.
6. Re-run all engine, release, visual, inventory, handoff, build, WFF, memory, repository, whitespace, and CI gates.
7. Merge the studio branch first, then the consumer branch, using normal non-squashed merge commits so the consumer's referenced studio commit is permanently reachable from studio `main`.

## Re-review acceptance criteria

Phase 3 may be approved when:

- owner acceptance/rejection is explicit and committed;
- APPROVAL-0002 contains exact item-level bindings and validation enforces them;
- importer verifies exact Git/LFS snapshot lineage and is atomic/fail-safe;
- glyph licensing/provenance is accurate and notice-bound;
- all new deliberate-failure tests pass;
- all previously reported static/device gates remain green;
- immutable release checksum remains unchanged;
- both reports and this review receive resolution sections;
- neither branch is merged before final re-review.

## Verification boundary

This review inspected branch history, source diffs, approval records, visual contract, validation logic, importer logic, handoff entries, studio export commits/LFS pointers, reports, and textual device evidence through the GitHub connector. It did not independently execute Blender, Android builds, ADB commands, or replay every committed video. Product-owner pixel acceptance is intentionally outside the architecture role.