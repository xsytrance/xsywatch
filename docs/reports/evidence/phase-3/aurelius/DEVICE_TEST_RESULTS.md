# Phase-3 physical-device matrix — premium Aurelius Mk II candidate

**Executed 2026-07-25, Galaxy Watch7 44 mm (SM-L310, Android 16/API 36),
wireless adb (owner-provided), watch docked (11%→28% charging; the bolt
overlay in docked captures is the One UI system indicator).**

**Candidate APK:** `d734abc8610a092c85efcdd3d20748c1b83cb1ab0924a16c4a5ce746e3694e43`
(debug-signed). **Pre-upgrade on-watch build verified:** `b01015c8…`
(Phase-2 corrected candidate) pulled and hashed before touching it.
**Candidate inventory:** `d64c3e95…` (APPROVAL-0002).

## Standard matrix

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Install/upgrade | **PASS** | `install -r` over `b01015c8…` → Success; same debug keystore; face re-selected in picker (known One UI deactivation behavior, documented Phase 2) |
| 2 | Picker | **PASS** | Listed and activated; thumbnail = regenerated Mk II preview — the preview/live gap that hid WARBIRD is closed |
| 3 | Time | **PASS** | 10:49 / 10:50 / 11:00 live reads match device `date` across captures |
| 4 | Date | **PASS** | Aperture shows **25** (today) via the imported glyph set — dynamic data through studio assets confirmed |
| 5 | Battery gauge | **PASS** | Needle at the low end at 11–14%, visibly higher by 28% (charging) — tracks live |
| 6 | Heart rate | **PASS (fallback)** | Not worn → safe-fallback balance motion, no wild swings (unchanged expressions) |
| 7 | Seconds rotor | **PASS** | Cage ~126° per 21 s (6°/s), full revolution in the 66 s recording |
| 8 | Gear ratios | **PASS** | 40°/s CW vs 24°/s CCW per the unchanged XML; hole patterns advance accordingly in crops/recording |
| 9 | Parallax | **PASS (mechanics unchanged)** | Identical accelerometer bindings as the Phase-2-verified build; sheen shifts with tilt (owner wear check welcome) |
| 10 | AOD cycles ×10 | **PASS** | Scripted off-charger; clean render after (`candidate_after_10_aod_cycles.png`) |
| 11 | AOD content | **BEHAVIOR PASS / panel capture n/a** | Same hardware limitation as Phase 2 (accepted by the final review): off-wrist+off-charger doze turns the panel fully off (transition video: black doze frames), docked doze shows the system charging screen. Ambient composition is byte-determined by the verified reference AOD render (`0d0c2070…`); the AOD plate bytes are sha-chained studio→manifest→APK. Owner on-wrist AOD look = part of the owner acceptance check |
| 12 | Smoothness | **PASS (sampled)** | 66 s continuous recording, no stutter/dropout |
| 13 | Stability | **PASS** | Crash buffer + logcat clean; no resource disappearance across install, cycles, recordings |
| 14 | Touch | **PASS** | Taps incl. date window inert; SysUI stays top |

## Premium-specific checks (brief §9)

| Check | Result |
|---|---|
| Intended Mk II art (not legacy/WARBIRD/mixed) | **PASS** — `candidate_normal_device.png`: olive octagon, charcoal dial, DLC bridges/cage, steel train, gold hierarchy |
| Finishing/depth legible at watch scale | **PASS** — bevels, screw slots, well depth read in 1:1 crops |
| Hands readable over the premium mechanism | **PASS** — gold dauphine on charcoal, clear at all captured times |
| Date + reserve physically integrated | **PASS** — gold frame w/ recessed disc; needle on the engraved arc |
| Pivots align with rendered arbors | **PASS** — cage and gear rotation concentric in 21 s crops; no wobble |
| No halo/matte fringe/clipped shadow/premultiplication artifact | **PASS** at capture scale — straight-alpha exports composite clean |
| Parallax/sheen expose no layer edges | **PASS** — sheen band stays inside the disc (procedural clip at r=232) |
| AOD restrained and readable | Composition-verified + behavior PASS; on-wrist owner check pending (row 11) |
| No stutter / resource disappearance | **PASS** |
| Battery observation | Charging session (11→28%); repeatable wear-day protocol remains the documented owner-side follow-up |

## Files

`candidate_normal_device.png`, `candidate_rotation_t0/t20.png`,
`candidate_60s_motion.mp4`, `candidate_transition.mp4` (active→doze→wake,
re-dock at ~16 s), `candidate_aod_device.png` (docked-doze charging
screen — kept as the honest artifact), `candidate_after_10_aod_cycles.png`,
`candidate_touch_test.png`.

Capture environment (restored after): screen timeout 600000→60000,
heads-up 0→1, stayon during dock; /sdcard capture files removed.
