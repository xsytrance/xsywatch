# HELLFORGE (`com.xsytrance.hellforge`, WFF v4)

War/occult demon-skull forge face — bone + metal + fire + black-magic red,
heavily animated. Released: `releases/hellforge/`.

## Build & install

```bash
# from repo root
tools/build_face.sh hellforge          # or: cd watchfaces/hellforge && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
