import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
"""Render digits 0-9 as equalizer-bar glyphs + colon, and a contact sheet."""
import random
from PIL import Image, ImageDraw, ImageFont

OUT = _ROOT + '/app/src/main/res/drawable-nodpi'
SHEET = '/tmp/claude-1000/-home-xsyprime-Hermes-hermes-workstation/488e9176-64d2-4e5d-9692-f5484f5fb667/scratchpad/digit_sheet.png'

W, H = 80, 104                 # digit canvas
BAR_W, GAP = 9, 2              # strip grid
GREEN = (155, 232, 33, 255)
BRIGHT = (198, 255, 74, 255)
DARK = (90, 140, 18, 255)

font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 128)
rnd = random.Random(11)

def glyph_mask(ch):
    """Render glyph tight-cropped and fitted into the canvas."""
    img = Image.new('L', (200, 200), 0)
    d = ImageDraw.Draw(img)
    d.text((20, 10), ch, font=font, fill=255)
    bbox = img.getbbox()
    g = img.crop(bbox)
    # fit to H-4 tall, keep aspect, center horizontally
    scale = (H - 4) / g.height
    g = g.resize((max(1, int(g.width * scale)), H - 4), Image.LANCZOS)
    mask = Image.new('L', (W, H), 0)
    mask.paste(g, ((W - g.width) // 2, 2))
    return mask

# VU-meter vertical gradient: red peaks -> orange -> yellow -> green base
VU_STOPS = [(0.00, (255, 64, 64)), (0.24, (255, 165, 40)),
            (0.48, (255, 232, 56)), (0.80, (155, 232, 33)), (1.00, (125, 200, 24))]

def vu_color(frac):
    for (f0, c0), (f1, c1) in zip(VU_STOPS, VU_STOPS[1:]):
        if frac <= f1:
            t = (frac - f0) / (f1 - f0)
            return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
    return VU_STOPS[-1][1]

def bars_from_mask(mask):
    """Slice the glyph into vertical bar runs per strip, VU-gradient colored."""
    px = mask.load()
    # rounded bar runs as an alpha mask, then pour the gradient through it
    shape = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(shape)
    glints = []
    x = 1
    while x + BAR_W <= W:
        runs, start = [], None
        for y in range(H):
            cov = sum(1 for xx in range(x, x + BAR_W) if px[xx, y] > 96) / BAR_W
            filled = cov > 0.38
            if filled and start is None:
                start = y
            if (not filled or y == H - 1) and start is not None:
                end = y if not filled else y + 1
                if end - start >= 7:
                    runs.append([start, end])
                start = None
        for i, (y0, y1) in enumerate(runs):
            y0 = max(0, y0 + rnd.randint(-2, 3))   # frozen-EQ jitter on run top
            d.rounded_rectangle([x, y0, x + BAR_W - 1, y1 - 1], radius=3, fill=255)
            if i == 0:
                glints.append((x, y0, min(y1 - 1, y0 + 5)))
        x += BAR_W + GAP
    grad = Image.new('RGBA', (W, H))
    gp = grad.load()
    for y in range(H):
        col = vu_color(y / (H - 1))
        for xx in range(W):
            gp[xx, y] = col + (255,)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(grad, (0, 0), shape)
    gd = ImageDraw.Draw(out)
    for x, ya, yb in glints:  # light glint on each strip's peak
        gd.rounded_rectangle([x, ya, x + BAR_W - 1, yb], radius=3, fill=(255, 255, 255, 110))
    return out

def dots_from_mask(mask, cell=8, gap=2):
    """LED dot-matrix cells, same language as the character's grin."""
    cols, rows = W // (cell + gap), H // (cell + gap)
    small = mask.resize((cols, rows), Image.BOX)
    sp = small.load()
    shape = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(shape)
    for r in range(rows):
        for c in range(cols):
            if sp[c, r] > 70:
                x0, y0 = c * (cell + gap) + 1, r * (cell + gap) + 1
                d.rounded_rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], radius=2, fill=255)
    grad = Image.new('RGBA', (W, H))
    gp = grad.load()
    for y in range(H):
        col = vu_color(y / (H - 1))
        for xx in range(W):
            gp[xx, y] = col + (255,)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(grad, (0, 0), shape)
    return out

for n in range(10):
    dots_from_mask(glyph_mask(str(n))).save(f'{OUT}/eqd{n}.png')

# Colon: two matrix cells, colored to match the gradient at their height
col = Image.new('RGBA', (18, 104), (0, 0, 0, 0))
d = ImageDraw.Draw(col)
d.rounded_rectangle([5, 32, 12, 39], radius=2, fill=vu_color(35 / 103) + (255,))
d.rounded_rectangle([5, 62, 12, 69], radius=2, fill=vu_color(65 / 103) + (255,))
col.save(f'{OUT}/eqcolon.png')

# Contact sheet for review
sheet = Image.new('RGB', (W * 10 + 90, H + 20), (10, 10, 10))
for n in range(10):
    im = Image.open(f'{OUT}/eqd{n}.png')
    sheet.paste(im, (5 + n * (W + 9), 10), im)
sheet.save(SHEET)
print('digits written')

# ---------- Mini LED digits (22x30) for HR / step readouts ----------
MW, MH, MBW, MGAP = 22, 30, 4, 1

RED, RED_CAP = (255, 45, 64, 255), (255, 128, 128, 255)      # heart rate
AMBER, AMBER_CAP = (255, 165, 40, 255), (255, 212, 112, 255)  # steps (pendant hues)

def mini_digit(ch, base=GREEN, cap=BRIGHT):
    mask = glyph_mask(ch).resize((MW, MH), Image.LANCZOS)
    px = mask.load()
    out = Image.new('RGBA', (MW, MH), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    x = 0
    while x + MBW <= MW:
        runs, start = [], None
        for y in range(MH):
            cov = sum(1 for xx in range(x, x + MBW) if px[xx, y] > 80) / MBW
            filled = cov > 0.35
            if filled and start is None:
                start = y
            if (not filled or y == MH - 1) and start is not None:
                end = y if not filled else y + 1
                if end - start >= 3:
                    runs.append([start, end])
                start = None
        for i, (y0, y1) in enumerate(runs):
            d.rounded_rectangle([x, y0, x + MBW - 1, y1 - 1], radius=1, fill=base)
            if i == 0:
                d.rounded_rectangle([x, y0, x + MBW - 1, min(y1 - 1, y0 + 3)], radius=1, fill=cap)
        x += MBW + MGAP
    return out

for n in range(10):
    mini_digit(str(n), RED, RED_CAP).save(f'{OUT}/mdr{n}.png')
    mini_digit(str(n), AMBER, AMBER_CAP).save(f'{OUT}/mda{n}.png')

# ---------- Pixel-LED icons: beating heart + footprints ----------
def cells(grid, cell=4, bright_rows=1, base=GREEN, cap=BRIGHT):
    h, w = len(grid), len(grid[0])
    im = Image.new('RGBA', (w * cell, h * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                col = cap if r < bright_rows else base
                d.rounded_rectangle([c*cell, r*cell, c*cell+cell-1, r*cell+cell-1], radius=1, fill=col)
    return im

HEART = ["0110110",
         "1111111",
         "1111111",
         "0111110",
         "0011100",
         "0001000"]
cells([[int(x) for x in row] for row in HEART], cell=4, bright_rows=2,
      base=RED, cap=RED_CAP).save(f'{OUT}/ledheart.png')

FEET = ["0110000",
        "0110011",
        "0110011",
        "0000011",
        "0110000",
        "0110011"]
cells([[int(x) for x in row] for row in FEET], cell=4, bright_rows=0,
      base=AMBER, cap=AMBER_CAP).save(f'{OUT}/ledfeet.png')

# Small shadow pads behind the readouts
from PIL import ImageFilter as _IF
pad = Image.new('RGBA', (170, 48), (0, 0, 0, 0))
pd = ImageDraw.Draw(pad)
pd.rounded_rectangle([6, 6, 164, 42], radius=18, fill=(0, 0, 0, 170))
pad = pad.filter(_IF.GaussianBlur(6))
pad.save(f'{OUT}/padsmall.png')
print('mini digits + icons written')
