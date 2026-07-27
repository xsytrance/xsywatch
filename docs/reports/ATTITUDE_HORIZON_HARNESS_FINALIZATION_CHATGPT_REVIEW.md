# ATTITUDE Horizon Spike — Harness Finalization ChatGPT Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `spike/attitude-horizon-watch7`  
**Commit reviewed:** `169a18ca85cf925a92fee739e01bdac3799b9718`  
**Verdict:** **HARNESS ARCHITECTURE ACCEPTED; DEVICE SESSION STILL BLOCKED ON FINALIZATION-INTEGRITY PATCH**

## Accepted

The harness now implements the required executable workflow:

- `plan`;
- `session-init`;
- `verify-installed`;
- `capture`;
- `extract-frames`;
- `analyze`;
- `finalize`.

It remains structurally unable to install an APK, keeps installation manual and owner-initiated, binds sessions to device and APK identity, preserves raw evidence, records deterministic frame extraction, performs unsmoothed horizon analysis, and keeps owner observations fail-closed.

The follow-up isolation-gate correction is accepted. The earlier red-test push is transparently recorded rather than amended away, and the new direct product-path prohibition is stronger than the original broad prefix check. The three accepted APKs remain unchanged.

## Blocking defect: finalization trusts presence rather than validity

`cmd_analyze` correctly records a resting capture with too few measurable frames as `status: BLOCKED`. However, `cmd_finalize` currently checks only that an analysis entry exists for each mandatory video capture. It does not require that the analysis status is `MEASURED` or otherwise explicitly acceptable.

Therefore a session can contain a mandatory analysis record whose own result is `BLOCKED` and still advance to `PENDING_OWNER_REVIEW` as though the machine evidence were complete.

The existing successful-finalization test reinforces this weakness by inserting placeholder analysis records and hashes without requiring the referenced files or bindings to exist.

This violates the intended fail-closed contract and must be corrected before any physical session begins.

## Additional integrity closure required

Finalization must independently revalidate the evidence it is about to summarize. It must not trust only the index fields already stored in `SESSION.json`.

At minimum it must:

1. Require every mandatory video analysis to have an allowed successful status. A stored `BLOCKED`, missing, malformed or unknown status is a blocking problem.
2. Resolve each analysis file, require it to exist, verify its recorded SHA-256, parse it, and verify its capture ID, variant, built APK hash, installed pullback hash, device identity, raw-capture hash and frame-manifest hash against the session.
3. Resolve every mandatory raw capture, require it to exist when the disposition claims capture success, and recompute its SHA-256. A stored hash field alone is not sufficient.
4. Resolve every mandatory frame manifest, verify its file hash, source-video hash and frame inventory, and require each listed frame to exist and match its hash.
5. Treat a mandatory normal screenshot that is missing or `NOT_OBTAINABLE` as blocking. The AOD screenshot may remain explicitly non-obtainable because of the known doze pipeline limitation.
6. Treat partial AOD cycling, crash/ANR findings, mask-edge exposure, or any mandatory machine finding as an ISSUE/BLOCKED disposition rather than machine-complete owner review.
7. Check mask-edge exposure across the relevant motion evidence, not only one midpoint frame, so clipping at an extreme cannot be missed.
8. Require frame extraction to check the `ffmpeg` return code and reject zero-frame output. Record an explicit disposition when actual frame count materially diverges from the declared capture duration.
9. Preserve the distinction between machine failure, machine issue, non-obtainable evidence and owner preference. Owner answers can never convert failed machine evidence into a pass.

## Current authorization

- Preserve the three byte-identical debug APKs.
- Patch only the harness, evidence schema and offline tests.
- Do not install or contact the Watch7.
- Do not change watchface XML, artwork, package identities or APK bytes.
- Do not modify Aurelius, shared-engine, release, signing, store or production ATTITUDE paths.
- Do not begin the device session until this review is answered and re-reviewed.
