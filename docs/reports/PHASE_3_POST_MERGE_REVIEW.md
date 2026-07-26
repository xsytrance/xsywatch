# Phase 3 Post-Merge Architecture Review

**Repository:** `xsytrance/xsywatch`  
**Main head reviewed:** `74ddde7a5cf2503817a262d8bd67d6bb30ba9b17`  
**Paired studio main:** `xsytrance/AGENOR-Horology@cd6718609f38ca79e3b46198a538924cd3e661e9`  
**Review date:** 2026-07-26  
**Verdict:** **APPROVED — Phase 3 remains closed**

## Promotion and merge acceptance

The required studio-first promotion and merge sequence was followed:

1. `AGENOR-Horology` promoted all 50 current r2 handoff lifecycles through metadata-only commit `67b68cb`, recorded the result, and merged through `cd67186`.
2. `xsywatch` synchronized that committed metadata through the hardened importer, promoted `APPROVAL-0004` and `field-tourbillon-mk2-r2`, generated the approved goldens through the established renderer, and merged through `74ddde7`.
3. Both Phase 3 branches are fully contained in their corresponding `main` histories; each `main` is ahead of its branch only by the intended non-squashed merge commit.
4. The immutable Phase 1 release remains unchanged.

The reported final gates are internally consistent with the committed state: 95 engine tests, 38 visual/lineage tests, 62 date-aperture renders with zero violations, 10/10 release fixtures, deterministic XML generation, clean inventory, byte-identical approved reference renders, 10/10 builds, WFF and memory validation, repository validation, whitespace validation, and green CI.

## Assessment of the non-mechanical validator change

The promotion commit correctly expanded the visual-lineage gate from checking only `goldens/<approved_version>` to checking **every committed golden directory** against the approval record that authorized its bytes.

This change is architecturally correct and is accepted.

Superseding a visual generation changes which generation is active; it does not release the older approved evidence from immutability. Without this change, the moment `field-tourbillon-v1` ceased to be active, its normal and AOD reference bytes could change without validation failure. That would recreate the same trust failure class demonstrated by the WARBIRD incident: valid names and structure with incorrect pixels.

The new `test_superseded_golden_change` is appropriate because it states the invariant directly rather than relying only on fixtures that happened to target the previously active version.

The validator change did not alter runtime resources, the tested APK, handoff checksums, approval hashes, or the immutable release. It strengthens historical evidence preservation and therefore does not invalidate the final Phase 3 product or architecture approval.

## Non-blocking future hardening

The current committed golden sets are correctly backed by records whose owner and architecture statuses are both approved. In a later validator-hardening phase, make this invariant explicit by:

1. requiring both `owner.status == "approved"` and `architecture_review.status == "approved"` for every committed golden set; and
2. requiring exactly one authoritative approved record for each committed `visual_version`, rejecting duplicate or ambiguous approved records rather than selecting the last matching record.

These are prospective governance hardening items. They do not represent defects in the current Phase 3 data, because `APPROVAL-0001` and `APPROVAL-0004` are each unique and fully approved.

## Final verdict

**The historical-golden validator expansion is approved. Phase 3 is closed on both repositories. No corrective Phase 3 work is required. Phase 4 remains unstarted and must receive a separately approved scope.**
