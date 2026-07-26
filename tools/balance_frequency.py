#!/usr/bin/env python3
"""Measure the heart rate the Aurelius face is actually USING.

The balance wheel is driven by

    180 + 35 * sin(t * clamp(HEART_RATE<30 ? 70 : HEART_RATE, 40, 200) * 0.10472)

so it oscillates at HR/60 Hz — one oscillation per heartbeat. Measuring
that frequency from a screen recording therefore reads back the heart
rate the runtime handed the face, without needing to interpret pixels
as a number.

This is what settles the API-36 permission question empirically: the
documented fallback is exactly 70 bpm = 1.1667 Hz, so a face running on
the fallback is distinguishable from one receiving live heart rate.

    adb shell screenrecord --time-limit 14 --size 480x480 /sdcard/r.mp4
    ffmpeg -i r.mp4 -vf fps=30 frames/f%04d.png
    python3 tools/balance_frequency.py frames/

Pure stdlib + Pillow: a Goertzel-style DFT sweep over the 150
highest-variance pixels of the z21_bal layer box.
"""

import math, sys
from PIL import Image
from pathlib import Path
FPS = 30.0
BOX = (194, 316, 194+92, 316+92)
def load(d):
    out=[]
    for p in sorted(Path(d).glob('*.png')):
        im = Image.open(p).convert('L').crop(BOX).resize((46,46), Image.BILINEAR)
        out.append(list(im.tobytes()))
    return out
def peak(frames, lo=0.4, hi=4.0, step=0.005):
    T=len(frames); N=len(frames[0])
    mean=[sum(f[i] for f in frames)/T for i in range(N)]
    var=[sum((f[i]-mean[i])**2 for f in frames) for i in range(N)]
    top=sorted(range(N), key=lambda i:-var[i])[:150]
    sig=[[frames[t][i]-mean[i] for t in range(T)] for i in top]
    win=[0.5-0.5*math.cos(2*math.pi*t/(T-1)) for t in range(T)]
    best=(0,-1); f=lo
    while f<=hi:
        w=2*math.pi*f/FPS; tot=0.0
        for s in sig:
            re=im_=0.0
            for t in range(T):
                v=s[t]*win[t]; re+=v*math.cos(w*t); im_+=v*math.sin(w*t)
            tot+=re*re+im_*im_
        if tot>best[1]: best=(f,tot)
        f+=step
    return best[0]
d=sys.argv[1]
fr=load(d)
f=peak(fr)
print(f"{d}: frames={len(fr)}  peak={f:.4f} Hz  implied HR={f*60:.1f} bpm")
