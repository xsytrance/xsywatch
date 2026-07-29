#!/usr/bin/env python3
"""VECTOR PROBE — phase 0 of the MERIDIAN PRO ship plan, in two rungs.

Everything the redesign is built on rests on two device facts nobody has
ever checked on this hardware, and a face that fails to inflate is a silent
black screen. So: one unproven construct per rung, side-by-side installable.

  A — PARTDRAW. Vector drawing, nothing else. A weighted-stroke zone arc,
      a battery-driven progress sweep, a seconds sweep (so liveness is
      answerable at a glance), a sweep-gradient disc, and a round-rect +
      line cluster. If A is black, the whole vector architecture falls
      back to procedural sprites.

  B — ZERO PERMISSIONS. Rung A plus live readouts of STEP_COUNT, STEP_GOAL,
      STEP_PERCENT, HEART_RATE and BATTERY_CHARGING_STATUS, with an EMPTY
      uses-permission set. AURELIUS proved heart rate flows permissionless
      (the WFF runtime holds the sensor); steps are unproven. The answer
      decides how empty the Play data-safety form is — measured now, not
      discovered at review.

What to read off the wrist:
  A: do the arcs render, does the thin blue ring sweep once a minute,
     does the gold arc sit where the battery is?
  B: STEPS/GOAL/SPCT/HR showing numbers (not 0) with no permission ever
     granted; CHG flipping 0->1 on the charger.

Usage:
    python3 tools/make_vector_probe.py --stage A
    python3 tools/make_vector_probe.py --stage B
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FACE = REPO / "watchfaces/vector-probe"
OUT = FACE / "app/src/main/res/drawable"
RAW = FACE / "app/src/main/res/raw"
sys.path.insert(0, str(Path(__file__).resolve().parent))

AMB0 = ('<Variant mode="AMBIENT" target="alpha" value="0" duration="0.4" '
        'startOffset="0.0" interpolation="EASE_OUT" />')

# Rows for rung B: label baked into the background, value as live text.
ROWS = [
    ("STEPS", "[STEP_COUNT]"),
    ("GOAL",  "[STEP_GOAL]"),
    ("SPCT",  "[STEP_PERCENT]"),
    ("HR",    "[HEART_RATE]"),
    ("CHG",   "[BATTERY_CHARGING_STATUS]"),
]
ROW_0, ROW_PITCH = 236, 40
LABEL_X, VALUE_X, VALUE_W = 190, 210, 130


def build_xml(stage: str, widths: dict[str, int] | None) -> str:
    o = []
    a = o.append
    a('<?xml version="1.0" encoding="utf-8"?>')
    a('<!--')
    a('GENERATED FILE - do not edit by hand.')
    a('  Authoritative source: tools/make_vector_probe.py')
    a(f'  Rung {stage} of the phase 0 device probes;')
    a('  see docs/plans/MERIDIAN_PRO_SHIP_PLAN.md section 3.')
    a('-->')
    a('<WatchFace width="480" height="480">')
    a('  <Metadata key="CLOCK_TYPE" value="ANALOG" />')
    a('  <Metadata key="PREVIEW_TIME" value="10:09:32" />')
    if stage == "B":
        a('  <BitmapFonts>')
        a('    <BitmapFont name="vp">')
        for ch, w in sorted(widths.items()):
            nm = "pct" if ch == "%" else ch
            a(f'      <Character name="{ch}" resource="vp_{nm}" '
              f'width="{w}" height="44" />')
        a('    </BitmapFont>')
        a('  </BitmapFonts>')
    a('  <Scene backgroundColor="#FF000000">')

    if stage == "B":
        a('    <PartImage name="z00_bg" x="0" y="0" width="480" height="480" '
          'alpha="255">')
        a(f'      {AMB0}')
        a('      <Image resource="bg_b" />')
        a('    </PartImage>')

    # ---- 1. the zone arc: WeightedStroke -------------------------------
    a('    <PartDraw name="z10_zone" x="0" y="0" width="480" height="480" '
      'alpha="255">')
    a('      <Variant mode="AMBIENT" target="alpha" value="100" '
      'duration="0.4" startOffset="0.0" interpolation="EASE_OUT" />')
    a('      <Arc centerX="240" centerY="240" width="420" height="420" '
      'startAngle="-120" endAngle="120">')
    a('        <WeightedStroke colors="#2F7A66 #C89A3C #B8402F" '
      'weights="5.0 3.0 2.0" thickness="16" cap="ROUND" />')
    a('      </Arc>')
    a('    </PartDraw>')

    # ---- 2. battery progress: Transform on endAngle --------------------
    a('    <PartDraw name="z11_batt" x="0" y="0" width="480" height="480" '
      'alpha="255">')
    a(f'      {AMB0}')
    a('      <Arc centerX="240" centerY="240" width="360" height="360" '
      'startAngle="-120" endAngle="120">')
    a('        <Stroke color="#22FFFFFF" thickness="10" cap="ROUND" />')
    a('      </Arc>')
    a('      <Arc centerX="240" centerY="240" width="360" height="360" '
      'startAngle="-120" endAngle="120">')
    a('        <Stroke color="#EBC468" thickness="10" cap="ROUND" />')
    a('        <Transform target="endAngle" value="-120 + 240 * '
      'clamp([BATTERY_PERCENT], 0, 100) / 100" />')
    a('      </Arc>')
    a('    </PartDraw>')

    # ---- 3. seconds sweep: liveness at a glance ------------------------
    a('    <PartDraw name="z12_sec" x="0" y="0" width="480" height="480" '
      'alpha="255">')
    a(f'      {AMB0}')
    a('      <Arc centerX="240" centerY="240" width="300" height="300" '
      'startAngle="0" endAngle="360">')
    a('        <Stroke color="#14FFFFFF" thickness="6" cap="BUTT" />')
    a('      </Arc>')
    a('      <Arc centerX="240" centerY="240" width="300" height="300" '
      'startAngle="0" endAngle="0">')
    a('        <Stroke color="#7ED0FF" thickness="6" cap="ROUND" />')
    a('        <Transform target="endAngle" '
      'value="([SECOND] + [MILLISECOND] / 1000) * 6" />')
    a('      </Arc>')
    a('    </PartDraw>')

    # ---- 4. sweep gradient in a Fill, plus the other shapes ------------
    a('    <PartDraw name="z13_shapes" x="0" y="0" width="480" height="480" '
      'alpha="255">')
    a(f'      {AMB0}')
    a('      <Ellipse x="100" y="310" width="100" height="100">')
    a('        <Fill color="#FFFFFFFF">')
    a('          <SweepGradient centerX="150" centerY="360" startAngle="0" '
      'endAngle="360" colors="#B8402F #C89A3C #2F7A66 #B8402F" '
      'positions="0.0 0.33 0.66 1.0" />')
    a('        </Fill>')
    a('      </Ellipse>')
    a('      <RoundRectangle x="290" y="318" width="96" height="84" '
      'cornerRadiusX="10" cornerRadiusY="10">')
    a('        <Stroke color="#9CA8B6" thickness="4" />')
    a('      </RoundRectangle>')
    a('      <Line startX="300" startY="360" endX="376" endY="360">')
    a('        <Stroke color="#EBC468" thickness="3" />')
    a('      </Line>')
    a('    </PartDraw>')

    # ---- rung B: the permissionless sources ----------------------------
    if stage == "B":
        for i, (label, src) in enumerate(ROWS):
            y = ROW_0 + i * ROW_PITCH
            a(f'    <PartText name="z2{i}_val" x="{VALUE_X}" y="{y - 17}" '
              f'width="{VALUE_W}" height="34">')
            a(f'      {AMB0}')
            a(f'      <Text align="START"><BitmapFont family="vp" size="26" '
              f'color="#EBC468"><Template>%d<Parameter expression="{src}" />'
              f'</Template></BitmapFont></Text>')
            a('    </PartText>')

    a('  </Scene>')
    a('</WatchFace>')
    return "\n".join(o) + "\n"


def background_b() -> Image.Image:
    """Labels for rung B, baked. The values beside them are live text."""
    SS = 3
    S = 480 * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13 * SS)
    ft = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11 * SS)
    d.text((240 * SS, 196 * SS), "ZERO PERMISSIONS DECLARED", font=ft,
           fill=(128, 140, 152, 255), anchor="mm")
    for i, (label, _) in enumerate(ROWS):
        y = (ROW_0 + i * ROW_PITCH) * SS
        d.text((LABEL_X * SS, y), label, font=f, fill=(150, 162, 176, 255),
               anchor="rm")
    return img.resize((480, 480), Image.LANCZOS)


def preview(stage: str) -> Image.Image:
    """What the picker shows, and the reference the wrist is compared to."""
    import math
    img = Image.new("RGB", (480, 480), (0, 0, 0))
    d = ImageDraw.Draw(img)
    def arc(r, a0, a1, col, w):
        d.arc([240 - r, 240 - r, 240 + r, 240 + r], a0 - 90, a1 - 90,
              fill=col, width=w)
    arc(210, -120, 0, (47, 122, 102), 16)
    arc(210, 0, 72, (200, 154, 60), 16)
    arc(210, 72, 120, (184, 64, 47), 16)
    arc(180, -120, 67, (235, 196, 104), 10)      # battery at 78%
    arc(150, 0, 192, (126, 208, 255), 6)         # seconds at 32
    for i in range(0, 360, 20):
        x = 150 + 50 * math.cos(math.radians(i))
        y = 360 + 50 * math.sin(math.radians(i))
        d.pieslice([100, 310, 200, 410], i, i + 20,
                   fill=(int(184 - i / 3), int(64 + i / 4), 60))
    d.rounded_rectangle([290, 318, 386, 402], 10, outline=(156, 168, 182),
                        width=4)
    d.line([300, 360, 376, 360], fill=(235, 196, 104), width=3)
    f = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    d.text((240, 40), f"VPROBE {stage}", font=f, fill=(226, 232, 238),
           anchor="mm")
    return img


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["A", "B"], required=True)
    a = ap.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    widths = None
    if a.stage == "B":
        from make_an_gauge import bitmap_glyphs
        widths = bitmap_glyphs(OUT, prefix="vp")
        background_b().save(OUT / "bg_b.png", optimize=True)

    (RAW / "watchface.xml").write_text(build_xml(a.stage, widths))
    preview(a.stage).resize((192, 192), Image.LANCZOS).save(
        OUT / "preview.png", optimize=True)
    preview(a.stage).save(REPO / f"previews/VPROBE-{a.stage}-expected.png")
    print(f"  rung {a.stage} -> {RAW / 'watchface.xml'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
