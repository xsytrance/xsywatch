# 2.0.0-rc1 — SUPERSEDED, unapproved historical candidate

**Status: superseded by 2.0.0-rc2. Never approved, never published.**

Preserved unchanged as evidence, exactly as ADR-009 §5 preserves
superseded visual generations. Nothing in this directory is rebuilt,
rewritten, or deleted.

## Why it was superseded

The Phase 4 Checkpoint B review
(`docs/reports/PHASE_4_CHECKPOINT_B_CHATGPT_REVIEW.md`) returned CHANGES
REQUESTED. Three of the required corrections change package bytes, so they
could not be applied to rc1 without invalidating its recorded hashes:

1. **fail-closed dex gate** — rc1's build deleted every release dex
   without inspecting it (blocker 3);
2. **manifest permissions** — rc1 declared `BODY_SENSORS` and
   `ACTIVITY_RECOGNITION`, both invalid or unused on an API-36-only
   package (blocker 4);
3. **consumer lineage** — rc1's `CANDIDATE.json` attributed its artifacts
   to a `consumer_commit` that predated the packaging work which produced
   them (blocker 2).

Blocker 2 is a defect in rc1's *record*, not its bytes. It is left
uncorrected here on purpose: rewriting a superseded candidate's manifest
to look correct would destroy the evidence of what was actually claimed.
The correction lives in rc2, which carries explicit
`consumer_source_commit` / `consumer_artifact_commit` /
`candidate_metadata_commit` roles.

## What rc1 recorded

| | |
|---|---|
| Version | 2.0.0-rc1, versionCode 2 |
| AAB | `ff61ca19e9c084089306ec95b0dc372d779a0ad00c482b3f6d6b3414d2c6bcf7` |
| Debug APK | `d02bf91494f94abb5176685baea19b6e788dbd5c92d0df50c4bfde14d00c7956` |
| Visual version | `field-tourbillon-mk2-rc1` (APPROVAL-0005, proposed) |
| Publication status | not published |
| Device evidence | blocked |
| Wear evidence | none |

## What carried forward unchanged

The **visual pixels did not change.** rc2 uses the same
`field-tourbillon-mk2-rc1` generation and the same APPROVAL-0005 record.
No new visual generation was manufactured merely because package metadata
moved — the corrections are packaging, manifest and provenance only, and
no runtime visual resource differs between rc1 and rc2.

Successor: `releases/aurelius/candidates/2.0.0-rc2/`.
