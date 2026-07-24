#!/usr/bin/env python3
"""Post-process raw 4x glyph renders: LANCZOS downscale + faint AO halo,
write final PNGs to assets-source/glyphs + res/drawable-nodpi."""
import os

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'assets-source', 'glyphs', 'raw4x')
OUT = os.path.join(ROOT, 'assets-source', 'glyphs')
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')
SS = 4

for f in sorted(os.listdir(RAW)):
    if not f.endswith('.png'):
        continue
    im = Image.open(os.path.join(RAW, f)).convert('RGBA')
    final = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    # faint contact-shadow halo hugging the carved silhouette
    a = final.getchannel('A')
    halo = a.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: int(v * 0.16))
    base = Image.new('RGBA', final.size, (0, 0, 0, 0))
    base.putalpha(halo)
    base.alpha_composite(final)
    base.save(os.path.join(OUT, f))
    base.save(os.path.join(RES, f))
    print(f'{f}: {base.size[0]}x{base.size[1]}')
print('glyphs post-processed -> assets-source/glyphs + drawable-nodpi')
