#!/bin/bash
# Run Google's official WFF validator (google/watchface) against a watchface
# XML file.  Usage: tools/wff_validate.sh <wff-version> <watchface.xml>
#
# The validator jar is built once into ~/Applications/wff-validator/ from a
# clone of https://github.com/google/watchface (third_party/wff/specification/
# validator, deps bundled in libs/, XSD 1.1 via Xerces). Build recipe:
#   javac -cp "libs/*" -d classes $(find src -name '*.java')
#   (cd specification/documents && zip -r classes/docs.zip .)
#   jar cfm wff-validator.jar <manifest with Version:> -C classes .
# If the jar is missing this script fails with instructions rather than
# silently skipping validation.
set -euo pipefail
VER="${1:?usage: wff_validate.sh <wff-version> <watchface.xml>}"
XML="${2:?usage: wff_validate.sh <wff-version> <watchface.xml>}"
INSTALL="${WFF_VALIDATOR_HOME:-$HOME/Applications/wff-validator}"
JAVA="${JAVA_HOME:-$HOME/Android/android-studio/jbr}/bin/java"

if [ ! -f "$INSTALL/wff-validator.jar" ]; then
    echo "ERROR: $INSTALL/wff-validator.jar not found." >&2
    echo "Build it from https://github.com/google/watchface (see header of this script)." >&2
    exit 2
fi
exec "$JAVA" -cp "$INSTALL/wff-validator.jar:$INSTALL/libs/*" \
    com.samsung.watchface.DWFValidationApplication "$VER" "$XML"
