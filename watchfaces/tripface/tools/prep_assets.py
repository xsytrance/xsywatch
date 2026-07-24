import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
"""Prepare watchface assets from the xsytrance artwork."""
import math
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

SRC = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'xsytrance_character.jpg')  # donor preserved in-repo (was a session-upload path)
OUT = _ROOT + '/app/src/main/res/drawable-nodpi'
SIZE = 480

im = Image.open(SRC).convert('RGB')
W, H = im.size  # 960 x 1208

# --- Background: square crop centered on the character's head/torso ---
# Head sits around (435, 300); include some graffiti above and the necklace below.
side = 660
cx, cy = 460, 420
box = (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)
bg = im.crop(box).resize((SIZE, SIZE), Image.LANCZOS)

# Punch up color a touch, then darken so the green clock pops
bg = ImageEnhance.Color(bg).enhance(1.15)
bg = ImageEnhance.Brightness(bg).enhance(0.82)
bg = ImageEnhance.Contrast(bg).enhance(1.08)

# Radial vignette: darker toward the rim (helps on round AMOLED)
vig = Image.new('L', (SIZE, SIZE), 0)
d = ImageDraw.Draw(vig)
for r in range(SIZE // 2, 0, -1):
    # 1.0 at center -> ~0.35 at rim
    t = r / (SIZE / 2)
    val = int(255 * (1.0 - 0.65 * (t ** 2.2)))
    d.ellipse([SIZE/2 - r, SIZE/2 - r, SIZE/2 + r, SIZE/2 + r], fill=val)
vig = vig.filter(ImageFilter.GaussianBlur(6))
black = Image.new('RGB', (SIZE, SIZE), (0, 0, 0))
bg = Image.composite(bg, black, vig)
bg.save(f'{OUT}/bg.png')

# --- Rotating psychedelic ring: segmented arcs in acid greens ---
GREENS = [(155, 232, 33), (198, 255, 74), (90, 140, 18), (155, 232, 33)]
ring = Image.new('RGBA', (SIZE * 2, SIZE * 2), (0, 0, 0, 0))  # 2x for AA
rd = ImageDraw.Draw(ring)
C = SIZE  # center in 2x space

# Outer segmented ring
import random
rnd = random.Random(42)
a = 0.0
i = 0
while a < 360:
    seg = rnd.uniform(8, 42)
    gap = rnd.uniform(4, 14)
    col = GREENS[i % len(GREENS)]
    alpha = rnd.choice([255, 200, 140])
    wdt = rnd.choice([10, 10, 16])
    r = 452  # radius in 2x space -> 226 at 1x
    rd.arc([C - r, C - r, C + r, C + r], start=a, end=a + seg,
           fill=col + (alpha,), width=wdt)
    a += seg + gap
    i += 1

# Inner thin dashed ring, offset rhythm
a = 5.0
while a < 365:
    r = 414
    rd.arc([C - r, C - r, C + r, C + r], start=a, end=a + 6,
           fill=(155, 232, 33, 110), width=4)
    a += 18

# Target ticks (like the crosshair motifs in the art)
for ang in range(0, 360, 30):
    x1 = C + 396 * math.cos(math.radians(ang))
    y1 = C + 396 * math.sin(math.radians(ang))
    x2 = C + 430 * math.cos(math.radians(ang))
    y2 = C + 430 * math.sin(math.radians(ang))
    rd.line([x1, y1, x2, y2], fill=(198, 255, 74, 90), width=4)

ring = ring.resize((SIZE, SIZE), Image.LANCZOS)
ring.save(f'{OUT}/ring.png')

# Placeholder preview (replaced with a real screenshot later)
prev = bg.copy().resize((400, 400), Image.LANCZOS)
prev.save(_ROOT + '/app/src/main/res/drawable/preview.png')
print('assets written')
