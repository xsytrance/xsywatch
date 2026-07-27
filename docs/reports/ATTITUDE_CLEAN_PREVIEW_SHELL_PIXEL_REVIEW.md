# ATTITUDE Clean Preview Shell — Pixel Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `preview/attitude-motion-shell`  
**Implementation reviewed:** `3c04efc8de6a1381d90c733605e339b4f37dd1f8`  
**Verdict:** **APPROVED FOR PREVIEW-ONLY DISTRIBUTION**

## Evidence inspected

Direct visual inspection used owner-uploaded phone screenshots showing:

- `NORMAL_PROPOSED.png`;
- `MOTION_STATES_PROPOSED.png`;
- `AOD_COMPARISON.png`;
- `NORMAL_COMPARISON.png`.

Uploaded screenshot SHA-256 values:

- `13840.png`: `0bd941ae6a6e48101e9f0a2898ccaeade0b268cffc6c8ae0307bd7f6cfb914f6`;
- `13839.png`: `e590f0617288471234c4b433f74bccc970ffdde102d8cd824eab035405fa71c2`;
- `13838.png`: `377683a975a92f0a5e6e1b3c51c1d22ae63df5543b69c954088b8acc84d3555b`;
- `13837.png`: `7ae765ad1a178e6a55b4cd0ad23982b64685653760cd1719cd42bce6ddbcdfef`.

These are screenshots rather than the original committed PNG bytes, so they establish qualitative pixel approval, not independent hash verification of the committed review files.

## Visual ruling

The clean shell successfully removes the visual contamination caused by the deliberately crude engineering spike.

Accepted qualities:

- time, ATTITUDE title, horizon aperture, profile name and `MOTION PREVIEW` disclosure have a clear hierarchy;
- the blue/umber split is immediately legible as an artificial horizon;
- the fixed amber datum remains visually separate from the moving horizon;
- roll-left, roll-right, pitch-up, pitch-down and combined-extreme states are distinguishable at a glance;
- no visible horizon-field leakage or uncovered corners appear in the reviewed states;
- the three profiles are visually identical in neutral mode except for their labels, as intended;
- AOD is neutral, restrained and substantially cleaner than normal mode;
- there are no analog hands or pseudo-digital glyphs competing with the interaction test.

The shell now answers the intended subjective preview question without pretending to be production ATTITUDE artwork.

## Non-blocking observations

- The fixed amber datum is intentionally subtle and could be larger in a product design, but it is adequate for this preview.
- The sparse rings, type treatment and aperture are test-shell elements, not MERIDIAN design direction.
- Static renders do not prove absence of on-device clipping, jitter or sensor discontinuity; those remain formal-harness questions.
- Preview exposure must be disclosed before later formal owner observations because expectation bias is unavoidable.

## Distribution authorization

Claude may send the exact three APKs recorded in `previews/attitude-motion-shell/BUILD_RECORD.json`:

| Profile | Package | SHA-256 | Bytes |
|---|---|---|---:|
| DAMPED | `com.xsytrance.attitude.preview.damped` | `de6f79a3f0333aa53643caf06f60043d1bf71dbd317c39854e735f87399a5234` | 2,487,286 |
| PROPOSED | `com.xsytrance.attitude.preview.proposed` | `93e3969df98eb867c2dfa60e3a2210eb660b17d1161c89c11480ed44dbaad77a` | 2,487,306 |
| ASSERTIVE | `com.xsytrance.attitude.preview.assertive` | `57d89f96a098442883dd62b22a5fb6c5587a15f5e9c790350792ccef121812e7` | 2,487,302 |

Distribution conditions:

- send the exact existing APK files without rebuilding, modifying, repackaging or re-signing;
- identify each package and provide its full SHA-256 and byte count;
- recommend preview order DAMPED → PROPOSED → ASSERTIVE;
- do not install automatically or contact the Watch7;
- do not use these APKs with the formal evidence harness;
- record that preview exposure occurred before formal observations.

## Remaining audit note

Claude's prior prose quoted review-image hashes that differ from the committed `REVIEW_MANIFEST.json`. Claude must explain whether those were pre-fix render hashes. This discrepancy does not change the separate APK identities above, but it must be documented rather than ignored.

## Boundaries

This approval does not authorize:

- production ATTITUDE implementation;
- MERIDIAN refinement;
- formal evidence claims;
- modification of the accepted spike APKs or harness;
- release candidate, AAB, signing, store preparation or merge.
