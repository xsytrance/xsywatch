#!/usr/bin/env python3
"""Native 960px preview of the AURELIUS Warbird v4 face (bg_hd master + pre-downscale sprites)."""
import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
import build
from PIL import Image, ImageDraw, ImageFont, ImageChops

OUT_PATH=f'{build.SCRATCH}/aur_preview_hd.png'
X=2; SB=480*X

build.gen_bg()
bg=Image.open(f'{build.ROOT}/tools/bg_hd.png').convert('RGBA')

caps={}
_orig=Image.Image.resize
def cap_named(names):
    idx={'n':0}
    def f(self,size,*a,**k):
        if self.mode=='RGBA' and self.width>size[0] and idx['n']<len(names):
            caps[names[idx['n']]]=self.copy(); idx['n']+=1
        return _orig(self,size,*a,**k)
    return f
Image.Image.resize=cap_named(['prop','needle','hub']); build.gen_assets()
Image.Image.resize=cap_named(['hour','minute']); build.gen_hands()
Image.Image.resize=_orig

t=35.0; hh,mm=10,9; batt=0.72; hr=88
def paste(b,im,cx,cy,rot=0.0,target=None):
    im=im.convert('RGBA')
    if target: im=im.resize((target,target),Image.LANCZOS)
    if rot: im=im.rotate(-rot,resample=Image.BICUBIC)
    b.paste(im,(int(cx*X-im.width/2),int(cy*X-im.height/2)),im)
pr_t=2*(build.PR_COWL-4)*X; ne_t=2*(build.GA_R+6)*X
paste(bg,caps['prop'],*build.PROP,(t%60)*6,target=pr_t)
paste(bg,caps['needle'],*build.GAUGE_L,-67.5+135*batt,target=ne_t)
paste(bg,caps['needle'],*build.GAUGE_R,-67.5+135*max(0,min(1,(hr-40)/140)),target=ne_t)
f=ImageFont.truetype(build.RAJD,25*X); d=ImageDraw.Draw(bg)
bb=d.textbbox((0,0),'24',font=f)
d.text((build.DATEW[0]*X-(bb[2]-bb[0])/2-bb[0],build.DATEW[1]*X-(bb[3]-bb[1])/2-bb[1]),'24',
       font=f,fill=build.KHAKI+(255,))
sh=Image.open(f'{build.NODPI}/sheen.png').convert('RGBA').resize((SB,SB),Image.LANCZOS)
bg.paste(sh,(0,0),sh)
for key,ang in (('hour',(hh+mm/60)*30),('minute',mm*6)):
    im2=caps[key].convert('RGBA').resize((SB,SB),Image.LANCZOS).rotate(-ang,center=(SB//2,SB//2),resample=Image.BICUBIC)
    bg.paste(im2,(0,0),im2)
paste(bg,caps['hub'],*build.HUBC,target=24*X)
m=Image.new('L',(SB,SB),0); ImageDraw.Draw(m).ellipse([0,0,SB,SB],fill=255)
out=Image.new('RGB',(SB,SB),(0,0,0)); out.paste(bg.convert('RGB'),(0,0),m)
out.save(OUT_PATH); print('HD ->',OUT_PATH)
