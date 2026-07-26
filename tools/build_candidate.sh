#!/bin/bash
# Build and VERIFY the Aurelius release-candidate artifacts.
#
#   tools/build_candidate.sh [--clean] [--out DIR]
#
# Produces a Wear OS App Bundle for distribution and a debug APK for
# physical device testing, then runs tools/verify_candidate.py and FAILS
# the build if verification fails. Verification is not an optional step a
# later human might remember to run: an unverified artifact is not a
# candidate.
#
# Google Play requires a Wear OS app BUNDLE (.aab) for watch faces
# (support.google.com/googleplay/android-developer/answer/13560201,
# checked 2026-07-26). The debug APK is the sideload/device-test artifact,
# not the distribution artifact.
#
# The release dex is removed only after tools/dex_guard.py proves every
# class in it is a generated R class (fail-closed). The gate runs inside
# the Gradle build and its report is passed to the verifier as evidence.
#
# No production signing material is created or used. The bundle is built
# unsigned: Play App Signing holds the app signing key, and the
# developer-held upload key is a separate, later, explicitly authorised
# operation (ADR-010 §5).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FACE_DIR="$ROOT/watchfaces/aurelius"
OUT=""
CLEAN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --clean) CLEAN=1; shift ;;
        --out) OUT="$2"; shift 2 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

: "${ANDROID_HOME:=${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"
: "${JAVA_HOME:=$HOME/jdk}"
export JAVA_HOME PATH="$JAVA_HOME/bin:$PATH"

VERSION="$(grep -oE 'versionName = "[^"]+"' "$FACE_DIR/app/build.gradle.kts" \
           | head -1 | sed 's/.*"\(.*\)"/\1/')"
[ -n "$VERSION" ] || { echo "could not read versionName" >&2; exit 1; }
echo "== candidate version: $VERSION =="

cd "$FACE_DIR"
if [ "$CLEAN" -eq 1 ]; then
    echo "== clean =="
    ./gradlew --quiet --no-daemon clean >/dev/null 2>&1 || true
    rm -rf build app/build
fi

echo "== bundleRelease (.aab) — dex gate runs inside this =="
./gradlew --no-daemon --quiet bundleRelease

echo "== assembleDebug (.apk, device testing) =="
./gradlew --no-daemon --quiet assembleDebug

AAB="$(find app/build/outputs/bundle -name '*.aab' | head -1)"
APK="app/build/outputs/apk/debug/app-debug.apk"
DEX_REPORT="app/build/outputs/dex_gate.json"
[ -f "$AAB" ] || { echo "no .aab produced" >&2; exit 1; }
[ -f "$APK" ] || { echo "no debug .apk produced" >&2; exit 1; }
[ -f "$DEX_REPORT" ] || {
    echo "no dex-gate report at $DEX_REPORT — the fail-closed gate did not run" >&2
    exit 1
}

echo
echo "aab: $(sha256sum "$AAB" | cut -d' ' -f1)  $(stat -c%s "$AAB") bytes"
echo "apk: $(sha256sum "$APK" | cut -d' ' -f1)  $(stat -c%s "$APK") bytes"

if [ -n "$OUT" ]; then
    mkdir -p "$OUT"
    cp "$AAB" "$OUT/aurelius-$VERSION.aab"
    cp "$APK" "$OUT/aurelius-$VERSION-debug.apk"
    cp "$DEX_REPORT" "$OUT/dex_gate.json"
    echo "copied to $OUT"
    VAAB="$OUT/aurelius-$VERSION.aab"
    VAPK="$OUT/aurelius-$VERSION-debug.apk"
    VDEX="$OUT/dex_gate.json"
else
    VAAB="$FACE_DIR/$AAB"
    VAPK="$FACE_DIR/$APK"
    VDEX="$FACE_DIR/$DEX_REPORT"
fi

echo
echo "== verify (build fails if this fails) =="
cd "$ROOT"
python3 tools/verify_candidate.py aurelius --version "$VERSION" \
    --aab "$VAAB" --apk "$VAPK" --dex-report "$VDEX"
echo "== candidate $VERSION built and verified =="
