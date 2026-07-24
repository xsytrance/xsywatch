#!/bin/bash
# Build one watchface: tools/build_face.sh <slug> [gradle-task]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="${1:?usage: build_face.sh <slug> [task]}"
TASK="${2:-assembleDebug}"
DIR="$ROOT/watchfaces/$SLUG"
[ -d "$DIR" ] || { echo "unknown face '$SLUG'; available:"; ls "$ROOT/watchfaces"; exit 1; }

export JAVA_HOME="${JAVA_HOME:-$HOME/Android/android-studio/jbr}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
# generate machine-local SDK pointer if absent (git-ignored)
[ -f "$DIR/local.properties" ] || echo "sdk.dir=$ANDROID_HOME" > "$DIR/local.properties"

cd "$DIR"
./gradlew --console=plain -q "$TASK"
APK="$DIR/app/build/outputs/apk/debug/app-debug.apk"
[ -f "$APK" ] && echo "BUILT $SLUG -> ${APK#$ROOT/}" || { echo "BUILD FAILED for $SLUG (no APK)"; exit 1; }
