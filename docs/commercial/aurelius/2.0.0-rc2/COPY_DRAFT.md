# AURELIUS 2.0.0-rc2 — draft listing copy

**Status:** DRAFT for owner review. Nothing here is published, and nothing
here may be published until the owner approves the wording, the price and
the launch decision.

Every claim below is either demonstrable from the product or explicitly
framed as design language. The forbidden-claim list at the end is not
decoration — several natural-sounding phrasings are excluded because they
would be untrue.

---

## Product name

**AURELIUS — Field Tourbillon Mk II**

Short form for constrained fields: **AURELIUS Field Tourbillon**.

## One-line positioning

> An animated mechanical watch face for Wear OS: an elite field
> instrument, finished like independent horology.

## Short description (≤80 characters)

> Animated field-tourbillon watch face. Machined finish, restrained AOD.

(74 characters.)

## Long description

> AURELIUS is a mechanically animated watch face for Wear OS, built around
> a tourbillon-inspired seconds cage and a live gear train.
>
> The design is a field instrument first: muted olive titanium tones,
> charcoal and blackened-metal surfaces, and a sparse warm-gold hierarchy
> used only where it clarifies what you are reading. The finishing pass is
> where the detail lives — directional satin brushing, selectively
> polished bevels, machined screw slots, deep jewel cups and refined gear
> teeth that reward a close look without ever competing with the time.
>
> A framed date aperture sits at three o'clock. A reserve gauge tracks
> your watch's battery level across a marked arc. The seconds cage turns
> once a minute, the gear train turns with it, and a subtle sheen shifts
> as you move your wrist.
>
> Always-on mode is deliberately restrained: a dark ambient composition
> that keeps the time, date and mechanical silhouette readable while
> keeping the lit area small.
>
> Everything is drawn on your watch. AURELIUS does not collect your data,
> does not send anything off your device, and has no network access.

## Factual feature list

- Analog hours and minutes with a tourbillon-inspired seconds cage
- Live gear train and balance-wheel animation
- Framed date aperture, all days 1–31 verified to fit
- Watch-battery reserve gauge on a marked arc
- Heart-rate-reactive balance wheel, with a safe fallback when no reading
  is available
- Accelerometer-driven crystal sheen (parallax)
- Restrained always-on mode
- Watch Face Format v4
- No permissions requested, no network access, no data collection

## Compatibility

> Requires Wear OS 6 (Android 16, API 36) or later, and a device that
> supports Watch Face Format version 4.
>
> Tested on the Samsung Galaxy Watch7 44 mm. It has not been tested on
> other devices or sizes.

The second sentence is mandatory. One device model has been tested, and
the listing may not imply otherwise.

## Always-on display language

> Always-on mode uses a dark, low-luminance composition designed to keep
> the display restrained.

Do **not** state or imply an official compliance figure until the WO-P7
result is final for the shipping build. The measured result for
`field-tourbillon-mk2-rc1` is a maximum of 3.972% average luminance
against the 15% limit (144 samples across a day) — that number may be
cited internally and to reviewers, but the public listing should describe
the design intent, not quote a certification.

## Battery disclaimer

> Battery use depends on your watch, your settings and how you use it.
> Animated watch faces generally use more power than static ones. AURELIUS
> reduces its animation in always-on mode.

Do **not** quote hours, percentages, or comparisons. Per-face battery
impact in this project is anecdotal and has never been measured under
controlled conditions.

## Heart-rate and on-device data behaviour

> AURELIUS requests no permissions. It reads the heart-rate value your
> watch already provides, only to animate the balance wheel, and your
> battery level only to move the reserve gauge.
> Both values are read on your watch, used to draw the face, and nothing
> else. AURELIUS has no network access and sends nothing off your device.
> It stores no history and keeps no records.

**It is not a health or fitness tool. It does not measure, track, log or
diagnose anything.**

## Data safety declaration — draft

To be entered in the Play Console Data safety form. Google requires the
form to be completed **even when an app collects no data**, and requires a
privacy policy link regardless.

| Question | Draft answer | Basis |
|---|---|---|
| Does your app collect or share any of the required user data types? | **No** | The face is a declarative WFF package with no code (`android:hasCode="false"`), **no declared permissions at all**, no network permission, and no network capability in the format. Nothing can leave the device. |
| Is all user data encrypted in transit? | N/A — no data in transit | as above |
| Do you provide a way to request data deletion? | N/A — no data collected or stored | as above |
| Health / fitness data | Heart rate is **read on-device and rendered**, never collected, stored, or transmitted | Play defines collection as transmitting data off-device; the ephemeral-processing carve-out applies |

**Before submission this must be re-verified against the final bundle, not
assumed.** It is a legal declaration.

**RESOLVED for 2.0.0-rc2 — the manifest declares NO permission at all.**

`ACTIVITY_RECOGNITION` removed: the face references no step, distance,
calorie, floor or elevation source, so it backed no feature.
`BODY_SENSORS` removed: apps targeting API 36+ must use the granular
`android.permission.health.*` permissions, and the legacy one only applies
with `android:maxSdkVersion="35"`, which `minSdk 36` can never reach.

The listing may therefore state that AURELIUS requests **no permissions**.
See `docs/reports/PHASE_4_PERMISSION_INVESTIGATION.md`.

⚠️ Still to confirm on the device: that `[HEART_RATE]` reaches the face
without a declared permission. If the Watch7 shows the balance wheel stuck
at the 70 bpm fallback, `android.permission.health.READ_HEART_RATE` is
required and this section must be rewritten before submission.

## Privacy policy — draft

> **AURELIUS privacy policy**
>
> AURELIUS is a watch face for Wear OS. It does not collect, store, share
> or transmit any personal information.
>
> To draw the watch face, AURELIUS reads values your watch already
> provides: the current time and date, your watch's battery level, and —
> to animate the balance wheel — the heart-rate value your watch reports.
> These values are used only to draw what you see, moment to moment. They
> are not recorded, not saved, and not sent anywhere.
>
> AURELIUS contains no code, requests no permissions, and has no network
> access. There are no accounts, no analytics, no advertising and no
> third-party services.
>
> Questions: <SUPPORT EMAIL — owner to supply>
>
> Last updated: <DATE>

⚠️ **Owner action:** this must be hosted at a public URL before
submission. Play requires a privacy policy link even for a no-collection
app, and there is no repository substitute for hosting.

## Support process — draft

> Support: <SUPPORT EMAIL — owner to supply>
>
> Please include your watch model and Wear OS version. Expect a reply
> within <N> business days.

⚠️ **Owner action:** email address and a response-time commitment the
owner is willing to keep. Do not publish a commitment that will not be met.

## Attribution notice

> Typography: Rajdhani, © Indian Type Foundry, licensed under the SIL Open
> Font License 1.1.

Full audit: `docs/asset-licenses.json`, notices in `THIRD_PARTY_NOTICES/`.

## Release notes — 2.0.0-rc2

> **2.0.0-rc2**
>
> - New craftsmanship pass: darker, tighter blackened-metal bridges,
>   refined charcoal and olive surfaces, directional satin brushing,
>   selectively polished bevels, deeper jewel cups and crisper gear teeth.
> - Crisper reserve-gauge markings for easier reading at a glance.
> - Substantially smaller download.
> - Now requires Wear OS 6 (API 36), matching the Watch Face Format
>   version the face uses.
> - Requests no permissions at all.

## Known limitations (to disclose)

- Tested on one device model only — Galaxy Watch7 44 mm.
- Battery impact is not measured under controlled conditions.
- Requires Wear OS 6 / API 36; it will not install on earlier devices.

## Proposed price positioning — FOR OWNER DECISION

No price is proposed as fact. For the owner to consider:

| Option | Rationale | Consequence |
|---|---|---|
| Free | Largest reach; builds an audience for later paid products | No merchant account needed; no revenue |
| Paid, low (~$1–2) | Matches most of the watch-face market | Requires a payments profile; low margin per install |
| Paid, premium (~$4–6) | Matches the finishing quality and the mechanical animation; positions AGENOR as a premium studio | Smaller audience; raises expectations for support and updates |

⚠️ Whether a payments profile is even needed depends on this choice, and
the merchant prerequisites could not be verified from an official page
during the audit (PAY-1). Resolve the price question before that research
is repeated.

---

## Claims that must NOT be made

Not stylistic preferences — each of these would be false:

- that the watch contains a **physical mechanical tourbillon**, or any
  mechanical movement at all;
- that the watch is made of **titanium, DLC, sapphire, gold or ruby** —
  the face *depicts* those materials; the device does not contain them;
- any **medical, diagnostic or fitness-accuracy** claim;
- any **guaranteed battery life**, duration or efficiency comparison;
- **chronometer or accuracy certification**;
- **official AOD compliance**, until the WO-P7 result is final for the
  shipping build;
- **universal or untested compatibility** beyond the Galaxy Watch7 44 mm;
- that the product is **published or available**, until it actually is.
