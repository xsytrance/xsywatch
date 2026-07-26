# Phase 4 — Aurelius baseline verification (Checkpoint A, step 1)

**Repository:** `xsytrance/xsywatch`
**Branch:** `phase-4/aurelius-release-readiness`
**Branch point:** `3333d427e9c87f1c59b26d61c41f6b9ce6435152` (main)
**Paired studio branch:** `AGENOR-Horology@phase-4/aurelius-craftsmanship-release-assets` from `3f12eda7c3c98c942d4a297eab7a721864aedf4d`
**Verified:** 2026-07-26
**Verdict:** baseline reproduces exactly; every gate green; no approved
pixel, resource, package field or release artifact modified.

This report records the measured starting state for Phase 4. It changes no
runtime pixels and no package/version metadata, as required by the phase
scope §7.

---

## 0. Rebuild note — nothing derived is committed

**Everything derived in this report must be rebuilt before it can be
inspected.** The repository deliberately tracks source and evidence, not
build output: `watchfaces/*/app/build/` is untracked, and the reference
renders, APKs, validator runs and evaluator runs below exist only in a
working tree until someone regenerates them.

If you are picking this up on another machine, or after a clean, rebuild
what you need with the exact commands in §2–§4. In particular:

- the Aurelius APK hashed at `5a1271ab…` in §3 is **not** in Git — rebuild
  it with `tools/build_all.sh` (or `tools/build_face.sh aurelius`);
- the reference renders compared in §2 are regenerated on demand by
  `tools/render_reference.py`; only the committed goldens are tracked;
- the studio proposal renders in the paired repository are committed, but
  their scenes can be rebuilt from `scripts/build_aurelius_craft.py`.

The only artifacts that are authoritative *as committed bytes* are the
goldens, the inventories, the approval records, the immutable release under
`releases/aurelius/current/`, and the studio exports. Everything else is
reproducible and should be treated as disposable.

---

## 1. Repository state

| Check | Result |
|---|---|
| `xsywatch` main head | `3333d427e9c87f1c59b26d61c41f6b9ce6435152` ✅ matches expected |
| required commit `3e0616aa…` | present |
| required commit `3333d427…` | present |
| `AGENOR-Horology` main head | `3f12eda7c3c98c942d4a297eab7a721864aedf4d` ✅ matches expected |
| required commit `3f12eda7…` | present |
| both working trees | clean |
| both local `main` vs `origin/main` | identical |
| Phase 3 merged | yes — `74ddde7` (consumer), `cd67186` (studio), both ancestors of their `main` |
| approved visual version | `field-tourbillon-mk2-r2` |
| pre-existing Phase 4 implementation | none — the only Phase-4 paths are the three newly committed scope documents |

---

## 2. Approved goldens reproduce byte-for-byte

```bash
python3 tools/render_reference.py aurelius --goldens --check
```

| Render | SHA-256 | Expected (phase scope §2) | Result |
|---|---|---|---|
| normal | `7fd2cf63607e2aa6ef53d0443c44e16885284705d5f4336602aa3ce2526a556e` | same | ✅ byte-identical |
| aod | `2f2be0e91b7473b5bb492cdc55094777d570a268f36e751d109be56888f1e936` | same | ✅ byte-identical |

Renderer determinism selftest (`--selftest`): PASS, including
`parallax_neutral`.

---

## 3. Phase 3 APK rebuilds exactly

```bash
tools/build_all.sh          # JAVA_HOME=/home/xsyprime/jdk, ANDROID_HOME=~/Android/Sdk
```

| Artifact | SHA-256 | Size |
|---|---|---|
| rebuilt `app-debug.apk` | `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a` | 3,600,717 B |
| Phase 3 tested APK (scope §2) | `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a` | — |

**Exact reproduction achieved.** The established environment rebuilds the
tested Phase 3 candidate byte-for-byte, so scope §7.3's conditional
("where the established toolchain permits exact reproduction") is satisfied
rather than waived. This is a stronger result than Phase 4 required and it
gives the release-candidate work in Workstream 5 a proven reproducibility
baseline to compare against.

---

## 4. Complete gate suite

All commands run from the repository root on the reference Linux machine.

| Gate | Command | Result |
|---|---|---|
| engine tests | `python3 -m unittest discover -s tests/engine` | **95 passed** |
| visual + lineage tests | `python3 -m unittest discover -s tests/visual` | **38 passed** (50 after §6) |
| engine generation drift | `python3 tools/generate_face.py aurelius --check` | committed XML matches deterministic generation |
| resource inventory | `python3 tools/inventory_resources.py aurelius --check` | clean, 60 resources |
| reference render vs goldens | `python3 tools/render_reference.py aurelius --goldens --check` | byte-identical |
| renderer determinism | `python3 tools/render_reference.py aurelius --selftest` | PASS |
| date-aperture proof | `python3 tools/date_aperture_proof.py aurelius --check` | **62 renders, 0 violations**, worst margin 3.07 px vs 2.0 px contract |
| release fixtures | `python3 tools/test_release_workflow.py` | 10/10 behaved as required |
| all-ten builds | `tools/build_all.sh` | **10/10 PASS** |
| official WFF validator | `tools/wff_validate.sh 4 …/res/raw/watchface.xml` | ✅ PASSED against WFF v4 |
| memory footprint (rebuilt candidate) | `java -jar memory-footprint.jar --watch-face … --schema-version 4 --ambient-limit-mb 10 --active-limit-mb 100` | ✅ PASS |
| memory footprint (immutable release) | same, against `releases/aurelius/current/aurelius.apk` | ✅ PASS |
| repository validation | `python3 tools/validate.py` | **0 errors, 13 warnings** |
| whitespace / conflict markers | `git diff --check` | clean |
| CI | `.github/workflows/validate.yml` | ✅ **green** — run `30216783275`, `validate` job passed in 29 s on branch head `b4dd574` |

### The 13 validation warnings

All pre-existing and all documented; none introduced by Phase 4.

- 4 × `releases[<face>/current]: no preview image` — ares-wargod, bone-watch, hellforge, pinball;
- 3 × `source[<face>]: no release yet` — arcwright, chronova, tripface;
- 1 × `size: docs/reports/evidence/phase-3/aurelius/candidate_60s_motion.mp4 is 8.5 MB (>8 MB)`;
- 5 × `paths: … external donor ref …ComfyUI…` — documented provenance, ADR-007.

---

## 5. Inventory

### Package / version metadata — unchanged, and not to be changed at Checkpoint A

| Field | Value |
|---|---|
| applicationId / namespace | `com.xsytrance.aurelius` |
| versionCode | `1` |
| versionName | `1.0` |
| minSdk / targetSdk / compileSdk | 34 / 36 / 36 |
| WFF version | 4 (`@integer/wff_version`) |
| label / icon | `AURELIUS` / `@drawable/preview` |
| declared permissions | `BODY_SENSORS`, `ACTIVITY_RECOGNITION` |
| standalone | `true` |
| `android:hasCode` | `false` |

The two declared permissions are the reason the policy audit must cover
health-data disclosure — see `docs/reports/PHASE_4_POLICY_AUDIT.md`.

### Release directories

`releases/{ares-wargod,aurelius,bone-watch,bushido,hellforge,pinball,pulseface}/current/`
— 7 channels, all `current`, no versioned archives yet.

### Signing state

Debug only. No `signingConfig`, `storeFile`, `keyAlias` or keystore
reference exists in any Gradle file; no `.jks`/`.keystore`/`keystore*` file
exists anywhere in the tree. This is the deliberate Phase-1 position and it
is unchanged.

### Toolchain (measured)

| Tool | Version |
|---|---|
| JDK | Temurin 21.0.11+10 LTS |
| Gradle | 9.6.1 (committed wrapper) |
| Android SDK / build-tools | 36 / 36.0.0 |
| Python | 3.14.4 |
| Pillow | 12.1.1 — matches the `states.toml` `[render]` pin |
| Blender (studio) | 4.5.11 LTS |
| WFF validator | google/watchface, "Maximum Supported Format Version #5" |
| memory-footprint evaluator | 1.7.0 |
| GPU (studio) | NVIDIA RTX 5060 Ti, OPTIX |

### Product copy and previews

- source preview `watchfaces/aurelius/app/src/main/res/drawable/preview.png`, 195,404 B (400×400, generated consumer-side from the r2 normal reference);
- release preview `releases/aurelius/current/preview.png`, 335,519 B;
- no store listing copy, long description, feature list, support text or privacy statement exists yet — all are Workstream 8 deliverables and all are currently **absent**.

### Licenses and provenance

- `docs/asset-licenses.json` — 28 audited entries (27 OFL-1.1 fonts + 1 CC0 HDRI), enforced by `validate.py`;
- `docs/LICENSING.md`, `THIRD_PARTY_NOTICES/fonts/`;
- `docs/derived-asset-provenance.json` — Rajdhani-derived rasters;
- `watchfaces/aurelius/engine/handoff.json` — 50 studio assets, lifecycle `approved`, metadata commit `67b68cbf…`;
- **open owner action carried from Phase 1:** the AI-model license position for commercial sale of generated artwork is unresolved (`docs/LICENSING.md`).

### Known limitations

`docs/KNOWN_LIMITATIONS.md` is current and unmodified. The items that bear
on Phase 4 are: debug signing only; 4 faces without release previews;
battery impact anecdotal; single-device testing; Cycles re-renders not
byte-deterministic; AOD panel capture unavailable on this hardware.

---

## 6. Evidence preservation

| Generation | Approval | Owner | Architecture | Artifacts |
|---|---|---|---|---|
| `field-tourbillon-v1` | APPROVAL-0001 | approved | approved | goldens preserved |
| `field-tourbillon-mk2` | APPROVAL-0002 | proposed | pending | candidate preserved |
| `field-tourbillon-mk2-r1` | APPROVAL-0003 | proposed | pending | candidate + evidence preserved |
| `field-tourbillon-mk2-r2` | APPROVAL-0004 | **approved** | **approved** | active golden |

Golden hashes verified on disk:

| Path | SHA-256 |
|---|---|
| `goldens/field-tourbillon-mk2-r2/normal.png` | `7fd2cf63…6a556e` |
| `goldens/field-tourbillon-mk2-r2/aod.png` | `2f2be0e9…8f1e936` |
| `goldens/field-tourbillon-v1/normal.png` | `f52b715e…0b15f6d` |
| `goldens/field-tourbillon-v1/aod.png` | `04161e9b…259e4fd6` |
| `inventories/versions/field-tourbillon-mk2-r2.json` | `b76f9ceb…3875c269` ✅ matches scope §2 |
| `inventories/inventory.json` | `b76f9ceb…3875c269` |

Evidence directories present: `docs/reports/evidence/phase-2/aurelius/{baseline,candidate}`,
`docs/reports/evidence/phase-3/aurelius/{,r1,r2}`. All four approval
records, all prior inventory snapshots and the complete WARBIRD/Bfont
investigations are intact.

---

## 7. `releases/aurelius/current/` is untouched

```
844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2  aurelius.apk
```

Matches the pinned checksum exactly. Size 3,664,664 B. The `.immutable`
marker, `RELEASE.md` and `preview.png` are unmodified. Nothing in Phase 4
Checkpoint A writes to this directory.

Note the rebuilt candidate (3,600,717 B) is a *different artifact* from the
immutable v1 release (3,664,664 B) — different generation, different
resources. Both are expected to differ; neither replaces the other.

---

## 8. What this baseline permits

Because the goldens and the APK both reproduce exactly, any later Phase 4
difference is attributable to a deliberate change rather than to
environment drift. That is the whole point of running this step before
touching anything.

---

## 9. Qualifications

1. ~~**CI not yet observed for this branch.**~~ **Resolved:** the branch
   was pushed and GitHub Actions run
   [`30216783275`](https://github.com/xsytrance/xsywatch/actions/runs/30216783275)
   passed in 29 s at branch head `b4dd574`. Note CI deliberately does not
   build APKs, run the WFF validator or run the memory evaluator (runner
   cost; see the workflow header) — those three gates are local-only and
   their results are recorded in §3–§4 above.
2. **Device evidence is not part of this baseline.** No Watch7 was
   attached. Physical validation belongs to Checkpoint B and to the wear
   packet.
3. **The memory evaluator and WFF validator are unlicensed third-party
   binaries** built locally from `google/watchface`; they are not vendored
   into the repository. They must be present at
   `~/Applications/wff-validator/` to re-run those two gates.
4. **Exact APK reproduction is a property of this machine and toolchain.**
   It has not been demonstrated on a second machine, and scope §11.8
   (two clean builds from a documented environment) belongs to Checkpoint B.
