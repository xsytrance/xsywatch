#!/bin/bash
# Build a controlled permission variant of the Aurelius candidate, for the
# on-device comparison described in docs/reports/PHASE_4_PERMISSION_INVESTIGATION.md.
#
#   tools/build_permission_variant.sh READ_HEART_RATE
#   tools/build_permission_variant.sh none
#
# Variant A ("none") is what the candidate ships: no sensor or health
# permission at all. Variant B ("READ_HEART_RATE") adds the granular
# android.permission.health.READ_HEART_RATE declaration that Wear OS 6
# uses in place of the legacy BODY_SENSORS.
#
# The variant is written to a scratch output directory and the manifest is
# ALWAYS restored, so this can never leave the candidate source modified.
set -euo pipefail

VARIANT="${1:?usage: build_permission_variant.sh READ_HEART_RATE|none}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAN="$ROOT/watchfaces/aurelius/app/src/main/AndroidManifest.xml"
OUT="${2:-$ROOT/build/permission-variants/$VARIANT}"
BACKUP="$(mktemp)"

cleanup() { cp "$BACKUP" "$MAN"; rm -f "$BACKUP"; }
trap cleanup EXIT

cp "$MAN" "$BACKUP"

case "$VARIANT" in
    none)
        echo "== variant A: no sensor/health permission (as shipped) ==" ;;
    READ_HEART_RATE)
        echo "== variant B: android.permission.health.READ_HEART_RATE =="
        python3 - "$MAN" <<'PY'
import sys, re
p = sys.argv[1]
s = open(p).read()
perm = ('    <uses-permission '
        'android:name="android.permission.health.READ_HEART_RATE" />\n\n')
s = s.replace("    <application", perm + "    <application", 1)
open(p, "w").write(s)
print("   injected READ_HEART_RATE")
PY
        ;;
    *) echo "unknown variant: $VARIANT" >&2; exit 2 ;;
esac

mkdir -p "$OUT"
bash "$ROOT/tools/build_candidate.sh" --clean --out "$OUT"
echo
echo "variant '$VARIANT' artifacts in $OUT"
echo "manifest restored to the committed state"
