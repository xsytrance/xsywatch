#!/usr/bin/env python3
"""MERIDIAN PROBE — assets and watchface.xml for the instrument face.

WHY THIS FACE EXISTS

Phase 0 of docs/plans/MERIDIAN_PRO_MASTER_PLAN.md. It is a measuring
instrument, not a design, and it answers questions that would otherwise be
discovered halfway through building a face on top of them.

  1. WHAT ARE WEATHER.CONDITION'S INTEGERS? The source exists at every format
     version and the schema documents none of its values, which is why the
     collection branches on precipitation and temperature instead. Fog, mist,
     thunder, hail and sleet are not derivable that way. CONDITION_NAME is a
     string, so a face cannot branch on it — but it CAN print it, next to the
     integer. Wear this through varied weather and the mapping falls out.

  2. DOES THE FORECAST RETURN ANYTHING? WEATHER.HOURS.<n>.* and
     WEATHER.DAYS.<n>.* are real sources at v4 and v5 — declared as xs:pattern
     members of weatherSourceType, which is why a search of the enumerations
     missed them and an earlier revision of the plan wrongly said they did not
     exist. What the schema does NOT say is how many indices a provider
     populates. Each index carries its own IS_AVAILABLE, which implies the
     answer is "ask it". So we ask it: H+0, H+3 and D+1 are shown next to
     their availability flags.

  3. DOES THE v4 DOUBLED PREFIX RESOLVE? Current-conditions UV is spelled
     WEATHER.WEATHER.UV_INDEX at v4 and WEATHER.UV_INDEX at v5 — but the
     forecast's UV is spelled cleanly at BOTH. The probe prints
     WEATHER.WEATHER.UV_INDEX directly above WEATHER.HOURS.0.UV_INDEX. Two
     numbers, one glance, and we learn whether the doubled prefix is a live
     source or a schema typo nothing implements.

  4. CAN A COMPLICATION DRIVE A NEEDLE? Almost certainly not. The format
     exposes only COMPLICATION.RANGED_VALUE_COLOR_INTERPOLATE and
     COMPLICATION.WEIGHTED_ELEMENTS_COLORS, and both are colour-interpolation
     weights rather than readable numbers — there is no source to put in a
     Transform. The slot costs four lines, so it is carried to settle the
     point on hardware rather than by inference.

  5. IS THE SUN COMPASS CONVINCING? It needs no complication and no
     magnetometer: solar azimuth is 180 deg at local solar noon and walks
     ~15 deg per hour either side. That is the plan's section 7A
     recommendation, so the needle here IS a sun compass, and wearing the
     probe is how we find out whether it reads as an instrument or as a
     decoration. Northern hemisphere assumed — there is no location source.

WHY THIS SCRIPT ALSO WRITES THE XML

The BitmapFont is proportional, so every <Character> has to declare the width
of the glyph that was actually rendered. Splitting that across a generator and
a hand-written spec is exactly the kind of drift the repo has been bitten by
before. One script owns both, and the widths are correct by construction.

This is the collection's FIRST BITMAP FONT WITH LETTERS — every face so far
carries digits and a percent sign only, because every readout so far was a
number. CONDITION_NAME is words.

Usage:
    python3 tools/make_probe_assets.py
    python3 tools/make_probe_assets.py --check   # verify, write nothing
"""

from __future__ import annotations

import argparse
import math
import string
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FACE = REPO / "watchfaces/probe"
OUT = FACE / "app/src/main/res/drawable"
XML = FACE / "app/src/main/res/raw/watchface.xml"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

GLYPH_H = 34
SS = 3

# WFF Character names are the literal characters. Space needs a real, blank
# glyph or the renderer has nothing to advance by.
CHARS = list(string.ascii_uppercase) + list(string.digits) + [
    " ", ".", ":", "-", "/", "%", "?"]
SAFE = {" ": "space", ".": "dot", ":": "colon", "-": "dash", "/": "slash",
        "%": "pct", "?": "query"}

INK = (226, 232, 238, 255)
DIM = (128, 140, 152, 255)
ACCENT = (255, 176, 64, 255)

# --- layout -----------------------------------------------------------
# Everything is placed against a 480 round face. The rows run down the
# middle where the disc is widest; the last row sits at y=412, where the
# disc still spans x=73..407, so nothing is clipped by the bezel.
ROSE = 118                      # compass card, centred at (240, 104)
ROSE_X, ROSE_Y = 240 - ROSE // 2, 45
ROSE_CX, ROSE_CY = ROSE_X + ROSE // 2, ROSE_Y + ROSE // 2

ROW_0, ROW_PITCH = 202, 21
LABEL_R = 118                   # baked labels are right-aligned here
COL1, COL2, COL3 = 126, 250, 340

TIME_Y = 180
SLOT = (185, 424, 110, 30)      # x, y, w, h


def cell_metrics():
    """One vertical cell shared by every glyph.

    Cropping each glyph to its own ink box and rescaling that to a common
    height destroys the font's vertical metrics: a full stop and a colon have
    tiny ink boxes, so they get magnified into tall bars, and a bitmap font
    has no baseline of its own to put them back on. So the cell is measured
    once across the whole charset and every glyph is drawn into it at a fixed
    baseline. Only the horizontal extent varies.
    """
    f = ImageFont.truetype(FONT, GLYPH_H * SS)
    boxes = [f.getbbox(c) for c in CHARS if c != " "]
    return f, min(b[1] for b in boxes), max(b[3] for b in boxes)


def glyph(ch: str, f, top: int, bot: int) -> Image.Image:
    cell_h = bot - top
    scale = GLYPH_H / cell_h
    # A side bearing, because adjacent glyphs are composited edge to edge and
    # without it "HI 19" closes up into "HI19".
    bear = round(1.4 * SS)
    if ch == " ":
        return Image.new("RGBA", (max(1, round(GLYPH_H * 0.30)), GLYPH_H),
                         (0, 0, 0, 0))
    b = f.getbbox(ch)
    w = max(1, b[2] - b[0])
    img = Image.new("RGBA", (w + 2 * bear, cell_h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((bear - b[0], -top), ch, font=f, fill=INK)
    return img.resize((max(1, round(img.width * scale)), GLYPH_H),
                      Image.LANCZOS)


def compass_rose(size: int = ROSE) -> Image.Image:
    """A card with cardinal letters and degree ticks. The needle rotates over
    it, so the card itself never moves."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2.0
    d.ellipse([2 * SS, 2 * SS, S - 2 * SS, S - 2 * SS],
              outline=(90, 100, 112, 255), width=2 * SS)
    for deg in range(0, 360, 10):
        a = math.radians(deg - 90)
        major = deg % 90 == 0
        r0 = c * (0.80 if major else 0.88)
        d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0),
                (c + math.cos(a) * c * 0.95, c + math.sin(a) * c * 0.95)],
               fill=INK if major else DIM, width=(3 if major else 1) * SS)
    f = ImageFont.truetype(FONT, int(13 * SS))
    for deg, ch in ((0, "N"), (90, "E"), (180, "S"), (270, "W")):
        a = math.radians(deg - 90)
        d.text((c + math.cos(a) * c * 0.66, c + math.sin(a) * c * 0.66), ch,
               font=f, fill=ACCENT if ch == "N" else INK, anchor="mm")
    return img.resize((size, size), Image.LANCZOS)


def needle(size: int = ROSE) -> Image.Image:
    """Drawn pointing up, i.e. at bearing 000. The spec rotates it to the
    solar azimuth, so the red tip points at where the sun bears."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2.0
    d.polygon([(c, c - c * 0.74), (c - 5 * SS, c), (c + 5 * SS, c)],
              fill=(232, 72, 56, 255))
    d.polygon([(c, c + c * 0.52), (c - 4 * SS, c), (c + 4 * SS, c)],
              fill=(150, 158, 168, 255))
    d.ellipse([c - 6 * SS, c - 6 * SS, c + 6 * SS, c + 6 * SS],
              fill=(40, 44, 50, 255), outline=INK, width=SS)
    return img.resize((size, size), Image.LANCZOS)


# Row labels, baked. Index matches ROWS in the XML section below.
ROW_LABELS = ["WX", "COND", "", "TEMP", "RAIN", "UV",
              "H+0", "H+3", "D+1", "D+1", "MOON"]


def background(size: int = 480) -> Image.Image:
    """Static labels. Baked rather than composed from text parts because none
    of them ever change, and a part per word would triple the layer count."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (8, 10, 14, 255))
    d = ImageDraw.Draw(img)
    f_small = ImageFont.truetype(FONT, int(11 * SS))
    f_tiny = ImageFont.truetype(FONT, int(8 * SS))

    d.text((S / 2, 18 * SS), "MERIDIAN PROBE", font=f_small, fill=ACCENT,
           anchor="mm")
    d.text((S / 2, 31 * SS), "WX DECODE / FORECAST / SUN COMPASS",
           font=f_tiny, fill=DIM, anchor="mm")

    for i, lab in enumerate(ROW_LABELS):
        if not lab:
            continue
        y = ROW_0 + i * ROW_PITCH
        d.text((LABEL_R * SS, y * SS), lab, font=f_tiny, fill=DIM, anchor="rm")

    # A hairline under the readout block, so the complication slot below it
    # reads as separate hardware rather than another row.
    y = (ROW_0 + 10 * ROW_PITCH + 12) * SS
    d.line([(150 * SS, y), (330 * SS, y)], fill=(46, 52, 60, 255), width=SS)
    return img.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------------
# watchface.xml
# ---------------------------------------------------------------------

# One row = (stage, column, label-index, format, expression). Column 0 is the
# full-width centred row used for the one string readout.
#
# Every readout is %d over round(), deliberately. Mixing %d and %.1f across
# sources whose runtime types are undocumented is a way to earn a format
# exception on the wrist a week into a two-week wear; integers lose nothing
# here that the decode needs.
#
# THE STAGE TAG EXISTS BECAUSE THE FIRST BUILD RENDERED AS A BLACK SCREEN.
#
# A watch face that fails to inflate shows nothing at all — there is no
# partial render and no on-screen error. The first probe put a dozen unproven
# sources and three never-used elements into one face, so any single one of
# them being rejected killed the whole thing and told us nothing about which.
# That is a bad instrument: the entire point is to isolate a variable.
#
# So the probe is now a ladder. Each stage adds ONE class of risk to the one
# below it, and each builds as its own package, so they sit in the picker
# together and the last one that renders names the culprit.
#
#   A  scaffold only — plate, sun compass, digital time. Every element here
#      is already shipping in the MERIDIAN line; only the 43-glyph font is
#      new, and a font that big has never been tried.
#   B  + current weather, all sources proven in shipping faces, PLUS the
#      string readout (%s through <Upper>), which is new.
#   C  + the v4 doubled prefix WEATHER.WEATHER.UV_INDEX, and MOON_PHASE_
#      POSITION. Both are declared by the schema and neither has ever run.
#   D  + the forecast family. The biggest unknown: sixteen sources the
#      schema declares and no provider is known to populate.
#   E  + the complication slot. = the full probe as first built.
STAGES = "ABCDE"

ROWS = [
    # -- stage B: current conditions, every source already shipping ------
    # WX — is there any weather data at all, and is the provider erroring
    ("B", 1, 0, "%d", "[WEATHER.IS_AVAILABLE]"),
    ("B", 2, 0, "ERR:%d", "[WEATHER.IS_ERROR]"),
    # COND — the integer under decode, and whether it is a day or night value
    ("B", 1, 1, "%d", "[WEATHER.CONDITION]"),
    ("B", 2, 1, "DAY:%d", "[WEATHER.IS_DAY]"),
    # the name, full width — the only string on the face, and the only
    # <Upper> and %s anywhere in the collection
    ("B", 0, 2, "%s", "[WEATHER.CONDITION_NAME]"),
    # temperature now, and today's declared range
    ("B", 1, 3, "%d", "round([WEATHER.TEMPERATURE])"),
    ("B", 2, 3, "HI:%d", "round([WEATHER.TEMPERATURE_HIGH])"),
    ("B", 3, 3, "LO:%d", "round([WEATHER.TEMPERATURE_LOW])"),
    ("B", 1, 4, "%d%%", "round([WEATHER.CHANCE_OF_PRECIPITATION])"),
    # -- stage C: declared, never run -----------------------------------
    ("C", 1, 5, "V4:%d", "round([WEATHER.WEATHER.UV_INDEX])"),
    ("C", 1, 10, "%d%%", "round([MOON_PHASE_POSITION] * 100)"),
    ("C", 2, 10, "SEC:%d", "[SECOND]"),
    # -- stage D: the forecast family -----------------------------------
    ("D", 2, 5, "H0:%d", "round([WEATHER.HOURS.0.UV_INDEX])"),
    ("D", 1, 6, "AV:%d", "[WEATHER.HOURS.0.IS_AVAILABLE]"),
    ("D", 2, 6, "C:%d", "[WEATHER.HOURS.0.CONDITION]"),
    ("D", 3, 6, "T:%d", "round([WEATHER.HOURS.0.TEMPERATURE])"),
    ("D", 1, 7, "AV:%d", "[WEATHER.HOURS.3.IS_AVAILABLE]"),
    ("D", 2, 7, "C:%d", "[WEATHER.HOURS.3.CONDITION]"),
    ("D", 3, 7, "T:%d", "round([WEATHER.HOURS.3.TEMPERATURE])"),
    ("D", 1, 8, "AV:%d", "[WEATHER.DAYS.1.IS_AVAILABLE]"),
    ("D", 2, 8, "CD:%d", "[WEATHER.DAYS.1.CONDITION_DAY]"),
    ("D", 3, 8, "CN:%d", "[WEATHER.DAYS.1.CONDITION_NIGHT]"),
    ("D", 1, 9, "HI:%d", "round([WEATHER.DAYS.1.TEMPERATURE_HIGH])"),
    ("D", 2, 9, "LO:%d", "round([WEATHER.DAYS.1.TEMPERATURE_LOW])"),
    ("D", 3, 9, "P:%d", "round([WEATHER.DAYS.1.CHANCE_OF_PRECIPITATION])"),
]

COL_X = {1: COL1, 2: COL2, 3: COL3}
COL_W = {1: 120, 2: 92, 3: 74}

# Solar azimuth, northern hemisphere: due south (180) at local solar noon,
# walking 15 deg per hour either side. Clock time is used as a stand-in for
# solar time — there is no longitude source to correct it with, which is
# itself part of what wearing this is meant to reveal.
SUN_AZ = ("((180 + 15 * ([HOUR_0_23] + [MINUTE] / 60 - 12)) % 360)")

HEADER = """<?xml version="1.0" encoding="utf-8"?>
<!--
GENERATED FILE - do not edit by hand.
  Authoritative source: tools/make_probe_assets.py
  Regenerate: python3 tools/make_probe_assets.py

MERIDIAN PROBE is a measuring instrument, not a design. See the module
docstring of the generator for what each readout is here to answer, and
docs/plans/MERIDIAN_PRO_MASTER_PLAN.md section 3 for why phase 0 exists.

Authored at format v4, not v5: v4 is proven on the Watch 7 and every source
this face needs exists there. Confirming that v5 installs and renders at all
is one of the things the probe is for.
-->
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_xml(widths: dict[str, int], stage: str = "E") -> str:
    keep = STAGES[:STAGES.index(stage) + 1]
    o = [HEADER, '<WatchFace width="480" height="480">',
         '  <Metadata key="CLOCK_TYPE" value="DIGITAL" />',
         '  <Metadata key="PREVIEW_TIME" value="10:09:32" />',
         '  <BitmapFonts>', '    <BitmapFont name="pb">']
    for ch in CHARS:
        name = SAFE.get(ch, ch.lower() if ch.isalpha() else ch)
        o.append(f'      <Character name="{esc(ch)}" resource="pb_{name}" '
                 f'width="{widths[ch]}" height="{GLYPH_H}" />')
    o += ['    </BitmapFont>', '  </BitmapFonts>',
          '  <Scene backgroundColor="#FF000000">']

    def ambient(alpha: int = 0, off: str = "0.0") -> str:
        return (f'      <Variant mode="AMBIENT" target="alpha" value="{alpha}"'
                f' duration="0.4" startOffset="{off}" interpolation="EASE_OUT" />')

    # Plate. Everything below it is hidden in ambient: this face is worn for
    # weeks, and a screen of static bright text at fixed positions is a
    # burn-in pattern. Only the dimmed clock survives the transition.
    o += [f'    <PartImage name="z00_plate" x="0" y="0" width="480" '
          f'height="480" alpha="255">', ambient(),
          '      <Image resource="pb_bg" />', '    </PartImage>']

    o += [f'    <PartImage name="z01_rose" x="{ROSE_X}" y="{ROSE_Y}" '
          f'width="{ROSE}" height="{ROSE}" alpha="255">', ambient(),
          '      <Image resource="pb_rose" />', '    </PartImage>']
    o += [f'    <PartImage name="z02_needle" x="{ROSE_X}" y="{ROSE_Y}" '
          f'width="{ROSE}" height="{ROSE}" alpha="255" pivotX="0.5" '
          f'pivotY="0.5">', ambient(),
          f'      <Transform target="angle" value="{esc(SUN_AZ)}" />',
          '      <Image resource="pb_needle" />', '    </PartImage>']

    # Clock. The interactive one goes dark in ambient and a dimmer twin
    # fades up in its place.
    o += [f'    <PartText name="z10_time" x="120" y="{TIME_Y - 15}" '
          f'width="240" height="30">', ambient(),
          '      <Text align="CENTER"><BitmapFont family="pb" size="22" '
          'color="#E8EEF4"><Template>%02d:%02d:%02d'
          '<Parameter expression="[HOUR_0_23]" />'
          '<Parameter expression="[MINUTE]" />'
          '<Parameter expression="[SECOND]" /></Template></BitmapFont></Text>',
          '    </PartText>']
    o += [f'    <PartText name="z11_time_aod" x="120" y="{TIME_Y - 15}" '
          f'width="240" height="30" alpha="0">',
          '      <Variant mode="AMBIENT" target="alpha" value="150" '
          'duration="0.4" startOffset="0.0" interpolation="EASE_IN" />',
          '      <Text align="CENTER"><BitmapFont family="pb" size="22" '
          'color="#8A94A0"><Template>%02d:%02d'
          '<Parameter expression="[HOUR_0_23]" />'
          '<Parameter expression="[MINUTE]" /></Template></BitmapFont></Text>',
          '    </PartText>']

    for i, (st, col, row, fmt, expr) in enumerate(ROWS):
        if st not in keep:
            continue
        y = ROW_0 + row * ROW_PITCH
        if col == 0:
            x, w, align = 60, 360, "CENTER"
        else:
            x, w, align = COL_X[col], COL_W[col], "START"
        body = (f'<Template>{esc(fmt)}<Parameter expression="{esc(expr)}" />'
                f'</Template>')
        # CONDITION_NAME arrives in the provider's own casing and the font
        # has no lowercase glyphs, so it is folded rather than dropped.
        if "%s" in fmt:
            body = f'<Upper>{body}</Upper>'
        o += [f'    <PartText name="z2{i:02d}_r{row}c{col}" x="{x}" '
              f'y="{y - 11}" width="{w}" height="22">', ambient(off="0.1"),
              f'      <Text align="{align}"><BitmapFont family="pb" size="15" '
              f'color="#E2E8EE">{body}</BitmapFont></Text>',
              '    </PartText>']

    # The complication slot. RANGED_VALUE is the type a compass provider
    # would use; WATCH_BATTERY is the default so the slot visibly populates
    # before any provider is assigned, and an empty box cannot be mistaken
    # for a bound-but-silent one.
    sx, sy, sw, sh = SLOT
    if "E" in keep:
        o += [f'    <ComplicationSlot name="probe_slot" x="{sx}" y="{sy}" '
              f'width="{sw}" height="{sh}" slotId="1001" '
              f'supportedTypes="RANGED_VALUE SHORT_TEXT">',
              '      <DefaultProviderPolicy '
              'defaultSystemProvider="WATCH_BATTERY" '
              'defaultSystemProviderType="RANGED_VALUE" />',
              f'      <BoundingBox x="{sx}" y="{sy}" width="{sw}" '
              f'height="{sh}" />',
              '      <Complication type="RANGED_VALUE" />',
              '      <Complication type="SHORT_TEXT" />',
              '      <Variant mode="AMBIENT" target="alpha" value="0" '
              'duration="0.4" startOffset="0.0" interpolation="EASE_OUT" />',
              '    </ComplicationSlot>']

    o += ['  </Scene>', '</WatchFace>', '']
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the tree matches this script; write nothing")
    ap.add_argument("--stage", choices=list(STAGES), default="E",
                    help="risk ladder rung to emit; see STAGES. Default E is "
                         "the full probe.")
    a = ap.parse_args()

    f, top, bot = cell_metrics()
    glyphs = {ch: glyph(ch, f, top, bot) for ch in CHARS}
    widths = {ch: g.width for ch, g in glyphs.items()}
    xml = build_xml(widths, a.stage)

    if a.check:
        if not XML.exists():
            print(f"MISSING {XML.relative_to(REPO)}")
            return 1
        if XML.read_text() != xml:
            print(f"STALE   {XML.relative_to(REPO)} — regenerate")
            return 1
        missing = [ch for ch in CHARS
                   if not (OUT / f"pb_{SAFE.get(ch, ch.lower() if ch.isalpha() else ch)}.png").exists()]
        if missing:
            print(f"MISSING {len(missing)} glyph(s)")
            return 1
        print("PROBE OK — xml and glyphs match the generator")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    XML.parent.mkdir(parents=True, exist_ok=True)
    for ch, g in glyphs.items():
        name = SAFE.get(ch, ch.lower() if ch.isalpha() else ch)
        g.save(OUT / f"pb_{name}.png", optimize=True)
    compass_rose().save(OUT / "pb_rose.png", optimize=True)
    needle().save(OUT / "pb_needle.png", optimize=True)
    bg = background()
    bg.save(OUT / "pb_bg.png", optimize=True)
    bg.resize((192, 192), Image.LANCZOS).save(OUT / "preview.png",
                                              optimize=True)
    XML.write_text(xml)

    print(f"  {len(CHARS)} glyphs + rose + needle + background -> "
          f"{OUT.relative_to(REPO)}")
    print(f"  {len(ROWS)} readouts -> {XML.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
