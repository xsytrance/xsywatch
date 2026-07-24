# Licensing & Attribution

**Status: corrected 2026-07-24** during the Phase-1 review pass. The original
Phase-1 statement that "no embedded TTF/OTF" fonts existed was **wrong** and is
superseded by the audit below (kept per update discipline: the error is
labeled, not erased).

## Repository license

Proprietary / all rights reserved — see [`LICENSE`](../LICENSE). Owner
decision from the Phase-1 review: keep proprietary for now; third-party
notices are explicit; nothing is open-sourced by accident.

## Third-party asset audit (verified from committed bytes)

Machine-readable inventory: [`docs/asset-licenses.json`](asset-licenses.json)
— **27 font files + 1 HDRI**, every entry recorded with SHA-256, embedded
copyright, license id, redistribution/commercial flags, and notice file.
Enforced by `tools/validate.py`: a tracked font/HDRI/EXR without a matching
inventory entry (or with altered bytes, or a missing required notice) is a
validation **ERROR**. This enforcement is negatively tested by
`tools/test_release_workflow.py` fixtures T8/T9.

### Fonts — all SIL Open Font License 1.1

Verified by parsing each font's embedded name table (copyright, license,
license-URL records) — not by filename assumption. All permit redistribution
and commercial use; OFL requires the license text to accompany distribution
(provided in `THIRD_PARTY_NOTICES/fonts/`); fonts may not be sold standalone.

| Typeface | Copyright (embedded) | Used by faces | Notice |
|---|---|---|---|
| Orbitron | 2018 The Orbitron Project Authors (theleagueof) | arcwright, bushido, chronova, pulseface | fonts/orbitron-OFL.txt |
| Marcellus | 2012 Brian J. Bonislawsky / Astigmatic | ares-wargod, aurelius, bone-watch, hellforge, pinball | fonts/marcellus-OFL.txt |
| Marcellus SC | 2012 Brian J. Bonislawsky / Astigmatic | same as Marcellus | fonts/marcellussc-OFL.txt |
| Rajdhani (+SemiBold) | 2014 Indian Type Foundry | aurelius, bushido | fonts/rajdhani-OFL.txt |
| Chakra Petch (+SemiBold) | 2018 The Chakra Petch Project Authors | bushido, pulseface | fonts/chakrapetch-OFL.txt |
| Metamorphous | 2011 Sorkin Type Co | hellforge, pinball | fonts/metamorphous-OFL.txt |
| Pirata One | 2012 R. Fuenzalida, N. Massi | hellforge, pinball | fonts/pirataone-OFL.txt |
| UnifrakturCook | 2010 j. 'mach' wust; 2009 Peter Wiegel | hellforge, pinball | fonts/unifrakturcook-OFL.txt |

### HDRI

`watchfaces/arcwright/assets-source/hdri/studio_small_08_1k.hdr` —
Poly Haven "Studio Small 08", **CC0 1.0** (no attribution required;
provenance recorded in the inventory and in arcwright's BUILD_LOG, which
documents the download: "polyhaven studio_small_08 (CC0)").

## Original work

Watchface XML, Gradle config, Python tooling, and documentation authored by
the project (AGENOR/xsytrance with Claude Code assistance). Dial/layer art
and previews were produced via local AI image generation (ComfyUI/SD-family,
LaMa/IOPaint cleanup) from the owner's own prompts and donor images, plus
Pillow compositing. **Open owner action before commercial sale:** confirm the
license terms of the specific model checkpoints used permit commercial use of
outputs.

## Adding a new third-party asset (procedure)

1. Verify the actual source and license of the bytes you are committing.
2. Add the file, then add its entry (path, sha256, license, flags, notice) to
   `docs/asset-licenses.json`.
3. Add the license/notice text under `THIRD_PARTY_NOTICES/` if required.
4. `python3 tools/validate.py` must pass — it fails on unrecorded assets.
