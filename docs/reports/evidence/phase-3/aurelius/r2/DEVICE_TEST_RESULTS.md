# Focused Watch7 test — revision `field-tourbillon-mk2-r2`

**Executed 2026-07-26 13:19–13:33 EDT.** Galaxy Watch7 44 mm (SM-L310,
Android 16 / API 36), wireless adb `192.168.1.183:36715` (owner-provided),
docked, battery 100% (wireless charging; the system charging pill at
12 o'clock is a One UI overlay, not face art).

Scope per the Phase-3 r1 review §"Focused Watch7 closure": **date inside
the enlarged aperture, frame integration at actual scale, absence of the
lower engraving with no awkward void, `AURELIUS` legibility, normal/AOD
transitions, motion, stability, touch**, bound to the r2 artifacts.

| Binding | Value |
|---|---|
| Candidate APK (verified from device bytes) | `5a1271ab95c9fdbc04c1b8b5781a40cea2cb4ca11f279c69cb70aeb23f50474a` |
| Resource inventory | `b76f9ceb01b555a4915448bb8408e8d008937c484913b033491f5c9e3875c269` |
| Candidate references | normal `7fd2cf63…`, aod `2f2be0e9…` |
| Approval record | `APPROVAL-0004` (owner status `proposed`) |
| Studio producing commit | `c8c29dc` · metadata stamping commit `5cf8f04` |
| Pre-upgrade build on watch | `57dad013…` (the superseded r1 candidate) |

The APK hash above was not taken on trust from the build directory: the
installed `base.apk` was pulled back off the watch and hashed. It equals
the recorded r2 candidate exactly. The pre-upgrade pull likewise equals
the r1 candidate exactly, so this is a verified r1 → r2 upgrade.

## Results

| Check | Result | Evidence / notes |
|---|---|---|
| Install / upgrade continuity | **PASS** | `install -r` over the r1 candidate `57dad013…` → Success. Installed bytes pulled back and hashed = `5a1271ab…`. The face stayed active through this upgrade (no picker re-selection was needed) |
| Runtime host | **PASS** | `dumpsys activity service com.samsung.wear.watchface.runtime` → `Resource only package name com.xsytrance.aurelius` |
| **Date inside the enlarged aperture** | **PASS** | Live day `26` sits fully within the drawn frame with visible clear space on all four sides (`candidate_date_aperture_crop.png`, 10× nearest-neighbour). Measured from the device pixels: inner aperture **40 × 30 px**, glyph bbox 31 × 24 px, **minimum clear margin 2 px** — stable across ink thresholds median+8 … median+16. See qualification below |
| **Aperture geometry vs reference** | **PASS** | The inner opening measures **40 × 30 px on the device and 40 × 30 px in the committed r2 reference render** — the enlarged geometry reached the panel intact |
| **Frame integration at actual scale** | **PASS** | The larger frame reads as part of the plate, does not collide with the right gear or the cage, and does not compete with the hands. Confirmed at 1:1 and at a half-scale proxy |
| **Lower engraving absent** | **PASS** | `FIELD TOURBILLON Mk II` is gone from the plate. Side-by-side crop against the r1 device capture shows the crammed dark lettering under the tourbillon ring in r1 and clean dial in r2. **No awkward void** — the area reads as intentional negative space |
| **Engraving — `AURELIUS`** | **PASS** | Clean, evenly spaced, legible at 1:1 and still readable at half scale |
| Normal legibility | **PASS** | Gold dauphine hands over the charcoal dial read instantly; date legible at half scale |
| **AOD — behaviour** | **PASS** | 10 scripted sleep/wake cycles completed (`r2_cycles.log` = 10 lines); clean, complete render afterwards (`candidate_after_10_aod_cycles.png`) with all mechanics, hands, date and the `AURELIUS` engraving present. No resource loss |
| **AOD — aperture coherence** | **PASS** | The AOD plate draws the aperture as a thin power-efficient outline, **exactly concentric with the normal opening** (both centred at 321.5, 299.5; AOD outline 44 × 34 px tracing the 40 × 30 px normal inner opening). Requirement 7 of the r1 review is met in the shipped plate bytes |
| **AOD — pixel capture** | **NOT OBTAINABLE (documented hardware limitation, unchanged)** | Two `screencap` attempts at verified `mWakefulness=Dozing` (45 s and 75 s into doze) both returned the same fully black 1975-byte frame, extrema (0,0). Kept honestly as `candidate_aod_doze_screencap_black.png` — byte-identical (`be8b170a…`) to the r1 artifact, i.e. the same non-capturable doze pipeline accepted in the Phase-2 final review, not an r2 regression |
| **AOD — byte lineage instead** | **PASS** | Since the ambient frame cannot be photographed, it is proved by bytes: `bg_aod.png` and `bg.png` extracted from the *installed* APK are byte-identical to the repository sources (`aafb7e04…`, `f3452917…`), as is `res/raw/watchface.xml` (`6278f26c…`). The ambient composition is therefore the CI-verified r2 AOD reference render `2f2be0e9…` |
| Stability | **PASS** | `logcat -b crash` contains zero entries matching the face or runtime; zero `FATAL EXCEPTION` / `ANR in` / `died` in the main buffer across install, 10 cycles and recording |
| Smoothness | **PASS** | 32.17 s recording (`candidate_motion.mp4`, 320 frames ≈ 9.95 fps as captured by `screenrecord`). Per-region inter-frame analysis: left gear mean Δ 11.40, right gear 7.02, cage 7.61, with only **1 near-static pair out of 319** in each region — a single duplicated encoder frame, no stutter or dropout. The fastest layer (`z10_gl`, 40°/s) shows the largest delta, consistent with spec |
| Touch | **PASS** | Taps at the dial centre, the date window and the left gear were inert; `topResumedActivity` stayed `SysUiActivity` |

## Qualification on the on-device margin measurement

The 2 px minimum measured above is a *corroborating* figure, not the
authoritative one. It is derived from a composited device frame in which
the accelerometer-driven sheen overlays the gold frame and the panel
applies its own anti-aliasing, so both the frame edge and the glyph edge
are threshold-dependent. Measured against the committed reference render
the same way, the margins come out L4 R3 T3 B3 — matching the
deterministic proof's 3.07 px worst case — while the device frame reads
L2 R7 T4 B2. The ~3 px lateral difference tracks a uniform bias in
locating the sheen-lit frame edge, not a moved glyph; the aperture
*size* measures identically (40 × 30) in both.

**The authoritative containment proof remains the deterministic one**:
62 renders (days 1..31 × normal/AOD), 0 violations, worst margin 3.07 px,
enforced by `tests/visual/test_date_aperture.py`. The device test
confirms that result rather than replacing it, which is exactly the
`qualitative-behavioral-lineage` device mode recorded in ADR-009 §6a.

## Device-vs-reference pixel comparison

Not re-attempted as a gate, and deliberately so. The r1 evidence
established that a direct device-to-reference pixel comparison is not
meaningful for this face — mechanical layers move at up to 40°/s and the
sheen is accelerometer-parallaxed by up to ±40 px, neither of which can
be pinned at capture time. That finding is now recorded architecturally
in ADR-009 §6a and in the face contract's `[device_validation]` block
(`mode = "qualitative-behavioral-lineage"`), and
`tools/compare_visuals.py --mode device` refuses to emit a verdict for
such a face. The device gate applied here is therefore the one the
contract actually declares: **visual inspection + behavioural validation
+ exact byte lineage**, all satisfied above.

## Files

`candidate_normal_device.png` (`76de1b18…`),
`candidate_after_10_aod_cycles.png` (`63bca011…`),
`candidate_date_aperture_crop.png` (`f60e2ebb…`),
`candidate_touch_test.png` (`f1c8634c…`),
`candidate_aod_doze_screencap_black.png` (`be8b170a…`),
`candidate_motion.mp4` (`1acfa493…`, 32.17 s),
`r2_cycles.log` (`0bd732d5…`, 10 cycles).

Capture environment restored afterwards: screen timeout 600000→60000,
heads-up notifications 0→1, stay-awake off, `/sdcard` capture files and
scripts removed.

## Standing decision

Nothing is promoted by this test. `owner.status` remains `proposed`,
`architecture_review` remains `pending`, `approved_version` remains
`field-tourbillon-v1`, and `goldens/` still contains only v1. Final
pixel acceptance of r2 is the product owner's call.
