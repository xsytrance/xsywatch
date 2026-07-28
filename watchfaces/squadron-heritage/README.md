# MERIDIAN HERITAGE

A field watch that flew. Cream painted numerals, aged brass furniture, warm patina on a sand-drab dial.

Part of **ATTITUDE SQUADRON** — a collection of watch faces rooted in
vintage prop-fighter aircraft. Every face in the family shares one platform:
the same architecture, complication logic, live data bindings and horizon
motion contract. This variant differs in artwork and identity only.

**Development build, not a release candidate.** Debug signing only, no
bundle, no store metadata, package namespaced `.dev`.

| | |
|---|---|
| Package | `com.xsytrance.squadron.heritage.dev` |
| Version | `0.1.0-dev` (versionCode 1) |
| Dial mark | MERIDIAN / HERITAGE |
| Markers | aviator |
| Horizon window | knurled |
| Dial texture | grain |
| Weathering | 50% |

## The signature

The hour and minute hands are sculpted propeller blades — a round shank with
collar rivets, an asymmetric paddle planform with the axis at 32% chord, a
hard camber split between lit and shaded faces, a lume stripe on the lit
face, a painted tip warning band and an opposed counterweight blade. The
pinion is the spinner hub.

## Regenerating

Artwork authority is the studio repository. Do not hand-edit `res/drawable`
or `res/raw/watchface.xml`; both are generated and both are checked.

```bash
python3 tools/squadron_scaffold.py --only heritage
python3 tools/generate_face.py squadron-heritage
tools/build_face.sh squadron-heritage
```
