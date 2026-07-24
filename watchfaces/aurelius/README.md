# AURELIUS "Field Tourbillon" (`com.xsytrance.aurelius`, WFF v4)

Cel-shaded olive-drab military skeleton with WW1 wood-propeller bridge.
Tourbillon cage = seconds, balance wheel oscillates with live heart rate,
battery = power-reserve gauge. Owner has flagged a future remix.
Multiple design iterations preserved in `tools/` (cel_v3, photoreal_v2,
warbird_v4). Released: `releases/aurelius/` (current release pinned
immutable).

**Engine-managed since Phase 2:** `engine/face.toml` is the authoritative
source; the committed `res/raw/watchface.xml` is generated
(`python3 tools/generate_face.py aurelius`, `--check` in CI). Semantic
parity with the Phase-1 release is regression-tested
(tests/engine/test_aurelius_parity.py). Do not hand-edit the XML.

## Build & install

```bash
# from repo root
tools/build_face.sh aurelius          # or: cd watchfaces/aurelius && JAVA_HOME=<jdk21> ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Validate the WFF XML and repo state: `docs/BUILD_AND_RELEASE.md`.

## Asset provenance

Committed `res/drawable*` art is canonical. Generator scripts live in
`tools/` (paths are repo-relative as of Phase 1); some reference external
AI-generation donor images outside the repo — regeneration is optional, the
build never requires it.
