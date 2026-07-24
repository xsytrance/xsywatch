# Candidate physical-device evidence — BLOCKED (disclosed per brief §4.9)

**Date:** 2026-07-24
**Requirement:** brief §4.9 — install the engine-generated Aurelius
candidate on the physical Galaxy Watch7 44 mm and run the full
`docs/DEVICE_TEST_MATRIX.md` with screenshots/recording.

**Status: BLOCKED — same blocker as the baseline capture.** No device is
reachable (`adb devices` and `adb mdns services` both empty; no stored
pairing). Wireless-debug pairing requires the owner to enable it on the
watch and supply the session IP:port/pairing code.

## What was proven WITHOUT the device (not presented as device evidence)

- Engine-generated XML is **semantically identical** to the baseline that
  is inside the on-wrist-proven Phase-1 release APK
  (tests/engine/test_aurelius_parity.py — every element, attribute, and
  expression; single documented identifier rename).
- Official WFF validator: PASS (format v4) — `wff_validator_results.md`.
- Memory-footprint evaluator: PASS for candidate and release APKs —
  `memory_footprint_results.md`.
- Gradle build: PASS; released APK untouched (pinned immutable).

## To close this item (owner + one command each)

1. Enable Wireless debugging on the watch, provide IP:port + pairing code.
2. Run the capture commands and matrix in `docs/DEVICE_TEST_MATRIX.md`.
3. Drop captures + per-row pass/fail notes in this directory; update the
   phase report §15 and the ledger review note.

The device matrix is an explicit OPEN acceptance item for Phase 2
architecture review (report §19 Deviations).
