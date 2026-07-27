# ATTITUDE Clean Preview Shell — Preliminary ChatGPT Review

**Repository:** `xsytrance/xsywatch`  
**Branch:** `preview/attitude-motion-shell`  
**Commit reviewed:** `3c04efc8de6a1381d90c733605e339b4f37dd1f8`  
**Verdict:** **STRUCTURE ACCEPTED; APK DISTRIBUTION HELD FOR DIRECT PIXEL REVIEW**

## Accepted offline structure

The branch is correctly isolated from the validated formal spike and device harness. The change set is limited to the preview shell plus its build-output ignore rules.

Accepted design and engineering properties:

- preview-only package namespace is distinct from the formal spike namespace;
- DAMPED, PROPOSED and ASSERTIVE can coexist with the three validated spike packages;
- the preview imports the accepted spike motion-expression builders rather than retyping the motion contract;
- the aperture geometry is held to the formal spike geometry;
- the shell has no analog hands and uses readable system text;
- AOD uses a separate neutral resource and the WFF XML forces neutral ambient placement;
- no permissions, signing configuration, AAB, release candidate or production authorization is introduced;
- the three accepted formal spike APK hashes remain authoritative and must remain unchanged.

The PROPOSED WFF XML inspected at the reviewed commit has the expected imported motion contract, separate normal/AOD resources, neutral ambient variants, readable digital time, profile label and `MOTION PREVIEW` disclosure.

## Direct pixels still required

Hashes and manifests are not visual approval. The GitHub connector exposes the committed PNG files as encoded binary rather than a directly inspectable image surface in this review environment.

Before the three preview APKs are sent, the owner must upload these exact committed review files directly to ChatGPT:

1. `previews/attitude-motion-shell/review/NORMAL_COMPARISON.png`
2. `previews/attitude-motion-shell/review/AOD_COMPARISON.png`
3. `previews/attitude-motion-shell/review/MOTION_STATES_PROPOSED.png`

Optional but useful:

4. `previews/attitude-motion-shell/review/NORMAL_PROPOSED.png`

Do not substitute phone screenshots of GitHub thumbnails if the original PNGs can be sent. Original files preserve scale and contrast.

## Hash discrepancy requiring clarification

The submitted narrative quoted these abbreviated hashes:

- `NORMAL_PROPOSED.png`: `f7d2a51e…`
- `AOD_COMPARISON.png`: `9c6e0b34…`
- `MOTION_STATES_PROPOSED.png`: `34d05ba8…`

The committed `review/REVIEW_MANIFEST.json` at `3c04efc8...` records:

- `NORMAL_PROPOSED.png`: `b627b2779587cc8e3a7cc4961584be04867aaa67ba28c79fb24bac722c31fef7`
- `AOD_COMPARISON.png`: `a76de6cb4dc5230e57f16269fd3bb19b5a78c2edbe47ff140fc9e452f033b0f9`
- `MOTION_STATES_PROPOSED.png`: `8122fa843be00a90935b2b255a4c81511cfb61073ef4e4f3311bea2b6e19b030`

The committed manifest is the repository authority, but Claude must explain whether the narrative hashes came from pre-fix renders or another generation. Do not regenerate or alter the pixels merely to reconcile prose. Report the explanation and preserve the reviewed commit.

## Current hold

Do not send the preview APKs yet.

After the owner uploads the committed comparison and motion-state PNGs, ChatGPT will review:

- time and label legibility at watch scale;
- datum/horizon hierarchy;
- whether the shell is visually neutral enough for motion judgment;
- whether profile labels are prominent without overpowering the instrument;
- normal-mode corner/field containment;
- AOD brightness, clutter and neutrality;
- extreme-state clipping and visual confusion.

No production ATTITUDE, MERIDIAN refinement, formal-device evidence, release, signing, store or merge work is authorized by this review.