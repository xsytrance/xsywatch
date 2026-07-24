#!/bin/bash
# Build every watchface; print a PASS/FAIL table; exit 1 if any fail.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
declare -A RESULT
rc=0
for d in "$ROOT"/watchfaces/*/; do
  slug="$(basename "$d")"
  if "$ROOT/tools/build_face.sh" "$slug" >/tmp/agenor-build-$slug.log 2>&1; then
    RESULT[$slug]=PASS
  else
    RESULT[$slug]="FAIL (log: /tmp/agenor-build-$slug.log)"; rc=1
  fi
  printf '%-14s %s\n' "$slug" "${RESULT[$slug]}"
done
exit $rc
