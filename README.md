# AGENOR Horology Engine — xsywatch

Canonical source repository for the **AGENOR watchface ecosystem**: premium
watch faces for **Samsung Galaxy Watch7 (44 mm, 480×480 round AMOLED)** built
primarily on the Wear OS **Watch Face Format (WFF) v4** (one legacy
WFF v2 face: tripface) with a fully Linux-native, free
toolchain.

> Architecture ledger (authoritative): [`docs/CHATGPT_ARCHITECT.md`](docs/CHATGPT_ARCHITECT.md)
> Current phase report: [`docs/reports/PHASE_1_REPOSITORY_NORMALIZATION.md`](docs/reports/PHASE_1_REPOSITORY_NORMALIZATION.md)

## Watchfaces

| Face | Slug | Package | Design language | Released APK | Source |
|------|------|---------|-----------------|:---:|:---:|
| BUSHIDO | `bushido` | com.xsytrance.bushido | cyberpunk-samurai | ✔ | ✔ |
| ARES War God | `ares-wargod` | com.xsytrance.ares | mythological (carved marble) | ✔ | ✔ |
| Aurelius "Field Tourbillon" | `aurelius` | com.xsytrance.aurelius | military skeleton horology | ✔ | ✔ |
| Bone Watch (archived) | `bone-watch` | com.xsytrance.bonewatch | gothic memento-mori | ✔ | ✔ |
| HellForge | `hellforge` | com.xsytrance.hellforge | war/occult demon-forge | ✔ | ✔ |
| Pinball | `pinball` | com.xsytrance.pinball | retro-arcade 3D pinball | ✔ | ✔ |
| PulseFace | `pulseface` | com.xsytrance.pulseface | (see face README) | ✔ | ✔ |
| Arcwright | `arcwright` | com.xsytrance.arcwright | experimental (v0.0.1) | — | ✔ |
| Chronova | `chronova` | com.xsytrance.xenochronengine | experimental (v0.1) | — | ✔ |
| TripFace (frozen, WFF v2) | `tripface` | com.xsytrance.tripface | legacy experimental | — | ✔ |

Full inventory with status detail: [`docs/WATCHFACE_INVENTORY.md`](docs/WATCHFACE_INVENTORY.md)

## Repository structure

```
docs/                architecture ledger, guides, ADRs, phase reports
watchfaces/<slug>/   one complete editable WFF project per face
                     (Gradle + app/src/main/res/raw/watchface.xml + tools/)
tools/               cross-face build / validate / release scripts
releases/<slug>/     released APK + preview + metadata (+ MANIFEST.json index)
```

There is intentionally **no `engine/` directory yet** — shared-code extraction
is Phase 2, and empty scaffolding is worse than none (see ADR-005). The 3D
asset pipeline (Blender/Material Maker library) lives in the sibling repository
[`AGENOR-Horology`](https://github.com/xsytrance/AGENOR-Horology).

## Toolchain (Linux-native, all free)

| Tool | Version | Notes |
|------|---------|-------|
| JDK | 21 (Android Studio JBR) | `~/Android/android-studio/jbr` or any JDK 21 |
| Gradle | 9.6.1 via wrapper | each face ships `./gradlew` — no global install needed |
| Android SDK | compileSdk 36, build-tools 36.0.0, platform-tools 37 | set `sdk.dir` in `local.properties` or `ANDROID_HOME` |
| Python | 3.x + Pillow | asset-generation scripts (`watchfaces/<slug>/tools/`) |
| WFF validator | Google `watchface` validator | see `docs/BUILD_AND_RELEASE.md` |

**Samsung Watch Face Studio is NOT required or used.** It has no Linux build
(Windows/macOS only, verified 2026-07); all faces here are hand-authored WFF
XML. This is a deliberate, documented decision (ledger ADR-004).

## Build

```bash
tools/check_prereqs.sh              # verify JDK/SDK/python are usable
tools/build_face.sh bushido         # build one face  -> app/build/outputs/apk/debug/
tools/build_all.sh                  # build every face, summary table at the end
python3 tools/validate.py           # repo-wide validation (source, releases, APK metadata via aapt2, licenses)
```

## Install on Galaxy Watch7

1. On the watch: Settings → About watch → Software → tap **Build number** ×5
   → back → Developer options → enable **Wireless debugging**.
2. On the workstation (same Wi-Fi):
   ```bash
   adb pair <watch-ip>:<pairing-port>    # code shown on watch
   adb connect <watch-ip>:<port>
   adb install -r releases/bushido/current/bushido.apk
   ```
3. Long-press the current watch face → pick the new face.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) — branch/commit conventions, the
face-project layout contract, validation gates, and the release process
(`docs/BUILD_AND_RELEASE.md`).

## Status (2026-07-24)

Phase 1 (repository normalization) complete: all 10 face source projects
imported, 7 released APKs preserved under `releases/` with checksums and
manifests, builds reproduced from clean source via Gradle wrapper, repo-wide
validation in place. Known gaps are tracked in
[`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md).
