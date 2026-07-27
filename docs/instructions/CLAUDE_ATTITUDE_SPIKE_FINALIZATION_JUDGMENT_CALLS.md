# Claude Judgment Calls — ATTITUDE Spike Finalization Integrity

**Repository:** `xsytrance/xsywatch`  
**Branch:** `spike/attitude-horizon-watch7`  
**Apply on top of:** `aeea5be467a6f2165bb00683da6b99e1035c2af9`

This file intentionally records the parent commit on which the decision applies rather than an “expected current head.” A file cannot name the commit that will contain itself without recreating the same self-reference problem already solved for the studio evidence.

## Decision

**Proceed with the finalization-integrity patch.**

The scope in `CLAUDE_NEXT_TASK_ATTITUDE_SPIKE_FINALIZATION_INTEGRITY.md` remains authoritative. The two open judgment calls are resolved below.

Nothing may be installed and no physical device may be contacted during this assignment.

## 1. Frame-count and duration policy

Do not derive extraction success solely from the intended capture duration. Separate two different questions:

1. Did frame extraction faithfully decode the video that actually exists?
2. Did the device recording itself run long enough to satisfy the intended test duration?

### Actual media duration

Use `ffprobe` to record the actual source-video duration.

Record at minimum:

- ffprobe version;
- exact ffprobe command;
- actual duration in seconds;
- intended duration in seconds;
- duration ratio;
- expected extracted-frame count derived from actual duration;
- actual extracted-frame count.

### Extraction-integrity rule

For fixed-rate extraction at 30 fps:

`expected_from_media = round(actual_media_duration_seconds * 30)`

Extraction is acceptable only when:

- ffmpeg exits successfully;
- at least one frame is produced;
- every emitted frame is hashed and listed;
- actual extracted count differs from `expected_from_media` by no more than:
  - two frames, or
  - one percent of `expected_from_media`,
  - whichever tolerance is larger.

A count outside that extraction tolerance is `BLOCKED`, because it indicates an extraction or metadata-integrity problem rather than merely a short device capture.

### Capture-duration disposition

Compare actual media duration against the intended duration:

- **PASS:** actual duration is at least 95% of intended duration;
- **PARTIAL:** actual duration is at least 80% but below 95%;
- **BLOCKED:** actual duration is below 80%.

`PARTIAL` and `BLOCKED` both prevent machine-complete finalization. The distinction exists for diagnosis only; neither may advance to owner review as complete evidence.

Boundary tests are required at exactly 80% and 95%, immediately below both thresholds, and for extraction count at the exact tolerance boundary and one frame beyond it.

Do not use the originally proposed 50% lower boundary. Half-length recordings are not credible substitutes for the declared 30-second or 60-second protocols.

## 2. Full-frame clipping scan

Use a **full scan of every extracted frame** for each relevant motion capture. Do not substitute periodic sampling.

The implementation may and should be optimized, but optimization must not change coverage:

- precompute the inset aperture mask once;
- inspect only the aperture bounding box;
- use Pillow operations, array operations, or another deterministic method rather than repeatedly walking the entire 480×480 image in pure Python;
- preserve the existing inset that excludes rim anti-aliasing;
- do not smooth, interpolate, or discard frames.

Record:

- total extracted frames;
- total scanned frames;
- scan coverage percentage, which must be 100%;
- runtime;
- uncovered-frame count;
- maximum uncovered pixels in any frame;
- maximum uncovered percentage;
- first exposed frame, if any;
- worst exposed frame, if any;
- last exposed frame, if any;
- hashes of those identified frames;
- measured horizon angle and displacement for identified frames when measurable.

Any genuine uncovered aperture pixel inside the validated inset is a machine `ISSUE` and blocks completion. Do not let owner preference waive clipping.

Report the actual runtime. Do not silently introduce sampling merely because the full scan is slower than expected.

## 3. Preserve all accepted boundaries

The patch may change only the harness, its evidence schema, documentation, and offline tests.

It must not change:

- any spike watchface XML;
- any spike artwork;
- application IDs;
- motion profiles;
- APK bytes;
- shared WFF engine;
- Aurelius;
- production ATTITUDE;
- release, signing, packaging or store state.

All three APKs must remain byte-identical after a full clean rebuild.

## 4. Stop condition

Complete the integrity patch, run the full offline suite, rebuild and verify the three APKs, commit and push, then stop.

Do not begin a device session. The patched harness must be re-reviewed before any Watch7 installation or contact occurs.
