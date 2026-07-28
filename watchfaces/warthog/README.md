# MERIDIAN WARTHOG

A Fairchild Republic A-10 Thunderbolt II, seen head-on. Gunship-grey nose
skin, bubble canopy, tiger eyes, and the shark mouth biting across the lower
dial.

**Development build, not a release candidate.** Debug signing only, no
bundle, no store metadata, package namespaced `.dev`.

| | |
|---|---|
| Package | `com.xsytrance.warthog.dev` |
| Version | `0.2.0-dev` (versionCode 2) — mk2, the fierce revision |
| Aircraft | Fairchild Republic A-10 Thunderbolt II |
| Dial mark | MERIDIAN / WARTHOG |
| Format | WFF v4, 480×480 |
| Studio source | `~/AGENOR-Horology/scripts/warthog.py` |

## Why this is not an ATTITUDE SQUADRON variant

The squadron collection is one chassis in thirteen paint jobs. Every variant
shares the component list, the data bindings and the horizon contract, so the
aircraft never reaches the mechanism — which is precisely why no squadron
face reads as a *particular* aeroplane. Their propeller is a shared
`seconds_rotor` and their circular window is a shared `horizon_field`.

This face shares none of that structure. It has no propeller and no horizon
window, because the A-10 is a twin-turbofan jet with neither. The "BRRRT" is
not an engine; it is the GAU-8/A Avenger, a seven-barrel 30mm rotary cannon
the airframe was built around.

## mk2 — the fierce revision

mk1 read as cute. The causes were specific: evenly spaced, evenly sized,
clean-white teeth; two round cartoon eyes with catchlights; and no evidence
anywhere on the dial that the aircraft is a weapon.

mk2 deletes the eyes, rebuilds the jaw with irregular pitch, varied length,
canines and tilt, and turns the plate into a weapons console — radar PPI with
a live phosphor sweep, a turbine gauge oscillating on the wearer's heart
rate, an ammunition drum on battery, threat chevrons at the muzzle. The gun
is rebuilt as hardware rather than flat discs. Tapping the face fires it.

Full rationale, including why it cannot make a sound: `docs/WARTHOG_MK2.md`.

## The signature

`z30_gun` is the GAU-8 muzzle seen head-on, turning once a minute. **The gun
is the seconds hand.**

One barrel carries a scorched firing ring. This is load-bearing, not
decoration: seven identical bores are ambiguous under 1/7 rotational
symmetry, and without a marked barrel a full revolution cannot be read.
`~/AGENOR-Horology/aircraft-warthog/review/WARTHOG_GUN_ROTATION.png` is the
proof sheet.

**Tap to fire.** `z50_brrrt` is a twelve-frame muzzle burst on WFF's only
interaction hook, `AnimationController play="TAP"`. It is hidden before and
after and suppressed in ambient. A tap anywhere fires it — the format has no
pointer position and no per-region hit testing.

**It cannot make the sound.** The Watch7 has a speaker, but Watch Face Format
defines no audio, vibration or haptic element at any version through 5, and a
face ships `hasCode=false`. Real audio would mean rewriting as a Kotlin
`WatchFaceService` — a different project. See `docs/WARTHOG_MK2.md`.

Supporting elements:

- **Hands** are 30mm rounds — brass case with an extractor groove, a
  threat-red HEI band at the ogive root, gunmetal projectile, lume spine.
- **Radar PPI** at twelve, with a phosphor sweep on a four-second revolution.
- **Turbine gauge** on the left, its needle oscillating at the wearer's own
  heart rate — live data, not decoration.
- **Ammunition drum** on the right: battery, scaled to the GAU-8's 1,174
  rounds and shown both as a needle and a digital count.
- **Date** and **steps** sit in stencilled windows above the jaw.
- **Ambient** strips to the jaw outline, a muzzle ember at twelve and the
  date. Steps and heart rate go fully dark rather than leaving empty frames
  lit, and the muzzle does not rotate in ambient.

## The collection rule this face establishes

> The aircraft's defining moving part drives the watch's defining motion, and
> the dial architecture is derived from that airframe.

Reuse that rule, not this component list. A C-130 should not inherit a rotary
cannon any more than the A-10 should have inherited a propeller. Sharing the
component list is what produced thirteen faces that read as one.

## Art provenance

Every pixel is original procedural construction in the studio script. No
external image is opened at any point in the build.

`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md` established that all collected
aircraft reference material is third-party copyrighted, retained as an
inventoried record and **never traced**; that finding governs this face.
Shark-mouth nose art is a common wartime motif, drawn here as original
geometry rather than derived from any specific airframe photograph.

## Build

```bash
python3 ~/AGENOR-Horology/scripts/warthog.py     # artwork + review sheets
python3 tools/generate_face.py warthog           # engine/face.toml -> watchface.xml
bash tools/wff_validate.sh 4 watchfaces/warthog/app/src/main/res/raw/watchface.xml
bash tools/build_face.sh warthog
```

Both the artwork and the XML are deterministic; `--check` on either generator
is a drift gate.
