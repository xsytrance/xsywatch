# Device Test Matrix — Galaxy Watch7 44 mm

The physical-device gate for any engine-migrated or releasable face.
Run after `tools/build_face.sh <slug>` with the watch connected over
wireless ADB. Evidence lands under
`docs/reports/evidence/<phase>/<slug>/candidate/`.

## Connecting the watch (owner step)

On the watch: Settings → Developer options → Wireless debugging → note
IP:port and pairing code. Then:

```bash
adb pair <ip>:<pairing-port>        # enter code
adb connect <ip>:<port>
adb devices                         # must list the watch
```

## Install & capture

```bash
adb install -r watchfaces/<slug>/app/build/outputs/apk/debug/app-debug.apk
adb shell screencap -p /sdcard/normal.png && adb pull /sdcard/normal.png
# put watch in AOD (palm-cover or wait), then:
adb shell screencap -p /sdcard/aod.png && adb pull /sdcard/aod.png
adb shell screenrecord --time-limit 30 /sdcard/motion.mp4 && adb pull /sdcard/motion.mp4
adb shell getprop ro.build.version.release ro.build.version.sdk ro.product.model
```

## Matrix (record pass/fail + notes per row)

| # | Check | Pass criteria |
|---|-------|---------------|
| 1 | Install/upgrade | `adb install -r` succeeds over the existing face |
| 2 | Picker | face appears in picker and activates |
| 3 | Time | analog time matches a reference clock |
| 4 | Date | aperture shows today's date |
| 5 | Battery gauge | needle position plausible vs Settings battery % |
| 6 | Heart rate | oscillator speeds with a real HR reading; safe fallback before first reading (no wild motion) |
| 7 | Seconds rotor | tourbillon cage completes 1 rotation in 60 s (time it) |
| 8 | Gear ratios | z10_gl CW ~40°/s, z11_gr CCW ~24°/s (5:3, opposite) |
| 9 | Parallax | background/sheen shift on wrist tilt without edge clipping |
| 10 | AOD cycles | normal→AOD→normal ×10, transitions staged and clean |
| 11 | AOD content | readable, restrained, no bright sheen |
| 12 | Smoothness | no obvious stutter over a 10-minute observation |
| 13 | Stability | no disappearance, resource failure, or crash |
| 14 | Touch | n/a for aurelius (no touch targets) — verify none trigger |

Also record: device model/software/API, test date-time, observed battery %
and HR values during capture.

## Battery observation protocol (repeatable, non-definitive)

1. Charge to 100%, enable the face, normal usage day, note % at fixed
   times (e.g. 09:00 / 13:00 / 18:00 / 22:00) in the evidence notes.
2. Compare against the same protocol on the previous face build.
3. A definitive benchmark (controlled AOD/active duty cycle) is out of
   scope until Phase 3+.
