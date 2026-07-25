# Phase 2 Report — Aurelius Reference Engine Slice

**Branch:** `phase-2/aurelius-reference-engine` (from `main` @ `a99551f`)
**Date:** 2026-07-24 · **Executor:** Claude Code
**Brief:** `docs/phases/PHASE_2_AURELIUS_REFERENCE_ENGINE.md` · **ADR:** ADR-008

## 1. Executive summary

The first real slice of the AGENOR engine exists and is proven: a
deterministic build-time WFF generation system (`engine/wffgen`,
0.1.0-experimental, stdlib-only) whose extraction choices are grounded in a
reproducible ten-face audit. Aurelius is now generated from an authoritative
`face.toml` spec with **element-by-element semantic parity** against the
Phase-1 baseline (regression-tested), passes the **official WFF validator**
and **memory-footprint evaluator**, builds cleanly, and leaves the released
APK byte-identical and pinned immutable. Generality is proven by two
non-proprietary fixtures that also pass the official validator. One
acceptance item is blocked and fully disclosed: physical Galaxy Watch7
evidence (no watch reachable from the build environment).

## 2. Baseline commit and evidence

Branch base `main` @ `a99551f` (descends from approved `84145b2`).
Baseline capture (`docs/reports/evidence/phase-2/aurelius/baseline/`):
validation 0 errors; build_all 10/10; CI green; SHA-256 of the immutable
release APK (`844b9c43…`), the pre-migration `watchface.xml` (`a8ce33ac…`,
snapshot committed as `watchface_baseline.xml`), and every runtime resource.
Physical baseline capture **blocked** — `DEVICE_EVIDENCE_BLOCKER.md`
documents the empty `adb devices`/`mdns` output and the mitigation.

## 3. Ten-face component-audit findings

`tools/analyze_wff_patterns.py` → `PHASE_2_COMPONENT_AUDIT.{json,md}`
(deterministic; byte-identical on repeat runs). Highlights: parallax
expression shape in **9/10** faces; `[SECOND]`/`[MILLISECOND]` in 10/10;
battery in 7; heart rate in 7; `[DAY]` in 7; analog hour/minute angle
shapes in 5/4; smooth-elapsed rotation in 4; sin-breathing alpha in 3;
`Group` used by only 3 faces; `Reference` by none; tripface confirmed as
the lone WFF v2. Unsafe list: 4 faces have unclamped `[HEART_RATE]`
expressions (aurelius is not one of them) — Phase-3 cleanup candidates.

## 4. Extraction decisions and rejected abstractions

Extracted (≥3-face evidence or Aurelius-proven): parallax, elapsed-time
base, analog hand angles, seconds rotor, continuous rotation with
direction/ratio metadata, HR oscillator w/ fallback+clamp, battery gauge,
date aperture, AOD crossfade/dim policies, breathing sheen. Rejected for
now: `Group`/`Reference` (audit shows 0 `Reference` uses; forcing them
would make generated XML harder to read — brief §3 explicitly allows
declining); digital clock stacks and step/weather bindings (2-face or
1-face patterns; remain face-specific until a second face migrates);
tripface's v2 constructs (frozen face).

## 5. Final engine architecture

`engine/wffgen`: `model` (canonical deterministic serializer; fixed per-tag
attribute order; inline text-stack support) → `expressions` (builders
emitting the exact device-proven strings) → `profiles` (AOD policies +
mandatory ledger-§8 motion classes) → `components` (10-factory registry) →
`spec` (TOML via stdlib tomllib) → `render` (banner-stamped output) →
`validation` (structural gates). CLI: `tools/generate_face.py` (identity
verification vs Gradle, double-render determinism assertion, `--check`).

## 6. Engine API / component inventory

Components: `background_pair`, `rotating_image`, `seconds_rotor`,
`hr_balance`, `battery_needle`, `date_text`, `sheen`, `analog_hand`,
`static_image`, `text_line`. Expressions: `elapsed_seconds`,
`seconds_precise`, `hour_angle`, `minute_angle`, `seconds_angle`, `clamp`,
`ratio`, `rotation_continuous`, `parallax_offset`, `heart_rate_bpm`,
`hr_oscillator_angle`, `gauge_angle`, `breathing_alpha`, `num`. Profiles:
`AmbientPolicy` (+`HIDE_IN_AOD`, `REVEAL_IN_AOD`, `dim()`), `MotionClass`
(5 classes). All experimental at 0.1.0 (engine/README.md documents the
stability contract).

## 7. Authoritative Aurelius spec format

`watchfaces/aurelius/engine/face.toml` — pure data (TOML): face metadata,
identity pin (package/versionCode/versionName), 40-glyph bitmap-font table,
12 ordered component instances with coordinates, pivots, AOD policies, and
documented mechanics (gear ratio 5:3 CW/CCW, HR oscillator 2π/60 rad/beat,
battery gauge 292.5°+45°). No face-local Python composition was needed.

## 8. Generated-source workflow

Edit `face.toml` → `python3 tools/generate_face.py aurelius` → commit both.
`--check` fails on drift (validate.py and CI both run it). Generated XML
carries a banner naming spec, command, and engine version. Hand-editing the
XML is now a validation failure.

## 9. XML parity and deterministic-generation evidence

`tests/engine/test_aurelius_parity.py`: flattened element sequence of the
generated document equals the frozen imported Phase-1 source baseline
(not claimed as byte-extracted APK content — see §15) — same tags, same
attributes (numeric attrs compared numerically, e.g. `0` ≡ `0.0`; all
expression strings compared **exactly**), comments ignored, one documented
identifier rename (`z00_aod`→`z01_aod`) via an explicit map. Determinism:
double-render asserted on every generation; analyzer and fixtures
byte-identical across runs; `--check` passes against the committed file.

## 10. Test inventory and results

`tests/engine/`: **68 tests, all passing** (34 at initial submission) — `test_expressions` (11:
baseline-string parity + safety), `test_components` (13: metadata contract,
direction metadata, pivots, validation failures incl. duplicate names,
z-order, canvas bounds, naming, missing resources, AOD bounds),
`test_render` (5: determinism, banner, structure, ordering),
`test_aurelius_parity` (2), `test_fixtures` (3: determinism+validation+no
Aurelius leakage). Plus the Phase-1 `tools/test_release_workflow.py`
re-run: **10/10 fixtures still pass**.

## 11. Fixture results

`fixture_analog.toml` (hand stack, AOD, battery needle, rotating wheel) and
`fixture_digital.toml` (AOD, battery, HR, parallax, bitmap-font clock):
deterministic, structurally valid, zero proprietary resources (test-
enforced), and **both PASS the official WFF validator, format v4**
(evidence file below).

## 12. All-ten build results

`tools/build_all.sh`: **10/10 PASS** at baseline and re-verified after
migration (final run recorded in §13 evidence). Aurelius builds from the
engine-generated XML.

## 13. Repository validation and release-fixture results

`python3 tools/validate.py`: **0 errors, 12 warnings** (same documented
set as Phase 1) — now additionally covering engine drift, fixture
determinism/validation, immutable-release pins, and handoff manifests.
Deliberate-failure fixtures verified during development: spec drift
(speed 40→41) caught; immutable-APK tamper caught (checksum + pin); short
`source_commit` caught. `tools/test_release_workflow.py`: 10/10.

## 14. WFF validator and memory-evaluator results

Official validator (google/watchface, rebuilt offline; wrapper
`tools/wff_validate.sh`; jar at `~/Applications/wff-validator/`):
**PASSED ×3** (aurelius, both fixtures) — evidence:
`candidate/wff_validator_results.md`. Memory-footprint evaluator
(play-validations 1.7.0, `executable-jar` build): **PASS** for the
engine-built candidate APK and the immutable release APK — evidence:
`candidate/memory_footprint_results.md` (limits 10 MB ambient / 100 MB
active, schema 4).

## 15. Physical Watch7 test matrix and evidence paths

**EXECUTED 2026-07-24 (evening session)** on the physical Galaxy Watch7
44 mm (SM-L310, Android 16 / API 36) over owner-provided wireless adb.
Full per-row results:
`docs/reports/evidence/phase-2/aurelius/baseline/DEVICE_TEST_RESULTS.md`
and `candidate/DEVICE_TEST_RESULTS.md` (which supersede the two
DEVICE_EVIDENCE_BLOCKER notes).

Summary: the immutable Phase-1 APK (`844b9c43…`) was installed and the
full baseline matrix captured (normal/AOD screenshots during verified
Doze, transition + 60 s motion recordings, cage 6°/s timing, 5:3
counter-rotating gears, 10× AOD cycles, touch/stability rows — all PASS).

**The first candidate run caught a real regression:** the repo's Aurelius
art assets (46 of 53 PNGs + preview) had diverged from the released APK
since the Phase-1 source import — the candidate rendered the unreleased
WARBIRD design. Root cause, fix, and lineage proof:
`candidate/ASSET_DIVERGENCE_FINDING.md`. The art was restored from the
immutable release APK's own bytes (which also **proves byte-for-byte XML
lineage**: the APK's `res/raw/watchface.xml` extracts to exactly
`watchface_baseline.xml`'s hash `a8ce33ac…`). The corrected candidate
(`b01015c8…`) passes the full matrix with an explicit
**no-regression** conclusion vs baseline. `install -r` upgrade continuity
held at every step (one documented One UI behavior: reinstalling the
active face deactivates it; re-select in the picker).

Row-level caveats (details in the results files): parallax (row 9) was
physically verified via owner tilt on the corrected candidate
(recording committed); a direct candidate doze screencap was not
obtainable (non-capturable display pipeline during that window) — AOD
behavior is proven by the 10-cycle run and the ambient render is
byte-determined equal to the baseline's captured AOD.

## 16. Current-release checksum preservation

`releases/aurelius/current/aurelius.apk` untouched:
`844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2`
(equals Phase-1 manifest value), now enforced by the tracked
`.immutable` pin — any byte change fails validation.

## 17. Licensing / provenance impact

No new third-party assets. Fixtures use synthetic resource names only.
Handoff manifests carry license/provenance per entry; the example entry is
`original`. License inventory validation remains clean.

## 18. Asset-handoff contract implementation

`docs/ASSET_HANDOFF_CONTRACT.md` (all 16 required fields incl. stable id,
source commit, dimensions/color-space/alpha/pivot, frame timing + loop
semantics, AOD suitability, license, SHA-256, lifecycle, consumer,
regeneration command) + machine schema `docs/asset-handoff.schema.json` +
validator enforcement + synthetic non-approved example
(`watchfaces/aurelius/engine/handoff.json`, real asset-repo commit
`2376d68…`, `example: true`, null destination). Sibling repo untouched.

## 19. Deviations from the brief

1. ~~**Physical-device evidence (baseline §4.1.4 and candidate §4.9) not
   captured**~~ — **resolved 2026-07-24 evening**: full baseline and
   candidate matrices executed on the physical Watch7 (§15); the run
   surfaced and fixed a real source-asset divergence
   (`candidate/ASSET_DIVERGENCE_FINDING.md`). The §4.1.4 "before any
   modification" baseline ordering could no longer be literally satisfied
   (the branch predates the device session); the immutable APK stood in as
   the pre-modification artifact, which is exactly its §4.1.4 role.
   Row-level caveats documented in §15.
2. Baseline capture happened at branch creation rather than before any
   repo activity — no Aurelius file was modified before capture.
3. `Reference`/`Group` deliberately not adopted (audit-backed; permitted
   by brief §3).
No other deviations.

## 20. Technical debt and risks

Engine APIs unproven beyond one face (expected; experimental tag) ·
9 faces remain hand-authored · unclamped HR expressions in 4 legacy faces ·
WFF validator/memory tools live outside the repo (`~/Applications`) with a
documented rebuild recipe but no CI integration yet · fixture XMLs are
generated (not committed), so validator coverage of them is local+CI via
engine, not via the official validator in CI · ~~device-evidence gap until
watch pairing is available~~ (closed — §24; remaining risk is the absence
of an automated visual/resource-lineage gate, which the WARBIRD finding
showed is the real exposure — mandated for Phase 3 by the final review).

## 21. Recommended Phase 3

Per brief §10: premium Aurelius rebuild + first real asset-studio
integration — studio template/lighting/camera rigs and first approved
material families in `AGENOR-Horology`; first parametric gear/tourbillon
exports flowing through the (now-live) handoff manifest with real
checksums; visually upgraded Aurelius candidate assembled from approved
assets; ~~close the device-evidence gap first~~ (closed — §24; instead,
Phase 3 must add the visual/resource-lineage gate required by
`PHASE_2_FINAL_REVIEW.md`: golden normal/AOD renders, pixel/perceptual
comparison with masks, resource-inventory reports, real handoff-manifest
provenance, and device evidence for the first premium candidate);
CI additions: build the WFF validator in CI, run it on all engine outputs.

## 22. Branch and commit hashes

`phase-2/aurelius-reference-engine`:
1. `c218aea` — capture baseline and audit WFF patterns
2. `49fc612` — add deterministic WFF engine foundation
3. `9873405` — migrate Aurelius to engine-generated XML
4. `399ef23` — add fixtures, validation, and asset handoff contract
5. (final commit) — device evidence disclosure, CI, docs, this report

---

## 23. Review corrections (post-review pass, 2026-07-24)

ChatGPT review (`PHASE_2_CHATGPT_REVIEW.md`, commit `973d30a`) returned
CHANGES REQUESTED with four blockers. Status:

**Blocker 2 — ratio() (FIXED, `cb10ddb`).** General normalization is now
`(clamp(e, lo, hi) - lo) / (hi - lo)`; the zero-based fast path emits the
exact device-proven battery string so Aurelius parity is untouched;
`hi <= lo` raises. Positive/negative tests added (zero-based, nonzero-based,
negative-based, invalid ranges, gauge parity).

**Blocker 3 — handoff schema enforcement (FIXED, `cb10ddb`).**
`check_handoff` now implements the complete schema contract in stdlib
checks — including asset-id pattern, type checks, dimension/pivot/frame
rules, all enums, sha256 format AND requiredness for real destinations,
path-traversal rejection, and destination containment under the consuming
face's `app/src/main/res/`. 26-case test suite
(`tests/engine/test_handoff_validation.py`). The contract doc now describes
the mechanism literally.

**Blocker 4 — WFF-version cross-check (FIXED, `cb10ddb`).**
`generate_face.py` resolves the manifest format version through
`@integer/wff_version` and refuses generation/check on mismatch or when
unresolvable; deliberate-mismatch and unresolvable tests added
(`test_generate_face_checks.py`). Aurelius stays WFF v4.

**Blocker 1 — physical Watch7 evidence (STILL BLOCKED).** Re-attempted at
correction time: `adb devices` and `adb mdns services` remain empty; no
stored pairing exists, and wireless-debug pairing requires owner-held
credentials (IP:port + code shown on the watch). The review's full
procedure — baseline matrix on the immutable APK, candidate build +
`install -r` upgrade-continuity check (with signature-mismatch fallback),
candidate matrix, explicit regression comparison — is ready to execute the
moment pairing is available (`docs/DEVICE_TEST_MATRIX.md`). Baseline-lineage
wording corrected everywhere: `watchface_baseline.xml` is the frozen
imported Phase-1 source baseline, not proven APK-extracted content; the
preserved APK + physical test are the authoritative release-behavior
evidence.

Re-verification after corrections: 68 engine tests OK; release-workflow
fixtures 10/10; build_all 10/10; official WFF validator PASS ×3 (re-run);
memory evaluator PASS ×2 (re-run); `tools/validate.py` 0 errors; immutable
release checksum unchanged (`844b9c43…`); CI green on the branch.

## 24. Blocker-1 closure: device evidence session (2026-07-24 evening)

The owner provided wireless-debug access to the physical Watch7 and the
review's full blocker-1 procedure was executed end-to-end (§15 for the
summary; per-row results in both `DEVICE_TEST_RESULTS.md` files).

Two findings beyond the matrix itself:

1. **The device test caught a real regression, vindicating the review's
   refusal to waive it.** The repo's Aurelius drawables had been WARBIRD
   art (a different, unreleased design) since the Phase-1 source import —
   semantically-correct XML over wrong PNGs, invisible to every static
   gate. Fixed by restoring the drawables from the immutable release
   APK's bytes; corrected candidate `b01015c8…` re-passed the full matrix
   with no regression vs baseline
   (`candidate/ASSET_DIVERGENCE_FINDING.md`).
2. **XML byte lineage is now proven, upgrading the §23 wording.** The
   immutable APK's `res/raw/watchface.xml` (stored verbatim by AAPT2)
   extracts to hash `a8ce33ac…` — byte-identical to
   `watchface_baseline.xml`. The "frozen imported source baseline" is
   therefore also the released XML, byte-for-byte; the same extraction
   comparison is what exposed the PNG divergence.

Post-fix re-verification (this session): `generate_face.py aurelius
--check` OK; 68/68 engine tests; 10/10 release-workflow fixtures; 10/10
all-faces build; WFF validator PASS; memory evaluator PASS (corrected
candidate); `tools/validate.py` 0 errors; `git diff --check` clean;
immutable release checksum unchanged (`844b9c43…`).
