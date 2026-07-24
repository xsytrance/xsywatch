"""Render candidate digit styles through the VU pipeline into one comparison sheet."""
import random
from PIL import Image, ImageDraw, ImageFont

S = '/tmp/claude-1000/-home-xsyprime-Hermes-hermes-workstation/488e9176-64d2-4e5d-9692-f5484f5fb667/scratchpad'
W, H = 80, 104
BAR_W, GAP = 9, 2

VU_STOPS = [(0.00, (255, 64, 64)), (0.24, (255, 165, 40)),
            (0.48, (255, 232, 56)), (0.80, (155, 232, 33)), (1.00, (125, 200, 24))]

def vu_color(frac):
    for (f0, c0), (f1, c1) in zip(VU_STOPS, VU_STOPS[1:]):
        if frac <= f1:
            t = (frac - f0) / (f1 - f0)
            return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
    return VU_STOPS[-1][1]

def glyph_mask(ch, fontpath, size=128):
    font = ImageFont.truetype(fontpath, size)
    img = Image.new('L', (300, 300), 0)
    ImageDraw.Draw(img).text((30, 30), ch, font=font, fill=255)
    bbox = img.getbbox()
    g = img.crop(bbox)
    scale = (H - 4) / g.height
    g = g.resize((max(1, min(W - 2, int(g.width * scale))), H - 4), Image.LANCZOS)
    mask = Image.new('L', (W, H), 0)
    mask.paste(g, ((W - g.width) // 2, 2))
    return mask

def gradient_through(shape, glints=()):
    grad = Image.new('RGBA', (W, H))
    gp = grad.load()
    for y in range(H):
        col = vu_color(y / (H - 1))
        for xx in range(W):
            gp[xx, y] = col + (255,)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(grad, (0, 0), shape)
    gd = ImageDraw.Draw(out)
    for x0, ya, yb, x1 in glints:
        gd.rounded_rectangle([x0, ya, x1, yb], radius=3, fill=(255, 255, 255, 110))
    return out

def style_bars(ch, fontpath, seed=11):
    rnd = random.Random(seed + ord(ch))
    px = glyph_mask(ch, fontpath).load()
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
            y0 = max(0, y0 + rnd.randint(-2, 3))
            d.rounded_rectangle([x, y0, x + BAR_W - 1, y1 - 1], radius=3, fill=255)
            if i == 0:
                glints.append((x, y0, min(y1 - 1, y0 + 5), x + BAR_W - 1))
        x += BAR_W + GAP
    return gradient_through(shape, glints)

def style_dots(ch, fontpath, cell=8, gap=2):
    """LED dot-matrix, like the character's grin."""
    mask = glyph_mask(ch, fontpath)
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
    return gradient_through(shape)

SEG_MAP = {  # classic 7-segment: a b c d e f g
    '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc',
    '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcfgd'}

def style_7seg(ch):
    t = 12  # segment thickness
    L, R, TOP, MID, BOT = 8, W - 8, 4, H // 2, H - 4
    segs = {
        'a': [L + 4, TOP, R - 4, TOP + t],
        'b': [R - t, TOP + 4, R, MID - 2],
        'c': [R - t, MID + 2, R, BOT - 4],
        'd': [L + 4, BOT - t, R - 4, BOT],
        'e': [L, MID + 2, L + t, BOT - 4],
        'f': [L, TOP + 4, L + t, MID - 2],
        'g': [L + 4, MID - t // 2, R - 4, MID + t // 2],
    }
    shape = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(shape)
    for s in SEG_MAP[ch]:
        d.rounded_rectangle(segs[s], radius=5, fill=255)
    return gradient_through(shape)

STYLES = [
    ('1. CURRENT   (DejaVu bars)',      lambda c: style_bars(c, '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    ('2. ORBITRON  (techno bars)',      lambda c: style_bars(c, f'{S}/fonts/orbitron.ttf')),
    ('3. AUDIOWIDE (speaker-grille bars)', lambda c: style_bars(c, f'{S}/fonts/audiowide.ttf')),
    ('4. BUNGEE    (heavy street bars)', lambda c: style_bars(c, f'{S}/fonts/bungee.ttf')),
    ('5. RUBIK MONO (blocky bars)',     lambda c: style_bars(c, f'{S}/fonts/rubikmono.ttf')),
    ('6. DOT MATRIX (grin-style LED)',  lambda c: style_dots(c, '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    ('7. PIXEL ARCADE (Press Start dots)', lambda c: style_dots(c, f'{S}/fonts/pressstart.ttf', cell=9, gap=2)),
    ('8. SEVEN-SEG (retro digital)',    style_7seg),
]

DIGITS = '0123456789'
label_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 22)
row_h = H + 46
sheet = Image.new('RGB', (10 * (W + 6) + 30, row_h * len(STYLES) + 16), (12, 12, 12))
sd = ImageDraw.Draw(sheet)
for r, (label, fn) in enumerate(STYLES):
    y = 8 + r * row_h
    sd.text((16, y), label, font=label_font, fill=(230, 230, 230))
    for i, ch in enumerate(DIGITS):
        im = fn(ch)
        sheet.paste(im, (16 + i * (W + 6), y + 32), im)
sheet.save(f'{S}/font_tasting.png')
print('sheet saved')
