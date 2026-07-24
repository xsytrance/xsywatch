import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
"""Mock 3 abstract 'time as music gear' concepts over the real face background."""
from PIL import Image, ImageDraw, ImageFont

S = '/tmp/claude-1000/-home-xsyprime-Hermes-hermes-workstation/488e9176-64d2-4e5d-9692-f5484f5fb667/scratchpad'
RES = _ROOT + '/app/src/main/res/drawable-nodpi'
TIME = [1, 0, 3, 8]  # mock 10:38

VU_STOPS = [(0.00, (255, 64, 64)), (0.24, (255, 165, 40)),
            (0.48, (255, 232, 56)), (0.80, (155, 232, 33)), (1.00, (125, 200, 24))]

def vu_color(frac):
    for (f0, c0), (f1, c1) in zip(VU_STOPS, VU_STOPS[1:]):
        if frac <= f1:
            t = (frac - f0) / (f1 - f0)
            return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
    return VU_STOPS[-1][1]

def base_face(dim=0.55):
    bg = Image.open(f'{RES}/bg.png').convert('RGB').resize((480, 480))
    bg = Image.eval(bg, lambda v: int(v * dim))
    ring = Image.open(f'{RES}/ring.png').convert('RGBA').resize((480, 480))
    bg = bg.convert('RGBA')
    bg.alpha_composite(Image.eval(ring, lambda v: v // 2))
    return bg

def crop_circle(im):
    m = Image.new('L', (480, 480), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 480, 480], fill=255)
    out = Image.new('RGB', (480, 480), (0, 0, 0))
    out.paste(im.convert('RGB'), (0, 0), m)
    return out

lf = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 15)

# ---- Concept A: 808 step-sequencer grid --------------------------------
def mock_sequencer():
    im = base_face()
    d = ImageDraw.Draw(im, 'RGBA')
    pw, ph, gx, gy = 26, 22, 4, 8
    x0 = (480 - (10 * (pw + gx) - gx)) // 2
    y0 = 244
    for row, val in enumerate(TIME):
        y = y0 + row * (ph + gy)
        for colm in range(10):
            x = x0 + colm * (pw + gx)
            if colm == val:
                c = vu_color(1 - colm / 9)
                d.rounded_rectangle([x, y, x + pw, y + ph], radius=5, fill=c + (255,))
                d.rounded_rectangle([x + 3, y + 3, x + pw - 3, y + 8], radius=3,
                                    fill=(255, 255, 255, 120))
            else:
                d.rounded_rectangle([x, y, x + pw, y + ph], radius=5,
                                    fill=(10, 24, 4, 170), outline=(155, 232, 33, 90))
        lab = ['H', 'h', 'M', 'm'][row]
        d.text((x0 - 22, y + 3), lab, font=lf, fill=(155, 232, 33, 200))
    # playhead sweeping column (animated on-watch, one col/second)
    px = x0 + 6 * (pw + gx)
    d.rectangle([px - 2, y0 - 10, px + pw + 2, y0 + 4 * (ph + gy) - gy + 10],
                fill=(198, 255, 74, 36))
    return crop_circle(im)

# ---- Concept B: mixer channel faders -----------------------------------
def mock_faders():
    im = base_face()
    d = ImageDraw.Draw(im, 'RGBA')
    xs = [138, 206, 274, 342]
    ty0, ty1 = 214, 408   # track
    for i, (x, val) in enumerate(zip(xs, TIME)):
        d.rounded_rectangle([x - 4, ty0, x + 4, ty1], radius=4, fill=(8, 18, 3, 200),
                            outline=(155, 232, 33, 110))
        for v in range(10):
            yy = ty1 - v * (ty1 - ty0) / 9
            d.line([x - 12, yy, x - 7, yy], fill=(155, 232, 33, 140), width=2)
        yy = ty1 - val * (ty1 - ty0) / 9
        c = vu_color(1 - val / 9)
        # fader cap
        d.rounded_rectangle([x - 20, yy - 9, x + 20, yy + 9], radius=6, fill=c + (255,))
        d.line([x - 20, yy, x + 20, yy], fill=(0, 0, 0, 200), width=3)
        d.text((x - 5, ty1 + 8), ['H', 'h', 'M', 'm'][i], font=lf, fill=(155, 232, 33, 220))
    return crop_circle(im)

# ---- Concept C: VU needle meters ----------------------------------------
import math
def mock_vu_needles():
    im = base_face()
    d = ImageDraw.Draw(im, 'RGBA')
    boxes = [(72, 240), (176, 240), (280, 240), (72, 330), (176, 330)]  # 4 used
    positions = [(70, 236), (250, 236), (70, 330), (250, 330)]
    for (bx, by), val, lab in zip(positions, TIME, ['H', 'h', 'M', 'm']):
        w, h = 160, 84
        d.rounded_rectangle([bx, by, bx + w, by + h], radius=10, fill=(6, 14, 2, 210),
                            outline=(155, 232, 33, 130), width=2)
        cx, cy, r = bx + w / 2, by + h - 12, 62
        for v in range(10):
            a = math.pi + (v / 9) * math.pi  # sweep left->right
            x1 = cx + (r - 8) * math.cos(a); y1 = cy + (r - 8) * math.sin(a)
            x2 = cx + r * math.cos(a);       y2 = cy + r * math.sin(a)
            d.line([x1, y1, x2, y2], fill=vu_color(1 - v / 9) + (230,), width=3)
        a = math.pi + (val / 9) * math.pi
        d.line([cx, cy, cx + (r - 12) * math.cos(a), cy + (r - 12) * math.sin(a)],
               fill=(255, 255, 255, 240), width=4)
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(198, 255, 74, 255))
        d.text((bx + 8, by + 6), lab, font=lf, fill=(155, 232, 33, 220))
    return crop_circle(im)

mock_sequencer().save(f'{S}/concept_sequencer.png')
mock_faders().save(f'{S}/concept_faders.png')
mock_vu_needles().save(f'{S}/concept_vu.png')

# side-by-side sheet
sheet = Image.new('RGB', (3 * 500 + 20, 540), (12, 12, 12))
sd = ImageDraw.Draw(sheet)
bf = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 24)
for i, (name, f) in enumerate([('A. 808 SEQUENCER', 'concept_sequencer'),
                               ('B. MIXER FADERS', 'concept_faders'),
                               ('C. VU NEEDLES', 'concept_vu')]):
    sheet.paste(Image.open(f'{S}/{f}.png'), (15 + i * 500, 46))
    sd.text((20 + i * 500, 10), name + '  (10:38)', font=bf, fill=(235, 235, 235))
sheet.save(f'{S}/concepts_sheet.png')
print('concepts saved')
