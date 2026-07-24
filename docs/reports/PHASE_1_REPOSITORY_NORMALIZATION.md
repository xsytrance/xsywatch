# Phase 1 Report — Repository Normalization & Reproducible Source Import

**Branch:** `phase-1/repository-normalization` · **Date:** 2026-07-24
**Executor:** Claude Code · **Ledger:** `docs/CHATGPT_ARCHITECT.md`

## 1. Executive summary

`xsywatch` was transformed from an artifact-only shelf (7 APKs + 3 previews at
repo root, no docs, no source) into a reproducible engineering repository:
**10 complete editable WFF source projects imported, all 10 build successfully
from the imported source**, 7 released APKs preserved with checksummed
metadata under `releases/`, repo-wide validation passes with 0 errors, no
secrets found, and the 7-vs-8 discrepancy is resolved (commit-message
miscount — no APK is missing). The ledger's Phase-1 acceptance criteria are
all met.

## 2. Original repository state

Two commits: `d8ed43b` (7 APKs + 3 previews at root) and `b740207` (the
architecture ledger). No source, no README, no .gitignore, no tooling.

## 3. Local source locations discovered

| Location | Contents | Disposition |
|---|---|---|
| `~/Android/<Name>` ×10 | complete Gradle WFF projects (see §6) | imported → `watchfaces/<slug>/` |
| `~/Android/{HermesApproval,PrimeBeaconWear,WearComposeLaunchpad}` | Wear OS apps, not watch faces | excluded (out of scope) |
| `~/AGENOR-Horology` (pushed: xsytrance/AGENOR-Horology) | 3D asset pipeline (Blender/Material Maker), docs, scripts | kept as sibling repo (ADR-005) |
| `~/Android/WATCHFACE-DEV-MANUAL.md`, `BONE-WATCH-PLAN.md` | local reference docs | not imported (personal notes; flagged as candidate for later import) |
| `~/.claude/uploads/.../d7e1ddb3-10289.jpg` | tripface donor art in a volatile path | preserved → `watchfaces/tripface/tools/xsytrance_character.jpg` |

## 4. Final repository tree (condensed)

```
README.md  CONTRIBUTING.md  .gitignore
docs/
  CHATGPT_ARCHITECT.md          (ledger, updated)
  BUILD_AND_RELEASE.md  WATCHFACE_INVENTORY.md  KNOWN_LIMITATIONS.md  LICENSING.md
  decisions/ADR-005..007        reports/PHASE_1_REPOSITORY_NORMALIZATION.md
watchfaces/<slug>/              ×10 complete Gradle+WFF projects w/ gradlew + README
tools/
  check_prereqs.sh  build_face.sh  build_all.sh  package_release.py
  gen_release_manifest.py  validate.py  test_release_workflow.py
releases/
  MANIFEST.json                 (machine-readable, SHA-256)
  <slug>/current/{<slug>.apk, preview.*, RELEASE.md}   ×7
```

1,004 tracked files; repo ~79 MB (APKs 28 MB + source art).

## 5. Watchface inventory

See `docs/WATCHFACE_INVENTORY.md`. Summary: 7 released (bushido, ares-wargod,
aurelius, bone-watch, hellforge, pinball, pulseface), 3 source-only
(arcwright v0.0.1, chronova v0.1, tripface). All WFF v4 except tripface
(WFF v2). All packages `com.xsytrance.*`, all versionCode 1, targetSdk 36.

## 6. APK-to-source mapping (verified via aapt2 package names)

| APK (original name) | Source project (local) | Now |
|---|---|---|
| xsywatch-bushido.apk | ~/Android/XsywatchBushido | watchfaces/bushido |
| ares-wargod.apk | ~/Android/AresWarGod | watchfaces/ares-wargod |
| aurelius.apk | ~/Android/Aurelius | watchfaces/aurelius |
| bone-watch.apk | ~/Android/BoneWatch | watchfaces/bone-watch |
| hellforge.apk | ~/Android/HellForge | watchfaces/hellforge |
| pinball.apk | ~/Android/Pinball | watchfaces/pinball |
| pulseface.apk | ~/Android/PulseWatchFace | watchfaces/pulseface |
| — (none) | ~/Android/Arcwright | watchfaces/arcwright |
| — (none) | ~/Android/Chronova | watchfaces/chronova |
| — (none) | ~/Android/XsytranceWatchFace | watchfaces/tripface |

## 7. Missing or incomplete watchfaces

- **"Eighth face": resolved.** Commit `d8ed43b`'s message says "Eight" but
  lists exactly seven names; seven APKs map 1:1 to seven source projects.
  The message miscounted. Nothing is missing.
- No face has missing source. 4 releases lack preview images (warning).

## 8. Toolchain and versions (verified on this machine)

JDK 21.0.10 (Android Studio JBR) · Gradle 9.6.1 (wrapper now committed per
face) · Android SDK: compileSdk/targetSdk 36, build-tools 36.0.0,
platform-tools 37.0.0 (adb 1.0.41) · Python 3 + Pillow 12.2.0 ·
aapt2 36.0.0 · git 2.53.0. Samsung Watch Face Studio: **not used — no Linux
build exists** (Win/macOS 1.9.5 only, verified 2026-07); supported Linux
workflow is hand-authored WFF XML + Gradle (ledger ADR-004). Optional
WFS route would require a Windows VM; no Linux WFS solution is claimed.

## 9. Build commands

```bash
tools/check_prereqs.sh          # environment gate
tools/build_face.sh <slug>      # one face
tools/build_all.sh              # all faces, PASS/FAIL table
python3 tools/validate.py       # repo-wide validation
python3 tools/package_release.py <slug>  # stage a release safely (see §21)
```

## 10. Build results per watchface (from imported source, this machine)

arcwright PASS · ares-wargod PASS · aurelius PASS · bone-watch PASS ·
bushido PASS · chronova PASS · hellforge PASS · pinball PASS ·
pulseface PASS · tripface PASS — **10/10.**
Additionally, rebuilt APK package/versionCode/versionName metadata matches
the released APKs for all 7 released faces.

## 11. Validation results

`python3 tools/validate.py` → **0 errors, 12 warnings** (4 missing release
previews; 3 source-only faces; 5 external AI-donor path references kept as
documented provenance). Two ERRORs found during development (absolute paths
in bushido/tripface tools) were fixed in commit 4.

## 12. Files intentionally excluded

Per-project: `build/`, `.gradle/`, `.kotlin/`, `local.properties` (machine
SDK path), `.idea/`, nested `.git` repos (4 projects had them; their history
remains in `~/Android/` originals), `__pycache__`. Non-watchface apps (§3).

## 13. Security & secret-scan results

No `*.jks/*.keystore/*.p12/*.pepk/keystore.properties` anywhere; no
`signingConfig` in any Gradle file; all APKs debug-signed; `.gitignore`
blocks key formats going forward; validate.py enforces on every run.
`git diff --check` clean.

## 14. Licensing / attribution findings

**Corrected in the review pass (see §21):** the original claim here that no
embedded TTF/OTF fonts existed was wrong. The verified audit found **27
tracked OFL-1.1 font files (8 upstream font projects) + 1 CC0 HDRI**, all now
inventoried in `docs/asset-licenses.json` with per-file SHA-256 and embedded
copyright metadata, with OFL notice texts in `THIRD_PARTY_NOTICES/fonts/`.
The repository now carries a proprietary `LICENSE` (owner decision). Art is
locally AI-generated from owner prompts/donors; model-license check remains
flagged before commercial sale. Details: `docs/LICENSING.md`.

## 15. Decisions made (ADRs)

- ADR-005: AGENOR-Horology stays a sibling repo; no empty `engine/` scaffold.
- ADR-006: `releases/<slug>/current|vX.Y.Z/` layout; existing APKs stay
  tracked; future binaries also go to GitHub Releases.
- ADR-007: commit Gradle wrappers; normalize only project-internal paths in
  Phase 1; external donor paths documented, not rewritten.

## 16. Deviations from CHATGPT_ARCHITECT.md

- Ledger §5 proposes `engine/`, `tests/`, `previews/`, `assets/` top-level
  dirs → deferred (no real content yet; empty dirs misrepresent maturity).
  Ledger §5 itself says to adapt rather than copy blindly.
- Ledger style-guide docs (MATERIAL_SYSTEM, ANIMATION_SYSTEM, per-language
  style guides) → not written this phase; equivalents exist in the sibling
  asset repo and will migrate when the engine layer lands (Phase 2).

## 17. Technical debt

Per-face duplicated WFF patterns (no engine layer yet) · generator scripts
depend on external donors for regeneration · previews missing for 4 releases ·
no CHANGELOG.md yet · bone-watch creatively rejected but kept · battery impact
unmeasured · single-device testing only · `docs/watchfaces/` per-face deep
docs not yet written (per-face READMEs + BUILDLOGs cover the essentials).

## 18. Risks

- Debug signing only: installed faces are wiped if a differently-signed build
  replaces them; store distribution impossible until a keystore decision.
- AI-model licensing for commercial sale unverified (§14).
- 79 MB repo (APKs + art in git): fine now; watch growth (ADR-006 threshold).
- tripface is WFF v2 — divergent from the v4 baseline; upgrade or freeze.

## 19. Recommended Phase 2

Per ledger P2/P3 backlog and ADR-003: pick **one reference face** (suggest
`aurelius` — richest bindings: HR balance, battery reserve, tourbillon
sprite) and (1) regenerate its missing release preview, (2) extract the first
shared engine pieces (chapter-ring/AOD/HR-binding XML patterns + shared
Python sprite tooling) against it, (3) define the asset lifecycle
(experimental→approved), (4) add a CHANGELOG and cut a v1.0.1 release through
the new `package_release.sh` path end-to-end, (5) owner decisions: license,
release keystore, bone-watch fate.

## 20. Git branch and commits

Branch `phase-1/repository-normalization` off `main` (`b740207`):

1. `814a168` — audit and repository hygiene
2. `b54f81b` — release artifact normalization
3. `be4f8ea` — import editable source for all 10 watchfaces
4. `aa2beba` — build and validation tooling
5. (this commit) — documentation and architecture-ledger update

---

## 21. Review corrections (post-review pass, 2026-07-24)

ChatGPT review (`PHASE_1_CHATGPT_REVIEW.md`, commit `4b39658`) returned
CHANGES REQUESTED with two merge blockers. Both are corrected on this branch:

**Blocker 1 — licensing.** The §14 "no fonts" claim was false: 27 OFL-1.1
font files across 8 upstream projects (Orbitron, Marcellus, Marcellus SC,
Rajdhani, Chakra Petch, Metamorphous, Pirata One, UnifrakturCook) plus the
Poly Haven `studio_small_08` CC0 HDRI are tracked. Every file's embedded
name-table copyright/license metadata was parsed from the committed bytes and
recorded in `docs/asset-licenses.json` (SHA-256 per file); canonical OFL.txt
notices fetched per family into `THIRD_PARTY_NOTICES/fonts/`. `validate.py`
now ERRORs on any tracked font/HDRI/EXR without a byte-matching inventory
entry, on missing license ids/permission flags, on missing required notices,
and on stale entries — negatively tested (fixtures T8/T9).

**Blocker 2 — release tooling.** `MANIFEST.json` moved to schema 2 (nested
face → channels; identity = (slug, channel), duplicates rejected).
`package_release.py` replaces `package_release.sh`: archives `current` to the
immutable `v<old>` before replacement, refuses same-version and
archive-overwrite without explicit destructive flags, verifies built-APK
metadata against source Gradle via aapt2, and fails on zero or ambiguous
previews across `drawable*`. `validate.py` now inspects every released APK
directly with aapt2 (package/versionCode/versionName/targetSdk) against both
manifest and source. Proven end-to-end by `tools/test_release_workflow.py`
(10 fixtures: T1–T10, all PASS — including a real sandboxed Gradle rebuild at
a bumped version and byte-identical archive verification).

Owner decisions applied: ADR-005 ratified; repository proprietary (LICENSE);
bone-watch archived/creative-rejected; tripface frozen (legacy WFF v2);
no keystore created. Non-blocking recommendations implemented: CI workflow
(first Actions run pending), README "primarily WFF v4" wording, aapt2 in
check_prereqs, mktemp build logs. Re-verification: all 10 faces rebuilt PASS;
validate.py 0 errors. Correction commits are listed in the review file's
resolution section.
