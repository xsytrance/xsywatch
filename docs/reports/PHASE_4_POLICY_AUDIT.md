# Phase 4 — Official distribution-policy audit

**Repository:** `xsytrance/xsywatch`
**Product:** AURELIUS — Field Tourbillon Mk II, `com.xsytrance.aurelius`
**Audit status:** **COMPLETE for the items marked verified; PARTIAL overall**
**Date checked:** 2026-07-26
**Method:** primary/official sources only — `developer.android.com` and
`support.google.com/googleplay/android-developer`. No blog, no cached
memory, no screenshot, no inference from a third party.

Internet access was available, so the audit was performed rather than
blocked. Items that could not be read from an official page on this date
are marked **NOT VERIFIED** and are *not* guessed. An unverified item is an
open action, not a finding.

Nothing in this audit changes package or version metadata. Per phase scope
§12 and ADR-010 §6, that happens only after Checkpoint A is accepted.

---

## Summary of what this means for Aurelius

**Already compliant:**

- Watch Face Format v4 — WFF has been mandatory for installing watch faces
  on all Wear OS devices since January 2026, and Aurelius is already WFF v4.
- targetSdk 36 clears the Wear OS requirement (API 35+) with a year of
  headroom.
- Memory footprint is inside the official 10 MB ambient / 100 MB
  interactive budget — already gated locally by the official evaluator.
- Zero complication slots, so the ≤8 limit is trivially satisfied.

**Concrete blockers before any submission:**

1. **No `.aab` exists.** Play requires a Wear OS *app bundle* for watch
   faces; the repository only produces a debug APK.
2. **No release signing identity exists**, and Play App Signing enrolment
   plus an upload key is required.
3. **The 12-tester / 14-day closed-testing requirement** applies to new
   personal developer accounts and gates production access entirely.
4. **The official AOD metric is not the one we measure** — see AOD-1 below.
   This is the most important technical finding in the audit.
5. **minSdk 34 vs WFF v4's Wear OS 6 / API 36 floor** needs a decision.

**Unresolved owner decisions:** developer-account type and status, whether
Aurelius is paid or free, price and markets, support contact, privacy
policy hosting, and the AI-artwork licence position carried from Phase 1.

---

## Findings

Each row records: the requirement, the official source, the date checked,
applicability to Aurelius, the required repository action, and any
unresolved owner decision.

---

### FMT-1 — Watch Face Format is mandatory

> "As of January 2026, the Watch Face Format is required for installing
> watch faces on all Wear OS devices."

- **Source:** https://developer.android.com/training/wearables/wff
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ✅ **already compliant** — Aurelius is WFF v4, declared via
  `com.google.wear.watchface.format.version` = `@integer/wff_version` (4).
- **Repository action:** none.
- **Owner decision:** none.

---

### FMT-2 — WFF version ↔ platform floor

| WFF version | Min Wear OS | Min API |
|---|---|---|
| 1 | 4 | 33 |
| 2 | 5 | 34 |
| 3 | 5.1 | 35 |
| **4** | **6** | **36** |

- **Source:** https://developer.android.com/training/wearables/wff
- **Checked:** 2026-07-26
- **Applies:** yes, and this is a **live inconsistency**.
- **Finding:** Aurelius declares WFF v4, which requires Wear OS 6 / API 36,
  but `minSdk = 34`. As declared, the package is installable on API 34–35
  devices that cannot render WFF v4.
- **Repository action:** decide between raising `minSdk` to 36 to match the
  declared format, or lowering the WFF version. **Do not change this at
  Checkpoint A** — it is a package-metadata change, which the scope defers.
  Record it as a Checkpoint B input.
- **Owner decision:** whether Aurelius targets Wear OS 6+ only. Raising
  minSdk narrows the addressable market; keeping 34 risks installs that
  cannot render. Recommendation: raise `minSdk` to 36, because the Watch7
  is the only tested device and it runs API 36.

---

### PKG-1 — Watch faces must be submitted as a Wear OS app bundle

> Submissions require "a Wear OS app bundle (.aab file) that you created
> (or that a tool such as Watch Face Studio created for you)."

- **Source:** https://support.google.com/googleplay/android-developer/answer/13560201
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ❌ **not met.** `tools/build_all.sh` produces
  `assembleDebug` APKs only. No `bundleRelease` target, no `.aab`, anywhere
  in the repository.
- **Repository action (Checkpoint B):** add an `.aab` build path, and
  produce the candidate bundle under
  `releases/aurelius/candidates/<version>/`. The debug APK remains the
  device-test artifact; the bundle is the distribution artifact.
- **Owner decision:** none — this is mechanical.

---

### PKG-2 — Bundle size limits

- Maximum compressed download size generated from an app bundle: **200 MB**.
- The 100 MB limit applies only to apps published with APKs and created
  before August 2021.
- **Source:** https://support.google.com/googleplay/android-developer/answer/9859152
- **Checked:** 2026-07-26
- **Applies:** yes, trivially — the current APK is 3.6 MB.
- **Repository action:** none.

---

### SDK-1 — Target API level

> New apps and app updates must target Android 16 (API 36) or higher, with
> exceptions: **Wear OS apps: Android 15 (API level 35) or higher.**
> Existing apps must target API 35+ from **August 31, 2026** to remain
> available to new users on newer devices. An extension to
> **November 1, 2026** is available on request via Play Console.

- **Source:** https://developer.android.com/google/play/requirements/target-sdk
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ✅ **compliant** — `targetSdk = 36` exceeds the Wear OS
  minimum of 35.
- **Repository action:** none, but do not *lower* targetSdk. Note the
  August 31, 2026 date is ~5 weeks out; any release plan should not slip
  past it with a lower target.
- **Owner decision:** none.

---

### SIGN-1 — Play App Signing

- New apps are automatically enrolled in Play App Signing with
  Google-generated, quantum-ready hybrid keys.
- **Upload key:** developer-held, Java keystore, **RSA 2048-bit minimum**;
  resettable if lost.
- **App signing key:** Google-managed; Google-generated keys are RSA
  4096-bit, combined with post-quantum ML-DSA-65. Custom keys must be RSA
  2048-bit or higher. A self-managed key **cannot be reset if lost**.
- **Source:** https://support.google.com/googleplay/android-developer/answer/9842756
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ❌ **not met** — no upload key exists. Current signing is
  debug only (correctly; ADR-010 §5 forbids creating production signing
  material without explicit owner authorisation).
- **Repository action:** the Workstream 7 signing/custody plan must specify
  an **RSA 2048+ upload key** created outside Git, and must record that
  Google holds the app signing key. No key material may be committed.
- **Owner decision:** who owns the commercial signing identity, and
  explicit authorisation to generate it. **Not authorised at Checkpoint A.**

---

### TEST-1 — Closed-testing requirement for new personal accounts

> "At least 12 testers must be opted-in to your closed test when you apply
> for production access. They must have been opted-in for the last 14 days
> continuously." Testers who opt in for under 14 days and opt out are not
> counted, and the 14 days must be consecutive.

Applies to personal developer accounts created after **November 13, 2023**.
Production access is then applied for on the Play Console Dashboard.

- **Source:** https://support.google.com/googleplay/android-developer/answer/14151465
- **Checked:** 2026-07-26
- **Applies:** **depends on account type** — organisation accounts are not
  subject to this; personal accounts created after 2023-11-13 are.
- **Repository action:** none in-repo, but this materially changes the
  launch timeline: a minimum of 14 continuous days with 12 testers *before*
  production access can even be requested.
- **Owner decision:** ⚠️ **what type is the AGENOR developer account, when
  was it created, and does it already have production access?** This is the
  single largest unknown in the release schedule. The watch-face publishing
  guide also states that new personal developer accounts must satisfy app
  testing **and device verification** requirements before publishing.
- **NOT VERIFIED:** the specifics of the device-verification requirement —
  the page referenced it without detail on this date.

---

### AOD-1 — Always-on display pixel budget (WO-P7)

> **`WO-P7` — Always on Display, Watch Face Format:** "Has an Always on
> Display mode and illuminates no more than 15% of pixels. This is
> calculated as the average value across the watch face, with a
> fully-opaque white pixel having a value of 100% and a black pixel 0%. RGB
> colors are interpolated linearly between these two values. This check is
> repeated at approximately 10 minute intervals from the start to the end
> of a whole day, and every calculation must satisfy the 15% limit."

- **Source:** https://developer.android.com/docs/quality-guidelines/wear-app-quality
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Finding — this is the important one.** The official metric is
  **average luminance across the face**, sampled at ~10-minute intervals
  across a whole day, with every sample under 15%.
  The studio metric currently used (`scripts/aod_post.py`,
  `craft_proposal_sheet.py`) is **the percentage of pixels above a 15/255
  threshold** — a *count* of lit pixels, not an *average* of luminance, and
  measured on a single frame rather than across a day. The numbers are not
  comparable, and our internal ≤10% rule is a proxy that happens to be
  stricter in spirit but does not evaluate the same quantity.
- **Repository action:** implement the official metric — mean normalised
  luminance over the face — and evaluate it across the AOD state's full
  daily variation (the date and battery values change; the seconds cage is
  parked in ambient). Report both numbers, and keep the existing count
  metric only as a secondary signal. This is a **Checkpoint B gate**, but
  the studio proposals should be re-scored under it before a direction is
  finalised.
- **Owner decision:** none — this is a correctness fix.
- **Current standing:** the AOD renders are visually very dark and the
  count metric is ~7%, so the face is *likely* well inside 15% average
  luminance. **That is an expectation, not a measurement**, and it must not
  be reported as compliance until computed.

---

### MEM-1 — Memory budget (WO-P8)

> **`WO-P8`:** "Assets do not exceed the memory budget of 10 MB in ambient
> mode, and 100 MB in interactive mode."

- **Source:** https://developer.android.com/docs/quality-guidelines/wear-app-quality
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ✅ **compliant and already gated.** `tools/wff_validate.sh`'s
  companion evaluator runs with exactly `--ambient-limit-mb 10
  --active-limit-mb 100` and PASSes for both the rebuilt candidate and the
  immutable release (baseline report §4).
- **Repository action:** none. Keep the limits pinned to these values.

---

### CPLx-1 — Complication slot limit (WO-P10)

> **`WO-P10`:** "The watch face must have no more than 8 complication
> slots."

- **Source:** https://developer.android.com/docs/quality-guidelines/wear-app-quality
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ✅ compliant — Aurelius declares no complication slots.
- **Repository action:** none. Note this ceiling before any future
  decision to add complications (the phase scope forbids adding them now).

---

### UX-1 — Watch face visual requirements (WO-V12, WO-V16, WO-P3)

- **`WO-V12`** — "Display the time of day clearly on the watch face."
- **`WO-V16`** — content "fits within the physical display area", "no text
  or controls overlap with each other", "no text or controls are cut off by
  the screen edges", "larger or equal to a 192dp circle".
- **`WO-P3`** — "Check that the user can install, set, and personalize the
  watch face without crashing, including adding complications when
  applicable."
- **Source:** https://developer.android.com/docs/quality-guidelines/wear-app-quality
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** consistent with the Phase-3 device matrix, which covered
  install, picker, activation, legibility, clipping and stability. The
  date-aperture proof directly addresses "not cut off" for the one element
  where art frames live text.
- **Repository action:** map the Checkpoint B device matrix rows explicitly
  onto these requirement IDs so the evidence cites the official criteria
  rather than our own wording.

---

### MEDIA-1 — Play listing icon for watch faces (WO-G4)

> **`WO-G4`:** for single watch faces the icon must "accurately represent
> the watch face", "not include text, graphics, or device frames that are
> not part of the watch face experience", and "feature a **centered,
> circular watch face scaled to touch the outer edges** of the icon asset."

- **Source:** https://developer.android.com/docs/quality-guidelines/wear-app-quality
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Finding:** the current icon is `@drawable/preview` — a 400×400
  Lanczos downsample of the r2 normal reference render. That render is the
  **full square canvas including black corners around the octagonal case**,
  so the watch face does not touch the outer edges of the asset.
- **Repository action (Checkpoint B, Workstream 8):** produce a dedicated
  listing icon in which the face is centred and scaled to the asset edges,
  rather than reusing the preview render. Keep it derived from committed
  bytes and checksum-manifested.
- **Owner decision:** none, but note the tension: Aurelius's case is
  octagonal while the requirement describes a circular face touching the
  edges. The circular *display* is what matters; the design should fill
  the asset.
- **NOT VERIFIED:** the exact icon pixel dimensions and file format
  (commonly cited as 512×512 PNG) could not be read from an official page
  on this date. **Do not assume 512×512** — confirm before producing the
  asset.

---

### MEDIA-2 — Play listing screenshots for watch faces (WO-G6)

> **`WO-G6`:** the listing must "contain at least one screenshot that
> accurately depicts the current version of the watch face"; "show more
> than one of the available permutations, if the watch face is
> customizable"; "provide screenshots showing only the watch face
> experience"; "not position the screenshots within device frames, or
> include additional text, graphics, or backgrounds that are not part of
> the interface of the app"; and "include screenshots with a 1:1 aspect
> ratio."

Play Console Help additionally states Wear OS screenshots must be 1:1 with
a **minimum size of 384 × 384 px**, and that up to **8 screenshots** may be
added per supported device type.

- **Sources:**
  https://developer.android.com/docs/quality-guidelines/wear-app-quality ·
  https://support.google.com/googleplay/android-developer/answer/9866151
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Finding — this constrains the commercial packet.** The phase scope
  §14 asks for a "watch-on-wrist or device-context image". Such an image
  **may not be used as a Play screenshot**, because device frames and
  non-interface backgrounds are prohibited. It can only be used as other
  promotional media.
- **Repository action (Checkpoint B):** generate 1:1 screenshots ≥384×384
  containing only the face — the 480×480 renders already satisfy this.
  Aurelius is not user-customizable, so the "permutations" clause does not
  bite; normal and AOD are the natural set.
- **Owner decision:** none.

---

### MEDIA-3 — Feature graphic and promo video

- **NOT VERIFIED.** Exact dimensions and requirements for the feature
  graphic and promotional video could not be read from an official page on
  this date (the preview-assets help page did not render usable content).
- **Repository action:** confirm from Play Console Help before producing
  these assets. The phase scope lists both as optional.

---

### LIST-1 — Store listing, category and tags (WO-G9)

> **`WO-G9`:** "Self tag all watch face submissions on the Google Play
> Console with the appropriate categories that accurately represent the
> watch face."

The publishing guide also requires choosing a category and tags, uploading
at least one Wear OS screenshot, adding preview assets, and creating a
store listing for discoverability.

- **Sources:**
  https://developer.android.com/docs/quality-guidelines/wear-app-quality ·
  https://support.google.com/googleplay/android-developer/answer/13560201
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ❌ no listing copy of any kind exists yet (baseline §5).
- **Repository action:** Workstream 8 copy deliverables.
- **Owner decision:** final product name for the listing, category and tag
  selection.

---

### SRC-1 — Watch face source-size and shape limits (WO-G10, WO-G11)

> **`WO-G10`:** a `watch_face_shapes.xml` file "can contain only 10
> distinct `<WatchFace>` elements".
> **`WO-G11`:** "The total size of the XML source file that defines your
> watch face design cannot exceed 10 MB."

- **Source:** https://developer.android.com/docs/quality-guidelines/wear-app-quality
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Status:** ✅ compliant with very wide margin — the generated
  `res/raw/watchface.xml` is a few tens of kilobytes and no
  `watch_face_shapes.xml` is used.
- **Repository action:** none; add both as assertions in the candidate
  validation so they cannot silently regress.

---

### PRIV-1 — Data safety declaration

All developers must complete the Data safety form declaring collection,
sharing, security practices and purposes — **including apps that collect no
data**, which must still complete the form, state that no collection
occurs, and **provide a privacy policy link**. Data processed ephemerally
(in memory, for a real-time request, not stored) does not require
disclosure. The form has explicit **Health info** and **Fitness info**
categories.

- **Source:** https://support.google.com/googleplay/android-developer/answer/10787469
- **Checked:** 2026-07-26
- **Applies:** yes.
- **Finding:** Aurelius declares `BODY_SENSORS` and
  `ACTIVITY_RECOGNITION`. Heart rate is read on-device and rendered; it is
  not transmitted off-device and not stored. On the face of the definition
  ("data collection" = information **transmitted off-device**) this is
  *not* collection, and the ephemeral-processing carve-out appears to
  apply.
- **Repository action:** state the on-device-only behaviour precisely, from
  the actual WFF expressions, in a document that the data-safety answers
  are derived from. WFF has no network capability and the manifest requests
  no network permission — that is a strong, checkable argument, and it
  should be written down with the evidence rather than asserted.
- **Owner decision:** ⚠️ **a privacy policy URL is required even for a
  no-collection app.** Someone must host one. This is an owner action with
  no repository substitute.
- **Caution:** the "no data collected" answer must be verified against the
  final bundle, not assumed. It is a legal declaration.

---

### HEALTH-1 — Heart-rate / body-sensor disclosure

- **Partly covered by PRIV-1.** The Data safety form's Health and Fitness
  categories are the mechanism.
- **NOT VERIFIED:** whether `BODY_SENSORS` on a watch face triggers any
  *additional* Play declaration (for example a sensitive-permission
  justification or a health-apps policy declaration) could not be confirmed
  from an official page on this date.
- **Repository action:** before submission, confirm whether the permission
  is required at all. **A WFF watch face reading `[HEART_RATE]` may not
  need a manifest `BODY_SENSORS` declaration**, since the platform supplies
  the value to the format rather than the app reading the sensor directly.
  If it is not required, removing it removes the entire question — that is
  the cleanest outcome and should be tested on-device first.
- **Owner decision:** none yet; depends on the above.

---

### PAY-1 — Paid apps and merchant prerequisites

- **NOT VERIFIED.** The merchant-account prerequisites, seller-supported
  countries and registration steps could not be read from an official page
  on this date; the page reached covered only registration-fee payment
  methods.
- **Repository action:** none at Checkpoint A.
- **Owner decision:** ⚠️ whether Aurelius is free or paid, at what price,
  and in which markets. This determines whether a payments profile is
  needed at all, and it is a prerequisite for the pricing line in the
  commercial packet.

---

### CONT-1 — Package name and update continuity

- **NOT VERIFIED** from an official page on this date. The Play App Signing
  page did not address package-name changes or update continuity.
- **Established platform fact, not a policy citation:** an Android package
  name is immutable once published, and an update must be signed by the
  same app signing key. This is why ADR-010 §3 keeps
  `com.xsytrance.aurelius`.
- **Repository action:** keep the package name. Do not rename it without a
  superseding ADR.
- **Owner decision:** none, provided the name is kept.

---

### REGION-1 — Supported regions and devices

- **NOT VERIFIED.** Country/region availability rules and Wear OS device
  targeting were not read from an official page on this date.
- **Applies:** tested devices are the constraint that matters for honesty:
  Aurelius has been validated on **one** device, the Galaxy Watch7 44 mm.
- **Repository action:** the compatibility statement in the commercial copy
  must say exactly that, and must not claim broader compatibility
  (ADR-010 §9, phase scope §14 truthfulness rules).
- **Owner decision:** target markets.

---

## Open items, ranked

| # | Item | Type | Blocks |
|---|---|---|---|
| 1 | Developer account type / production access status (TEST-1) | owner | the entire launch timeline |
| 2 | Official AOD average-luminance metric not implemented (AOD-1) | repo | a truthful AOD compliance claim |
| 3 | No `.aab` build path (PKG-1) | repo | submission |
| 4 | No upload key / signing plan (SIGN-1) | owner + repo | submission |
| 5 | minSdk 34 vs WFF v4 API 36 floor (FMT-2) | owner + repo | correctness of install targeting |
| 6 | Privacy policy URL (PRIV-1) | owner | data safety form |
| 7 | Whether `BODY_SENSORS` is needed at all (HEALTH-1) | repo | disclosure scope |
| 8 | Listing icon does not fill the asset (MEDIA-1) | repo | listing quality |
| 9 | Free vs paid, price, markets (PAY-1) | owner | commercial packet |
| 10 | AI-artwork licence for commercial sale | owner | carried from Phase 1 |

## Items still to verify from official sources

MEDIA-1 icon dimensions/format · MEDIA-3 feature graphic and video specs ·
HEALTH-1 additional `BODY_SENSORS` declarations · PAY-1 merchant
prerequisites · CONT-1 package/update continuity as a *cited policy* ·
REGION-1 region and device availability · TEST-1 device-verification
detail.

These are recorded as unverified rather than filled in from memory. Phase
scope §12 forbids treating anything but a primary source as authoritative,
and an audit that guesses is worse than one that admits a gap.
