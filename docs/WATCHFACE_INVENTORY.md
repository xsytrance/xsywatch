# Watchface Inventory

Verified against local source and APK metadata on 2026-07-24
(aapt2 36.0.0 dump of each APK; Gradle config of each project).
All faces: WFF v4 (exception: `tripface` is WFF v2), target Galaxy Watch7
44 mm (480×480), targetSdk 36, debug-signed, versionCode 1.

## Released (source + APK)

| Slug | Display name | Package | versionName | Release preview | Design language |
|------|--------------|---------|------------|:---:|-----------------|
| `bushido` | X1c7 BUSHIDO | com.xsytrance.bushido | 1.0 | ✔ (jpg) | cyberpunk-samurai; wrist-raise reveal |
| `ares-wargod` | ARES | com.xsytrance.ares | 1.0 | — | mythological; carved-marble god of war |
| `aurelius` | AURELIUS | com.xsytrance.aurelius | 1.0 | ✔ | military skeleton "Field Tourbillon"; cage = seconds, HR balance, battery reserve — **engine-managed (Phase 2 reference face)** |
| `bone-watch` | BONE | com.xsytrance.bonewatch | 1.0 | — | gothic memento-mori skull; HR-pulsing eye ember — **ARCHIVED/creative-rejected (owner decision)** |
| `hellforge` | HELLFORGE | com.xsytrance.hellforge | 1.0 | — | war/occult demon-skull forge, heavily animated |
| `pinball` | PINBALL | com.xsytrance.pinball | 1.0 | — | 3D pinball; DMD score-display time, ricocheting ball |
| `pulseface` | XSY PULSE | com.xsytrance.pulseface | 1.0 | ✔ | pulse/heart-rate–centric (see face README) |

## Unreleased source (no APK in `releases/`)

| Slug | Display name | Package | versionName | Status |
|------|--------------|---------|------------|--------|
| `arcwright` | ARCWRIGHT | com.xsytrance.arcwright | 0.0.1 | early experimental |
| `chronova` | CHRONOVA | com.xsytrance.xenochronengine | 0.1 | experimental ("xenochron engine") |
| `tripface` | XSYTRANCE Trip | com.xsytrance.tripface | 1.0 | **FROZEN** legacy experimental (WFF v2, owner decision) |

## The "eighth face" discrepancy — resolved

Commit `d8ed43b` ("Add watch face APK releases and previews") says **eight**
faces but lists — and contains — exactly **seven** APKs. Conclusion after
auditing every local project: **the commit message miscounted; no APK is
missing.** All seven APKs map 1:1 to local source projects (package names
verified). The three unreleased projects above were never built for release
and are now imported as source-only faces.

## Excluded local projects (not watch faces)

`HermesApproval`, `PrimeBeaconWear`, `WearComposeLaunchpad` — Wear OS apps,
not WFF watch faces; out of scope for this repository.

## Related repository

`AGENOR-Horology` (github.com/xsytrance/AGENOR-Horology) — the 3D asset
pipeline (Blender/Material Maker library, render/sprite tooling, AlienMilitary
spec). Kept as a sibling repo; see ADR-005.
