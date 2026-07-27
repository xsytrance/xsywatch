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

## Where this stands after owner inspection (2026-07-27)

Groups A and B are complete: **15 PASS, 1 ISSUE**, recorded verbatim in
`OWNER_OBSERVATIONS.json` and rendered into `DEVICE_TEST_RESULTS.md`.

**The ISSUE is `Date readability`.** Owner: *"yeah its grey on grey"* and
*"looks off-center too"*. Both are reproducible against the DESIGN, not the
panel:

- glyph-vs-window contrast measures **4.53:1** — which technically scrapes
  WCAG AA for normal text, and is precisely why no gate flagged it. That is
  a desk metric applied to a wrist at a glance.
- the deterministic aperture proof shows the glyphs sit **1px high on all
  62 renders** (top 3.07 vs bottom 4.07) and drift left horizontally by up
  to **3px on day 1**.

The aperture proof passes because it asserts **containment only**, with a
2px minimum clear margin. **Centring was never asserted, so nothing was
checking it.** That is a gap in the gate, not merely a blemish on the face.

An ISSUE row means rc2 is **not acceptable as-is**. Fixing it would change
package bytes and therefore require rc3 plus a fresh architecture review —
an owner decision, deliberately not taken here.

## The three heart-rate rows — blocked on network, not on effort

Two attempts on 2026-07-27, neither usable:

1. owner read **130 bpm** while away from the home network;
2. owner read **98 bpm**, but `adb` returned `No route to host` at the last
   known address `192.168.1.183:38371`, so no recording was possible.

**Neither number is evidence.** The comparison is only meaningful when the
watch reading and the balance-wheel recording are simultaneous, so neither
may be paired with the earlier 104.1 bpm measurement nor with any later
recording. Recorded rather than quietly discarded.

`tools/hr_probe.sh` exists for exactly this and fails closed: an
unreachable device, a sleeping panel or a zero-byte recording is reported
as BLOCKED, never as a number. The full procedure is in
`OWNER_OBSERVATIONS.json` under `resume_procedure` — about ten minutes of
owner time once the watch is reachable.

## To close `device-validated`

1. **Nine owner rows remain** — the three heart-rate rows and the six
   Group D disposition rows. Group D is deliberately deferred until after
   the wear sessions, when the judgement is meaningful.
2. **Resolve the `Date readability` ISSUE.** An owner decision: accept it
   as-is, or fix it and cut rc3.
3. Results are recorded in `OWNER_OBSERVATIONS.json` — **never converted
   to PASS without explicit observations**, and `NOT TESTED` is a final
   result, not a placeholder.
4. `python3 tools/device_matrix.py aurelius --version 2.0.0-rc2 --rebuild-doc`
5. `python3 tools/check_candidate_readiness.py aurelius --version 2.0.0-rc2 --stamp`

Three wear sessions bound to this APK remain outstanding regardless, via
`tools/wear_log.py`.

**Checkpoint B must not be approved on the owner rows being absent.**
