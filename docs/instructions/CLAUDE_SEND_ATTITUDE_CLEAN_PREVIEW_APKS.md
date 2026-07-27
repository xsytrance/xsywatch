# Claude Next Task — Send ATTITUDE Clean Preview APKs

Pull:

- repository: `xsytrance/xsywatch`;
- branch: `preview/attitude-motion-shell`;
- branch must contain pixel-review commit `ab7a8c7eb44cba150e9f084f5ec89f47a56df7b8`.

Do not require exact HEAD equality because this instruction file is committed after the review it references.

Read first:

- `docs/reports/ATTITUDE_CLEAN_PREVIEW_SHELL_PIXEL_REVIEW.md`;
- `previews/attitude-motion-shell/BUILD_RECORD.json`;
- `previews/attitude-motion-shell/REVIEW_MANIFEST.json`.

## Assignment

Send the owner the three existing preview APK files exactly as built. Do not rebuild them first.

Files:

1. `previews/attitude-motion-shell/dist/attitude-preview-damped-debug.apk`
   - package: `com.xsytrance.attitude.preview.damped`
   - SHA-256: `de6f79a3f0333aa53643caf06f60043d1bf71dbd317c39854e735f87399a5234`
   - bytes: `2487286`

2. `previews/attitude-motion-shell/dist/attitude-preview-proposed-debug.apk`
   - package: `com.xsytrance.attitude.preview.proposed`
   - SHA-256: `93e3969df98eb867c2dfa60e3a2210eb660b17d1161c89c11480ed44dbaad77a`
   - bytes: `2487306`

3. `previews/attitude-motion-shell/dist/attitude-preview-assertive-debug.apk`
   - package: `com.xsytrance.attitude.preview.assertive`
   - SHA-256: `57d89f96a098442883dd62b22a5fb6c5587a15f5e9c790350792ccef121812e7`
   - bytes: `2487302`

Before sending, hash and stat each existing file. Stop if any value differs.

Send the files individually without modifying, repackaging, recompressing or re-signing them. Do not install them and do not contact the Watch7.

Tell the owner to preview them in this order:

1. DAMPED;
2. PROPOSED;
3. ASSERTIVE.

Frame the preview narrowly: judge whether the reactive horizon is promising, gimmicky or obviously wrong; do not treat the preview as formal evidence for jitter, clipping, stability, clamp behavior or final profile selection.

Record explicitly that this preview occurred before the later formal owner observations.

## Hash discrepancy explanation

In the same response, explain why the review-image hashes quoted in the prior completion report differed from the final values in `REVIEW_MANIFEST.json`.

State exactly whether the quoted hashes were from pre-fix renders, stale local output, or a reporting error. Quote the authoritative final manifest hashes. Do not guess.

This discrepancy concerns review renders, not the independently recorded APK hashes, but it must be resolved transparently.

## Boundaries

Do not:

- rebuild or modify the APKs;
- install anything;
- contact the watch;
- alter the validated spike or harness;
- use preview APKs in the formal evidence harness;
- begin MERIDIAN refinement or production ATTITUDE work;
- create an AAB, release candidate, signing or store state;
- merge the branch.

Stop after sending the three exact files and giving the hash explanation.
