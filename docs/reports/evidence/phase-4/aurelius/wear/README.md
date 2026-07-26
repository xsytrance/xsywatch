# AURELIUS — Phase-4 owner wear-test packet

This is the evidence area for ordinary-use wear observations. Scripted
matrices prove correctness; wearing the watch is the only thing that
reveals product friction (ADR-010 §7).

## For AGENOR — how to record a session

After wearing the watch, run:

```bash
python3 tools/wear_log.py
```

It asks one question at a time and writes the session for you. **Press
Enter to skip anything you did not observe** — a blank field is honest
evidence; a guessed one is not. You never need to open a JSON file or edit
`WEAR_LOG.md` by hand.

Other commands:

```bash
python3 tools/wear_log.py --show       # one line per session recorded
python3 tools/wear_log.py --validate   # schema + artifact-binding check
python3 tools/wear_log.py --render     # rebuild WEAR_LOG.md from sessions/
```

Then commit:

```bash
git add docs/reports/evidence/phase-4 && git commit
```

## What to try to cover

Ideally across several ordinary sessions rather than one scripted dock test:

- a normal workday;
- outdoor / daylight exposure;
- a low-light or evening period;
- sustained AOD use;
- at least one charging transition.

## Layout

```
wear/
  README.md            this file
  BASELINE.md          objective facts already known from Phase 3
  WEAR_LOG.md          generated roll-up — do not hand-edit
  sessions/            one JSON per session, written by the tool
```

## Battery honesty rule

`WEAR_LOG.md` labels every battery figure as experiential. An informal
start/end reading is not a controlled measurement and must not be converted
into an efficiency claim in release copy (phase scope §8, ADR-010 §9).
`docs/KNOWN_LIMITATIONS.md` already records that per-face battery impact is
anecdotal; nothing in this packet changes that until a controlled method
exists.

## Artifact binding

Every session records the exact build it was observed on. At Checkpoint A
that is the tested Phase-3 candidate:

| Field | Value |
|---|---|
| APK SHA-256 | `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a` |
| package | `com.xsytrance.aurelius` |
| version | 1.0 (versionCode 1) |
| visual version | `field-tourbillon-mk2-r2` (APPROVAL-0004) |
| device | Samsung Galaxy Watch7 44 mm (SM-L310, Android 16 / API 36) |

`--validate` fails a session whose artifact hash does not match, so an
observation can never drift away from the build it describes. At
Checkpoint B the binding is repointed at the release candidate and new
sessions are recorded against that artifact.

**Rebuild note:** the APK above is not committed. Rebuild it with
`tools/build_all.sh` before installing — see
`docs/reports/PHASE_4_BASELINE.md` §0.
