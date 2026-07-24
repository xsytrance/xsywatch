#!/usr/bin/env python3
"""ARES — WFF v4 (Galaxy Watch 7, 480x480). Keep the concept's carved icons/labels/
numerals baked; only enlarge the live/value numbers (carved BitmapFont). Wrath HR glow.
Stages: bg | glyphs | xml | preview | all."""
import sys, os, subprocess, json
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; FONT=f'{RES}/font'; S=480
IVORY=(236,227,206); SHADOW=(23,18,11); BRONZE=(190,156,96); MARC=f'{FONT}/marcellus.ttf'

DATE=(337,128,24); BATT=(320,360,18)   # analog: no digital time; battery centred in medallion
VAL_LEFT=55; VAL_SZ=20
# (live-expr | None, static-str, baked-value y-centre)  measured off the marble
VALS=[('[HEART_RATE]',None,120),(None,'512',168),('[STEP_COUNT]',None,209),
      (None,'6.21',245),(None,'48',290),(None,'7h 36m',335)]

CHARS={**{str(d):str(d) for d in range(10)}, ':':'colon','%':'pct','.':'dot',' ':'space',
       **{c:c.lower() for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'},
       **{c:c+'_' for c in 'abcdefghijklmnopqrstuvwxyz'}}
FS=64
def gen_glyphs():
    f=ImageFont.truetype(MARC,FS); asc,desc=f.getmetrics(); H=asc+desc; meta={}
    for ch,rn in CHARS.items():
        if ch==' ':
            w=int(FS*0.28); im=Image.new('RGBA',(w,H),(0,0,0,0))
        else:
            w=max(6,int(round(f.getlength(ch)))+6); im=Image.new('RGBA',(w,H),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.text((5,asc+3),ch,font=f,fill=SHADOW+(235,),anchor='ls')
            d.text((3,asc),ch,font=f,fill=IVORY+(255,),anchor='ls')
        nm=f'g_{rn}'; im.save(f'{NODPI}/{nm}.png'); meta[ch]=(nm,w,H)
    json.dump(meta,open(f'{ROOT}/tools/glyphs.json','w')); print('glyphs',len(meta),'H',H)
def _meta(): return json.load(open(f'{ROOT}/tools/glyphs.json'))

def gen_hands():
    ss=4; C=240*ss
    def hand(length,bw,tw,tail,name):
        im=Image.new('RGBA',(480*ss,480*ss),(0,0,0,0)); d=ImageDraw.Draw(im); ty=C-length*ss
        d.polygon([(C-bw/2*ss,C),(C-tw/2*ss,ty+9*ss),(C,ty-12*ss),(C+tw/2*ss,ty+9*ss),(C+bw/2*ss,C),
                   (C+bw*0.42*ss,C+tail*ss),(C-bw*0.42*ss,C+tail*ss)],fill=IVORY+(255,))
        d.line([(C,C+tail*ss),(C,ty-4*ss)],fill=BRONZE+(255,),width=int(3.2*ss))  # bronze rib
        im=im.resize((480,480),Image.LANCZOS)
        a=im.split()[3]; sh=Image.new('RGBA',(480,480),SHADOW+(0,)); sh.putalpha(a.point(lambda v:int(v*0.7)))
        out=Image.new('RGBA',(480,480),(0,0,0,0)); out.alpha_composite(sh,(2,3)); out.alpha_composite(im)
        out.save(f'{NODPI}/{name}.png')
    hand(124,22,8,26,'hour_hand'); hand(180,15,5,30,'min_hand')
    hb=Image.new('RGBA',(72,72),(0,0,0,0)); hd=ImageDraw.Draw(hb)
    hd.ellipse([12,13,60,61],fill=SHADOW+(200,)); hd.ellipse([10,10,58,58],fill=BRONZE+(255,))
    hd.ellipse([21,21,47,47],fill=(224,192,132,255)); hd.ellipse([29,29,39,39],fill=SHADOW+(255,))
    hb.save(f'{NODPI}/hub.png'); print('hands: hour, minute, hub')

# ---------------- preview ----------------
def _str(b,s,cx,cy,size,anchor='center'):
    m=_meta(); H=list(m.values())[0][2]; sc=size/H; gl=[]; tot=0
    for ch in s:
        if ch not in m: ch=' '
        nm,w,h=m[ch]; gw=w*sc; gl.append((nm,gw)); tot+=gw
    x=cx-tot/2 if anchor=='center' else (cx if anchor=='start' else cx-tot)
    for nm,gw in gl:
        g=Image.open(f'{NODPI}/{nm}.png').convert('RGBA').resize((max(1,int(gw)),int(size)),Image.LANCZOS)
        b.alpha_composite(g,(int(x),int(cy-size/2))); x+=gw
def compose_preview(t='10:09:30'):
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA'); hh,mm,ss=[int(x) for x in t.split(':')]
    _str(b,'SUN 20',*DATE); _str(b,'86%',*BATT)
    demo={'[HEART_RATE]':'72','[STEP_COUNT]':'8426'}
    for live,stat,y in VALS: _str(b,demo.get(live,stat),VAL_LEFT,y,VAL_SZ,anchor='start')
    # analog hands (WFF angle = CW from 12; PIL rotate is CCW)
    ha=((hh%12)+mm/60)*30; ma=(mm+ss/60)*6
    for name,ang in (('hour_hand',ha),('min_hand',ma)):
        h=Image.open(f'{NODPI}/{name}.png').convert('RGBA').rotate(-ang,center=(240,240),resample=Image.BICUBIC)
        b.alpha_composite(h)
    hub=Image.open(f'{NODPI}/hub.png').convert('RGBA'); b.alpha_composite(hub,(240-36,240-36))
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255)
    b.putalpha(ImageChops.multiply(b.split()[3],m)); b.save(f'{DRAW}/preview.png')
    out='/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/ares_preview.png'
    b.convert('RGB').save(out); print('preview ->',out)

# ---------------- WFF xml ----------------
PX='clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'; PY='clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
Tm='([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
def Vr(t,v,dur=1.0,off=0.0,ip='LINEAR'): return f'      <Variant mode="AMBIENT" target="{t}" value="{v}" duration="{dur}" startOffset="{off}" interpolation="{ip}" />\n'
def XF(t,v): return f'      <Transform target="{t}" value="{v}" />\n'
def img(name,res,cx,cy,w,h,alpha,kids='',pivot=None):
    piv=f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"' if pivot else ''
    return f'    <PartImage name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}" alpha="{alpha}"{piv}>\n{kids}      <Image resource="{res}" />\n    </PartImage>\n'
def bffonts():
    m=_meta(); esc={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}; rows=''
    for ch,(nm,w,h) in m.items(): rows+=f'      <Character name="{esc.get(ch,ch)}" resource="{nm}" width="{w}" height="{h}" />\n'
    return '  <BitmapFonts>\n    <BitmapFont name="carved">\n'+rows+'    </BitmapFont>\n  </BitmapFonts>\n'
def bf(sz): return f'<BitmapFont family="carved" size="{sz}" color="#FFFFFF" />'
def part(name,x,y,w,h,size,off,tmpl=None,params=None,upper=False,s=None,align='CENTER',color='#FFFFFF'):
    if tmpl is not None:
        inner='<Template>'+tmpl
        for p in (params or []): inner+=f'<Parameter expression="{p}" />'
        inner+='</Template>'
    else: inner=s
    if upper: inner=f'<Upper>{inner}</Upper>'
    return (f'    <PartText name="{name}" x="{x}" y="{y}" width="{w}" height="{h}">\n'+Vr('alpha','0',0.4,off)
            +f'      <Text align="{align}"><BitmapFont family="carved" size="{size}" color="{color}">{inner}</BitmapFont></Text>\n    </PartText>\n')

def gen_xml():
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="DIGITAL" />\n  <Metadata key="PREVIEW_TIME" value="10:09:32" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF080706">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.5,0,'EASE_OUT')+XF('x',f'0 + 4 * {PX}')+XF('y',f'0 + 4 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.5,0,'EASE_IN')))
    o.append(img('z01_wrath','wrath',240,240,480,480,0,kids=Vr('alpha','0',0.4,0.05)+XF('alpha',f'clamp(([HEART_RATE] - 78) * 2.2, 0, 95)')))
    o.append(img('z02_sheen','sheen',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.1,'EASE_OUT')+XF('alpha',f'100 + 40 * abs(sin({Tm} * 0.5))')+XF('x',f'0 + 55 * {PX}')))
    o.append(part('z11_date',DATE[0]-85,DATE[1]-16,170,32,DATE[2],0.22,tmpl='%s %d',params=['[DAY_OF_WEEK_S]','[DAY]'],upper=True))
    for i,(live,stat,y) in enumerate(VALS):
        off=0.26+i*0.03
        if live: o.append(part(f'z20_v{i}',VAL_LEFT,y-16,90,32,VAL_SZ,off,tmpl='%d',params=[live],align='START'))
        else:    o.append(part(f'z20_v{i}',VAL_LEFT,y-16,90,32,VAL_SZ,off,s=stat,align='START'))
    # battery centred in the shield medallion, muted to blend with the carving
    o.append(part('z30_batt',BATT[0]-35,BATT[1]-16,70,32,BATT[2],0.4,tmpl='%d%%',params=['[BATTERY_PERCENT]'],color='#D6C8A4'))
    # LIVE analog hands (dim in ambient) + centre hub on top
    o.append(img('z40_hour','hour_hand',240,240,480,480,255,pivot=('0.5','0.5'),
        kids=Vr('alpha','185',0.4,0.0)+XF('angle','([HOUR_0_11] + [MINUTE] / 60) * 30')))
    o.append(img('z41_min','min_hand',240,240,480,480,255,pivot=('0.5','0.5'),
        kids=Vr('alpha','185',0.4,0.0)+XF('angle','([MINUTE] + [SECOND] / 60) * 6')))
    o.append(img('z42_hub','hub',240,240,72,72,255,kids=Vr('alpha','185',0.4,0.0)))
    o.append('  </Scene>\n</WatchFace>\n')
    xml=''.join(o); open(f'{RES}/raw/watchface.xml','w').write(xml); print('watchface.xml',len(xml),'bytes')

if __name__=='__main__':
    st=sys.argv[1] if len(sys.argv)>1 else 'all'
    if st in ('bg','all'): subprocess.run(['python3',f'{ROOT}/tools/bg.py'],check=True)
    if st in ('glyphs','all'): gen_glyphs()
    if st in ('hands','all'): gen_hands()
    if st in ('xml','all'): gen_xml()
    if st in ('preview','all'): compose_preview()
