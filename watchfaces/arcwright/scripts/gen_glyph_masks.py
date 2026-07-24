#!/usr/bin/env python3
"""Glyph masks for displacement-engraved digit tiles.

Per glyph, two aligned masks at 8x tile resolution:
  disp_*  — gaussian-blurred silhouette -> smooth chamfer slope when used as
            negative displacement on the plate
  fill_*  — eroded sharp silhouette -> the oil-dark fill zone on the floor
            (chamfer band between the two stays bright-cut steel)
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'assets-source/fonts/orbitron.ttf')
OUT = os.path.join(ROOT, 'assets-source/glyphs/masks')
os.makedirs(OUT, exist_ok=True)

SETS = [('lg', 52, 68, 0.72), ('sm', 32, 44, 0.72)]
GLYPHS = list('0123456789') + [':']
SS = 8

for tag, w, h, hfrac in SETS:
    W, H = w * SS, h * SS
    # size the font so cap height ~= hfrac of the tile
    fs = int(H * hfrac * 0.92)
    font = ImageFont.truetype(FONT, fs)
    for g in GLYPHS:
        sil = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(sil)
        bbox = d.textbbox((0, 0), g, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((W - tw) / 2 - bbox[0], (H - th) / 2 - bbox[1]), g,
               font=font, fill=255)
        name = 'colon' if g == ':' else g
        # displacement: blur = chamfer slope (wider blur -> gentler walls)
        sil.filter(ImageFilter.GaussianBlur(SS * 0.75)).save(
            os.path.join(OUT, f'disp_{tag}_{name}.png'))
        # fill zone: eroded so the chamfer band remains bright-cut
        sil.filter(ImageFilter.MinFilter(2 * int(SS * 0.9) + 1)).save(
            os.path.join(OUT, f'fill_{tag}_{name}.png'))
    print(f'{tag}: masks for {len(GLYPHS)} glyphs at {W}x{H}')
print('masks written')
