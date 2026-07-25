# Phase 3 ChatGPT r1 Review — Aurelius Field Tourbillon Mk II

**Consumer repository:** `xsytrance/xsywatch`  
**Consumer branch:** `phase-3/premium-aurelius-visual-lineage`  
**Consumer head reviewed:** `c8fe253daa79cadc30051d8209ac432056890ea8`  
**Studio repository:** `xsytrance/AGENOR-Horology`  
**Studio branch:** `phase-3/aurelius-studio-slice`  
**Studio head reviewed:** `35b668e3974a885a0b09388f557739bb03f4561b`  
**Review date:** 2026-07-25  
**Verdict:** **CHANGES REQUESTED — engineering architecture accepted; final owner pixel approval withheld pending one focused r2 composition pass**

## Executive assessment

The Phase 3 engineering trust chain is now complete and accepted. The importer parses the exact committed metadata blob, rejects working-tree metadata divergence, verifies every export against the producing Git/LFS snapshot, stages atomically, and rolls back byte-identically. The Rajdhani Bold substitution removes the Bfont commercial ambiguity without altering the selected Olive Instrument / Black Titanium restraint design. Revision `field-tourbillon-mk2-r1`, `APPROVAL-0003`, its inventory, candidate renders, APK, and device evidence are preserved as a distinct proposed revision.

The focused Watch7 test also passed the relevant functional checks: upgrade continuity, live Rajdhani date glyphs, dynamic date binding, AURELIUS engraving, normal readability, ten AOD cycles, stability, smooth motion, and inert touch. The immutable Phase 1 release remains untouched.

No additional engine, importer, provenance, handoff, or release blocker was found in this re-review.

However, r1 disclosed two visible composition defects that should not be frozen into the first premium approved golden:

1. the live date digits visibly overhang the drawn aperture frame; and
2. the lower `FIELD TOURBILLON Mk II` engraving is largely hidden by the tourbillon assembly.

Both are inexpensive plate-art corrections now and expensive historical debt after approval. The product owner therefore does **not** approve r1 as rendered.

## Accepted engineering corrections

### 1. Committed metadata is authoritative

Accepted. `tools/import_handoff.py` resolves `metadata_commit`, reads and parses `<metadata_commit>:<metadata path>`, rejects any working-tree difference, and consults the working tree only for verified LFS-smudged payload bytes. The added tests cover dirty metadata fields, export-set truncation, committed success, legitimate metadata-commit movement, and unchanged consumer state after failure.

### 2. OFL typeface revision

Accepted. All 39 glyph masters and both engraved plates now derive from the SHA-bound Rajdhani Bold OFL-1.1 source. Bfont provenance remains as superseded historical evidence. The nine non-text layers remain byte-identical to Mk II; the reported whole-face r1 delta is confined to text-bearing pixels.

### 3. Supersession and evidence preservation

Accepted. `APPROVAL-0003` supersedes but does not rewrite `APPROVAL-0002`; Mk II candidate references, inventory, approval record, APK/device evidence, and historical provenance remain committed. r1 remains proposed and no release/golden/lifecycle promotion occurred.

## Owner pixel decision — approve with final changes

The selected product direction remains approved:

- Olive Instrument identity;
- Black Titanium Command restraint;
- muted olive and charcoal hierarchy;
- restrained warm-metal details;
- current mechanics, materials, camera, lighting, hands, motion, and data behavior.

The owner requests one final visual revision, preferably named:

`field-tourbillon-mk2-r2`

### Required visual change 1 — properly integrated date aperture

The current studio frame uses an inner opening materially smaller than the live two-digit BitmapFont presentation. Enlarge and rebalance the **plate-art aperture**, rather than shrinking the live data into illegibility.

Acceptance requirements:

1. Keep the date center and WFF data behavior unchanged unless evidence proves a small alignment adjustment is necessary.
2. Preserve zero XML/spec delta if practical.
3. Every valid day value `1..31` must fit inside the visible inner aperture.
4. At 480×480 reference scale, the rendered glyph alpha bounds must have at least **2 px clear margin** from the inner frame on every side.
5. No glyph may overlap the frame, appear clipped, or look optically off-center.
6. The enlarged frame must not collide visually with adjacent mechanics or weaken hand readability.
7. Normal and AOD plate variants must use the same coherent aperture geometry.

Add a deterministic date-aperture proof:

- an automated bounds test covering all values `1..31`; and
- a committed proof/contact sheet including at minimum `1`, `8`, `11`, `22`, `28`, and `31` in normal and AOD treatment.

The test must fail if any glyph alpha bound crosses the required clear-margin region.

### Required visual change 2 — remove the hidden lower engraving

Remove `FIELD TOURBILLON Mk II` from the on-face plate artwork rather than moving another label into an already dense mechanism.

Rationale:

- it is largely occluded;
- hidden text reads as unfinished hierarchy;
- the watch already has the restrained, legible `AURELIUS` signature;
- the full model name remains available in package metadata, documentation, picker description, and release copy;
- removal better matches the approved dark, disciplined, non-gaudy art direction.

Do not replace it with a larger badge, curved slogan, stencil, or extra branding.

## Architecture clarification — device comparison applicability

The r1 evidence correctly demonstrates that a direct device-screenshot-to-reference pixel gate is not universally meaningful for a face with continuously rotating layers and accelerometer-driven full-screen parallax.

Update ADR-009 and the Aurelius visual contract so they do not imply otherwise.

Required clarification:

1. Deterministic reference-to-committed-reference comparison remains exact and mandatory.
2. Device screenshot comparison may be a quantitative hard gate only when all material dynamic phases and sensor inputs can be controlled or masked without hiding most of the face.
3. For dynamic/parallax faces such as Aurelius, the device gate is explicitly:
   - human visual inspection;
   - behavioral validation;
   - exact APK/resource/inventory byte lineage;
   - documented normal/AOD evidence and qualifications.
4. Add a machine-readable applicability/mode field to the face contract, rather than leaving static-face thresholds apparently active for Aurelius. A suitable value is `qualitative-behavioral-lineage`, with the reason recorded.
5. Preserve any generic static-face threshold profile for faces where it is actually applicable.

## Required r2 discipline

Do not overwrite r1.

Create and preserve:

- `field-tourbillon-mk2-r2` studio exports/generation identity;
- a new producing commit and later metadata-stamping commit;
- a new consumer candidate directory;
- a new per-version inventory snapshot;
- a new approval record, preferably `APPROVAL-0004`, explicitly superseding `APPROVAL-0003`;
- new normal/AOD hashes;
- new APK hash;
- focused device evidence.

The expected studio byte delta should be narrow: primarily `bg.png` and `bg_aod.png`, plus consumer preview/reference/inventory artifacts. Rajdhani glyph exports and the nine mechanical layers should remain byte-identical unless a documented date-layout necessity requires otherwise.

Focused Watch7 closure must verify:

- current live date sits fully within the enlarged aperture;
- the frame remains integrated and readable at actual scale;
- the lower hidden engraving is absent with no awkward void;
- AURELIUS remains restrained and legible;
- normal/AOD transitions, motion, stability, and touch remain sound;
- exact APK and inventory hashes are recorded.

Re-run all engine, visual, lineage, handoff, release, build, WFF, memory, repository, whitespace, and CI gates.

## Promotion state

Until r2 receives final owner and architecture acceptance, do not:

- merge either Phase 3 branch;
- set owner or architecture status to approved;
- move a candidate into approved goldens;
- clear `proposed_version`;
- promote handoff lifecycles;
- modify the immutable release;
- begin Phase 4.

## Re-review boundary

This review accepted the engineering architecture based on branch history, source, manifests, records, test implementation, reports, and textual device evidence available through GitHub. It did not independently execute Blender, Gradle, ADB, WFF validation, or replay every video. The final r2 pixel decision remains an explicit product-owner judgment.
