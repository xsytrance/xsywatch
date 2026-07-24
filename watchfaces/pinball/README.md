# PINBALL (`com.xsytrance.pinball`, WFF v4)

3D pinball playfield: orange DMD dot-matrix score-display shows the time,
ricocheting chrome ball, flashing pop-bumpers. Released: `releases/pinball/`.

## Build & install

```bash
# from repo root
tools/build_face.sh pinball          # or: cd watchfaces/pinball && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
