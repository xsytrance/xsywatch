#!/bin/bash
# Verify the machine can build AGENOR watchfaces. Exit 0 = ready.
set -u
fail=0
say() { printf '%-28s %s\n' "$1" "$2"; }

# JDK 21
JH="${JAVA_HOME:-$HOME/Android/android-studio/jbr}"
if "$JH/bin/java" -version 2>&1 | grep -q 'version "21'; then
  say "JDK 21" "OK ($JH)"
else
  say "JDK 21" "MISSING — set JAVA_HOME to a JDK 21 (e.g. Android Studio jbr)"; fail=1
fi

# Android SDK
SDK="${ANDROID_HOME:-$HOME/Android/Sdk}"
if [ -d "$SDK/platforms" ] && ls "$SDK/build-tools" >/dev/null 2>&1; then
  say "Android SDK" "OK ($SDK, build-tools: $(ls "$SDK/build-tools" | sort -V | tail -1))"
else
  say "Android SDK" "MISSING — install SDK w/ platform 36 + build-tools, set ANDROID_HOME"; fail=1
fi
[ -x "$SDK/platform-tools/adb" ] && say "adb" "OK" || { say "adb" "MISSING (platform-tools)"; fail=1; }

# Python + Pillow (asset tools only — not needed for plain builds)
if python3 -c 'import PIL' 2>/dev/null; then say "python3+Pillow" "OK"; else say "python3+Pillow" "missing (only needed for asset regeneration)"; fi

# network or cached gradle deps
[ -d "$HOME/.gradle" ] && say "gradle cache" "present" || say "gradle cache" "cold (first build downloads deps)"

exit $fail
