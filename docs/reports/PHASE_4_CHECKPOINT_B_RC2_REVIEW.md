# Phase 4 Checkpoint B rc2 — Architecture Re-review

**Consumer repository:** `xsytrance/xsywatch`  
**Branch:** `phase-4/aurelius-release-readiness`  
**Consumer head reviewed:** `6c026357d5430a255dccda6b99c8dc404647435d`  
**Paired studio head reviewed:** `xsytrance/AGENOR-Horology@b638dfb50b8589ce2e3c11f8d31cc82a51a882d9`  
**Review date:** 2026-07-26  
**Verdict:** **CHANGES REQUESTED — original blockers materially corrected; three narrow static trust-boundary defects remain, and Checkpoint B acceptance remains blocked by device/wear evidence**

## Executive assessment

The rc2 response is strong and honest. It correctly preserves rc1 as a superseded package candidate without manufacturing a new visual generation, keeps `field-tourbillon-mk2-rc1` and APPROVAL-0005 proposed, separates consumer source/artifact/metadata roles, rebuilds AAB and APK twice from detached source worktrees, makes release-DEX removal fail-closed, removes stale permissions, introduces content-derived readiness gates, closes candidate-specific procedural-art provenance, and keeps the immutable historical release untouched.

The five original engineering blockers are substantially addressed. Three residual static defects prevent final architecture acceptance of the consumer release-candidate layer. None requires new studio rendering or pixel changes.

## Accepted corrections

The following are accepted in principle and should be preserved:

- rc1 remains immutable and explicitly superseded;
- rc2 package metadata changes do not create a false visual generation;
- `consumer_source_commit`, `consumer_artifact_commit`, and `candidate_metadata_commit` are distinct roles;
- two detached-worktree builds reproduce the canonical AAB/APK hashes;
- release DEX is parsed before deletion, cross-checked with `dexdump`, and rejected on unexpected classes;
- AAB is DEX-free;
- `ACTIVITY_RECOGNITION` and unqualified `BODY_SENSORS` are removed;
- no-permission heart-rate behavior remains honestly blocked pending Watch7 evidence;
- `READINESS.json` reports only three of thirteen gates complete and cannot treat blocker documents or empty directories as passing evidence;
- WO-P7 passes at 3.972% maximum against 15%;
- candidate-specific provenance reports zero external AI-checkpoint or donor-image pixels while preserving the repository-wide historical warning;
- 137 engine tests, 67 visual tests, 62 aperture renders, ten builds, WFF, memory, repository validation and CI are reported green;
- `releases/aurelius/current/` remains unchanged.

## Blocker 1 — artifact and metadata commit bytes are not authoritative in the lineage verifier

`tools/verify_lineage.py` proves that the declared artifact commit contains files with the expected names, but it computes the canonical artifact hashes from the **current working-tree files**:

```python
blob = path_at(args.artifact, f"{rel}/{name}")
...
canonical[name] = sha256_file(cand / name)
```

It does not hash the artifact bytes stored at `consumer_artifact_commit` or compare the current bytes to that commit's blob.

A future sequence could therefore:

1. create artifact commit A;
2. change the AAB/APK later;
3. rebuild metadata around the later bytes;
4. keep naming artifact commit A;
5. pass the current verifier if the source rebuild matches the later working-tree files.

The current rc2 data appears sound because the AAB/APK have not changed after `ea2b0e58`, but the tool does not guarantee the claim it records.

The same authority boundary applies to metadata: `metadata=auto` resolves the last commit touching `CANDIDATE.json`, but the verifier checks only that `CANDIDATE.json` and `READINESS.json` exist at that commit. It does not parse those committed blobs or reject current-tree divergence.

### Required correction

- Hash artifact bytes **at** `consumer_artifact_commit`.
- For ordinary Git blobs, hash the committed blob bytes.
- For Git LFS pointers, require the pointer OID to equal the canonical SHA-256 and verify the smudged payload independently.
- Require the current committed AAB/APK bytes to equal the artifact-commit objects.
- Read and parse `CANDIDATE.json`, `READINESS.json`, `LINEAGE.json`, and `PROVENANCE.json` from the resolved metadata commit, or explicitly reject divergence from those committed blobs.
- Require the artifact commit to contain exactly the canonical artifact set and VERIFY evidence declared for the version.

Add deliberate-failure tests for:

- AAB changed after the named artifact commit;
- APK changed after the named artifact commit;
- artifact commit containing a different artifact with the same filename;
- dirty or later metadata differing from the resolved metadata commit;
- an LFS OID mismatch;
- extra or missing canonical artifacts at the artifact commit.

## Blocker 2 — debug APK DEX is named but not classified

The release DEX gate is accepted. However, the debug APK used for physical testing contains:

- `classes.dex`
- `classes2.dex`

`verify_candidate.py` only enumerates those names and states that the debug APK may retain generated R DEX. It does not extract and parse either DEX file, so it does not prove that both contain only the intended debug/R classes or explain why two files exist.

The physical Watch7 gate will be performed against this APK. Its executable contents must therefore be understood even though Play distribution uses the DEX-free AAB.

### Required correction

- Extract every DEX from the debug APK.
- Parse and record SHA-256, size, and every defined class descriptor using the existing self-contained parser.
- Cross-check with `dexdump` when available.
- Define the allowed debug-APK class policy explicitly.
- For a resource-only `hasCode=false` package, prefer generated R classes only; any additional class must be explained and approved rather than silently accepted.
- Fail verification on unreadable, unexplained, or disallowed debug DEX.
- Correct the stale `build.gradle.kts` comment that says verification proves neither AAB nor APK contains DEX.

Add tests for:

- unexpected class in debug `classes.dex`;
- unexpected class in debug `classes2.dex`;
- unreadable debug DEX;
- two allowed R-only DEX files;
- parser/dexdump disagreement.

## Blocker 3 — candidate provenance metadata contradicts the provenance closure

`PROVENANCE.json` concludes that the repository-wide AI/donor warning is not applicable to the current Aurelius candidate. The studio report says the same.

But `CANDIDATE.json` still records:

```json
"open_owner_action": "AI-model licence position for commercial sale of generated artwork remains unresolved (docs/LICENSING.md)"
```

That is a candidate-specific contradiction. Either the provenance closure is valid, or this remains an open owner action; the manifest cannot state both.

### Required correction

- Replace the stale `open_owner_action` with an explicit scoped result referencing `PROVENANCE.json`, or remove it when there is no current-candidate action.
- Preserve `docs/LICENSING.md` unchanged for legacy products.
- Extend `check_candidate_readiness.py` to reject disagreement between candidate provenance fields and `PROVENANCE.json` conclusion/status.
- Add a deliberate-failure test for a candidate manifest claiming unresolved AI provenance while the bound provenance record says not applicable, and the inverse.

## Operational acceptance blockers — correctly still open

These are not static implementation defects and must remain blocked until real evidence exists:

1. physical Watch7 validation of APK `939d2b44…`;
2. installed-APK pullback hash;
3. installed resource/XML lineage;
4. empirical no-permission versus `READ_HEART_RATE` behavior;
5. three ordinary wear sessions bound to rc2;
6. final owner pixel/wear acceptance of APPROVAL-0005;
7. architecture approval after the evidence closes;
8. TEST-1 account facts;
9. hosted privacy-policy URL;
10. support address and response commitment;
11. owner price decision;
12. separate authorization before production signing.

TEST-1, privacy hosting, support and price are launch-policy inputs rather than excuses to misstate RC integrity. They may remain honestly blocked in an unpublished candidate.

## Studio status

The studio slice requires no additional rendering or asset change. Keep:

- producing commit `04015886dbee5cd17b66c4627f822aef3db73d16`;
- metadata commit `97ba0f1ceeee721a7a2ec0521603bd61935d036d`;
- all fifty lifecycles `candidate`;
- `CommandSatin_ReservePrecision` pixels unchanged.

## Closeout sequence

1. Fix the artifact/metadata commit-byte binding.
2. Classify and gate every debug-APK DEX file.
3. Reconcile candidate provenance metadata and readiness consistency.
4. Rerun all static gates and CI.
5. Connect the Watch7 and run permission + physical lineage validation.
6. Install the final unchanged-or-rebuilt rc2 APK and bind all device evidence to its exact hash.
7. Complete the three owner wear sessions.
8. Record owner acceptance or requested pixel changes.
9. Return both branches for final Checkpoint B review.

Do not merge, approve, promote, sign with production material, upload, publish, modify the immutable current release, or begin another product.

## Verdict

**The rc2 correction set is close and the current artifacts appear internally sound, but Checkpoint B remains CHANGES REQUESTED until commit-object lineage, debug-DEX classification, candidate-provenance consistency, physical Watch7 evidence, and owner wear acceptance are complete.**
