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

All Mk II assets are original parametric/procedural studio work
(AGENOR-Horology, Phase 3); no third-party textures/HDRIs, no
AI-generated donors. Glyph and engraving masters use Blender's bundled
font (DejaVu-derived, license-compatible; recorded in the studio report
§14). No change to the existing font/HDRI audit.

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
