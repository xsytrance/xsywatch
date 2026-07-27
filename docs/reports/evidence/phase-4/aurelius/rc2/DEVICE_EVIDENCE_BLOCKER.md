# rc2 physical Watch7 validation — DEVICE BLOCKER CLOSED

**Status:** the device blocker is **closed**. What remains is owner
observation and wear time, not device access.

**Superseded twice, kept honest rather than deleted:**

1. The first revision claimed `adb devices` reported zero devices
   throughout and that nothing on the physical matrix could proceed. A
   device session on 2026-07-26 disproved that.
2. The second revision recorded four passing rows but stated the
   Checkpoint B visual matrix had not been run and that no
   `DEVICE_TEST_RESULTS.md` existed. **That is also now false.**

The full corrected matrix ran on **2026-07-27** against
`192.168.1.183:38371`, on the already-installed rc2 APK
`939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc`.

**Authoritative record: `DEVICE_TEST_RESULTS.md` in this directory.**
20 measured rows, **0 failures**. Artefacts under `matrix/`.

## What is still outstanding — and it is not device access

- **14 owner rows** in `DEVICE_TEST_RESULTS.md`, marked `PENDING — owner`.
  They need eyes on a physical watch: parallax, actual-scale legibility,
  Command Satin quality, reserve-tick restraint, absence of unintended
  ornament, AOD restraint, AOD post-cycle visual integrity, battery-gauge
  plausibility, time/date correctness, heart-rate agreement with the
  watch's own reading, post-exertion rise, off-wrist fallback, absence of
  any permission prompt, and the final disposition.
- **2 hand rows** (`z50_hour`, `z51_min`) — a 60 s capture cannot
  distinguish a slow hand from a stopped one, so they are deliberately not
  scored.
- **3 wear sessions** bound to this APK via `tools/wear_log.py`, covering
  `office`, `home`, `outdoor`, `low-light`.

`device-validated` therefore stays **blocked** — correctly, and for a
reason that is now true.

## Two harness defects the live run exposed

Recorded because they are the reason the first live attempt produced
nothing usable, and because both were false-pass risks:

1. The Watch7 screen times out in seconds. `screenrecord` wrote a
   **zero-byte** file and the normal-mode `screencap` returned an entirely
   black frame — and the normal-mode row reported **PASS** on file
   existence alone. The harness now raises the screen timeout for the
   duration of the capture, restores it afterwards, verifies
   `mWakefulness=Awake`, rejects a zero-byte recording, and rejects any
   capture that is entirely black.
2. Extracted frames are a derived intermediate (~340 MB for 60 s). They
   are deleted after analysis unless `--keep-frames` is passed;
   `motion.mp4` is the committed evidence and the frames re-extract from
   it with a single `ffmpeg` call.

## To close `device-validated`

1. AGENOR observes the 14 owner rows on the watch and reports them.
2. The results are recorded against those rows — **never converted to PASS
   without explicit observations**.
3. Re-derive readiness with
   `python3 tools/check_candidate_readiness.py aurelius --version 2.0.0-rc2 --stamp`.

**Checkpoint B must not be approved on the owner rows being absent.**
