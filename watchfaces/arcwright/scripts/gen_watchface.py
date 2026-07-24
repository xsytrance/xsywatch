#!/usr/bin/env python3
"""ARCWRIGHT scene generator — assembly mode.

The static machine is ONE integrated render (assembly/base.png, full GI) and
every moving part is an in-place sprite rendered inside that same scene, so
sprites carry true neighborhood lighting and land on their own pre-baked
contact shadows. Engraved bitmap-font clocks seat in the display wells.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_XML = os.path.join(ROOT, 'app/src/main/res/raw/watchface.xml')
OUT_MAP = os.path.join(ROOT, 'docs/ANIMATION_MAP.md')

T = '([SECOND] + [MILLISECOND] / 1000)'
TH = '([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'

XML = []
ANIM = []

PAR_Y = 'clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'
PAR_X = 'clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'


def img(res, cx, cy, w, h, name, alpha=255, angle=None, transforms=(),
        variants=('dim',), pivot=(0.5, 0.5), plane=0):
    x, y = int(cx - w / 2), int(cy - h / 2)
    transforms = list(transforms)
    if plane:
        transforms += [('x', f'{x} + {plane} * {PAR_Y}'),
                       ('y', f'{y} + {plane} * {PAR_X}')]
    a = f' angle="{angle}"' if angle is not None else ''
    p = (f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"'
         if pivot != (0.5, 0.5) or any(t == 'angle' for t, _ in transforms) else '')
    var = {'dim': '      <Variant mode="AMBIENT" target="alpha" value="45" />',
           'hide': '      <Variant mode="AMBIENT" target="alpha" value="0" />',
           None: ''}
    vlines = '\n'.join(var[v] for v in variants if v in var and var[v])
    tlines = '\n'.join(f'      <Transform target="{t}" value="{e}" />'
                       for t, e in transforms)
    body = '\n'.join(s for s in (vlines, tlines) if s)
    XML.append(f'''    <PartImage x="{x}" y="{y}" width="{w}" height="{h}" name="{name}" alpha="{alpha}"{a}{p}>
{body}
      <Image resource="{res}" />
    </PartImage>''')


def rot(res, cx, cy, size, name, rate_deg_s, base='T', ccw=False,
        variants=('dim',), pivot=(0.5, 0.5), reason='', cycle='', plane=0):
    t = T if base == 'T' else TH
    expr = f'{t} * {rate_deg_s}'
    if ccw:
        expr = f'360 - ({expr})'
    img(res, cx, cy, size, size, name,
        transforms=[('angle', expr)], variants=variants, pivot=pivot, plane=plane)
    ANIM.append((name, res, f'({cx},{cy})', 'CCW' if ccw else 'CW',
                 cycle or f'{360 / rate_deg_s:.0f}s/rot', reason))


# ================= SCENE =================

# the machine, two GI slabs: plate below, chassis-and-above on top.
# Under-chassis movers (rear gears, piston rods) sandwich between them.
img('base_lower', 240, 240, 480, 480, 'z00_base_lower', plane=4)

rot('gear_rear_l', 166, 306, 260, 'z02_rear_gear_l', 2.0, base='TH', plane=5,
    reason='primary rear drive', cycle='180s/rot')
rot('gear_rear_m', 330, 176, 150, 'z02_rear_gear_m', 3.0, base='TH', ccw=True,
    plane=5, reason='meshed 36T:24T with rear L', cycle='120s/rot')

# piston rods slide INSIDE their sleeves: rods here, sleeves in base_upper —
# only the crown pokes above the sleeve mouth, exactly like the real thing
for i, (px_, phase) in enumerate([(206, 0), (274, 3.1416)]):
    XML.append(f'''    <PartImage x="{px_ - 30}" y="300" width="60" height="60" name="z02_rod_{i}" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="45" />
      <Transform target="x" value="{px_ - 30} + 5 * {PAR_Y}" />
      <Transform target="y" value="300 - 9 * sin({T} * 3.1416 + {phase})" />
      <Image resource="rod_{i}" />
    </PartImage>''')
    ANIM.append((f'z02_rod_{i}', f'rod_{i}', f'({px_},330)', 'reciprocating',
                 '2s stroke', f'piston pair, {"left" if i == 0 else "right"} (antiphase)'))

img('base_upper', 240, 240, 480, 480, 'z04_base_upper', plane=6)

# indexing rings
img('ring_hour', 240, 240, 252, 252, 'z05_ring_hour',
    transforms=[('angle', '[HOUR_0_11] * 30')], variants=('dim',))
ANIM.append(('z05_ring_hour', 'ring_hour', '(240,240)', 'CW creeping',
             '30 deg per hour', 'hour indexing ring'))
img('ring_min', 240, 240, 286, 286, 'z05_ring_min',
    transforms=[('angle', '[MINUTE] * 6')], variants=('dim',))
ANIM.append(('z05_ring_min', 'ring_min', '(240,240)', 'CW stepping',
             '6 deg per minute', 'minute indexing ring'))

# quadrant gear clusters — instance-specific in-place sprites
rot('nw_gear_a', 138, 148, 110, 'z05_nw_gear_a', 15, plane=7,
    reason='NW cluster driver (22T)', cycle='24s/rot')
rot('nw_gear_c', 204, 196, 60, 'z05_nw_gear_c', 27.5, ccw=True, plane=7,
    reason='meshed with NW A (22T:12T)', cycle='13s/rot')
rot('ne_gear_a', 342, 148, 110, 'z05_ne_gear_a', 12, ccw=True, plane=7,
    reason='NE cluster driver', cycle='30s/rot')
rot('ne_gear_c', 276, 196, 60, 'z05_ne_gear_c', 22, plane=7,
    reason='meshed with NE A', cycle='16s/rot')
img('ratchet', 135, 332, 90, 90, 'z05_ratchet',
    transforms=[('angle', 'floor([SECOND]) * 18')], variants=('dim',))
ANIM.append(('z05_ratchet', 'ratchet', '(135,332)', 'CW stepped',
             '18 deg per second (20 teeth)', 'ratchet indexing the SEC train'))
rot('sw_gear_d', 192, 368, 44, 'z05_sw_gear_d', 30, ccw=True, plane=7,
    reason='SW escapement follower', cycle='12s/rot')
rot('se_gear_b', 342, 332, 84, 'z05_se_gear_b', 9, plane=7,
    reason='SE cluster driver', cycle='40s/rot')
img('cam', 286, 368, 72, 72, 'z05_se_cam',
    transforms=[('angle', f'{T} * 20')], variants=('dim',), pivot=(0.42, 0.5))
ANIM.append(('z05_se_cam', 'cam', '(286,368) pivot(0.42)', 'CW eccentric',
             '18s/rot', 'eccentric cam driven off SE B'))

# turbine + chamber rotors
rot('fan', 240, 88, 84, 'z10_fan', 72, plane=8,
    reason='intake turbine', cycle='5s/rot')
rot('ring_outer', 240, 240, 168, 'z11_ring_outer', 6, plane=8,
    reason='chamber containment ring', cycle='60s/rot')
rot('ring_inner', 240, 240, 132, 'z11_ring_inner', 9, ccw=True, plane=9,
    reason='gyro ring, counter-rotates', cycle='40s/rot')

# engraved bitmap clocks seated in the display wells
XML.append('''    <DigitalClock x="44" y="206" width="88" height="56">
      <TimeText format="hh" hourFormat="SYNC_TO_DEVICE" align="CENTER"
                x="0" y="0" width="88" height="56">
        <BitmapFont family="engraved_lg" size="56" color="#FFFFFF" />
      </TimeText>
    </DigitalClock>
    <DigitalClock x="348" y="206" width="88" height="56">
      <TimeText format="mm" align="CENTER" x="0" y="0" width="88" height="56">
        <BitmapFont family="engraved_lg" size="56" color="#FFFFFF" />
      </TimeText>
    </DigitalClock>
    <DigitalClock x="208" y="372" width="64" height="44">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <TimeText format="ss" align="CENTER" x="0" y="0" width="64" height="44">
        <BitmapFont family="engraved_sm" size="44" color="#FFFFFF" />
      </TimeText>
    </DigitalClock>''')

# ================= document =================

FONTS = '''  <BitmapFonts>
    <BitmapFont name="engraved_lg">
''' + '\n'.join(f'      <Character name="{c}" resource="glyph_lg_{c if c != ":" else "colon"}" width="52" height="68" />'
                for c in list('0123456789') + [':']) + '''
    </BitmapFont>
    <BitmapFont name="engraved_sm">
''' + '\n'.join(f'      <Character name="{c}" resource="glyph_sm_{c}" width="32" height="44" />'
                for c in '0123456789') + '''
    </BitmapFont>
  </BitmapFonts>'''

body = '\n\n'.join(XML)
xml = f'''<?xml version="1.0" encoding="utf-8"?>
<WatchFace width="480" height="480">
  <Metadata key="CLOCK_TYPE" value="DIGITAL" />
  <Metadata key="PREVIEW_TIME" value="10:08:32" />
{FONTS}
  <Scene backgroundColor="#FF000000">

{body}

  </Scene>
</WatchFace>
'''
with open(OUT_XML, 'w') as fh:
    fh.write(xml)

with open(OUT_MAP, 'w') as fh:
    fh.write('# ARCWRIGHT animation map (assembly mode)\n\n')
    fh.write('Generated by `scripts/gen_watchface.py` — single source of truth.\n\n')
    fh.write('| Group | Asset | Pivot | Motion | Cycle | Why |\n|---|---|---|---|---|---|\n')
    for name, res, piv, mot, cyc, why in ANIM:
        fh.write(f'| {name} | {res} | {piv} | {mot} | {cyc} | {why} |\n')
    fh.write(f'\nTotal independently animated groups: **{len(ANIM)}**\n')

print(f'watchface.xml written ({os.path.getsize(OUT_XML)} bytes); '
      f'{len(ANIM)} animated groups')
