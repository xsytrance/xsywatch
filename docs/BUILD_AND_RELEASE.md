# Build & Release Guide

## Toolchain

| Component | Version | Where |
|-----------|---------|-------|
| JDK | 21 (OpenJDK / Android Studio JBR 21.0.10) | `~/Android/android-studio/jbr` or system JDK 21 |
| Gradle | 9.6.1 (via committed wrapper) | `watchfaces/<slug>/gradlew` |
| Android SDK | compileSdk 36, build-tools 36.0.0, platform-tools 37.0.0 | `ANDROID_HOME` / `local.properties` |
| Kotlin/AGP | as pinned in each face's `build.gradle.kts` | — |
| Python 3 + Pillow | asset generation | system python3 |
| adb | 37.0.0 | `$ANDROID_HOME/platform-tools` |

First-time machine setup:

```bash
tools/check_prereqs.sh     # tells you exactly what's missing
```

Each face reads the SDK location from (in order) `local.properties`
(git-ignored, machine-specific) or the `ANDROID_HOME` environment variable.
`tools/build_face.sh` generates `local.properties` automatically from
`ANDROID_HOME` when missing.

## Building

```bash
tools/build_face.sh <slug>         # one face → watchfaces/<slug>/app/build/outputs/apk/debug/app-debug.apk
tools/build_all.sh                 # all faces; prints PASS/FAIL table; exit 1 on any failure
```

Direct Gradle, if you prefer:

```bash
cd watchfaces/<slug>
JAVA_HOME=~/Android/android-studio/jbr ./gradlew assembleDebug
```

### Asset regeneration (optional, per-face)

Faces with generated art ship a `tools/build.py`. These scripts regenerate
res/drawable layers from source/donor images. Some donors are **external
provenance** (AI-generated intermediates outside the repo, documented per-face
in its README) — the committed drawables are the canonical result, so a clean
clone builds without regenerating anything.

## WFF validation

Google's official WFF validator (memory-note: built offline previously):

```bash
# validator jar: see https://github.com/google/watchface — dwf-format-2-validator
java -jar wff-validator.jar 4 watchfaces/<slug>/app/src/main/res/raw/watchface.xml
```

Repo-wide structural validation (source presence, metadata, releases,
duplicate package IDs, oversized assets, absolute paths, secrets):

```bash
python3 tools/validate.py          # exit 0 = clean; issues listed with severity
```

## Installing on Galaxy Watch7

```bash
adb pair <ip>:<pairing-port>       # once; code shown on watch
adb connect <ip>:<port>
adb install -r <apk>
```

Watch-side: Developer options + Wireless debugging must be enabled. After
install, long-press the active face to select the new one. For faces using
health data (HR), grant Sensors permission on first run.

## Release process

1. Bump `versionCode` (integer, monotonic) and `versionName` (semver) in
   `watchfaces/<slug>/app/build.gradle.kts`.
2. `tools/build_face.sh <slug>` — build must succeed from clean source.
3. Validate: WFF validator + `tools/validate.py` + on-device sanity
   (normal mode, AOD, complications, one full minute-sweep).
4. `tools/package_release.sh <slug>` — copies the APK + preview into
   `releases/<slug>/current/`, writes `RELEASE.md` metadata (checksum, date,
   source commit), regenerates `releases/MANIFEST.json`.
5. Commit with `release(<slug>): vX.Y.Z (versionCode N)`.
6. Optionally attach the APK to a versioned GitHub Release (preferred for
   large/history-heavy artifacts — ledger §5 release policy).

### Versioning rules

- `versionCode`: monotonically increasing integer per face, never reused.
- `versionName`: semver `MAJOR.MINOR.PATCH`; visual redesign = MAJOR,
  new complication/animation = MINOR, fixes/tuning = PATCH.
- Released APK filename: `releases/<slug>/current/<slug>.apk` (history moves
  to `releases/<slug>/vX.Y.Z/` when superseded).

## Signing status

All current APKs are **debug-signed** (sideload-only). No release keystore
exists yet; creating one is a Phase-2+ decision and the keystore must live
outside the repository (`.gitignore` already blocks common key formats).
