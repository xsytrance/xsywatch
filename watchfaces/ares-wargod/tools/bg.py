import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
"""ARES — background: full marble face (all numerals in frame), de-bake only live values."""
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import os, random
OUT=_ROOT + '/app/src/main/res/drawable-nodpi'
os.makedirs(OUT,exist_ok=True); S=480
src=Image.open(_ROOT + '/tools/ares_clean.png').convert('RGB')
# full disc so the whole numeral ring (r~560) fits inside the round screen
CX,CY,R=627,627,600
face=src.crop((CX-R,CY-R,CX+R,CY+R)).resize((S,S),Image.LANCZOS)

face=ImageEnhance.Color(face).enhance(1.05)
face=ImageEnhance.Contrast(face).enhance(1.04)
r,g,b=face.split()
r=r.point(lambda v:min(255,int(v*1.04+3))); b=b.point(lambda v:int(v*0.96))
face=Image.merge('RGB',(r,g,b))

def soften(box,blur=16,pad=22,feather=7):
    """Erase a baked live-value: heavy blur over a PADDED region so surrounding
    marble dilutes the carved strokes, then paste the box-sized centre back."""
    x0,y0,x1,y1=box
    patch=face.crop((x0-pad,y0-pad,x1+pad,y1+pad)).filter(ImageFilter.GaussianBlur(blur))
    inner=patch.crop((pad,pad,pad+(x1-x0),pad+(y1-y0)))
    m=Image.new('L',(x1-x0,y1-y0),0); ImageDraw.Draw(m).rounded_rectangle([0,0,x1-x0-1,y1-y0-1],radius=8,fill=255)
    m=m.filter(ImageFilter.GaussianBlur(feather)); face.paste(inner,(x0,y0),m)

# clean inpainted base — only the baked stat VALUES + battery % remain to erase
for y,xr in [(120,94),(168,98),(209,118),(245,102),(290,88),(335,118)]:
    soften((50,y-13,xr,y+8),blur=13,pad=18)
soften((284,344,360,384))                  # 86% (battery)

# very light rim vignette (keep numerals bright)
vig=Image.new('L',(S,S),0); vd=ImageDraw.Draw(vig)
for rr in range(S//2,0,-1):
    t=rr/(S/2); vd.ellipse([S/2-rr,S/2-rr,S/2+rr,S/2+rr],fill=int(255*(1-0.18*t**5)))
vig=vig.filter(ImageFilter.GaussianBlur(6))
face=Image.composite(face,Image.new('RGB',(S,S),(8,7,6)),vig)
face.save(f'{OUT}/bg.png')

aod=ImageEnhance.Brightness(face).enhance(0.30); aod=ImageEnhance.Color(aod).enhance(0.5)
aod.save(f'{OUT}/bg_aod.png')

# wrath-of-Ares glow: red aura that intensifies with heart rate (alpha driven in WFF)
wr=Image.new('RGBA',(S,S),(0,0,0,0)); wd=ImageDraw.Draw(wr)
for rr in range(210,0,-1):
    t=rr/210.0; a=int(150*(1-t)**2.0)
    wd.ellipse([220-rr,250-rr,220+rr,250+rr],fill=(200,40,30,a))
wr=wr.filter(ImageFilter.GaussianBlur(24)); wr.save(f'{OUT}/wrath.png')

# raking sheen (tilt highlight)
sheen=Image.new('RGBA',(S,S),(0,0,0,0)); ImageDraw.Draw(sheen).polygon([(-120,0),(60,0),(220,480),(40,480)],fill=(255,248,230,38))
sheen.filter(ImageFilter.GaussianBlur(48)).save(f'{OUT}/sheen.png')
# drifting haze
cloud=Image.new('RGBA',(560,240),(0,0,0,0)); cd=ImageDraw.Draw(cloud); rnd=random.Random(3)
for _ in range(40):
    x=rnd.uniform(0,560); y=rnd.uniform(40,200); rr=rnd.uniform(40,110)
    cd.ellipse([x-rr,y-rr*0.5,x+rr,y+rr*0.5],fill=(220,214,200,9))
cloud.filter(ImageFilter.GaussianBlur(28)).save(f'{OUT}/cloud.png')
print('bg written (R=600, full numeral ring)')
