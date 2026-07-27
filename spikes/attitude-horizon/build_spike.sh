#!/bin/bash
# DISPOSABLE SPIKE build. Debug APKs only, never a bundle.
#   spikes/attitude-horizon/build_spike.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
export JAVA_HOME="${JAVA_HOME:-$HOME/Android/android-studio/jbr}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
[ -f "$DIR/local.properties" ] || echo "sdk.dir=$ANDROID_HOME" > "$DIR/local.properties"
cd "$DIR"
# assemble<Flavour>Debug only. `bundle` tasks are deliberately never invoked.
./gradlew --console=plain -q \
    assembleDampedDebug assembleProposedDebug assembleAssertiveDebug
echo
for f in damped proposed assertive; do
  APK="$DIR/app/build/outputs/apk/$f/debug/app-$f-debug.apk"
  if [ -f "$APK" ]; then
    printf '%-10s %10d B  %s\n' "$f" "$(stat -c%s "$APK")" "$(sha256sum "$APK" | cut -d' ' -f1)"
  else
    echo "MISSING $f"; exit 1
  fi
done
if find "$DIR" -name '*.aab' | grep -q .; then
  echo "ERROR: an AAB was produced; the spike must not create one" >&2; exit 1
fi
echo "no AAB produced"
