#!/usr/bin/env python3
"""Engraving masks for ARCWRIGHT's non-digit carved features.

White = carve. Each mask ships two aligned variants like the glyph masks:
  disp_* (blurred -> chamfer slope) and fill_* (eroded -> dark-fill floor).

Masks:
  bezel   — 60-tick perimeter scale, engraved numerals every 5 (1920px)
  label_hrs / label_min / label_sec — instrument labels for display bezels
  makers  — "ARCWRIGHT No.001" arc for the back plate, 6 o'clock
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'assets-source/fonts/orbitron.ttf')
OUT = os.path.join(ROOT, 'assets-source/masks')
os.makedirs(OUT, exist_ok=True)


def emit(name, sil, blur, erode):
    sil.filter(ImageFilter.GaussianBlur(blur)).save(
        os.path.join(OUT, f'disp_{name}.png'))
    k = 2 * int(erode) + 1
    sil.filter(ImageFilter.MinFilter(k)).save(
        os.path.join(OUT, f'fill_{name}.png'))
    print(f'{name}: {sil.size[0]}x{sil.size[1]}')


def text_on(im, d, xy, s, font, anchor='mm', rot=None, center=None):
    if rot is None:
        d.text(xy, s, font=font, fill=255, anchor=anchor)
        return
    tmp = Image.new('L', (300, 120), 0)
    td = ImageDraw.Draw(tmp)
    td.text((150, 60), s, font=font, fill=255, anchor='mm')
    tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=False, center=(150, 60))
    im.paste(tmp, (int(xy[0] - 150), int(xy[1] - 60)), tmp)


# ---------- bezel: 60 ticks + numerals every 5 ----------
N = 1920
C = N / 2
bez = Image.new('L', (N, N), 0)
d = ImageDraw.Draw(bez)
r_out = N * 0.492
f_num = ImageFont.truetype(FONT, int(N * 0.032))
for i in range(60):
    a = math.radians(i * 6 - 90)
    major = (i % 5 == 0)
    r1 = r_out - N * (0.006 if major else 0.004)
    r0 = r1 - N * (0.030 if major else 0.016)
    w = int(N * (0.006 if major else 0.003))
    d.line([C + r0 * math.cos(a), C + r0 * math.sin(a),
            C + r1 * math.cos(a), C + r1 * math.sin(a)], fill=255, width=w)
for i in range(0, 60, 5):
    a = math.radians(i * 6 - 90)
    rn = r_out - N * 0.058
    # numerals stay upright-readable: rotate tangentially, flip on lower half
    rot = -(i * 6) if not (90 < (i * 6) % 360 < 270) else -(i * 6) + 180
    text_on(bez, d, (C + rn * math.cos(a), C + rn * math.sin(a)),
            f'{i:02d}', f_num, rot=rot)
emit('bezel', bez, N * 0.0016, N * 0.0011)

# ---------- display labels ----------
f_lab = ImageFont.truetype(FONT, 46)
for name, s, w in [('label_hrs', 'HRS', 272), ('label_min', 'MIN', 272),
                   ('label_sec', 'SEC', 208)]:
    im = Image.new('L', (w, 64), 0)
    d = ImageDraw.Draw(im)
    d.text((w / 2, 32), s, font=f_lab, fill=255, anchor='mm')
    emit(name, im, 2.2, 1.6)

# ---------- maker's mark (arc text, plate 6 o'clock) ----------
N2 = 1920
mk = Image.new('L', (N2, N2), 0)
d = ImageDraw.Draw(mk)
f_mk = ImageFont.truetype(FONT, int(N2 * 0.020))
label = 'ARCWRIGHT · No.001'
r_mk = N2 * 0.40
arc_span = math.radians(42)
for k, ch in enumerate(label):
    t = k / (len(label) - 1) - 0.5
    a = math.pi / 2 - t * arc_span          # centered at 6 o'clock (screen)
    x, y = N2 / 2 + r_mk * math.cos(a), N2 / 2 + r_mk * math.sin(a)
    text_on(mk, d, (x, y), ch, f_mk, rot=math.degrees(a) + 270 - 360)
emit('makers', mk, N2 * 0.0013, N2 * 0.0009)

print('masks written to assets-source/masks')
