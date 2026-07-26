# Phase 4 — API-36 heart-rate permission investigation

**Status:** static and documentary analysis **COMPLETE**; on-device
empirical confirmation **BLOCKED — no Galaxy Watch7 reachable**
**Date:** 2026-07-26
**Applies to:** `com.xsytrance.aurelius` 2.0.0-rc2, minSdk/targetSdk 36

Checkpoint B blocker 4. The rc1 manifest declared:

```xml
<uses-permission android:name="android.permission.BODY_SENSORS" />
<uses-permission android:name="android.permission.ACTIVITY_RECOGNITION" />
```

Both are removed in rc2. This records why, and what remains unproven.

---

## Finding 1 — `ACTIVITY_RECOGNITION` backed no feature. Removed.

Determinable statically and conclusively. The complete set of data sources
referenced by the generated WFF XML is:

```
[ACCELEROMETER_ANGLE_X] [ACCELEROMETER_ANGLE_Y] [BATTERY_PERCENT]
[DAY] [HEART_RATE] [HOUR_0_11] [MILLISECOND] [MINUTE] [SECOND]
```

There is no `[STEP_COUNT]`, `[DISTANCE]`, `[CALORIES]`, `[FLOORS]` or
`[ELEVATION_GAIN]` anywhere in `engine/face.toml` or
`app/src/main/res/raw/watchface.xml`. The permission was declared and
never used — a sensitive permission with no backing feature, which is
both a Play-policy risk and a user-trust cost for nothing.

**Action: removed.** `tools/verify_candidate.py` now fails the build if
`ACTIVITY_RECOGNITION` is declared while no activity source appears in the
generated XML, so it cannot come back silently.

## Finding 2 — unqualified `BODY_SENSORS` is invalid on an API-36-only package. Removed.

From the official Wear OS 6 behaviour-change documentation
(<https://developer.android.com/training/wearables/versions/6/changes>,
checked 2026-07-26):

> Apps targeting API level 36 or higher must declare granular health
> permissions instead of the old `BODY_SENSORS` permissions.

| Wear OS 5.1 | Wear OS 6 (`android.permission.health`) |
|---|---|
| `BODY_SENSORS` | `READ_HEART_RATE` |
| `BODY_SENSORS_BACKGROUND` | `READ_HEALTH_DATA_IN_BACKGROUND` |

And from the health-permissions guide
(<https://developer.android.com/health-and-fitness/health-services/permissions>):

> ```xml
> <uses-permission android:name="android.permission.BODY_SENSORS"
>                  android:maxSdkVersion="35" />
> <uses-permission android:name="android.permission.health.READ_HEART_RATE" />
> ```

The legacy permission is only meaningful with `android:maxSdkVersion="35"`.
Aurelius has `minSdk = 36`, so that ceiling can never be reached: an
unqualified `BODY_SENSORS` declaration on this package is dead metadata
that still reads to a reviewer and a user as a broad sensor request.

**Action: removed.** `verify_candidate.py` fails the build on an
unqualified `BODY_SENSORS` when `minSdk >= 36`.

## Finding 3 — whether the package needs ANY permission is unproven

This is the open question, and it is not answered by documentation.

**The argument for needing none:**

- Aurelius is a declarative Watch Face Format package. `AndroidManifest`
  declares `android:hasCode="false"`, and there is not one `.java` or
  `.kt` source. The package **cannot call an API, cannot request a
  runtime permission, and cannot receive a permission result.** A
  permission a package can never request is of doubtful value.
- `[HEART_RATE]` is a WFF *data source*: the platform evaluates it and
  renders the result. The app is not the reader.
- No page in the Watch Face Format documentation states that a WFF
  package must declare a permission for any data source.
- The face has a documented fallback — `HEART_RATE < 30 ? 70 :
  HEART_RATE`, clamped to 40–200 — so an unavailable reading degrades
  into an already-tested, already-rendered state rather than breaking.

**What could still be true:** the platform may gate `[HEART_RATE]` on the
package declaring `android.permission.health.READ_HEART_RATE`, in which
case the balance wheel would silently animate at the 70 bpm fallback
forever. That is a real, if benign, functional regression — and only the
device can distinguish it from correct behaviour.

**Decision for rc2: declare nothing.** Minimum privilege is the correct
default when the alternative is declaring a sensitive health permission
speculatively. The failure mode of being wrong is graceful and already
tested; the failure mode of over-declaring is a sensitive permission we
cannot justify to a reviewer.

## What must still be tested on the Watch7

**BLOCKED — no device was reachable during this session.** `adb devices`
returned zero attached devices throughout.

| # | Test | Expected if no permission is needed |
|---|---|---|
| 1 | Install rc2 (variant A, no permissions), wear the watch | balance wheel responds to real, changing HR |
| 2 | Observe the app's permission page in settings | no sensitive permission listed; no consent prompt |
| 3 | Remove the watch / cover the sensor | HR becomes unavailable; balance falls back to 70 bpm, no visual break |
| 4 | Install variant B (`android.permission.health.READ_HEART_RATE`) | compare behaviour against A |
| 5 | Variant B with the permission denied | fallback path, no crash |

**Variant B is pre-built** so the comparison needs only the device, not
another development cycle:

```bash
tools/build_permission_variant.sh READ_HEART_RATE
```

If test 1 shows the balance wheel does **not** track live heart rate while
test 4 shows it does, the granular permission is required: adopt variant
B, complete the Health-apps declaration posture, and update the privacy
and Data-safety text accordingly. Until then rc2 ships variant A.

## Consequences for the disclosure material

With no permission declared, the on-device story is simpler and is
already what the copy says:

- `docs/commercial/aurelius/2.0.0-rc1/COPY_DRAFT.md` §heart-rate — updated
  to state that no sensor permission is declared;
- Data-safety draft — unchanged conclusion (no data collected), with the
  open `BODY_SENSORS` question now closed;
- privacy-policy draft — unchanged conclusion, wording tightened.

**None of this may be described as final until test 1 runs.** The
`permissions-verified` readiness gate is `blocked`, not `complete`.
