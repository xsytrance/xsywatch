#!/usr/bin/env python3
"""XSY PULSE — cyberpunk heart-monitor Watch Face Format v4 builder.
Target: Samsung Galaxy Watch 7 44mm (Wear OS 6 / One UI 8), canvas 480x480.

One file so layout can never drift between assets, watchface.xml and the
faithful preview compositor. Stages (argv): bg | glyphs | xml | preview | all
"""
import sys, os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
RES  = f'{ROOT}/app/src/main/res'
NODPI= f'{RES}/drawable-nodpi'
DRAW = f'{RES}/drawable'
SCRATCH = '/tmp/claude-1000/-home-xsyprime-hermes360/69cb56ba-1a43-493d-974e-399afca379a3/scratchpad'
S, C = 480, 240
os.makedirs(NODPI, exist_ok=True); os.makedirs(DRAW, exist_ok=True)

# ---------------------------------------------------------------- palette ----
INK      = (7, 7, 13)        # #07070D near-black
CYAN     = (0, 229, 255)     # #00E5FF
MAGENTA  = (255, 45, 149)    # #FF2D95
VIOLET   = (167, 139, 250)   # #A78BFA
RED      = (255, 59, 78)     # #FF3B4E
ICE      = (234, 251, 255)   # #EAFBFF  white-cyan core
PINK     = (255, 232, 241)   # #FFE8F1  white-pink core

FONT_ORB = f'{ROOT}/tools/fonts/orbitron.ttf'

# ---------------------------------------------------------------- layout -----
L = {
    'brand':    (240, 36),    # XSY PULSE micro-brand
    'date':     (240, 62),    # WED 23
    'time':     (240, 112),   # hh:mm  (box 240x66, size 48)
    'secs':     (362, 126),   # ss     (box 56x44,  size 22)
    'hr':       (240, 222),   # HUGE bpm number (box 300x124, size 100)
    'heart':    (168, 290),   # beating heart icon
    'bpm_lbl':  (210, 290),   # BPM label
    'pmax_val': (288, 290),   # % of age-max HR (owner ~42 -> max 178)
    'pmax_lbl': (344, 291),   # %MAX label
    'zone':     (240, 306),   # HR zone word plate (REST/CALM/ACTIVE/PUSH/MAX)
    'ecg_cy':   348,          # ECG strip band center (img 960x72)
    'shoe':     (104, 404),
    'steps':    (168, 404),
    'bolt':     (376, 404),
    'batt':     (312, 404),
    'comp':     (240, 417),   # complication slot center (120x44)
}
ARC = dict(r=222, th=6, a0=225.0, span=270.0)     # HR ring 40..200 bpm, gap at 6h
ECG_W, ECG_H, ECG_PERIOD, ECG_SPEED = 960, 72, 240, 130

AMBER  = (255, 184, 74)
MAXHR  = 178                                       # owner age ~42 -> 220-42
BASELINE = (58, 108)                               # owner's documented resting range
ZONES = [                                          # (lo, hi, word, color)
    (40,  65,  'REST',   CYAN),
    (65,  95,  'CALM',   VIOLET),
    (95,  135, 'ACTIVE', AMBER),
    (135, 165, 'PUSH',   MAGENTA),
    (165, 200, 'MAX',    RED),
]
def bpm_angle(bpm):
    return ARC['a0'] + ARC['span'] * (max(40, min(200, bpm)) - 40) / 160

# ------------------------------------------------------------- helpers -------
def _ss_draw(w, h, fn, ss=4):
    im = Image.new('RGBA', (w*ss, h*ss), (0, 0, 0, 0))
    fn(ImageDraw.Draw(im), ss)
    return im.resize((w, h), Image.LANCZOS)

def neon(im, color, grow=2, blur=5, gain=0.9):
    """Outer neon glow around the opaque pixels of an RGBA image."""
    a = im.split()[3]
    glow = Image.new('RGBA', im.size, color + (0,))
    ga = a.filter(ImageFilter.MaxFilter(2*grow + 1)).filter(ImageFilter.GaussianBlur(blur))
    glow.putalpha(ga.point(lambda v: int(v * gain)))
    return Image.alpha_composite(glow, im)

def radial_mask(size, r0, r1, lo=0, hi=255):
    """L mask: value hi inside r0, fades to lo at r1."""
    m = Image.new('L', (size, size), lo)
    d = ImageDraw.Draw(m)
    cx = size / 2
    for r in range(int(r1), int(r0), -1):
        t = (r - r0) / max(1, (r1 - r0))
        d.ellipse([cx-r, cx-r, cx+r, cx+r], fill=int(hi + (lo - hi) * t))
    d.ellipse([cx-r0, cx-r0, cx+r0, cx+r0], fill=hi)
    return m

# =============================================================== BG ==========
def gen_bg():
    # ---- base: near-black with a faint cool radial lift -------------------
    bg = Image.new('RGB', (S, S), INK)
    lift = Image.new('L', (S, S), 0)
    ld = ImageDraw.Draw(lift)
    for r in range(260, 0, -2):
        t = r / 260
        ld.ellipse([C-r, C-r-30, C+r, C+r-30], fill=int(26 * (1 - t)))
    bg = ImageChops.add(bg, Image.merge('RGB', (
        lift.point(lambda v: v // 4), lift.point(lambda v: v // 3), lift.point(lambda v: v // 2))))

    # corner nebula accents (magenta low-left, violet up-right)
    neb = Image.new('RGBA', (S, S), (0, 0, 0, 0)); nd = ImageDraw.Draw(neb)
    nd.ellipse([-120, 330, 180, 620], fill=MAGENTA + (26,))
    nd.ellipse([300, -140, 620, 160], fill=VIOLET + (24,))
    nd.ellipse([-140, -120, 120, 140], fill=CYAN + (16,))
    neb = neb.filter(ImageFilter.GaussianBlur(60))
    bg = Image.alpha_composite(bg.convert('RGBA'), neb)

    # scanlines: 1px every 4px
    scan = Image.new('RGBA', (S, S), (0, 0, 0, 0)); sd = ImageDraw.Draw(scan)
    for y in range(0, S, 4):
        sd.line([(0, y), (S, y)], fill=(0, 0, 0, 26))
        if y % 16 == 0:
            sd.line([(0, y+1), (S, y+1)], fill=CYAN + (7,))
    bg = Image.alpha_composite(bg, scan)

    # vignette
    vig = radial_mask(S, 150, 244, lo=255, hi=0).point(lambda v: 255 - v)
    dark = Image.new('RGBA', (S, S), (2, 2, 6, 255))
    dark.putalpha(vig.point(lambda v: int((255 - v) * 0.55)))
    bg = Image.alpha_composite(bg, dark)
    bg.convert('RGB').save(f'{NODPI}/bg.png')

    # ---- AOD: plain near-black, ultra-dim vignette only (burn-in safe) ----
    aod = Image.new('RGB', (S, S), (3, 3, 6))
    ad = ImageDraw.Draw(aod)
    ad.ellipse([C-238, C-238, C+238, C+238], outline=(10, 14, 18), width=2)
    aod.save(f'{NODPI}/bg_aod.png')

    # ---- grid layer (parallax): hex grid + circuit traces -----------------
    def hexgrid(d, ss):
        r = 34 * ss
        dx, dy = r * math.sqrt(3), r * 1.5
        col = CYAN + (30,)
        for row in range(-1, int(S*ss/dy) + 2):
            for colm in range(-1, int(S*ss/dx) + 2):
                cx = colm * dx + (dx/2 if row % 2 else 0)
                cy = row * dy
                pts = [(cx + r*math.sin(math.radians(a)), cy + r*math.cos(math.radians(a)))
                       for a in range(0, 360, 60)]
                d.polygon(pts, outline=col, width=max(1, ss//2))
    grid = _ss_draw(S, S, hexgrid, ss=2)

    gd = ImageDraw.Draw(grid)
    # circuit traces with solder nodes
    traces = [
        [(20, 150), (90, 150), (120, 120), (200, 120)],
        [(460, 330), (390, 330), (356, 364), (300, 364)],
        [(60, 330), (110, 330), (140, 300)],
        [(420, 150), (370, 150), (340, 180)],
        [(240, 470), (240, 444)],
    ]
    for i, tr in enumerate(traces):
        col = (MAGENTA if i % 3 == 1 else (VIOLET if i % 3 == 2 else CYAN))
        gd.line(tr, fill=col + (60,), width=2)
        x, y = tr[-1]
        gd.ellipse([x-3, y-3, x+3, y+3], outline=col + (90,), width=1)

    # ECG strip band delimiters + faint vertical ticks (static "graph paper")
    y0, y1 = L['ecg_cy'] - ECG_H//2, L['ecg_cy'] + ECG_H//2
    gd.line([(0, y0), (S, y0)], fill=CYAN + (36,), width=1)
    gd.line([(0, y1), (S, y1)], fill=CYAN + (36,), width=1)
    for x in range(0, S, 24):
        gd.line([(x, y0+2), (x, y1-2)], fill=CYAN + (13,))

    # fade the grid toward the center so the HR number owns the frame
    fade = radial_mask(S, 90, 210, lo=255, hi=64)
    grid.putalpha(ImageChops.multiply(grid.split()[3], fade))
    grid.save(f'{NODPI}/grid.png')

    # ---- per-beat aura ring behind the HR number --------------------------
    aura = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); adr = ImageDraw.Draw(aura)
    for r in range(132, 88, -1):
        t = (r - 88) / 44
        a = int(105 * (1 - abs(t - 0.5) * 2))
        col = MAGENTA if t > 0.45 else RED
        adr.ellipse([150-r, 150-r, 150+r, 150+r], outline=col + (max(0, a),), width=2)
    aura = aura.filter(ImageFilter.GaussianBlur(10))
    aura.save(f'{NODPI}/aura.png')

    # ---- HR-intensity heat wash (alpha driven by HR in WFF) ---------------
    heat = Image.new('RGBA', (S, S), (0, 0, 0, 0)); hd = ImageDraw.Draw(heat)
    for r in range(240, 0, -2):
        t = r / 240
        hd.ellipse([C-r, C-r, C+r, C+r], fill=RED + (int(120 * (1 - t) ** 1.6),))
    heat = heat.filter(ImageFilter.GaussianBlur(12))
    heat.save(f'{NODPI}/heat.png')

    # ---- ECG waveform strip (seamless scroll, 2 cycles per screen) --------
    def ecg_cycle_pts(x0, ss, base):
        p = lambda x, y: (x0 + x*ss, base - y*ss)
        return [
            p(0, 0), p(28, 0),                       # baseline
            p(34, 5), p(42, 7), p(50, 5), p(56, 0),  # P wave
            p(70, 0),
            p(74, -6),                               # Q
            p(81, 30),                               # R spike
            p(88, -11),                              # S
            p(94, 0), p(112, 0),
            p(122, 6), p(134, 10), p(146, 6), p(156, 0),  # T wave
            p(ECG_PERIOD, 0),
        ]
    def ecg_draw(d, ss):
        base = (ECG_H // 2 + 12) * ss
        for cyc in range(ECG_W // ECG_PERIOD):
            d.line(ecg_cycle_pts(cyc * ECG_PERIOD * ss, ss, base),
                   fill=CYAN + (255,), width=2*ss, joint='curve')
    wave = _ss_draw(ECG_W, ECG_H, ecg_draw, ss=4)
    neon(wave, CYAN, 2, 5, 0.8).save(f'{NODPI}/ecg.png')

    # ---- HR arc track: zone-colored geography + personal baseline band ----
    def track(d, ss):
        r, th = ARC['r']*ss, ARC['th']*ss
        bb = [C*ss-r, C*ss-r, C*ss+r, C*ss+r]
        # zone band segments (low alpha, live cyan sweep rides on top)
        for lo, hi, _w, col in ZONES:
            d.arc(bb, bpm_angle(lo)-90, bpm_angle(hi)-90, fill=col + (78,), width=th)
        # personal baseline band 58-108 bpm, violet, just inside the gauge
        rb = (ARC['r'] - 10) * ss
        bbb = [C*ss-rb, C*ss-rb, C*ss+rb, C*ss+rb]
        d.arc(bbb, bpm_angle(BASELINE[0])-90, bpm_angle(BASELINE[1])-90,
              fill=VIOLET + (120,), width=3*ss)
        # ticks at zone boundaries (40/65/95/135/165/200)
        for bpm in [40] + [z[1] for z in ZONES]:
            a = math.radians(bpm_angle(bpm) - 90)
            x0, y0 = C*ss + (r-9*ss)*math.cos(a), C*ss + (r-9*ss)*math.sin(a)
            x1, y1 = C*ss + (r+7*ss)*math.cos(a), C*ss + (r+7*ss)*math.sin(a)
            d.line([(x0, y0), (x1, y1)], fill=ICE + (130,), width=2*ss)
    _ss_draw(S, S, track, ss=2).save(f'{NODPI}/arc_track.png')

    # ---- HR zone word plates (pre-rendered: tint would muddy neon hues) ---
    zf = ImageFont.truetype(FONT_ORB, 20)
    for _lo, _hi, word, col in ZONES:
        core = tuple(int(c*0.35 + 255*0.65) for c in col)
        w = int(zf.getlength(word)) + 32
        h = 34
        pl = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(pl).text((w//2, h//2), word, font=zf, fill=core + (255,),
                                anchor='mm')
        pl = neon(pl, col, 1, 4, 0.55)
        ImageDraw.Draw(pl).text((w//2, h//2), word, font=zf, fill=core + (255,),
                                anchor='mm')
        pl.save(f'{NODPI}/zone_{word.lower()}.png')

    # ---- moving specular sheen -------------------------------------------
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(-140, 0), (40, 0), (240, 480), (60, 480)],
                               fill=(200, 245, 255, 22))
    sh.filter(ImageFilter.GaussianBlur(48)).save(f'{NODPI}/sheen.png')

    # ---- complication neon frame (corner brackets) ------------------------
    def brackets(d, ss):
        w, h, k, lw = 136*ss, 58*ss, 16*ss, max(2, 2*ss)
        for (cx, cy, sx, sy) in ((0,0,1,1),(w,0,-1,1),(0,h,1,-1),(w,h,-1,-1)):
            d.line([(cx, cy+sy*k), (cx, cy), (cx+sx*k, cy)], fill=CYAN + (230,), width=lw)
        d.line([(k+6*ss, h//2), (k+14*ss, h//2)], fill=MAGENTA + (150,), width=lw)
        d.line([(w-k-14*ss, h//2), (w-k-6*ss, h//2)], fill=MAGENTA + (150,), width=lw)
    fr = _ss_draw(136, 58, brackets)
    neon(fr, CYAN, 1, 3, 0.6).save(f'{NODPI}/compframe.png')

    # ---- icons ------------------------------------------------------------
    def heart(d, ss):
        s = ss
        d.pieslice([2*s, 3*s, 13*s, 14*s], 180, 360, fill=MAGENTA + (255,))
        d.pieslice([11*s, 3*s, 22*s, 14*s], 180, 360, fill=MAGENTA + (255,))
        d.polygon([(2*s, 9*s), (22*s, 9*s), (12*s, 22*s)], fill=MAGENTA + (255,))
    neon(_ss_draw(24, 24, heart), MAGENTA, 2, 4).save(f'{NODPI}/heart.png')

    def shoe(d, ss):
        s = ss; col = CYAN + (255,); lw = max(2, 2*s)
        d.line([(4*s, 16*s), (4*s, 7*s)], fill=col, width=lw)
        d.line([(4*s, 7*s), (11*s, 7*s)], fill=col, width=lw)
        d.line([(11*s, 7*s), (15*s, 12*s)], fill=col, width=lw)
        d.line([(15*s, 12*s), (26*s, 15*s)], fill=col, width=lw)
        d.line([(26*s, 15*s), (26*s, 18*s)], fill=col, width=lw)
        d.line([(4*s, 18*s), (26*s, 18*s)], fill=col, width=lw)
    neon(_ss_draw(30, 24, shoe), CYAN, 1, 3).save(f'{NODPI}/shoe.png')

    def bolt(d, ss):
        s = ss
        d.polygon([(13*s, 2*s), (5*s, 13*s), (10*s, 13*s), (8*s, 22*s),
                   (17*s, 10*s), (12*s, 10*s)], fill=VIOLET + (255,))
    neon(_ss_draw(22, 24, bolt), VIOLET, 1, 3).save(f'{NODPI}/bolt.png')

    print('bg: bg bg_aod grid aura heat ecg arc_track sheen compframe heart shoe bolt')

# =============================================================== GLYPHS ======
# neo  = white-cyan core + cyan glow  (time/date/steps/battery/brand)
# hot  = white-pink core + magenta/red glow (HR number + BPM label)
NEO_CHARS = {**{str(i): str(i) for i in range(10)},
             **{ch: ch.lower() for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'},
             ':': 'colon', '%': 'pct', '.': 'dot', ' ': 'space'}
HOT_CHARS = {**{str(i): str(i) for i in range(10)}, 'B': 'b', 'P': 'p', 'M': 'm'}
FS = 96          # render size; WFF `size` scales the cell

def _render_glyph(ch, font, asc, H, core, glowc):
    pad = 10
    if ch == ' ':
        w = int(FS * 0.30) + pad*2
        return Image.new('RGBA', (w, H), (0, 0, 0, 0)), w
    w = max(8, int(round(font.getlength(ch)))) + pad*2
    im = Image.new('RGBA', (w, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad, asc), ch, font=font, fill=core + (255,), anchor='ls', stroke_width=2,
           stroke_fill=core + (255,))
    im = neon(im, glowc, 2, 6, 0.85)
    # crisp core re-draw on top of the glow
    d = ImageDraw.Draw(im)
    d.text((pad, asc), ch, font=font, fill=core + (255,), anchor='ls', stroke_width=2,
           stroke_fill=core + (255,))
    return im, w

def gen_glyphs():
    f = ImageFont.truetype(FONT_ORB, FS)
    asc, desc = f.getmetrics()
    H = asc + desc + 8            # +8: room for glow bleed
    meta = {'neo': {}, 'hot': {}}
    for fam, chars, core, glow in (('neo', NEO_CHARS, ICE, CYAN),
                                   ('hot', HOT_CHARS, PINK, MAGENTA)):
        p = 'n' if fam == 'neo' else 'h'
        for ch, rn in chars.items():
            im, w = _render_glyph(ch, f, asc + 4, H, core, glow)
            name = f'g_{p}_{rn}'
            im.save(f'{NODPI}/{name}.png')
            meta[fam][ch] = (name, w, H)
    json.dump(meta, open(f'{ROOT}/tools/glyphs.json', 'w'))
    print(f'glyphs: neo={len(meta["neo"])} hot={len(meta["hot"])} cell H={H}')

def _meta():
    return json.load(open(f'{ROOT}/tools/glyphs.json'))

# =============================================================== XML =========
T    = '([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
BPM  = '(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 220))'
BEAT = f'abs(sin({T} * {BPM} * 0.05236))'                 # 1 flash per beat
PX   = 'clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'
PY   = 'clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
HEAT = 'clamp(([HEART_RATE] - 78) * 2.2, 0, 95)'          # HR-reactive skin
HRCL = '(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 200))'

def Vr(t, v, dur=0.35, off=0.0, ip='EASE_OUT'):
    return (f'      <Variant mode="AMBIENT" target="{t}" value="{v}" '
            f'duration="{dur}" startOffset="{off}" interpolation="{ip}" />\n')

def XF(t, v):
    return f'      <Transform target="{t}" value="{v}" />\n'

def img(name, res, cx, cy, w, h, alpha=255, kids='', pivot=None):
    piv = f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"' if pivot else ''
    return (f'    <PartImage name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" '
            f'width="{w}" height="{h}" alpha="{alpha}"{piv}>\n'
            f'{kids}      <Image resource="{res}" />\n    </PartImage>\n')

def bffonts():
    m = _meta()
    esc = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}
    out = '  <BitmapFonts>\n'
    for fam in ('neo', 'hot'):
        out += f'    <BitmapFont name="{fam}">\n'
        for ch, (nm, w, h) in m[fam].items():
            out += (f'      <Character name="{esc.get(ch, ch)}" resource="{nm}" '
                    f'width="{w}" height="{h}" />\n')
        out += '    </BitmapFont>\n'
    return out + '  </BitmapFonts>\n'

def ptext(name, cx, cy, w, h, fam, size, tmpl, params, upper=False,
          variant='', xf=''):
    inner = f'<Template>{tmpl}'
    for p in params:
        inner += f'<Parameter expression="{p}" />'
    inner += '</Template>'
    if upper:
        inner = f'<Upper>{inner}</Upper>'
    return (f'    <PartText name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" '
            f'width="{w}" height="{h}">\n{variant}{xf}'
            f'      <Text align="CENTER"><BitmapFont family="{fam}" size="{size}" '
            f'color="#FFFFFF">{inner}</BitmapFont></Text>\n    </PartText>\n')

def pstatic(name, cx, cy, w, h, fam, size, text, variant='', xf=''):
    return (f'    <PartText name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" '
            f'width="{w}" height="{h}">\n{variant}{xf}'
            f'      <Text align="CENTER"><BitmapFont family="{fam}" size="{size}" '
            f'color="#FFFFFF">{text}</BitmapFont></Text>\n    </PartText>\n')

def gen_xml():
    o = ['<?xml version="1.0" encoding="utf-8"?>\n'
         '<WatchFace width="480" height="480">\n'
         '  <Metadata key="CLOCK_TYPE" value="DIGITAL" />\n'
         '  <Metadata key="PREVIEW_TIME" value="10:09:32" />\n']
    o.append(bffonts())
    o.append('  <Scene backgroundColor="#FF07070D">\n')

    # z0 backgrounds: interactive bg crossfades to AOD ghost, subtle parallax
    o.append(img('z00_bg', 'bg', C, C, S, S, 255,
                 kids=Vr('alpha', '0', 0.45, 0.0)
                 + XF('x', f'0 + 4 * {PX}') + XF('y', f'0 + 4 * {PY}')))
    o.append(img('z00_aod', 'bg_aod', C, C, S, S, 0,
                 kids=Vr('alpha', '255', 0.45, 0.0, 'EASE_IN')))

    # z1 hex/circuit grid — counter-parallax (2nd depth layer)
    o.append(img('z01_grid', 'grid', C, C, S, S, 255,
                 kids=Vr('alpha', '0', 0.4, 0.05)
                 + XF('x', f'0 - 7 * {PX}') + XF('y', f'0 - 7 * {PY}')))

    # z2 HR-intensity heat wash (face "heats up" with high HR)
    o.append(img('z02_heat', 'heat', C, C, S, S, 0,
                 kids=Vr('alpha', '0', 0.4, 0.10) + XF('alpha', HEAT)))

    # z3 per-beat aura ring behind the HR number — the face literally beats
    o.append(img('z03_aura', 'aura', L['hr'][0], L['hr'][1] + 4, 300, 300, 0,
                 pivot=('0.5', '0.5'),
                 kids=Vr('alpha', '0', 0.4, 0.08)
                 + XF('alpha', f'70 + 185 * {BEAT}')
                 + XF('scaleX', f'1 + 0.06 * {BEAT}')
                 + XF('scaleY', f'1 + 0.06 * {BEAT}')))

    # z4 HR ring: dim track + live arc sweeping 40..200 bpm
    o.append(img('z04_track', 'arc_track', C, C, S, S, 255,
                 kids=Vr('alpha', '0', 0.35, 0.15)))
    a = ARC
    o.append('    <PartDraw name="z04_hr_arc" x="0" y="0" width="480" height="480">\n'
             + Vr('alpha', '0', 0.5, 0.18, 'OVERSHOOT')
             + f'      <Arc centerX="{C}" centerY="{C}" width="{a["r"]*2}" height="{a["r"]*2}" '
             f'startAngle="{a["a0"]}" endAngle="{a["a0"] + 60}" direction="CLOCKWISE">\n'
             f'        <Transform target="endAngle" '
             f'value="{a["a0"]} + {a["span"]} * ({HRCL} - 40) / 160" />\n'
             f'        <Stroke color="#00E5FF" thickness="{a["th"]}" cap="ROUND" />\n'
             '      </Arc>\n    </PartDraw>\n')

    # z5 ECG strip — signature motif, scrolls right-to-left forever
    ey = L['ecg_cy'] - ECG_H // 2
    o.append(f'    <PartImage name="z05_ecg" x="0" y="{ey}" width="{ECG_W}" height="{ECG_H}" alpha="255">\n'
             + Vr('alpha', '0', 0.4, 0.22)
             + XF('x', f'-480 + (({T} * {ECG_SPEED}) % 480)')
             + '      <Image resource="ecg" />\n    </PartImage>\n')

    # z6 moving specular sheen (sells the glass)
    o.append(img('z06_sheen', 'sheen', C, C, S, S, 0,
                 kids=Vr('alpha', '0', 0.5, 0.30)
                 + XF('alpha', f'40 + 30 * abs(sin({T} * 0.5))')
                 + XF('x', f'0 + 55 * {PX}')))

    # z7 brand + date
    o.append(pstatic('z07_brand', *L['brand'], 170, 20, 'neo', 12, 'XSY PULSE',
                     variant=Vr('alpha', '0', 0.35, 0.50)))
    o.append(ptext('z07_date', *L['date'], 220, 28, 'neo', 18, '%s %d',
                   ['[DAY_OF_WEEK_S]', '[DAY]'], upper=True,
                   variant=Vr('alpha', '0', 0.35, 0.12)))

    # z8 time hh:mm + small seconds (BitmapFont — TTFs silently fail)
    tx, ty = L['time']; tw, th = 240, 66
    o.append(f'    <Group name="z08_time" x="{tx-tw//2}" y="{ty-th//2}" width="{tw}" height="{th}" alpha="255">\n'
             + Vr('alpha', '150', 0.35, 0.04)
             + f'      <DigitalClock x="0" y="0" width="{tw}" height="{th}">\n'
             f'        <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" '
             f'x="0" y="0" width="{tw}" height="{th}">\n'
             f'          <BitmapFont family="neo" size="48" color="#FFFFFF" />\n'
             '        </TimeText>\n      </DigitalClock>\n    </Group>\n')
    sx, sy = L['secs']; sw, sh = 56, 44
    o.append(f'    <Group name="z08_secs" x="{sx-sw//2}" y="{sy-sh//2}" width="{sw}" height="{sh}" alpha="255">\n'
             + Vr('alpha', '0', 0.3, 0.10)
             + f'      <DigitalClock x="0" y="0" width="{sw}" height="{sh}">\n'
             f'        <TimeText format="ss" align="CENTER" x="0" y="0" width="{sw}" height="{sh}">\n'
             f'          <BitmapFont family="neo" size="22" color="#FFFFFF" />\n'
             '        </TimeText>\n      </DigitalClock>\n    </Group>\n')

    # z9 THE CENTERPIECE — live heart rate, huge, breathing with each beat
    o.append(ptext('z09_hr', *L['hr'], 300, 124, 'hot', 100, '%d', [BPM],
                   variant=Vr('alpha', '120', 0.35, 0.06),
                   xf=XF('alpha', f'205 + 50 * {BEAT}')))
    o.append(img('z09_heart', 'heart', *L['heart'], 24, 24, 255,
                 kids=Vr('alpha', '0', 0.35, 0.14)
                 + XF('alpha', f'70 + 185 * {BEAT}')))
    o.append(pstatic('z09_bpm', *L['bpm_lbl'], 64, 24, 'hot', 18, 'BPM',
                     variant=Vr('alpha', '0', 0.35, 0.14)))
    # % of age-max HR (owner ~42 -> HRmax 178); WFF is stateless, so only
    # instantaneous derivations of [HEART_RATE] are possible
    o.append(ptext('z09_pmax', *L['pmax_val'], 56, 24, 'neo', 18, '%d',
                   [f'round({BPM} * 100 / {MAXHR})'],
                   variant=Vr('alpha', '0', 0.35, 0.16)))
    o.append(pstatic('z09_pmax_l', *L['pmax_lbl'], 66, 18, 'neo', 13, '%MAX',
                     variant=Vr('alpha', '0', 0.35, 0.18)))

    # z9b HR zone label — Condition: first matching Compare wins (XSD-ordered)
    zc = []
    zc.append('    <Condition>\n      <Expressions>\n')
    for lo, hi, word, _c in ZONES[:-1]:
        zc.append(f'        <Expression name="z_{word.lower()}">{BPM} &lt; {hi}</Expression>\n')
    zc.append('      </Expressions>\n')
    zx, zy = L['zone']
    def zplate(word):
        im = Image.open(f'{NODPI}/zone_{word.lower()}.png')
        w, h = im.size
        return (f'        <PartImage name="z09_zone_{word.lower()}" x="{zx - w//2}" '
                f'y="{zy - h//2}" width="{w}" height="{h}" alpha="255">\n'
                f'    {Vr("alpha", "0", 0.35, 0.16)}'
                f'          <Image resource="zone_{word.lower()}" />\n        </PartImage>\n')
    for lo, hi, word, _c in ZONES[:-1]:
        zc.append(f'      <Compare expression="z_{word.lower()}">\n{zplate(word)}      </Compare>\n')
    zc.append(f'      <Default>\n{zplate(ZONES[-1][2])}      </Default>\n')
    zc.append('    </Condition>\n')
    o.append(''.join(zc))

    # z10 steps + battery readouts
    o.append(img('z10_shoe', 'shoe', *L['shoe'], 30, 24, 255,
                 kids=Vr('alpha', '0', 0.35, 0.28)))
    o.append(ptext('z10_steps', *L['steps'], 110, 28, 'neo', 20, '%d',
                   ['[STEP_COUNT]'], variant=Vr('alpha', '0', 0.35, 0.28)))
    o.append(img('z10_bolt', 'bolt', *L['bolt'], 22, 24, 255,
                 kids=Vr('alpha', '0', 0.35, 0.32)))
    o.append(ptext('z10_batt', *L['batt'], 100, 28, 'neo', 20, '%d%%',
                   ['[BATTERY_PERCENT]'], variant=Vr('alpha', '0', 0.35, 0.32)))

    # z11 Hermes360 complication slot, framed in our own neon brackets
    ccx, ccy = L['comp']
    o.append(img('z11_compframe', 'compframe', ccx, ccy + 2, 136, 58, 255,
                 kids=Vr('alpha', '0', 0.4, 0.38, 'OVERSHOOT')))
    o.append(f'    <ComplicationSlot name="hermes_slot" x="{ccx-60}" y="{ccy-22}" '
             'width="120" height="44" slotId="1001" supportedTypes="SHORT_TEXT">\n'
             '      <DefaultProviderPolicy '
             'primaryProvider="com.xsyprime.primebeaconwear/com.xsyprime.primebeaconwear.PulseComplicationService" '
             'primaryProviderType="SHORT_TEXT" '
             'defaultSystemProvider="WATCH_BATTERY" defaultSystemProviderType="SHORT_TEXT" />\n'
             f'      <BoundingBox x="0" y="0" width="120" height="44" />\n'
             '      <Complication type="SHORT_TEXT" />\n'
             '    </ComplicationSlot>\n')

    o.append('  </Scene>\n</WatchFace>\n')
    xml = ''.join(o)
    with open(f'{RES}/raw/watchface.xml', 'w') as fh:
        fh.write(xml)
    print('watchface.xml written:', len(xml), 'bytes')

# =============================================================== PREVIEW =====
# Faithful WFF mimic: BitmapFont scaled by size/cellH laid left-to-right,
# arc angles 0deg = 12 o'clock clockwise (PIL angle = wff - 90).
PV = dict(time='10:09', secs='32', hr=96, steps='7645', batt=84,
          date='WED 23', beat=0.85)

def _str(base, fam, s, cx, cy, size):
    m = _meta()[fam]
    H = next(iter(m.values()))[2]
    sc = size / H
    parts, tot = [], 0.0
    for ch in s:
        ch = ch if ch in m else ' '
        nm, w, h = m[ch]
        parts.append((nm, w * sc)); tot += w * sc
    x = cx - tot / 2
    for nm, gw in parts:
        g = Image.open(f'{NODPI}/{nm}.png').convert('RGBA')
        g = g.resize((max(1, int(round(gw))), int(round(size))), Image.LANCZOS)
        base.alpha_composite(g, (int(x), int(cy - size / 2)))
        x += gw

def _p(base, name, cx, cy, alpha=255, scale=1.0):
    im = Image.open(f'{NODPI}/{name}.png').convert('RGBA')
    if scale != 1.0:
        im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
    if alpha < 255:
        im = im.copy()
        im.putalpha(im.split()[3].point(lambda v: int(v * alpha / 255)))
    base.alpha_composite(im, (int(cx - im.width/2), int(cy - im.height/2)))

def compose_preview():
    beat, hr = PV['beat'], PV['hr']
    base = Image.open(f'{NODPI}/bg.png').convert('RGBA')
    _p(base, 'grid', C, C)
    heat_a = max(0, min(95, (hr - 78) * 2.2))
    if heat_a > 0:
        _p(base, 'heat', C, C, int(heat_a))
    _p(base, 'aura', L['hr'][0], L['hr'][1] + 4, int(70 + 185*beat), 1 + 0.06*beat)

    # HR arc: zone-colored track + baseline band (baked) + live sweep
    _p(base, 'arc_track', C, C)
    d = ImageDraw.Draw(base)
    a0 = ARC['a0']; a1 = bpm_angle(hr)
    r = ARC['r']
    d.arc([C-r, C-r, C+r, C+r], a0-90, a1-90, fill=CYAN, width=ARC['th'])

    # scrolling ECG at an arbitrary loop offset
    ecg = Image.open(f'{NODPI}/ecg.png').convert('RGBA')
    xoff = -480 + int((7.3 * ECG_SPEED) % 480)
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    lay.alpha_composite(ecg, (xoff, L['ecg_cy'] - ECG_H // 2))
    base.alpha_composite(lay)

    _p(base, 'sheen', C, C, 55)

    _str(base, 'neo', 'XSY PULSE', *L['brand'], 12)
    _str(base, 'neo', PV['date'], *L['date'], 18)
    _str(base, 'neo', PV['time'], *L['time'], 48)
    _str(base, 'neo', PV['secs'], *L['secs'], 22)
    _str(base, 'hot', str(hr), *L['hr'], 100)
    _p(base, 'heart', *L['heart'], int(70 + 185*beat))
    _str(base, 'hot', 'BPM', *L['bpm_lbl'], 18)
    _str(base, 'neo', str(round(hr * 100 / MAXHR)), *L['pmax_val'], 18)
    _str(base, 'neo', '%MAX', *L['pmax_lbl'], 13)
    zone_word = next((w for lo, hi, w, _c in ZONES if hr < hi), ZONES[-1][2])
    _p(base, f'zone_{zone_word.lower()}', *L['zone'])
    _p(base, 'shoe', *L['shoe'])
    _str(base, 'neo', PV['steps'], *L['steps'], 20)
    _p(base, 'bolt', *L['bolt'])
    _str(base, 'neo', f"{PV['batt']}%", *L['batt'], 20)

    # complication: our frame + system-font placeholder (provider draws its own text)
    _p(base, 'compframe', L['comp'][0], L['comp'][1] + 2)
    try:
        sysf = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        d.text(L['comp'], f"{PV['batt']}%", font=sysf, fill=(220, 230, 235), anchor='mm')
    except OSError:
        pass

    circ = Image.new('L', (S, S), 0)
    ImageDraw.Draw(circ).ellipse([0, 0, S, S], fill=255)
    base.putalpha(ImageChops.multiply(base.split()[3], circ))
    base.save(f'{DRAW}/preview.png')
    out = f'{SCRATCH}/pulse_preview.png'
    base.convert('RGB').save(out)
    print('preview ->', f'{DRAW}/preview.png', 'and', out)

# =============================================================== MAIN ========
if __name__ == '__main__':
    st = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if st in ('bg', 'all'): gen_bg()
    if st in ('glyphs', 'all'): gen_glyphs()
    if st in ('xml', 'all'): gen_xml()
    if st in ('preview', 'all'): compose_preview()
