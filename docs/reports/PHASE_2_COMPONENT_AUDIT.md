# Phase 2 Component Audit — all committed watchfaces

Generated deterministically by `tools/analyze_wff_patterns.py`; do not edit by hand.
Machine-readable twin: `PHASE_2_COMPONENT_AUDIT.json`.

## Per-face summary

| Face | WFF | Clock | Elems | Groups | Refs | Rotating parts | Fonts | Unused res | Unsafe |
|---|---|---|---|---|---|---|---|---|---|
| arcwright | 4 | DIGITAL | 135 | 0 | 0 | 15 | 2 | 18 | 0 |
| ares-wargod | 4 | DIGITAL | 142 | 0 | 0 | 2 | 1 | 11 | 1 |
| aurelius | 4 | ANALOG | 96 | 0 | 0 | 7 | 1 | 5 | 0 |
| bone-watch | 4 | ANALOG | 137 | 0 | 0 | 3 | 1 | 0 | 1 |
| bushido | 4 | DIGITAL | 179 | 3 | 0 | 0 | 0 | 3 | 1 |
| chronova | 4 | DIGITAL | 340 | 0 | 0 | 17 | 0 | 0 | 0 |
| hellforge | 4 | ANALOG | 124 | 0 | 0 | 3 | 1 | 0 | 1 |
| pinball | 4 | DIGITAL | 110 | 0 | 0 | 0 | 1 | 0 | 0 |
| pulseface | 4 | DIGITAL | 198 | 2 | 0 | 0 | 2 | 0 | 0 |
| tripface | 2 | DIGITAL | 622 | 13 | 0 | 2 | 0 | 10 | 0 |

## Data-source usage (which faces bind which data)

- `[ACCELEROMETER_ANGLE_X]` — 9 face(s): arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface
- `[ACCELEROMETER_ANGLE_Y]` — 9 face(s): arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface
- `[AMPM_STRING]` — 1 face(s): bushido
- `[BATTERY_PERCENT]` — 7 face(s): ares-wargod, aurelius, bone-watch, bushido, hellforge, pinball, pulseface
- `[DAY]` — 7 face(s): ares-wargod, aurelius, bone-watch, bushido, hellforge, pinball, pulseface
- `[DAY_OF_WEEK_S]` — 6 face(s): ares-wargod, bone-watch, bushido, hellforge, pinball, pulseface
- `[HEART_RATE]` — 7 face(s): ares-wargod, aurelius, bone-watch, bushido, hellforge, pulseface, tripface
- `[HOUR_0_11]` — 6 face(s): arcwright, ares-wargod, aurelius, bone-watch, chronova, hellforge
- `[MILLISECOND]` — 10 face(s): arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface, tripface
- `[MINUTE]` — 9 face(s): arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface
- `[MONTH_S]` — 1 face(s): bushido
- `[SECOND]` — 10 face(s): arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface, tripface
- `[STEP_COUNT]` — 3 face(s): ares-wargod, bushido, pulseface
- `[STEP_PERCENT]` — 2 face(s): bushido, tripface

## 1. Components suitable for immediate extraction (pattern in ≥3 faces)

- (9 faces: arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface) `N + N * clamp([ACCELEROMETER_ANGLE_X], -N, N) / N`
- (9 faces: arcwright, ares-wargod, aurelius, bone-watch, bushido, chronova, hellforge, pinball, pulseface) `N + N * clamp([ACCELEROMETER_ANGLE_Y], -N, N) / N`
- (7 faces: ares-wargod, aurelius, bone-watch, bushido, hellforge, pinball, pulseface) `[DAY]`
- (6 faces: ares-wargod, bone-watch, bushido, hellforge, pinball, pulseface) `[BATTERY_PERCENT]`
- (6 faces: ares-wargod, bone-watch, bushido, hellforge, pinball, pulseface) `[DAY_OF_WEEK_S]`
- (5 faces: ares-wargod, aurelius, bone-watch, chronova, hellforge) `([HOUR_0_11] + [MINUTE] / N) * N`
- (4 faces: ares-wargod, aurelius, bone-watch, hellforge) `([MINUTE] + [SECOND] / N) * N`
- (4 faces: arcwright, aurelius, chronova, tripface) `([SECOND] + [MILLISECOND] / N) * N`
- (4 faces: ares-wargod, bone-watch, bushido, hellforge) `[HEART_RATE]`
- (3 faces: ares-wargod, bushido, pulseface) `N + N * abs(sin(([MINUTE] * N + [SECOND] + [MILLISECOND] / N) * N))`
- (3 faces: aurelius, hellforge, pinball) `N + N*sin(([MINUTE] * N + [SECOND] + [MILLISECOND] / N)*N)`
- (3 faces: ares-wargod, bushido, pulseface) `[STEP_COUNT]`

## 2. Similar but face-specific (2 faces — do not force-share yet)

- (bone-watch, hellforge) `(([MINUTE] * N + [SECOND] + [MILLISECOND] / N) % N) * N`
- (arcwright, chronova) `([MINUTE] * N + [SECOND] + [MILLISECOND] / N) * N`
- (bushido, pulseface) `-N + ((([MINUTE] * N + [SECOND] + [MILLISECOND] / N) * N) % N)`
- (bushido, pulseface) `N + N * abs(sin(([MINUTE] * N + [SECOND] + [MILLISECOND] / N) * (clamp(([HEART_RATE] < N ? N : [HEART_RATE]), N, N)) * N))`
- (bone-watch, hellforge) `N + N*abs(sin(([MINUTE] * N + [SECOND] + [MILLISECOND] / N)*N))`
- (arcwright, chronova) `N - (([MINUTE] * N + [SECOND] + [MILLISECOND] / N) * N)`
- (arcwright, chronova) `N - (([SECOND] + [MILLISECOND] / N) * N)`
- (chronova, tripface) `N - ([SECOND] + [MILLISECOND] / N) * N`
- (bushido, pulseface) `N - N * clamp([ACCELEROMETER_ANGLE_X], -N, N) / N`
- (arcwright, chronova) `N - N * sin(([SECOND] + [MILLISECOND] / N) * N + N)`
- (arcwright, chronova) `[MINUTE] * N`
- (ares-wargod, pulseface) `clamp(([HEART_RATE] - N) * N, N, N)`
- (arcwright, chronova) `floor([SECOND]) * N`

## 3. One-off patterns (not worth abstracting)

41 single-face expression shapes (full list in the JSON; deliberately not abstracted).

## 4. Unsafe/inconsistent patterns needing later cleanup

- **ares-wargod**: unclamped HEART_RATE expression: [HEART_RATE]
- **bone-watch**: unclamped HEART_RATE expression: [HEART_RATE]
- **bushido**: unclamped HEART_RATE expression: [HEART_RATE]
- **hellforge**: unclamped HEART_RATE expression: [HEART_RATE]

## Per-face detail

### arcwright (`watchfaces/arcwright/app/src/main/res/raw/watchface.xml`)

- WFF 4, DIGITAL, 135 elements, 41 named (18 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[HOUR_0_11]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`
- rotating parts: z02_rear_gear_l, z02_rear_gear_m, z05_ne_gear_a, z05_ne_gear_c, z05_nw_gear_a, z05_nw_gear_c, z05_ratchet, z05_ring_hour, z05_ring_min, z05_se_cam, z05_se_gear_b, z05_sw_gear_d, z10_fan, z11_ring_inner, z11_ring_outer
- bitmap fonts: engraved_lg(11 glyphs), engraved_sm(10 glyphs)
- unused resources: bezel_ring60, chamber_housing, chassis, conduit_housing, display_hrs, display_min, display_sec, gear_a, gear_b, gear_c, gear_d, glyph_sm_colon, piston_rod, piston_sleeve, plate_back, ring_inner_rot, ring_outer_rot, turbine_housing
- missing resources: none

### ares-wargod (`watchfaces/ares-wargod/app/src/main/res/raw/watchface.xml`)

- WFF 4, DIGITAL, 142 elements, 82 named (15 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[BATTERY_PERCENT]`, `[DAY]`, `[DAY_OF_WEEK_S]`, `[HEART_RATE]`, `[HOUR_0_11]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`, `[STEP_COUNT]`
- rotating parts: z40_hour, z41_min
- bitmap fonts: carved(66 glyphs)
- unused resources: ares_title, cloud, ic_bolt, ic_feet, ic_flame, ic_floors, ic_heart, ic_moon, ic_pin, panel_stat, panel_time
- missing resources: none

### aurelius (`watchfaces/aurelius/app/src/main/res/raw/watchface.xml`)

- WFF 4, ANALOG, 96 elements, 52 named (12 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[BATTERY_PERCENT]`, `[DAY]`, `[HEART_RATE]`, `[HOUR_0_11]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`
- rotating parts: z10_gl, z11_gr, z21_bal, z22_cage, z31_resv, z50_hour, z51_min
- bitmap fonts: aur(39 glyphs)
- unused resources: needle, prop, tourb_base, tourb_disc, tourb_rim
- missing resources: none

### bone-watch (`watchfaces/bone-watch/app/src/main/res/raw/watchface.xml`)

- WFF 4, ANALOG, 137 elements, 80 named (13 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[BATTERY_PERCENT]`, `[DAY]`, `[DAY_OF_WEEK_S]`, `[HEART_RATE]`, `[HOUR_0_11]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`
- rotating parts: z40_hour, z41_min, z42_sec
- bitmap fonts: bone(66 glyphs)
- unused resources: none
- missing resources: none

### bushido (`watchfaces/bushido/app/src/main/res/raw/watchface.xml`)

- WFF 4, DIGITAL, 179 elements, 39 named (37 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[AMPM_STRING]`, `[BATTERY_PERCENT]`, `[DAY]`, `[DAY_OF_WEEK_S]`, `[HEART_RATE]`, `[MILLISECOND]`, `[MINUTE]`, `[MONTH_S]`, `[SECOND]`, `[STEP_COUNT]`, `[STEP_PERCENT]`
- rotating parts: none
- bitmap fonts: none
- unused resources: fog, k_bushido, k_mirai
- missing resources: none

### chronova (`watchfaces/chronova/app/src/main/res/raw/watchface.xml`)

- WFF 4, DIGITAL, 340 elements, 62 named (62 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[HOUR_0_11]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`
- rotating parts: z02_rear_gear_l, z02_rear_gear_m, z05_ne_gear_a, z05_ne_gear_c, z05_nw_gear_a, z05_nw_gear_c, z05_ratchet, z05_ring_hour, z05_ring_min, z05_se_cam, z05_se_gear_b, z05_se_gear_d, z05_sw_gear_d, z10_fan, z11_ring_inner, z11_ring_outer, z12_core
- bitmap fonts: none
- unused resources: none
- missing resources: none

### hellforge (`watchfaces/hellforge/app/src/main/res/raw/watchface.xml`)

- WFF 4, ANALOG, 124 elements, 57 named (16 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[BATTERY_PERCENT]`, `[DAY]`, `[DAY_OF_WEEK_S]`, `[HEART_RATE]`, `[HOUR_0_11]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`
- rotating parts: z40_hour, z41_min, z42_sec
- bitmap fonts: hell(40 glyphs)
- unused resources: none
- missing resources: none

### pinball (`watchfaces/pinball/app/src/main/res/raw/watchface.xml`)

- WFF 4, DIGITAL, 110 elements, 55 named (14 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[BATTERY_PERCENT]`, `[DAY]`, `[DAY_OF_WEEK_S]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`
- rotating parts: none
- bitmap fonts: dmd(40 glyphs)
- unused resources: none
- missing resources: none

### pulseface (`watchfaces/pulseface/app/src/main/res/raw/watchface.xml`)

- WFF 4, DIGITAL, 198 elements, 88 named (28 z-prefixed)
- data sources: `[ACCELEROMETER_ANGLE_X]`, `[ACCELEROMETER_ANGLE_Y]`, `[BATTERY_PERCENT]`, `[DAY]`, `[DAY_OF_WEEK_S]`, `[HEART_RATE]`, `[MILLISECOND]`, `[MINUTE]`, `[SECOND]`, `[STEP_COUNT]`
- rotating parts: none
- bitmap fonts: neo(40 glyphs), hot(13 glyphs)
- unused resources: none
- missing resources: none

### tripface (`watchfaces/tripface/app/src/main/res/raw/watchface.xml`)

- WFF 2, DIGITAL, 622 elements, 264 named (0 z-prefixed)
- data sources: `[HEART_RATE]`, `[MILLISECOND]`, `[SECOND]`, `[STEP_PERCENT]`
- rotating parts: ring_inner, ring_outer
- bitmap fonts: none
- unused resources: md0, md1, md2, md3, md4, md5, md6, md7, md8, md9
- missing resources: none
