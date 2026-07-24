#!/usr/bin/env python3
"""AURELIUS — Skeleton Tourbillon v2 PHOTOREAL (WFF v4, Galaxy Watch 7 480x480).
v2: everything photographic. bg composed at native 960 then img2img-refined (Juggernaut-XL);
rotating gears are PHOTO DISCS cut from the dial itself; the tourbillon is a real photo
tourbillon disc cut from seed 811013; hands are img2img-photified with silhouette re-cut.
Stages: bg | photify | finalize | assets | hands | glyphs | xml | preview | anim | debug | all
(photify + hands need ComfyUI on :8188; 'all' runs the full chain in order)"""
import sys, os, json, math, random, time, shutil, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageEnhance

ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))); RES=f'{ROOT}/app/src/main/res'
NODPI=f'{RES}/drawable-nodpi'; DRAW=f'{RES}/drawable'; S=480
os.makedirs(NODPI,exist_ok=True); os.makedirs(DRAW,exist_ok=True); os.makedirs(f'{RES}/raw',exist_ok=True)
SRC=f'{ROOT}/tools/dial_src.png'
TOURB_SRC='/home/xsyprime/AI/ComfyUI/output/aurelius_00003_.png'   # photo tourbillon donor
MARC=f'{RES}/font/marcellus.ttf'
SCRATCH='/tmp/claude-1000/-home-xsyprime-xsywatch/555d57e3-c801-4258-96e7-5de12ef1db82/scratchpad'
COMFY_IN='/home/xsyprime/AI/ComfyUI/input'; COMFY_OUT='/home/xsyprime/AI/ComfyUI/output'

# ---- geometry ----
HUB=(497.0,481.0); GEAR=(550.0,760.0)          # dial_src 1024-space
F=0.50; ROT=math.degrees(math.atan2(GEAR[0]-HUB[0],GEAR[1]-HUB[1]))
TOURB=(240,368); TR_DISC=60; TR_WELL=64        # face px
TB_C=(700,705); TB_R=140                        # photo tourbillon centre/radius in donor
GEAR_L=(138,288); GL_R=50                       # baked gear axles measured on finished bg
GEAR_R=(330,209); GR_R=48
BEZ_IN=195; BEZ_OUT=227; CASE_OUT=240
DATEW=(322,310)
RESV_C=315.0; RESV_SPAN=45.0; RESV_R=176

RG_DK=(96,52,36); RG=(198,122,86); RG_MID=(224,156,116); RG_HI=(247,196,156); RG_SPEC=(255,240,224)
ST_DK=(52,54,60); ST=(148,152,162); ST_HI=(214,218,228); ST_SPEC=(248,250,255)
RUBY=(196,24,72); RUBY_HI=(255,120,168); CREAM=(238,224,198)

def _lerp(a,b,t): t=max(0.0,min(1.0,t)); return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def _oct_pts(r,ss=1):
    return [(240*ss+r*ss*math.sin(math.radians(22.5+45*k)),240*ss-r*ss*math.cos(math.radians(22.5+45*k))) for k in range(8)]
def _brush(size,color_a=18,seed=7):
    rnd=random.Random(seed); t=Image.new('RGBA',(size,size),(0,0,0,0)); d=ImageDraw.Draw(t)
    for _ in range(size*3):
        p=rnd.randint(0,size-1); a=rnd.randint(4,color_a); L=rnd.randint(size//4,size)
        o=rnd.randint(0,size-L); c=(255,255,255,a) if rnd.random()<0.5 else (0,0,0,a)
        d.line([(p,o),(p,o+L)],fill=c,width=1)
    return t
def _screw(r=16,ss=4,ang=25):
    R=r*ss; im=Image.new('RGBA',(2*R,2*R),(0,0,0,0)); d=ImageDraw.Draw(im); c=R
    d.ellipse([0,0,2*R-1,2*R-1],fill=(30,22,18,255))
    d.ellipse([int(R*0.10)]*2+[int(R*1.90)]*2,fill=ST_DK+(255,))
    for rr in range(int(R*0.82),0,-1):
        t=rr/(R*0.82); base=_lerp(ST_SPEC,ST,0.25+0.75*t)
        d.ellipse([c-rr,c-rr*0.98-R*0.04,c+rr,c+rr*0.98-R*0.04],fill=base+(255,))
    hexp=[(c+R*0.52*math.sin(math.radians(ang+60*k)),c-R*0.52*math.cos(math.radians(ang+60*k))) for k in range(6)]
    d.polygon(hexp,fill=(40,34,30,255))
    hexp2=[(c+R*0.44*math.sin(math.radians(ang+60*k)),c-R*0.44*math.cos(math.radians(ang+60*k))) for k in range(6)]
    d.polygon(hexp2,fill=(74,70,68,255))
    d.ellipse([c-R*0.62,c-R*0.72,c+R*0.1,c-R*0.18],fill=(255,255,255,80))
    return im.resize((2*r,2*r),Image.LANCZOS)

# ------------------------------------------------------------------ ComfyUI img2img
def _comfy_img2img(in_path,prefix,pos,neg,denoise,steps=30,cfg=5.5,seed=99101):
    fn=os.path.basename(in_path); shutil.copy(in_path,f'{COMFY_IN}/{fn}')
    before=set(os.listdir(COMFY_OUT))
    wf={
     "1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"}},
     "2":{"class_type":"LoadImage","inputs":{"image":fn}},
     "3":{"class_type":"VAEEncode","inputs":{"pixels":["2",0],"vae":["1",2]}},
     "4":{"class_type":"CLIPTextEncode","inputs":{"text":pos,"clip":["1",1]}},
     "5":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["1",1]}},
     "6":{"class_type":"KSampler","inputs":{"seed":seed,"steps":steps,"cfg":cfg,"sampler_name":"dpmpp_2m","scheduler":"karras",
          "denoise":denoise,"model":["1",0],"positive":["4",0],"negative":["5",0],"latent_image":["3",0]}},
     "7":{"class_type":"VAEDecode","inputs":{"samples":["6",0],"vae":["1",2]}},
     "8":{"class_type":"SaveImage","inputs":{"filename_prefix":prefix,"images":["7",0]}}}
    req=urllib.request.Request("http://127.0.0.1:8188/prompt",
        data=json.dumps({"prompt":wf}).encode(),headers={"Content-Type":"application/json"})
    json.load(urllib.request.urlopen(req))
    for _ in range(240):
        time.sleep(2)
        new=[f for f in os.listdir(COMFY_OUT) if f.startswith(prefix) and f not in before]
        if new: time.sleep(1); return f'{COMFY_OUT}/{sorted(new)[-1]}'
    raise RuntimeError('comfy timeout for '+prefix)
NEG_COMMON=("text, letters, numbers, watermark, logo, blurry, painting, drawing, illustration, "
            "cartoon, flat colors, low quality, deformed, oversaturated")

# ------------------------------------------------------------------ bg (960 native)
def gen_bg():
    """Compose the full face at native 960 (art + well + date + bezel) -> tools/bg960_pre.png"""
    ss=2; SS=S*ss
    src=Image.open(SRC).convert('RGB')
    src=src.rotate(ROT,center=HUB,resample=Image.BICUBIC,fillcolor=(10,8,7))
    W=S/F; x0=HUB[0]-W/2; y0=HUB[1]-W/2
    d=src.crop((int(x0),int(y0),int(x0+W),int(y0+W))).resize((SS,SS),Image.LANCZOS)
    d=ImageEnhance.Contrast(d).enhance(1.05); d=ImageEnhance.Color(d).enhance(1.06)
    d=d.convert('RGBA')
    fade=Image.new('L',(SS,SS),255); fd=ImageDraw.Draw(fade)
    for rr in range(240,188,-1):
        a=255 if rr<=190 else max(0,int(255*(1-(rr-190)/22.0)))
        fd.ellipse([(240-rr)*ss,(240-rr)*ss,(240+rr)*ss,(240+rr)*ss],fill=a)
    d=Image.composite(d,Image.new('RGBA',(SS,SS),(16,14,15,255)),fade)
    dd=ImageDraw.Draw(d)
    # tourbillon well (photo disc + rim cover most of it; keep a dark recess)
    tx,ty=TOURB[0]*ss,TOURB[1]*ss
    for rr in range(TR_WELL*ss,0,-1):
        t=rr/(TR_WELL*ss); col=_lerp((30,22,18),(66,52,42),t)
        dd.ellipse([tx-rr,ty-rr,tx+rr,ty+rr],fill=col+(255,))
    # date window
    wx,wy=DATEW[0]*ss,DATEW[1]*ss; w2,h2=23*ss,15*ss
    dd.rounded_rectangle([wx-w2-3*ss,wy-h2-3*ss,wx+w2+3*ss,wy+h2+3*ss],radius=6*ss,fill=RG_DK+(255,))
    dd.rounded_rectangle([wx-w2-2*ss,wy-h2-2*ss,wx+w2+2*ss,wy+h2+2*ss],radius=5*ss,outline=RG_HI+(255,),width=2*ss)
    dd.rounded_rectangle([wx-w2,wy-h2,wx+w2,wy+h2],radius=4*ss,fill=(14,11,9,255))
    # bezel + case (drawn; img2img gives it photographic finish)
    B=Image.new('RGBA',(SS,SS),(0,0,0,0)); bd=ImageDraw.Draw(B)
    for rr in range(CASE_OUT*ss,(BEZ_IN-2)*ss,-1):
        t=(rr/ss-BEZ_IN)/(CASE_OUT-BEZ_IN)
        bd.ellipse([240*ss-rr,240*ss-rr,240*ss+rr,240*ss+rr],outline=_lerp((22,20,22),(52,50,54),0.5+0.5*math.sin(t*math.pi))+(255,),width=3)
    corners=_oct_pts(BEZ_OUT,ss); LIGHT=math.radians(-45)
    for k in range(8):
        p1=corners[k]; p2=corners[(k+1)%8]
        na=math.radians(45+45*k); lum=0.90+0.20*max(0.0,math.cos(na-LIGHT))
        base=tuple(min(255,int(c*lum)) for c in RG)
        seg=[p1,p2]
        aa1=math.degrees(math.atan2(p2[0]-240*ss,-(p2[1]-240*ss))); aa0=math.degrees(math.atan2(p1[0]-240*ss,-(p1[1]-240*ss)))
        if aa1<aa0: aa1+=360
        for q in range(13):
            a=math.radians(aa1+(aa0-aa1)*q/12)
            seg.append((240*ss+BEZ_IN*ss*math.sin(a),240*ss-BEZ_IN*ss*math.cos(a)))
        bd.polygon(seg,fill=base+(255,))
    mask=Image.new('L',(SS,SS),0); md=ImageDraw.Draw(mask)
    md.polygon(_oct_pts(BEZ_OUT,ss),fill=255); md.ellipse([(240-BEZ_IN)*ss]*2+[(240+BEZ_IN)*ss]*2,fill=0)
    br=_brush(SS,16,seed=11)
    B.paste(Image.composite(br,Image.new('RGBA',(SS,SS),(0,0,0,0)),mask),(0,0),Image.composite(br,Image.new('RGBA',(SS,SS),(0,0,0,0)),mask))
    for k in range(8):
        p1=corners[k]; p2=corners[(k+1)%8]; na=math.radians(45+45*k)
        lit=max(0.0,math.cos(na-LIGHT)); col=_lerp(RG_DK,RG_SPEC,0.15+0.85*lit)
        bd.line([p1,p2],fill=col+(255,),width=2*ss)
    for q in range(720):
        a=math.radians(q/2); lit=max(0.0,math.cos(a-math.radians(315)))
        col=_lerp(RG_MID,RG_SPEC,0.25+0.75*lit**1.5)
        for rr in (BEZ_IN,BEZ_IN+2,BEZ_IN+4):
            x=240*ss+rr*ss*math.sin(a); y=240*ss-rr*ss*math.cos(a)
            bd.ellipse([x-ss,y-ss,x+ss,y+ss],fill=col+(255,))
    sc=_screw(15)
    for k in range(8):
        a=math.radians(22.5+45*k); r=(BEZ_IN+BEZ_OUT)/2+1
        x=240+r*math.sin(a); y=240-r*math.cos(a)
        scr=sc.rotate(random.Random(k).randint(0,359))
        px=Image.new('RGBA',(SS,SS),(0,0,0,0))
        px.paste(scr.resize((30*ss,30*ss),Image.LANCZOS),(int(x*ss-15*ss),int(y*ss-15*ss)))
        B.alpha_composite(px)
    d.alpha_composite(B)
    d.convert('RGB').save(f'{ROOT}/tools/bg960_pre.png'); print('bg960_pre composed (960 native)')

def photify_bg():
    pos=("macro product photograph of a luxury skeleton watch, brushed 18k rose gold octagonal bezel with "
         "polished hexagonal steel screws, polished beveled chamfer edges, rose gold skeletonized movement, "
         "visible gears and ruby jewels, dark recessed tourbillon aperture, studio product lighting, "
         "crisp reflections, metal grain, extremely detailed, photorealistic, sharp focus, 8k")
    out=_comfy_img2img(f'{ROOT}/tools/bg960_pre.png','aur_bgref',pos,NEG_COMMON,denoise=0.38,steps=34,seed=424241)
    shutil.copy(out,f'{ROOT}/tools/bg960_post.png'); print('photified ->',out)

def finalize_bg():
    """bg960_post -> stamp text/ticks that must stay crisp -> bg.png/bg_aod.png/sheen.png"""
    d=Image.open(f'{ROOT}/tools/bg960_post.png').convert('RGBA'); ss=2; SS=S*ss
    bd=ImageDraw.Draw(d)
    # power-reserve arc + ticks
    a0=RESV_C-RESV_SPAN/2; a1=RESV_C+RESV_SPAN/2
    bd.arc([(240-RESV_R)*ss,(240-RESV_R)*ss,(240+RESV_R)*ss,(240+RESV_R)*ss],a0-90,a1-90,fill=RG_HI+(255,),width=2*ss)
    for i in range(5):
        a=math.radians(a0+RESV_SPAN*i/4); r1,r2=RESV_R-1,RESV_R-(8 if i%2==0 else 5)
        bd.line([((240+r1*math.sin(a))*ss,(240-r1*math.cos(a))*ss),((240+r2*math.sin(a))*ss,(240-r2*math.cos(a))*ss)],fill=RG_HI+(255,),width=2*ss)
    # engraved brand
    f=ImageFont.truetype(MARC,15*ss); txt='A U R E L I U S'
    bb=bd.textbbox((0,0),txt,font=f); tx0=240*ss-(bb[2]-bb[0])/2; ty0=(240-BEZ_OUT+9)*ss
    bd.text((tx0+ss,ty0+ss),txt,font=f,fill=(255,236,214,140)); bd.text((tx0,ty0),txt,font=f,fill=(84,44,30,255))
    f2=ImageFont.truetype(MARC,10*ss); txt2='G E N È V E'; bb2=bd.textbbox((0,0),txt2,font=f2)
    bd.text((240*ss-(bb2[2]-bb2[0])/2+ss,(240+BEZ_OUT-22)*ss+ss),txt2,font=f2,fill=(255,236,214,120))
    bd.text((240*ss-(bb2[2]-bb2[0])/2,(240+BEZ_OUT-22)*ss),txt2,font=f2,fill=(84,44,30,255))
    # re-black the date window interior (img2img may have textured it)
    wx,wy=DATEW[0]*ss,DATEW[1]*ss; w2,h2=23*ss,15*ss
    bd.rounded_rectangle([wx-w2,wy-h2,wx+w2,wy+h2],radius=4*ss,fill=(14,11,9,255))
    dsm=d.resize((S,S),Image.LANCZOS)
    vig=Image.new('L',(S,S),0); vd=ImageDraw.Draw(vig)
    for rr in range(BEZ_IN,0,-1):
        vd.ellipse([240-rr,240-rr,240+rr,240+rr],fill=int(60*(rr/BEZ_IN)**3))
    dsm=Image.composite(Image.new('RGBA',(S,S),(8,5,4,255)),dsm,vig.filter(ImageFilter.GaussianBlur(4)))
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([0,0,S,S],fill=255)
    dsm.putalpha(m); dsm.save(f'{NODPI}/bg.png')
    a=ImageEnhance.Brightness(dsm.convert('RGB')).enhance(0.30); a=ImageEnhance.Color(a).enhance(0.55)
    a=a.convert('RGBA'); a.putalpha(m); a.save(f'{NODPI}/bg_aod.png')
    sh=Image.new('RGBA',(S,S),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    for i in range(-S,2*S):
        t=abs((i-160)/210.0)
        if t<1: sd.line([(i,0),(i-220,S)],fill=(255,250,240,int(40*(1-t)**2)),width=1)
    shm=Image.new('L',(S,S),0); smd=ImageDraw.Draw(shm)
    for rr in range(BEZ_IN,0,-1):
        smd.ellipse([240-rr,240-rr,240+rr,240+rr],fill=255 if rr<BEZ_IN-14 else int(255*(BEZ_IN-rr)/14))
    sh.putalpha(ImageChops.multiply(sh.split()[3],shm)); sh.save(f'{NODPI}/sheen.png')
    print('bg.png / bg_aod.png / sheen.png finalized')

# ------------------------------------------------------------------ photo-disc assets
def _feather_disc(im,cx,cy,r,feather=5):
    disc=im.crop((int(cx-r),int(cy-r),int(cx+r),int(cy+r))).convert('RGBA')
    m=Image.new('L',(2*r,2*r),0); md=ImageDraw.Draw(m)
    md.ellipse([0,0,2*r,2*r],fill=255)
    for i in range(feather):
        md.ellipse([i,i,2*r-i,2*r-i],outline=int(255*(i+1)/feather),width=2)
    disc.putalpha(m); return disc

def gen_assets():
    bg=Image.open(f'{NODPI}/bg.png').convert('RGB')
    # rotating photo gears cut straight from the finished bg (seamless at angle 0)
    _feather_disc(bg,*GEAR_L,GL_R,5).save(f'{NODPI}/gear_l.png')
    _feather_disc(bg,*GEAR_R,GR_R,5).save(f'{NODPI}/gear_r.png')
    # photo tourbillon disc from donor render
    don=Image.open(TOURB_SRC).convert('RGB')
    disc=_feather_disc(don,*TB_C,TB_R,10).resize((2*TR_DISC,2*TR_DISC),Image.LANCZOS)
    disc=ImageEnhance.Color(disc).enhance(1.04)
    disc.save(f'{NODPI}/tourb_disc.png')
    # static rim ring above the disc: polished RG ring + 60-tick seconds track, hole in middle
    ss=4; RO=(TR_DISC+10)*ss; rim=Image.new('RGBA',(2*RO,2*RO),(0,0,0,0)); rd=ImageDraw.Draw(rim); c=RO
    hole=(TR_DISC-6)*ss
    for w_,col in ((int(9*ss),RG_DK),(int(6*ss),RG),(int(3*ss),RG_MID)):
        rd.ellipse([c-(hole+8*ss),c-(hole+8*ss),c+(hole+8*ss),c+(hole+8*ss)],outline=col+(255,),width=w_)
    rd.arc([c-(hole+8*ss),c-(hole+8*ss),c+(hole+8*ss),c+(hole+8*ss)],170,330,fill=RG_HI+(255,),width=int(2.4*ss))
    for k in range(60):
        a=math.radians(k*6); big=(k%15==0)
        r1=hole+13*ss; r2=hole+(4 if big else 8)*ss
        col=RG_SPEC if big else RG_HI
        rd.line([(c+r1*math.sin(a),c-r1*math.cos(a)),(c+r2*math.sin(a),c-r2*math.cos(a))],fill=col+(240,),width=(2 if big else 1)*ss)
    # inner shadow lip over the disc edge
    for i in range(4*ss):
        rd.ellipse([c-hole-i,c-hole-i,c+hole+i,c+hole+i],outline=(0,0,0,int(90*(1-i/(4*ss)))),width=2)
    rim=rim.resize((2*(TR_DISC+10),2*(TR_DISC+10)),Image.LANCZOS)
    rim.save(f'{NODPI}/tourb_rim.png')
    # power-reserve needle
    n=Image.new('RGBA',(S*2,S*2),(0,0,0,0)); nd=ImageDraw.Draw(n)
    tipy=(240-RESV_R)*2
    nd.polygon([(480,tipy),(480-7,tipy+26),(480+7,tipy+26)],fill=RG_DK+(255,))
    nd.polygon([(480,tipy+3),(480-4,tipy+23),(480+4,tipy+23)],fill=RG_HI+(255,))
    n=n.resize((S,S),Image.LANCZOS); n.save(f'{NODPI}/resv_needle.png')
    # centre hub
    ss=6; R=13*ss; h=Image.new('RGBA',(2*R,2*R),(0,0,0,0)); hd=ImageDraw.Draw(h); c=R
    for rr in range(R,0,-1):
        t=rr/R; hd.ellipse([c-rr,c-rr,c+rr,c+rr],fill=_lerp(RG_HI,RG_DK,t**1.3)+(255,))
    hd.ellipse([c-R*0.52,c-R*0.52,c+R*0.52,c+R*0.52],fill=RUBY+(255,))
    hd.ellipse([c-R*0.34,c-R*0.40,c+R*0.02,c-R*0.04],fill=RUBY_HI+(235,))
    hd.arc([c-R*0.94,c-R*0.94,c+R*0.94,c+R*0.94],200,340,fill=RG_SPEC+(220,),width=max(2,int(R*0.07)))
    h=h.resize((26,26),Image.LANCZOS); h.save(f'{NODPI}/hub.png')
    print('assets: photo gear_l gear_r tourb_disc + tourb_rim resv_needle hub')

# ------------------------------------------------------------------ hands (drawn -> photified -> re-cut)
def _hand_shape(length,wbase,wtip,ss=2):
    C=240*ss; im=Image.new('RGBA',(S*ss,S*ss),(0,0,0,0)); d=ImageDraw.Draw(im)
    L=length*ss; wb=wbase*ss; wt=wtip*ss; tail=26*ss
    def outline(dx,dy):
        return [(C-wb+dx,C+tail+dy),(C-wb+dx,C-L*0.62+dy),(C-wt+dx,C-L+dy),
                (C+wt+dx,C-L+dy),(C+wb+dx,C-L*0.62+dy),(C+wb+dx,C+tail+dy)]
    d.polygon(outline(0,0),fill=RG_DK+(255,))
    left=[(C+0,C+tail),(C+0,C-L)]+[(C-wt+2,C-L+2),(C-wb+2,C-L*0.62),(C-wb+2,C+tail)]
    right=[(C+0,C+tail),(C+0,C-L)]+[(C+wt-2,C-L+2),(C+wb-2,C-L*0.62),(C+wb-2,C+tail)]
    d.polygon([left[1],left[2],left[3],left[4],left[0]],fill=RG_MID+(255,))
    d.polygon([right[1],right[2],right[3],right[4],right[0]],fill=_lerp(RG,RG_DK,0.25)+(255,))
    sl_w=max(3*ss,int(wb*0.42))
    slot=[(C-sl_w,C-L*0.56),(C-sl_w*0.5,C-L*0.86),(C+sl_w*0.5,C-L*0.86),(C+sl_w,C-L*0.56),(C+sl_w,C-8*ss),(C-sl_w,C-8*ss)]
    d.polygon(slot,fill=(0,0,0,0)); d.polygon(slot,outline=RG_DK+(255,),width=2*ss)
    d.polygon([(C-wt*0.55,C-L+4*ss),(C+wt*0.55,C-L+4*ss),(C+wb*0.42,C-L*0.90),(C-wb*0.42,C-L*0.90)],fill=CREAM+(255,))
    d.line([(C-wb+2,C+tail-2*ss),(C-wb+2,C-L*0.62),(C-wt+2,C-L+2*ss)],fill=RG_SPEC+(230,),width=2*ss)
    return im
def gen_hands():
    """photify both hands on one 1024 sheet, then re-cut with original alpha"""
    hour=_hand_shape(122,11,7); minute=_hand_shape(178,9,5)
    sheet=Image.new('RGB',(1024,1024),(24,18,15))
    nz=Image.new('RGBA',(1024,1024),(0,0,0,0)); rnd=random.Random(5); nd=ImageDraw.Draw(nz)
    for _ in range(4000):
        x=rnd.randint(0,1023); y=rnd.randint(0,1023)
        nd.point((x,y),fill=(rnd.randint(20,60),)*3+(60,))
    sheet.paste(nz,(0,0),nz)
    # place hand crops (the interesting 300x560 region around each hand, scaled 1.6x)
    hc=hour.crop((240*2-80,240*2-320,240*2+80,240*2+80))    # 160x400
    mc=minute.crop((240*2-70,240*2-420,240*2+70,240*2+80))  # 140x500
    hc2=hc.resize((int(hc.width*1.8),int(hc.height*1.8)),Image.LANCZOS)
    mc2=mc.resize((int(mc.width*1.8),int(mc.height*1.8)),Image.LANCZOS)
    sheet.paste(hc2,(150,140),hc2); sheet.paste(mc2,(600,60),mc2)
    sheet.save(f'{ROOT}/tools/hands_pre.png')
    pos=("macro product photograph of two polished 18k rose gold skeleton watch hands on dark velvet, "
         "beveled polished edges, faceted metal surfaces catching studio light, cream luminous tips, "
         "openworked slots, extreme detail, photorealistic, sharp focus")
    out=_comfy_img2img(f'{ROOT}/tools/hands_pre.png','aur_hands',pos,NEG_COMMON,denoise=0.45,steps=32,seed=77007)
    ph=Image.open(out).convert('RGB'); ph.save(f'{ROOT}/tools/hands_post.png')
    # re-cut: paste photified pixels back into full-canvas sprites through original alpha
    for name,orig,crop_box,paste_xy,sc in (
        ('hour_hand',hour,(240*2-80,240*2-320,240*2+80,240*2+80),(150,140),1.8),
        ('min_hand',minute,(240*2-70,240*2-420,240*2+70,240*2+80),(600,60),1.8)):
        cb=orig.crop(crop_box); w,h=cb.size
        reg=ph.crop((paste_xy[0],paste_xy[1],paste_xy[0]+int(w*sc),paste_xy[1]+int(h*sc))).resize((w,h),Image.LANCZOS)
        alpha=cb.split()[3].point(lambda v:255 if v>140 else 0).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
        spr=Image.new('RGBA',orig.size,(0,0,0,0))
        reg_rgba=reg.convert('RGBA'); reg_rgba.putalpha(alpha)
        spr.paste(reg_rgba,crop_box[:2])
        # soft drop shadow
        shl=Image.new('RGBA',orig.size,(0,0,0,0))
        sh_a=Image.new('L',orig.size,0); sh_a.paste(alpha,(crop_box[0]+5,crop_box[1]+6))
        shl.putalpha(sh_a.point(lambda v:int(v*0.45))); shl=shl.filter(ImageFilter.GaussianBlur(3))
        outp=Image.new('RGBA',orig.size,(0,0,0,0)); outp.alpha_composite(shl); outp.alpha_composite(spr)
        outp.resize((S,S),Image.LANCZOS).save(f'{NODPI}/{name}.png')
    print('hands photified + re-cut')

# ------------------------------------------------------------------ glyphs
CHARS={**{str(n):str(n) for n in range(10)},'%':'pct',':':'colon',' ':'space',
       **{ch:ch.lower() for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
def gen_glyphs():
    ch_h=30; f=ImageFont.truetype(MARC,ch_h); H=ch_h+8; meta={}
    for ch,rn in CHARS.items():
        if ch==' ':
            im=Image.new('RGBA',(12,H),(0,0,0,0)); meta[ch]=(f'g_{rn}',12,H); im.save(f'{NODPI}/g_{rn}.png'); continue
        bb=f.getbbox(ch); w=bb[2]-bb[0]+10
        im=Image.new('RGBA',(w,H),(0,0,0,0)); d=ImageDraw.Draw(im); ox,oy=5-bb[0],3
        d.text((ox+1,oy+1),ch,font=f,fill=(30,16,10,255))
        gm=Image.new('L',(w,H),0); ImageDraw.Draw(gm).text((ox,oy),ch,font=f,fill=255)
        grad=Image.new('RGBA',(w,H),(0,0,0,0)); gd2=ImageDraw.Draw(grad)
        for y in range(H):
            gd2.line([(0,y),(w,y)],fill=_lerp(RG_SPEC,RG_MID,y/H)+(255,))
        gold=Image.new('RGBA',(w,H),(0,0,0,0)); gold.paste(grad,(0,0),gm); im.alpha_composite(gold)
        d.text((ox,oy-1),ch,font=f,fill=(255,246,232,60))
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
    _p(b,'tourb_disc',*TOURB,255,(t%60)*6)
    _p(b,'tourb_rim',*TOURB)
    _str(b,'%d'%(24),*DATEW,24)
    _p(b,'resv_needle',240,240,255,(RESV_C-RESV_SPAN/2+RESV_SPAN*0.88)%360)
    sh=Image.open(f'{NODPI}/sheen.png').convert('RGBA'); off=int(30*math.sin(t*0.5))
    shc=Image.new('RGBA',(S,S),(0,0,0,0)); shc.alpha_composite(sh,(off,0)); shc.putalpha(shc.split()[3].point(lambda v:int(v*0.8)))
    b.alpha_composite(shc)
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
    o=['<?xml version="1.0" encoding="utf-8"?>\n<WatchFace width="480" height="480">\n'
       '  <Metadata key="CLOCK_TYPE" value="ANALOG" />\n  <Metadata key="PREVIEW_TIME" value="10:09:35" />\n']
    o.append(bffonts()); o.append('  <Scene backgroundColor="#FF060403">\n')
    o.append(img('z00_bg','bg',240,240,480,480,255,kids=Vr('alpha','0',0.6,0,'EASE_OUT')+XF('x',f'0 + 3 * {PX}')+XF('y',f'0 + 3 * {PY}')))
    o.append(img('z00_aod','bg_aod',240,240,480,480,0,kids=Vr('alpha','255',0.6,0,'EASE_IN')))
    o.append(img('z10_gl','gear_l',*GEAR_L,2*GL_R,2*GL_R,255,pivot=('0.5','0.5'),kids=Vr('alpha','90',0.4,0.1)+XF('angle',f'({T} * 40) % 360')))
    o.append(img('z11_gr','gear_r',*GEAR_R,2*GR_R,2*GR_R,255,pivot=('0.5','0.5'),kids=Vr('alpha','90',0.4,0.12)+XF('angle',f'360 - (({T} * 24) % 360)')))
    o.append(img('z20_td','tourb_disc',*TOURB,2*TR_DISC,2*TR_DISC,255,pivot=('0.5','0.5'),kids=Vr('alpha','130',0.4,0.16)
              +XF('angle','([SECOND] + [MILLISECOND] / 1000) * 6')))
    o.append(img('z21_tr','tourb_rim',*TOURB,2*(TR_DISC+10),2*(TR_DISC+10),255,kids=Vr('alpha','140',0.4,0.16)))
    o.append(f'    <PartText name="z30_date" x="{DATEW[0]-30}" y="{DATEW[1]-14}" width="60" height="28">\n'
             +Vr('alpha','140',0.4,0.2)
             +'      <Text align="CENTER"><BitmapFont family="aur" size="24" color="#FFFFFF"><Template>%d<Parameter expression="[DAY]" /></Template></BitmapFont></Text>\n    </PartText>\n')
    o.append(img('z31_resv','resv_needle',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','120',0.4,0.2)
              +XF('angle',f'{RESV_C-RESV_SPAN/2} + {RESV_SPAN} * clamp([BATTERY_PERCENT], 0, 100) / 100')))
    o.append(img('z40_sheen','sheen',240,240,480,480,0,kids=Vr('alpha','0',0.5,0.1,'EASE_OUT')
              +XF('alpha',f'110 + 60*sin({T}*0.45)')+XF('x',f'0 + 48 * {PX}')+XF('y',f'0 + 18 * {PY}')))
    o.append(img('z50_hour','hour_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','190',0.5,0.0,'EASE_OUT')+XF('angle','([HOUR_0_11] + [MINUTE] / 60) * 30')))
    o.append(img('z51_min','min_hand',240,240,480,480,255,pivot=('0.5','0.5'),kids=Vr('alpha','190',0.5,0.0,'EASE_OUT')+XF('angle','([MINUTE] + [SECOND] / 60) * 6')))
    o.append(img('z52_hub','hub',240,240,26,26,255,kids=Vr('alpha','200',0.4,0.0)))
    o.append('  </Scene>\n</WatchFace>\n')
    open(f'{RES}/raw/watchface.xml','w').write(''.join(o)); print('watchface.xml',len(''.join(o)),'bytes')

if __name__=='__main__':
    st=sys.argv[1] if len(sys.argv)>1 else 'all'
    if st in ('bg','all'): gen_bg()
    if st in ('photify','all'): photify_bg()
    if st in ('finalize','all'): finalize_bg()
    if st in ('assets','all'): gen_assets()
    if st in ('hands','all'): gen_hands()
    if st in ('glyphs','all'): gen_glyphs()
    if st in ('xml','all'): gen_xml()
    if st in ('preview','all'): compose_preview()
    if st in ('anim','all'): animate()
    if st=='debug': debug()
