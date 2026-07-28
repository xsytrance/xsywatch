# MERIDIAN WARTHOG mk2 — fierce, instrumented, and it fires

Revision of `watchfaces/warthog` from `0.1.0-dev` to `0.2.0-dev`, answering
one review note: *"it's cute; I expected something more fierce."*

## Why mk1 was cute

Worth stating precisely, because "make it badass" is not actionable and the
actual causes were specific and fixable.

1. **Regularity.** The jaw was eleven evenly spaced, evenly sized,
   clean-white triangles on a smooth curve. Even spacing is what separates a
   cartoon grin from a predator's mouth. Real teeth vary in pitch, length and
   angle, and some are canines.
2. **Eyes.** Two large round eyes with white sclera, a coloured iris and a
   specular catchlight is the visual grammar of an animated character. Nose
   art on a real airframe is flatter, angrier and more graphic.
3. **Emptiness.** A big friendly face with three readouts and nothing else
   reads as a mascot. There was no evidence the aircraft is a weapon.

## What mk2 changes

**The eyes are gone.** The gun is the only thing looking at you.

**The jaw is irregular by construction.** `_tooth_plan()` jitters pitch,
varies length by up to 3.2×, places canines at the quarter points, tilts each
tooth independently and dirties the enamel toward the roots. The gum is
near-black rather than pillar-box red, and the throat falls away behind the
teeth instead of sitting flat.

**The plate is a weapons console.** Diamond tread armour, panel seams and
rivet lines, threat chevrons flanking the muzzle, a `MASTER ARM` legend, and
three live instruments:

| Instrument | Driven by | Component |
|---|---|---|
| Radar PPI with phosphor sweep | wall clock, 4s/revolution | `rotating_image` |
| Turbine gauge | wearer's heart rate | `hr_balance` |
| Ammunition drum | battery, scaled to 1,174 rounds | `battery_needle` |

The turbine needle genuinely oscillates at your pulse; it is not decoration.

**The gun is hardware now.** mk1 drew flat discs on a flat plate. mk2 builds
a chamfered clamp ring, a fourteen-bolt circle, radial machining, and bores
with real depth — chamfered crown, lit near wall, shadowed far wall, rifling
catching light in the throat. Soot is biased toward the firing position, and
the barrel at twelve carries a heat-glowing crown.

## Tap to fire

`z50_brrrt` is a twelve-frame muzzle burst: ignition, bloom, expanding shock
ring, drifting smoke, gone. It plays on tap, is hidden before and after, and
is suppressed entirely in ambient.

This required a new engine component, `tap_sequence`
(`engine/wffgen/components.py`), emitting `PartAnimatedImage` +
`AnimationController play="TAP"` + `SequenceImages`.

**Constraint worth knowing:** WFF has no pointer position and no per-region
hit testing. The trigger vocabulary is exactly `TAP`, `ON_VISIBLE`,
`ON_NEXT_SECOND`, `ON_NEXT_MINUTE`, `ON_NEXT_HOUR`
(`common/simpleTypes/eventTriggerType.xsd`). A tap *anywhere* on the face
fires the gun — you cannot require the tap to land on the muzzle.

## Can it actually make the BRRRT sound? No.

The Galaxy Watch7 has a speaker. A watch face cannot use it.

Verified against Google's own schema shipped inside the WFF validator, across
**every format version 1 through 5**:

```
$ grep -rin "sound|audio|vibrat|haptic|speaker" <wff>/{1,2,3,4,5}/**.xsd
(no matches)
```

There is no audio element, no vibration element and no haptic element in the
format at any version. Compounding it, a WFF face declares
`android:hasCode="false"` and ships no executable code at all, so there is
nothing that *could* call the audio APIs even if a hook existed.

**The only way to get real sound** would be to abandon Watch Face Format and
rewrite as a Kotlin `WatchFaceService` using the AndroidX watchface library —
a full Android app with code, its own render loop, and its own power,
review and battery characteristics. That is a different project, not a
setting. The muzzle flash is the honest maximum within WFF: a visual report,
silent.

## Verification

| Gate | Result |
|---|---|
| Google WFF validator (v4), incl. tap sequence | PASSED |
| Repo test suite | 235 passed, 84 subtests |
| Studio artwork determinism | 38 assets byte-identical on rebuild |
| XML generation determinism | committed XML matches |
| APK install + pullback | `8d72489b…cebb4db`, 3,323,890 bytes, MATCH |

### A note on running the squadron tests

`tests/engine/test_squadron_collection.py` pins the committed squadron import
to the studio repository's current `HEAD`. Building Warthog requires the
studio checked out on `aircraft/warthog`, which makes those two lineage tests
fail with a `studio_commit` mismatch — a checkout artifact, not a regression;
no squadron artwork changes. Leave the studio on
`phase-3/attitude-squadron-collection` when running the full suite, or use a
separate worktree for Warthog work.

## Art provenance, unchanged

Every pixel is original procedural construction in
`~/AGENOR-Horology/scripts/warthog.py`. No external image is opened.
`docs/reports/AIRCRAFT_WATCH_DISCOVERY.md` established that all collected
aircraft reference is third-party copyright, kept as an inventoried record
and never traced.

## Still open

- The 2-second recognition test has not been run. Whether a stranger says
  "A-10" at arm's length remains unmeasured, and it is the bar that matters.
- Real squadron liveries as the variant axis (23rd FG, Idaho ANG, Desert
  Storm lizard camo) rather than colourways.
- C-130 next, to prove the one-aircraft-one-mechanism rule generalises.
