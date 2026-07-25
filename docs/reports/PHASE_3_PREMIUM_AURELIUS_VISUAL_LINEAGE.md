# Phase 3 report — Premium Aurelius Mk II and the visual/resource-lineage gate

**Branch:** `phase-3/premium-aurelius-visual-lineage` (base: `main` @ `759f74e`)  
**Paired studio branch:** `AGENOR-Horology phase-3/aurelius-studio-slice`  
**Studio report:** `AGENOR-Horology/docs/reports/PHASE_3_AURELIUS_STUDIO_SLICE.md`

## 1. Executive summary

Both Phase-3 outcomes delivered in the mandated order. The
visual/resource-lineage gate was built and proven against all nine
deliberate-failure classes — including a synthetic reproduction of the
WARBIRD incident — BEFORE any production asset moved. The first real
AGENOR studio handoff then delivered the owner-selected Aurelius "Field
Tourbillon Mk II" (concept B tuned with A restraint) as a pure,
fully-manifested asset swap with zero XML/spec delta, integrated through
the existing engine, verified by every static gate, and confirmed on the
physical Galaxy Watch7.

## 2. Branches and commits

`xsywatch` (this branch):
1. `a94b309` — legacy visual contract + deterministic inventories
2. `be95f8d` — deterministic renderer, comparison, legacy goldens
3. `da0a436` — intentional visual approval workflow + failure fixtures + CI
4. `9e50125` — real studio handoff import (50 assets) + proposed candidate
5. (final) — device evidence + this report

`AGENOR-Horology`: `bb57a9a` audit/concepts → `632768b` foundation →
`aea4911` mechanical slice + A/B/C renders → `74ac144` owner selection →
`1d51b58` LIB extraction + Mk II exports (the handoff source commit) →
`7626ec8` metadata stamp → `4125148` studio report.

## 3. WARBIRD-derived risk model

Phase 2 proved structural gates cannot see pixels. Phase 3 treats visual
identity as a tested contract: every runtime byte inventoried and
checksum-bound, approved references reproducible byte-for-byte from
committed sources, intentional change only through machine-readable
owner-approved records, and physical-device confirmation for each visual
generation. The WARBIRD class (same name/valid metadata/wrong art) is now
a permanent automated regression fixture (ADR-009).

## 4–6. Visual contract, renderer, comparison

- **Contract** (`watchfaces/aurelius/visual/states.toml`): seven fully
  pinned states (hero 10:09:35/day 24/80%/HR 72/accel 0, AOD forcing
  sub-minute sources to 0 per device-observed ambient behavior, battery/
  HR/parallax variants); golden + candidate lifecycle; comparison policy.
- **Renderer** (`tools/render_reference.py` + `tools/visuallib.py`):
  composes the COMMITTED generated XML + committed res/ bytes (spec→XML
  already gated by `generate_face.py --check`; this closes XML→pixels),
  evaluating the WFF expression subset (arithmetic, %, comparisons,
  ternary, clamp, sin, data sources) in IEEE-754 doubles. Byte-identical
  reruns proven per state (`--selftest`) and in CI. Non-reproduced
  runtime behaviors documented (ambient transitions, panel response,
  system overlays, runtime resampling) — relevant only to device
  captures.
- **Comparison** (`tools/compare_visuals.py`): exact mode (zero
  tolerance) for deterministic renders; evidence-calibrated device
  profile (1.5% changed / mean Δ3 / max Δ48) two orders below
  WARBIRD-scale deltas; amplified diff heat-maps; sha-bound reports;
  masks restricted by a ≥60% face-disc coverage policy.

## 7. Deliberate-failure fixture results

`tests/visual/test_lineage_gate.py` — 17 tests, all green, covering the
nine mandated classes: same-name background substitution (synthetic
WARBIRD: FAILS at 91.2% changed pixels AND fails plain `validate.py`
directly), hand substitution, font-glyph substitution, unexpected extra
drawable, unmanifested studio bytes, unapproved golden change, approval-
hash mismatch, over-broad mask (rejected at 2% disc coverage), inventory
checksum tamper — plus determinism and reproduction positives and
expression-evaluator units.

## 8. Legacy inventory and goldens

`field-tourbillon-v1` goldens (normal `f52b715e…`, aod `04161e9b…`),
byte-reproducible in CI; legacy inventory (60 resources) committed;
bound by owner-approved APPROVAL-0001 (countersigned at the concept
checkpoint). Discovery: `tourb_base/disc/rim.png` ship unreferenced (also
in the immutable APK) — grandfathered with rationale on the explicit
allowlist.

## 9. Intentional visual approval workflow

Machine-readable records under `visual/approvals/` bind previous/proposed
golden hashes, inventory hash, changed resources, handoff ids, metrics,
rationale, owner status, architecture-review status, and device-evidence
path. `validate.py` (stdlib) enforces: approved goldens byte-match an
owner-approved record; committed inventory is record-bound AND matches
live tree bytes; uninventoried resources fail. The candidate lifecycle
(`states.toml goldens.proposed_version`) lets a proposed generation be
CI-verified (deterministic re-render must match the bound candidate
renders) while approved goldens stay frozen until owner promotion.

## 10. Owner-selected concept

**B — Olive Instrument, tuned with A (Black Titanium Command) restraint**
(`AGENOR-Horology watchfaces/AureliusMk2/concept/OWNER_SELECTION.json`,
production palette S): olive bead-blast identity, charcoal instrument
base, DLC dominance, steel mechanics, warm gold strictly as hierarchy
detail; WARBIRD/AlienMilitary/neon/clutter excluded. Emotional target:
elite reconnaissance field tourbillon.

## 11. Studio assets and handoff

50 exports (11 layers + 39 BitmapFont glyphs) produced at AGENOR commit
`1d51b58` against the calibrated 43 mm = 480 px camera contract, at the
EXACT legacy layer set, boxes, art-zero pivots, and glyph cell widths.
`tools/import_handoff.py` verified every byte against the studio sha256
(and the commit's existence) before copying, re-verified after, and
wrote 50 real manifest entries (lifecycle `candidate`, real destinations,
regeneration commands). The synthetic Phase-2 example is retired.
`tools/validate.py` recomputes every manifest checksum on every run.

## 12–14. Candidate inventory, spec delta, visual diff

- Candidate inventory `d64c3e95…` (60 resources; 50 studio-handoff + 10
  legacy/structural), bound to APPROVAL-0002.
- **Zero XML/spec delta**: `face.toml` untouched; generation and the
  full Phase-2 parity suite pass unchanged. The premium candidate is
  pixels only — by construction at export time.
- Candidate renders `candidates/field-tourbillon-mk2/` (normal
  `28fd289e…`, aod `0d0c2070…`), byte-reproducible in CI and bound to
  APPROVAL-0002 (owner status: `proposed` — final pixel acceptance is the
  owner's device review). Measured intentional delta vs v1: 78.99%
  changed pixels, mean Δ67.9 (recorded in the approval record as the
  generation change, not drift).

## 15. Static verification (candidate `d734abc8…`)

- Engine tests: 68/68 · release-workflow fixtures: 10/10
- `generate_face.py aurelius --check`: OK (zero delta)
- All-ten build: 10/10 PASS
- Official WFF validator: PASS (v4)
- Memory-footprint evaluator: PASS
- `tools/validate.py`: 0 errors (visual gate included)
- Visual suite: 17/17 · inventory `--check`: clean
- CI: green through the import commit (`9e50125`)
- Immutable Phase-1 release: `844b9c43…` unchanged, pin enforced

## 16–17. Physical Galaxy Watch7 evidence

Device: SM-L310, Android 16 / API 36, wireless adb (owner-provided),
2026-07-25 session; battery 11–22% on charger during captures (bolt
overlay visible in docked captures; noted where relevant).

- **Upgrade continuity**: `install -r` over the Phase-2 corrected
  candidate (`b01015c8…` verified on-device pre-upgrade) → Success; face
  re-selected in picker (documented One UI deactivation behavior).
- **Intended pixels confirmed live** (`candidate_normal_device.png`):
  Mk II olive/charcoal/DLC/steel/gold design — not legacy, not WARBIRD,
  not mixed; picker thumbnail now matches the live render (preview.png
  regenerated from the candidate — the exact gap that hid WARBIRD is
  closed).
- **Dynamic data**: date aperture renders TODAY (25) via the imported
  glyph set; reserve needle at the low-battery arc position consistent
  with 11–14%; hands at live time over the premium mechanism, legible.
- **Mechanics**: cage ~126° per 21 s (6°/s) with concentric rotation
  about the rendered arbors; gear pivots aligned (no wobble in crops);
  66 s motion recording continuous, no stutter, no resource
  disappearance; touch inert (SysUI stays top); crash buffers clean.
- **AOD**: enter/exit + 10 scripted cycles PASS with a clean render
  after; the panel's ambient frame is not capturable in this hardware
  state (off-wrist doze = display off; docked doze = system charging
  screen — same qualification the Phase-2 final review accepted). The
  ambient composition is byte-determined by the CI-verified reference
  AOD render (`0d0c2070…`), and the AOD plate bytes are sha-chained
  studio → manifest → APK. On-wrist AOD look is explicitly part of the
  owner's acceptance check.
- Evidence: `docs/reports/evidence/phase-3/aurelius/` (device captures,
  recordings, per-row notes in `DEVICE_TEST_RESULTS.md`).

## 18. Immutable release preservation

`releases/aurelius/current/aurelius.apk` = `844b9c43…` throughout; the
`.immutable` pin is validation-enforced; no release was created or
promoted.

## 19. Licensing / AI-donor findings

The mechanical, material, camera and lighting work is original
parametric/procedural studio work (AGENOR-Horology, Phase 3): no
third-party textures or HDRIs, no AI-generated donors.

**Corrected after review (blocker 4).** This section previously stated
that the glyph and engraving masters use "Blender's bundled font
(DejaVu-derived, license-compatible)". That was an assumption and it was
wrong. The measured font is Blender's **built-in `Bfont 001.001`**, a
PostScript Type 1 program compiled into the executable
(`filepath == '<builtin>'`), carrying no embedded copyright notice,
SHA-256 `8bb299bdca151cb48bf1909eafffabe733fdd74171c11aeb72b9f09104962aed`
(reproducible via `AGENOR-Horology scripts/extract_builtin_font.py`). It
is provably **not** DejaVu and **not** Inter — the same string rendered
with each yields different outline geometry — and Blender 4.5.11 bundles
no DejaVu *Sans* at all. Because `Bfont` is absent from Blender's
`license.md` Fonts table (which lists only separately distributed font
files), it is covered by Blender's own licence: **GPL-3.0-or-later,
© Blender Foundation**, not a permissive font licence.

Consequences, all recorded machine-readably:

- The 39 `font-glyphs` exports and the 2 plates carrying baked
  `AURELIUS` / `FIELD TOURBILLON Mk II` engravings now declare
  `license: "derived:blender-bfont-type1"` instead of `"original"`.
- `docs/derived-asset-provenance.json` holds the resolvable record
  (identity, pinned Blender binary hash, licence, notice, open item);
  `THIRD_PARTY_NOTICES/fonts/blender-bfont-NOTICE.txt` holds the notice.
- `tools/validate.py` enforces both directions: a `font-glyphs` export
  may never claim `original`, and any `derived:<id>` must resolve to a
  record whose `notice_file` exists.

**OPEN owner/legal item (not a merge blocker, but a release blocker).**
Bfont carries no font exception, so whether GPL terms reach raster
artwork derived from a GPL font program is unresolved; typeface-design
protection also varies by jurisdiction. The record is flagged
`commercial_use_resolved: false`. Recommended mitigation is cheap and
already available: re-render the glyph and engraving masters with a font
already audited and notice-bound here (e.g. `rajdhani_bold.ttf`,
OFL-1.1 — also the legacy Aurelius face font). It is deliberately **not**
applied in this correction round because it would change candidate pixels
while the owner's on-watch acceptance is pending; it is offered as an
explicit option within that pending decision.

## 20. Deviations, risks, technical debt, next phase

- Deviations: none against the brief's mandatory order or boundaries.
  The reference renderer targets the committed XML rather than face.toml
  directly (stronger chain; documented §4–6). Candidate lifecycle added
  `goldens.proposed_version` to keep CI honest pre-promotion (ADR-009
  §5-consistent; validated).
- Risks/debt: concept-grade surface finishing (hero sculpting is the
  natural Phase-4 studio increment); Cycles re-renders are not
  byte-deterministic (committed bytes are canonical — same rule as donor
  images); official WFF validator still runs locally with committed
  evidence rather than in CI (unlicensed-binary + toolchain caveats
  unchanged from Phase 2); wear-day battery observation remains
  owner-side.
- Recommended Phase 4: owner promotion decision (goldens flip +
  lifecycle `candidate → approved`), release packaging decision for
  Mk II, hero-grade studio finishing pass, WFF validator CI onboarding
  from a pinned upstream revision, and the deferred Pinball creative
  thread.

## 21. Workflow note for promotion (post-review)

To promote after owner acceptance: flip APPROVAL-0002 owner status to
`approved`, copy `candidates/field-tourbillon-mk2/*` to
`goldens/field-tourbillon-mk2/`, set `approved_version` to
`field-tourbillon-mk2`, clear `proposed_version`, flip the 50 manifest
lifecycles to `approved`, and re-run the full gate. Every step is
validated; nothing moves silently.

## 22. Review corrections (post-review pass, 2026-07-25)

ChatGPT's coordinated Phase-3 review (`PHASE_3_CHATGPT_REVIEW.md`,
consumer commit `b104845`, studio commit `644ee3e`) returned CHANGES
REQUESTED with four blockers. Engineering blockers 2–4 are fixed; blocker
1 is the owner's pending decision and is deliberately untouched.

**Blocker 2 — APPROVAL-0002 item-level bindings (FIXED).**
The prose summaries are replaced with exact values: **49**
`changed_resources` repository-relative paths, **50** `handoff_asset_ids`,
`preview.png` recorded separately under `generated_consumer_resources`
as a generated consumer preview, and **1** `unchanged_handoff_assets`
declaration. Per-version inventory snapshots are now committed
(`visual/inventories/versions/field-tourbillon-{v1,mk2}.json`, hashes
`fee59354…` / `d64c3e95…` matching the two records) so the delta is
computable rather than asserted. `tools/validate.py::check_visual_delta`
computes the authoritative delta between snapshots and proves exact
coverage: unlisted changes, listed-but-unchanged resources, unknown or
duplicate or missing handoff ids, prose/wildcard entries, records not
bound to their inventory, and generated previews masquerading as handoff
assets are all errors.
A genuine subtlety surfaced and is now enforced rather than hidden: the
transparent 12×40 spacer glyph `g_space.png` is **byte-identical** across
both generations, so it is a manifested asset with no pixel delta. Any
such asset must be declared in `unchanged_handoff_assets` with a reason,
or validation fails.
Tests: 11 new cases in `tests/visual/test_lineage_gate.py`, covering all
six mandated fixtures (omitted id, unknown id, duplicate id, prose
wildcard "ALL 50", omitted changed resource, extra unchanged resource)
plus inventory-binding, generated-preview and declaration invariants.

**Blocker 3 — importer verifies the declared commit snapshot (FIXED).**
`tools/import_handoff.py` no longer trusts the studio working tree. For
every export it reads the Git object at `<source_commit>:<export_path>`;
Git-LFS pointers are parsed and their `oid sha256:` compared against the
handoff hash, ordinary blobs are hashed directly. Every `source_paths`
entry and each `spec_path` must exist at that same commit. Commit roles
are explicit and machine-checked: the **producing commit** (`1d51b58`)
versus the **metadata stamping commit** (`6c9afa8`, resolved with
`git log -1 -- <metadata>`), with the producing commit required to be an
ancestor of the stamping commit. The import is two-phase and fail-safe:
verify the whole set → stage to a temporary directory → re-verify staged
bytes → replace resources and manifest only then, with originals held in
memory and restored on any exception. The manifest now records both
commits.
Re-verification of the existing data found it sound: all 50 exports match
the declared commit at LFS-pointer level (the weakness was the tool's
guarantee, exactly as the review judged).
Tests: 11 new cases in `tests/engine/test_handoff_import.py` against a
synthetic studio repo — dirty working tree, dirty-tree-with-matching-
metadata (the precise pre-review hole), wrong historical commit, missing
source path, missing spec path, LFS OID mismatch, pointer-aware
verification, uncommitted metadata, and a mid-replace failure proving the
consumer tree and manifest stay byte-identical.

**Blocker 4 — glyph licensing and provenance (FIXED).** See §19: the
font was misidentified as DejaVu; it is Blender's GPL-licensed built-in
`Bfont`. Provenance record, notice, reproducible extractor, corrected
manifest entries, validator enforcement, and 7 new tests
(`TestDerivedFontProvenance`, `TestRealAureliusProvenance`) are in place,
with the commercial-use question flagged as an explicit open item.

**Blocker 1 — owner pixel acceptance (INTENTIONALLY OPEN).** Nothing was
promoted: `owner.status` remains `proposed`, `architecture_review.status`
remains `pending`, `approved_version` remains `field-tourbillon-v1`,
`proposed_version` remains set, all 50 handoff lifecycles remain
`candidate`, and `goldens/` still contains only `field-tourbillon-v1`.

### Re-verification after corrections

| Gate | Result |
|---|---|
| Engine tests | **86/86** (was 68; +11 importer, +7 provenance) |
| Visual/lineage tests | **28/28** (was 17; +11 approval-delta) |
| Release-workflow fixtures | 10/10 |
| Deterministic generation (`--check`) | OK — zero XML delta |
| Resource inventory `--check` | clean, 60 resources, unchanged `d64c3e95…` |
| Reference render vs candidates | byte-identical; bound to APPROVAL-0002 |
| All-ten build | 10/10 PASS |
| Official WFF validator | PASS (v4) |
| Memory-footprint evaluator | PASS |
| `tools/validate.py` | 0 errors |
| `git diff --check` | clean |
| **Candidate APK** | **`d734abc8…` — unchanged**, so the Phase-3 device evidence still binds exactly (only manifest metadata changed; no packaged resource byte moved) |
| Immutable Phase-1 release | `844b9c43…` unchanged |

## 23. Re-review corrections and revision r1 (2026-07-25)

ChatGPT's Phase-3 re-review (`PHASE_3_CHATGPT_REREVIEW.md`, consumer
`69709e2` / studio `58cf13c`) accepted the approval-binding, source-
snapshot, rollback and provenance work, and returned one narrow
engineering blocker plus an owner recommendation. Both are addressed.

### Metadata bytes are now bound to `metadata_commit` (FIXED)

`tools/import_handoff.py` previously resolved `metadata_commit` with
`git log -1 -- <metadata>` but parsed the **working-tree** metadata, so an
uncommitted edit to `license`, `lifecycle`, `pivot`, `dimensions`,
`consumer_component`, `regenerate`, generation identity, or the export set
could enter the manifest while still being attributed to the older
commit. The importer now reads the blob at
`<metadata_commit>:<metadata_rel>` and parses **that** as authoritative,
rejecting any working-tree divergence outright. The working tree is
consulted only to obtain LFS-smudged export payloads, and only after
their committed OIDs have been verified.

8 new tests (19 total in `tests/engine/test_handoff_import.py`): an
uncommitted edit to committed metadata is rejected; dirty licence,
lifecycle, pivot, dimensions, component and regenerate fields cannot
reach `engine/handoff.json`; a dirty removal cannot truncate the
manifest; committed metadata still imports; and committing the edit —
which necessarily moves `metadata_commit` — is accepted with the new
commit recorded. Every failure path asserts the consumer tree and
manifest stay byte-identical.

### Owner decision: approve with changes — typeface substituted (APPLIED)

The owner-selected `OliveInstrument_Restrained` design is preserved
exactly. All 39 BitmapFont glyph masters and both baked plate engravings
(`AURELIUS`, `FIELD TOURBILLON Mk II`) now derive from the audited
**Rajdhani Bold, SIL OFL-1.1** source (`691470dd…`, commercial use
permitted, already tracked in `docs/asset-licenses.json` and the legacy
Aurelius face font) instead of Blender's GPL built-in `Bfont`. The
licensing ambiguity is removed permanently, before this generation could
become an approved commercial baseline.

The substitution is measurably surgical: **4.24% of face pixels changed
at mean channel delta 0.35** between `field-tourbillon-mk2` and
`field-tourbillon-mk2-r1`, confined to glyph and engraving regions. On
the studio side only `bg`, `bg_aod` and the 39 glyph raws were
re-rendered; the 9 non-text layers are byte-identical.

### New revision, nothing overwritten

| Artefact | Value |
|---|---|
| Revision | `field-tourbillon-mk2-r1` (`proposed_version`) |
| Studio producing commit | `5c44f74` |
| Studio metadata stamping commit | `d0ef4a7` |
| Inventory snapshot | `versions/field-tourbillon-mk2-r1.json` — `35f95830…` |
| Candidate normal / AOD | `a766e444…` / `69a8724b…` |
| Approval record | `APPROVAL-0003`, superseding `APPROVAL-0002` per ADR-009 |
| Candidate APK | `57dad013…` |

`APPROVAL-0003` carries the same item-level rigour: 49 exact changed
studio resources, 50 exact handoff asset ids, `preview.png` recorded
separately as a generated consumer resource, `g_space.png` declared under
`unchanged_handoff_assets`, and **both** deltas measured — 78.99% versus
the approved v1 golden (the intended generation change) and 4.24% versus
the superseded mk2 candidate (the typeface substitution alone).

Preserved as historical proposed evidence, unmodified: the
`field-tourbillon-mk2` candidates, `APPROVAL-0002`, the mk2 inventory
snapshot, the mk2 device evidence (bound to APK `d734abc8…`), and the
complete Bfont provenance investigation — the registry record is retained
and marked `superseded_by: rajdhani-bold-ofl-1.1` with its conservative
posture intact.

### Re-verification

| Gate | Result |
|---|---|
| Engine tests | **95/95** (was 86; +8 metadata binding, +1 provenance evidence) |
| Visual/lineage tests | 28/28 |
| Release-workflow fixtures | 10/10 |
| Deterministic generation | OK — zero XML delta retained |
| Inventory `--check` | clean, 60 resources |
| Reference render | byte-identical; bound to APPROVAL-0003 (proposed) |
| All-ten build | 10/10 PASS |
| Official WFF validator | PASS (v4) |
| Memory-footprint evaluator | PASS |
| `tools/validate.py` | 0 errors |
| `git diff --check` | clean |
| Immutable Phase-1 release | `844b9c43…` unchanged |

Nothing promoted: `owner.status` proposed, `architecture_review` pending,
`approved_version` still `field-tourbillon-v1`, `proposed_version` set,
all 50 lifecycles `candidate`, `goldens/` contains only v1.

### Physical-device evidence for r1 — CAPTURED

Focused Watch7 test executed 2026-07-25 (SM-L310, Android 16/API 36),
bound to candidate APK `57dad013…`, inventory `35f95830…` and
`APPROVAL-0003`. Full per-row results:
`docs/reports/evidence/phase-3/aurelius/r1/DEVICE_TEST_RESULTS.md`.

PASS: upgrade continuity from the mk2 candidate `d734abc8…`; picker;
**Rajdhani glyphs rendering live** (date aperture shows the live day in
the substituted typeface); dynamic date path; the `AURELIUS` engraving;
normal legibility; 10 AOD cycles with a clean render afterwards;
stability (crash buffers empty); 32 s smoothness recording; touch inert.

AOD pixel capture remains **not obtainable** on this hardware (doze
returns a fully black frame) — the qualification accepted in the Phase-2
final review; the ambient composition is byte-determined by the
CI-verified r1 AOD reference `69a8724b…` and the sha-chained `bg_aod`
bytes.

Two findings are recorded rather than silently fixed, both requiring
owner sign-off because they change pixels:

1. **Date digits overhang the drawn aperture frame.** Pre-existing —
   verified present in the mk2 device capture too, so it is plate
   composition, not the typeface substitution (Rajdhani Bold is chunkier,
   so marginally more visible). The WFF text box is 60×28 at size 24
   while the frame drawn in the art is ≈36×19 inside. One-parameter
   studio fix when directed.
2. **The `FIELD TOURBILLON Mk II` engraving is largely occluded** by the
   tourbillon well ring. Also pre-existing and identical in mk2.

### Methodological finding — the device profile cannot gate this face

Device-vs-reference pixel comparison was attempted rigorously and does
not work for Aurelius: even against a reference rendered at the device's
observed state, the static bezel annulus shows mean channel delta 23.8.
Two uncontrollable inputs cause it — mechanical layers rotate at up to
40°/s so the capture instant cannot be pinned, and the fullscreen sheen
is accelerometer-parallaxed by up to ±40 px while the watch sits tilted
on its dock. The `[compare.device_profile]` thresholds are therefore
sound for a static face but cannot gate a dynamic, parallaxed one. The
effective device gate for this face is visual + behavioural + the
byte-chain (studio export → manifest sha → imported resource → inventory
→ packaged APK). Recommend recording this in ADR-009 rather than leaving
the device profile implying a capability it cannot deliver for this class
of face.

## 24. Revision r2 — composition corrections (2026-07-25)

ChatGPT's r1 review (`PHASE_3_CHATGPT_R1_REVIEW.md`, consumer `acf51db` /
studio `60ab14d`) accepted the engineering architecture outright and
withheld owner pixel approval pending one focused composition pass. Both
required visual corrections and the device-comparison clarification are
implemented as revision `field-tourbillon-mk2-r2`.

### Correction 1 — date aperture now contains every day 1..31

r1's opening was authored by eye at 31.3 × 14.5 px while the live
presentation inks up to 33.0 × 24 px (`z30_date` is a 60×28 px box at
BitmapFont size 24; widest day "30" = cells 27+28 at scale 24/40). The
r2 opening is **40.2 × 30.1 px**, derived from those metrics plus the
mandated 2 px clear margin. The date centre and WFF data behaviour are
unchanged, so the **XML/spec delta stays zero**.

Containment is proved over the full value domain rather than sampled:

| | |
|---|---|
| Tool | `tools/date_aperture_proof.py` |
| Renders checked | **62** (days 1..31 × normal/AOD) |
| Required clear margin | 2.0 px |
| **Worst margin observed** | **3.07 px** |
| Violations | 0 |
| Proof sheet | `visual/proofs/date_aperture_r2.png` (days 1, 8, 11, 22, 28, 31 in both treatments, inner-aperture guide overlaid) |
| Bounds data | `visual/proofs/date_aperture_r2.json` |
| Test | `tests/visual/test_date_aperture.py` — 9 cases |

The test suite includes deliberate-failure fixtures: it reproduces the r1
geometry and asserts every sampled day breaches the margin, and it
simulates a 25% wider typeface to prove the check is sensitive to ink
growth. Two things the tests themselves caught during development are
fixed rather than papered over — a redundant second declaration of the
aperture bounds (now derived from centre + size, single source of truth),
and single-digit centring, which is bounded by a documented
`max_center_offset_px` tolerance because the reference renderer places
integer glyph cells (worst case 1.5 px on the narrow "1") while the WFF
runtime performs its own layout.

### Correction 2 — occluded lower engraving removed

`FIELD TOURBILLON Mk II` is deleted from the plate artwork. Not
repositioned, not replaced with a badge, curved label, stencil or slogan.
The restrained `AURELIUS` signature is the only face marking; the full
model name remains in package metadata, picker text, documentation and
release copy.

### Device-comparison architecture clarified

ADR-009 gains §6a and §6b, and the face contract gains a machine-readable
mode:

- deterministic reference-to-committed-reference comparison remains
  **exact and mandatory**;
- a device screenshot is a quantitative hard gate **only** when every
  material motion phase and sensor input can be controlled or safely
  masked (without breaching the mask-coverage policy);
- Aurelius declares `device_validation.mode = "qualitative-behavioral-
  lineage"` with its reason and required evidence, because 40°/s gears
  and ±40 px accelerometer sheen parallax make capture-time state
  uncontrollable;
- `tools/compare_visuals.py --mode device` now reports metrics and
  **refuses to emit a verdict** for such a face, so static-face
  thresholds can never appear to gate a face they cannot;
- the generic `[compare.device_profile]` is preserved for faces where it
  genuinely applies.

ADR-009 §6b additionally requires live-presentation containment to be
proved over the full value domain wherever plate art frames runtime
content — the general rule behind correction 1.

### Revision artefacts (nothing overwritten)

| Artefact | Value |
|---|---|
| Revision | `field-tourbillon-mk2-r2` (`proposed_version`) |
| Studio producing commit | `c8c29dc` |
| Studio metadata stamping commit | `5cf8f04` |
| Studio export delta | exactly `bg.png` + `bg_aod.png` |
| Inventory snapshot | `versions/field-tourbillon-mk2-r2.json` — `b76f9ceb…` |
| Candidate normal / AOD | `7fd2cf63…` / `2f2be0e9…` |
| Approval record | `APPROVAL-0004`, superseding `APPROVAL-0003` |
| Candidate APK | `5a1271ab…` |

Preserved untouched: mk2 and r1 candidates, `APPROVAL-0002` and
`APPROVAL-0003`, both earlier inventory snapshots, the mk2 and r1 device
evidence, the complete Bfont investigation, and the immutable release.

Measured deltas: **78.99%** changed pixels versus the approved v1 golden
(the intended generation change) and **31.40% at mean channel delta 2.42**
versus r1 — the low mean confirming the change is confined to the
aperture and the removed engraving, consistent with a studio export delta
of just the two plates.

### Re-verification

| Gate | Result |
|---|---|
| Engine tests | 95/95 |
| Visual/lineage tests | **37/37** (was 28; +9 aperture) |
| Date-aperture proof | 62 renders, 0 violations, worst margin 3.07 px |
| Release-workflow fixtures | 10/10 |
| Deterministic generation | OK — zero XML delta |
| Inventory `--check` | clean, 60 resources |
| Reference render | byte-identical; bound to APPROVAL-0004 |
| All-ten build | 10/10 PASS |
| Official WFF validator | PASS (v4) |
| Memory-footprint evaluator | PASS |
| `tools/validate.py` | 0 errors |
| `git diff --check` | clean |
| Immutable Phase-1 release | `844b9c43…` unchanged |

Nothing promoted: `owner.status` proposed, `architecture_review` pending,
`approved_version` still `field-tourbillon-v1`, `proposed_version` set to
r2, all 50 lifecycles `candidate`, `goldens/` contains only v1.
