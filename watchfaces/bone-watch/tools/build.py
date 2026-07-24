#!/usr/bin/env python3
"""BONE WATCH — WFF v4 (Galaxy Watch 7, 480x480). Gothic memento-mori: AI bone dial
(ComfyUI/Juggernaut, UI-free), carved bone hands, blood-red HR ember in the eye sockets,
carved-bone BitmapFont. Stages: bg | glyphs | hands | xml | preview | all."""
import sys, os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; FONT=f'{RES}/font'; S=480
os.makedirs(NODPI,exist_ok=True); os.makedirs(DRAW,exist_ok=True)
DIAL=f'{ROOT}/tools/bonewatch_00001_.png'
BONE=(232,223,200); BONE_HI=(245,239,223); BONE_SH=(70,60,46); SHADOW=(24,18,12)
RED=(150,20,20); RED_HI=(210,40,32); MARC=f'{FONT}/marcellus.ttf'
EYE_L=(195,214); EYE_R=(285,214)         # eye sockets (HR ember)
DATEV=(240,366); LEFTV=(198,390); BATTV=(282,390)   # readouts in the jaw→VI clear band

# ------------------------------------------------------------------ BG
def gen_bg():
    d=Image.open(DIAL).convert('RGB').resize((S,S),Image.LANCZOS)
    d=ImageEnhance.Contrast(d).enhance(1.06); d=ImageEnhance.Color(d).enhance(1.04)
    # gentle rim vignette
    vig=Image.new('L',(S,S),0); vd=ImageDraw.Draw(vig)
    for rr in range(S//2,0,-1):
        t=rr/(S/2); vd.ellipse([S/2-rr,S/2-rr,S/2+rr,S/2+rr],fill=int(255*(1-0.35*t**3)))
    vig=vig.filter(ImageFilter.GaussianBlur(6)); d=Image.composite(d,Image.new('RGB',(S,S),(6,4,3)),vig)
    d.save(f'{NODPI}/bg.png')
    aod=ImageEnhance.Brightness(d).enhance(0.34); aod=ImageEnhance.Color(aod).enhance(0.55); aod.save(f'{NODPI}/bg_aod.png')
    # blood ember (one socket) — additive red glow, pulsed by HR in WFF
    for name,rr in (('ember',30),):
        e=Image.new('RGBA',(84,84),(0,0,0,0)); ed=ImageDraw.Draw(e)
        for r in range(40,0,-1):
            a=int(200*(1-r/40)**2.0); ed.ellipse([42-r,42-r,42+r,42+r],fill=RED_HI+(a,))
        e.filter(ImageFilter.GaussianBlur(6)).save(f'{NODPI}/{name}.png')
    # raking candle sheen
    sh=Image.new('RGBA',(S,S),(0,0,0,0)); ImageDraw.Draw(sh).polygon([(-120,0),(70,0),(230,480),(50,480)],fill=(255,244,214,34))
    sh.filter(ImageFilter.GaussianBlur(50)).save(f'{NODPI}/sheen.png')
    print('bg: bg, bg_aod, ember, sheen')

# ------------------------------------------------------------------ HANDS
def gen_hands():
    ss=4; C=240*ss
    def bone(length,shaft,knob,tail,name,tint=None):
        im=Image.new('RGBA',(480*ss,480*ss),(0,0,0,0)); dr=ImageDraw.Draw(im)
        ty=C-length*ss; col=(tint or BONE)+(255,)
        # shaft
        dr.line([(C,C+tail*ss),(C,ty+knob*ss)],fill=col,width=int(shaft*ss))
        # top epiphysis (two lobes = bone head)
        dr.ellipse([C-knob*ss,ty,C-knob*0.05*ss,ty+knob*1.8*ss],fill=col)
        dr.ellipse([C+knob*0.05*ss,ty,C+knob*ss,ty+knob*1.8*ss],fill=col)
        dr.ellipse([C-knob*0.7*ss,ty+knob*0.4*ss,C+knob*0.7*ss,ty+knob*1.9*ss],fill=col)
        # base counterweight knob
        dr.ellipse([C-knob*0.9*ss,C+tail*ss-knob*ss,C+knob*0.9*ss,C+tail*ss+knob*0.7*ss],fill=col)
        im=im.resize((480,480),Image.LANCZOS)
        # shading: darker lower-right, light upper-left rib
        a=im.split()[3]
        sh=Image.new('RGBA',(480,480),BONE_SH+(0,)); sh.putalpha(a.point(lambda v:int(v*0.55)))
        hi=Image.new('RGBA',(480,480),BONE_HI+(0,)); hi.putalpha(a.point(lambda v:int(v*0.5)))
        out=Image.new('RGBA',(480,480),(0,0,0,0))
        drop=Image.new('RGBA',(480,480),SHADOW+(0,)); drop.putalpha(a.point(lambda v:int(v*0.8)))
        out.alpha_composite(drop,(3,4)); out.alpha_composite(im)
        out.alpha_composite(sh,(2,3)); out.alpha_composite(hi,(-1,-2))
        out.save(f'{NODPI}/{name}.png')
    bone(120,11,10,26,'hour_hand')
    bone(176,8,8,30,'min_hand')
    bone(196,4,4,34,'sec_hand',tint=RED_HI)
    # hub: bone knob with a red core (little eye)
    hb=Image.new('RGBA',(64,64),(0,0,0,0)); hd=ImageDraw.Draw(hb)
    hd.ellipse([12,13,54,55],fill=SHADOW+(200,)); hd.ellipse([10,10,52,52],fill=BONE+(255,))
    hd.ellipse([19,19,43,43],fill=BONE_HI+(255,)); hd.ellipse([25,25,39,39],fill=RED+(255,)); hd.ellipse([28,28,36,36],fill=RED_HI+(255,))
    hb.save(f'{NODPI}/hub.png'); print('hands: hour, minute, second, hub')

# ------------------------------------------------------------------ ROMAN NUMERALS (carved bone)
ROMANS=['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']
def gen_numerals(r=208, size=34):
    dial=Image.open(DIAL).convert('RGB').resize((S,S),Image.LANCZOS)
    tex=dial.crop((196,20,284,64)).resize((70,70),Image.LANCZOS)   # clean bone patch (top bezel)
    f=ImageFont.truetype(MARC,size)
    ring=Image.new('RGBA',(S,S),(0,0,0,0))
    for i,rn in enumerate(ROMANS):
        a=math.radians(i*30); cx=240+r*math.sin(a); cy=240-r*math.cos(a)
        bb=f.getbbox(rn); w=bb[2]-bb[0]; h=bb[3]-bb[1]; pad=10
        gm=Image.new('L',(w+pad*2,h+pad*2),0); ImageDraw.Draw(gm).text((pad-bb[0],pad-bb[1]),rn,font=f,fill=255)
        W,Hh=gm.size
        # fill glyph with bone texture; carve = dark drop + light top-left rib
        body=Image.new('RGBA',(W,Hh),(0,0,0,0)); body.paste(tex.resize((W,Hh)),(0,0),gm)
        cell=Image.new('RGBA',(W+6,Hh+6),(0,0,0,0))
        drop=Image.new('RGBA',(W,Hh),SHADOW+(0,)); drop.putalpha(gm.point(lambda v:int(v*0.85)))
        hi=Image.new('RGBA',(W,Hh),BONE_HI+(0,)); hi.putalpha(gm.point(lambda v:int(v*0.55)))
        cell.alpha_composite(drop,(4,5)); cell.alpha_composite(body,(3,3)); cell.alpha_composite(hi,(1,1))
        ring.alpha_composite(cell,(int(cx-cell.width/2),int(cy-cell.height/2)))
    ring.save(f'{NODPI}/numerals.png'); print('numerals: carved bone I-XII @ r',r)

# ------------------------------------------------------------------ GLYPHS (carved bone)
CHARS={**{str(d):str(d) for d in range(10)}, ':':'colon','%':'pct','.':'dot',' ':'space',
       **{c:c.lower() for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'},
       **{c:c+'_' for c in 'abcdefghijklmnopqrstuvwxyz'}}
FS=60
def gen_glyphs():
    f=ImageFont.truetype(MARC,FS); asc,desc=f.getmetrics(); H=asc+desc; meta={}
    for ch,rn in CHARS.items():
        if ch==' ':
            w=int(FS*0.28); im=Image.new('RGBA',(w,H),(0,0,0,0))
        else:
            w=max(6,int(round(f.getlength(ch)))+6); im=Image.new('RGBA',(w,H),(0,0,0,0)); dd=ImageDraw.Draw(im)
            dd.text((5,asc+3),ch,font=f,fill=SHADOW+(230,),anchor='ls')
            dd.text((3,asc),ch,font=f,fill=BONE_HI+(255,),anchor='ls')
        nm=f'g_{rn}'; im.save(f'{NODPI}/{nm}.png'); meta[ch]=(nm,w,H)
    json.dump(meta,open(f'{ROOT}/tools/glyphs.json','w')); print('glyphs',len(meta),'H',H)
def _meta(): return json.load(open(f'{ROOT}/tools/glyphs.json'))

# ------------------------------------------------------------------ PREVIEW
def _str(b,s,cx,cy,size,anchor='center'):
    m=_meta(); H=list(m.values())[0][2]; sc=size/H; gl=[]; tot=0
    for ch in s:
        if ch not in m: ch=' '
        nm,w,h=m[ch]; gw=w*sc; gl.append((nm,gw)); tot+=gw
    x=cx-tot/2 if anchor=='center' else (cx if anchor=='start' else cx-tot)
    for nm,gw in gl:
        g=Image.open(f'{NODPI}/{nm}.png').convert('RGBA').resize((max(1,int(gw)),int(size)),Image.LANCZOS)
        b.alpha_composite(g,(int(x),int(cy-size/2))); x+=gw
def _paste(b,name,cx,cy):
    im=Image.open(f'{NODPI}/{name}.png').convert('RGBA'); b.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

def compose_preview(t='10:09:34'):
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA'); hh,mm,ss=[int(x) for x in t.split(':')]
    _paste(b,'numerals',240,240)
    for e in (EYE_L,EYE_R): _paste(b,'ember',*e)     # HR ember (demo on)
    _str(b,'SAT 24',*DATEV,19); _str(b,'72',*LEFTV,16); _str(b,'88%',*BATTV,16)
    for name,ang in (('hour_hand',((hh%12)+mm/60)*30),('min_hand',(mm+ss/60)*6),('sec_hand',ss*6)):
        h=Image.open(f'{NODPI}/{name}.png').convert('RGBA').rotate(-ang,center=(240,240),resample=Image.BICUBIC)
        b.alpha_composite(h)
    _paste(b,'hub',240,240)
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255)
    b.putalpha(ImageChops.multiply(b.split()[3],m)); b.save(f'{DRAW}/preview.png')
    out='/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/bone_preview.png'
    b.convert('RGB').save(out); print('preview ->',out)

# ------------------------------------------------------------------ WFF XML
PX='clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'; PY='clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
T='([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
BPM='(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 220))'
EMBER=f'(28 + clamp(([HEART_RATE] - 55) * 2, 0, 165)) * (0.62 + 0.38 * abs(sin({T} * {BPM} * 0.05236)))'
def Vr(t,v,dur=1.0,off=0.0,ip='LINEAR'): return f'      <Variant mode="AMBIENT" target="{t}" value="{v}" duration="{dur}" startOffset="{off}" interpolation="{ip}" />\n'
def XF(t,v): return f'      <Transform target="{t}" value="{v}" />\n'
def img(name,res,cx,cy,w,h,alpha,kids='',pivot=None):
    piv=f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"' if pivot else ''
    return f'    <PartImage name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}" alpha="{alpha}"{piv}>\n{kids}      <Image resource="{res}" />\n    </PartImage>\n'
def bffonts():
    m=_meta(); esc={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}; rows=''
    for ch,(nm,w,h) in m.items(): rows+=f'      <Character name="{esc.get(ch,ch)}" resource="{nm}" width="{w}" height="{h}" />\n'
    return '  <BitmapFonts>\n    <BitmapFont name="bone">\n'+rows+'    </BitmapFont>\n  </BitmapFonts>\n'
def part(name,cx,cy,w,h,size,off,tmpl=None,params=None,upper=False,s=None):
    if tmpl is not None:
        inner='<Template>'+tmpl
        for p in (params or []): inner+=f'<Parameter expression="{p}" />'
        inner+='</Template>'
    else: inner=s
    if upper: inner=f'<Upper>{inner}</Upper>'
    return (f'    <PartText name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}">\n'+Vr('alpha','0',0.4,off)
            +f'      <Text align="CENTER"><BitmapFont family="bone" size="{size}" color="#FFFFFF">{inner}</BitmapFont></Text>\n    </PartText>\n')

def gen_xml():
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="ANALOG" />\n  <Metadata key="PREVIEW_TIME" value="10:09:34" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF060403">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.5,0,'EASE_OUT')+XF('x',f'0 + 4 * {PX}')+XF('y',f'0 + 4 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.5,0,'EASE_IN')))
    o.append(img('z04_num','numerals',240,240,480,480,255,kids=Vr('alpha','70',0.45,0.12,'EASE_OUT')+XF('x',f'0 + 4 * {PX}')+XF('y',f'0 + 4 * {PY}')))
    # blood-red HR ember in each eye socket (off in ambient)
    for i,(ex,ey) in enumerate((EYE_L,EYE_R)):
        o.append(img(f'z05_ember{i}','ember',ex,ey,84,84,0,kids=Vr('alpha','0',0.4,0.2)+XF('alpha',EMBER)+XF('scaleX',f'0.85 + 0.25*abs(sin({T}*{BPM}*0.05236))')+XF('scaleY',f'0.85 + 0.25*abs(sin({T}*{BPM}*0.05236))')))
    o.append(img('z06_sheen','sheen',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.1,'EASE_OUT')+XF('alpha',f'90 + 40*abs(sin({T}*0.5))')+XF('x',f'0 + 55 * {PX}')))
    # readouts (bottom): HR . date . battery
    o.append(part('z11_date',*DATEV,150,28,19,0.30,tmpl='%s %d',params=['[DAY_OF_WEEK_S]','[DAY]'],upper=True))
    o.append(part('z10_hr',*LEFTV,60,24,16,0.28,tmpl='%d',params=['[HEART_RATE]']))
    o.append(part('z12_batt',*BATTV,60,24,16,0.32,tmpl='%d%%',params=['[BATTERY_PERCENT]']))
    # analog bone hands (dim in ambient) + hub; second hand hidden in ambient
    o.append(img('z40_hour','hour_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','190',0.4,0.0)+XF('angle','([HOUR_0_11] + [MINUTE] / 60) * 30')))
    o.append(img('z41_min','min_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','190',0.4,0.0)+XF('angle','([MINUTE] + [SECOND] / 60) * 6')))
    o.append(img('z42_sec','sec_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','0',0.3,0.0)+XF('angle',f'({T} % 60) * 6')))
    o.append(img('z43_hub','hub',240,240,64,64,255,kids=Vr('alpha','200',0.4,0.0)))
    o.append('  </Scene>\n</WatchFace>\n')
    xml=''.join(o); open(f'{RES}/raw/watchface.xml','w').write(xml); print('watchface.xml',len(xml),'bytes')

if __name__=='__main__':
    st=sys.argv[1] if len(sys.argv)>1 else 'all'
    if st in ('bg','all'): gen_bg()
    if st in ('numerals','all'): gen_numerals()
    if st in ('glyphs','all'): gen_glyphs()
    if st in ('hands','all'): gen_hands()
    if st in ('xml','all'): gen_xml()
    if st in ('preview','all'): compose_preview()
