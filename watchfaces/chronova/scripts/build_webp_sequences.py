#!/usr/bin/env python3
"""CHRONOVA frame-sequence effects -> animated WebP (12fps, localized, alpha).

Two sequences, both invisible when idle (AnimationController HIDE before/after):
  surge.webp  — reactor tap surge (TAP trigger), ~1.5s, 240x240 over the core
  ignite.webp — startup ignition (ON_VISIBLE trigger), ~1.5s, same region

Frames are PIL-procedural; encoding via ffmpeg libwebp (yuva420p keeps alpha).
"""
import math
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')
SRCDIR = os.path.join(ROOT, 'assets-source', 'glow')

SIZE = 240
C = SIZE / 2
N = 18       # frames
FPS = 12

BLUE = (79, 195, 255)
MAGENTA = (255, 79, 216)
VIOLET = (180, 79, 255)
WHITE = (240, 240, 255)


def orb(d, r, color, alpha):
    if r <= 0 or alpha <= 0:
        return
    d.ellipse([C - r, C - r, C + r, C + r], fill=color + (int(alpha),))


def surge_frame(i):
    """Rings contract -> core contracts -> 6 spokes fire -> bloom -> fade."""
    t = i / (N - 1)
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # contracting containment rings (t 0..0.45)
    if t < 0.5:
        k = t / 0.5
        for base_r, w in ((104, 5), (86, 3)):
            r = base_r - 22 * k
            a = int(200 * (1 - 0.3 * k))
            d.ellipse([C - r, C - r, C + r, C + r], outline=VIOLET + (a,), width=w)
    # core contraction then release
    if t < 0.45:
        orb(d, 34 - 20 * (t / 0.45), WHITE, 230)
    else:
        k = (t - 0.45) / 0.55
        orb(d, 14 + 88 * k, VIOLET, 190 * (1 - k))
        orb(d, 10 + 40 * k, WHITE, 240 * (1 - k))
    # six principal spokes (t 0.4..0.9), alternating side colors
    if 0.4 < t < 0.95:
        k = (t - 0.4) / 0.55
        for j in range(6):
            a = math.radians(j * 60)
            col = BLUE if math.cos(a) < 0 else MAGENTA
            r0 = 18 + 70 * k
            r1 = r0 + 34
            fade = int(230 * (1 - k))
            d.line([C + r0 * math.cos(a), C + r0 * math.sin(a),
                    C + min(r1, C - 4) * math.cos(a), C + min(r1, C - 4) * math.sin(a)],
                   fill=col + (fade,), width=7)
    im = im.filter(ImageFilter.GaussianBlur(2.2))
    # global fade-out tail
    if t > 0.85:
        im.putalpha(im.getchannel('A').point(lambda v: int(v * (1 - (t - 0.85) / 0.15))))
    return im


def ignite_frame(i):
    """Rim ring wakes -> inner ring -> core flash -> settle (reveals live core)."""
    t = i / (N - 1)
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # outer ring sweep-in (t 0..0.4): arc grows clockwise
    if t < 0.55:
        sweep = min(1, t / 0.4)
        a = int(220 * min(1, (0.55 - t) / 0.15 if t > 0.4 else 1))
        d.arc([C - 100, C - 100, C + 100, C + 100], -90, -90 + 360 * sweep,
              fill=VIOLET + (a,), width=5)
    # inner ring (t 0.2..0.6)
    if 0.2 < t < 0.7:
        k = min(1, (t - 0.2) / 0.3)
        a = int(190 * (1 if t < 0.55 else (0.7 - t) / 0.15))
        d.arc([C - 68, C - 68, C + 68, C + 68], 90, 90 + 360 * k,
              fill=BLUE + (max(0, a),), width=4)
    # core ignition flash (t 0.45..1): overshoot then settle
    if t > 0.45:
        k = (t - 0.45) / 0.55
        burst = math.sin(min(1, k * 1.4) * math.pi)  # up then down
        orb(d, 20 + 46 * burst, VIOLET, 170 * burst)
        orb(d, 12 + 22 * burst, WHITE, 220 * burst)
    im = im.filter(ImageFilter.GaussianBlur(2.0))
    if t > 0.9:
        im.putalpha(im.getchannel('A').point(lambda v: int(v * (1 - (t - 0.9) / 0.1))))
    return im


def encode(name, frame_fn):
    with tempfile.TemporaryDirectory() as td:
        for i in range(N):
            frame_fn(i).save(f'{td}/f{i:02d}.png')
        out = os.path.join(RES, f'{name}.webp')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS),
                        '-i', f'{td}/f%02d.png', '-c:v', 'libwebp', '-lossless', '0',
                        '-q:v', '82', '-pix_fmt', 'yuva420p', '-loop', '1', out],
                       check=True)
        os.makedirs(SRCDIR, exist_ok=True)
        subprocess.run(['cp', out, os.path.join(SRCDIR, f'{name}.webp')], check=True)
        print(f'{name}.webp: {os.path.getsize(out)//1024} KB, {N} frames @ {FPS}fps')


encode('surge', surge_frame)
encode('ignite', ignite_frame)
