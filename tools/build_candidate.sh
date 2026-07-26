#!/bin/bash
# Build the Aurelius release-candidate artifacts: a Wear OS App Bundle for
# distribution and a debug APK for physical device testing.
#
#   tools/build_candidate.sh [--clean] [--out DIR]
#
# Google Play requires a Wear OS app BUNDLE (.aab) for watch faces
# (support.google.com/googleplay/android-developer/answer/13560201,
# checked 2026-07-26). The debug APK remains the sideload/device-test
# artifact; it is NOT the distribution artifact.
#
# No production signing material is created or used. The bundle is built
# unsigned-for-upload: Play App Signing holds the app signing key and the
# developer-held upload key is a separate, later, explicitly authorised
# operation (ADR-010 §5).
set -euo pipefail

FACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/watchfaces/aurelius"
OUT=""
CLEAN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --clean) CLEAN=1; shift ;;
        --out) OUT="$2"; shift 2 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

: "${JAVA_HOME:?set JAVA_HOME (JDK 21)}"
: "${ANDROID_HOME:?set ANDROID_HOME}"
export PATH="$JAVA_HOME/bin:$PATH"

cd "$FACE_DIR"
if [ "$CLEAN" -eq 1 ]; then
    echo "== clean =="
    ./gradlew --quiet --no-daemon clean
    rm -rf build app/build
fi

echo "== bundleRelease (.aab) =="
./gradlew --no-daemon --quiet bundleRelease

echo "== assembleDebug (.apk, device testing) =="
./gradlew --no-daemon --quiet assembleDebug

AAB="$(find app/build/outputs/bundle -name '*.aab' | head -1)"
APK="app/build/outputs/apk/debug/app-debug.apk"
[ -f "$AAB" ] || { echo "no .aab produced" >&2; exit 1; }
[ -f "$APK" ] || { echo "no debug .apk produced" >&2; exit 1; }

echo
echo "aab: $(sha256sum "$AAB" | cut -d' ' -f1)  $(stat -c%s "$AAB") bytes  $AAB"
echo "apk: $(sha256sum "$APK" | cut -d' ' -f1)  $(stat -c%s "$APK") bytes  $APK"

if [ -n "$OUT" ]; then
    mkdir -p "$OUT"
    cp "$AAB" "$OUT/aurelius-2.0.0-rc1.aab"
    cp "$APK" "$OUT/aurelius-2.0.0-rc1-debug.apk"
    echo "copied to $OUT"
fi
