#!/usr/bin/env python3
"""CHRONOVA asset generator — procedural pass 1 (PIL + numpy).

Every asset is deterministic (seeded). Regenerate with:
    python scripts/generate_assets.py
Outputs land in assets-source/<category>/ and are copied into
app/src/main/res/drawable-nodpi/.
"""
import math
import os
import random
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets-source')
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')
FONT = os.path.join(ROOT, 'app/src/main/res/font/orbitron.ttf')

rnd = random.Random(2077)

# ---------- palette ----------
STEEL = (42, 46, 54)
STEEL_D = (20, 23, 27)
STEEL_L = (96, 104, 116)
EDGE_HI = (150, 160, 175)
BRASS = (160, 122, 58)
BRASS_L = (208, 168, 96)
BLUE = (79, 195, 255)
MAGENTA = (255, 79, 216)
VIOLET = (180, 79, 255)

MANIFEST = []  # (category, filename, size, description)


def save(img, category, name, desc):
    d = os.path.join(SRC, category)
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, name))
    MANIFEST.append((category, name, f'{img.width}x{img.height}', desc))


# ---------- texture helpers ----------

def brushed(size, base, strength=10, seed=1):
    """Circular brushed-metal texture: concentric machining marks + speckle."""
    n = size
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cx = cy = (n - 1) / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    rng = np.random.default_rng(seed)
    radial_noise = rng.normal(0, 1, int(n * 0.8)).astype(np.float32)
    # smooth the per-radius noise so marks look machined, not random
    k = np.ones(5, np.float32) / 5
    radial_noise = np.convolve(radial_noise, k, mode='same')
    idx = np.clip(r.astype(np.int32), 0, len(radial_noise) - 1)
    tex = radial_noise[idx] * strength
    speck = rng.normal(0, strength * 0.25, (n, n)).astype(np.float32)
    out = np.zeros((n, n, 4), np.uint8)
    for c in range(3):
        out[..., c] = np.clip(base[c] + tex + speck, 0, 255)
    out[..., 3] = 255
    return Image.fromarray(out, 'RGBA')


def shade_disc(img, light_dir=(-1, -1), amount=26):
    """Directional top-left light falloff over a disc image."""
    n = img.width
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cx = cy = (n - 1) / 2
    dx, dy = light_dir
    grad = ((xx - cx) * dx + (yy - cy) * dy) / n
    arr = np.array(img).astype(np.float32)
    for c in range(3):
        arr[..., c] = np.clip(arr[..., c] - grad * amount * 2, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def circle_mask(size, r0=0, r1=None, ss_img=None):
    m = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(m)
    r1 = r1 if r1 is not None else size / 2
    c = size / 2
    d.ellipse([c - r1, c - r1, c + r1, c + r1], fill=255)
    if r0 > 0:
        d.ellipse([c - r0, c - r0, c + r0, c + r0], fill=0)
    return m


def screw(d, x, y, r=5, angle=None):
    """Screw head with slot."""
    d.ellipse([x - r, y - r, x + r, y + r], fill=STEEL_D, outline=EDGE_HI)
    a = angle if angle is not None else rnd.uniform(0, math.pi)
    d.line([x - r * 0.7 * math.cos(a), y - r * 0.7 * math.sin(a),
            x + r * 0.7 * math.cos(a), y + r * 0.7 * math.sin(a)],
           fill=(8, 9, 11), width=max(2, r // 3))


def glow_orb(size, color, hard=0.35):
    n = size
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    intensity = np.clip(1 - r, 0, 1) ** 2
    core = np.clip(1 - r / hard, 0, 1)
    arr = np.zeros((n, n, 4), np.uint8)
    for i in range(3):
        arr[..., i] = np.clip(color[i] * intensity + 255 * core, 0, 255)
    arr[..., 3] = np.clip(255 * intensity * 1.6, 0, 255)
    return Image.fromarray(arr, 'RGBA')


# ---------- component builders (all drawn 2x, downsampled) ----------

def gear(final_size, teeth, style='steel', spokes=5, hub=0.22, tooth_depth=0.13,
         seed=3):
    S = final_size * 2
    c = S / 2
    r_out = S * 0.5 - 2
    r_root = r_out * (1 - tooth_depth)
    body = brushed(S, {'steel': STEEL, 'dark': STEEL_D, 'brass': BRASS}[style],
                   strength=9, seed=seed)
    body = shade_disc(body)
    # tooth silhouette
    m = Image.new('L', (S, S), 0)
    md = ImageDraw.Draw(m)
    md.ellipse([c - r_root, c - r_root, c + r_root, c + r_root], fill=255)
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        half = math.pi / teeth * 0.52
        pts = []
        for aa, rr in [(a0 - half, r_root), (a0 - half * 0.45, r_out),
                       (a0 + half * 0.45, r_out), (a0 + half, r_root)]:
            pts.append((c + rr * math.cos(aa), c + rr * math.sin(aa)))
        md.polygon(pts, fill=255)
    # spoke cutouts
    if spokes:
        r_hub = r_root * (hub + 0.16)
        r_rim = r_root * 0.8
        for i in range(spokes):
            a0 = 2 * math.pi * (i + 0.5) / spokes
            spread = math.pi / spokes * 0.62
            pts = []
            for t in np.linspace(a0 - spread, a0 + spread, 8):
                pts.append((c + r_rim * math.cos(t), c + r_rim * math.sin(t)))
            for t in np.linspace(a0 + spread * 0.7, a0 - spread * 0.7, 6):
                pts.append((c + r_hub * math.cos(t), c + r_hub * math.sin(t)))
            md.polygon(pts, fill=0)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(body, (0, 0), m)
    d = ImageDraw.Draw(out)
    # rim + root ring shading
    d.ellipse([c - r_root, c - r_root, c + r_root, c + r_root],
              outline=EDGE_HI, width=2)
    d.ellipse([c - r_root * 0.82, c - r_root * 0.82, c + r_root * 0.82,
               c + r_root * 0.82], outline=(0, 0, 0, 140), width=3)
    # hub with bearing
    r_h = r_root * hub
    hue = BRASS if style != 'brass' else STEEL
    d.ellipse([c - r_h, c - r_h, c + r_h, c + r_h],
              fill={'steel': STEEL_D, 'dark': (14, 16, 19), 'brass': BRASS}[style],
              outline=EDGE_HI, width=2)
    d.ellipse([c - r_h * 0.45, c - r_h * 0.45, c + r_h * 0.45, c + r_h * 0.45],
              fill=(10, 11, 13), outline=(BRASS_L if style != 'brass' else EDGE_HI),
              width=2)
    for i in range(min(6, teeth // 3)):
        a = 2 * math.pi * i / min(6, teeth // 3) + 0.4
        screw(d, c + r_h * 0.72 * math.cos(a), c + r_h * 0.72 * math.sin(a), 5)
    return out.resize((final_size, final_size), Image.LANCZOS)


def plain_ring(final_size, width_frac=0.12, style=STEEL, marks=24, seed=5,
               segmented=False, notch_every=0):
    S = final_size * 2
    c = S / 2
    r1 = S / 2 - 2
    r0 = r1 * (1 - width_frac)
    body = shade_disc(brushed(S, style, seed=seed))
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(body, (0, 0), circle_mask(S, r0, r1))
    d = ImageDraw.Draw(out)
    d.ellipse([c - r1, c - r1, c + r1, c + r1], outline=EDGE_HI, width=2)
    d.ellipse([c - r0, c - r0, c + r0, c + r0], outline=(0, 0, 0, 160), width=2)
    rm = (r0 + r1) / 2
    if segmented:
        for i in range(marks):
            a = 2 * math.pi * i / marks
            gap = 0.35 / marks * 2 * math.pi
            d.arc([c - rm, c - rm, c + rm, c + rm],
                  math.degrees(a), math.degrees(a + gap), fill=(5, 6, 8), width=int(r1 - r0))
    else:
        for i in range(marks):
            a = 2 * math.pi * i / marks
            x0, y0 = c + r0 * math.cos(a), c + r0 * math.sin(a)
            x1, y1 = c + r1 * math.cos(a), c + r1 * math.sin(a)
            d.line([x0, y0, x1, y1], fill=(12, 13, 16), width=3)
    if notch_every:
        for i in range(0, marks, notch_every):
            a = 2 * math.pi * i / marks
            screw(d, c + rm * math.cos(a), c + rm * math.sin(a), 6, angle=a)
    return out.resize((final_size, final_size), Image.LANCZOS)


def conduit(final_w, final_h, color, label_collars=True):
    """Horizontal energy tube: casing, glass, inner strand, bloom."""
    W, H = final_w * 2, final_h * 2
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = H * 0.12
    # dark casing
    d.rounded_rectangle([2, pad, W - 2, H - pad], radius=(H - 2 * pad) / 2,
                        fill=STEEL_D, outline=EDGE_HI, width=2)
    # glass inner
    g0 = pad + H * 0.10
    d.rounded_rectangle([H * 0.18, g0, W - H * 0.18, H - g0],
                        radius=(H - 2 * g0) / 2, fill=(18, 20, 30, 255))
    # energy strand
    strand = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(strand)
    ymid = H / 2
    pts = [(H * 0.2 + t * (W - H * 0.4),
            ymid + math.sin(t * math.pi * 4 + 1.3) * H * 0.045)
           for t in np.linspace(0, 1, 40)]
    sd.line(pts, fill=color + (255,), width=int(H * 0.14), joint='curve')
    core = [(H * 0.2 + t * (W - H * 0.4),
             ymid + math.sin(t * math.pi * 4 + 1.3) * H * 0.045)
            for t in np.linspace(0, 1, 40)]
    sd.line(core, fill=(255, 255, 255, 230), width=max(2, int(H * 0.035)))
    strand = strand.filter(ImageFilter.GaussianBlur(1.5))
    bloom = strand.filter(ImageFilter.GaussianBlur(H * 0.12))
    im.alpha_composite(bloom)
    im.alpha_composite(strand)
    # collars
    if label_collars:
        for x in (H * 0.05, W - H * 0.45):
            d.rounded_rectangle([x, pad * 0.4, x + H * 0.40, H - pad * 0.4],
                                radius=6, fill=STEEL, outline=EDGE_HI, width=2)
            d.line([x + H * 0.2, pad * 0.6, x + H * 0.2, H - pad * 0.6],
                   fill=(0, 0, 0, 120), width=3)
    return im.resize((final_w, final_h), Image.LANCZOS)


def display_panel(final_w, final_h, label, accent):
    W, H = final_w * 2, final_h * 2
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # metal frame
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=H * 0.22, fill=STEEL,
                        outline=EDGE_HI, width=3)
    d.rounded_rectangle([6, 6, W - 7, H - 7], radius=H * 0.19,
                        outline=(0, 0, 0, 150), width=3)
    # dark glass window
    d.rounded_rectangle([W * 0.08, H * 0.26, W * 0.92, H * 0.92],
                        radius=H * 0.12, fill=(8, 10, 16),
                        outline=accent + (140,), width=2)
    # label plate
    f = ImageFont.truetype(FONT, int(H * 0.15))
    tw = d.textlength(label, font=f)
    d.text(((W - tw) / 2, H * 0.07), label, font=f, fill=accent + (255,))
    for (sx, sy) in [(W * 0.06, H * 0.12), (W * 0.94, H * 0.12),
                     (W * 0.06, H * 0.88), (W * 0.94, H * 0.88)]:
        screw(d, sx, sy, 7)
    # glass glint
    d.line([W * 0.14, H * 0.32, W * 0.4, H * 0.30], fill=(255, 255, 255, 40), width=4)
    return im.resize((final_w, final_h), Image.LANCZOS)


def build_ring60(size=480):
    """Mathematically correct 60-position outer scale, 60 at top."""
    S = size * 2
    c = S / 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r_out = S * 0.492
    f = ImageFont.truetype(FONT, int(S * 0.030))
    for i in range(60):
        a = math.radians(i * 6 - 90)  # position 0 (=60) at 12 o'clock
        major = i % 5 == 0
        r_in = r_out - (S * 0.028 if major else S * 0.014)
        wdt = 5 if major else 3
        col = (168, 178, 190, 255) if major else (110, 118, 128, 200)
        d.line([c + r_in * math.cos(a), c + r_in * math.sin(a),
                c + r_out * math.cos(a), c + r_out * math.sin(a)], fill=col, width=wdt)
        if major:
            lab = f'{60 if i == 0 else i:02d}'
            rt = r_out - S * 0.052
            tx, ty = c + rt * math.cos(a), c + rt * math.sin(a)
            tw = d.textlength(lab, font=f)
            d.text((tx - tw / 2, ty - S * 0.017), lab, font=f,
                   fill=(196, 205, 215, 255))
    return im.resize((size, size), Image.LANCZOS)


def side_arc(size, color, start_deg, end_deg):
    S = size * 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = S * 0.455
    c = S / 2
    d.arc([c - r, c - r, c + r, c + r], start_deg, end_deg, fill=color + (255,), width=6)
    im = im.alpha_composite if False else im
    glow = im.filter(ImageFilter.GaussianBlur(10))
    out = Image.alpha_composite(glow, im)
    return out.resize((size, size), Image.LANCZOS)


# =====================================================================
# BUILD ALL ASSETS
# =====================================================================

# 00 backing plate + rear cavity
S = 960
plate = brushed(S, (12, 13, 16), strength=6, seed=11)
plate = shade_disc(plate, amount=18)
pm = circle_mask(S)
bp = Image.new('RGBA', (S, S), (0, 0, 0, 0))
bp.paste(plate, (0, 0), pm)
d = ImageDraw.Draw(bp)
c = S / 2
# cavity rings (depth illusion)
for rr, dk in [(0.47, 90), (0.40, 60), (0.30, 40)]:
    d.ellipse([c - S * rr, c - S * rr, c + S * rr, c + S * rr],
              outline=(0, 0, 0, dk), width=int(S * 0.012))
bp = bp.filter(ImageFilter.GaussianBlur(0.6))
save(bp.resize((480, 480), Image.LANCZOS), 'chassis', 'plate_back.png',
     'void-black backing plate with cavity shading')

# 04 structural chassis: symmetric bridges + plates + XSY stamp
S = 960
ch = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(ch)
c = S / 2
body = shade_disc(brushed(S, STEEL, seed=21))


def bridge(a_deg, w_frac=0.11, r0=0.17, r1=0.44):
    """Radial structural bridge as a mask polygon."""
    a = math.radians(a_deg)
    w = S * w_frac / 2
    perp = a + math.pi / 2
    p = []
    for rr, ww in [(r0, w * 0.75), (r1, w)]:
        px, py = c + S * rr * math.cos(a), c + S * rr * math.sin(a)
        p.append((px + ww * math.cos(perp), py + ww * math.sin(perp)))
    for rr, ww in [(r1, -w), (r0, -w * 0.75)]:
        px, py = c + S * rr * math.cos(a), c + S * rr * math.sin(a)
        p.append((px + ww * math.cos(perp), py + ww * math.sin(perp)))
    return p


m = Image.new('L', (S, S), 0)
md = ImageDraw.Draw(m)
for ang in (0, 90, 180, 270, 45, 135, 225, 315):
    md.polygon(bridge(ang, 0.10 if ang % 90 else 0.13), fill=255)
# central mount ring & outer rim plate
md.ellipse([c - S * 0.235, c - S * 0.235, c + S * 0.235, c + S * 0.235], fill=255)
md.ellipse([c - S * 0.155, c - S * 0.155, c + S * 0.155, c + S * 0.155], fill=0)
md.ellipse([c - S * 0.478, c - S * 0.478, c + S * 0.478, c + S * 0.478],
           outline=255, width=int(S * 0.030))
ch.paste(body, (0, 0), m)
d = ImageDraw.Draw(ch)
# edges on bridges
for ang in (0, 90, 180, 270, 45, 135, 225, 315):
    p = bridge(ang, 0.10 if ang % 90 else 0.13)
    d.line(p + [p[0]], fill=(0, 0, 0, 170), width=3)
    a = math.radians(ang)
    for rr in (0.20, 0.30, 0.40):
        screw(d, c + S * rr * math.cos(a), c + S * rr * math.sin(a), 8, angle=a)
d.ellipse([c - S * 0.235, c - S * 0.235, c + S * 0.235, c + S * 0.235],
          outline=EDGE_HI, width=3)
d.ellipse([c - S * 0.155, c - S * 0.155, c + S * 0.155, c + S * 0.155],
          outline=(0, 0, 0, 190), width=4)
# XSY micro-stamp (easter egg, bottom-right bridge)
f = ImageFont.truetype(FONT, 16)
d.text((c + S * 0.30, c + S * 0.315), 'XSY-77', font=f, fill=(70, 76, 84, 255))
save(ch.resize((480, 480), Image.LANCZOS), 'chassis', 'chassis.png',
     'structural bridges, mount ring, screws, XSY-77 stamp')

# gears
save(gear(260, 36, 'dark', spokes=6, seed=31), 'gears', 'gear_rear_l.png',
     'large rear gear, dark steel, 36T')
save(gear(150, 24, 'dark', spokes=5, seed=32), 'gears', 'gear_rear_m.png',
     'medium rear gear, dark steel, 24T')
save(gear(110, 22, 'steel', spokes=5, seed=33), 'gears', 'gear_a.png',
     'mid gear A, steel, 22T')
save(gear(84, 16, 'steel', spokes=4, seed=34), 'gears', 'gear_b.png',
     'mid gear B, steel, 16T')
save(gear(60, 12, 'brass', spokes=3, seed=35), 'gears', 'gear_c.png',
     'small gear C, brass, 12T')
save(gear(44, 10, 'brass', spokes=0, seed=36), 'gears', 'gear_d.png',
     'tiny gear D, brass, 10T')

# eccentric cam: disc with offset bearing
cam = gear(72, 14, 'steel', spokes=0, seed=37, tooth_depth=0.10)
cd = ImageDraw.Draw(cam)
cd.ellipse([46, 30, 60, 44], fill=(10, 11, 13), outline=BRASS_L, width=2)
save(cam, 'gears', 'cam.png', 'eccentric cam, offset bearing at 60% radius')

# ratchet wheel: sawtooth
S2 = 180
rt = Image.new('RGBA', (S2, S2), (0, 0, 0, 0))
rd = ImageDraw.Draw(rt)
c2 = S2 / 2
r_o, r_i = S2 * 0.48, S2 * 0.36
pts = []
for i in range(20):
    a0 = 2 * math.pi * i / 20
    a1 = 2 * math.pi * (i + 1) / 20
    pts.append((c2 + r_o * math.cos(a0), c2 + r_o * math.sin(a0)))
    pts.append((c2 + r_i * math.cos(a1), c2 + r_i * math.sin(a1)))
rd.polygon(pts, fill=STEEL, outline=EDGE_HI)
rd.ellipse([c2 - r_i * 0.55, c2 - r_i * 0.55, c2 + r_i * 0.55, c2 + r_i * 0.55],
           fill=STEEL_D, outline=BRASS_L, width=2)
screw(rd, c2, c2, 8)
save(rt.resize((90, 90), Image.LANCZOS), 'gears', 'ratchet.png',
     'sawtooth ratchet wheel, 20 teeth, steps 1/sec')

# turbine at 12 o'clock
housing = plain_ring(130, 0.30, STEEL, marks=12, seed=41, notch_every=3)
save(housing, 'rotors', 'turbine_housing.png', '12 o-clock circular module housing')
fan = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
fd = ImageDraw.Draw(fan)
cf = 100
for i in range(7):
    a = 2 * math.pi * i / 7
    blade = [(cf + 12 * math.cos(a + 1.9), cf + 12 * math.sin(a + 1.9)),
             (cf + 88 * math.cos(a + 0.42), cf + 88 * math.sin(a + 0.42)),
             (cf + 88 * math.cos(a + 0.05), cf + 88 * math.sin(a + 0.05)),
             (cf + 12 * math.cos(a + 1.2), cf + 12 * math.sin(a + 1.2))]
    fd.polygon(blade, fill=(96, 104, 118, 255), outline=(170, 180, 195, 255))
fd.ellipse([cf - 16, cf - 16, cf + 16, cf + 16], fill=STEEL_D, outline=BRASS_L, width=2)
save(fan.resize((84, 84), Image.LANCZOS), 'rotors', 'fan.png',
     '7-blade turbine fan (rotates inside housing)')

# reactor stack
save(plain_ring(210, 0.16, STEEL, marks=16, seed=51, notch_every=4),
     'reactor', 'reactor_housing.png', 'outer containment housing, bolted')
save(plain_ring(168, 0.13, STEEL_D, marks=8, seed=52, segmented=True),
     'reactor', 'ring_outer_rot.png', 'counter-rotating containment ring (CW)')
save(plain_ring(132, 0.15, STEEL, marks=6, seed=53, segmented=True),
     'reactor', 'ring_inner_rot.png', 'inner gyroscopic ring (CCW)')

core = glow_orb(150, (120, 100, 255))
lat = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
ld = ImageDraw.Draw(lat)
cc = 75
for i in range(9):  # electrical lattice filaments, clipped inside the orb
    a0 = rnd.uniform(0, 2 * math.pi)
    a1 = a0 + rnd.uniform(1.2, 2.8)
    r0 = rnd.uniform(14, 46)
    pts = [(cc + r0 * math.cos(t) * rnd.uniform(0.9, 1.1),
            cc + r0 * math.sin(t) * rnd.uniform(0.9, 1.1))
           for t in np.linspace(a0, a1, 14)]
    ld.line(pts, fill=(210, 225, 255, 150), width=2)
lat = lat.filter(ImageFilter.GaussianBlur(0.8))
lm = circle_mask(150, 0, 52).filter(ImageFilter.GaussianBlur(6))
core.paste(Image.alpha_composite(core.crop((0, 0, 150, 150)), lat), (0, 0), lm)
save(core, 'reactor', 'core_glow.png', 'plasma core + clipped electrical lattice')
save(glow_orb(240, (90, 70, 220), hard=0.10), 'glow', 'core_bloom.png',
     'soft violet bloom behind core')

# outward pulse ring (animated via scale+fade)
pr = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
pd = ImageDraw.Draw(pr)
pd.ellipse([8, 8, 192, 192], outline=(170, 140, 255, 220), width=5)
pr = pr.filter(ImageFilter.GaussianBlur(3))
save(pr, 'glow', 'pulse_ring.png', 'expanding energy pulse ring')

# conduits (three colors) + energy packets
save(conduit(150, 46, BLUE), 'conduits', 'conduit_blue.png', 'blue energy tube')
save(conduit(150, 46, MAGENTA), 'conduits', 'conduit_magenta.png', 'magenta energy tube')
save(conduit(150, 46, VIOLET), 'conduits', 'conduit_violet.png', 'violet energy tube')
for nm, col in [('packet_blue', BLUE), ('packet_magenta', MAGENTA),
                ('packet_violet', VIOLET)]:
    save(glow_orb(30, col, hard=0.30), 'glow', f'{nm}.png', f'traveling packet {nm}')


def bolt(final_w, final_h, color, seed):
    """Jagged lightning arc sized to overlay a conduit's glass channel.

    Two seeds per color give two bolt shapes; the scene flips between them
    at ~10Hz during bursts so the arc appears to jump."""
    W, H = final_w * 2, final_h * 2
    r = random.Random(seed)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, x1 = H * 0.25, W - H * 0.25
    ymid = H / 2
    n = 16
    pts = [(x0, ymid)]
    for i in range(1, n - 1):
        x = x0 + (x1 - x0) * i / (n - 1) + r.uniform(-H * 0.04, H * 0.04)
        # alternate rough polarity so it zigzags instead of wandering
        sign = 1 if (i % 2 == 0) else -1
        pts.append((x, ymid + sign * r.uniform(H * 0.04, H * 0.20)))
    pts.append((x1, ymid))
    d.line(pts, fill=color + (255,), width=int(H * 0.040))
    # forked side branches off random elbows
    for _ in range(4):
        bx, by = pts[r.randint(2, n - 3)]
        mx = bx + r.uniform(H * 0.10, H * 0.22) * r.choice([-1, 1])
        my = by + r.uniform(H * 0.10, H * 0.20) * r.choice([-1, 1])
        ex = mx + r.uniform(H * 0.08, H * 0.18) * r.choice([-1, 1])
        ey = my + r.uniform(H * 0.08, H * 0.16) * (1 if my > by else -1)
        d.line([(bx, by), (mx, my), (ex, ey)], fill=color + (200,),
               width=max(2, int(H * 0.02)))
    glow = layer.filter(ImageFilter.GaussianBlur(H * 0.16))
    glow2 = layer.filter(ImageFilter.GaussianBlur(H * 0.05))
    core = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(core).line(pts, fill=(255, 255, 255, 255),
                              width=max(2, int(H * 0.018)))
    core = core.filter(ImageFilter.GaussianBlur(0.6))
    layer.alpha_composite(glow2)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    im.alpha_composite(glow)
    im.alpha_composite(layer)
    im.alpha_composite(core)
    return im.resize((final_w, final_h), Image.LANCZOS)


for nm, col, sa, sb in [('bolt_blue', BLUE, 4001, 4002),
                        ('bolt_magenta', MAGENTA, 4003, 4004)]:
    save(bolt(150, 46, col, sa), 'conduits', f'{nm}_a.png',
         f'lightning arc variant A ({nm})')
    save(bolt(150, 46, col, sb), 'conduits', f'{nm}_b.png',
         f'lightning arc variant B ({nm})')

# display housings
save(display_panel(136, 96, 'HOURS', BLUE), 'displays', 'display_hours.png',
     'hours housing, blue accent')
save(display_panel(136, 96, 'MINUTES', MAGENTA), 'displays', 'display_minutes.png',
     'minutes housing, magenta accent')
save(display_panel(104, 76, 'SEC', VIOLET), 'displays', 'display_sec.png',
     'seconds housing, violet accent')

# index rings around reactor: hour (12 notches) & minute (60 notches)
hr_ring = plain_ring(252, 0.055, STEEL_D, marks=12, seed=61)
hd = ImageDraw.Draw(hr_ring)
hd.ellipse([126 - 4, 4, 126 + 4, 12], fill=BLUE + (255,))  # marker at 12
save(hr_ring, 'gears', 'ring_hour.png', '12-position hour indexing ring')
mn_ring = plain_ring(286, 0.045, STEEL_D, marks=60, seed=62)
md2 = ImageDraw.Draw(mn_ring)
md2.ellipse([143 - 3, 2, 143 + 3, 8], fill=MAGENTA + (255,))
save(mn_ring, 'gears', 'ring_min.png', '60-position minute indexing ring')

# pistons
sl = Image.new('RGBA', (72, 140), (0, 0, 0, 0))
sd = ImageDraw.Draw(sl)
sd.rounded_rectangle([8, 4, 64, 100], radius=10, fill=STEEL, outline=EDGE_HI, width=2)
sd.rounded_rectangle([16, 12, 56, 92], radius=6, fill=(12, 14, 17))
for yy in (24, 48, 72):
    sd.line([16, yy, 56, yy], fill=(70, 76, 86), width=3)
save(sl.resize((36, 70), Image.LANCZOS), 'pistons', 'piston_sleeve.png',
     'piston cylinder sleeve')
rod = Image.new('RGBA', (32, 120), (0, 0, 0, 0))
rd2 = ImageDraw.Draw(rod)
rd2.rounded_rectangle([10, 0, 22, 120], radius=6, fill=(130, 138, 150),
                      outline=(40, 44, 50), width=2)
rd2.rounded_rectangle([2, 0, 30, 22], radius=6, fill=BRASS, outline=BRASS_L, width=2)
save(rod.resize((16, 60), Image.LANCZOS), 'pistons', 'piston_rod.png',
     'piston rod with brass crown')

# outer ring & side glow arcs
save(build_ring60(480), 'chassis', 'ring60.png',
     '60-position perimeter scale, exact 6-degree increments')
save(side_arc(480, BLUE, 118, 242), 'glow', 'arc_blue.png', 'left blue glow arc')
save(side_arc(480, MAGENTA, 298, 62), 'glow', 'arc_magenta.png', 'right magenta arc')

# SEC energy feed column
ec = Image.new('RGBA', (40, 120), (0, 0, 0, 0))
ed = ImageDraw.Draw(ec)
ed.line([20, 6, 20, 114], fill=VIOLET + (255,), width=6)
ec = ec.filter(ImageFilter.GaussianBlur(2))
ed = ImageDraw.Draw(ec)
ed.line([20, 6, 20, 114], fill=(255, 255, 255, 200), width=2)
save(ec.resize((20, 60), Image.LANCZOS), 'conduits', 'energy_col.png',
     'vertical energy feed into SEC display')


# ---------- foreground glass glints (parallax plane: moves the most) ----------
gl = Image.new('RGBA', (960, 960), (0, 0, 0, 0))
gd = ImageDraw.Draw(gl)
# two soft diagonal streaks upper-left, one faint arc lower-right
gd.line([(140, 330), (430, 60)], fill=(255, 255, 255, 34), width=46)
gd.line([(230, 420), (520, 150)], fill=(255, 255, 255, 20), width=26)
gd.arc([80, 80, 880, 880], 20, 80, fill=(255, 255, 255, 26), width=18)
gl = gl.filter(ImageFilter.GaussianBlur(22))
save(gl.resize((480, 480), Image.LANCZOS), 'glow', 'glints.png',
     'foreground glass reflections (fastest parallax plane)')

# copy everything into res/drawable-nodpi
os.makedirs(RES, exist_ok=True)
count = 0
for cat, name, dim, desc in MANIFEST:
    shutil.copy(os.path.join(SRC, cat, name), os.path.join(RES, name))
    count += 1

with open(os.path.join(ROOT, 'docs', 'ASSET_MAP.md'), 'w') as fh:
    fh.write('# CHRONOVA asset map (procedural pass 1)\n\n')
    fh.write('| Category | File | Size | Description |\n|---|---|---|---|\n')
    for cat, name, dim, desc in MANIFEST:
        fh.write(f'| {cat} | `{name}` | {dim} | {desc} |\n')
    fh.write('\nAll assets generated by `scripts/generate_assets.py` (seed 2077).\n')
    fh.write('Pivot/z-order/motion columns live in `docs/ANIMATION_MAP.md`.\n')
    fh.write('''
## Photoreal overrides (Blender 4.5.11, Cycles CPU)

These files are OVERWRITTEN by `scripts/render_blender_layers.py` after the
PIL pass (run order matters): plate_back, chassis, gear_rear_l, gear_rear_m,
gear_a, gear_b, gear_c, gear_d, ratchet, cam, fan, turbine_housing,
reactor_housing, ring_outer_rot, ring_inner_rot, piston_sleeve, piston_rod.
Emissive sprites (blooms, packets, arcs, conduits, energy column), display
panels (text), and ring60 remain PIL-procedural by design.

## WebP sequences (FFmpeg, `scripts/build_webp_sequences.py`)

| File | Size | Frames | Description |
|---|---|---|---|
| `surge.webp` | 240x240 | 18 @ 12fps | reactor tap surge |
| `ignite.webp` | 240x240 | 18 @ 12fps | startup ignition |
''')

print(f'{count} assets generated and copied to res/drawable-nodpi')
print('REMINDER: re-run render_blender_layers.py — this pass overwrote its outputs')
