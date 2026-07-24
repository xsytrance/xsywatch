# ARES (`com.xsytrance.ares`, WFF v4)

Carved-marble god-of-war face: sculptural relief dial with BitmapFont time
(custom TTFs don't render in WFF on Watch7 — pre-rendered glyphs instead).
Released: `releases/ares-wargod/`.

## Build & install

```bash
# from repo root
tools/build_face.sh ares-wargod          # or: cd watchfaces/ares-wargod && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
