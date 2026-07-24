import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
"""X1c7 BUSHIDO — background layer generation (samurai neon cityscape)."""
import math, random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops

SRC = _os.path.join(_os.path.dirname(_os.path.dirname(_ROOT)), 'releases', 'bushido', 'current', 'preview.jpg')  # concept art = release preview
OUT = _ROOT + '/app/src/main/res/drawable-nodpi'
S = 480
rnd = random.Random(7)

src = Image.open(SRC).convert('RGB')

# ---- Full watch-screen scene crop (samurai centred) ----
# Screen circle in source ~ center (398,543) r~300. Crop a touch wider for parallax.
CX, CY, R = 398, 543, 312
box = (CX - R, CY - R, CX + R, CY + R)
scene = src.crop(box).resize((S, S), Image.LANCZOS)

# Neon pop, then darken so UI reads on top
scene = ImageEnhance.Color(scene).enhance(1.28)
scene = ImageEnhance.Contrast(scene).enhance(1.10)
scene = ImageEnhance.Brightness(scene).enhance(0.62)

# Cool cyber grade: lift blues, trim warm midtones a touch
r, g, b = scene.split()
b = b.point(lambda v: min(255, int(v * 1.10 + 6)))
r = r.point(lambda v: int(v * 0.98))
scene = Image.merge('RGB', (r, g, b))

px = scene.load()

# ---- Kill the baked mock-up UI: an intentional HUD darkening ----
# 1) Top gradient panel (hides baked "10:08" + top bar), fades out by mid-screen.
top = Image.new('L', (S, S), 0)
td = ImageDraw.Draw(top)
for y in range(S):
    t = y / (S * 0.52)                # fully dark at top, gone ~55%
    a = int(205 * max(0.0, 1.0 - t) ** 1.35)
    td.line([(0, y), (S, y)], fill=a)
top = top.filter(ImageFilter.GaussianBlur(8))
scene = Image.composite(Image.new('RGB', (S, S), (2, 5, 10)), scene, top)

# 2) Bottom gradient (grounds the stats + distance), fades up from bottom.
bot = Image.new('L', (S, S), 0)
bd = ImageDraw.Draw(bot)
for y in range(S):
    t = (S - y) / (S * 0.34)
    a = int(190 * max(0.0, 1.0 - t) ** 1.4)
    bd.line([(0, y), (S, y)], fill=a)
bot = bot.filter(ImageFilter.GaussianBlur(8))
scene = Image.composite(Image.new('RGB', (S, S), (3, 4, 9)), scene, bot)

# ---- Enhanced moon / energy halo behind the samurai ----
halo = Image.new('RGBA', (S, S), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
mcx, mcy = 240, 250
for rr in range(150, 0, -1):
    t = rr / 150.0
    a = int(70 * (1 - t) ** 2.2)
    col = (120, 225, 255, a)
    hd.ellipse([mcx - rr, mcy - rr, mcx + rr, mcy + rr], fill=col)
halo = halo.filter(ImageFilter.GaussianBlur(10))
scene = Image.alpha_composite(scene.convert('RGBA'), halo).convert('RGB')

# ---- Central HUD panels: blur + darken the baked mock-up text bands ----
# The big clock band and the X1c7 label band sit dead-centre (vignette can't
# reach them); blur them into soft glow so nothing of the mock-up reads through.
def darken_band(img, y0, y1, x0, x1, blur, dark):
    reg = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    reg = ImageEnhance.Brightness(reg).enhance(dark)
    m = Image.new('L', (x1 - x0, y1 - y0), 0)
    md = ImageDraw.Draw(m)
    md.rectangle([0, 0, x1 - x0, y1 - y0], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(18))
    img.paste(reg, (x0, y0), m)
    return img

scene = darken_band(scene, 80, 190, 60, 430, 12, 0.5)    # big clock band
scene = darken_band(scene, 185, 262, 150, 340, 9, 0.55)  # X1c7 / kanji band
scene = darken_band(scene, 26, 118, 88, 432, 9, 0.5)     # top bar (SAT/date/wx)
scene = darken_band(scene, 348, 408, 38, 158, 8, 0.6)    # steps stat
scene = darken_band(scene, 348, 408, 322, 442, 8, 0.6)   # cal stat
scene = darken_band(scene, 414, 468, 170, 310, 8, 0.6)   # distance

# ---- Radial vignette: neon rim darkening for the round AMOLED ----
vig = Image.new('L', (S, S), 0)
vd = ImageDraw.Draw(vig)
for rr in range(S // 2, 0, -1):
    t = rr / (S / 2)
    val = int(255 * (1.0 - 0.86 * (t ** 2.0)))
    vd.ellipse([S/2 - rr, S/2 - rr, S/2 + rr, S/2 + rr], fill=val)
vig = vig.filter(ImageFilter.GaussianBlur(6))
scene = Image.composite(scene, Image.new('RGB', (S, S), (0, 0, 0)), vig)

# Faint magenta bloom drifting up from the bottom city (atmosphere)
bloom = Image.new('RGBA', (S, S), (0, 0, 0, 0))
bl = ImageDraw.Draw(bloom)
bl.ellipse([-40, 360, 220, 560], fill=(255, 40, 130, 26))
bl.ellipse([300, 360, 540, 560], fill=(60, 120, 255, 22))
bloom = bloom.filter(ImageFilter.GaussianBlur(40))
scene = Image.alpha_composite(scene.convert('RGBA'), bloom).convert('RGB')

scene.convert('RGB').save(f'{OUT}/bg.png')

# ---- AMBIENT (AOD) background: near-black, only a ghost of the samurai ----
aod = ImageEnhance.Brightness(scene).enhance(0.16)
aod = ImageEnhance.Color(aod).enhance(0.35)
aod = Image.composite(aod, Image.new('RGB', (S, S), (0, 0, 0)), vig.point(lambda v: int(v*0.8)))
aod.save(f'{OUT}/bg_aod.png')

# ---- Rain layer: seamless vertically over 480, tile height 480 (image 480x960) ----
RH = 960
rain = Image.new('RGBA', (S, RH), (0, 0, 0, 0))
rdw = ImageDraw.Draw(rain)
for _ in range(260):
    x = rnd.uniform(0, S)
    y = rnd.uniform(0, 480)              # place in top half then mirror for seamless
    ln = rnd.uniform(10, 26)
    a = rnd.randint(18, 60)
    slant = rnd.uniform(-1.2, -0.4)
    col = (200, 225, 255, a)
    rdw.line([(x, y), (x + slant * ln * 0.3, y + ln)], fill=col, width=1)
    rdw.line([(x, y + 480), (x + slant * ln * 0.3, y + 480 + ln)], fill=col, width=1)
rain = rain.filter(ImageFilter.GaussianBlur(0.4))
rain.save(f'{OUT}/rain.png')

# ---- Drifting fog band (behind samurai mid-city) ----
fog = Image.new('RGBA', (620, 220), (0, 0, 0, 0))
fd = ImageDraw.Draw(fog)
for _ in range(50):
    x = rnd.uniform(0, 620); y = rnd.uniform(40, 180)
    rr = rnd.uniform(30, 90); a = rnd.randint(6, 16)
    fd.ellipse([x-rr, y-rr*0.5, x+rr, y+rr*0.5], fill=(150, 180, 210, a))
fog = fog.filter(ImageFilter.GaussianBlur(24))
fog.save(f'{OUT}/fog.png')

# ---- Breathing moon glow (additive, pulsed in WFF) ----
mg = Image.new('RGBA', (300, 300), (0, 0, 0, 0))
mgd = ImageDraw.Draw(mg)
for rr in range(150, 0, -1):
    t = rr/150.0; a = int(90*(1-t)**2.4)
    mgd.ellipse([150-rr,150-rr,150+rr,150+rr], fill=(140,235,255,a))
mg = mg.filter(ImageFilter.GaussianBlur(12))
mg.save(f'{OUT}/moonglow.png')

# ---- Scanlines + faint tech grid overlay (static, low alpha) ----
scan = Image.new('RGBA', (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(scan)
for y in range(0, S, 3):
    sd.line([(0, y), (S, y)], fill=(0, 0, 0, 26), width=1)
scan.save(f'{OUT}/scan.png')

print('background assets written:', 'bg, bg_aod, rain, fog, moonglow, scan')
