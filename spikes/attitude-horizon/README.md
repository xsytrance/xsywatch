# ATTITUDE horizon spike — DISPOSABLE

```
╔══════════════════════════════════════════════════════════════════════╗
║  THROWAWAY ENGINEERING EXPERIMENT.                                   ║
║  Not product code. Not product artwork. Not a release candidate.     ║
║  Nothing here may be promoted into ATTITUDE. Delete when done.       ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Branch:** `spike/attitude-horizon-watch7`
**Base:** `origin/main` @ `3333d427e9c87f1c59b26d61c41f6b9ce6435152`

## Why this base

`main` is the accepted, merged consumer baseline. It carries the
deterministic WFF infrastructure (`engine/wffgen`) and the build tooling,
and it carries **none** of the Aurelius Phase 4 candidate, readiness,
release or evidence work — those live on
`phase-4/aurelius-release-readiness` and were deliberately not inherited.
It contains no ATTITUDE production code. Its head commit adds only a Phase 4
planning document, which is a brief rather than candidate work.

It is explicitly **not** based on `cfccf30`, which is merely where the
Aurelius working branch happens to be. No Aurelius branch is merged here.

## What this answers

Only the questions a device can answer:

- are WFF accelerometer angles stable enough at rest that a still wrist
  gives a still horizon?
- do rotation and vertical translation compose correctly on-device?
- is the response direction intuitive?
- does the gain feel premium or twitchy?
- does AOD truly freeze neutral?
- does the letterbox aperture stay covered at every reachable state?

## Identity

| | |
|---|---|
| Base package | `com.xsytrance.attitude.spike` |
| Label | ATTITUDE Horizon Spike |
| Version | `0.0.1-spike`, versionCode 1 |
| Status | disposable engineering experiment; no store or release identity |
| Artifacts | **debug APKs only** |

Three independently installable variants, so they can be compared on the
watch without reflashing:

| Profile | Displayed roll | Displayed pitch | Application ID |
|---|---|---|---|
| DAMPED | ±14° | ±14 px | `com.xsytrance.attitude.spike.damped` |
| PROPOSED | ±22° | ±26 px | `com.xsytrance.attitude.spike.proposed` |
| ASSERTIVE | ±30° | ±34 px | `com.xsytrance.attitude.spike.assertive` |

All three clamp wrist roll at ±45° and wrist pitch at ±40°, map neutral
exactly to zero, are monotonic and symmetric, and force roll = 0 and
pitch = 0 in AOD.

## Deliberately crude

Greyscale plus one muted amber, a rounded letterbox aperture, an oversized
geometric sky/ground field, a crude pitch ladder, a fixed neutral index,
four reference ticks, plain placeholder bars for hands, and a `SPIKE`
marker. **No final SEXTANT art, no studio typography, no designed hands, no
complications, no wordmarks, no external references, no aircraft imagery.**

It is meant to look unmistakably experimental so none of its pixels could
drift into production.

## How it works

WFF has no mask primitive for a `PartImage`, so the horizon is **occluded,
not masked**: the oversized field is drawn first, then a plate with a
*transparent aperture* is drawn over it. Everything outside the aperture is
opaque plate. This is why the field must be oversized — at the travel
extremes the hole must still be entirely covered.

The generator is **spike-local by design**. It does not import or modify
`engine/wffgen`: a disposable experiment must not put pressure on the
shared engine, and no reusable horizon component is extracted. The
duplication is deliberate.

## Commands

```bash
python3 spikes/attitude-horizon/generate_spike.py          # regenerate
python3 spikes/attitude-horizon/generate_spike.py --check  # determinism
./spikes/attitude-horizon/build_spike.sh                   # 3 debug APKs
python3 -m unittest discover -s spikes/attitude-horizon/tests
python3 spikes/attitude-horizon/device_harness.py          # plan only
```

## Offline gates proved

Deterministic XML and resource generation; WFF v4 validation PASS on all
three; **zero declared permissions**; AOD statically neutral (constant
`AMBIENT` variants, never an expression); positive coverage margin for
every profile at both signs of the simultaneous extremes; distinct package
IDs; debug APKs byte-identical across a clean rebuild; no AAB; no signing
or release files; no Aurelius, shared-engine or product-face file touched.

Deliberate-failure fixtures cover excessive roll gain, excessive pitch
travel, a missing clamp, an asymmetric mapping, a moving AOD, an undersized
field, duplicate package IDs, accidental AAB generation and shared-engine
modification.

## NOT installed

**No installation has occurred.** The device harness is prepared and
refuses to act without an explicit owner-initiated `--run`, and even then
it does not auto-install: it prints the command and stops. Installation
waits until AGENOR is home and starts the session.

Owner answers live in `OWNER_COMPARISON.json`, fail-closed: every answer
starts `PENDING` and stays `PENDING` until given explicitly. **26 answers
are outstanding.** Nothing is inferred from a measurement or from silence.

## When the spike is finished

Record the owner decision — a profile, reduced motion, roll-only, static,
or reactive motion rejected — and then **delete this directory**. Its
purpose is to produce a decision, not an artifact.
