#!/usr/bin/env python3
"""HELLFORGE — WFF v4 (Galaxy Watch 7, 480x480). Bone+metal+fire+red+war+black-magic.
AI demon-skull/pentagram dial (ComfyUI), animated: lava flicker, rising embers, HR fire-eyes,
pulsing sigil, war hands. Stages: bg | glyphs | hands | assets | xml | preview | anim | all."""
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; FONT=f'{RES}/font'; S=480
os.makedirs(NODPI,exist_ok=True); os.makedirs(DRAW,exist_ok=True)
DIAL=f'{ROOT}/tools/warbone_00001_.png'
METAL=(40,35,30); METAL_HI=(96,88,78); BONE=(216,206,186); BONE_HI=(240,232,214)
FIRE=(255,120,24); FIRE_HI=(255,196,70); RED=(200,22,14); RED_HI=(255,70,32); SHADOW=(8,5,3)
MARC=f'{FONT}/marcellus.ttf'
EYE_L=(205,209); EYE_R=(276,209)
DATEV=(240,352); HRV=(196,352); BATTV=(286,352)

# ------------------------------------------------------------ BG + FX assets
def gen_bg():
    d=Image.open(DIAL).convert('RGB').resize((S,S),Image.LANCZOS)
    d=ImageEnhance.Contrast(d).enhance(1.10); d=ImageEnhance.Color(d).enhance(1.12); d=ImageEnhance.Brightness(d).enhance(0.96)
    vig=Image.new('L',(S,S),0); vd=ImageDraw.Draw(vig)
    for rr in range(S//2,0,-1):
        t=rr/(S/2); vd.ellipse([S/2-rr,S/2-rr,S/2+rr,S/2+rr],fill=int(255*(1-0.45*t**3)))
    vig=vig.filter(ImageFilter.GaussianBlur(6)); d=Image.composite(d,Image.new('RGB',(S,S),(4,2,1)),vig)
    d.save(f'{NODPI}/bg.png')
    ImageEnhance.Brightness(ImageEnhance.Color(d).enhance(0.6)).enhance(0.32).save(f'{NODPI}/bg_aod.png')

    # fire glow ring on the lava (additive; alpha flickers in WFF)
    fr=Image.new('RGBA',(S,S),(0,0,0,0)); fd=ImageDraw.Draw(fr)
    for r in range(238,150,-1):
        t=(r-150)/88; a=int(150*(1-abs(t-0.62)/0.5)) if abs(t-0.62)<0.5 else 0
        col=FIRE_HI if t>0.6 else FIRE
        fd.ellipse([240-r,240-r,240+r,240+r],outline=col+(max(0,a),),width=2)
    fr=fr.filter(ImageFilter.GaussianBlur(9)); fr.save(f'{NODPI}/fireglow.png')

    # rising embers (480x960 seamless, scroll up)
    em=Image.new('RGBA',(S,960),(0,0,0,0)); ed=ImageDraw.Draw(em); rnd=random.Random(5)
    for _ in range(260):
        x=rnd.uniform(0,S); y=rnd.uniform(0,480); s=rnd.uniform(1.2,3.2); a=rnd.randint(80,220)
        c=rnd.choice([FIRE_HI,FIRE,RED_HI])
        ed.ellipse([x-s,y-s,x+s,y+s],fill=c+(a,)); ed.ellipse([x-s,y+480-s,x+s,y+480+s],fill=c+(a,))
    em=em.filter(ImageFilter.GaussianBlur(0.6)); em.save(f'{NODPI}/embers.png')

    # eye ember (fire in the sockets)
    e=Image.new('RGBA',(80,80),(0,0,0,0)); ec=ImageDraw.Draw(e)
    for r in range(38,0,-1):
        t=r/38; a=int(220*(1-t)**1.8); col=FIRE_HI if t<0.4 else RED_HI
        ec.ellipse([40-r,40-r,40+r,40+r],fill=col+(a,))
    e.filter(ImageFilter.GaussianBlur(4)).save(f'{NODPI}/eye.png')

    # sigil pulse: a red pentagram-ish star glow
    sg=Image.new('RGBA',(S,S),(0,0,0,0)); sd=ImageDraw.Draw(sg); R=150
    pts=[(240+R*math.sin(math.radians(a)),240-R*math.cos(math.radians(a))) for a in range(0,360,72)]
    order=[0,2,4,1,3,0]
    for i in range(5): sd.line([pts[order[i]],pts[order[i+1]]],fill=RED_HI+(150,),width=5)
    sg=sg.filter(ImageFilter.GaussianBlur(7)); sg.save(f'{NODPI}/sigil.png')

    # raking ember sheen
    sh=Image.new('RGBA',(S,S),(0,0,0,0)); ImageDraw.Draw(sh).polygon([(-120,0),(70,0),(230,480),(50,480)],fill=(255,150,60,26))
    sh.filter(ImageFilter.GaussianBlur(52)).save(f'{NODPI}/sheen.png')
    print('bg + fx: bg,bg_aod,fireglow,embers,eye,sigil,sheen')

# ------------------------------------------------------------ WAR HANDS (metal blade + hot edge)
def gen_hands():
    ss=4; C=240*ss
    def blade(length,w,tail,name,hot=True,allred=False):
        im=Image.new('RGBA',(S*ss,S*ss),(0,0,0,0)); dr=ImageDraw.Draw(im); ty=C-length*ss
        body=[(C-w/2*ss,C),(C-w*0.28*ss,ty+14*ss),(C,ty-8*ss),(C+w*0.28*ss,ty+14*ss),(C+w/2*ss,C),
              (C+w*0.34*ss,C+tail*ss),(C-w*0.34*ss,C+tail*ss)]
        base=(RED if allred else METAL)
        dr.polygon(body,fill=base+(255,))
        if not allred:
            dr.line([(C,C+tail*ss),(C,ty)],fill=METAL_HI+(255,),width=int(2*ss))  # spine highlight
        im=im.resize((S,S),Image.LANCZOS)
        a=im.split()[3]
        out=Image.new('RGBA',(S,S),(0,0,0,0))
        drop=Image.new('RGBA',(S,S),SHADOW+(0,)); drop.putalpha(a.point(lambda v:int(v*0.85))); out.alpha_composite(drop,(3,4))
        if hot:  # red-hot glowing edge
            edge=a.filter(ImageFilter.MaxFilter(5)); glow=Image.new('RGBA',(S,S),RED_HI+(0,)); glow.putalpha(ImageChops.subtract(edge,a).filter(ImageFilter.GaussianBlur(2)).point(lambda v:min(255,int(v*2.2)))); out.alpha_composite(glow)
        out.alpha_composite(im)
        out.save(f'{NODPI}/{name}.png')
    blade(118,20,24,'hour_hand'); blade(172,14,28,'min_hand'); blade(196,6,34,'sec_hand',allred=True,hot=True)
    hb=Image.new('RGBA',(60,60),(0,0,0,0)); hd=ImageDraw.Draw(hb)
    hd.ellipse([8,9,52,53],fill=SHADOW+(220,)); hd.ellipse([6,6,50,50],fill=METAL+(255,))
    hd.ellipse([15,15,41,41],fill=METAL_HI+(255,)); hd.ellipse([22,22,34,34],fill=RED+(255,)); hd.ellipse([25,25,31,31],fill=FIRE_HI+(255,))
    hb.save(f'{NODPI}/hub.png'); print('hands: hour,min,sec,hub')

# ------------------------------------------------------------ GLYPHS (bone, fire-edged)
CHARS={**{str(d):str(d) for d in range(10)}, ':':'colon','%':'pct','.':'dot',' ':'space',
       **{c:c.lower() for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
FS=60
def gen_glyphs():
    f=ImageFont.truetype(MARC,FS); asc,desc=f.getmetrics(); H=asc+desc; meta={}
    for ch,rn in CHARS.items():
        if ch==' ': w=int(FS*0.28); im=Image.new('RGBA',(w,H),(0,0,0,0))
        else:
            w=max(6,int(round(f.getlength(ch)))+8); im=Image.new('RGBA',(w,H),(0,0,0,0)); dd=ImageDraw.Draw(im)
            for ox,oy in ((-2,0),(2,0),(0,-2),(0,2)): dd.text((4+ox,asc+oy),ch,font=f,fill=RED_HI+(120,),anchor='ls')  # fire halo
            dd.text((5,asc+2),ch,font=f,fill=SHADOW+(255,),anchor='ls'); dd.text((4,asc),ch,font=f,fill=BONE_HI+(255,),anchor='ls')
        nm=f'g_{rn}'; im.save(f'{NODPI}/{nm}.png'); meta[ch]=(nm,w,H)
    json.dump(meta,open(f'{ROOT}/tools/glyphs.json','w')); print('glyphs',len(meta))
def _meta(): return json.load(open(f'{ROOT}/tools/glyphs.json'))

# ------------------------------------------------------------ HOUR NUMERALS (made of real bones)
ROMANS=['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']
NUMF=f'{FONT}/metamorphous.ttf'
def _lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def _carved(text,size):
    import random as _r
    f=ImageFont.truetype(NUMF,size); bb=f.getbbox(text); w=bb[2]-bb[0]; h=bb[3]-bb[1]; pad=9
    W,H=w+pad*2,h+pad*2; ox,oy=pad-bb[0],pad-bb[1]
    gm=Image.new('L',(W,H),0); ImageDraw.Draw(gm).text((ox,oy),text,font=f,fill=255)
    out=Image.new('RGBA',(W,H),(0,0,0,0))
    # 1) outer hot glow
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); glow.paste(FIRE,(0,0),gm.filter(ImageFilter.MaxFilter(3))); glow=glow.filter(ImageFilter.GaussianBlur(4)); out.alpha_composite(glow)
    # 2) extruded dark depth
    dd=ImageDraw.Draw(out)
    for k in (3,2,1): dd.text((ox+k,oy+k),text,font=f,fill=SHADOW+(240,))
    # 3) forged fill: bone-white (cool, top) -> amber -> red-hot (bottom)
    grad=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(grad)
    for y in range(H):
        t=y/max(1,H-1); c=_lerp(BONE_HI,FIRE_HI,t*1.6) if t<0.55 else _lerp(FIRE,RED_HI,(t-0.55)/0.45)
        gd.line([(0,y),(W,y)],fill=c+(255,))
    face=Image.new('RGBA',(W,H),(0,0,0,0)); face.paste(grad,(0,0),gm); out.alpha_composite(face)
    # 4) molten cracks (glowing seams inside the glyph)
    rnd=_r.Random(hash(text)&0xffff); cr=Image.new('RGBA',(W,H),(0,0,0,0)); cd=ImageDraw.Draw(cr)
    for _ in range(2):
        x0=rnd.randint(int(W*0.3),int(W*0.7)); y0=rnd.randint(2,H-2); pts=[(x0,y0)]
        for _ in range(3): pts.append((pts[-1][0]+rnd.randint(-5,5),pts[-1][1]+rnd.randint(-7,-2)))
        cd.line(pts,fill=FIRE_HI+(255,),width=1)
    cr=Image.composite(cr,Image.new('RGBA',(W,H),(0,0,0,0)),gm); out.alpha_composite(cr.filter(ImageFilter.GaussianBlur(0.5)))
    # 5) top bevel highlight
    hl=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(hl).text((ox-1,oy-1),text,font=f,fill=(255,250,236,150)); out.alpha_composite(Image.composite(hl,Image.new('RGBA',(W,H),(0,0,0,0)),gm))
    return out
def gen_numerals(r=207,size=22):
    ring=Image.new('RGBA',(S,S),(0,0,0,0))
    for i,rn in enumerate(ROMANS):
        a=math.radians(i*30); cx=240+r*math.sin(a); cy=240-r*math.cos(a); n=_carved(rn,size)
        halo=Image.new('RGBA',n.size,(0,0,0,0)); halo.paste(RED_HI,(0,0),n.split()[3]); halo=halo.filter(ImageFilter.GaussianBlur(5))
        ring.alpha_composite(halo,(int(cx-n.width/2),int(cy-n.height/2))); ring.alpha_composite(n,(int(cx-n.width/2),int(cy-n.height/2)))
    ring.save(f'{NODPI}/numerals.png'); print('numerals: carved bone Metamorphous size',size)
def numtest():
    sheet=Image.new('RGB',(6*88,2*70),(20,15,11))
    for i,rn in enumerate(ROMANS):
        n=_carved(rn,22); px=(i%6)*88+(88-n.width)//2; py=(i//6)*70+(70-n.height)//2; sheet.paste(n,(px,py),n)
    sheet.save('/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/bonenum_sheet.png'); print('numtest sheet saved')

# ------------------------------------------------------------ preview / anim helpers
def _str(b,s,cx,cy,size,anchor='center'):
    m=_meta(); H=list(m.values())[0][2]; sc=size/H; gl=[]; tot=0
    for ch in s:
        ch=ch if ch in m else ' '; nm,w,h=m[ch]; gw=w*sc; gl.append((nm,gw)); tot+=gw
    x=cx-tot/2 if anchor=='center' else cx
    for nm,gw in gl:
        g=Image.open(f'{NODPI}/{nm}.png').convert('RGBA').resize((max(1,int(gw)),int(size)),Image.LANCZOS)
        b.alpha_composite(g,(int(x),int(cy-size/2))); x+=gw
def _p(b,name,cx,cy,alpha=255,scale=1.0):
    im=Image.open(f'{NODPI}/{name}.png').convert('RGBA')
    if scale!=1.0: im=im.resize((int(im.width*scale),int(im.height*scale)),Image.LANCZOS)
    if alpha<255: im=im.copy(); im.putalpha(im.split()[3].point(lambda v:int(v*alpha/255)))
    b.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

def _frame(t, reveal=1.0):
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA')
    fl=120+50*math.sin(t*9)+35*math.sin(t*15.7+1.3)+25*math.sin(t*23+2); fl=max(50,min(235,fl))
    _p(b,'sigil',240,240,int(70+50*abs(math.sin(t*1.5))));
    _p(b,'fireglow',240,240,int(fl))
    # rising embers
    em=Image.open(f'{NODPI}/embers.png').convert('RGBA'); yo=int(-(t*150)%480)
    ec=Image.new('RGBA',(S,S),(0,0,0,0)); ec.alpha_composite(em,(0,yo-480)); ec.alpha_composite(em,(0,yo)); b.alpha_composite(ec)
    _p(b,'numerals',240,240)
    beat=abs(math.sin(t*72/60*math.pi)); eye=int((90+120*beat)*reveal)
    for e in (EYE_L,EYE_R): _p(b,'eye',*e,eye,0.8+0.3*beat)
    if reveal>0.6:
        _str(b,'SAT 24',*DATEV,18); _str(b,'72',*HRV,15); _str(b,'88%',*BATTV,15)
    hh,mm,ss=10,9,int(t)%60
    for name,ang in (('hour_hand',(10+9/60)*30),('min_hand',9*6),('sec_hand',ss*6)):
        h=Image.open(f'{NODPI}/{name}.png').convert('RGBA').rotate(-ang,center=(240,240),resample=Image.BICUBIC); b.alpha_composite(h)
    _p(b,'hub',240,240)
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255); b.putalpha(ImageChops.multiply(b.split()[3],m))
    return b

def compose_preview():
    b=_frame(2.0); b.convert('RGB').save('/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/hell_preview.png')
    b.save(f'{DRAW}/preview.png'); print('preview saved')

def animate():
    frames=[_frame(i/12.0).convert('RGB').resize((320,320)) for i in range(48)]
    out='/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/hell_anim.gif'
    frames[0].save(out,save_all=True,append_images=frames[1:],duration=70,loop=0,optimize=True); print('anim ->',out)

# ------------------------------------------------------------ WFF XML
PX='clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'; PY='clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
T='([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
BPM='(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 220))'
FLICK=f'clamp(120 + 50*sin({T}*9) + 35*sin({T}*15.7 + 1.3) + 25*sin({T}*23 + 2) + clamp(([HEART_RATE]-70)*1.5,0,60), 60, 245)'
BEAT=f'abs(sin({T} * {BPM} * 0.05236))'
def Vr(t,v,dur=1.0,off=0.0,ip='LINEAR'): return f'      <Variant mode="AMBIENT" target="{t}" value="{v}" duration="{dur}" startOffset="{off}" interpolation="{ip}" />\n'
def XF(t,v): return f'      <Transform target="{t}" value="{v}" />\n'
def img(name,res,cx,cy,w,h,alpha,kids='',pivot=None):
    piv=f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"' if pivot else ''
    return f'    <PartImage name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}" alpha="{alpha}"{piv}>\n{kids}      <Image resource="{res}" />\n    </PartImage>\n'
def bffonts():
    m=_meta(); esc={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}; rows=''
    for ch,(nm,w,h) in m.items(): rows+=f'      <Character name="{esc.get(ch,ch)}" resource="{nm}" width="{w}" height="{h}" />\n'
    return '  <BitmapFonts>\n    <BitmapFont name="hell">\n'+rows+'    </BitmapFont>\n  </BitmapFonts>\n'
def part(name,cx,cy,w,h,size,off,tmpl,params,upper=False):
    inner='<Template>'+tmpl
    for p in params: inner+=f'<Parameter expression="{p}" />'
    inner+='</Template>'
    if upper: inner=f'<Upper>{inner}</Upper>'
    return (f'    <PartText name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}">\n'+Vr('alpha','0',0.4,off)
            +f'      <Text align="CENTER"><BitmapFont family="hell" size="{size}" color="#FFFFFF">{inner}</BitmapFont></Text>\n    </PartText>\n')

def gen_xml():
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="ANALOG" />\n  <Metadata key="PREVIEW_TIME" value="10:09:34" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF040201">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.5,0,'EASE_OUT')+XF('x',f'0 + 4 * {PX}')+XF('y',f'0 + 4 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.5,0,'EASE_IN')))
    o.append(img('z02_sigil','sigil',240,240,480,480,0,kids=Vr('alpha','0',0.4,0.1)+XF('alpha',f'70 + 60*{BEAT}')))
    o.append(img('z03_fire','fireglow',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.05,'EASE_OUT')+XF('alpha',FLICK)))
    o.append(img('z04_embers','embers',240,240,480,960,0,kids=Vr('alpha','0',0.4,0.12)+XF('alpha',f'110 + 40*sin({T}*4)')+XF('y',f'-480 + ((480 - (({T} * 150) % 480)))')))
    o.append(img('z04b_num','numerals',240,240,480,480,255,kids=Vr('alpha','80',0.45,0.14,'EASE_OUT')+XF('x',f'0 + 4 * {PX}')+XF('y',f'0 + 4 * {PY}')))
    for i,(ex,ey) in enumerate((EYE_L,EYE_R)):
        o.append(img(f'z05_eye{i}','eye',ex,ey,80,80,0,kids=Vr('alpha','0',0.4,0.18)+XF('alpha',f'(90 + clamp(([HEART_RATE]-55)*2,0,150)) * (0.55 + 0.45*{BEAT})')+XF('scaleX',f'0.8+0.35*{BEAT}')+XF('scaleY',f'0.8+0.35*{BEAT}')))
    o.append(img('z06_sheen','sheen',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.1,'EASE_OUT')+XF('alpha',f'70 + 40*abs(sin({T}*0.6))')+XF('x',f'0 + 55 * {PX}')))
    o.append(part('z10_date',*DATEV,150,26,18,0.3,'%s %d',['[DAY_OF_WEEK_S]','[DAY]'],True))
    o.append(part('z11_hr',*HRV,56,22,15,0.28,'%d',['[HEART_RATE]']))
    o.append(part('z12_batt',*BATTV,56,22,15,0.32,'%d%%',['[BATTERY_PERCENT]']))
    o.append(img('z40_hour','hour_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','200',0.4,0.0)+XF('angle','([HOUR_0_11] + [MINUTE] / 60) * 30')))
    o.append(img('z41_min','min_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','200',0.4,0.0)+XF('angle','([MINUTE] + [SECOND] / 60) * 6')))
    o.append(img('z42_sec','sec_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','0',0.3,0.0)+XF('angle',f'({T} % 60) * 6')))
    o.append(img('z43_hub','hub',240,240,60,60,255,kids=Vr('alpha','210',0.4,0.0)))
    o.append('  </Scene>\n</WatchFace>\n')
    open(f'{RES}/raw/watchface.xml','w').write(''.join(o)); print('watchface.xml',len(''.join(o)),'bytes')

if __name__=='__main__':
    st=sys.argv[1] if len(sys.argv)>1 else 'all'
    if st in ('bg','all'): gen_bg()
    if st in ('numerals','all'): gen_numerals()
    if st in ('glyphs','all'): gen_glyphs()
    if st in ('hands','all'): gen_hands()
    if st in ('xml','all'): gen_xml()
    if st in ('preview','all'): compose_preview()
    if st in ('anim','all'): animate()
