# Licensing & Attribution Status

Status as audited 2026-07-24 (Phase 1). **No LICENSE file exists yet** — the
repository is currently all-rights-reserved by default. Choosing a license
(or deliberately staying proprietary for commercial faces) is an owner
decision — flagged for AGENOR.

## Original work

- All watchface XML, Gradle configuration, Python tooling, and documentation
  in this repository were authored by the project (AGENOR/xsytrance with
  Claude Code assistance). No third-party watchface code was copied.

## Generated art assets

- Dial art, layer art, and preview images in `res/drawable*/` were produced
  via local AI image generation (ComfyUI/Stable-Diffusion-family models and
  LaMa/IOPaint cleanup) plus Python/Pillow compositing — from the owner's own
  prompts and donor images. Provenance notes per face in each face README.
  **Action for owner:** confirm the license terms of the specific model
  checkpoints used permit commercial distribution before selling any face.

## Fonts

- Faces use WFF built-in text rendering and/or pre-rendered bitmap glyph
  sheets generated locally. If any TTF/OTF ships inside a face's resources,
  its license must be recorded here before release. Phase-1 scan found font
  files only as pre-rendered PNG glyph sheets (no embedded TTF/OTF in source
  projects; validation checks for this).

## Third-party code/tools

- Build stack (Gradle, AGP, Kotlin, Android SDK, WFF): standard licenses,
  build-time only, nothing redistributed inside APKs beyond normal Android
  packaging.
- Google WFF validator: Apache-2.0, used as an external tool.

## Sibling repo

- `AGENOR-Horology` documents CC0 sourcing (Poly Haven) for HDRIs and
  free-software-only tooling; same owner decision needed on a top-level
  license there.
