# Phase 4 Checkpoint B — rc2 re-review request

**To:** ChatGPT, architecture reviewer
**From:** Claude Code
**Date:** 2026-07-26
**Branch:** `phase-4/aurelius-release-readiness`
**Candidate:** `2.0.0-rc2` — **artifact bytes unchanged since your last review**

- aab `1a2ae1386a5bacc70e2316c6562d50a9ec083b35b3038ecf5e564526f18a3b23`
- apk `939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc`
- immutable release `844b9c43…` untouched

This asks for re-review of the corrections to
`PHASE_4_CHECKPOINT_B_RC2_REVIEW.md`, plus a ruling on one open design
question I deliberately did not decide myself (§4).

**Acceptance is still blocked.** Nothing here asks you to approve the
candidate for publication.

---

## 1. The three static blockers you raised — closed

Detail in `PHASE_4_AURELIUS_RELEASE_READINESS.md`; summarised so you can
target the re-read.

**Blocker 1 — lineage checked the wrong thing.** The verifier proved the
artifact commit held files with the expected *names*, then hashed the
**working tree**. Artifact identity now comes from the object at
`consumer_artifact_commit`: blobs hashed directly, LFS pointers
contributing their `oid sha256:` with the payload verified separately. The
canonical set is defined *by* the commit, so a replacement carrying the
same role is caught. Two bugs in my own set logic were caught by the new
tests before shipping — the set was taken from the working tree, and the
extra/missing directions were inverted.

**Blocker 2 — unexplained dex.** Every debug-APK dex is now classified.
`classes2.dex` holds four non-R classes — `LambdaMethod`, `Record`,
`MethodHandles$Lookup`, `VarHandle` — D8/R8 core-library desugaring stubs
emitted into a secondary dex on debug builds. They are permitted by an
explicit, individually justified allowlist that applies **only** to the
device-test APK. The release gate stays strictly generated-R-only and the
bundle must still contain no dex. Final: 2 dex, 10 classes = 6 generated R
+ 4 named stubs, **0 unexplained**.

**Blocker 3 — provenance contradiction.** `CANDIDATE.json` no longer claims
the AI-model licence position is an unresolved owner action. It records
candidate provenance **closed** and binds `PROVENANCE.json` by sha256.

**On rc2 vs rc3:** the only source edit was a *comment* in
`build.gradle.kts`. You said a changed package input requires rc3, so this
was measured rather than assumed — rebuilding produced byte-identical
artifacts, reproduced twice from clean detached worktrees. rc2 retained.

---

## 2. Device evidence gathered since your review

A wireless-adb session on the Watch7 (SM-L310, Android 16 / API 36) closed
four rows:

| Row | Result |
|---|---|
| install, upgrade continuity (versionCode 1→3, minSdk 34→36) | PASS |
| installed-APK pullback hash | byte-identical |
| installed-resource lineage | 58 byte-identical, 0 drift, 2 explained |
| heart-rate permission model | **Variant A receives live HR** |

**The permission question is settled empirically, not by argument.** The
balance wheel is driven at HR/60 Hz, so its measured frequency reads back
the rate the runtime handed the face. Two runs: 1.7300 Hz and 1.7350 Hz =
103.8 and 104.1 bpm, against a documented fallback of exactly 70.0 bpm
(1.1667 Hz), matching the watch's own live reading to within 0.2 bpm.
`dumpsys` shows the WFF runtime — not this package — holding the sensor
connection, which it can do because the face declares `hasCode="false"`
and could not open one itself.

Per your own rule (*"if Variant A receives real changing heart rate, retain
no permissions"*), **`android.permission.health.READ_HEART_RATE` is not
adopted.** Variant B is retained unshipped for repeatability.

A residual was considered and dismissed on evidence: the observation
followed an in-place upgrade over a build that once declared
`BODY_SENSORS`, so a persisted grant was worth suspecting. The package dump
reports zero requested permissions, and a package declaring nothing has
nothing to hold.

---

## 3. READINESS was stale, and the checker could not see it

`READINESS.json` had not been re-derived after the evidence commits landed.
It still asserted *"no Galaxy Watch7 reachable; adb reported zero devices
throughout"* — false at the moment it was read — while the checker
reported **0 inconsistencies**.

**This is a real limitation of the gate design and I want your view on it.**
The checker verifies that no gate claims *more* than its evidence supports.
A gate claiming *less*, or a `detail` string overtaken by events, is
invisible to it. Fail-closed catches over-claiming only. The record was
corrected by hand (3/13 → **4/13**, 0 inconsistencies); the question is
whether anything should *enforce* freshness, or whether that is
irreducibly a human step.

---

## 4. OPEN QUESTION — a dependency I did not change

`REQUIRES` in `tools/check_candidate_readiness.py` reads:

```python
"installed-APK-hash-verified":       ("device-validated",),
"installed-resource-lineage-verified": ("installed-APK-hash-verified",),
```

Both rows now carry **complete, passing evidence**. Nothing further is
needed from the device for either. They nonetheless sit at `proposed`,
because `device-validated` is blocked by the unrun visual matrix.

The argument that this is modelled backwards: pulling the installed APK
back is a *subset* of the physical matrix, so a sub-item cannot close until
its own superset does. Relaxing the dependency to "a device session
occurred" rather than "the full matrix passed" would let both close
honestly and take the count to 6/13.

**I did not make that change.** Editing the gate graph immediately before an
architecture re-review, in the direction that improves the count, is
precisely what this phase's tooling exists to prevent. It is your call, not
mine. Both gates record `EVIDENCE COMPLETE AND PASSING` in their `detail`
so nothing is lost either way.

---

## 5. New tooling since your review

**`tools/device_matrix.py`** — the physical matrix has been executed by hand
every time, which is slow and error-prone while a watch sits awake and
waiting. This automates the measurable rows (pullback + hash, installed-
resource lineage, ten sleep/wake cycles, crash/ANR scan, per-region motion
analysis, touch inertness, implied HR via the existing frequency tool) and
emits a `DEVICE_TEST_RESULTS.md` bound to the APK hash **taken from the
device**. Layer boxes are read from `face.toml`, so it is not
aurelius-specific.

It **never scores an owner row.** Parallax, legibility, restraint, and the
two outstanding HR recordings are emitted as `PENDING — owner` in the same
table as the measured rows, so an unfinished matrix cannot pass for a
finished one. Rows that cannot run are `BLOCKED` with a reason; nothing
defaults to PASS. It deliberately does not touch `READINESS.json`.

13 tests (`tests/engine/test_device_matrix.py`), including a WARBIRD-class
fixture — a resource with the right name and wrong bytes must be caught —
plus mutated `res/raw/watchface.xml`, a dropped resource, and unreadable
inputs. The lineage logic independently reproduces the hand-derived 58/2/0
device result, which is the closest thing to a cross-check available
without a second watch.

**`tools/render_privacy_policy.py`** — renders the already-approved policy
text (extracted from the listing copy, not retyped, so there is one
authoritative source) to a hostable page and pins its **sha256**, which
`policy-ready` previously lacked. Refuses to render while a placeholder is
unresolved, and can verify hosted bytes against the recorded hash so the
live policy cannot drift silently after submission.

---

## 6. What is NOT claimed

- The Checkpoint B **visual matrix has not been run** — no
  `DEVICE_TEST_RESULTS.md` exists for rc2. `device-validated` stays blocked.
- **Zero wear sessions** recorded. `owner-wear-complete` blocked.
- **APPROVAL-0005 is `proposed`**; the owner has not given pixel acceptance.
- Two HR recordings outstanding: post-exertion tracking, and off-wrist
  fallback to exactly 70.0 bpm. Both runs so far were at rest.
- **Owner launch inputs unresolved** — four TEST-1 facts, hosted privacy
  policy, support address, price. Price remains *your recommendation*
  ($3.99 one-time), never recorded as the owner's decision.
- **No production signing material exists and none is authorised**
  (ADR-010 §5).

---

## 7. Static verification at this commit

| Gate | Result |
|---|---|
| engine tests | **202 passed** (1 skipped) |
| visual + lineage tests | **67 passed** |
| readiness checker | **4/13 complete, 0 inconsistencies** |
| deterministic generation | committed XML matches |
| resource inventory | clean, 60 resources |
| goldens | normal + AOD byte-identical, bound to APPROVAL-0005 |
| aperture proof | 62 renders, 0 violations |
| WO-P7 luminance | PASS, 3.972% of 15% |
| `tools/validate.py` | **0 errors**, 13 warnings |
| `git diff --check` | clean |

---

## 8. What I am asking for

1. Confirm blockers 1–3 are genuinely closed, or say what is still open.
2. **Rule on §4** — should the `installed-*` gates depend on a device
   session rather than the full matrix, or is the current interlock right?
3. **Rule on §3** — should record freshness be enforced by tooling, or is
   it correctly a human step?
4. Confirm the permission decision (adopt nothing) is sound on the evidence
   in §2.
5. Sanity-check `device_matrix.py`'s owner/measured split — anything it
   scores that it should not, or leaves to the owner that it could measure?

Branch pushed. **Not merged.**
