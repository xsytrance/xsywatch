# Baseline physical-device matrix — Phase-1 immutable APK

**Status: EXECUTED 2026-07-24 (evening session). This file supersedes
`DEVICE_EVIDENCE_BLOCKER.md`, which is retained only as history of the
earlier blocked attempt.**

## Device context

| Item | Value |
|------|-------|
| Device | Samsung Galaxy Watch7 44 mm (SM-L310, `fresh7blue`) |
| OS / API | Android 16, API 36 |
| Build | BP2A.250325.020.L310XXS2BZF4 (One UI Watch) |
| Connection | wireless adb `192.168.1.183:44809` (owner-provided pairing) |
| Test window | 2026-07-24 20:02–20:16 EDT |
| Battery during captures | 21% → 19% discharging; on charger from ~20:12 (16%, charging) |
| Wear state | NOT worn (on desk, then charger) → HR sensor has no live reading; the design's 70 bpm safe fallback is the active path |

## APK under test

- `releases/aurelius/current/aurelius.apk` (immutable Phase-1 release)
- SHA-256 `844b9c430f65e0dfaec88604175f1345b4173d647496de4b4ed74359ccfdbcc2`
  (re-verified at install time; matches the `.immutable` pin)
- Installed with `adb install -r` **over the pre-existing on-watch copy** → `Success`

## Matrix results

| # | Check | Result | Evidence / notes |
|---|-------|--------|------------------|
| 1 | Install/upgrade | **PASS** | `adb install -r` → Success over existing install |
| 2 | Picker | **PASS** | Face listed and activated by tap (long-press → picker → tap) |
| 3 | Time | **PASS** | Hands read 8:03 / 8:04 / 8:06 / 8:14 / 8:15 PM against device `date` at each capture (`baseline_normal.png` @ 20:04:03) |
| 4 | Date | **PASS** | Aperture shows **24** (2026-07-24) in all captures |
| 5 | Battery gauge | **PASS** | RESERVE needle at low end of 45° arc at 19–21% reported by `dumpsys battery` |
| 6 | Heart rate | **PASS (fallback path)** | Watch not worn → no live HR; balance oscillates steadily with no wild motion — this exercises the safe-fallback row directly. Live-HR speed-up not testable unworn; see candidate notes |
| 7 | Seconds rotor | **PASS** | Cage marker 186° @ 20:04:31 → ~315° @ 20:04:52 (20.6 s ≈ 124° ≈ 6°/s = 360°/60 s); full revolution confirmed in `baseline_60s_motion.mp4` |
| 8 | Gear ratios | **PASS** | z10_gl CW / z11_gr CCW, ~5:3 opposite rotation visible across `baseline_rotation_t0/t20.png` and the 60 s recording |
| 9 | Parallax | **PASS (by identical binding)** | Sheen bound to `ACCELEROMETER_ANGLE_X/Y`; physically verified in the same session on the corrected candidate via owner tilt (`../candidate/candidate_parallax_tilt.mp4`) — the binding expression is semantically identical in both XMLs; not separately re-run on the baseline build |
| 10 | AOD cycles ×10 | **PASS** | Scripted `KEYCODE_SLEEP`/wake ×10 (`aodcycles.log` = 10); clean active render after (`baseline_after_10_aod_cycles.png`); `mWakefulness=Awake` |
| 11 | AOD content | **PASS** | `baseline_aod.png` captured while `dumpsys power` reported `mWakefulness=Dozing`: dimmed restrained render, sheen suppressed, cage parked at 12 (seconds stop in ambient), time/date readable |
| 12 | Smoothness | **PASS (sampled)** | 24 s transition recording + 63 s motion recording show continuous cage/gear motion, no stutter; session totalled ~15 min of interaction without hesitation. A strict continuous 10-min wear observation remains an owner-side spot check |
| 13 | Stability | **PASS** | `logcat -b crash` empty for face/runtime; zero fatal/ANR/died lines mentioning aurelius; face never disappeared across installs, 10 AOD cycles, and recordings |
| 14 | Touch | **PASS** | Taps at (120,120), (360,240), (240,360) and the date window (322,310) triggered nothing; `topResumedActivity` remained SysUI home |

## Files

- `baseline_normal.png` — active render @ 20:04:03, 19% battery
- `baseline_aod.png` — ambient render during verified Doze @ 20:06:15
- `baseline_rotation_t0.png` / `baseline_rotation_t20.png` — cage timing pair
- `baseline_transition.mp4` — 24 s normal→AOD→normal (transition staged and clean; timeline: active 0–5 s, ambient 6–10 s, awake 11 s+)
- `baseline_60s_motion.mp4` — 63 s continuous motion (full cage revolution)
- `baseline_after_10_aod_cycles.png` — post-endurance render
- `baseline_touch_test.png` — post-tap state

## Capture-environment notes (deviations from stock settings, all restored)

- `settings put system screen_off_timeout 600000` during captures (stock 60000, restored after)
- `settings put global heads_up_notifications_enabled 0` during recordings (stock 1, restored after) — every adb (re)connect posts a "Wireless debugging connected" notification that otherwise overlays the dial
- `svc power stayon true` while docked for recording stability
- One discarded recording attempt was contaminated by that adb notification plus the charging screen; it was re-run clean and only the clean take is kept
