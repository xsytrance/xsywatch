# CHRONOVA

*A miniature alien engine under the glass.* Watch Face Format v4 face for
Galaxy Watch7 (Wear OS 6) — internal engine codename **Xenochron Engine**
(`com.xsytrance.xenochronengine`).

Blue machinery left drives the HOURS display; magenta right drives MINUTES; a
violet feed drives SEC at the bottom; a breathing plasma reactor sits at the
heart with counter-rotating containment rings, staggered energy packets, a 6s
radial pulse, and a sub-second synchronization surge at every minute boundary.
27 independently animated mechanical groups; exact 60-position perimeter scale.

## Build

```bash
python scripts/generate_assets.py   # PIL baseline: glows, panels, outer scale (needs Pillow + numpy)
~/Android/blender/blender-4.5.11-linux-x64/blender -b -noaudio \
    --python scripts/render_blender_layers.py   # photoreal metal ON TOP (order matters!)
python scripts/gen_watchface.py
gradle :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId com.xsytrance.xenochronengine
```

## Docs
- `docs/ARCHITECTURE.md` — pipeline, z-stack, WFF rules learned the hard way
- `docs/ASSET_MAP.md` / `docs/ANIMATION_MAP.md` — generated, always current
- `docs/BUILD_LOG.md` — session-by-session record
- `docs/HANDOFF.md` — deferred phases (gyro, taps, complications, flavors, AOD)

Reference art: `reference/xenochron-engine-concept.png` (visual target; never
modified, never shipped on-face — the physical watch provides bezel and case).

---

## Repository integration (Phase 1, 2026-07-24)

- Status: **experimental, unreleased** — no APK in `releases/`.
- Build from repo root: `tools/build_face.sh chronova`
  (or `cd watchfaces/chronova && JAVA_HOME=<jdk21> ./gradlew assembleDebug`).
- Asset pipeline additionally uses Blender (`scripts/render_blender_layers.py`);
  committed `res/drawable*` art is canonical — regeneration optional.
