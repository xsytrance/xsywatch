# Phase 4 Checkpoint B — rc2 architecture re-review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `phase-4/aurelius-release-readiness`  
**Head reviewed:** `e55068fa841cbba8ef98d8685211ee0a1dacae10`  
**Candidate:** `2.0.0-rc2`  
**Visual generation:** `field-tourbillon-mk2-rc1`  
**Date:** 2026-07-26  
**Verdict:** **STATIC ARCHITECTURE CONDITIONALLY APPROVED — FINAL CHECKPOINT B ACCEPTANCE REMAINS BLOCKED**

## Executive verdict

The three static trust-boundary blockers from `PHASE_4_CHECKPOINT_B_RC2_REVIEW.md` are closed:

1. artifact and metadata authority is commit-object based rather than current-working-tree based;
2. both debug-APK dex files are classified, with a release-only R-class allowlist and an explicit device-test-only allowlist for four D8/R8 desugaring stubs;
3. `CANDIDATE.json` and `PROVENANCE.json` now agree that current Aurelius runtime pixels contain no external AI-checkpoint or donor-image contribution.

The following rc2 identities remain accepted:

- AAB `1a2ae1386a5bacc70e2316c6562d50a9ec083b35b3038ecf5e564526f18a3b23`;
- debug APK `939d2b44b51557dc7f8598870d32af2f6f9cdb7c30472d17376332cb149012fc`;
- consumer source commit `f6f00663`;
- consumer artifact commit `fa995ffa`;
- consumer metadata commit `61f54c46`;
- studio producing commit `04015886dbee5cd17b66c4627f822aef3db73d16`;
- studio metadata commit `97ba0f1ceeee721a7a2ec0521603bd61935d036d`;
- proposed normal golden `23e1d8e83f642d751ec3ad0c7cf1037faf8359b87ed31288a359a09d81c1d790`;
- proposed AOD golden `3e340f4379e1ca8462071761c8c46b8e0e292a7614ac9a2ccde7454a6af934aa`;
- inventory `1ec66797d1f4fdbf123e68240662ec256f056e8429941871e89cf675310359ce`.

No rc3 is required merely because a source comment changed when two detached source-commit rebuilds prove that the package bytes remain identical.

## Permission decision

The no-permission candidate is accepted as the correct rc2 package posture.

Evidence shows:

- the package declares zero permissions;
- the declarative WFF runtime, not the resource-only package, owns the sensor connection;
- balance frequency reads 103.8 and 104.1 bpm while the watch reports approximately 104 bpm;
- those values are materially distinct from the exact 70 bpm fallback.

Therefore `android.permission.health.READ_HEART_RATE` must not be added to rc2. The unshipped granular-permission variant remains useful as reproducibility evidence, not as the selected product.

The full matrix must still capture:

- post-exertion live-rate rise;
- off-wrist fallback to 70 bpm;
- no prompt and no package permission entry.

Those observations complete behavioral confirmation; they do not reopen the static package decision unless the results contradict the existing evidence.

## Ruling 1 — readiness dependency graph

The current dependency direction is incorrect:

```text
installed-APK-hash-verified -> device-validated
```

An installed-byte pullback is independent evidence and a prerequisite for trusting the broader visual matrix. It is not logically downstream of the full matrix.

Adopt this DAG:

```text
assembled
  -> consumer-lineage-verified
  -> dex-gate-passed
  -> permissions-verified

consumer-lineage-verified
  -> installed-APK-hash-verified

installed-APK-hash-verified
  -> installed-resource-lineage-verified

installed-resource-lineage-verified + permissions-verified
  -> device-validated

device-validated
  -> owner-wear-complete
owner-wear-complete
  -> owner-pixel-approved
```

Exact required changes:

```python
"installed-APK-hash-verified": ("consumer-lineage-verified",),
"installed-resource-lineage-verified": ("installed-APK-hash-verified",),
"device-validated": (
    "installed-resource-lineage-verified",
    "permissions-verified",
),
```

This is not a relaxation to improve a score. It corrects causal direction and makes the full matrix depend on proof that the intended bytes are installed.

After the graph change, the two installed-byte gates may be set to `complete` only if their current evidence passes all existing content/hash checks. Add dependency tests proving:

- installed hash cannot complete before consumer lineage;
- resource lineage cannot complete before installed hash;
- device validation cannot complete before installed-resource lineage and permission verification;
- the installed-byte gates do not require owner visual judgment.

## Ruling 2 — readiness freshness

Freshness should be machine-enforced for machine-derived facts. It should not depend solely on a human remembering to rewrite stale prose.

Do not attempt to infer truth from timestamps alone. Instead:

1. For every readiness gate, define the canonical evidence path set.
2. Compute a deterministic evidence fingerprint from sorted repo-relative paths plus SHA-256 values. For directories, include every committed evidence file recursively.
3. Record for each evaluated gate:
   - `evidence_fingerprint`;
   - `evaluated_at_commit`;
   - `checker_schema` or tool version.
4. Recompute fingerprints during readiness checking and reject stale records when the evidence set or bytes changed.
5. Generate machine-derived `detail` and summary text where practical. Keep subjective prose in a separate `owner_note` or `reviewer_note` field.
6. Reject a detail/state combination that references a blocker condition no longer present in the canonical evidence set.

The preferred design is eventually:

```text
READINESS_INPUT.json     owner/reviewer decisions, waivers, notes
READINESS.json           generated machine-derived state record
```

A smaller Phase 4 implementation may retain one file if the evidence fingerprints and generated state summaries are sufficient. Do not let this governance improvement block the live matrix; implement and test it before final Checkpoint B review.

## Ruling 3 — `device_matrix.py` owner/measured boundary

The owner/measured split is architecturally correct. The tool should never decide whether the face looks premium, restrained, readable, or aesthetically accepted.

The following remain owner rows:

- parallax impression and clipping;
- actual-scale normal legibility;
- Command Satin visual quality;
- reserve-tick usefulness and restraint;
- absence of unintended ornament;
- AOD visual restraint;
- battery-gauge plausibility;
- time/date visual correctness;
- post-exertion and off-wrist contextual interpretation;
- final owner disposition.

Before first production use of the harness, make these narrow corrections:

### A. Motion cannot pass when only one region moves

Current logic passes `Smoothness / motion` when any parsed region exceeds the motion threshold. That is too weak for a face with several specified moving mechanisms.

Read component type/speed from `face.toml` and emit per-component measured rows. At minimum, require every continuously moving high-rate Aurelius mechanism expected during the capture to show non-static deltas:

- left gear;
- right gear;
- tourbillon cage;
- HR-driven balance.

Minute/hour hands may use a longer start/end-angle or visual-owner check if a sixty-second capture cannot robustly distinguish them. Do not claim the whole mechanical matrix passed because one gear moved.

### B. Make sixty seconds the default

Checkpoint B requires at least sixty seconds of motion evidence. Change the default from 32 seconds to 60 seconds, while retaining an explicit override for tests.

### C. Split AOD transition mechanics from visual integrity

The tool may automatically pass `10/10 wake/sleep transitions` when wakefulness telemetry passes. The existence of a post-cycle screenshot does not prove that the render is visually complete.

Report separately:

- measured transition result;
- post-cycle screenshot captured;
- owner visual inspection of the post-cycle frame.

### D. Runtime-host selection is measurable

If the package is not named by the active WFF runtime, report `BLOCKED — face not selected`, not `PENDING — owner`. Selection is an owner action; active-host state is machine-measurable.

### E. Heart-rate wording

The tool may pass `live data distinct from fallback` when measured frequency is clearly not 70 bpm. Matching the panel's displayed/known heart-rate reading and interpreting post-exertion/off-wrist context remain owner observations.

### F. Preserve fail-closed behavior

Retain:

- right-name/wrong-bytes detection;
- raw `watchface.xml` verification;
- missing/unreadable resource failures;
- owner rows never defaulting to PASS;
- `READINESS.json` never being edited automatically by the matrix runner.

## Launch-input ruling

The launch-decision sheet is accepted as the correct owner-input boundary. These facts must not be guessed:

- Play account type;
- account creation period;
- current Production access;
- prior production-access app;
- actual support address;
- response-time commitment;
- privacy-policy hosting confirmation;
- price and initial markets.

Architecture recommendation, still requiring owner acceptance:

- price: **$3.99 one-time**;
- support response target: **within three business days**;
- privacy path: `https://x1c7.com/privacy/aurelius` on the existing x1c7.com deployment;
- support alias: `support@x1c7.com` if that mailbox or forwarding alias is actually provisioned;
- initial markets: all Play-supported paid markets where the English listing and support posture are acceptable, unless the owner deliberately chooses a narrower launch.

Do not record the recommended email as fact until delivery/forwarding is tested.

## Acceptance state

The static architecture is conditionally approved. Final Checkpoint B acceptance remains blocked by:

1. first live run of the corrected full device matrix;
2. completion of all owner rows;
3. three wear sessions bound to rc2;
4. explicit owner pixel/wear disposition;
5. launch-decision facts;
6. final readiness re-derivation with freshness enforcement;
7. final architecture review.

`APPROVAL-0005` remains owner `proposed`, architecture `pending`. No golden, lifecycle, branch or release promotion is authorized.

## Boundaries

Do not:

- merge either Phase 4 branch;
- approve or promote APPROVAL-0005;
- promote studio lifecycles;
- modify rc2 artifact bytes;
- create rc3 unless package bytes genuinely change;
- create production signing material;
- upload or publish;
- modify `releases/aurelius/current/`;
- begin another product.
