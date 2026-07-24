#!/usr/bin/env python3
"""
X1c7 BUSHIDO — Watch Face Format v4 builder for Galaxy Watch 7 (480x480).

One file so the layout can never drift between the assets, the watchface.xml,
and the preview compositor. Stages (argv): assets | xml | preview | all
"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
RES  = f'{ROOT}/app/src/main/res'
NODPI= f'{RES}/drawable-nodpi'
DRAW = f'{RES}/drawable'
FONTDIR = '/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/fonts'
CJK  = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
S = 480

os.makedirs(NODPI, exist_ok=True); os.makedirs(DRAW, exist_ok=True)

# ---------------------------------------------------------------- palette ----
INK      = '#05070C'
WHITE    = '#EAF6FF'
MAGENTA  = '#FF2E7A'
MAG_DIM  = '#B01E54'
CYAN     = '#37E3FF'
CYAN_DIM = '#1C7C93'
RED      = '#FF3B5C'
MUTE     = '#7F97A6'
AMBER    = '#FFC24B'

def hx(c):  # '#RRGGBB' -> (r,g,b)
    c = c.lstrip('#'); return tuple(int(c[i:i+2],16) for i in (0,2,4))

# WFF res/font families (filename without extension)
F_DISP   = 'chakra_bold'         # ChakraPetch-Bold  (big time, X1c7)
F_DISP2  = 'chakra_semibold'     # ChakraPetch-SemiBold (SAT, values)
F_LABEL  = 'rajdhani_semibold'   # Rajdhani (labels)
F_LABELB = 'rajdhani_bold'

# PIL font file map for the faithful preview
PILF = {
    F_DISP:   f'{FONTDIR}/ChakraPetch-Bold.ttf',
    F_DISP2:  f'{FONTDIR}/ChakraPetch-SemiBold.ttf',
    F_LABEL:  f'{FONTDIR}/Rajdhani-SemiBold.ttf',
    F_LABELB: f'{FONTDIR}/Rajdhani-Bold.ttf',
}
_fc = {}
def pil(fam, size):
    k=(fam,int(size))
    if k not in _fc: _fc[k]=ImageFont.truetype(PILF[fam], int(size))
    return _fc[k]

# ------------------------------------------------------------- LAYOUT ---------
# Everything as (center_x, center_y). Boxes derived from font size.
L = {
    'mask':      (86, 80, 46),
    'sat':       (240, 58),
    'date':      (240, 90),
    'wx_icon':   (392, 64, 30),
    'wx_temp':   (394, 94),

    'hour':      (158, 186),
    'colon':     (240, 180),
    'minute':    (322, 186),
    'ampm':      (400, 156),
    'secs':      (400, 193),
    'hglow':     (158, 190),
    'mglow':     (322, 190),

    'x1c7':      (240, 250),
    'kanji':     (240, 281),   # 影の戦士

    'batt_val':  (70, 197),
    'batt_lbl':  (70, 219),
    'bpm_icon':  (452, 171),
    'bpm_val':   (452, 197),
    'bpm_lbl':   (452, 219),
    'ecg':       (424, 253),

    'steps_icon':(60, 380),
    'steps_val': (112, 372),
    'steps_lbl': (100, 396),
    'cal_icon':  (422, 380),
    'cal_val':   (368, 372),
    'cal_lbl':   (384, 396),

    'dist_lbl':  (240, 424),
    'dist_val':  (240, 446),
    'torii':     (240, 467),
}
# progress arcs (WFF: 0deg = 12 o'clock, clockwise)
BATT_ARC = dict(cx=240, cy=240, r=206, th=13, a0=232, a1=304)   # left rim
STEP_ARC = dict(cx=240, cy=240, r=206, th=6,  a0=318, a1=42)    # top rim (wraps 0)

# =============================================================== ASSETS =======
def _supersample_draw(w, h, fn, ss=4):
    im = Image.new('RGBA', (w*ss, h*ss), (0,0,0,0))
    d = ImageDraw.Draw(im)
    fn(d, ss)
    return im.resize((w, h), Image.LANCZOS)

def neon(im, color, grow=3, blur=6, core=True):
    """Add an outer neon glow around opaque pixels of im (RGBA)."""
    a = im.split()[3]
    glow = Image.new('RGBA', im.size, color+(0,))
    ga = a.filter(ImageFilter.MaxFilter(2*grow+1)).filter(ImageFilter.GaussianBlur(blur))
    glow.putalpha(ga.point(lambda v: int(v*0.85)))
    out = Image.alpha_composite(glow, im)
    return out

def gen_assets():
    mag, cyan, red, white = hx(MAGENTA), hx(CYAN), hx(RED), hx(WHITE)

    # ---- samurai oni-mask logo (top-left) --------------------------------
    def mask(d, ss):
        s=ss; cx,cy=23*s,23*s
        # kabuto horns + oni face, line art
        lw=max(2,2*s)
        col=mag+(255,)
        # face shield
        d.polygon([(cx-13*s,cy-6*s),(cx+13*s,cy-6*s),(cx+9*s,cy+12*s),(cx,cy+16*s),
                   (cx-9*s,cy+12*s)], outline=col, width=lw)
        # horns
        d.arc([cx-20*s,cy-20*s,cx-2*s,cy-2*s],200,320,fill=col,width=lw)
        d.arc([cx+2*s,cy-20*s,cx+20*s,cy-2*s],220,340,fill=col,width=lw)
        # eyes (angry)
        d.polygon([(cx-9*s,cy),(cx-3*s,cy-2*s),(cx-4*s,cy+3*s)],fill=cyan+(255,))
        d.polygon([(cx+9*s,cy),(cx+3*s,cy-2*s),(cx+4*s,cy+3*s)],fill=cyan+(255,))
        # tusks
        d.line([(cx-5*s,cy+9*s),(cx-7*s,cy+13*s)],fill=col,width=lw)
        d.line([(cx+5*s,cy+9*s),(cx+7*s,cy+13*s)],fill=col,width=lw)
    im = _supersample_draw(46,46,mask)
    neon(im, mag, 2, 4).save(f'{NODPI}/mask.png')

    # ---- torii gate (bottom) --------------------------------------------
    def torii(d, ss):
        s=ss; col=mag+(255,); lw=max(2,3*s)
        top=6*s; W=44*s
        d.line([(4*s,top),(W-4*s,top)],fill=col,width=lw)                 # kasagi
        d.line([(7*s,top+5*s),(W-7*s,top+5*s)],fill=col,width=max(2,2*s)) # nuki
        d.line([(12*s,top+2*s),(12*s,30*s)],fill=col,width=lw)            # left pillar
        d.line([(W-12*s,top+2*s),(W-12*s,30*s)],fill=col,width=lw)        # right pillar
    im=_supersample_draw(48,34,torii); neon(im,mag,2,4).save(f'{NODPI}/torii.png')

    # ---- shoe (steps) ----------------------------------------------------
    def shoe(d, ss):
        s=ss; col=cyan+(255,); lw=max(2,2*s)
        d.line([(4*s,18*s),(4*s,8*s)],fill=col,width=lw)
        d.line([(4*s,8*s),(11*s,8*s)],fill=col,width=lw)
        d.line([(11*s,8*s),(15*s,13*s)],fill=col,width=lw)
        d.line([(15*s,13*s),(28*s,17*s)],fill=col,width=lw)
        d.line([(28*s,17*s),(28*s,20*s)],fill=col,width=lw)
        d.line([(4*s,20*s),(28*s,20*s)],fill=col,width=lw)
        for i in range(3):
            d.line([(9*s+i*3*s,9*s),(11*s+i*3*s,13*s)],fill=col,width=max(1,s))
    im=_supersample_draw(32,26,shoe); neon(im,cyan,2,3).save(f'{NODPI}/shoe.png')

    # ---- fire (calories) -------------------------------------------------
    def fire(d, ss):
        s=ss; col=hx(AMBER)+(255,); lw=max(2,2*s)
        d.line([(13*s,3*s),(19*s,12*s),(16*s,17*s),(18*s,24*s),(13*s,27*s),
                (8*s,24*s),(9*s,16*s),(13*s,3*s)],fill=col,width=lw,joint='curve')
        d.line([(13*s,14*s),(15*s,20*s),(13*s,24*s),(11*s,20*s),(13*s,14*s)],
               fill=hx(MAGENTA)+(255,),width=max(1,s),joint='curve')
    im=_supersample_draw(26,30,fire); neon(im,hx(AMBER),2,3).save(f'{NODPI}/fire.png')

    # ---- heart (bpm) — flashes ------------------------------------------
    def heart(d, ss):
        s=ss; col=red+(255,)
        d.pieslice([3*s,4*s,14*s,15*s],180,360,fill=col)
        d.pieslice([12*s,4*s,23*s,15*s],180,360,fill=col)
        d.polygon([(3*s,10*s),(23*s,10*s),(13*s,24*s)],fill=col)
    im=_supersample_draw(26,26,heart); neon(im,red,2,4).save(f'{NODPI}/heart.png')

    # ---- crescent moon (weather) ----------------------------------------
    def moon(d, ss):
        s=ss; col=cyan+(255,)
        d.ellipse([3*s,3*s,27*s,27*s],fill=col)
        d.ellipse([9*s,1*s,31*s,25*s],fill=(0,0,0,0))
    base=Image.new('RGBA',(30*4,30*4),(0,0,0,0)); dd=ImageDraw.Draw(base)
    dd.ellipse([3*4,3*4,27*4,27*4],fill=cyan+(255,))
    dd.ellipse([10*4,0,34*4,24*4],fill=(0,0,0,0))
    base=base.resize((30,30),Image.LANCZOS)
    neon(base,cyan,2,3).save(f'{NODPI}/moon.png')

    # ---- ECG heartbeat trace (right rim) --------------------------------
    def ecg(d, ss):
        s=ss; col=red+(255,); lw=max(2,2*s); y=14*s
        pts=[(0,y),(14*s,y),(20*s,y-3*s),(26*s,y+10*s),(32*s,y-26*s),
             (38*s,y+6*s),(44*s,y),(64*s,y)]
        d.line(pts,fill=col,width=lw,joint='curve')
    im=_supersample_draw(64,30,ecg); neon(im,red,2,4).save(f'{NODPI}/ecg.png')

    # ---- rim ticks (static bezel) ---------------------------------------
    def rim(d, ss):
        s=ss; c=240*s; R=232*s
        for deg in range(0,360,6):
            major = deg%30==0
            r0 = R-(14*s if major else 8*s); r1=R-2*s
            a=math.radians(deg-90)
            col=(hx(CYAN) if major else (90,120,140))+(200 if major else 120,)
            d.line([(c+r0*math.cos(a),c+r0*math.sin(a)),
                    (c+r1*math.cos(a),c+r1*math.sin(a))],
                   fill=col,width=(3*s if major else max(1,s)))
    im=_supersample_draw(S,S,rim,ss=2); im.save(f'{NODPI}/rim.png')

    # ---- battery track (dim, behind live arc) ---------------------------
    def _arc_img(cfg, color, alpha, name, ss=4):
        w=Image.new('RGBA',(S*ss,S*ss),(0,0,0,0)); d=ImageDraw.Draw(w)
        cx,cy,r,th=cfg['cx']*ss,cfg['cy']*ss,cfg['r']*ss,cfg['th']*ss
        bb=[cx-r,cy-r,cx+r,cy+r]
        # convert 12-o'clock CW angles to PIL (0=3o'clock CCW): pil = deg-90
        a0=cfg['a0']-90; a1=cfg['a1']-90
        if a1<a0: a1+=360
        d.arc(bb,a0,a1,fill=color+(alpha,),width=int(th))
        w.resize((S,S),Image.LANCZOS).save(f'{NODPI}/{name}.png')
    _arc_img(BATT_ARC, (40,60,80), 150, 'batt_track')
    _arc_img(STEP_ARC, (40,60,80), 130, 'step_track')

    # ---- neon glow sprites (behind digits) ------------------------------
    for name,col in (('glow_mag',mag),('glow_cyan',cyan)):
        g=Image.new('RGBA',(260,200),(0,0,0,0)); gd=ImageDraw.Draw(g)
        gd.ellipse([30,40,230,160],fill=col+(90,))
        g=g.filter(ImageFilter.GaussianBlur(38)); g.save(f'{NODPI}/{name}.png')

    # ---- kanji plates (pre-rendered; avoids bundling a CJK font) --------
    def kanji(text, size, color, name, glowc):
        f=ImageFont.truetype(CJK, size)
        bb=f.getbbox(text); w=bb[2]-bb[0]; h=bb[3]-bb[1]
        pad=size//2
        im=Image.new('RGBA',(w+pad*2,h+pad*2),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.text((pad-bb[0],pad-bb[1]),text,font=f,fill=hx(color)+(255,))
        neon(im,hx(glowc),2,5).save(f'{NODPI}/{name}.png')
    kanji('影の戦士', 30, MAGENTA, 'k_senshi', MAGENTA)   # shadow warrior
    kanji('武士道',   40, WHITE,   'k_bushido', CYAN)      # bushido (unused spare)
    kanji('未来',     34, CYAN,    'k_mirai',   CYAN)      # future (spare)

    print('assets: mask torii shoe fire heart moon ecg rim batt_track step_track '
          'glow_mag glow_cyan k_senshi k_bushido k_mirai')

# =============================================================== PREVIEW ======
def _paste(base, name, cx, cy):
    im=Image.open(f'{NODPI}/{name}.png').convert('RGBA')
    base.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

def _text(d, cx, cy, s, fam, size, color, anchor='mm', ls=0):
    d.text((cx,cy), s, font=pil(fam,size), fill=hx(color), anchor=anchor)

def compose_preview(t='10:08:38', save='preview.png'):
    base=Image.open(f'{NODPI}/bg.png').convert('RGBA')
    # rim + rain + scan
    base.alpha_composite(Image.open(f'{NODPI}/rim.png').convert('RGBA'))
    rain=Image.open(f'{NODPI}/rain.png').convert('RGBA').crop((0,300,480,780))
    base.alpha_composite(rain)
    base.alpha_composite(Image.open(f'{NODPI}/scan.png').convert('RGBA'))
    d=ImageDraw.Draw(base)

    hh,mm,ssx = t.split(':')
    # progress arcs (battery 100, steps ~62%)
    def draw_arc(cfg, pct, color):
        cx,cy,r,th=cfg['cx'],cfg['cy'],cfg['r'],cfg['th']
        a0=cfg['a0']; span=(cfg['a1']-cfg['a0'])%360
        a1=cfg['a0']+span*pct
        bb=[cx-r,cy-r,cx+r,cy+r]
        d.arc(bb,a0-90,a1-90,fill=hx(color),width=th)
    _paste(base,'batt_track',240,240); _paste(base,'step_track',240,240)
    draw_arc(BATT_ARC,1.0,MAGENTA); draw_arc(STEP_ARC,0.62,CYAN)

    # gl! background glows behind digits
    _paste(base,'glow_cyan',*L['hglow'][:2]); _paste(base,'glow_mag',*L['mglow'][:2])

    # top
    _paste(base,'mask',L['mask'][0],L['mask'][1])
    _text(d,*L['sat'],'SAT',F_DISP2,26,MAGENTA)
    _text(d,*L['date'],'MAY 24',F_LABEL,23,WHITE)
    _paste(base,'moon',L['wx_icon'][0],L['wx_icon'][1])
    _text(d,*L['wx_temp'],'20°',F_LABEL,24,CYAN)

    # big time
    _text(d,*L['hour'],hh,F_DISP,100,WHITE,anchor='mm')
    _text(d,*L['colon'],':',F_DISP,88,MAGENTA,anchor='mm')
    _text(d,*L['minute'],mm,F_DISP,100,MAGENTA,anchor='mm')
    _text(d,*L['ampm'],'PM',F_LABELB,24,MAGENTA,anchor='mm')
    _text(d,*L['secs'],ssx,F_LABELB,32,WHITE,anchor='mm')

    # sub label
    _text(d,*L['x1c7'],'X1c7',F_DISP,30,CYAN,anchor='mm',ls=4)
    _paste(base,'k_senshi',L['kanji'][0],L['kanji'][1])

    # battery / bpm
    _text(d,*L['batt_val'],'100%',F_DISP2,24,WHITE,anchor='mm')
    _text(d,*L['batt_lbl'],'BATTERY',F_LABEL,15,MAGENTA,anchor='mm')
    _paste(base,'heart',L['bpm_icon'][0],L['bpm_icon'][1])
    _text(d,*L['bpm_val'],'78',F_DISP2,24,RED,anchor='mm')
    _text(d,*L['bpm_lbl'],'BPM',F_LABEL,15,MAGENTA,anchor='mm')
    _paste(base,'ecg',L['ecg'][0],L['ecg'][1])

    # steps / cal / distance
    _paste(base,'shoe',L['steps_icon'][0],L['steps_icon'][1])
    _text(d,*L['steps_val'],'7645',F_DISP2,26,WHITE,anchor='mm')
    _text(d,*L['steps_lbl'],'STEPS',F_LABEL,15,CYAN,anchor='mm')
    _paste(base,'fire',L['cal_icon'][0],L['cal_icon'][1])
    _text(d,*L['cal_val'],'1245',F_DISP2,26,WHITE,anchor='mm')
    _text(d,*L['cal_lbl'],'CAL',F_LABEL,15,AMBER,anchor='mm')

    _text(d,*L['dist_lbl'],'DISTANCE',F_LABEL,15,MUTE,anchor='mm')
    _text(d,*L['dist_val'],'5.62 KM',F_DISP2,22,WHITE,anchor='mm')
    _paste(base,'torii',L['torii'][0],L['torii'][1])

    # round mask
    mask=Image.new('L',(S,S),0); ImageDraw.Draw(mask).ellipse([0,0,S,S],fill=255)
    base.putalpha(ImageChops.multiply(base.split()[3],mask))
    out=f'/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/{save}'
    base.convert('RGB').save(out)
    # App/picker preview (transparent-round on black) into res/drawable
    base.save(f'{DRAW}/preview.png')
    print('preview ->', out, 'and', f'{DRAW}/preview.png')
    return out

# =============================================================== XML ==========
# Continuous per-hour seconds (smooth, only hitches on the hour)
T   = '([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
BPM = '(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 220))'
BEAT= f'abs(sin({T} * {BPM} * 0.05236))'
PX  = 'clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'
PY  = 'clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'

def _box(cx, cy, w, h):
    return int(cx - w/2), int(cy - h/2), int(w), int(h)

def _partimg(name, res, cx, cy, w, h, alpha=255, pivot=None, extra='', children=''):
    x, y, W, H = _box(cx, cy, w, h)
    piv = f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"' if pivot else ''
    return (f'    <PartImage name="{name}" x="{x}" y="{y}" width="{W}" height="{H}" '
            f'alpha="{alpha}"{piv}{extra}>\n{children}      <Image resource="{res}" />\n'
            f'    </PartImage>\n')

def _ptext(name, cx, cy, w, h, s, fam, size, color, align='CENTER',
          template=None, param=None, upper=False, extra='', variant='', xf=''):
    x, y, W, H = _box(cx, cy, w, h)
    if template is not None:
        inner = f'<Template>{template}'
        if isinstance(param, (list, tuple)):
            for p in param: inner += f'<Parameter expression="{p}" />'
        elif param:
            inner += f'<Parameter expression="{param}" />'
        inner += '</Template>'
        if upper: inner = f'<Upper>{inner}</Upper>'
    else:
        inner = f'<Upper>{s}</Upper>' if upper else s
    return (f'    <PartText name="{name}" x="{x}" y="{y}" width="{W}" height="{H}"{extra}>\n'
            f'{variant}{xf}      <Text align="{align}">\n'
            f'        <Font family="{fam}" size="{size}" color="{color}">{inner}</Font>\n'
            f'      </Text>\n    </PartText>\n')

def V(target, value, dur=1.0, off=0.0, interp='LINEAR'):
    return (f'      <Variant mode="AMBIENT" target="{target}" value="{value}" '
            f'duration="{dur}" startOffset="{off}" interpolation="{interp}" />\n')

def XF(target, value):
    return f'      <Transform target="{target}" value="{value}" />\n'

def gen_xml():
    def cx(k): return L[k][0]
    def cy(k): return L[k][1]
    out = []
    out.append('<?xml version="1.0" encoding="utf-8"?>\n'
               '<WatchFace width="480" height="480">\n'
               '  <Metadata key="CLOCK_TYPE" value="DIGITAL" />\n'
               '  <Metadata key="PREVIEW_TIME" value="10:08:32" />\n'
               f'  <Scene backgroundColor="#FF05070C">\n')

    # ---- L0 city (interactive) + AOD ghost, crossfade + parallax -----------
    out.append(_partimg('z00_bg', 'bg', 240, 240, 480, 480, 255,
        extra='',
        children=V('alpha', '0', 0.45, 0.0, 'EASE_OUT')
               + XF('x', f'0 + 6 * {PX}') + XF('y', f'0 + 6 * {PY}')))
    out.append(_partimg('z00_bg_aod', 'bg_aod', 240, 240, 480, 480, 0,
        children=V('alpha', '255', 0.45, 0.0, 'EASE_IN')))

    # ---- moon halo (breathing, interactive only) --------------------------
    out.append(_partimg('z01_moon', 'moonglow', 240, 250, 300, 300, 0, pivot=('0.5','0.5'),
        children=V('alpha', '0', 0.4, 0.05)
               + XF('alpha', f'150 + 70 * abs(sin({T} * 0.6))')
               + XF('scaleX', f'1 + 0.05 * abs(sin({T} * 0.6))')
               + XF('scaleY', f'1 + 0.05 * abs(sin({T} * 0.6))')))

    # ---- rim ticks --------------------------------------------------------
    out.append(_partimg('z02_rim', 'rim', 240, 240, 480, 480, 200,
        children=V('alpha', '70', 0.4, 0.1) + XF('x', f'0 + 3 * {PX}') + XF('y', f'0 + 3 * {PY}')))

    # ---- rain (scroll, interactive only) ----------------------------------
    out.append(_partimg('z03_rain', 'rain', 240, 240, 480, 960, 150,
        children=V('alpha', '0', 0.3, 0.12)
               + XF('y', f'-480 + (({T} * 190) % 480)') + XF('x', f'0 - 3 * {PX}')))

    # ---- battery arc (left rim, sweeps open on wake) ----------------------
    b = BATT_ARC
    out.append(_partimg('z04_batt_track', 'batt_track', 240, 240, 480, 480, 130,
        children=V('alpha', '0', 0.3, 0.18)))
    out.append('    <PartDraw name="z04_batt" x="0" y="0" width="480" height="480">\n'
        + V('alpha', '0', 0.5, 0.2, 'OVERSHOOT')
        + f'      <Arc centerX="{b["cx"]}" centerY="{b["cy"]}" width="{b["r"]*2}" height="{b["r"]*2}" '
          f'startAngle="{b["a0"]}" endAngle="{b["a1"]}" direction="CLOCKWISE">\n'
        + f'        <Transform target="endAngle" value="{b["a0"]} + {b["a1"]-b["a0"]} * [BATTERY_PERCENT] / 100" />\n'
        + f'        <Stroke color="{MAGENTA}" thickness="{b["th"]}" cap="ROUND" />\n'
        + '      </Arc>\n    </PartDraw>\n')

    # ---- step-goal arc (top rim, crosses 12) ------------------------------
    s = STEP_ARC
    out.append(_partimg('z04_step_track', 'step_track', 240, 240, 480, 480, 120,
        children=V('alpha', '0', 0.3, 0.22)))
    out.append('    <PartDraw name="z04_step" x="0" y="0" width="480" height="480">\n'
        + V('alpha', '0', 0.5, 0.24, 'OVERSHOOT')
        + f'      <Arc centerX="{s["cx"]}" centerY="{s["cy"]}" width="{s["r"]*2}" height="{s["r"]*2}" '
          f'startAngle="{s["a0"]}" endAngle="{s["a0"]+84}" direction="CLOCKWISE">\n'
        + f'        <Transform target="endAngle" value="{s["a0"]} + 84 * clamp([STEP_PERCENT], 0, 100) / 100" />\n'
        + f'        <Stroke color="{CYAN}" thickness="{s["th"]}" cap="ROUND" />\n'
        + '      </Arc>\n    </PartDraw>\n')

    # ---- digit glows ------------------------------------------------------
    out.append(_partimg('z05_hglow', 'glow_cyan', cx('hglow'), cy('hglow'), 260, 200, 0,
        children=V('alpha', '0', 0.4, 0.1)))
    out.append(_partimg('z05_mglow', 'glow_mag', cx('mglow'), cy('mglow'), 260, 200, 0,
        children=V('alpha', '0', 0.4, 0.12)))

    # ---- BIG TIME ---------------------------------------------------------
    hx0, hy0, hw, hh = _box(cx('hour'), cy('hour'), 150, 132)
    out.append(f'    <Group name="z06_hour" x="{hx0}" y="{hy0}" width="{hw}" height="{hh}" alpha="255">\n'
        + V('alpha', '150', 0.35, 0.05, 'EASE_OUT')
        + XF('x', f'{hx0} + 4 * {PX}')
        + f'      <DigitalClock x="0" y="0" width="{hw}" height="{hh}">\n'
        + f'        <TimeText format="hh" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="0" width="{hw}" height="{hh}">\n'
        + f'          <Font family="{F_DISP}" size="100" color="{WHITE}" />\n'
        + '        </TimeText>\n      </DigitalClock>\n    </Group>\n')

    mx0, my0, mw, mh = _box(cx('minute'), cy('minute'), 150, 132)
    out.append(f'    <Group name="z06_min" x="{mx0}" y="{my0}" width="{mw}" height="{mh}" alpha="255">\n'
        + V('alpha', '150', 0.35, 0.06, 'EASE_OUT')
        + XF('x', f'{mx0} + 4 * {PX}')
        + f'      <DigitalClock x="0" y="0" width="{mw}" height="{mh}">\n'
        + f'        <TimeText format="mm" align="CENTER" x="0" y="0" width="{mw}" height="{mh}">\n'
        + f'          <Font family="{F_DISP}" size="100" color="{MAGENTA}" />\n'
        + '        </TimeText>\n      </DigitalClock>\n    </Group>\n')

    # pulsing colon
    out.append(_ptext('z06_colon', cx('colon'), cy('colon'), 40, 120, ':', F_DISP, 88, MAGENTA,
        variant=V('alpha', '0', 0.3, 0.05),
        xf=XF('alpha', f'120 + 135 * abs(sin([SECOND] * 3.14159))')))

    out.append(_ptext('z06_ampm', cx('ampm'), cy('ampm'), 60, 34, 'PM', F_LABELB, 24, MAGENTA,
        template='%s', param='[AMPM_STRING]', variant=V('alpha', '0', 0.3, 0.14)))

    sx0, sy0, sw, sh = _box(cx('secs'), cy('secs'), 60, 44)
    out.append(f'    <Group name="z06_sec" x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" alpha="255">\n'
        + V('alpha', '0', 0.3, 0.14)
        + f'      <DigitalClock x="0" y="0" width="{sw}" height="{sh}">\n'
        + f'        <TimeText format="ss" align="CENTER" x="0" y="0" width="{sw}" height="{sh}">\n'
        + f'          <Font family="{F_LABELB}" size="32" color="{WHITE}" />\n'
        + '        </TimeText>\n      </DigitalClock>\n    </Group>\n')

    # ---- sub-brand --------------------------------------------------------
    out.append(_ptext('z07_x1c7', cx('x1c7'), cy('x1c7'), 200, 40, 'X1c7', F_DISP, 30, CYAN,
        variant=V('alpha', '0', 0.4, 0.34, 'EASE_OUT'),
        extra=''))
    out.append(_partimg('z07_kanji', 'k_senshi', cx('kanji'), cy('kanji'), 150, 56, 255,
        children=V('alpha', '0', 0.4, 0.38, 'EASE_OUT')))

    # ---- top bar ----------------------------------------------------------
    out.append(_partimg('z08_mask', 'mask', cx('mask'), cy('mask'), 46, 46, 255,
        children=V('alpha', '0', 0.35, 0.4)))
    out.append(_ptext('z08_sat', cx('sat'), cy('sat'), 160, 34, None, F_DISP2, 26, MAGENTA,
        template='%s', param='[DAY_OF_WEEK_S]', upper=True,
        variant=V('alpha', '0', 0.35, 0.42)))
    out.append(_ptext('z08_date', cx('date'), cy('date'), 200, 30, None, F_LABEL, 23, WHITE,
        template='%s %d', param=['[MONTH_S]', '[DAY]'], upper=True,
        variant=V('alpha', '0', 0.35, 0.44)))
    out.append(_partimg('z08_moon', 'moon', cx('wx_icon'), cy('wx_icon'), 30, 30, 255,
        children=V('alpha', '0', 0.35, 0.46)))
    out.append(_ptext('z08_temp', cx('wx_temp'), cy('wx_temp'), 70, 30, None, F_LABEL, 24, CYAN,
        template='%d°', param='round([WEATHER.TEMPERATURE])',
        variant=V('alpha', '0', 0.35, 0.46)))

    # ---- battery / bpm readouts ------------------------------------------
    out.append(_ptext('z09_batt', cx('batt_val'), cy('batt_val'), 90, 34, None, F_DISP2, 24, WHITE,
        template='%d%%', param='[BATTERY_PERCENT]', variant=V('alpha', '0', 0.35, 0.5)))
    out.append(_ptext('z09_batt_l', cx('batt_lbl'), cy('batt_lbl'), 90, 22, 'BATTERY', F_LABEL, 15, MAGENTA,
        variant=V('alpha', '0', 0.35, 0.52)))
    out.append(_partimg('z09_heart', 'heart', cx('bpm_icon'), cy('bpm_icon'), 26, 26, 255,
        children=V('alpha', '0', 0.35, 0.5) + XF('alpha', f'70 + 185 * {BEAT}')))
    out.append(_ptext('z09_bpm', cx('bpm_val'), cy('bpm_val'), 60, 34, None, F_DISP2, 24, RED,
        template='%d', param='[HEART_RATE]', variant=V('alpha', '0', 0.35, 0.52)))
    out.append(_ptext('z09_bpm_l', cx('bpm_lbl'), cy('bpm_lbl'), 60, 22, 'BPM', F_LABEL, 15, MAGENTA,
        variant=V('alpha', '0', 0.35, 0.54)))
    out.append(_partimg('z09_ecg', 'ecg', cx('ecg'), cy('ecg'), 64, 30, 220,
        children=V('alpha', '0', 0.35, 0.54)))

    # ---- steps / cal (complication) / distance (complication) -------------
    out.append(_partimg('z10_shoe', 'shoe', cx('steps_icon'), cy('steps_icon'), 32, 26, 255,
        children=V('alpha', '0', 0.35, 0.56)))
    out.append(_ptext('z10_steps', cx('steps_val'), cy('steps_val'), 90, 34, None, F_DISP2, 24, WHITE,
        template='%d', param='[STEP_COUNT]', variant=V('alpha', '0', 0.35, 0.56)))
    out.append(_ptext('z10_steps_l', cx('steps_lbl'), cy('steps_lbl'), 80, 22, 'STEPS', F_LABEL, 15, CYAN,
        variant=V('alpha', '0', 0.35, 0.58)))
    out.append(_partimg('z10_fire', 'fire', cx('cal_icon'), cy('cal_icon'), 26, 30, 255,
        children=V('alpha', '0', 0.35, 0.56)))
    out.append(_ptext('z10_cal_l', cx('cal_lbl'), cy('cal_lbl'), 60, 22, 'CAL', F_LABEL, 15, AMBER,
        variant=V('alpha', '0', 0.35, 0.58)))

    # ---- distance + torii -------------------------------------------------
    out.append(_ptext('z11_dist_l', cx('dist_lbl'), cy('dist_lbl'), 130, 22, 'DISTANCE', F_LABEL, 15, MUTE,
        variant=V('alpha', '0', 0.35, 0.6)))
    out.append(_partimg('z11_torii', 'torii', cx('torii'), cy('torii'), 48, 34, 255, pivot=('0.5','0.5'),
        children=V('alpha', '0', 0.5, 0.62, 'OVERSHOOT')
               + V('scaleX', '0.2', 0.5, 0.62, 'OVERSHOOT')
               + V('scaleY', '0.2', 0.5, 0.62, 'OVERSHOOT')))

    # ---- scanlines (top, always subtle) -----------------------------------
    out.append(_partimg('z12_scan', 'scan', 240, 240, 480, 480, 90,
        children=V('alpha', '40', 0.3, 0.0)))

    # ---- Calories complication (tap zone, right) --------------------------
    ccx, ccy = cx('cal_val'), cy('cal_val')
    out.append(f'    <ComplicationSlot name="cal_slot" x="{ccx-45}" y="{ccy-20}" width="90" height="40" '
               'slotId="1001" supportedTypes="SHORT_TEXT">\n'
               '      <DefaultProviderPolicy defaultSystemProvider="STEP_COUNT" defaultSystemProviderType="SHORT_TEXT" />\n'
               f'      <BoundingBox x="{ccx-45}" y="{ccy-20}" width="90" height="40" />\n'
               '      <Complication type="SHORT_TEXT" />\n'
               '    </ComplicationSlot>\n')
    # ---- Distance complication (tap zone, bottom) -------------------------
    dcx, dcy = cx('dist_val'), cy('dist_val')
    out.append(f'    <ComplicationSlot name="dist_slot" x="{dcx-60}" y="{dcy-18}" width="120" height="36" '
               'slotId="1002" supportedTypes="SHORT_TEXT">\n'
               '      <DefaultProviderPolicy defaultSystemProvider="STEP_COUNT" defaultSystemProviderType="SHORT_TEXT" />\n'
               f'      <BoundingBox x="{dcx-60}" y="{dcy-18}" width="120" height="36" />\n'
               '      <Complication type="SHORT_TEXT" />\n'
               '    </ComplicationSlot>\n')

    out.append('  </Scene>\n</WatchFace>\n')
    xml = ''.join(out)
    with open(f'{RES}/raw/watchface.xml', 'w') as f:
        f.write(xml)
    print('watchface.xml written:', len(xml), 'bytes')

# =============================================================== ANIMATE ======
def _ease(kind, x):
    x = max(0.0, min(1.0, x))
    if kind=='EASE_OUT':  return 1-(1-x)**2
    if kind=='EASE_IN':   return x*x
    if kind=='EASE_IN_OUT': return 3*x*x-2*x*x*x
    if kind=='OVERSHOOT':
        c=2.4; y=x-1; return 1+(c+1)*y**3+c*y**2
    return x

def _sprite(fn):
    lay=Image.new('RGBA',(S,S),(0,0,0,0)); d=ImageDraw.Draw(lay); fn(lay,d); return lay

def _rain_at(off):
    r=Image.open(f'{NODPI}/rain.png').convert('RGBA')
    y=int(-480+(off%480)); lay=Image.new('RGBA',(S,S),(0,0,0,0))
    lay.alpha_composite(r,(0,y)); return lay

def animate(save='bushido_reveal.gif'):
    def arc_sprite(cfg,pct,color,th=None):
        def fn(lay,d):
            c=cfg; r=c['r']; a0=c['a0']; span=(c['a1']-c['a0'])%360
            d.arc([c['cx']-r,c['cy']-r,c['cx']+r,c['cy']+r],a0-90,a0-90+span*pct,
                  fill=hx(color),width=th or c['th'])
        return _sprite(fn)
    def img_sprite(name,cx,cy):
        def fn(lay,d): _paste(lay,name,cx,cy)
        return _sprite(fn)
    def txt_sprite(cx,cy,s,fam,size,color):
        def fn(lay,d): _text(d,cx,cy,s,fam,size,color)
        return _sprite(fn)

    # static sprites (built once)
    rim=Image.open(f'{NODPI}/rim.png').convert('RGBA')
    scan=Image.open(f'{NODPI}/scan.png').convert('RGBA')
    bg=Image.open(f'{NODPI}/bg.png').convert('RGBA')
    aod=Image.open(f'{NODPI}/bg_aod.png').convert('RGBA')
    S_batt=arc_sprite(BATT_ARC,1.0,MAGENTA); S_bt=img_sprite('batt_track',240,240)
    S_step=arc_sprite(STEP_ARC,0.62,CYAN);   S_st=img_sprite('step_track',240,240)
    S_hg=img_sprite('glow_cyan',*L['hglow'][:2]); S_mg=img_sprite('glow_mag',*L['mglow'][:2])
    S_hour=txt_sprite(*L['hour'],'10',F_DISP,100,WHITE)
    S_min =txt_sprite(*L['minute'],'08',F_DISP,100,MAGENTA)
    S_ampm=txt_sprite(*L['ampm'],'PM',F_LABELB,24,MAGENTA)
    S_sec =txt_sprite(*L['secs'],'38',F_LABELB,32,WHITE)
    S_x1c7=txt_sprite(*L['x1c7'],'X1c7',F_DISP,30,CYAN)
    S_kanji=img_sprite('k_senshi',*L['kanji'])
    S_mask=img_sprite('mask',L['mask'][0],L['mask'][1])
    S_sat=txt_sprite(*L['sat'],'SAT',F_DISP2,26,MAGENTA)
    S_date=txt_sprite(*L['date'],'MAY 24',F_LABEL,23,WHITE)
    S_wxi=img_sprite('moon',L['wx_icon'][0],L['wx_icon'][1])
    S_temp=txt_sprite(*L['wx_temp'],'20°',F_LABEL,24,CYAN)
    S_bv=txt_sprite(*L['batt_val'],'100%',F_DISP2,24,WHITE)
    S_bl=txt_sprite(*L['batt_lbl'],'BATTERY',F_LABEL,15,MAGENTA)
    S_bpm=txt_sprite(*L['bpm_val'],'78',F_DISP2,24,RED)
    S_bpl=txt_sprite(*L['bpm_lbl'],'BPM',F_LABEL,15,MAGENTA)
    S_ecg=img_sprite('ecg',*L['ecg'])
    S_shoe=img_sprite('shoe',L['steps_icon'][0],L['steps_icon'][1])
    S_sv=txt_sprite(*L['steps_val'],'7645',F_DISP2,24,WHITE)
    S_sl=txt_sprite(*L['steps_lbl'],'STEPS',F_LABEL,15,CYAN)
    S_fire=img_sprite('fire',L['cal_icon'][0],L['cal_icon'][1])
    S_cv=txt_sprite(*L['cal_val'],'1245',F_DISP2,24,WHITE)
    S_cl=txt_sprite(*L['cal_lbl'],'CAL',F_LABEL,15,AMBER)
    S_dl=txt_sprite(*L['dist_lbl'],'DISTANCE',F_LABEL,15,MUTE)
    S_dv=txt_sprite(*L['dist_val'],'5.62 KM',F_DISP2,22,WHITE)

    # (sprite, start, dur, interp, base_alpha_frac)
    SCHED=[
      (S_bt,.18,.30,'EASE_OUT',0),(S_batt,.20,.40,'OVERSHOOT',0),
      (S_st,.22,.30,'EASE_OUT',0),(S_step,.24,.40,'OVERSHOOT',0),
      (S_hg,.10,.40,'EASE_OUT',0),(S_mg,.12,.40,'EASE_OUT',0),
      (S_hour,.05,.35,'EASE_OUT',.59),(S_min,.06,.35,'EASE_OUT',.59),
      (S_ampm,.14,.30,'EASE_OUT',0),(S_sec,.14,.30,'EASE_OUT',0),
      (S_x1c7,.34,.40,'EASE_OUT',0),(S_kanji,.38,.40,'EASE_OUT',0),
      (S_mask,.40,.35,'EASE_OUT',0),(S_sat,.42,.35,'EASE_OUT',0),
      (S_date,.44,.35,'EASE_OUT',0),(S_wxi,.46,.35,'EASE_OUT',0),(S_temp,.46,.35,'EASE_OUT',0),
      (S_bv,.50,.35,'EASE_OUT',0),(S_bl,.52,.35,'EASE_OUT',0),
      (S_bpm,.52,.35,'EASE_OUT',0),(S_bpl,.54,.35,'EASE_OUT',0),(S_ecg,.54,.35,'EASE_OUT',0),
      (S_shoe,.56,.35,'EASE_OUT',0),(S_sv,.56,.35,'EASE_OUT',0),(S_sl,.58,.35,'EASE_OUT',0),
      (S_fire,.56,.35,'EASE_OUT',0),(S_cv,.56,.35,'EASE_OUT',0),(S_cl,.58,.35,'EASE_OUT',0),
      (S_dl,.60,.35,'EASE_OUT',0),(S_dv,.60,.35,'EASE_OUT',0),
    ]
    circ=Image.new('L',(S,S),0); ImageDraw.Draw(circ).ellipse([0,0,S,S],fill=255)

    def apply(base, spr, alpha):
        if alpha<=1: return
        a=spr.split()[3].point(lambda v:int(v*min(1.0,alpha/255)))
        s2=spr.copy(); s2.putalpha(a); base.alpha_composite(s2)

    frames=[]; fps=25
    HOLD=1.4; REV=1.15; PRE=0.24
    tt=0.0; total=PRE+REV+HOLD
    while tt<total:
        g=max(0.0,(tt-PRE)/REV)          # reveal progress 0..1
        base=Image.new('RGBA',(S,S),(0,0,0,255))
        # bg crossfade aod->bg
        ce=_ease('EASE_OUT',g/0.45 if g<0.45 else 1)
        base.alpha_composite(aod)
        bgc=bg.copy(); bgc.putalpha(bg.split()[3].point(lambda v:int(v*ce))); base.alpha_composite(bgc)
        # rim + rain (rain scrolls; fades in)
        re=_ease('EASE_OUT',(g-.10)/.30)
        if re>0:
            rr=rim.copy(); rr.putalpha(rim.split()[3].point(lambda v:int(v*(0.27+0.73*re)))); base.alpha_composite(rr)
        rainA=_ease('EASE_OUT',(g-.12)/.30)*0.6
        if rainA>0:
            rn=_rain_at(tt*190); rn.putalpha(rn.split()[3].point(lambda v:int(v*rainA))); base.alpha_composite(rn)
        # scheduled elements
        for spr,st,du,ki,bf in SCHED:
            e=_ease(ki,(g-st)/du)
            alpha=255*(bf+(1-bf)*e) if e>0 else (255*bf if bf>0 else 0)
            apply(base,spr,alpha)
        # colon pulse (after it appears)
        if g>0.05:
            cp=120+135*abs(math.sin(tt*math.pi))
            cs=txt_sprite(*L['colon'],':',F_DISP,88,MAGENTA); apply(base,cs,cp)
        # heart flash overlay when revealed
        base.alpha_composite(scan)
        base.putalpha(ImageChops.multiply(base.split()[3],circ))
        frames.append(base.convert('RGB').resize((320,320),Image.LANCZOS))
        tt+=1.0/fps

    outp=f'/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/{save}'
    frames[0].save(outp,save_all=True,append_images=frames[1:],
                   duration=int(1000/fps),loop=0,optimize=True)
    print('anim ->',outp,len(frames),'frames')
    return outp

if __name__=='__main__':
    stage = sys.argv[1] if len(sys.argv)>1 else 'all'
    if stage in ('assets','all'): gen_assets()
    if stage in ('xml','all'): gen_xml()
    if stage in ('preview','all'): compose_preview()
    if stage in ('anim','all'): animate()
