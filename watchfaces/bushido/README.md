# X1c7 BUSHIDO (`com.xsytrance.bushido`, WFF v4)

Cyberpunk-samurai face for Galaxy Watch7 44 mm. Wrist-raise ambient-transition
reveal (needs Wear OS 6 / One UI 8 Watch). Full engineering history in
[BUILDLOG.md](BUILDLOG.md). Released: `releases/bushido/`.

## Build & install

```bash
# from repo root
tools/build_face.sh bushido          # or: cd watchfaces/bushido && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
