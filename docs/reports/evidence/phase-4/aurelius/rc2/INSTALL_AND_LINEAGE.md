# rc2 — install, upgrade continuity and installed-byte lineage

**Device:** Samsung Galaxy Watch7 44 mm, SM-L310, Android 16 / API 36
**Connection:** wireless adb, `192.168.1.183:45079`
**Date:** 2026-07-26
**Candidate:** `com.xsytrance.aurelius` 2.0.0-rc2 (versionCode 3)

## Upgrade continuity — PASS

The device carried the earlier build before this install:

| | before | after |
|---|---|---|
| versionCode | 1 | **3** |
| versionName | 1.0 | **2.0.0-rc2** |
| minSdk | 34 | **36** |

`adb install -r` returned `Success`. Upgrading across the minSdk 34 → 36
change and two versionCode steps worked with no uninstall and no data
clear. One UI deactivates the active face on reinstall — documented
behaviour, not a fault.

## Installed-APK hash — PASS

Pulled back from `/data/app/…/base.apk`:

```
939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc  installed
939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc  candidate
```

**Byte-identical.** The artifact on the watch is the artifact in the
repository, not a re-signed or re-packaged variant.

## Installed-resource lineage — PASS

Every resource in the committed inventory, compared against the bytes
extracted from the **installed** APK:

| Result | Count |
|---|---|
| byte-identical to repository source | **58** |
| compiled at packaging (expected) | 2 |
| genuine drift | **0** |

The two non-identical entries are both explained and neither is drift:

- `res/xml/watch_face_info.xml` — the installed copy begins `03 00 08 00`,
  the Android binary-XML (AXML) magic. XML resources are **compiled** at
  packaging; the repository holds the source text. Same documented class
  as the Phase-2 baseline note.
- `res/values/integers.xml` — values resources are compiled into
  `resources.arsc` and do not survive as a separate `res/` entry.

Critically, **`res/raw/watchface.xml` is byte-identical to the repository
source**. Raw resources are stored verbatim, so the file that defines
every pixel of the face is provably the committed one.

The verified chain is therefore complete end to end:

`studio source → producing commit 04015886 → metadata commit 97ba0f1 →
handoff manifest sha → imported resource → inventory 1ec66797 →
consumer source commit a328669e → canonical APK 939d2b44 → installed APK
939d2b44 → physical panel`

## Permission state — rc2 requests nothing

```
requested permissions:   (none — zero blocks)
```

The earlier build requested `BODY_SENSORS` and `ACTIVITY_RECOGNITION`.
Worth recording: on that build `ACTIVITY_RECOGNITION` showed
`granted=false`. It was declared, never granted, and the face worked
anyway — direct confirmation that it backed no feature.

## Platform permission mapping — confirmed on the device

`dumpsys sensorservice` on this Watch7 reports the heart-rate sensors as:

```
0x00000012  Samsung HR Raw Sensor    | type: com.samsung.sensor.hr_raw   | perm: android.permission.health.READ_HEART_RATE
0x0000004d  Samsung HR Batch Sensor  | type: android.sensor.heart_rate   | perm: android.permission.health.READ_HEART_RATE
0x00000050  Samsung HR None Wakeup   | type: android.sensor.heart_rate   | perm: android.permission.health.READ_HEART_RATE
```

The device itself confirms the documented API-36 model: heart-rate access
is guarded by the granular `android.permission.health.READ_HEART_RATE`,
not by legacy `BODY_SENSORS`. This is the platform agreeing with
`docs/reports/PHASE_4_PERMISSION_INVESTIGATION.md` findings 2 and 3.

Whether the WFF runtime reads heart rate **on the face's behalf** — its
own process holding that permission — or whether a permission-less
declarative face simply receives nothing, is settled in
`PERMISSION_TEST.md` once the face is active on the wrist.
