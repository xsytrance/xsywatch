# MERIDIAN WARTHOG

A Fairchild Republic A-10 Thunderbolt II, seen head-on. Gunship-grey nose
skin, bubble canopy, tiger eyes, and the shark mouth biting across the lower
dial.

**Development build, not a release candidate.** Debug signing only, no
bundle, no store metadata, package namespaced `.dev`.

| | |
|---|---|
| Package | `com.xsytrance.warthog.dev` |
| Version | `0.1.0-dev` (versionCode 1) |
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

## The signature

`z30_gun` is the GAU-8 muzzle seen head-on, turning once a minute. **The gun
is the seconds hand.**

One barrel carries a scorched firing ring. This is load-bearing, not
decoration: seven identical bores are ambiguous under 1/7 rotational
symmetry, and without a marked barrel a full revolution cannot be read.
`~/AGENOR-Horology/aircraft-warthog/review/WARTHOG_GUN_ROTATION.png` is the
proof sheet.

Supporting elements:

- **Hands** are 30mm rounds — brass case with an extractor groove, HEI
  marking band at the ogive root, gunmetal projectile, lume spine.
- **Ammo gauge** is the battery, reflected in the canopy glass as a HUD arc.
  Rounds remaining are scaled to the drum's 1,174-round capacity.
- **Date** sits in the throat of the mouth, between the tooth rows.
- **Ambient** strips to the grin outline, a muzzle ember at twelve and the
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
