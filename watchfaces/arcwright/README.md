# ARCWRIGHT (`com.xsytrance.arcwright`, WFF v4) — experimental, unreleased

Early experimental face, v0.0.1. Builds, but has had no recent design work.
No release artifact exists.

## Build & install

```bash
# from repo root
tools/build_face.sh arcwright          # or: cd watchfaces/arcwright && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
