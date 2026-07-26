# AURELIUS 2.0.0-rc1 — release candidate (NOT PUBLISHED)

This is a **release candidate**, not a release. It is deliberately absent
from `releases/MANIFEST.json`: a candidate is not a published artifact and
must not be listed as one (ADR-010 §4).

`releases/aurelius/current/` is untouched and still holds the immutable
v1.0 release at `844b9c43…`.

| | |
|---|---|
| Package | `com.xsytrance.aurelius` |
| Version | 2.0.0-rc1 (versionCode 2) |
| minSdk / targetSdk / compileSdk | 36 / 36 / 36 |
| WFF version | 4 |
| Visual version | `field-tourbillon-mk2-rc1` (APPROVAL-0005, **proposed**) |
| Publication status | **not published** |

## Artifacts

| File | Role | SHA-256 | Size |
|---|---|---|---|
| `aurelius-2.0.0-rc1.aab` | distribution candidate — Play requires a Wear OS app bundle for watch faces | `ff61ca19e9c084089306ec95b0dc372d779a0ad00c482b3f6d6b3414d2c6bcf7` | 748,370 B |
| `aurelius-2.0.0-rc1-debug.apk` | sideload / device testing only | `d02bf91494f94abb5176685baea19b6e788dbd5c92d0df50c4bfde14d00c7956` | 831,637 B |

**Signing.** The APK carries the Android Debug certificate and is sideload
only. The bundle is **unsigned** — no upload key exists. Play App Signing
would hold the app signing key, and creating the developer-held upload key
is a later, separately authorised operation (ADR-010 §5). No production
signing material exists anywhere in this repository.

## Reproducibility

Both artifacts reproduced **byte-for-byte** across two independent clean
builds from the documented environment. No non-deterministic field needed
explaining.

```bash
tools/build_candidate.sh --clean --out <dir>
python3 tools/verify_candidate.py aurelius --version 2.0.0-rc1 \
    --aab <aab> --apk <apk> --write-manifest
```

## Size

The package dropped from 3,600,717 B to 831,637 B. AGP was packaging the
Kotlin runtime — 2.4 MB of `classes.dex` in a face that declares
`android:hasCode="false"` and contains no code. Removing it was also a
hard requirement: Play rejects a Watch Face Format bundle containing dex.

## Files

| File | What |
|---|---|
| `CANDIDATE.json` | the binding manifest — versions, commits, goldens, toolchain, validation, evidence, limitations |
| `VERIFY.json` | artifact inspection and cross-source identity consistency |
| `README.md` | this file |

## Not yet done

- no owner wear sessions recorded (Checkpoint B requires three);
- no physical Watch7 validation of rc1 — no device was reachable;
- Play developer account status (TEST-1) unresolved.
