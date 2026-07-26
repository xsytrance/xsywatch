# Phase 4 — Aurelius commercial release readiness

**Status:** **Checkpoint B implementation complete — acceptance blocked** (Checkpoint A record retained below)
**Repository:** `xsytrance/xsywatch`
**Branch:** `phase-4/aurelius-release-readiness`
**Branch point:** `3333d427e9c87f1c59b26d61c41f6b9ce6435152` (main)
**Paired studio branch:** `AGENOR-Horology@phase-4/aurelius-craftsmanship-release-assets` from `3f12eda7c3c98c942d4a297eab7a721864aedf4d`
**Governing decisions:** ADR-008, ADR-009, ADR-010
**Date:** 2026-07-26

Checkpoint A covers baseline verification, validator hardening, the wear
packet, the policy audit, and the studio proposals. **No production
refinement has begun.** Neither branch is merged.

---

## 1. Scope discipline — what was deliberately not done

Per the phase scope, none of the following happened:

- ❌ no `versionCode` / `versionName` change — still 1 / `1.0`;
- ❌ no `2.0.0-rc1` artifacts, no `releases/aurelius/candidates/` directory;
- ❌ no production signing material of any kind;
- ❌ no modification to `releases/aurelius/current/`;
- ❌ nothing published;
- ❌ no new visual golden promoted; `approved_version` is still
  `field-tourbillon-mk2-r2`;
- ❌ no craftsmanship import, no handoff stamp, no proposal pixel in this
  repository;
- ❌ no other watchface started;
- ❌ neither branch merged.

---

## 2. Verified baseline

Full detail: **`docs/reports/PHASE_4_BASELINE.md`**.

| Check | Result |
|---|---|
| `xsywatch` main head | `3333d427e9c87f1c59b26d61c41f6b9ce6435152` ✅ |
| required commits `3e0616aa…`, `3333d427…` | present |
| `AGENOR-Horology` main head | `3f12eda7c3c98c942d4a297eab7a721864aedf4d` ✅ |
| required commit `3f12eda7…` | present |
| both trees clean, both `main` == `origin/main` | ✅ |
| Phase 3 fully merged | ✅ `74ddde7` / `cd67186` |
| approved visual version | `field-tourbillon-mk2-r2` ✅ |
| pre-existing Phase-4 implementation | none |

### Reproduction

| Artifact | SHA-256 | Result |
|---|---|---|
| normal golden | `7fd2cf63607e2aa6ef53d0443c44e16885284705d5f4336602aa3ce2526a556e` | ✅ byte-identical |
| AOD golden | `2f2be0e91b7473b5bb492cdc55094777d570a268f36e751d109be56888f1e936` | ✅ byte-identical |
| rebuilt Phase-3 APK | `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a` | ✅ **exact**, 3,600,717 B |
| inventory snapshot r2 | `b76f9ceb01b555a4915448bb8408e8d008937c484913b033491f5c9e3875c269` | ✅ |

The APK rebuilding byte-for-byte means the scope's conditional ("where the
established toolchain permits exact reproduction") is **satisfied, not
waived**. Any later Phase-4 difference is therefore attributable to a
deliberate change rather than environment drift.

---

## 3. Complete gate results

| Gate | Result |
|---|---|
| engine tests | **95 passed** |
| visual + lineage tests | **38 → 50 passed** (+12 from §4) |
| engine generation drift | committed XML matches deterministic generation |
| resource inventory | clean, 60 resources |
| reference render vs goldens | byte-identical |
| renderer determinism selftest | PASS |
| date-aperture proof | **62 renders, 0 violations**, worst margin 3.07 px vs 2.0 px contract |
| handoff / import tests | included in the engine suite, PASS |
| release fixtures | **10/10** |
| deterministic generation | PASS |
| inventory checks | PASS |
| all-ten Gradle builds | **10/10 PASS** |
| official WFF validator | ✅ **PASSED** against WFF v4 |
| memory evaluator (rebuilt candidate) | ✅ **PASS** (10 MB ambient / 100 MB active) |
| memory evaluator (immutable release) | ✅ **PASS** |
| `tools/validate.py` | **0 errors, 13 warnings** (all pre-existing, documented) |
| `git diff --check` | clean, verified per-commit |
| CI | ✅ **green** — run `30216783275`, passed in 29 s at head `b4dd574` |

Toolchain: JDK 21.0.11, Gradle 9.6.1, SDK/build-tools 36, Python 3.14.4,
Pillow 12.1.1 (matches the `states.toml` pin), Blender 4.5.11, WFF
validator (google/watchface), memory-footprint 1.7.0.

---

## 4. Validator hardening — implemented

Implements both prospective governance items from
`docs/reports/PHASE_3_POST_MERGE_REVIEW.md` § "Non-blocking future
hardening". Commit `454c557`.

### What changed

1. **Dual approval.** A committed golden set is authorized only by a record
   with `owner.status == "approved"` **and**
   `architecture_review.status == "approved"`. Previously one
   owner-approved record sufficed, so a generation could reach `goldens/`
   with its architecture gate still open. Every committed golden directory
   is checked — active and superseded alike.

2. **Exactly one authoritative record per `visual_version`.** The previous
   code selected `records[-1]` from the matching approved records, so two
   approved records for one generation would validate silently against
   whichever sorted last. Duplicates are now reported as **ambiguity**, and
   the golden-hash comparison is **skipped** rather than run against an
   arbitrarily chosen record.

3. `architecture_review.status` now receives the same schema check
   `owner.status` already had (`pending|approved|rejected`, object-typed).

Half-approved records remain legal on their own as work-in-progress; they
are rejected only *as golden authorization*. Proposed and rejected records
stay committed as historical evidence per ADR-009 §5.

### Deliberate-failure tests — 12 new, all passing

`tests/visual/test_lineage_gate.py::GoldenAuthorizationTests`

| Case | Test |
|---|---|
| owner-approved, architecture-pending | `test_owner_approved_architecture_pending_rejected` |
| owner-approved, architecture-rejected | `test_owner_approved_architecture_rejected_is_rejected` |
| architecture-approved, owner-proposed | `test_architecture_approved_owner_proposed_rejected` |
| architecture-approved, owner-rejected | `test_architecture_approved_owner_rejected_is_rejected` |
| neither gate closed | `test_no_approved_record_at_all_rejected` |
| duplicate approved records (active generation) | `test_duplicate_approved_records_rejected` |
| duplicate approved records (superseded generation) | `test_duplicate_approved_record_for_superseded_version_rejected` |
| ambiguity not silently resolved | `test_ambiguous_duplicate_is_not_silently_resolved` |
| unknown `architecture_review.status` | `test_unknown_architecture_status_rejected` |
| `architecture_review` not an object | `test_architecture_review_must_be_an_object` |
| **positive control** — records unique and fully approved | `test_committed_records_are_unique_and_fully_approved` |
| **positive control** — proposed records survive as history | `test_proposed_records_are_preserved_as_history` |

The ambiguity test is the sharp one: it writes a duplicate approved record
carrying *different* golden hashes and asserts that validation reports the
ambiguity **and does not** emit "does not match approved record" — i.e. it
proves the validator refuses to compare against a guess.

### APPROVAL-0001 and APPROVAL-0004 confirmed

| Record | Version | Owner | Architecture | Unique |
|---|---|---|---|---|
| APPROVAL-0001 | `field-tourbillon-v1` | approved | approved | ✅ sole record |
| APPROVAL-0002 | `field-tourbillon-mk2` | proposed | pending | history |
| APPROVAL-0003 | `field-tourbillon-mk2-r1` | proposed | pending | history |
| APPROVAL-0004 | `field-tourbillon-mk2-r2` | approved | approved | ✅ sole record |

Both remain valid, unique and fully approved under the hardened rules. As
the post-merge review anticipated, this corrected no existing defect — it
made an invariant explicit.

### Confirmed non-impact

`git show --stat 454c557` touches exactly three files: `tools/validate.py`,
`tests/visual/test_lineage_gate.py`,
`watchfaces/aurelius/visual/approvals/README.md`. **No golden image, runtime
resource, inventory, APK or release artifact is modified.** Post-commit
re-verification: goldens still reproduce byte-identically, `validate.py`
still 0 errors, the immutable release still `844b9c43…`.

---

## 5. Owner wear-test packet

**Path:** `docs/reports/evidence/phase-4/aurelius/wear/`
**Status:** created, **empty of observations by design**

| File | Purpose |
|---|---|
| `README.md` | how AGENOR records a session |
| `BASELINE.md` | objective Phase-3 facts only |
| `WEAR_LOG.md` | generated roll-up — do not hand-edit |
| `sessions/` | one JSON per session, written by the tool |

### Workflow for AGENOR

```bash
python3 tools/wear_log.py            # guided, one question at a time
python3 tools/wear_log.py --show     # sessions recorded so far
python3 tools/wear_log.py --validate # schema + artifact-binding check
```

The tool asks each field in turn and writes the evidence file. **Pressing
Enter skips a question** and records `null`. AGENOR never opens a JSON file
or edits `WEAR_LOG.md`.

Captured fields cover every item the scope requires: date; approximate
duration; office/home/outdoor/transit/exercise/low-light context; normal
readability; AOD readability; date and reserve-gauge usability; motion
smoothness; whether animation becomes distracting; parallax impression;
picker and activation; charging and sleep/wake; battery start/end with
explicit caveats; stale or missing data; accidental interaction; glare,
clipping, contrast and hierarchy findings; whether it still feels premium
after repeated use; and disposition keep/investigate/change.

### No invented observations

Every subjective field is empty and stays empty until AGENOR records a
session. `BASELINE.md` contains only objective, sourced Phase-3 facts —
motion rates, the aperture proof result, the HR fallback, device
qualifications — and states the open questions **as questions**. A blank
field is honest evidence; a guessed one is not.

### Artifact binding

Each session records the exact APK it was observed on
(`5a1271ab…`, `com.xsytrance.aurelius` 1.0, Watch7 SM-L310).
`--validate` **fails** a session whose hash does not match, so an
observation cannot drift from the build it describes. At Checkpoint B the
binding is repointed at the release candidate.

Battery figures are labelled experiential in the generated log and must not
become efficiency claims (ADR-010 §9).

---

## 6. Official distribution-policy audit

Full detail: **`docs/reports/PHASE_4_POLICY_AUDIT.md`**. Primary sources
only, checked 2026-07-26. Internet was available, so the audit was
performed rather than marked BLOCKED.

### Already compliant

| Finding | Detail |
|---|---|
| FMT-1 | WFF mandatory for installing watch faces on all Wear OS devices since January 2026 — Aurelius is WFF v4 |
| SDK-1 | Wear OS apps must target API 35+; Aurelius targets 36 |
| MEM-1 | WO-P8 budget 10 MB ambient / 100 MB interactive — already gated and PASSing |
| CPLx-1 | WO-P10 ≤8 complication slots — Aurelius has none |
| SRC-1 | WO-G11 XML source ≤10 MB — far inside |
| PKG-2 | 200 MB bundle limit — current APK 3.6 MB |

### Blockers

| # | Finding | Detail |
|---|---|---|
| 1 | **TEST-1** | New personal developer accounts need **12 testers opted in for 14 consecutive days** before production access can be requested. **Whether this applies is the largest schedule unknown and only AGENOR can answer it.** |
| 2 | **AOD-1** | WO-P7 measures **average luminance across the face** at ~10-min intervals across a day, limit 15%. The studio measures **count of pixels above 15/255 on one frame**. Different quantities. Our ~7% is probably fine — that is an expectation, not a measurement. |
| 3 | **PKG-1** | Play requires a Wear OS **`.aab`** for watch faces. Only debug APKs exist. |
| 4 | **SIGN-1** | Play App Signing needs a developer-held **RSA 2048+ upload key**. None exists — correctly, per ADR-010 §5. |
| 5 | **FMT-2** | WFF v4 requires Wear OS 6 / API 36, but `minSdk = 34`. The package is installable on devices that cannot render it. Deferred: it is package metadata. |

### Constraints on the commercial packet

- **MEDIA-2 / WO-G6** — listing screenshots must be 1:1, ≥384×384, **no
  device frames or non-interface backgrounds**. The planned on-wrist image
  therefore **cannot be a Play screenshot**; it is other promotional media
  only.
- **MEDIA-1 / WO-G4** — the listing icon must be a centred face **scaled to
  the asset edges**. The current icon reuses the preview render, which
  keeps the black canvas corners around the octagonal case. A dedicated
  asset is needed.
- **PRIV-1** — the Data safety form is required **even for a no-collection
  app**, and a **privacy policy URL is required regardless**. Aurelius
  reads `[HEART_RATE]` on-device with no network permission and no WFF
  network capability, which is a strong checkable argument for "no data
  collected" — but it is a legal declaration and must be verified against
  the final bundle, not assumed.

### Not verified — recorded as gaps, not guesses

Icon dimensions/format · feature graphic and video specs · whether
`BODY_SENSORS` triggers extra declarations (and whether the permission is
needed at all for a WFF face) · merchant prerequisites · package/update
continuity as a cited policy · region and device availability ·
device-verification detail.

---

## 7. Packaging and signing observations

| Item | Current state |
|---|---|
| package | `com.xsytrance.aurelius` — unchanged, and to be kept (ADR-010 §3) |
| versionCode / versionName | `1` / `1.0` — **unchanged, deliberately** |
| minSdk / targetSdk / compileSdk | 34 / 36 / 36 |
| WFF version | 4 |
| declared permissions | `BODY_SENSORS`, `ACTIVITY_RECOGNITION` |
| build output | `assembleDebug` APK only — **no bundle target exists** |
| signing | debug only; no `signingConfig`, no keystore anywhere in the tree |
| release channels | 7 × `current/`, no versioned candidate directories |
| secrets | none — verified; `validate.py` enforces |

Reproducibility is a genuine asset here: the debug APK rebuilds
byte-for-byte, which gives Workstream 5 a proven baseline before the
`.aab` path is added.

---

## 8. Studio proposals — summary

Full detail: `AGENOR-Horology@docs/reports/PHASE_4_AURELIUS_CRAFTSMANSHIP_RELEASE_ASSETS.md`
and `watchfaces/AureliusMk2/craftsmanship/PROPOSALS.md`.

All three are rendered by importing the **approved r2 builder** with the
owner-selected palette S, so geometry, camera, layout, aperture,
typography, signature, canonical state and every pivot are identical **by
construction**.

- **A — Command Satin.** Darkest and most restrained. Bridges darker *and*
  glossier (`1A1C1E`→`15171A`, roughness 0.20–0.30 → 0.14–0.22); dial
  charcoal deepened with a *refined* rather than stronger bead grain;
  tighter screw, jewel, arbor and gear-tooth finishing. No patterning.
- **B — Atelier Stripe.** A plus one Geneva region on `BridgeUpper` alone —
  2.2 mm period, expressed as a roughness ripple on an unchanged black base
  so it reads as machining, not a lighter panel.
- **C — Precision Instrument.** No stripes. Four separated machining tiers
  from coarse bead blast to polished fasteners, plus crisper reserve ticks
  at unchanged size and position.

**Predicted export delta for all three:** zero XML/spec change; plates and
mechanical layers change; the 39 Rajdhani glyphs stay byte-identical.
Resource count stays 60; no new layer, no new animation, no added runtime
cost. **Predictions only** until a direction is selected.

**Measured AOD (studio count metric, ≤10% house rule):** base 7.133%,
A 7.198%, B 7.198%, C 7.253%. B equals A because the striped bridge is not
lit in ambient — the stripe is **invisible in AOD**. See AOD-1: this is not
the official metric.

---

## 9. Confirmation — approved pixels and release artifacts untouched

| Check | Result |
|---|---|
| `releases/aurelius/current/aurelius.apk` | `844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2` ✅ unchanged |
| size | 3,664,664 B ✅ |
| `.immutable`, `RELEASE.md`, `preview.png` | unmodified |
| approved goldens r2 | reproduce byte-identically after every commit |
| superseded goldens v1 | unmodified, still bound to APPROVAL-0001 |
| candidates mk2 / r1 / r2 | unmodified |
| all four approval records | unmodified except none — no record edited |
| resource inventory | unchanged, 60 resources, `b76f9ceb…` |
| runtime resources | unchanged — no drawable, no XML, no manifest edited |
| package/version metadata | unchanged |
| Phase 1–3 evidence | fully present |

Files added or changed on this branch are confined to: `tools/validate.py`,
`tools/wear_log.py`, `tests/visual/test_lineage_gate.py`,
`watchfaces/aurelius/visual/approvals/README.md` (documentation only), and
new documents under `docs/reports/`.

---

## 10. Exact consumer commits

| Commit | Subject |
|---|---|
| `454c557` | phase-4: require dual approval and a unique authoritative record per golden |
| `4325898` | phase-4: baseline verification report and owner wear-test packet |
| `6c82009` | phase-4: current official distribution-policy audit |
| *(this commit)* | phase-4: consumer Checkpoint A report |

Branch `phase-4/aurelius-release-readiness`, from `3333d427…`. **Not
merged.** No squash, no rebase, no force-push.

Studio commits: `680db48` (proposals), `87f6f7b` (studio report), on
`phase-4/aurelius-craftsmanship-release-assets` from `3f12eda7…`. **Not
merged.**

---

## 11. Recommendation to AGENOR

**A — Command Satin, with C's reserve-tick treatment grafted on.**

A is the approved identity rendered: it targets the one real weakness (the
slightly flat bridges) by going darker and glossier, at zero runtime cost,
without adding ornament. C's reserve ticks are a separable usability gain
on the one data element that is currently hard to read at a glance, and the
scope explicitly permits a combination. C in full overshoots — its coarse
tier-1 blast lightens the dial's diffuse response and moves away from the
restraint chosen in Phase 3. B is the highest risk for the least return:
invisible in AOD, plausible shimmer at ~5 px per band under the parallaxed
sheen, and a dress-watch cue on a face whose stated identity is field
instrument first.

**Constraints that materially affect the selection:**

1. **The wear log is empty.** Selecting now is selecting on renders alone.
   If wearing the watch shows the face is too dark, or the reserve gauge
   unreadable, C rises sharply. Consider recording one or two sessions
   first — the wear packet is ready and the studio work is non-destructive.
2. **AOD-1** — the official AOD metric is uncomputed. Unlikely to change
   the ranking at ~7%, but it is unmeasured.
3. **The differences are subtle at 480 px** and are properly judged on the
   physical panel, not a monitor. The crops are where they show.
4. **The policy blockers are schedule, not design.** The craftsmanship
   decision is not on the critical path to launch; TEST-1 and PKG-1 are.

---

## 12. Files AGENOR should inspect

**Decide the craftsmanship direction:**

```
AGENOR-Horology/watchfaces/AureliusMk2/craftsmanship/
  COMPARISON_normal.png      all four side by side
  COMPARISON_bridge.png      where A vs B differ most
  COMPARISON_cage.png        jewel cups, cage rim, tooth roots
  COMPARISON_reserve.png     C's tick treatment — the grafted element
  COMPARISON_date_gear.png   aperture frame and gear teeth
  COMPARISON_aod.png         ambient, all four
  PROPOSALS.md               per-surface values and per-direction risks
```

**Answer the blocking question:**

```
xsywatch/docs/reports/PHASE_4_POLICY_AUDIT.md   § TEST-1
```

— what type is the AGENOR developer account, when was it created, and does
it already have production access?

**Record wear evidence:**

```
xsywatch/docs/reports/evidence/phase-4/aurelius/wear/README.md
python3 tools/wear_log.py
```

---

## 13. Qualifications

1. **CI is green** on the consumer branch — run
   [`30216783275`](https://github.com/xsytrance/xsywatch/actions/runs/30216783275),
   29 s, at head `b4dd574`. CI deliberately does **not** build APKs, run
   the WFF validator or run the memory evaluator (runner cost, documented
   in the workflow header); those three were run locally and are recorded
   in §3. `AGENOR-Horology` has no CI workflow.
2. **No device evidence** in Checkpoint A — no Watch7 was attached.
   Physical validation belongs to Checkpoint B.
3. **Exact APK reproduction is demonstrated on one machine.** The two
   clean builds from a documented environment required by scope §11.8
   belong to Checkpoint B.
4. **The WFF validator and memory evaluator are unlicensed third-party
   binaries** built locally from `google/watchface`; they are not vendored
   and must be present at `~/Applications/wff-validator/`.
5. **Nothing derived is committed** — see `PHASE_4_BASELINE.md` §0. The APK
   hashed throughout this report must be rebuilt with `tools/build_all.sh`.
6. **The studio proposals render the concept assembly, not runtime layer
   exports.** They show the finishing; they do not prove the downsampled
   WFF composite. That proof exists only after a production export.

---

## 14. Stop point

Checkpoint A is complete. Per the phase scope, **production refinement does
not continue until AGENOR explicitly selects a craftsmanship direction.**
Both branches are returned unmerged for owner and ChatGPT review.

---

# Checkpoint B — release candidate

**Status:** **implementation complete — ACCEPTANCE BLOCKED** (returned unmerged)
**Date:** 2026-07-26
**Candidate:** `com.xsytrance.aurelius` 2.0.0-rc1 (versionCode 2)
**Visual version:** `field-tourbillon-mk2-rc1` — **proposed, NOT promoted**

## B0. Boundaries held

- ❌ rc1 **not** approved and **not** promoted to goldens — `field-tourbillon-mk2-r2` remains the active approved golden;
- ❌ neither branch merged;
- ❌ nothing published, no public listing;
- ❌ `releases/aurelius/current/` untouched — still `844b9c43…`;
- ❌ no production signing material created;
- ❌ no other watchface begun.

## B1. Studio commits and handoff

| | |
|---|---|
| Studio generation | `CommandSatin_ReservePrecision` |
| Owner selection | `d86d94c` |
| **Producing commit** | `04015886dbee5cd17b66c4627f822aef3db73d16` |
| **Metadata commit** | `97ba0f1ceeee721a7a2ec0521603bd61935d036d` |
| Import | 50 exports verified against the producing-commit snapshot, LFS-aware |
| Lifecycles | all `candidate` |

## B2. Changed and unchanged assets — measured, not predicted

**6 changed, 44 byte-identical**, measured from the finish's own object
ledger (`AGENOR@exports/aurelius_rc1/IMPACT.json`, `DELTA.json`).

| | |
|---|---|
| Changed runtime resources | `bg.png`, `bg_aod.png`, `cage.png`, `gear_l.png`, `gear_r.png`, `hub.png` |
| Generated consumer resource | `preview.png` — re-derived from the rc1 normal render |
| Unchanged manifested assets | 44 of 50, each byte-identical to r2 |
| Resource count | 60, unchanged |
| **XML/spec delta** | **zero** — rc1 `xml_sha256` equals r2's exactly |

**The Checkpoint A prediction was wrong about `balance.png`.** It does not
change: the balance wheel and spokes use `MAT_Gold_Warm` and appear in no
group the finish touches. Explained in the studio report §B3.

## B3. Proposed rc1 hashes

| | |
|---|---|
| rc1 normal | `23e1d8e83f642d751ec3ad0c7cf1037faf8359b87ed31288a359a09d81c1d790` |
| rc1 AOD | `3e340f4379e1ca8462071761c8c46b8e0e292a7614ac9a2ccde7454a6af934aa` |
| rc1 inventory | `1ec66797d1f4fdbf123e68240662ec256f056e8429941871e89cf675310359ce` |
| r2 normal (unchanged) | `7fd2cf63607e2aa6ef53d0443c44e16885284705d5f4336602aa3ce2526a556e` |
| r2 AOD (unchanged) | `2f2be0e91b7473b5bb492cdc55094777d570a268f36e751d109be56888f1e936` |

vs r2 — normal 65.17% of pixels at mean channel delta **6.41** (max 208);
AOD 6.29% at mean **0.13** (max 80). A restrained shift in how surfaces
catch light, not a redesign: r2-vs-v1 was mean 68.3.

APPROVAL-0005 supersedes APPROVAL-0004 **without modifying it**, and binds
previous goldens, proposed hashes, inventory snapshot, the 6 changed
resources, all 50 handoff ids, all 44 unchanged assets with per-asset
reasons, both studio commits, metrics, diff/heat-map/close-up paths, and
the wear, device and AOD-luminance evidence paths.
`owner: proposed`, `architecture_review: pending`.

## B4. Candidate artifacts

| Artifact | SHA-256 | Size | Signing |
|---|---|---|---|
| `aurelius-2.0.0-rc1.aab` | `ff61ca19e9c084089306ec95b0dc372d779a0ad00c482b3f6d6b3414d2c6bcf7` | 748,370 B | **unsigned** — no upload key exists |
| `aurelius-2.0.0-rc1-debug.apk` | `d02bf91494f94abb5176685baea19b6e788dbd5c92d0df50c4bfde14d00c7956` | 831,637 B | debug (Android Debug cert) |

`releases/aurelius/candidates/2.0.0-rc1/` with `CANDIDATE.json`,
`VERIFY.json`, `README.md`. Publication status **not published**.

**Reproducibility: both artifacts are BYTE-IDENTICAL across two
independent clean builds.** No non-deterministic field needed explaining.

### Package size fell 77%

3,600,717 → 831,637 bytes. AGP was packaging the Kotlin runtime — 2.4 MB
of `classes.dex` in a face declaring `hasCode="false"` with no code. This
was also a hard blocker: Play rejects a WFF bundle containing dex. A
further 3 KB R-class dex, which AGP emits unconditionally and which no
supported flag suppresses, is stripped before bundling; with
`hasCode="false"` the platform never loads a class loader for the package,
so it is inert.

## B5. WO-P7 — official AOD gate

| | |
|---|---|
| Metric | average luminance across the face disc; strictest of three readings |
| Sampling | 144 samples at 10-minute intervals across a whole day |
| Sensitivity | 14 runs varying date, battery and heart rate |
| Worst time sample | 00:50 — 3.952% |
| **Maximum overall** | **3.972%** |
| Limit | 15% |
| **Verdict** | **PASS** |

Evidence: `docs/reports/evidence/phase-4/aurelius/aod/`. The old ~7%
lit-pixel figure was a different quantity and is no longer used as
compliance anywhere.

## B6. Complete verification

| Gate | Result |
|---|---|
| engine tests | **97 passed** (95 → 97) |
| visual + lineage tests | **67 passed** (50 → 67) |
| date-aperture proof | **62 renders, 0 violations**, worst margin 3.07 px |
| validator-governance tests | 12, pass |
| WO-P7 tests | 17, pass |
| handoff / import tests | pass |
| release fixtures | 10/10 |
| deterministic generation | pass |
| resource inventory | clean, 60 resources |
| reference render vs proposed candidate | byte-identical, bound to APPROVAL-0005 |
| all-ten Gradle builds | **10/10 PASS** |
| APK build | ✅ |
| AAB build | ✅ |
| package metadata inspection | ✅ consistent across face.toml, Gradle, manifest, XML, .aab, .apk |
| official WFF validator | ✅ **PASS (v4)** on the XML extracted from the APK |
| memory evaluator | ✅ **PASS** |
| `tools/validate.py` | **0 errors, 13 warnings** |
| `git diff --check` | clean, per commit |
| studio guards | 10 pass across both interpreters |
| CI | see §B10 |

## B7. Signing

No production signing material exists. `docs/reports/PHASE_4_SIGNING_PLAN.md`
covers ownership, creation, storage, verified-by-restore backup, access
control, rotation, the release ceremony, and what may never be committed.
The bundle builds and verifies **unsigned**, so the packaging path is
proven without touching key material.

## B8. Commercial packet

`docs/commercial/aurelius/2.0.0-rc1/` — media derived from committed bytes,
Play assets separated from promotional ones (WO-G6 forbids device frames
in screenshots), 8-second motion render, full draft copy with data-safety
and privacy drafts. Every forbidden claim is enumerated and avoided.

## B9. Blocked — must close before Checkpoint B approval

1. **Wear evidence: ZERO sessions recorded.** The review requires one
   sustained workday, one outdoor/daylight plus low-light, and one with
   sustained AOD and a charging transition. These cannot be invented.
   `python3 tools/wear_log.py`, bound to APK `d02bf914…`.
2. **Physical Watch7 validation: BLOCKED.** `adb` reported zero devices
   all session. Full status and closing procedure:
   `docs/reports/evidence/phase-4/aurelius/rc1/DEVICE_EVIDENCE_BLOCKER.md`.
   The byte-lineage half of the policy is complete without a device;
   the on-panel half is not.
3. **TEST-1 unresolved** — `docs/reports/PHASE_4_TEST1_READINESS.md`.
4. **Privacy policy URL** — owner must host one.
5. **Price decision** and the AI-artwork licence position.

## B10. Consumer commits

| Commit | Subject |
|---|---|
| `454c557` | validator dual-approval hardening |
| `4325898` | baseline report and wear packet |
| `6c82009` | policy audit |
| `b4dd574` | Checkpoint A report |
| `51ef862` | CI status |
| `94f6f79` | rc1 import and proposed generation |
| `399ba12` | WO-P7 gate |
| `ba4d260` | Play package path, AAB, candidate |
| `5d64d52` | commercial packet, copy, signing plan |
| `2bc1d57` | TEST-1 readiness, device blocker, identity guards |
| *(this)* | Checkpoint B report |

## B11. Files to inspect

**Pixels:** `watchfaces/aurelius/visual/candidates/field-tourbillon-mk2-rc1/`
— `normal.png`, `aod.png`, `closeups/normal_reserve.png` (the graft),
`closeups/normal_bridge.png`, `diff/normal/diff_heatmap.png`.

**Governance:** `APPROVAL-0005-field-tourbillon-mk2-rc1.json`,
`releases/aurelius/candidates/2.0.0-rc1/CANDIDATE.json`.

**Decisions needed:** `PHASE_4_TEST1_READINESS.md`,
`docs/commercial/aurelius/2.0.0-rc1/COPY_DRAFT.md` (price, privacy URL,
support address).

---

# Checkpoint B round 2 — rc2, answering CHANGES REQUESTED

**Status:** **Checkpoint B implementation complete — acceptance blocked**
**Date:** 2026-07-26
**Candidate:** `com.xsytrance.aurelius` **2.0.0-rc2** (versionCode 3)
**Visual version:** `field-tourbillon-mk2-rc1` — unchanged, APPROVAL-0005 still proposed

Answers `docs/reports/PHASE_4_CHECKPOINT_B_CHATGPT_REVIEW.md`. rc1 is
preserved unmodified as an unapproved historical candidate.

## Why rc2 exists, and why the pixels did not change

Three required corrections change package bytes, so they could not be
applied to rc1 without invalidating its recorded hashes. **No runtime
visual resource differs between rc1 and rc2**, so the visual generation
and APPROVAL-0005 carry forward. No visual generation was manufactured for
a package-metadata change.

## Commit roles

| Role | Commit |
|---|---|
| `consumer_source_commit` | `a328669e487c6773b6c359d6b7ae4a5d1d5d4b49` |
| `consumer_artifact_commit` | `ea2b0e58354825890d0cf0e1ceebfdd0650b9e1b` |
| `candidate_metadata_commit` | `caa7ef4e6cbbbcfbff0c17f8f7b5ce78e32149cf` |
| studio producing | `04015886dbee5cd17b66c4627f822aef3db73d16` |
| studio metadata | `97ba0f1ceeee721a7a2ec0521603bd61935d036d` |

## rc2 artifacts

| Artifact | SHA-256 | Size | Signing |
|---|---|---|---|
| `aurelius-2.0.0-rc2.aab` | `1a2ae1386a5bacc70e2316c6562d50a9ec083b35b3038ecf5e564526f18a3b23` | 748,287 B | unsigned |
| `aurelius-2.0.0-rc2-debug.apk` | `939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc` | 831,529 B | debug |

**Both rebuilt twice from clean detached worktrees at the source commit,
byte-identical to each other and equal to the committed artifacts.**

## Blocker 1 — device and wear evidence: still BLOCKED

Headline changed as required. `adb` reported zero devices throughout, and
zero wear sessions exist. Neither can be invented.
`docs/reports/evidence/phase-4/aurelius/rc2/DEVICE_EVIDENCE_BLOCKER.md`.

## Blocker 2 — consumer lineage: CLOSED

The single `consumer_commit` is gone, replaced by three machine-checked
roles. Ancestry alone would not have caught rc1's defect — `399ba12`
genuinely *is* an ancestor. What catches it is requiring the source commit
to contain every build input, to declare the candidate's own versionName,
and to **rebuild to the canonical bytes**. 12 deliberate-failure tests,
including a stale source commit shaped exactly like rc1's.

## Blocker 3 — dex removal: now FAIL-CLOSED

`tools/dex_guard.py` enumerates every release dex, records sha256 and
size, parses every class descriptor it defines, and deletes only when the
whole set is inside the generated-R allowlist. A self-contained DEX parser
means the gate cannot be skipped by a missing SDK; `dexdump` runs as an
independent cross-check and disagreement is itself a failure. An
unparseable dex is never deleted.

Recorded for rc2: 1 dex, 3,076 B, six R classes, allowlist satisfied.
AAB contains no dex; the debug APK retains it, and that policy is stated
explicitly rather than left implicit. 13 tests, including the three
injections the review asked for and the R-only positive control.
`build_candidate.sh` now runs `verify_candidate.py` and fails the build.

## Blocker 4 — API-36 permissions: manifest CORRECTED, device test BLOCKED

**rc2 declares no permission at all.**

- `ACTIVITY_RECOGNITION` — removed. The generated WFF XML references no
  step, distance, calorie, floor or elevation source. It backed no feature.
- `BODY_SENSORS` — removed. Apps targeting API 36+ must use the granular
  `android.permission.health.*` permissions; the legacy one only applies
  with `android:maxSdkVersion="35"`, which `minSdk 36` can never reach.

Whether the WFF runtime supplies `[HEART_RATE]` without a declared
permission is **argued but unproven** — it needs the watch.
`tools/build_permission_variant.sh` builds the granular-permission variant
so the comparison needs only a device. `permissions-verified` is
**blocked**, not complete. Full reasoning:
`docs/reports/PHASE_4_PERMISSION_INVESTIGATION.md`.

## Blocker 5 — evidence validation: now CONTENT-BASED

`READINESS.json` + `tools/check_candidate_readiness.py`, 13 gates with
explicit `unknown|blocked|failed|waived|proposed|complete`. The checker
re-derives every claim: an empty wear directory, a blocker document, a
session bound to another APK, partial context coverage and a mismatched
installed-APK hash are each rejected, and `publishable` cannot open while
any predecessor is open. 15 deliberate-failure tests plus a positive
control proving it is not unfalsifiable in the other direction.

**Current state: 3 of 13 gates complete.** The record says so.

## Blocker 6 — candidate provenance: CLOSED, warning scoped not deleted

All 50 manifested assets plus the generated preview traced to producing
commit and source paths, with those scripts read *at that commit*.

| | |
|---|---|
| AI-checkpoint pixels | **0** |
| Donor-image pixels | **0** |
| Drifted assets | **0** |
| Repo-wide LICENSING.md warning | **NOT APPLICABLE to this candidate** |

Decisive cross-check: **zero image-ingest call sites in any studio
script**, so no external raster can reach a render. The repository-wide
warning remains accurate for the legacy faces it describes and is neither
deleted nor weakened — `PROVENANCE.json` says exactly that.

Two false positives were caught before this could be reported. A keyword
scan flagged all 50 assets on the word "checkpoint" in a comment; a
PIL-read heuristic then flagged all 50 on `Image.open(p)`. Detection is
now mechanism-based.

## Verification

| Gate | Result |
|---|---|
| engine tests | **137 passed** (95 → 137) |
| visual + lineage tests | **67 passed** |
| date-aperture proof | 62 renders, 0 violations |
| dex allowlist + deliberate failures | 13 passed |
| consumer-lineage tests | 12 passed |
| readiness-gate tests | 15 passed |
| studio guards | 10 passed (both interpreters) |
| WO-P7 | **PASS**, max 3.972% of 15% |
| release fixtures | 10/10 |
| deterministic generation | pass |
| resource inventory | clean, 60 resources |
| reference render vs proposed candidate | byte-identical |
| all-ten Gradle builds | **10/10 PASS** |
| two detached clean candidate builds | **byte-identical** |
| APK + AAB build | ✅ |
| package metadata / manifest verification | ✅ 0 problems |
| official WFF validator | ✅ PASS (v4, XML from the rc2 APK) |
| memory evaluator | ✅ PASS |
| readiness checker | ✅ 0 inconsistencies |
| provenance | ✅ clean |
| `tools/validate.py` | **0 errors, 13 warnings** |
| `git diff --check` | clean per commit |
| CI | see below |

`releases/aurelius/current/` untouched at `844b9c43…`.

## Owner launch inputs — not invented

| Item | State |
|---|---|
| TEST-1 account type / creation date / production access / prior app | **unresolved — four facts only AGENOR can supply** |
| Privacy policy URL | target `https://x1c7.com/privacy/aurelius` recorded; **not hosted**, no content checksum yet |
| Support email + response commitment | **owner to choose** |
| Price | ChatGPT recommends **$3.99 one-time**. Recorded as a *recommendation*, **not** as the owner's decision. Initial markets to be recorded with the final decision. |

## Remaining blockers to acceptance

1. physical Watch7 validation of rc2;
2. three owner wear sessions bound to APK `939d2b44…`;
3. on-device confirmation of the permission model;
4. owner pixel acceptance of APPROVAL-0005;
5. the four TEST-1 facts, hosted privacy policy, support address, price.


---

# Checkpoint B rc2 re-review — three static defects closed

**Date:** 2026-07-26
**Status:** static corrections complete; **acceptance still blocked** on device, wear and owner evidence
**Candidate:** 2.0.0-rc2 — **artifact bytes unchanged**

Answers `docs/reports/PHASE_4_CHECKPOINT_B_RC2_REVIEW.md`.

## Why this is still rc2 and not rc3

The only source-file edit is a **comment** in `build.gradle.kts` (the stale
claim that verification proved neither artifact contained dex). The review
said a changed package input requires rc3, so this was **measured, not
assumed**: rebuilding with the corrected comment produced

```
aab 1a2ae1386a5bacc70e2316c6562d50a9ec083b35b3038ecf5e564526f18a3b23
apk 939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc
```

— byte-identical to rc2. Two clean detached-worktree rebuilds from the new
source commit reproduce them again. The corrections are therefore
tooling/metadata-only in effect and rc2 is retained.

## Commit roles (moved forward; artifacts unchanged)

| Role | Commit |
|---|---|
| `consumer_source_commit` | `f6f00663f109490e294b0c0d60d1e224087c3dd0` |
| `consumer_artifact_commit` | `fa995ffad97c260ffb64a77d4f0916b593eb66a5` |
| `candidate_metadata_commit` | `61f54c465271a9115718c294a2bdca31f873a662` |

Superseded roles (`a328669e` / `ea2b0e58`) are retained in `LINEAGE.json`.

## Blocker 1 — commit objects are now authoritative

The verifier proved the artifact commit held files with the expected
*names*, then hashed the **working tree**. The claim it recorded was not
the claim it checked.

Artifact identity now comes from the object at
`consumer_artifact_commit`: blobs hashed directly, LFS pointers
contributing their `oid sha256:` with the payload verified separately (an
un-smudged checkout is reported, not failed). The disk file must equal
that object; the canonical set is defined *by* the commit — exactly one
`.aab`, one `.apk`, `VERIFY.json` — so a replacement carrying the same
role is caught. Metadata records are read, parsed and required to match
the resolved metadata commit and to declare this version.

Two bugs in my own set logic were caught by the new tests before shipping:
the canonical set was taken from the working tree, and the extra/missing
directions were inverted.

## Blocker 2 — every debug-APK dex classified

The classification immediately found what the review suspected.
`classes2.dex` holds four non-R classes:

```
Lcom/android/tools/r8/annotations/LambdaMethod;
Ljava/lang/Record;
Ljava/lang/invoke/MethodHandles$Lookup;
Ljava/lang/invoke/VarHandle;
```

D8/R8 core-library desugaring stubs, emitted into a secondary dex on debug
builds. Not application code, nothing references them, never distributed.
They are permitted by an **explicit, individually justified allowlist that
applies only to the device-test APK**. The release gate stays strictly
generated-R-only and the bundle still must contain no dex.

Final classification: 2 dex, 10 distinct classes = **6 generated R + 4
named stubs, 0 unexplained**.

## Blocker 3 — provenance contradiction resolved

`CANDIDATE.json` no longer claims the AI-model licence position is an
unresolved owner action. It records candidate provenance **closed** — zero
AI-checkpoint pixels, zero donor-image pixels, zero unresolved assets,
Rajdhani Bold the only third-party visual input — and binds
`PROVENANCE.json` by sha256. `docs/LICENSING.md` is unchanged and remains
accurate for the legacy faces it describes.

## Static verification

| Gate | Result |
|---|---|
| engine tests | **189 passed** (137 → 189) |
| visual + lineage tests | 67 passed |
| consumer-lineage tests | 32 |
| dex tests (release + debug) | 22 |
| readiness tests | 38 |
| aperture proof | 62 renders, 0 violations |
| WO-P7 | PASS, max 3.972% of 15% |
| release fixtures | 10/10 |
| deterministic generation | pass |
| resource inventory | clean, 60 resources |
| reference render vs candidate | byte-identical |
| all-ten builds | 10/10 PASS |
| two detached-worktree builds | byte-identical, equal canonical |
| AAB/APK verification | 0 problems |
| WFF validator | PASS (v4) |
| memory evaluator | PASS |
| readiness checker | 0 inconsistencies, 3/13 gates complete |
| provenance | clean |
| `tools/validate.py` | 0 errors, 13 warnings |
| `git diff --check` | clean |

`releases/aurelius/current/` untouched at `844b9c43…`.

## Device evidence gathered so far (rc2 APK `939d2b44…`)

| Gate | Result |
|---|---|
| upgrade continuity (versionCode 1 → 3, minSdk 34 → 36) | **PASS** |
| installed-APK pullback hash | **byte-identical** |
| installed-resource lineage | **58 byte-identical, 0 drift** |
| rc2 requested permissions | **none** |
| platform HR permission mapping | confirmed `android.permission.health.READ_HEART_RATE` |

Detail: `docs/reports/evidence/phase-4/aurelius/rc2/INSTALL_AND_LINEAGE.md`.

## Still blocked

The face is installed but **not yet selected in the picker**, so the
permission A/B comparison, the visual matrix and the three wear sessions
cannot proceed. Owner launch inputs remain unresolved and price remains a
recommendation only.
