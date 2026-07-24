#!/usr/bin/env python3
"""P1 probe: crude flat glyphs to validate WFF v4 BitmapFont runtime behavior
BEFORE investing in Blender-engraved art.

Deliberately ugly and diagnostic: each glyph carries a border showing its
exact box and a size-class letter, so emulator screenshots reveal scaling,
clipping, alignment and padding behavior unambiguously.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')
FONT = os.path.join(ROOT, 'assets-source/fonts/orbitron.ttf')
os.makedirs(RES, exist_ok=True)

SETS = [('lg', 52, 68, 46), ('sm', 32, 44, 28)]
GLYPHS = list('0123456789') + [':']

for tag, w, h, fs in SETS:
    font = ImageFont.truetype(FONT, fs)
    for g in GLYPHS:
        im = Image.new('RGBA', (w, h), (30, 32, 38, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w - 1, h - 1], outline=(120, 130, 150, 255), width=1)
        bbox = d.textbbox((0, 0), g, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((w - tw) / 2 - bbox[0], (h - th) / 2 - bbox[1]), g,
               font=font, fill=(190, 195, 205, 255))
        name = 'colon' if g == ':' else g
        im.save(os.path.join(RES, f'probe_{tag}_{name}.png'))
    print(f'{tag}: {len(GLYPHS)} glyphs at {w}x{h}')
print('probe glyphs written to res/drawable-nodpi')
