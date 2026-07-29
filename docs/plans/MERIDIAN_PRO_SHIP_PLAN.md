# MERIDIAN PRO — the ship plan

**Build the concept-sheet face and sell it on Google Play for the Galaxy
Watch 7.** Owner's directive, 2026-07-29. This supersedes
`MERIDIAN_PRO_REDESIGN_GRAND_PLAN.md` as the working document (that plan's
platform audit stands and is referenced, not repeated) and it **unparks
selling for this face specifically** — the 2026-07-27 "selling is parked"
ruling stays in force for AURELIUS and its nine launch decisions.

Concept: `previews/MERIDIAN_PRO_CONCEPT.png`.

---

## 1. Why this face is the one that can be sold

Every existing MERIDIAN face is blocked from sale by
`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md`: their plates and hands are
AI-generated. The concept face contains **no photograph and nothing that
needs a model** — bezel, milled plate, arcs, type, shadow. Every pixel comes
from `PartDraw` vectors or seeded procedural sprites, so it is **original by
construction from the first commit**. Provenance is not a debt to pay down;
it is a property of the design.

Equally important: **the commercial pipeline already exists.** Phase 4 built
it for AURELIUS and it transfers whole — the 13-gate readiness checker
(`tools/check_candidate_readiness.py`), device matrix
(`tools/device_matrix.py`), privacy-policy renderer with content checksum
(`tools/render_privacy_policy.py`), byte-stable release builds, evidence
binding to APK hashes, and ChatGPT as architecture reviewer
(`docs/CHATGPT_ARCHITECT.md` — read before every phase). MERIDIAN PRO walks a
road AURELIUS already paved; it does not re-derive it.

---

## 2. What v1 ships — the feature contract

Settled against the schema (details in the grand plan §2; three findings
since):

**Ships, all verified as real sources/elements at v4:**

| Feature | Mechanism |
|---|---|
| Power arc with zones + smooth sweep | `Arc` + `WeightedStroke` + `Transform endAngle` — validated |
| Battery % + **live charging bolt** | `BATTERY_PERCENT`, `BATTERY_CHARGING_STATUS` |
| Low-battery warning state | `BATTERY_IS_LOW` |
| Steps ring, count, **wearer's own goal** | `STEP_COUNT`, `STEP_PERCENT`, `STEP_GOAL` |
| Heart rate + zone-coloured ring | `HEART_RATE` |
| Three-field date `WED 27 MAY` | `DAY_OF_WEEK_S`, `DAY`, `MONTH_S` |
| 24H military time | `HOUR_0_23` |
| Moon phase, day/night | `MOON_PHASE_POSITION`, `MOON_PHASE_TYPE` |
| **Tap shortcuts** | `<Launch>`: HR dial → `HEALTH_HEART_RATE`, fuel arc → `BATTERY_STATUS`, date → `CALENDAR` |
| Five colour themes in the editor | `ColorConfiguration` + `Flavor` presets |
| Ambient + AOD | `Variant mode="AMBIENT"`, house pattern |

**Replaced (impossible as drawn):** sunrise/sunset → the two framed windows
carry **temperature + precipitation chance** (no location source exists at
any format version). **Cut:** tap-to-cycle metrics (no persistent state),
floors/calories/active-time (no sources). These are stated on the store
listing's terms, not discovered by a buyer.

**Design language:** the AN instrument grammar
(`docs/plans/AIRCRAFT_INSTRUMENT_GRAMMAR.md`) for every dial; Barlow
Condensed type; halo readouts; `shade()` compositing; palette sampled, not
invented.

---

## 3. Two device probes before anything is built on top

The lesson of this week, twice over: the validator does not check what the
device does, and a face that fails to inflate is a silent black screen. One
unproven construct per build.

**P0-A — PartDraw.** One face: a weighted-stroke zone arc, a
`Transform endAngle` progress arc, a sweep gradient. Nothing else. The entire
plan rests on this rendering on the Watch 7.

**P0-B — zero permissions.** Same face plus `STEP_COUNT`, `STEP_GOAL`,
`HEART_RATE`, `BATTERY_CHARGING_STATUS` readouts, **with an empty
`<uses-permission>` set**. AURELIUS proved live HR arrives with zero
permissions (the WFF runtime holds the sensor); steps are unproven. If steps
flow too, the Play **data-safety form is the trivial version** — a real
commercial asset. If not, we learn now, not at review time.

Both `.dev`, side-by-side installable, served over the Tailscale link (the
Wear Installer loop is proven). Gate: wrist photos.

---

## 4. Build phases

| # | Work | Gate |
|---|---|---|
| 0 | P0-A + P0-B probes | renders + sources flow on device |
| 1 | `tools/meridian_pro/geometry.py` — every coordinate once; bezel ring, minute track, applied indices with lume | contact sheet |
| 2 | Milled centre plate, wells, screws, layered shadow (all `shade()`-composited) | contact sheet |
| 3 | Vector layer: power arc, steps ring, HR ring, live sweeps | validator + render |
| 4 | Readouts: battery, steps/goal, BPM, three-field date, 24H — **centring asserted by gate, not eye** | legibility at 1× |
| 5 | Moon well; weather windows | render |
| 6 | Hands, boss, lume; AOD + ambient | on the wrist |
| 7 | Five themes (`Flavor`) + `<Launch>` tap zones | all five in the editor |
| 8 | Renderer learns `PartDraw`; visual test suite for the face; both sizes (480 native, 432 verified by render); memory + WO-P7 AOD ratio | review gate green |

New quality gate carried from this week's finding: **aperture centring is
asserted numerically** (the AURELIUS date defect and COMMODORE's inherited
one were the same class: containment was checked, centring never was).

---

## 5. Commercial hardening (the AURELIUS pipeline, applied)

1. **Identity:** production `applicationId` (no `.dev`), name cleared by a
   trademark/Play search (**"MERIDIAN PRO" is generic enough to collide —
   check before the listing is written**), versioning discipline from 1.0.0.
2. **Licensing:** Barlow Condensed is SIL OFL 1.1 — commercial use fine,
   notice required → `THIRD_PARTY_NOTICES/fonts/barlow-condensed-NOTICE.txt`
   (DejaVu already noticed). All other assets procedural, recorded in
   `PROVENANCE.md` per the house format.
3. **Signing:** no production keystore exists and none is authorised
   (ADR-010 §5). Needs an explicit owner authorisation; keystore generated
   offline, never committed (gitignore already blocks it).
4. **Release build:** byte-stable rebuild proof, lineage records, evidence
   bound to the APK hash — exactly the AURELIUS discipline.
5. **Readiness:** `check_candidate_readiness.py meridian-pro` through the 13
   gates, `--stamp` after every evidence change, device matrix run against
   the release candidate, owner wear sessions bound to the shipped hash.
6. **Review:** ChatGPT architecture checkpoint at rc, per the ledger.

---

## 6. The listing

- **Assets:** screenshots from the on-device face (all five themes, AOD),
  feature graphic composed from renders — the concept sheet itself is
  marketing-grade reference.
- **Privacy policy:** rendered by `tools/render_privacy_policy.py`, hosted
  under `x1c7.com`, checksum pinned. Zero-permission outcome from P0-B makes
  the data-safety form near-empty.
- **Price:** decision 3 below. Reference point: ChatGPT recommended $3.99
  one-time for AURELIUS.
- **Markets:** worldwide unless a reason emerges.

---

## 7. What only Rod can do, in the order it is needed

1. **Now:** install the two Phase 0 probes, photograph the results.
2. **During build:** judge the phase 1/2/4 contact sheets.
3. **Before release build:** authorise production signing (ADR-010).
4. **Before listing:** Play Console account facts (the four TEST-1 items);
   approve the name after the collision check; pick price + markets; support
   email + response commitment; put the rendered privacy policy live on
   x1c7.com.
5. **Before submit:** wear the rc through the device matrix owner rows.

Per the standing preference these arrive **one at a time, each with an
explanation**, as they block — never as a nine-item sheet.

## 8. Decisions (asked singly when they block)

1. Weather (temp + precip) in the two small windows — *recommended*.
2. Steps-only metric dial for v1, `ListConfiguration` later if missed —
   *recommended*.
3. Price — *recommendation $3.99 one-time*.
4. Name clearance result → final product name.

## 9. Risks, honestly

| Risk | Mitigation |
|---|---|
| `PartDraw` misbehaves on device | P0-A is half a day; fallback is procedural arc sprites (slower, same look) |
| Steps need a permission | declare `ACTIVITY_RECOGNITION` only; data-safety form grows one row |
| 40 mm (432px) untested — no device | vector scales; renderer verifies at 432; note in listing if unproven |
| Name collision on Play | search before listing; product name is one constant in the build |
| Play review latency/policy | zero permissions + WFF `hasCode=false` is the lowest-risk category there is |
