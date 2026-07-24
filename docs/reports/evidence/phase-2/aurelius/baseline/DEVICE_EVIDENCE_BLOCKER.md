# Baseline physical-device evidence — BLOCKED (disclosed per brief §4.9)

**Date:** 2026-07-24
**Requirement:** Phase 2 brief §4.1.4 — normal/AOD screenshots, wake/AOD
transition recording, and visible date/battery/HR values from the physical
Galaxy Watch7 44 mm, captured BEFORE modifying Aurelius.

**Status: BLOCKED — no device reachable from the build workstation.**

Evidence of the attempt:

```
$ adb devices -l
List of devices attached
            (empty)

$ adb mdns services
List of discovered mdns services
            (empty)
```

The watch connects over wireless ADB only when (a) Wireless debugging is
enabled on the watch and (b) the owner provides the current IP:port /
pairing code (it changes per session). Neither is available to the
autonomous build environment at capture time. No previous pairing exists on
this machine (`adb devices` empty).

**Mitigation used instead (disclosed, not a substitute):**

- The immutable Phase-1 release APK
  (`releases/aurelius/current/aurelius.apk`, SHA-256 recorded in
  BASELINE_CAPTURE.md) is the behavioral reference artifact.
- The pre-migration `watchface.xml` (frozen imported Phase-1 source
  baseline; not byte-extracted from the APK) SHA-256 is recorded, and
  migration parity is enforced by semantic XML equivalence checking
  (`tools/generate_face.py aurelius --check` + the parity section of the
  phase report) rather than by visual re-comparison alone.
- The candidate-evidence directory documents the same blocker; the full
  §4.9 device matrix remains **outstanding** and is listed as an explicit
  unresolved item in the phase report. When the owner provides the watch's
  wireless-debug address, run `docs/DEVICE_TEST_MATRIX.md` end-to-end and
  drop the captures here.

No Gradle result is being presented as device evidence.
