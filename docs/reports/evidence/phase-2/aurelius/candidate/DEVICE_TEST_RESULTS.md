# Candidate physical-device matrix — engine-generated Aurelius

**Status: EXECUTED 2026-07-24 (evening session), same session and device
as the baseline run. This file supersedes `DEVICE_EVIDENCE_BLOCKER.md`.**

Device context identical to `../baseline/DEVICE_TEST_RESULTS.md`
(SM-L310, Android 16 / API 36, BP2A.250325.020.L310XXS2BZF4, wireless adb).
Battery 24–36% and **charging** (docked) for most candidate captures.

## The two candidate builds (regression found and fixed mid-run)

| Build | SHA-256 | Result |
|-------|---------|--------|
| First candidate (pre-fix) | `cb3557bd9b4902e23409e17ba3b93374f8b0b794c81908c1683520ceacdc54ae` | `install -r` over baseline → Success, but rendered the **WARBIRD** design — repo art assets had diverged from the release APK since the Phase-1 import. Full analysis: `ASSET_DIVERGENCE_FINDING.md` |
| Corrected candidate | `b01015c87eea1e9b23859d98ebcae56ce808be4db7e066b3d25bc682724cc43e` | Art restored from the immutable release APK bytes; `install -r` over the first candidate → Success; renders the Field Tourbillon identically to baseline. **All matrix rows below are for this build** |

## Matrix results

| # | Check | Result | Evidence / notes |
|---|-------|--------|------------------|
| 1 | Install/upgrade | **PASS, with a documented system behavior** | `adb install -r` succeeded at every step (baseline→candidate1→candidate2; debug keystore continuity held). Caveat: One UI **deactivates the active watch face during reinstall** and falls back to another face; the face must be re-selected in the picker afterwards. Not a signature failure — data/continuity preserved |
| 2 | Picker | **PASS** | Face listed with correct preview and re-activated by tap after each install (`candidate_warbird_regression_picker.png` also shows the picker slot live) |
| 3 | Time | **PASS** | Hands read 8:26 PM against device `date` 20:26:24 at capture (`candidate_normal.png`); consistent across later captures |
| 4 | Date | **PASS** | Aperture shows **24** |
| 5 | Battery gauge | **PASS (live movement observed)** | RESERVE needle visibly higher at 32% (charging) than the baseline captures at 19–21% — the gauge demonstrably tracks `[BATTERY_PERCENT]` on device |
| 6 | Heart rate | **PASS (fallback path)** | Not worn → safe fallback active, balance oscillates steadily, no wild motion (same as baseline) |
| 7 | Seconds rotor | **PASS** | Marker ~348° @ :58 → ~108° @ :18 (20 s pair); full revolution in `candidate_60s_motion.mp4`: 90° @ rec-start (:15) → 270° @ +30 s → 90° @ +60 s |
| 8 | Gear ratios | **PASS** | z10_gl CW ~60°/1.5 s (=40°/s), z11_gr CCW ~36°/1.5 s (=24°/s), 5:3 opposite — same crops method as baseline |
| 9 | Parallax | **PASS (owner tilt, recorded)** | `candidate_parallax_tilt.mp4`: owner tilted the watch in hand for ~30 s; the sheen band visibly sweeps across the dial with orientation, no edge clipping. (Baseline shares the identical `ACCELEROMETER_ANGLE_X/Y` binding; not separately re-run on baseline) |
| 10 | AOD cycles ×10 | **PASS** | Scripted off-charger run: 10 logged sleep/wake cycles, clean active render after (`candidate_after_10_aod_cycles.png`, RESERVE needle mid-arc at ~50% charging — third live battery-gauge data point) |
| 11 | AOD content | **PASS (behavior) / screencap not obtainable (display pipeline)** | 10 AOD cycles + transition recording prove ambient entry/exit is stable. A direct candidate doze screencap could not be obtained in this session: every attempt (+3 s to +30 s into doze, `doze_always_on` on/off) returned a black frame — during the candidate window the panel used the non-capturable doze pipeline (`candidate_aod_doze_screencap_black.png` kept as the honest artifact; while docked, doze shows the system charging screen instead). The ambient render itself is byte-determined to equal baseline's captured AOD: identical `bg_aod.png` bytes and semantically identical ambient XML (`../baseline/baseline_aod.png`, captured during verified Doze). Optional owner spot-check: photograph the watch in AOD on wrist |
| 12 | Smoothness | **PASS (sampled)** | `candidate_60s_motion.mp4` (66 s) continuous, no stutter; multi-minute interactive session without hesitation |
| 13 | Stability | **PASS** | Crash buffer and logcat clean for face/runtime across three installs, AOD cycles, and recordings |
| 14 | Touch | **PASS** | Same 4-point tap test as baseline; `topResumedActivity` stayed SysUI home (`candidate_touch_test.png`) |

## Regression comparison vs baseline — explicit conclusion

With the corrected candidate (`b01015c8…`):

- Normal render is visually identical to the baseline capture (same art,
  layout, hands, glyphs; compare `candidate_normal.png` vs
  `../baseline/baseline_normal.png`).
- AOD render identical in structure and restraint (cage parked, dimmed).
- All mechanics identical within measurement: cage 6°/s, gears 40°/s CW /
  24°/s CCW, date/battery/fallback behavior the same.
- Upgrade continuity from the immutable Phase-1 baseline holds
  (`install -r` chain, same debug keystore).
- **No regression** between the immutable Phase-1 release and the
  engine-generated candidate — after the asset-divergence fix this run
  itself surfaced (`ASSET_DIVERGENCE_FINDING.md`). The pre-fix candidate
  was a genuine, matrix-caught regression and is documented, not hidden.

## Files

- `candidate_normal.png` — corrected candidate active render @ 20:26
- `candidate_aod_doze_screencap_black.png` — doze screencap attempt (black; see row 11)
- `candidate_parallax_tilt.mp4` — owner tilt, sheen parallax proof (row 9)
- `candidate_rotation_t0.png` / `candidate_rotation_t20.png` — cage pair
- `candidate_60s_motion.mp4` — 66 s continuous motion
- `candidate_after_10_aod_cycles.png` — post-endurance render
- `candidate_touch_test.png` — post-tap state
- `candidate_transition.mp4` — normal→AOD→normal transition (off-charger)
- `candidate_warbird_regression_picker.png` — the pre-fix regression as seen live
- `ASSET_DIVERGENCE_FINDING.md` — root cause + fix of the pre-fix regression
- `wff_validator_results.md`, `memory_footprint_results.md` — static PASSes
  (re-run against the corrected build in the phase report)
