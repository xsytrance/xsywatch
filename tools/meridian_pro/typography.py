"""MERIDIAN PRO — glyphs and live-text emission.

Two kinds of text on this face and they are built differently:

  BAKED labels (BATTERY, STEPS, BPM, 24H, the window captions) go onto the
  background sprite AFTER the Kontext pass, engraved. They never change, so
  a part each would be waste — and Kontext must not be allowed to typeset
  them, because it invents letterforms.

  LIVE readouts (battery %, steps, goal, HR, HH, date fields, temp, precip)
  are WFF BitmapFont text. Glyphs are white-with-alpha because the runtime
  tints them flat; depth comes from the face drawing each number twice
  (shadow pass, then fill) — the halo lesson from COMMODORE PRO.

The letter set is the full A-Z: DAY_OF_WEEK_S / MONTH_S return words, and
they pass through <Upper> since the provider's casing is its own business.
A-Z BitmapFont letters have not run on this device before (the face that
carried them first went black for other reasons and was shelved), so if
this face blacks, the ladder isolates the font first.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

SS = 4
GLYPH_H = 46

_F = os.path.expanduser("~/.local/share/fonts")
FONT_BOLD = f"{_F}/BarlowCondensed-Bold.ttf"
if not os.path.exists(FONT_BOLD):
    FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CHARS = [str(i) for i in range(10)] + [chr(c) for c in range(65, 91)] + \
        ["%", "-", "/"]
SAFE = {"%": "pct", "-": "dash", "/": "slash"}


def emit_glyphs(out_dir, prefix: str = "mp") -> dict[str, int]:
    """All glyphs share one measured cell — the colon-becomes-a-bar lesson."""
    f = ImageFont.truetype(FONT_BOLD, GLYPH_H * SS)
    boxes = [f.getbbox(c) for c in CHARS]
    top, bot = min(b[1] for b in boxes), max(b[3] for b in boxes)
    cell = bot - top
    scale = GLYPH_H / cell
    bear = round(SS * 1.1)
    widths = {}
    for ch in CHARS:
        b = f.getbbox(ch)
        w = max(1, b[2] - b[0])
        img = Image.new("RGBA", (w + 2 * bear, cell), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((bear - b[0], -top), ch, font=f,
                                 fill=(255, 255, 255, 255))
        img = img.resize((max(1, round(img.width * scale)), GLYPH_H),
                         Image.LANCZOS)
        img.save(out_dir / f"{prefix}_{SAFE.get(ch, ch.lower())}.png",
                 optimize=True)
        widths[ch] = img.width
    return widths


def font_xml(widths: dict[str, int], family: str = "mp",
             prefix: str = "mp") -> list[str]:
    o = ['  <BitmapFonts>', f'    <BitmapFont name="{family}">']
    for ch, w in sorted(widths.items()):
        o.append(f'      <Character name="{ch}" '
                 f'resource="{prefix}_{SAFE.get(ch, ch.lower())}" '
                 f'width="{w}" height="{GLYPH_H}" />')
    o += ['    </BitmapFont>', '  </BitmapFonts>']
    return o


def readout(name, x, y, w, h, size, template, params, colour="#EBC468",
            amb=0, align="CENTER", family="mp", upper=False) -> list[str]:
    """A live number with a closed halo: four diagonal passes, a cast
    shadow, then the fill. Six PartTexts, no new construct."""
    inner = "".join(f'<Parameter expression="{p}" />' for p in params)
    body = f'<Template>{template}{inner}</Template>'
    if upper:
        body = f'<Upper>{body}</Upper>'

    def part(tag, dx, dy, col, alpha):
        return [f'    <PartText name="{name}{tag}" x="{x+dx}" y="{y+dy}" '
                f'width="{w}" height="{h}" alpha="{alpha}">',
                f'      <Variant mode="AMBIENT" target="alpha" value="{amb}" '
                'duration="0.4" startOffset="0.2" interpolation="LINEAR" />',
                f'      <Text align="{align}"><BitmapFont family="{family}" '
                f'size="{size}" color="{col}">{body}</BitmapFont></Text>',
                '    </PartText>']
    d = max(2, round(size * 0.10))
    o = []
    for dx, dy in ((-d, -d), (d, -d), (-d, d), (d, d)):
        o += part(f"_h{dx}_{dy}".replace("-", "n"), dx, dy, "#000000", 110)
    o += part("_sh", 0, int(d * 1.6), "#000000", 195)
    o += part("", 0, 0, colour, 255)
    return o
