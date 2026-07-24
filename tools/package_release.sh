#!/bin/bash
# Package a built face into releases/<slug>/current/ and refresh manifests.
# Usage: tools/package_release.sh <slug>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="${1:?usage: package_release.sh <slug>}"
APK="$ROOT/watchfaces/$SLUG/app/build/outputs/apk/debug/app-debug.apk"
[ -f "$APK" ] || { echo "no built APK — run tools/build_face.sh $SLUG first"; exit 1; }
DEST="$ROOT/releases/$SLUG/current"
mkdir -p "$DEST"
cp "$APK" "$DEST/$SLUG.apk"
PREV="$ROOT/watchfaces/$SLUG/app/src/main/res/drawable/preview.png"
[ -f "$PREV" ] && cp "$PREV" "$DEST/preview.png" || echo "WARN: no source preview.png found"
python3 "$ROOT/tools/gen_release_manifest.py"
echo "packaged $SLUG -> ${DEST#$ROOT/} — review RELEASE.md, set source commit, then commit"
