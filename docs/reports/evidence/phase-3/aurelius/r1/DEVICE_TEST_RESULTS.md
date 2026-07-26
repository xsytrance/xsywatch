# Focused Watch7 test — revision `field-tourbillon-mk2-r1`

**Executed 2026-07-25 13:51–14:01 EDT.** Galaxy Watch7 44 mm (SM-L310,
Android 16 / API 36), wireless adb `192.168.1.183:33823` (owner-provided),
docked, battery 100% (charging; the system charging pill at 12 o'clock is
a One UI overlay, not face art).

Scope per the Phase-3 re-review: **glyphs, date, engravings, normal
legibility, AOD**, bound to the r1 artifacts.

| Binding | Value |
|---|---|
| Candidate APK | `57dad013 24a9cd014a4167a3a70c352e9633d080400af74499c4b3485cd5868a` |
| Resource inventory | `35f95830520757080d3d72db2c982e35e7d8f6f804533b394ee1ac98b2877d84` |
| Candidate references | normal `a766e444…`, aod `69a8724b…` |
| Approval record | `APPROVAL-0003` (owner status `proposed`) |
| Studio producing commit | `5c44f74` · metadata stamping commit `d0ef4a7` |
| Pre-upgrade build on watch | `d734abc8…` (the superseded mk2 candidate) |

## Results

| Check | Result | Evidence / notes |
|---|---|---|
| Install / upgrade continuity | **PASS** | `install -r` over the mk2 candidate `d734abc8…` → Success; face re-selected in the picker (documented One UI deactivation behaviour) |
| Picker | **PASS** | Listed with the regenerated r1 preview; activated by tap |
| **Glyphs (Rajdhani Bold)** | **PASS** | Date aperture renders `25` in the new OFL typeface — crisp, correctly weighted, no clipping of glyph art itself, no missing-glyph artefacts. This is the substituted artwork rendering live from the imported studio exports |
| **Date** | **PASS** | Shows the live day (25) via `[DAY]` through the BitmapFont; dynamic data path intact after the font swap |
| **Engraving — `AURELIUS`** | **PASS** | Clean, evenly spaced, legible at 1:1 (`candidate_normal_device.png`, crop verified) |
| **Engraving — `FIELD TOURBILLON Mk II`** | **PARTIALLY OCCLUDED — pre-existing, not a font regression** | The lower engraving sits behind the tourbillon well ring and is largely hidden. Verified identical in the mk2 device capture, so it originates in the plate composition, not the typeface change. Owner-visible item |
| Normal legibility | **PASS** | Gold dauphine hands over the charcoal dial read instantly; verified at 1:1 and at a half-scale proxy |
| **AOD — behaviour** | **PASS** | 10 scripted sleep/wake cycles completed (`r1_cycles.log` = 10); clean, complete render afterwards (`candidate_after_10_aod_cycles.png`) with all mechanics and the date present |
| **AOD — pixel capture** | **NOT OBTAINABLE (documented hardware limitation)** | `screencap` during verified `mWakefulness=Dozing` returns a fully black frame (extrema 0,0) — the same non-capturable doze pipeline accepted in the Phase-2 final review and Phase-3 report. Artefact kept honestly as `candidate_aod_doze_screencap_black.png`. The ambient composition is byte-determined by the CI-verified r1 AOD reference render `69a8724b…`, and the `bg_aod` bytes are sha-chained studio → manifest → APK |
| Stability | **PASS** | `logcat -b crash` clean for face/runtime; zero fatal/ANR/died entries; no resource disappearance across install, 10 cycles and recording |
| Smoothness | **PASS** | 32 s recording (`candidate_motion.mp4`), continuous cage/gear/hand motion, no stutter or dropout |
| Touch | **PASS** | Taps at three dial points plus the date window inert; `topResumedActivity` stayed SysUI |

## Finding — date digits overhang the drawn aperture frame

The date glyphs render slightly larger than the gold aperture frame baked
into the plate art, so they overhang it on the left and right.

**This is pre-existing and not caused by the typeface substitution**: the
same overhang is visible in the mk2 device capture (side-by-side crop
comparison performed). Rajdhani Bold is a chunkier face, so it is
marginally more noticeable.

Cause: the WFF `z30_date` text box is 60×28 px with BitmapFont size 24
(two ~16×24 px glyph cells ≈ 32×24 px of ink), while the frame drawn in
the plate art is ≈36×19 px inside. The art frame is simply undersized for
the text box.

Not fixed here: it is a pixel change requiring owner sign-off, and the
owner's acceptance of this revision is pending. Fix when directed —
enlarge `DateFrame` in `scripts/build_aurelius_mk2.py` (studio-side, one
parameter) and regenerate as a further revision.

## Methodological finding — device-vs-reference pixel comparison is not a usable gate for this face

Attempted rigorously and reported rather than quietly dropped. Comparing
`candidate_normal_device.png` against a reference render pinned to the
device's observed state (13:52:21, 100%, day 25, HR fallback) still
yields large deltas (mean 14.5 over the disc; 8.5% of pixels over delta
64), and even the *static* outer bezel annulus shows mean delta 23.8.

Two uncontrollable inputs explain it:

1. **Mechanical layers move at up to 40°/s** (`z10_gl` 40°/s, `z11_gr`
   24°/s, cage 6°/s). The capture instant cannot be pinned to the render
   state, and a one-second error rotates a gear by 40°.
2. **The sheen layer is accelerometer-parallaxed by up to ±40 px in X and
   ±14 px in Y.** The watch rests tilted on its dock, so the fullscreen
   sheen — which overlays the bezel and dial — is displaced by tens of
   pixels relative to any reference render, which pins accelerometer to 0.

The consequence for the architecture: the `[compare.device_profile]`
thresholds in `states.toml` are sound for a static face but cannot gate a
dynamic, parallaxed one. The device gate for Aurelius is therefore
**visual plus behavioural plus byte-chain** (studio export → handoff
manifest sha → imported resource → inventory → packaged APK), all of
which are verified above and in the phase report. Recommend recording
this explicitly in ADR-009 rather than leaving the device profile
implying a capability it cannot deliver for faces of this class.

## Files

`candidate_normal_device.png` (sha `7974eeb0…`),
`candidate_after_10_aod_cycles.png` (`656ea436…`),
`candidate_touch_test.png` (`499b94d5…`),
`candidate_aod_doze_screencap_black.png` (`be8b170a…`),
`candidate_motion.mp4` (32 s).

Capture environment restored afterwards: screen timeout 600000→60000,
heads-up notifications 0→1, stay-awake off, `/sdcard` capture files
removed.
