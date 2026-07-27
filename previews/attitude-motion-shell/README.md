# ATTITUDE motion preview shell — PREVIEW ONLY

```
╔══════════════════════════════════════════════════════════════════════╗
║  PREVIEW_ONLY: true          FORMAL_EVIDENCE_ALLOWED: false          ║
║  PRODUCTION_ASSET: false     RELEASE_CANDIDATE: false                ║
║  OWNER_PIXEL_APPROVED: false                                         ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Branch:** `preview/attitude-motion-shell`

## What this is, and what it is not

A clean shell for judging the horizon **motion** on the wrist. The
disposable spike is deliberately crude, and on-device its block lettering
and placeholder hands made the motion harder to read rather than easier.
This strips the noise while changing nothing about the motion itself.

It is **not** MERIDIAN, not production artwork, and not a candidate for
anything. It is intentionally a preview instrument rather than a luxury
face.

**The accepted spike APKs and the formal device harness remain
authoritative for all formal testing.** Nothing here may be fed into that
harness as though it were a validated spike package.

## The motion is imported, not reimplemented

`generate_preview.py` imports the accepted spike generator and calls its
expression builders directly. Clamps, gains, roll sign and the emitted
expression text are the **same code**, not a retyped copy, so the two
cannot drift apart. The tests compare against that generator rather than
against numbers duplicated in two places.

| Profile | Displayed roll | Displayed pitch | Package |
|---|---|---|---|
| DAMPED | ±14° | ±14 px | `com.xsytrance.attitude.preview.damped` |
| PROPOSED | ±22° | ±26 px | `com.xsytrance.attitude.preview.proposed` |
| ASSERTIVE | ±30° | ±34 px | `com.xsytrance.attitude.preview.assertive` |

Shared: wrist roll clamped ±45°, wrist pitch clamped ±40°, neutral maps
exactly to zero, no smoothing or easing anywhere, and AOD forces neutral
roll and pitch.

Aperture geometry is identical to the spike — centre (240, 252),
half-width 156, half-height 74, corner radius 42 — so the **apparent
motion scale is directly comparable**.

## What changed visually

- no analog hands; a real digital time readout instead
- real system text via WFF's standard `sans-serif`, **no custom glyph
  alphabet** and no pseudo-digital characters
- matte near-black field, two very quiet concentric rings, nothing else
- deep desaturated aviation blue sky, warm umber ground, crisp horizon
- sparse thin pitch ladder
- small fixed amber datum that stays put while the horizon moves beneath it
- profile name and `MOTION PREVIEW` where they can be read
- no date, steps, heart rate, battery, complications or seconds

AOD is a darker simplified shell: neutral frozen horizon, ladder removed
entirely via a separate ambient resource, time and profile label retained,
no large bright regions. **AOD figures here are concept-only and are not
WO-P7 compliance evidence.**

## Coexistence

The three preview packages coexist with each other and with all three
accepted spike packages. Six faces can be installed at once.

## Commands

```bash
python3 previews/attitude-motion-shell/generate_preview.py          # sources
python3 previews/attitude-motion-shell/generate_preview.py --check  # determinism
python3 previews/attitude-motion-shell/render_review.py             # review pixels
./previews/attitude-motion-shell/build_preview.sh                   # 3 debug APKs
python3 -m unittest discover -s previews/attitude-motion-shell/tests
```

## Review pixels

`review/` holds nine committed renders — three normal, three AOD, two
comparison sheets and a motion-state sheet — with dimensions and SHA-256 in
`review/REVIEW_MANIFEST.json`.

They compose the **same generated resources the watch face loads**, so the
layering is real. Only the text is drawn at render time rather than by WFF:
the face uses the device's `sans-serif`, and the previews use DejaVu Sans
(free licence) to stand in. Glyph shapes will differ slightly on-device;
layout, size and hierarchy will not.

**Hashes are not approval.** The owner and ChatGPT must look at actual
pixels.

## Installation

Not installed, and no device was contacted. If these are sent for a
phone-mediated look, the same rules apply as before: **a phone-side
installer may repackage or re-sign**, so a preview package is never a
substitute for a pullback-verified accepted spike build, and any subjective
impression formed here must be disclosed before later formal owner
observations.
