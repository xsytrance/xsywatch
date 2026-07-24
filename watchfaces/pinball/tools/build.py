#!/usr/bin/env python3
"""PINBALL — WFF v4 (Galaxy Watch 7, 480x480). 3D pinball playfield (ComfyUI), animated:
chrome ball ricochets, pop-bumpers flash, orange DMD score-display time.
Stages: bg | dmd | assets | xml | preview | anim | all."""
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; FONT=f'{RES}/font'; S=480
os.makedirs(NODPI,exist_ok=True); os.makedirs(DRAW,exist_ok=True)
DIAL=f'{ROOT}/tools/dial.png'
DMDF='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
AMBER=(255,150,30); AMBER_HI=(255,210,120); AMBER_DK=(70,32,4)
BUMPERS=[(90,135),(345,92),(372,240),(338,408),(92,396),(104,214)]
TIMEV=(240,116); DATEV=(240,150); BATTV=(240,372)

def gen_bg():
    d=Image.open(DIAL).convert('RGB').resize((S,S),Image.LANCZOS)
    d=ImageEnhance.Contrast(d).enhance(1.06); d=ImageEnhance.Color(d).enhance(1.10)
    vig=Image.new('L',(S,S),0); vd=ImageDraw.Draw(vig)
    for rr in range(S//2,0,-1):
        t=rr/(S/2); vd.ellipse([S/2-rr,S/2-rr,S/2+rr,S/2+rr],fill=int(255*(1-0.4*t**3)))
    d=Image.composite(d,Image.new('RGB',(S,S),(3,3,5)),vig.filter(ImageFilter.GaussianBlur(6)))
    d.save(f'{NODPI}/bg.png')
    ImageEnhance.Brightness(d).enhance(0.34).save(f'{NODPI}/bg_aod.png')
    # bumper flash: radial white-orange glow
    fl=Image.new('RGBA',(96,96),(0,0,0,0)); fd=ImageDraw.Draw(fl)
    for r in range(46,0,-1):
        t=r/46; a=int(230*(1-t)**1.7); c=(255,255,240) if t<0.35 else AMBER_HI
        fd.ellipse([48-r,48-r,48+r,48+r],fill=c+(a,))
    fl.filter(ImageFilter.GaussianBlur(3)).save(f'{NODPI}/flash.png')
    # chrome ball
    ss=4; b=Image.new('RGBA',(30*ss,30*ss),(0,0,0,0)); bd=ImageDraw.Draw(b); c=15*ss
    bd.ellipse([1*ss,1*ss,29*ss,29*ss],fill=(60,62,70,255))
    bd.ellipse([3*ss,3*ss,27*ss,25*ss],fill=(150,155,168,255))
    bd.ellipse([6*ss,5*ss,20*ss,17*ss],fill=(220,225,235,255))
    bd.ellipse([9*ss,7*ss,15*ss,12*ss],fill=(255,255,255,255))
    b=b.resize((30,30),Image.LANCZOS)
    sh=Image.new('RGBA',(30,30),(0,0,0,0)); ImageDraw.Draw(sh).ellipse([3,24,27,30],fill=(0,0,0,120)); sh=sh.filter(ImageFilter.GaussianBlur(2))
    out=Image.new('RGBA',(30,30),(0,0,0,0)); out.alpha_composite(sh); out.alpha_composite(b); out.save(f'{NODPI}/ball.png')
    # DMD score panel (dark inset with amber border)
    for nm,(w,h) in (('dmd_time',(150,40)),('dmd_sm',(120,26))):
        p=Image.new('RGBA',(w,h),(0,0,0,0)); pd=ImageDraw.Draw(p)
        pd.rounded_rectangle([0,0,w-1,h-1],radius=6,fill=(8,6,4,220))
        pd.rounded_rectangle([1,1,w-2,h-2],radius=6,outline=AMBER+(180,),width=2)
        p.save(f'{NODPI}/{nm}.png')
    print('bg + assets: bg,bg_aod,flash,ball,dmd panels')

# ---- DMD dot-matrix BitmapFont ----
CHARS={**{str(d):str(d) for d in range(10)}, ':':'colon','%':'pct','.':'dot',' ':'space',
       **{c:c.lower() for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
def gen_dmd():
    ch_h=22; f=ImageFont.truetype(DMDF,ch_h); meta={}; sp=3; dot=1.5
    asc,desc=f.getmetrics(); H=ch_h+6
    for ch,rn in CHARS.items():
        if ch==' ': w=10; im=Image.new('RGBA',(w,H),(0,0,0,0))
        else:
            bb=f.getbbox(ch); gw=bb[2]-bb[0]; w=gw+8
            m=Image.new('L',(w,H),0); ImageDraw.Draw(m).text((4-bb[0],(H-ch_h)//2-bb[1]//2+2),ch,font=f,fill=255)
            m=m.load(); im=Image.new('RGBA',(w,H),(0,0,0,0)); dd=ImageDraw.Draw(im)
            gy=1
            while gy<H:
                gx=1
                while gx<w:
                    on=m[min(w-1,gx),min(H-1,gy)]>110
                    if on:
                        dd.ellipse([gx-dot-0.6,gy-dot-0.6,gx+dot+0.6,gy+dot+0.6],fill=AMBER_DK+(200,))
                        dd.ellipse([gx-dot,gy-dot,gx+dot,gy+dot],fill=AMBER_HI+(255,))
                    gx+=sp
                gy+=sp
        nm=f'g_{rn}'; im.save(f'{NODPI}/{nm}.png'); meta[ch]=(nm,im.width,H)
    json.dump(meta,open(f'{ROOT}/tools/glyphs.json','w')); print('dmd glyphs',len(meta))
def _meta(): return json.load(open(f'{ROOT}/tools/glyphs.json'))

# ---- preview / anim ----
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
    if scale!=1.0: im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.LANCZOS)
    if alpha<255: im=im.copy(); im.putalpha(im.split()[3].point(lambda v:int(v*alpha/255)))
    b.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))

def _frame(t):
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA')
    for i,(bx,by) in enumerate(BUMPERS):
        fa=max(0.0,math.sin(t*3.3 + i*1.7)); _p(b,'flash',bx,by,int(60+180*fa*fa),0.7+0.4*fa)
    _p(b,'dmd_time',*TIMEV); _p(b,'dmd_sm',*DATEV,220); _p(b,'dmd_sm',*BATTV,220)
    _str(b,'10:09',*TIMEV,22); _str(b,'SAT 24',*DATEV,13); _str(b,'BALL 88%',*BATTV,12)
    bx=240+128*math.sin(t*0.9); by=258+112*math.sin(t*1.4+1.7); _p(b,'ball',bx,by)
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255); b.putalpha(ImageChops.multiply(b.split()[3],m))
    return b
def compose_preview():
    _frame(1.4).convert('RGB').save('/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/pin_preview.png'); print('preview')
def animate():
    fr=[_frame(i/12.0).convert('RGB').resize((320,320)) for i in range(48)]
    out='/tmp/claude-1000/-home-xsyprime-xsywatch/2655b40c-a508-4fa1-81b0-69587626d7d2/scratchpad/pin_anim.gif'
    fr[0].save(out,save_all=True,append_images=fr[1:],duration=70,loop=0,optimize=True); print('anim ->',out)

# ---- WFF XML ----
PX='clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'; PY='clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
T='([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
def Vr(t,v,dur=1.0,off=0.0,ip='LINEAR'): return f'      <Variant mode="AMBIENT" target="{t}" value="{v}" duration="{dur}" startOffset="{off}" interpolation="{ip}" />\n'
def XF(t,v): return f'      <Transform target="{t}" value="{v}" />\n'
def img(name,res,cx,cy,w,h,alpha,kids=''):
    return f'    <PartImage name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}" alpha="{alpha}">\n{kids}      <Image resource="{res}" />\n    </PartImage>\n'
def bffonts():
    m=_meta(); esc={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}; rows=''
    for ch,(nm,w,h) in m.items(): rows+=f'      <Character name="{esc.get(ch,ch)}" resource="{nm}" width="{w}" height="{h}" />\n'
    return '  <BitmapFonts>\n    <BitmapFont name="dmd">\n'+rows+'    </BitmapFont>\n  </BitmapFonts>\n'
def part(name,cx,cy,w,h,size,off,tmpl,params,upper=False):
    inner='<Template>'+tmpl
    for p in params: inner+=f'<Parameter expression="{p}" />'
    inner+='</Template>'
    if upper: inner=f'<Upper>{inner}</Upper>'
    return (f'    <PartText name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}">\n'+Vr('alpha','0',0.4,off)
            +f'      <Text align="CENTER"><BitmapFont family="dmd" size="{size}" color="#FFFFFF">{inner}</BitmapFont></Text>\n    </PartText>\n')

def gen_xml():
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="DIGITAL" />\n  <Metadata key="PREVIEW_TIME" value="10:09:32" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF030305">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.5,0,'EASE_OUT')+XF('x',f'0 + 4 * {PX}')+XF('y',f'0 + 4 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.5,0,'EASE_IN')))
    for i,(bx,by) in enumerate(BUMPERS):
        o.append(img(f'z05_bump{i}','flash',bx,by,96,96,0,kids=Vr('alpha','0',0.4,0.1)+XF('alpha',f'40 + 200 * pow(abs(sin({T}*3.3 + {i*1.7})),2)')))
    # DMD panels + readouts
    o.append(img('z10_p1','dmd_time',*TIMEV,150,40,255,kids=Vr('alpha','0',0.4,0.16)))
    o.append(img('z10_p2','dmd_sm',*DATEV,120,26,220,kids=Vr('alpha','0',0.4,0.2)))
    o.append(img('z10_p3','dmd_sm',*BATTV,120,26,220,kids=Vr('alpha','0',0.4,0.24)))
    o.append(part('z11_time',*TIMEV,140,34,22,0.18,'%s',['[HOUR_1_12_Z]']))  # placeholder replaced below
    o[-1]=(f'    <DigitalClock x="{TIMEV[0]-70}" y="{TIMEV[1]-17}" width="140" height="34">\n'+Vr('alpha','0',0.4,0.18)
           +f'      <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="0" width="140" height="34"><BitmapFont family="dmd" size="22" color="#FFFFFF" /></TimeText>\n    </DigitalClock>\n')
    o.append(part('z12_date',*DATEV,116,22,13,0.2,'%s %d',['[DAY_OF_WEEK_S]','[DAY]'],True))
    o.append(part('z13_batt',*BATTV,116,22,12,0.24,'BALL %d%%',['[BATTERY_PERCENT]']))
    # chrome ball ricochet
    o.append(img('z40_ball','ball',240,240,30,30,255,kids=Vr('alpha','0',0.4,0.0)+XF('x',f'0 + 128*sin({T}*0.9)')+XF('y',f'18 + 112*sin({T}*1.4 + 1.7)')))
    o.append('  </Scene>\n</WatchFace>\n')
    open(f'{RES}/raw/watchface.xml','w').write(''.join(o)); print('watchface.xml',len(''.join(o)),'bytes')

if __name__=='__main__':
    st=sys.argv[1] if len(sys.argv)>1 else 'all'
    if st in ('bg','all'): gen_bg()
    if st in ('dmd','all'): gen_dmd()
    if st in ('xml','all'): gen_xml()
    if st in ('preview','all'): compose_preview()
    if st in ('anim','all'): animate()
