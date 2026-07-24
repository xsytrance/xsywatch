#!/usr/bin/env python3
"""AURELIUS v4 — WARBIRD (WFF v4, Galaxy Watch 7 480x480).
The face IS an olive-drab WW1 fighter: riveted fuselage skin (ComfyUI photo texture),
painted shark-mouth teeth + angry eye + stencils (procedural, weathered into the metal),
spinning wooden prop in a riveted cowling at 12 = SECONDS, cockpit gauges: FUEL = battery,
PULSE = heart rate. Painted-metal realism, no cel outlines.
Stages: bg | assets | hands | glyphs | xml | preview | anim | debug | all"""
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; S=480
os.makedirs(NODPI,exist_ok=True); os.makedirs(DRAW,exist_ok=True); os.makedirs(f'{RES}/raw',exist_ok=True)
FUS='/home/xsyprime/AI/ComfyUI/output/fuselage_00004_.png'
RAJD=f'{RES}/font/rajdhani_bold.ttf'
SCRATCH='/tmp/claude-1000/-home-xsyprime-xsywatch/555d57e3-c801-4258-96e7-5de12ef1db82/scratchpad'

PROP=(240,132); PR_COWL=66
GAUGE_L=(92,240); GAUGE_R=(388,240); GA_R=45
DATEW=(240,300)
HUBC=(240,240)

KHAKI=(213,196,148); KHAKI_D=(160,146,106)
RED=(188,44,34); RED_D=(126,26,20); MAROON=(74,18,16)
WHITE=(238,234,222); BLACK=(24,22,18)
WOOD=(140,92,52); WOOD_D=(96,60,34); LAM=(190,146,94)
STEEL=(120,122,118); STEEL_D=(70,72,70); STEEL_HI=(180,182,176)

def _lerp(a,b,t): t=max(0.0,min(1.0,t)); return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def _grain(size,alpha=26,seed=4):
    rnd=random.Random(seed); n=Image.new('RGBA',(size,size),(0,0,0,0)); d=ImageDraw.Draw(n)
    for _ in range(size*size//38):
        x=rnd.randint(0,size-1); y=rnd.randint(0,size-1); v=rnd.randint(0,255)
        d.point((x,y),fill=(v,v,v,rnd.randint(6,alpha)))
    return n.filter(ImageFilter.GaussianBlur(0.4))
def _chips(mask,frac=0.05,seed=9,rmax=3):
    """eat small worn chips out of an alpha mask"""
    rnd=random.Random(seed); d=ImageDraw.Draw(mask); w,h=mask.size
    for _ in range(int(w*h*frac/60)):
        x=rnd.randint(0,w-1); y=rnd.randint(0,h-1); r=rnd.uniform(0.6,rmax)
        d.ellipse([x-r,y-r,x+r,y+r],fill=0)
    return mask

def _paint_on(bg,marking,lum_blur=2.2,lo=0.62,hi=1.22,chip_frac=0.05,seed=9,blur=0.6,rmax=3):
    """weather a flat marking layer onto photo metal: soften, chip, follow metal luminance"""
    m=marking.filter(ImageFilter.GaussianBlur(blur))
    a=_chips(m.split()[3],frac=chip_frac,seed=seed,rmax=rmax)
    lum=bg.convert('L').filter(ImageFilter.GaussianBlur(lum_blur))
    f=lum.point(lambda v:int(255*min(hi,lo+(hi-lo)*v/150)/hi))
    fac=Image.merge('RGB',[f,f,f])
    rgb=ImageChops.multiply(m.convert('RGB'),fac)
    out=Image.merge('RGBA',[*rgb.split(),a])
    bg.alpha_composite(out); return bg

# ------------------------------------------------------------------ background
def gen_bg():
    SC=2; SB=S*SC
    def U(v): return v*SC
    fus=Image.open(FUS).convert('RGB')
    d=fus.crop((0,0,1024,1024)).resize((SB,SB),Image.LANCZOS)
    d=ImageEnhance.Contrast(d).enhance(1.04); d=ImageEnhance.Color(d).enhance(1.05)
    d=d.convert('RGBA')
    dd=ImageDraw.Draw(d)

    # --- riveted outer ring band (texture shows through) ---
    ring=Image.new('RGBA',(SB,SB),(0,0,0,0)); rd=ImageDraw.Draw(ring)
    rd.ellipse([U(2),U(2),SB-U(2),SB-U(2)],outline=(20,22,14,200),width=U(8))
    rd.ellipse([U(8),U(8),SB-U(8),SB-U(8)],outline=(46,50,34,120),width=U(22))
    rd.ellipse([U(28),U(28),SB-U(28),SB-U(28)],outline=(20,22,14,150),width=U(3))
    d.alpha_composite(ring.filter(ImageFilter.GaussianBlur(U(1.5))))
    rnd=random.Random(3)
    for k in range(40):   # rivets around the ring
        a=math.radians(k*9+2)
        x=U(240+227*math.sin(a)); y=U(240-227*math.cos(a))
        rr=U(2.6)
        dd.ellipse([x-rr,y+U(1)-rr,x+rr,y+U(1)+rr],fill=(28,30,22,180))
        dd.ellipse([x-rr,y-rr,x+rr,y+rr],fill=_lerp(STEEL_D,(92,96,74),rnd.random())+(255,))
        dd.ellipse([x-rr*0.5,y-rr*0.75,x+rr*0.15,y-rr*0.1],fill=(200,200,188,140))

    # --- painted markings (weathered onto the skin) ---
    M=Image.new('RGBA',(SB,SB),(0,0,0,0)); md=ImageDraw.Draw(M)
    # == shark mouth ==
    TH0,TH1=141,219
    def lipP(th,r): a=math.radians(th); return (U(240+r*math.sin(a)),U(240-r*math.cos(a)))
    lo=[lipP(t,222) for t in range(TH0,TH1+1,3)]
    c0=lipP(TH0,222); c1=lipP(TH1,222)
    def onUp(t):
        x=c1[0]+(c0[0]-c1[0])*t; y=c1[1]+(c0[1]-c1[1])*t
        return (x,y-((1-(2*t-1)**2)*U(62)))
    up=[onUp(q/40.0) for q in range(41)]
    md.polygon(up+lo,fill=MAROON+(255,))
    md.line(up,fill=RED+(255,),width=U(13))
    md.line(lo,fill=RED+(255,),width=U(12))
    md.line(up,fill=RED_D+(255,),width=U(5))
    NT=7
    for i in range(NT):
        p0=onUp((i+0.08)/NT); p1=onUp((i+0.92)/NT); pm=onUp((i+0.5)/NT)
        md.polygon([p0,p1,(pm[0],pm[1]+U(42))],fill=WHITE+(255,))
        md.polygon([p0,p1,(pm[0],pm[1]+U(42))],outline=(150,140,120,255),width=SC)
    for i in range(NT-1):
        th0=TH1-(TH1-TH0)*(i+0.10)/(NT-1); th1=TH1-(TH1-TH0)*(i+0.90)/(NT-1); thm=TH1-(TH1-TH0)*(i+0.5)/(NT-1)
        p0=lipP(th0,220); p1=lipP(th1,220); pm=lipP(thm,220)
        md.polygon([p0,p1,(pm[0],pm[1]-U(38))],fill=WHITE+(255,))
        md.polygon([p0,p1,(pm[0],pm[1]-U(38))],outline=(150,140,120,255),width=SC)
    md.line(up,fill=BLACK+(255,),width=U(4))
    md.line(lo+[lo[-1]],fill=BLACK+(255,),width=U(4))
    # == angry eye ==
    ex,ey=U(150),U(310)
    almond=[]
    for q in range(25):
        t=q/24.0*math.pi
        almond.append((ex-U(34)*math.cos(t),ey-U(15)*math.sin(t)+U(2)*math.cos(t)))
    for q in range(25):
        t=q/24.0*math.pi
        almond.append((ex+U(34)*math.cos(t),ey+U(13)*math.sin(t)))
    md.polygon(almond,fill=WHITE+(255,))
    md.line(almond+[almond[0]],fill=BLACK+(255,),width=U(3))
    md.ellipse([ex+U(2),ey-U(13),ex+U(26),ey+U(11)],fill=BLACK+(255,))
    md.ellipse([ex+U(8),ey-U(9),ex+U(16),ey-U(1)],fill=WHITE+(235,))
    md.line([(ex-U(36),ey-U(14)),(ex+U(34),ey-U(26))],fill=BLACK+(255,),width=U(8))
    # == kill tally ==
    for i in range(4):
        tx=U(316+i*12); ty=U(300)
        md.line([(tx,ty),(tx,ty+U(24))],fill=BLACK+(230,),width=U(3))
    md.line([(U(308),U(322)),(U(360),U(302))],fill=BLACK+(230,),width=U(3))
    # == stencils ==
    f=ImageFont.truetype(RAJD,16*SC)
    bb=md.textbbox((0,0),'AURELIUS',font=f)
    md.text((U(128)-(bb[2]-bb[0])/2,U(150)),'AURELIUS',font=f,fill=KHAKI+(255,))
    f2=ImageFont.truetype(RAJD,10*SC)
    bb2=md.textbbox((0,0),'AERO SQN 24',font=f2)
    md.text((U(128)-(bb2[2]-bb2[0])/2,U(171)),'AERO SQN 24',font=f2,fill=KHAKI_D+(255,))
    bb3=md.textbbox((0,0),'SER. AT-01',font=f2)
    md.text((U(352)-(bb3[2]-bb3[0])/2,U(152)),'SER. AT-01',font=f2,fill=KHAKI_D+(255,))
    md.text((U(330),U(170)),'RESCUE',font=ImageFont.truetype(RAJD,10*SC),fill=(196,150,44,255))
    md.polygon([(U(374),U(173)),(U(384),U(176)),(U(374),U(179))],fill=(196,150,44,255))
    # == date placard ==
    md.rounded_rectangle([U(DATEW[0]-30),U(DATEW[1]-17),U(DATEW[0]+30),U(DATEW[1]+17)],radius=U(3),fill=(30,30,26,255))
    md.rounded_rectangle([U(DATEW[0]-30),U(DATEW[1]-17),U(DATEW[0]+30),U(DATEW[1]+17)],radius=U(3),outline=KHAKI_D+(255,),width=U(2))
    d=_paint_on(d,M,lum_blur=U(2.2),chip_frac=0.018,seed=9,blur=U(0.6),rmax=U(1.6))

    # --- engine cowling opening at 12 ---
    px,py=U(PROP[0]),U(PROP[1]); CW=U(PR_COWL)
    for rr in range(CW,0,-1):
        t=rr/CW
        dd.ellipse([px-rr,py-rr,px+rr,py+rr],fill=_lerp((10,10,9),(34,34,30),t*t)+(255,))
    for k in range(9):   # radial engine cylinders
        a=math.radians(k*40)
        cx_=px+CW*0.62*math.sin(a); cy_=py-CW*0.62*math.cos(a)
        dd.ellipse([cx_-U(9),cy_-U(9),cx_+U(9),cy_+U(9)],fill=(52,52,48,255))
        dd.ellipse([cx_-U(9),cy_-U(9),cx_+U(9),cy_+U(9)],outline=(20,20,18,255),width=SC)
        dd.ellipse([cx_-U(5),cy_-U(5),cx_+U(5),cy_+U(5)],fill=(70,70,64,255))
        dd.ellipse([cx_-U(4),cy_-U(5),cx_-U(1),cy_-U(2)],fill=(120,120,112,200))
    dd.ellipse([px-CW*0.40,py-CW*0.40,px+CW*0.40,py+CW*0.40],fill=(44,44,40,255))
    dd.ellipse([px-CW*0.40,py-CW*0.40,px+CW*0.40,py+CW*0.40],outline=(18,18,16,255),width=SC)
    CB=Image.new('RGBA',(SB,SB),(0,0,0,0)); cbd=ImageDraw.Draw(CB)
    cbd.ellipse([px-CW-U(9),py-CW-U(9),px+CW+U(9),py+CW+U(9)],outline=(52,56,40,255),width=U(11))
    cbd.ellipse([px-CW-U(9),py-CW-U(9),px+CW+U(9),py+CW+U(9)],outline=STEEL_D+(160,),width=U(3))
    cbd.arc([px-CW-U(9),py-CW-U(9),px+CW+U(9),py+CW+U(9)],200,340,fill=(120,124,96,150),width=U(3))
    d=_paint_on(d,CB,lum_blur=U(2.2),chip_frac=0.03,seed=11,blur=U(0.4),rmax=U(3))
    dd=ImageDraw.Draw(d)
    for k in range(12):
        a=math.radians(k*30+15); x=px+(CW+U(9))*math.sin(a); y=py-(CW+U(9))*math.cos(a)
        dd.ellipse([x-U(2),y-U(2),x+U(2),y+U(2)],fill=STEEL_D+(255,))
        dd.ellipse([x-U(1.2),y-U(1.6),x+U(0.2),y-U(0.4)],fill=(190,190,180,150))
    for k in range(60):
        a=math.radians(k*6); big=(k%15==0)
        r1=CW-U(2); r2=CW-U(8 if big else 4)
        col=(RED if k==0 else (KHAKI if big else KHAKI_D))
        dd.line([(px+r1*math.sin(a),py-r1*math.cos(a)),(px+r2*math.sin(a),py-r2*math.cos(a))],fill=col+(230,),width=U(2) if big else SC)

    # --- cockpit gauges ---
    for (gx0,gy0),lab,lo_l,hi_l in ((GAUGE_L,'FUEL','E','F'),(GAUGE_R,'PULSE','40','180')):
        gx,gy=U(gx0),U(gy0); GR=U(GA_R)
        G=Image.new('RGBA',(SB,SB),(0,0,0,0)); gd=ImageDraw.Draw(G)
        gd.ellipse([gx-GR-U(6),gy-GR-U(6),gx+GR+U(6),gy+GR+U(6)],fill=(50,54,40,255))
        gd.ellipse([gx-GR-U(6),gy-GR-U(6),gx+GR+U(6),gy+GR+U(6)],outline=STEEL_D+(255,),width=U(2))
        gd.ellipse([gx-GR,gy-GR,gx+GR,gy+GR],fill=(16,16,14,255))
        gd.ellipse([gx-GR,gy-GR,gx+GR,gy+GR],outline=(90,92,78,255),width=U(2))
        for i in range(9):
            aa=math.radians(-67.5+135*i/8); big=(i%2==0)
            r1=GR-U(4); r2=GR-U(11 if big else 7)
            gd.line([(gx+r1*math.sin(aa),gy-r1*math.cos(aa)),(gx+r2*math.sin(aa),gy-r2*math.cos(aa))],
                    fill=KHAKI+(255,),width=U(2) if big else SC)
        fg=ImageFont.truetype(RAJD,11*SC)
        bbg=gd.textbbox((0,0),lab,font=fg)
        gd.text((gx-(bbg[2]-bbg[0])/2,gy+U(10)),lab,font=fg,fill=KHAKI+(255,))
        fg2=ImageFont.truetype(RAJD,10*SC)
        a0=math.radians(-67.5); a1=math.radians(67.5)
        gd.text((gx+(GR-U(18))*math.sin(a0)-U(4),gy-(GR-U(18))*math.cos(a0)+U(2)),lo_l,font=fg2,fill=KHAKI_D+(255,))
        bbh=gd.textbbox((0,0),hi_l,font=fg2)
        gd.text((gx+(GR-U(18))*math.sin(a1)-(bbh[2]-bbh[0])+U(4),gy-(GR-U(18))*math.cos(a1)+U(2)),hi_l,font=fg2,fill=KHAKI_D+(255,))
        if lab=='FUEL': gd.arc([gx-GR+U(4),gy-GR+U(4),gx+GR-U(4),gy+GR-U(4)],-90-67.5,-90-40,fill=RED+(255,),width=U(4))
        for sa in (45,135,225,315):
            aa=math.radians(sa); x=gx+(GR+U(6))*math.sin(aa)*0.99; y=gy-(GR+U(6))*math.cos(aa)*0.99
            gd.ellipse([x-U(2),y-U(2),x+U(2),y+U(2)],fill=STEEL_D+(255,))
        d.alpha_composite(G)
        gl=Image.new('RGBA',(SB,SB),(0,0,0,0)); gld=ImageDraw.Draw(gl)
        gld.pieslice([gx-GR+U(3),gy-GR+U(3),gx+GR-U(3),gy+GR-U(3)],215,275,fill=(255,255,255,26))
        d.alpha_composite(gl.filter(ImageFilter.GaussianBlur(U(2))))

    # exhaust stains below cowling
    ex_=Image.new('RGBA',(SB,SB),(0,0,0,0)); exd=ImageDraw.Draw(ex_)
    for sx,w_,al in ((214,10,50),(240,14,60),(266,10,50)):
        exd.polygon([(U(sx-w_/2),py+CW+U(6)),(U(sx+w_/2),py+CW+U(6)),(U(sx+w_*1.3),py+CW+U(96)),(U(sx-w_*1.3),py+CW+U(96))],fill=(16,14,10,al))
    d.alpha_composite(ex_.filter(ImageFilter.GaussianBlur(U(6))))

    d.alpha_composite(_grain(SB,20))
    d.convert('RGB').save(f'{ROOT}/tools/bg_hd.png')
    d=d.resize((S,S),Image.LANCZOS)
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255)
    d.putalpha(m); d.save(f'{NODPI}/bg.png')
    a=ImageEnhance.Brightness(d.convert('RGB')).enhance(0.30); a=ImageEnhance.Color(a).enhance(0.6)
    a=a.convert('RGBA'); a.putalpha(m); a.save(f'{NODPI}/bg_aod.png')
    # canopy-glass sheen (built at 480; subtle soft bands)
    sh=Image.new('RGBA',(S,S),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.polygon([(120,0),(210,0),(-30,480),(-120,480)],fill=(255,255,255,22))
    sd.polygon([(258,0),(296,0),(46,480),(8,480)],fill=(255,255,255,16))
    shm=Image.new('L',(S,S),0); smd=ImageDraw.Draw(shm)
    smd.ellipse([6,6,S-6,S-6],fill=255)
    sh=sh.filter(ImageFilter.GaussianBlur(1.2))
    sh.putalpha(ImageChops.multiply(sh.split()[3],shm)); sh.save(f'{NODPI}/sheen.png')
    print('warbird bg + aod + sheen (2x master saved)')

# ------------------------------------------------------------------ live assets
def gen_assets():
    # 3-blade wooden prop + steel spinner (rotates in the cowling; red master tip = seconds)
    ss=4; R=(PR_COWL-4)*ss; W=2*R; im=Image.new('RGBA',(W,W),(0,0,0,0)); d=ImageDraw.Draw(im); c=R
    for bi,ang in enumerate((0,120,240)):
        a=math.radians(ang); dx,dy=math.sin(a),-math.cos(a); qx,qy=math.cos(a),math.sin(a)
        def bw(t):
            base=(8+15*math.sin(math.pi*min(1.0,t*0.94))**0.8)*ss
            if t>0.90: base*=math.sqrt(max(0.05,1-((t-0.90)/0.10)**2))
            return base
        def pt(t,frac):
            r=10*ss+(R-12*ss)*t; o=frac*bw(t)+3.0*ss*math.sin(math.pi*t)*t
            return (c+dx*r+qx*o,c+dy*r+qy*o)
        ts=[i/23 for i in range(24)]
        for k in range(4):
            f0=-0.5+k/4; f1=-0.5+(k+1)/4
            col=((214,168,110) if k%2==0 else (118,74,40))
            d.polygon([pt(t,f0) for t in ts]+[pt(t,f1) for t in reversed(ts)],fill=col+(255,))
        d.polygon([pt(t,0.16) for t in ts]+[pt(t,0.5) for t in reversed(ts)],fill=(40,26,14,70))
        d.line([pt(t,-0.34) for t in ts if t>0.15],fill=(232,210,170,120),width=int(1.2*ss))
        if bi==0:   # red master tip
            tt=[t for t in ts if t>=0.84]
            d.polygon([pt(t,-0.5) for t in tt]+[pt(t,0.5) for t in reversed(tt)],fill=RED+(255,))
    im=im.filter(ImageFilter.GaussianBlur(ss*0.22))
    # spinner cone
    for rr in range(16*ss,0,-1):
        t=rr/(16*ss)
        d.ellipse([c-rr,c-rr,c+rr,c+rr],fill=_lerp(STEEL_HI,STEEL_D,t**1.2)+(255,))
    d.ellipse([c-16*ss,c-16*ss,c+16*ss,c+16*ss],outline=(30,30,26,255),width=ss)
    d.ellipse([c-7*ss,c-9*ss,c-1*ss,c-3*ss],fill=(235,235,228,180))
    im.resize((W//ss,W//ss),Image.LANCZOS).save(f'{NODPI}/prop.png')
    # gauge needle (shared by FUEL / PULSE): full gauge canvas, pointing up, pivot centre
    ss=4; GW=2*(GA_R+6)*ss; n=Image.new('RGBA',(GW,GW),(0,0,0,0)); nd=ImageDraw.Draw(n); c2=GW//2
    L=(GA_R-7)*ss
    nd.polygon([(c2-2.2*ss,c2+10*ss),(c2-1.2*ss,c2-L),(c2+1.2*ss,c2-L),(c2+2.2*ss,c2+10*ss)],fill=WHITE+(255,))
    nd.polygon([(c2-1.0*ss,c2-L*0.55),(c2-0.8*ss,c2-L),(c2+0.8*ss,c2-L),(c2+1.0*ss,c2-L*0.55)],fill=RED+(255,))
    nd.ellipse([c2-4.5*ss,c2-4.5*ss,c2+4.5*ss,c2+4.5*ss],fill=STEEL_D+(255,))
    nd.ellipse([c2-2.2*ss,c2-2.7*ss,c2+0.4*ss,c2-0.2*ss],fill=STEEL_HI+(200,))
    n=n.filter(ImageFilter.GaussianBlur(ss*0.18))
    n.resize((GW//ss,GW//ss),Image.LANCZOS).save(f'{NODPI}/needle.png')
    # centre hub: dark steel dome
    ss=6; R2=12*ss; h=Image.new('RGBA',(2*R2,2*R2),(0,0,0,0)); hd=ImageDraw.Draw(h)
    for rr in range(R2,0,-1):
        t=rr/R2; hd.ellipse([R2-rr,R2-rr,R2+rr,R2+rr],fill=_lerp((150,152,142),(44,46,38),t**1.1)+(255,))
    hd.ellipse([2,2,2*R2-2,2*R2-2],outline=(20,20,16,255),width=int(1.6*ss))
    hd.ellipse([R2-R2*0.5,R2-R2*0.62,R2+R2*0.02,R2-R2*0.08],fill=(230,230,222,170))
    h.resize((24,24),Image.LANCZOS).save(f'{NODPI}/hub.png')
    print('warbird assets: prop needle hub')

# ------------------------------------------------------------------ hands (instrument needles)
def _hand(length,w,tail=24):
    ss=4; C=240*ss; im=Image.new('RGBA',(S*ss,S*ss),(0,0,0,0)); d=ImageDraw.Draw(im)
    L=length*ss; W_=w*ss; T=tail*ss
    sh=Image.new('RGBA',(S*ss,S*ss),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    body=[(C-W_,C+T),(C-W_*0.72,C-L*0.88),(C,C-L),(C+W_*0.72,C-L*0.88),(C+W_,C+T)]
    sd.polygon([(x+4*ss,y+5*ss) for x,y in body],fill=(0,0,0,110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2.4*ss)))
    d.polygon(body,fill=BLACK+(255,))
    d.line(body+[body[0]],fill=WHITE+(230,),width=int(1.4*ss))
    lume=[(C-W_*0.45,C-L*0.16),(C-W_*0.34,C-L*0.82),(C,C-L*0.93),(C+W_*0.34,C-L*0.82),(C+W_*0.45,C-L*0.16)]
    d.polygon(lume,fill=KHAKI+(255,))
    d.polygon([(C-W_*0.34,C-L*0.82),(C,C-L*0.93),(C+W_*0.34,C-L*0.82),(C,C-L*0.70)],fill=RED+(255,))
    im=im.filter(ImageFilter.GaussianBlur(ss*0.16))
    return im.resize((S,S),Image.LANCZOS)
def gen_hands():
    _hand(120,12).save(f'{NODPI}/hour_hand.png')
    _hand(176,9).save(f'{NODPI}/min_hand.png')
    print('instrument hands')

# ------------------------------------------------------------------ glyphs (worn khaki stencil)
CHARS={**{str(n):str(n) for n in range(10)},'%':'pct',':':'colon',' ':'space',
       **{ch:ch.lower() for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
def gen_glyphs():
    ch_h=30; f=ImageFont.truetype(RAJD,ch_h); H=ch_h+8; meta={}
    rnd=random.Random(7)
    for ch,rn in CHARS.items():
        if ch==' ':
            im=Image.new('RGBA',(12,H),(0,0,0,0)); meta[ch]=(f'g_{rn}',12,H); im.save(f'{NODPI}/g_{rn}.png'); continue
        bb=f.getbbox(ch); w=bb[2]-bb[0]+10
        im=Image.new('RGBA',(w,H),(0,0,0,0)); d=ImageDraw.Draw(im); ox,oy=5-bb[0],3
        d.text((ox+1,oy+1),ch,font=f,fill=(12,12,10,200))
        d.text((ox,oy),ch,font=f,fill=KHAKI+(255,))
        a=im.split()[3]
        for _ in range(w*H//55):   # stencil wear
            x=rnd.randint(0,w-1); y=rnd.randint(0,H-1); r=rnd.uniform(0.4,1.4)
            ImageDraw.Draw(a).ellipse([x-r,y-r,x+r,y+r],fill=0)
        im.putalpha(a)
        im.save(f'{NODPI}/g_{rn}.png'); meta[ch]=(f'g_{rn}',w,H)
    json.dump(meta,open(f'{ROOT}/tools/glyphs.json','w')); print('glyphs',len(meta))
def _meta(): return json.load(open(f'{ROOT}/tools/glyphs.json'))

# ------------------------------------------------------------------ preview / anim
def _str(b,s,cx,cy,size):
    m=_meta(); H=list(m.values())[0][2]; sc=size/H; gl=[]; tot=0
    for ch in s:
        ch=ch if ch in m else ' '; nm,w,h=m[ch]; gw=w*sc; gl.append((nm,gw)); tot+=gw
    x=cx-tot/2
    for nm,gw in gl:
        g=Image.open(f'{NODPI}/{nm}.png').convert('RGBA').resize((max(1,int(gw)),int(size)),Image.LANCZOS)
        b.alpha_composite(g,(int(x),int(cy-size/2))); x+=gw
def _p(b,name,cx,cy,alpha=255,rot=0.0):
    im=Image.open(f'{NODPI}/{name}.png').convert('RGBA')
    if rot: im=im.rotate(-rot,resample=Image.BICUBIC)
    if alpha<255: im=im.copy(); im.putalpha(im.split()[3].point(lambda v:int(v*alpha/255)))
    b.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))
def _frame(t,hh=10,mm=9,batt=0.72,hr=88):
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA')
    _p(b,'prop',*PROP,255,(t%60)*6)
    _p(b,'needle',*GAUGE_L,255,-67.5+135*batt)
    _p(b,'needle',*GAUGE_R,255,-67.5+135*max(0,min(1,(hr-40)/140)))
    _str(b,'24',*DATEW,24)
    b.alpha_composite(Image.open(f'{NODPI}/sheen.png').convert('RGBA'))
    for name,ang in (('hour_hand',(hh%12+mm/60)*30),('min_hand',mm*6)):
        h=Image.open(f'{NODPI}/{name}.png').convert('RGBA').rotate(-ang,center=(240,240),resample=Image.BICUBIC)
        b.alpha_composite(h)
    _p(b,'hub',*HUBC)
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255)
    b.putalpha(ImageChops.multiply(b.split()[3],m))
    return b
def compose_preview():
    b=_frame(35.0)
    bl=Image.new('RGBA',(S,S),(0,0,0,255)); bl.alpha_composite(b)
    bl.convert('RGB').save(f'{SCRATCH}/aur_preview.png')
    b.resize((400,400),Image.LANCZOS).save(f'{DRAW}/preview.png'); print('preview saved')
def animate():
    fr=[]
    for i in range(60):
        f_=_frame(i*1.0); bl=Image.new('RGBA',(S,S),(0,0,0,255)); bl.alpha_composite(f_)
        fr.append(bl.convert('RGB').resize((360,360),Image.LANCZOS))
    fr[0].save(f'{SCRATCH}/aur_anim.gif',save_all=True,append_images=fr[1:],duration=90,loop=0,optimize=True)
    print('anim ->',f'{SCRATCH}/aur_anim.gif')
def debug():
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA'); d=ImageDraw.Draw(b)
    for (x,y),lab in ((PROP,'P'),(GAUGE_L,'F'),(GAUGE_R,'H'),(DATEW,'D'),(HUBC,'C')):
        d.line([(x-12,y),(x+12,y)],fill=(0,255,0)); d.line([(x,y-12),(x,y+12)],fill=(0,255,0)); d.text((x+5,y+5),lab,fill=(0,255,0))
    b.convert('RGB').save(f'{SCRATCH}/aur_debug.png'); print('debug overlay saved')

# ------------------------------------------------------------------ WFF XML
PX='clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'; PY='clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
T='([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
HRC='(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 180))'
def Vr(t,v,dur=1.0,off=0.0,ip='LINEAR'): return f'      <Variant mode="AMBIENT" target="{t}" value="{v}" duration="{dur}" startOffset="{off}" interpolation="{ip}" />\n'
def XF(t,v): return f'      <Transform target="{t}" value="{v}" />\n'
def img(name,res,cx,cy,w,h,alpha,kids='',pivot=None):
    piv=f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"' if pivot else ''
    return f'    <PartImage name="{name}" x="{int(cx-w/2)}" y="{int(cy-h/2)}" width="{w}" height="{h}" alpha="{alpha}"{piv}>\n{kids}      <Image resource="{res}" />\n    </PartImage>\n'
def bffonts():
    m=_meta(); esc={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}; rows=''
    for ch,(nm,w,h) in m.items(): rows+=f'      <Character name="{esc.get(ch,ch)}" resource="{nm}" width="{w}" height="{h}" />\n'
    return '  <BitmapFonts>\n    <BitmapFont name="aur">\n'+rows+'    </BitmapFont>\n  </BitmapFonts>\n'
def gen_xml():
    pr=Image.open(f'{NODPI}/prop.png'); ne=Image.open(f'{NODPI}/needle.png')
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="ANALOG" />\n  <Metadata key="PREVIEW_TIME" value="10:09:35" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF060403">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.6,0,'EASE_OUT')+XF('x',f'0 + 3 * {PX}')+XF('y',f'0 + 3 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.6,0,'EASE_IN')))
    o.append(img('z10_prop','prop',*PROP,pr.width,pr.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','120',0.4,0.12)
              +XF('angle','([SECOND] + [MILLISECOND] / 1000) * 6')))
    o.append(img('z20_fuel','needle',*GAUGE_L,ne.width,ne.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','130',0.4,0.16)
              +XF('angle','-67.5 + 135 * clamp([BATTERY_PERCENT], 0, 100) / 100')))
    o.append(img('z21_pulse','needle',*GAUGE_R,ne.width,ne.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','130',0.4,0.18)
              +XF('angle',f'-67.5 + 135 * ({HRC} - 40) / 140')))
    o.append(f'    <PartText name="z30_date" x="{DATEW[0]-28}" y="{DATEW[1]-15}" width="56" height="30">\n'
             +Vr('alpha','150',0.4,0.2)
             +'      <Text align="CENTER"><BitmapFont family="aur" size="25" color="#FFFFFF"><Template>%d<Parameter expression="[DAY]" /></Template></BitmapFont></Text>\n    </PartText>\n')
    o.append(img('z40_sheen','sheen',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.1,'EASE_OUT')
              +XF('alpha',f'120 + 50*sin({T}*0.45)')+XF('x',f'0 + 40 * {PX}')+XF('y',f'0 + 14 * {PY}')))
    o.append(img('z50_hour','hour_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','200',0.5,0.0,'EASE_OUT')+XF('angle','([HOUR_0_11] + [MINUTE] / 60) * 30')))
    o.append(img('z51_min','min_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','200',0.5,0.0,'EASE_OUT')+XF('angle','([MINUTE] + [SECOND] / 60) * 6')))
    o.append(img('z52_hub','hub',*HUBC,24,24,255,kids=Vr('alpha','210',0.4,0.0)))
    o.append('  </Scene>\n</WatchFace>\n')
    open(f'{RES}/raw/watchface.xml','w').write(''.join(o)); print('watchface.xml',len(''.join(o)),'bytes')

if __name__=='__main__':
    st=sys.argv[1] if len(sys.argv)>1 else 'all'
    if st in ('bg','all'): gen_bg()
    if st in ('assets','all'): gen_assets()
    if st in ('hands','all'): gen_hands()
    if st in ('glyphs','all'): gen_glyphs()
    if st in ('xml','all'): gen_xml()
    if st in ('preview','all'): compose_preview()
    if st in ('anim','all'): animate()
    if st=='debug': debug()
