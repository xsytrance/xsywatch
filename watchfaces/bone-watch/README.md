# BONE (`com.xsytrance.bonewatch`, WFF v4)

Gothic memento-mori skull dial (ComfyUI-generated), heart-rate-pulsing eye
ember. **Creatively rejected by the owner** — source retained for parts
reuse. Released APK preserved: `releases/bone-watch/`.

## Build & install

```bash
# from repo root
tools/build_face.sh bone-watch          # or: cd watchfaces/bone-watch && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
