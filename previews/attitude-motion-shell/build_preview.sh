#!/bin/bash
# ATTITUDE motion PREVIEW shell. Debug APKs only, never a bundle.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
export JAVA_HOME="${JAVA_HOME:-$HOME/Android/android-studio/jbr}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
[ -f "$DIR/local.properties" ] || echo "sdk.dir=$ANDROID_HOME" > "$DIR/local.properties"
cd "$DIR"
./gradlew --console=plain -q \
    assembleDampedDebug assembleProposedDebug assembleAssertiveDebug
OUT="$DIR/dist"; mkdir -p "$OUT"
echo
for f in damped proposed assertive; do
  SRC="$DIR/app/build/outputs/apk/$f/debug/app-$f-debug.apk"
  DST="$OUT/attitude-preview-$f-debug.apk"
  [ -f "$SRC" ] || { echo "MISSING $f"; exit 1; }
  cp "$SRC" "$DST"
  printf '%-10s %10d B  %s\n' "$f" "$(stat -c%s "$DST")" "$(sha256sum "$DST" | cut -d' ' -f1)"
done
if find "$DIR" -name '*.aab' | grep -q .; then
  echo "ERROR: an AAB was produced" >&2; exit 1
fi
echo "no AAB produced"
