# rc2 — API-36 heart-rate permission test (Variant A)

**Device:** Galaxy Watch7 44 mm, SM-L310, Android 16 / API 36
**Candidate:** rc2 debug APK `939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc`
**Variant A:** the shipped manifest — **no sensor or health permission declared**
**Date:** 2026-07-26
**Result:** **Variant A receives live heart rate. Retain no permissions.**

## Why this is measurable rather than a judgement call

The balance wheel is driven by

```
180 + 35 * sin(t * clamp(HEART_RATE < 30 ? 70 : HEART_RATE, 40, 200) * 0.10472)
```

`0.10472 = 2π/60`, so the wheel oscillates at **HR/60 Hz — exactly one
oscillation per heartbeat**. Measuring that frequency from a screen
recording reads back the heart rate the runtime actually handed the face,
with no need to interpret pixels as a number.

The documented fallback is exactly **70 bpm = 1.1667 Hz**, so a face
running on the fallback is unambiguously distinguishable from one
receiving live data.

Tool: `tools/balance_frequency.py` — a DFT sweep over the 150
highest-variance pixels of the `z21_bal` layer box (x194 y316 92×92).

## Measurements

| Run | Frames | Dominant frequency | Implied HR |
|---|---|---|---|
| A-1 | 422 @30fps (14.07 s) | **1.7300 Hz** | **103.8 bpm** |
| A-2 (~90 s later) | 424 @30fps (14.13 s) | **1.7350 Hz** | **104.1 bpm** |
| fallback would be | — | 1.1667 Hz | 70.0 bpm |

A clean 2× harmonic appears at 3.46 Hz, as a sinusoid should produce.

The owner's other watch face was displaying **104 bpm** at the time. The
face's implied heart rate matches the watch's live reading to within
0.2 bpm and is nowhere near the 70 bpm fallback.

## Corroboration from the platform

While AURELIUS was the active face, `dumpsys sensorservice` reported:

```
Active sensors:
  ...
  Samsung HR None Wakeup Sensor (handle=0x00000050, connections=1)
```

That sensor is guarded by `android.permission.health.READ_HEART_RATE`:

```
0x00000050  Samsung HR None Wakeup Sensor | type: android.sensor.heart_rate
            | perm: android.permission.health.READ_HEART_RATE
```

Aurelius declares **no permissions** and contains **no code**
(`android:hasCode="false"`), so it cannot open a sensor connection itself.
The connection is held on the face's behalf by the Watch Face Format
runtime, which is exactly the model the manifest comment predicted.

## Package permission state

```
requested permissions:   (none — zero blocks)
```

No consent prompt appeared at install or at activation, and no sensitive
permission is attributable to this package.

The previous build requested `BODY_SENSORS` and `ACTIVITY_RECOGNITION`;
`ACTIVITY_RECOGNITION` was recorded as `granted=false` and the face worked
anyway — independent confirmation it backed no feature.

## Decision

Per the review's rule — *"If Variant A receives real changing heart rate,
retain no permissions"* — **rc2 keeps a manifest with no permissions.**

`android.permission.health.READ_HEART_RATE` is **not** adopted. A sensitive
health permission must not be retained merely because it looks safer; this
package demonstrably does not need one.

Variant B was still built for comparison and is retained unshipped at
`build/permission-variants/READ_HEART_RATE/`
(apk `17b718c7da2d9f3908a06ac79c70ef6d30afae41c54aef89b7e306ff00ac439f`,
aab `3c5f742ca9e7b3a8d794c2522438ecf2f6786d1709919f79fca95f1b3a0e3f03`),
so the comparison can be repeated without another development cycle.

## Outstanding

- **changing-HR confirmation** — both runs were taken at rest, ~104 bpm.
  A recording after deliberate exertion is needed to show the value
  *tracks* rather than merely differing from the fallback.
- **fallback confirmation** — a recording with the watch off-wrist, where
  the implied rate should collapse to exactly 70.0 bpm.

Both require the owner and are recorded here as incomplete rather than
inferred.
