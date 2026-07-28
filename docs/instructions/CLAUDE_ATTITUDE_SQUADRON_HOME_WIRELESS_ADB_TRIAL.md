# Claude Task — ATTITUDE SQUADRON Home Wireless-ADB Wrist Trial

## Owner gate

The owner is home, has the Galaxy Watch7 available, and explicitly authorizes a direct wireless-ADB comparison trial now.

This authorization is limited to installing and evaluating the four refreshed ATTITUDE SQUADRON development APKs listed below. It does **not** authorize release work, production signing, AAB creation, store preparation, merging, or modification of the watch faces.

This is a fast comparative wrist trial, **not** the formal ATTITUDE spike evidence harness. The spike harness's manual-install restriction remains unchanged and must not be modified or invoked for this session.

## Required repository state

Repository: `xsytrance/xsywatch`

Branch: `collection/attitude-squadron`

Implementation head reviewed: `044b2fb7d1bad40fb0c71e69127bcc57901dfbae`

Pull the latest branch before beginning. A later documentation-only commit containing this instruction is acceptable; the four APKs must still match the exact identities below.

## Exact authorized wrist pack

Use the existing files from `collection/apk/`. Do not rebuild, repackage, optimize, rename internally, or re-sign them.

| Order | Variant | Package | Bytes | SHA-256 |
|---:|---|---|---:|---|
| 1 | MERIDIAN HAYATE | `com.xsytrance.squadron.hayate.dev` | 3,085,081 | `1f11bea27388525d75ed2353db3c12b5d93108621ad4bc07ef11332afd087d50` |
| 2 | MERIDIAN COMMODORE | `com.xsytrance.squadron.commodore.dev` | 3,157,633 | `cbca9c81eda715240ba650da132d30ad4dda3d82d07864d8ffc8d91000f8ba21` |
| 3 | MERIDIAN PURE | `com.xsytrance.squadron.pure.dev` | 3,093,721 | `a59263a8c8723d88e9c7906a09a9199f8e8b440b81a5e0f655cbb06ae1db90ef` |
| 4 | MERIDIAN BALSA | `com.xsytrance.squadron.balsa.dev` | 3,090,509 | `05d011a4015c5770f6fd71844b1caef157d84244bdcde513d94c5bb830742ec0` |

Do not install the internal AGENOR build.

## Session style

Move quickly. Do not restart the offline development cycle and do not run the full 197-test suite again unless a local file hash is wrong or installation fails in a way suggesting repository drift.

The only permitted setup question is the dynamic wireless-debugging information needed to reach the watch:

- if the workstation is already paired with the Watch7, request the watch's current wireless-debugging `IP:PORT`;
- if it is not paired, request the `Pair new device` pairing `IP:PORT` and six-digit pairing code, then the normal wireless-debugging `IP:PORT`.

Do not interpret the owner's physical location as a blocker. Network reachability and explicit authorization are the relevant conditions, and both are now intended to be established.

## Step 1 — Local identity verification

Before contacting the watch:

1. Verify all four files exist.
2. Compute SHA-256 and byte counts.
3. Compare them exactly with this instruction and `collection/SQUADRON_BUILD_RECORD.json`.
4. Stop only if any identity differs.

Do not rebuild to repair a mismatch. Report it.

## Step 2 — Pair and connect

Use an explicit serial for every device command.

If pairing is needed:

```bash
adb pair <PAIR_IP:PAIR_PORT>
```

Enter the owner-provided pairing code only in the interactive prompt.

Then connect:

```bash
adb connect <WATCH_IP:WATCH_PORT>
adb devices -l
```

Select the Watch7 serial explicitly. Refuse to proceed if the target is ambiguous.

Record at minimum:

```bash
adb -s <SERIAL> shell getprop ro.product.manufacturer
adb -s <SERIAL> shell getprop ro.product.model
adb -s <SERIAL> shell getprop ro.build.version.release
adb -s <SERIAL> shell getprop ro.build.version.sdk
```

Confirm the target is the owner's Wear OS watch before installation.

## Step 3 — Directly install the four finalists

The owner authorizes Claude to run `adb install -r` for these four development APKs during this session.

Install in the fixed order:

1. HAYATE
2. COMMODORE
3. PURE
4. BALSA

Use:

```bash
adb -s <SERIAL> install -r <EXACT_APK_PATH>
```

Each package has a distinct ID and may coexist with the other variants.

Stop immediately on any installation failure. Do not uninstall unrelated packages, clear watch data, or use downgrade/permission-bypass flags without a new owner decision.

## Step 4 — Verify installed identities

For each package:

1. Resolve the installed path using `pm path`.
2. Require exactly one unambiguous `base.apk` path.
3. Pull the installed APK to a temporary session directory.
4. Compute SHA-256 and byte count.
5. Confirm the pullback matches the authorized local APK exactly.

Example pattern:

```bash
adb -s <SERIAL> shell pm path <PACKAGE>
adb -s <SERIAL> pull <REMOTE_BASE_APK> <LOCAL_PULLBACK>
sha256sum <LOCAL_PULLBACK>
stat -c %s <LOCAL_PULLBACK>
```

A mismatch blocks evaluation of that variant. Do not silently reinstall or update expected hashes.

## Step 5 — Fast four-face wrist comparison

The owner manually selects each face from the Watch7 face picker. Do not infer the selected face merely from the installed package list.

Evaluate in the same fixed order:

1. HAYATE
2. COMMODORE
3. PURE
4. BALSA

For each face, keep the trial to roughly two or three minutes and collect:

- one clear awake-mode on-wrist photograph from the owner;
- one AOD on-wrist photograph if AOD is enabled and obtainable;
- one short natural wrist-tilt video, approximately 10–15 seconds;
- a quick verbal reaction covering:
  - aircraft identity: obvious or too subtle;
  - propeller hands: detailed/readable or visually confusing;
  - premium feel at real size;
  - horizon integration;
  - any immediately unreadable data.

ADB may be used for a normal-mode screencap or short screen recording when useful, but owner wrist photos remain the authority for materials, perceived depth, glare, physical scale, and AOD appearance.

Do not begin the formal 45–60 minute motion-evidence harness during this comparison session.

## Step 6 — Consolidated ranking only

After all four have been viewed, ask the owner for one consolidated result:

- first place;
- second place;
- keep/develop later;
- eliminate or substantially revise;
- best propeller hands;
- strongest vintage prop-fighter identity;
- most commercially attractive;
- whether the common PROPOSED motion feels acceptable, too strong, too weak, or should become roll-only.

Do not interrupt between variants with design-change proposals. Finish the comparison first, then summarize the pattern.

## Step 7 — Session report and stop

Report:

- repository head;
- workstation ADB version;
- Watch7 serial, manufacturer/model, Wear OS/Android version and API level;
- pairing/connect result;
- all four local APK hashes and sizes;
- all four installed pullback hashes and sizes;
- installation result for each package;
- which photos/videos were collected;
- the owner's consolidated ranking and comments;
- any immediate machine issue or installation anomaly.

Then stop for ChatGPT review.

Do not modify source, regenerate artwork, rebuild APKs, merge, release, sign, create an AAB, or start store work in this session.
