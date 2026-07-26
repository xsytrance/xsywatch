# Phase 4 — Aurelius commercial release readiness

**Status:** **Checkpoint A complete — stopped at the owner checkpoint**
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
