#!/usr/bin/env python3
"""AURELIUS v3 — CEL-SHADED MECHA skeleton tourbillon (WFF v4, Galaxy Watch 7 480x480).
100% procedural cel art: thick warm-black outlines, hard 2-3 tone shading, bold speculars.
Live: tourbillon cage = seconds, balance beats with HR, two rotating gears, reserve = battery.
Stages: bg | assets | hands | glyphs | xml | preview | anim | debug | all"""
import sys, os, json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; S=480
os.makedirs(NODPI,exist_ok=True); os.makedirs(DRAW,exist_ok=True); os.makedirs(f'{RES}/raw',exist_ok=True)
MARC=f'{RES}/font/rajdhani_bold.ttf'
SCRATCH='/tmp/claude-1000/-home-xsyprime-xsywatch/555d57e3-c801-4258-96e7-5de12ef1db82/scratchpad'

TOURB=(240,362); TR_CAGE=58; TR_WELL=66
GEAR_L=(138,268); GL_R=52
GEAR_R=(342,218); GR_R=44
BEZ_IN=206; BEZ_OUT=238; CASE_OUT=240
DATEW=(322,300)
RESV_C=315.0; RESV_SPAN=45.0; RESV_R=178

# ---- cel palette: MILITARY / olive drab ----
OUT=(22,24,16)                                   # dark olive ink outline
RG=(118,124,72); RG_SH=(78,84,48); RG_HI=(162,168,106); RG_SPEC=(212,216,170)   # olive drab paint
PLATE=(52,54,40); PLATE_SH=(37,39,29)            # dial mainplate (dark canvas olive)
BGD=(19,21,15)                                   # deep well background
ST=(112,116,120); ST_SH=(70,74,80); ST_HI=(164,170,176)                          # parkerized gunmetal
RUBY=(202,52,40); RUBY_SH=(140,28,22); CREAM=(224,208,160); CREAM_SH=(172,158,118)  # red + khaki
BLUE=(92,156,255); BLUE_SH=(44,92,196)
WOOD=(150,96,54); WOOD_SH=(104,64,36); LAM=(206,160,104); LAM_SH=(174,128,76)       # laminated prop wood
BRASS=(196,164,84); BRASS_SH=(140,112,52); BRASS_HI=(232,208,132)                    # sheathed tips

def _shade_mask(size,cx,cy,r,off=0.30):
    """hard cel shade: circle minus itself offset toward light (top-left) -> bottom-right crescent"""
    m=Image.new('L',size,0); d=ImageDraw.Draw(m)
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=255)
    d.ellipse([cx-r-r*off,cy-r-r*off,cx+r-r*off,cy+r-r*off],fill=0)
    return m
def cel_disc(d,im,cx,cy,r,base,shade,ow,spec=True):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=base+(255,))
    sm=_shade_mask(im.size,cx,cy,r-ow*0.5)
    sh=Image.new('RGBA',im.size,(0,0,0,0)); sh.paste(shade+(255,),(0,0),sm); im.alpha_composite(sh)
    if spec:
        d.ellipse([cx-r*0.55,cy-r*0.62,cx-r*0.10,cy-r*0.28],fill=RG_SPEC+(230,) if base==RG else ST_HI+(235,))
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline=OUT+(255,),width=ow)

def cel_gear(r,teeth,spokes,steel=True,ss=3,seed=1,ruby=True):
    R=r*ss; W=2*(R+int(R*0.16)); im=Image.new('RGBA',(W,W),(0,0,0,0)); d=ImageDraw.Draw(im); c=W//2
    base,shade=(ST,ST_SH) if steel else (RG,RG_SH); ow=max(2,int(2.2*ss))
    # chunky teeth
    tw=math.pi/teeth*0.62
    for k in range(teeth):
        a0=2*math.pi*k/teeth
        p=[]
        for aa,rr in ((a0-tw,0.90),(a0-tw*0.42,1.10),(a0+tw*0.42,1.10),(a0+tw,0.90)):
            p.append((c+R*rr*math.sin(aa),c-R*rr*math.cos(aa)))
        d.polygon(p,fill=base+(255,),outline=OUT+(255,),width=ow)
    cel_disc(d,im,c,c,int(R*0.94),base,shade,ow); d=ImageDraw.Draw(im)
    # big round spoke holes
    for k in range(spokes):
        a0=2*math.pi*k/spokes+0.55
        hx=c+R*0.56*math.sin(a0); hy=c-R*0.56*math.cos(a0); hr=R*0.225
        d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],fill=(0,0,0,0))
        d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr],outline=OUT+(255,),width=ow)
        d.arc([hx-hr,hy-hr,hx+hr,hy+hr],200,340,fill=(0,0,0,90),width=int(hr*0.35))
    # hub + jewel + glint
    cel_disc(d,im,c,c,int(R*0.30),base,shade,ow,spec=False); d=ImageDraw.Draw(im)
    if ruby:
        d.ellipse([c-R*0.15,c-R*0.15,c+R*0.15,c+R*0.15],fill=RUBY+(255,),outline=OUT+(255,),width=ow)
        d.ellipse([c-R*0.15,c-R*0.02,c+R*0.15,c+R*0.15],fill=RUBY_SH+(140,))
        d.ellipse([c-R*0.085,c-R*0.10,c-R*0.015,c-R*0.03],fill=(255,255,255,255))
    return im.resize((W//ss,W//ss),Image.LANCZOS)

def _oct(r,cx=240,cy=240):
    return [(cx+r*math.sin(math.radians(22.5+45*k)),cy-r*math.cos(math.radians(22.5+45*k))) for k in range(8)]

# ------------------------------------------------------------------ background
def gen_bg():
    ss=3; SS=S*ss
    im=Image.new('RGBA',(SS,SS),BGD+(255,)); d=ImageDraw.Draw(im)
    OW=max(3,int(2.4*ss))
    def P(v): return v*ss
    # --- deep background: faint static cel gears (sit back, muted) ---
    rnd=random.Random(8)
    for (gx,gy,gr,tt) in ((88,120,52,12),(392,132,46,11),(150,420,44,10),(388,352,48,11),(240,120,58,13),(60,270,42,10)):
        g=cel_gear(gr,tt,3,steel=True,ss=3,ruby=False)
        g=ImageEnhance.Brightness(g).enhance(0.62); g=ImageEnhance.Color(g).enhance(0.7)
        g=g.resize((g.width*ss//3,g.height*ss//3),Image.LANCZOS)
        im.alpha_composite(g,(P(gx)-g.width//2,P(gy)-g.height//2))
    # --- mainplate: full disc with big skeleton cutouts ---
    plate=Image.new('RGBA',(SS,SS),(0,0,0,0)); pd=ImageDraw.Draw(plate)
    pd.ellipse([P(240-BEZ_IN)]*2+[P(240+BEZ_IN)]*2,fill=PLATE+(255,))
    # skeleton cutout holes (reveal bg gears)
    holes=((88,120,58),(392,132,52),(150,420,50),(388,352,54),(240,120,64),(60,270,46),(240,240,0))
    for hx,hy,hr in holes:
        if hr: pd.ellipse([P(hx-hr),P(hy-hr),P(hx+hr),P(hy+hr)],fill=(0,0,0,0))
    # cutout ink rims + inner shadow arcs
    for hx,hy,hr in holes:
        if hr:
            pd.ellipse([P(hx-hr),P(hy-hr),P(hx+hr),P(hy+hr)],outline=OUT+(255,),width=OW)
            pd.arc([P(hx-hr),P(hy-hr),P(hx+hr),P(hy+hr)],200,340,fill=(0,0,0,110),width=int(P(hr)*0.22))
    # plate hard shade (bottom-right)
    smask=Image.new('L',(SS,SS),0); smd=ImageDraw.Draw(smask)
    smd.ellipse([P(240-BEZ_IN)]*2+[P(240+BEZ_IN)]*2,fill=255)
    smd.ellipse([P(240-BEZ_IN-40)]*2+[P(240+BEZ_IN-40)]*2,fill=0)
    smd.pieslice([P(240-BEZ_IN-5)]*2+[P(240+BEZ_IN+5)]*2,200,60,fill=0)
    shl=Image.new('RGBA',(SS,SS),(0,0,0,0)); shl.paste(PLATE_SH+(255,),(0,0),ImageChops.multiply(smask,plate.split()[3]))
    plate.alpha_composite(shl)
    im.alpha_composite(plate)
    # --- minute track ring ---
    for k in range(60):
        a=math.radians(k*6); big=(k%5==0)
        r1,r2=BEZ_IN-4,BEZ_IN-(14 if big else 9)
        d.line([(P(240)+P(r1)*math.sin(a),P(240)-P(r1)*math.cos(a)),(P(240)+P(r2)*math.sin(a),P(240)-P(r2)*math.cos(a))],
               fill=(CREAM if big else CREAM_SH)+(255,),width=(3 if big else 2)*ss)
    # --- hour markers 12/3/9 (cel batons) ---
    for ang in (0,90,270):
        a=math.radians(ang)
        mx,my=240+176*math.sin(a),240-176*math.cos(a)
        bw,bh=(11,30) if ang==0 else (26,12)
        mcol,mhi=(RUBY,RUBY_SH) if ang==0 else (CREAM,CREAM_SH)   # red 12, khaki 3/9 (field-watch)
        d.rounded_rectangle([P(mx-bw/2),P(my-bh/2),P(mx+bw/2),P(my+bh/2)],radius=4*ss,fill=mcol+(255,),outline=OUT+(255,),width=OW)
        d.rounded_rectangle([P(mx-bw/2+3),P(my-bh/2+2),P(mx-bw/2+7),P(my+bh/2-2)],radius=2*ss,fill=mhi+(120,))
    # --- central 4-blade WW1 wooden propeller (laminated, brass tips, bolted hub) ---
    br=Image.new('RGBA',(SS,SS),(0,0,0,0)); bd2=ImageDraw.Draw(br)
    NPT=26; L=152
    for ang in (45,135,225,315):
        a=math.radians(ang); dx,dy=math.sin(a),-math.cos(a); qx,qy=math.cos(a),math.sin(a)
        def bw(t):   # blade width profile: fat paddle, rounded tip
            base=12+21*math.sin(math.pi*min(1.0,t*0.96))**0.72
            if t<0.10: base*=0.6+4.0*t
            if t>0.92: base*=math.sqrt(max(0.05,1-((t-0.92)/0.08)**2))
            return base
        def cam(t): return 4.5*math.sin(math.pi*t)*t         # subtle scimitar sweep
        def pt(t,frac):
            r=22+(L-22)*t; o=cam(t)+frac*bw(t)
            return (P(240+dx*r+qx*o),P(240+dy*r+qy*o))
        ts=[i/(NPT-1) for i in range(NPT)]
        # laminate stripes (lengthwise, bold alternating)
        NST=4
        for k in range(NST):
            f0=-0.5+k/NST; f1=-0.5+(k+1)/NST
            col=(LAM if k%2==0 else WOOD)
            poly=[pt(t,f0) for t in ts]+[pt(t,f1) for t in reversed(ts)]
            bd2.polygon(poly,fill=col+(255,))
        # hard cel shade on trailing half (keeps laminate visible underneath)
        shp=[pt(t,0.18) for t in ts]+[pt(t,0.5) for t in reversed(ts)]
        bd2.polygon(shp,fill=(30,22,14,86))
        # brass-sheathed tip (outer 12%)
        tt=[t for t in ts if t>=0.86]
        poly=[pt(t,-0.5) for t in tt]+[pt(t,0.5) for t in reversed(tt)]
        bd2.polygon(poly,fill=BRASS+(255,))
        bd2.polygon([pt(t,0.1) for t in tt]+[pt(t,0.5) for t in reversed(tt)],fill=BRASS_SH+(255,))
        bd2.line([pt(t,-0.38) for t in tt],fill=BRASS_HI+(255,),width=2*ss)
        # brass leading-edge strip
        le=[t for t in ts if 0.40<=t<=0.90]
        bd2.polygon([pt(t,-0.5) for t in le]+[pt(t,-0.36) for t in reversed(le)],fill=BRASS+(255,))
        # ink outline
        outline=[pt(t,-0.5) for t in ts]+[pt(t,0.5) for t in reversed(ts)]
        bd2.line(outline+[outline[0]],fill=OUT+(255,),width=OW,joint='curve')
        # glint on leading belly
        gl=[t for t in ts if 0.25<=t<=0.80]
        bd2.line([pt(t,-0.30) for t in gl],fill=(255,244,214,120),width=int(2.2*ss))
    # bolted hub boss (under the hands hub)
    bd2.ellipse([P(240-30)]*2+[P(240+30)]*2,fill=ST+(255,),outline=OUT+(255,),width=OW)
    bd2.ellipse([P(240-30),P(240+2),P(240+30),P(240+30)],fill=ST_SH+(150,))
    for k in range(6):
        ba=math.radians(60*k+30); bxx,byy=240+22*math.sin(ba),240-22*math.cos(ba)
        bd2.ellipse([P(bxx-4),P(byy-4),P(bxx+4),P(byy+4)],fill=ST_HI+(255,),outline=OUT+(255,),width=max(2,OW-ss))
    im.alpha_composite(br)
    # --- tourbillon well ---
    tx,ty=TOURB
    d.ellipse([P(tx-TR_WELL-8),P(ty-TR_WELL-8),P(tx+TR_WELL+8),P(ty+TR_WELL+8)],fill=RG+(255,),outline=OUT+(255,),width=OW)
    d.arc([P(tx-TR_WELL-8),P(ty-TR_WELL-8),P(tx+TR_WELL+8),P(ty+TR_WELL+8)],35,160,fill=RG_SH+(255,),width=int(4.5*ss))
    d.arc([P(tx-TR_WELL-8),P(ty-TR_WELL-8),P(tx+TR_WELL+8),P(ty+TR_WELL+8)],195,320,fill=RG_HI+(255,),width=int(3*ss))
    d.ellipse([P(tx-TR_WELL),P(ty-TR_WELL),P(tx+TR_WELL),P(ty+TR_WELL)],fill=BGD+(255,),outline=OUT+(255,),width=OW)
    for k in range(60):   # seconds ticks
        a=math.radians(k*6); big=(k%15==0)
        r1=TR_WELL-2; r2=TR_WELL-(10 if big else 6)
        d.line([(P(tx)+P(r1)*math.sin(a),P(ty)-P(r1)*math.cos(a)),(P(tx)+P(r2)*math.sin(a),P(ty)-P(r2)*math.cos(a))],
               fill=(CREAM if big else CREAM_SH)+(255,),width=(2 if big else 1)*ss+ss)
    # --- date window ---
    wx,wy=DATEW
    d.rounded_rectangle([P(wx-26),P(wy-17),P(wx+26),P(wy+17)],radius=6*ss,fill=RG+(255,),outline=OUT+(255,),width=OW)
    d.rounded_rectangle([P(wx-21),P(wy-12),P(wx+21),P(wy+12)],radius=4*ss,fill=(16,13,17,255),outline=OUT+(255,),width=max(2,OW-ss))
    # --- power reserve arc ---
    a0,a1=RESV_C-RESV_SPAN/2,RESV_C+RESV_SPAN/2
    d.arc([P(240-RESV_R)]*2+[P(240+RESV_R)]*2,a0-90,a1-90,fill=CREAM+(255,),width=3*ss)
    for i in range(5):
        a=math.radians(a0+RESV_SPAN*i/4); r1,r2=RESV_R+2,RESV_R-(9 if i%2==0 else 6)
        d.line([(P(240)+P(r1)*math.sin(a),P(240)-P(r1)*math.cos(a)),(P(240)+P(r2)*math.sin(a),P(240)-P(r2)*math.cos(a))],fill=CREAM+(255,),width=2*ss)
    fbat=ImageFont.truetype(MARC,11*ss)
    bbr=d.textbbox((0,0),'RESERVE',font=fbat)
    rx=240+(RESV_R-26)*math.sin(math.radians(RESV_C)); ry=240-(RESV_R-26)*math.cos(math.radians(RESV_C))
    d.text((P(rx)-(bbr[2]-bbr[0])/2,P(ry)),'RESERVE',font=fbat,fill=CREAM+(230,),stroke_width=ss,stroke_fill=OUT+(200,))
    # --- octagonal bezel (cel: alternating lit/shade flats, thick ink) ---
    LIGHT=math.radians(-45)
    for rr in range(CASE_OUT,BEZ_OUT-2,-1):
        d.ellipse([P(240-rr)]*2+[P(240+rr)]*2,outline=(30,28,32,255),width=3*ss)
    corners=_oct(BEZ_OUT)
    for k in range(8):
        p1,p2=corners[k],corners[(k+1)%8]
        na=math.radians(45+45*k); lit=math.cos(na-LIGHT)
        col=RG_HI if lit>0.55 else (RG if lit>-0.3 else RG_SH)
        seg=[(P(x),P(y)) for x,y in (p1,p2)]
        aa1=math.degrees(math.atan2(p2[0]-240,-(p2[1]-240))); aa0=math.degrees(math.atan2(p1[0]-240,-(p1[1]-240)))
        if aa1<aa0: aa1+=360
        for q in range(13):
            a=math.radians(aa1+(aa0-aa1)*q/12)
            seg.append((P(240)+P(BEZ_IN)*math.sin(a),P(240)-P(BEZ_IN)*math.cos(a)))
        d.polygon(seg,fill=col+(255,))
    d.line([(P(x),P(y)) for x,y in corners+[corners[0]]],fill=OUT+(255,),width=OW+ss,joint='curve')
    d.ellipse([P(240-BEZ_IN)]*2+[P(240+BEZ_IN)]*2,outline=OUT+(255,),width=OW+ss)
    d.ellipse([P(240-BEZ_IN+4)]*2+[P(240+BEZ_IN-0)]*2,outline=RG_SPEC+(120,),width=2*ss)
    # bezel screws (cel hex)
    for k in range(8):
        a=math.radians(22.5+45*k); r=(BEZ_IN+BEZ_OUT)/2
        x,y=240+r*math.sin(a),240-r*math.cos(a); sr=13
        d.ellipse([P(x-sr),P(y-sr),P(x+sr),P(y+sr)],fill=ST+(255,),outline=OUT+(255,),width=OW)
        d.ellipse([P(x-sr),P(y),P(x+sr),P(y+sr)],fill=ST_SH+(160,))
        hexp=[(P(x)+P(sr*0.55)*math.sin(math.radians(20+60*j)),P(y)-P(sr*0.55)*math.cos(math.radians(20+60*j))) for j in range(6)]
        d.polygon(hexp,fill=(52,50,56,255))
        d.ellipse([P(x-sr*0.45),P(y-sr*0.55),P(x-sr*0.05),P(y-sr*0.15)],fill=(255,255,255,235))
    # brand
    f=ImageFont.truetype(MARC,15*ss); txt='A U R E L I U S'
    bb=d.textbbox((0,0),txt,font=f); tx0=P(240)-(bb[2]-bb[0])/2; ty0=P(240-BEZ_OUT+10)
    d.text((tx0+ss,ty0+ss),txt,font=f,fill=(255,236,214,120)); d.text((tx0,ty0),txt,font=f,fill=OUT+(255,))
    f2=ImageFont.truetype(MARC,10*ss); txt2='FIELD TOURBILLON'; bb2=d.textbbox((0,0),txt2,font=f2)
    d.text((P(240)-(bb2[2]-bb2[0])/2,P(240+BEZ_OUT-26)),txt2,font=f2,fill=CREAM+(255,),stroke_width=ss,stroke_fill=OUT+(255,))
    # done
    fin=im.resize((S,S),Image.LANCZOS)
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255)
    fin.putalpha(m); fin.save(f'{NODPI}/bg.png')
    a=ImageEnhance.Brightness(fin.convert('RGB')).enhance(0.32); a=ImageEnhance.Color(a).enhance(0.6)
    a=a.convert('RGBA'); a.putalpha(m); a.save(f'{NODPI}/bg_aod.png')
    # anime glass shine: two hard-edged translucent bands
    sh=Image.new('RGBA',(S,S),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.polygon([(96,0),(214,0),(-40,480),(-158,480)],fill=(255,255,255,34))
    sd.polygon([(260,0),(308,0),(54,480),(6,480)],fill=(255,255,255,26))
    shm=Image.new('L',(S,S),0); smd2=ImageDraw.Draw(shm)
    for rr in range(BEZ_IN,0,-1):
        smd2.ellipse([240-rr,240-rr,240+rr,240+rr],fill=255 if rr<BEZ_IN-12 else int(255*(BEZ_IN-rr)/12))
    sh.putalpha(ImageChops.multiply(sh.split()[3],shm)); sh.save(f'{NODPI}/sheen.png')
    print('cel bg + bg_aod + sheen')

# ------------------------------------------------------------------ live assets
def gen_assets():
    cel_gear(GL_R,14,4,steel=True).save(f'{NODPI}/gear_l.png')
    cel_gear(GR_R,12,3,steel=False).save(f'{NODPI}/gear_r.png')
    # balance wheel (cel steel ring + curved spokes)
    ss=3; R=42*ss; W=2*R+8*ss; b=Image.new('RGBA',(W,W),(0,0,0,0)); bd=ImageDraw.Draw(b); c=W//2
    ow=max(2,int(2.2*ss))
    bd.ellipse([c-R,c-R,c+R,c+R],outline=OUT+(255,),width=int(R*0.30))
    bd.ellipse([c-R+int(R*0.055),c-R+int(R*0.055),c+R-int(R*0.055),c+R-int(R*0.055)],outline=ST+(255,),width=int(R*0.19))
    bd.arc([c-R+int(R*0.055)]*2+[c+R-int(R*0.055)]*2,25,150,fill=ST_SH+(255,),width=int(R*0.16))
    bd.arc([c-R+int(R*0.07)]*2+[c+R-int(R*0.07)]*2,200,300,fill=ST_HI+(255,),width=int(R*0.08))
    for k in range(4):    # gold timing weights
        a=math.radians(90*k+45); x=c+R*0.86*math.sin(a); y=c-R*0.86*math.cos(a)
        bd.ellipse([x-R*0.10,y-R*0.10,x+R*0.10,y+R*0.10],fill=RG+(255,),outline=OUT+(255,),width=ow)
    for sgn in (1,-1):
        pts=[]
        for q in range(19):
            t=q/18.0; a=sgn*(0.35+1.9*t); rr=R*0.82*t
            pts.append((c+rr*math.sin(a),c-rr*math.cos(a)))
        bd.line(pts,fill=OUT+(255,),width=int(R*0.14))
        bd.line(pts,fill=ST+(255,),width=int(R*0.08))
    bd.ellipse([c-R*0.16,c-R*0.16,c+R*0.16,c+R*0.16],fill=RUBY+(255,),outline=OUT+(255,),width=ow)
    bd.ellipse([c-R*0.09,c-R*0.11,c-R*0.01,c-R*0.03],fill=(255,255,255,255))
    b.resize((W//ss,W//ss),Image.LANCZOS).save(f'{NODPI}/balance.png')
    # tourbillon cage: 3 chunky cel arms + ring + ruby + red seconds marker
    ss=3; R=TR_CAGE*ss; W=2*R+6*ss; g=Image.new('RGBA',(W,W),(0,0,0,0)); gd=ImageDraw.Draw(g); c=W//2
    ow=max(3,int(2.6*ss))
    gd.ellipse([c-R,c-R,c+R,c+R],outline=OUT+(255,),width=int(R*0.17))
    gd.ellipse([c-R+int(R*0.045)]*2*1+[c+R-int(R*0.045),c+R-int(R*0.045)],outline=RG+(255,),width=int(R*0.09))
    gd.arc([c-R+int(R*0.045)]*2+[c+R-int(R*0.045)]*2,200,330,fill=RG_HI+(255,),width=int(R*0.05))
    gd.arc([c-R+int(R*0.045)]*2+[c+R-int(R*0.045)]*2,30,140,fill=RG_SH+(255,),width=int(R*0.06))
    for k in range(3):
        ang=math.radians(120*k)
        ex,ey=c+R*0.93*math.sin(ang),c-R*0.93*math.cos(ang)
        # tapered arm
        na=ang+math.pi/2; nx,ny=math.sin(na),-math.cos(na)
        w0,w1=R*0.16,R*0.085
        p=[(c+w0*nx,c+w0*ny),(ex+w1*nx,ey+w1*ny),(ex-w1*nx,ey-w1*ny),(c-w0*nx,c-w0*ny)]
        gd.polygon(p,fill=RG+(255,),outline=OUT+(255,),width=ow)
        gd.line([(c+w0*0.45*nx+ (ex-c)*0.12, c+w0*0.45*ny+(ey-c)*0.12),(ex+w1*0.3*nx-(ex-c)*0.06,ey+w1*0.3*ny-(ey-c)*0.06)],fill=RG_HI+(255,),width=int(R*0.045))
        gd.ellipse([ex-R*0.085,ey-R*0.085,ex+R*0.085,ey+R*0.085],fill=ST+(255,),outline=OUT+(255,),width=max(2,ow-ss))
    # red seconds marker triangle on ring
    gd.polygon([(c,int(c-R+R*0.02)),(c-R*0.11,int(c-R+R*0.24)),(c+R*0.11,int(c-R+R*0.24))],fill=(236,60,60,255))
    gd.polygon([(c,int(c-R+R*0.02)),(c-R*0.11,int(c-R+R*0.24)),(c+R*0.11,int(c-R+R*0.24))],outline=OUT+(255,),width=max(2,ow-ss))
    gd.ellipse([c-R*0.20,c-R*0.20,c+R*0.20,c+R*0.20],fill=RG+(255,),outline=OUT+(255,),width=ow)
    gd.ellipse([c-R*0.20,c-R*0.02,c+R*0.20,c+R*0.20],fill=RG_SH+(150,))
    gd.ellipse([c-R*0.115,c-R*0.115,c+R*0.115,c+R*0.115],fill=RUBY+(255,),outline=OUT+(255,),width=max(2,ow-ss))
    gd.ellipse([c-R*0.075,c-R*0.09,c-R*0.01,c-R*0.03],fill=(255,255,255,255))
    g.resize((W//ss,W//ss),Image.LANCZOS).save(f'{NODPI}/cage.png')
    # reserve needle (cel)
    n=Image.new('RGBA',(S*2,S*2),(0,0,0,0)); nd=ImageDraw.Draw(n)
    tipy=(240-RESV_R-6)*2
    nd.polygon([(480,tipy),(480-9,tipy+30),(480+9,tipy+30)],fill=RUBY+(255,),outline=OUT+(255,),width=3)
    n=n.resize((S,S),Image.LANCZOS); n.save(f'{NODPI}/resv_needle.png')
    # hub
    ss2=6; R2=14*ss2; h=Image.new('RGBA',(2*R2,2*R2),(0,0,0,0)); hd=ImageDraw.Draw(h); c2=R2
    hd.ellipse([2,2,2*R2-2,2*R2-2],fill=RG+(255,),outline=OUT+(255,),width=int(2.4*ss2))
    hd.ellipse([c2-R2*0.86,c2,c2+R2*0.86,c2+R2*0.86],fill=RG_SH+(140,))
    hd.ellipse([c2-R2*0.5,c2-R2*0.5,c2+R2*0.5,c2+R2*0.5],fill=RUBY+(255,),outline=OUT+(255,),width=int(1.8*ss2))
    hd.ellipse([c2-R2*0.30,c2-R2*0.36,c2-R2*0.02,c2-R2*0.08],fill=(255,255,255,255))
    h.resize((28,28),Image.LANCZOS).save(f'{NODPI}/hub.png')
    print('cel assets: gear_l gear_r balance cage resv_needle hub')

# ------------------------------------------------------------------ hands
def _cel_hand(length,wbase,wtip):
    ss=3; C=240*ss; im=Image.new('RGBA',(S*ss,S*ss),(0,0,0,0)); d=ImageDraw.Draw(im)
    L=length*ss; wb=wbase*ss; wt=wtip*ss; tail=26*ss; ow=int(2.6*ss)
    poly=[(C-wb,C+tail),(C-wb,C-L*0.60),(C-wt,C-L),(C+wt,C-L),(C+wb,C-L*0.60),(C+wb,C+tail)]
    # ink shadow offset (cel drop)
    sh=[(x+4*ss,y+5*ss) for x,y in poly]
    d.polygon(sh,fill=(0,0,0,90))
    d.polygon(poly,fill=ST+(255,),outline=OUT+(255,),width=ow)
    # hard shade right half
    d.polygon([(C,C+tail),(C,C-L),(C+wt-ow,C-L+ow),(C+wb-ow,C-L*0.60),(C+wb-ow,C+tail)],fill=ST_SH+(255,))
    # skeleton slot
    sl=max(3*ss,int(wb*0.40))
    slot=[(C-sl,C-L*0.52),(C-sl*0.5,C-L*0.84),(C+sl*0.5,C-L*0.84),(C+sl,C-L*0.52),(C+sl,C-10*ss),(C-sl,C-10*ss)]
    d.polygon(slot,fill=(0,0,0,0)); d.polygon(slot,outline=OUT+(255,),width=ow)
    # lume tip (khaki, cel) — overlaps the tip outline so it doesn't float
    d.polygon([(C-wt*0.72,C-L+ow*0.6),(C+wt*0.72,C-L+ow*0.6),(C+wb*0.45,C-L*0.88),(C-wb*0.45,C-L*0.88)],fill=CREAM+(255,))
    d.polygon([(C-wt*0.72,C-L+ow*0.6),(C+wt*0.72,C-L+ow*0.6),(C+wb*0.45,C-L*0.88),(C-wb*0.45,C-L*0.88)],outline=OUT+(255,),width=max(2,ow-ss))
    # bright spine
    d.line([(C-wb+2.4*ss,C+tail-3*ss),(C-wb+2.4*ss,C-L*0.60),(C-wt+2.4*ss,C-L+3*ss)],fill=ST_HI+(255,),width=int(2.2*ss))
    return im.resize((S,S),Image.LANCZOS)
def gen_hands():
    _cel_hand(124,12,8).save(f'{NODPI}/hour_hand.png')
    _cel_hand(178,10,6).save(f'{NODPI}/min_hand.png')
    print('cel hands')

# ------------------------------------------------------------------ glyphs (cream, ink outline)
CHARS={**{str(n):str(n) for n in range(10)},'%':'pct',':':'colon',' ':'space',
       **{ch:ch.lower() for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
def gen_glyphs():
    ch_h=30; f=ImageFont.truetype(MARC,ch_h); H=ch_h+10; meta={}
    for ch,rn in CHARS.items():
        if ch==' ':
            im=Image.new('RGBA',(12,H),(0,0,0,0)); meta[ch]=(f'g_{rn}',12,H); im.save(f'{NODPI}/g_{rn}.png'); continue
        bb=f.getbbox(ch); w=bb[2]-bb[0]+12
        im=Image.new('RGBA',(w,H),(0,0,0,0)); d=ImageDraw.Draw(im); ox,oy=6-bb[0],4
        d.text((ox,oy),ch,font=f,fill=CREAM+(255,),stroke_width=2,stroke_fill=OUT+(255,))
        gm=Image.new('L',(w,H),0); ImageDraw.Draw(gm).text((ox,oy),ch,font=f,fill=255)
        shl=Image.new('RGBA',(w,H),(0,0,0,0)); sd=ImageDraw.Draw(shl)
        sd.rectangle([0,H//2,w,H],fill=CREAM_SH+(120,))
        im.alpha_composite(Image.composite(shl,Image.new('RGBA',(w,H),(0,0,0,0)),gm))
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
def _frame(t,hh=10,mm=9):
    b=Image.open(f'{NODPI}/bg.png').convert('RGBA')
    _p(b,'gear_l',*GEAR_L,255,(t*40)%360)
    _p(b,'gear_r',*GEAR_R,255,(-t*24)%360)
    _p(b,'balance',*TOURB,255,35*math.sin(t*7.33))
    _p(b,'cage',*TOURB,255,(t%60)*6)
    _str(b,'24',*DATEW,24)
    _p(b,'resv_needle',240,240,255,(RESV_C-RESV_SPAN/2+RESV_SPAN*0.88))
    b.alpha_composite(Image.open(f'{NODPI}/sheen.png').convert('RGBA'))
    for name,ang in (('hour_hand',(hh%12+mm/60)*30),('min_hand',mm*6)):
        h=Image.open(f'{NODPI}/{name}.png').convert('RGBA').rotate(-ang,center=(240,240),resample=Image.BICUBIC)
        b.alpha_composite(h)
    _p(b,'hub',240,240)
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
    for (x,y),lab in ((TOURB,'T'),(GEAR_L,'L'),(GEAR_R,'R'),(DATEW,'D'),((240,240),'C')):
        d.line([(x-12,y),(x+12,y)],fill=(0,255,0)); d.line([(x,y-12),(x,y+12)],fill=(0,255,0)); d.text((x+5,y+5),lab,fill=(0,255,0))
    b.convert('RGB').save(f'{SCRATCH}/aur_debug.png'); print('debug overlay saved')

# ------------------------------------------------------------------ WFF XML
PX='clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'; PY='clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'
T='([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'
BPM='(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 200))'
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
    gl=Image.open(f'{NODPI}/gear_l.png'); gr=Image.open(f'{NODPI}/gear_r.png')
    bal=Image.open(f'{NODPI}/balance.png'); cg=Image.open(f'{NODPI}/cage.png')
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="ANALOG" />\n  <Metadata key="PREVIEW_TIME" value="10:09:35" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF060403">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.6,0,'EASE_OUT')+XF('x',f'0 + 3 * {PX}')+XF('y',f'0 + 3 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.6,0,'EASE_IN')))
    o.append(img('z10_gl','gear_l',*GEAR_L,gl.width,gl.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','90',0.4,0.1)+XF('angle',f'({T} * 40) % 360')))
    o.append(img('z11_gr','gear_r',*GEAR_R,gr.width,gr.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','90',0.4,0.12)+XF('angle',f'360 - (({T} * 24) % 360)')))
    o.append(img('z21_bal','balance',*TOURB,bal.width,bal.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','100',0.4,0.16)
              +XF('angle',f'180 + 35 * sin({T} * {BPM} * 0.10472)')))
    o.append(img('z22_cage','cage',*TOURB,cg.width,cg.height,255,pivot=('0.5','0.5'),kids=Vr('alpha','130',0.4,0.16)
              +XF('angle','([SECOND] + [MILLISECOND] / 1000) * 6')))
    o.append(f'    <PartText name="z30_date" x="{DATEW[0]-30}" y="{DATEW[1]-14}" width="60" height="28">\n'
             +Vr('alpha','140',0.4,0.2)
             +'      <Text align="CENTER"><BitmapFont family="aur" size="24" color="#FFFFFF"><Template>%d<Parameter expression="[DAY]" /></Template></BitmapFont></Text>\n    </PartText>\n')
    o.append(img('z31_resv','resv_needle',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','120',0.4,0.2)
              +XF('angle',f'{RESV_C-RESV_SPAN/2} + {RESV_SPAN} * clamp([BATTERY_PERCENT], 0, 100) / 100')))
    o.append(img('z40_sheen','sheen',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.1,'EASE_OUT')
              +XF('alpha',f'150 + 60*sin({T}*0.45)')+XF('x',f'0 + 40 * {PX}')+XF('y',f'0 + 14 * {PY}')))
    o.append(img('z50_hour','hour_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','190',0.5,0.0,'EASE_OUT')+XF('angle','([HOUR_0_11] + [MINUTE] / 60) * 30')))
    o.append(img('z51_min','min_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','190',0.5,0.0,'EASE_OUT')+XF('angle','([MINUTE] + [SECOND] / 60) * 6')))
    o.append(img('z52_hub','hub',240,240,28,28,255,kids=Vr('alpha','200',0.4,0.0)))
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
