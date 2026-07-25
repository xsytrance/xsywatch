# Finding: repo Aurelius art assets diverged from the immutable release (caught by the device matrix, fixed)

**Date:** 2026-07-24, during the first physical-device candidate run.
**Severity:** critical (wrong design rendered); caught exactly by the
physical test the review refused to waive.

## What the device showed

The first engine-generated candidate APK
(`cb3557bd9b4902e23409e17ba3b93374f8b0b794c81908c1683520ceacdc54ae`)
installed cleanly over the baseline (`adb install -r` → Success), but the
watch rendered the **WARBIRD** design (olive fighter-fuselage art:
shark-mouth, painted eye, kill tally, FUEL/PULSE gauge faces, radial-engine
cowling) instead of the Phase-1 **Field Tourbillon** cel design — with the
correct Field Tourbillon *layout and mechanics* (gear positions, cage at 6
o'clock, gauge arc, date window all in place and animating correctly).

`candidate_warbird_regression_picker.png` preserves the capture (the
picker's live-render slot showing WARBIRD as the active face; the direct
normal-mode warbird screenshot was overwritten during the session by the
corrected re-capture).

## Root cause

`phase-1: import editable source` (`be4f8ea`) copied
`watchfaces/aurelius/app/src/main/res/` from the working project **after**
its generator (`tools/build.py`) had been switched to the WARBIRD v4
design and had regenerated the PNG assets **under the same filenames**.
Result, present in every commit since Phase 1:

- `res/raw/watchface.xml` — Field Tourbillon (correct);
- 46 of 53 `drawable-nodpi` PNGs + `drawable/preview.png` — WARBIRD art
  (wrong): `bg.png`, `bg_aod.png`, all 43 `g_*` BitmapFont glyphs,
  `hour_hand.png`, `min_hand.png`, `hub.png`, `resv_needle.png`,
  `sheen.png`;
- 7 PNGs identical in both designs (`balance.png`, `cage.png`, `gear_l.png`,
  `gear_r.png`, `tourb_base.png`, `tourb_disc.png`, `tourb_rim.png`);
- 2 stray WARBIRD-only files never referenced by the XML (`prop.png`,
  `needle.png`).

No validation layer could catch this: XML parity is semantic-XML only,
the WFF validator and memory evaluator do not judge art content, and the
resource-hash list in `BASELINE_CAPTURE.md` recorded the already-divergent
tree as "baseline". The released face's propeller bridge is baked into
`bg.png`, so even the filenames looked plausible.

This confirms the review's blocker-1 skepticism verbatim: the repository
source did **not** have byte lineage to the released APK, and the physical
test was the only gate positioned to notice.

## Fix (this commit)

The immutable Phase-1 release APK is the authoritative behavior reference
(review's own definition), so the 46 divergent PNGs + `preview.png` were
replaced with the **bytes extracted from
`releases/aurelius/current/aurelius.apk`** (`unzip`; `res/drawable-nodpi`
and `res/raw` entries are stored by AAPT2 verbatim — proven by the 7
already-identical files and by `res/raw/watchface.xml` extracting to
exactly `a8ce33ac…`, the recorded `watchface_baseline.xml` hash).
`prop.png`/`needle.png` (unreferenced strays) were deleted.

Byte lineage now holds in both directions:

- release APK `res/raw/watchface.xml` == `watchface_baseline.xml`
  (`a8ce33ac1614430ed896a72964ce96572c363a000d690a9ef4cacf2a590fd29b`) —
  the Phase-1 XML source lineage that review noted was unproven is now
  **proven by extraction**;
- every repo drawable byte-equals its release-APK counterpart.

Corrected candidate APK:
`b01015c87eea1e9b23859d98ebcae56ce808be4db7e066b3d25bc682724cc43e` —
re-installed over the previous candidate (`install -r` → Success, upgrade
continuity again preserved) and verified on-device to render the Field
Tourbillon identically to the baseline (see `candidate_*.png/mp4` evidence
and `DEVICE_TEST_RESULTS.md`).

Re-verified after the fix: `generate_face.py aurelius --check` OK;
68/68 engine tests; 10/10 release-workflow fixtures; 10/10 all-faces
build; WFF validator PASS; memory-footprint PASS; `tools/validate.py`
0 errors; `git diff --check` clean; immutable release checksum unchanged
(`844b9c430f65…`).

## Also explained by this finding

- The watch-face picker preview looked correct all along:
  `preview.png` renders the *static* thumbnail, and Phase-1's APK preview
  was cel art; only the live render exposed the wrong drawables.
- WARBIRD art remains available in the working project
  (`~/Android/Aurelius`, generator `tools/build_warbird_v4.py` and seeds) —
  nothing creative was lost by this correction; the repo face simply
  returns to the design the immutable release actually ships.
