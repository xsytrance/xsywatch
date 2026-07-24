#!/usr/bin/env python3
"""CHRONOVA scene generator — emits res/raw/watchface.xml + docs/ANIMATION_MAP.md.

Single source of truth: every animated group is declared once in GROUPS below,
with pivot, direction, speed and rationale, then rendered into both the XML
and the animation map. Design space is 480x480, center (240,240).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_XML = os.path.join(ROOT, 'app/src/main/res/raw/watchface.xml')
OUT_MAP = os.path.join(ROOT, 'docs/ANIMATION_MAP.md')

T = '([SECOND] + [MILLISECOND] / 1000)'   # smooth seconds within the minute
# continuous time in seconds across the hour (for slow cycles > 60s)
TH = '([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)'

BLUE, MAGENTA, VIOLET = '#4FC3FF', '#FF4FD8', '#B44FFF'

XML = []          # xml fragments in z-order
ANIM = []         # (group, asset, pivot, direction, cycle, reason)


PAR_Y = 'clamp([ACCELEROMETER_ANGLE_X], -45, 45) / 45'  # horizontal (roll)
PAR_X = 'clamp([ACCELEROMETER_ANGLE_Y], -45, 45) / 45'  # vertical (pitch)


def img(res, cx, cy, w, h, name, alpha=255, angle=None, transforms=(),
        variants=('dim',), pivot=(0.5, 0.5), plane=0):
    """PartImage centered at (cx,cy). transforms: list of (target, expr).
    plane>0 adds wrist-tilt parallax: rear planes small, foreground large."""
    x, y = int(cx - w / 2), int(cy - h / 2)
    transforms = list(transforms)
    if plane:
        transforms += [('x', f'{x} + {plane} * {PAR_Y}'),
                       ('y', f'{y} + {plane} * {PAR_X}')]
    a = f' angle="{angle}"' if angle is not None else ''
    p = (f' pivotX="{pivot[0]}" pivotY="{pivot[1]}"'
         if pivot != (0.5, 0.5) or any(t == 'angle' for t, _ in transforms) else '')
    lines = [f'    <PartImage x="{x}" y="{y}" width="{w}" height="{h}" '
             f'name="{name}" alpha="{alpha}"{a}{p}>']
    if 'hide' in variants:
        lines.append('      <Variant mode="AMBIENT" target="alpha" value="0" />')
    elif 'dim' in variants:
        lines.append('      <Variant mode="AMBIENT" target="alpha" value="45" />')
    for target, expr in transforms:
        lines.append(f'      <Transform target="{target}" value="{expr}" />')
    lines.append(f'      <Image resource="{res}" />')
    lines.append('    </PartImage>')
    XML.append('\n'.join(lines))


def rot(res, cx, cy, size, name, rate_deg_s, base='T', ccw=False, alpha=255,
        variants=('dim',), pivot=(0.5, 0.5), reason='', cycle='', plane=0):
    t = T if base == 'T' else TH
    expr = f'{t} * {rate_deg_s}'
    if ccw:
        expr = f'360 - ({expr})'
    img(res, cx, cy, size, size, name, alpha=alpha,
        transforms=[('angle', expr)], variants=variants, pivot=pivot, plane=plane)
    ANIM.append((name, res, f'({cx},{cy}) pivot {pivot}',
                 'CCW' if ccw else 'CW',
                 cycle or f'{360 / rate_deg_s:.0f}s/rot', reason))


def packet(res, x0, y0, x1, y1, period, travel, offset, name):
    """Glow packet traveling (x0,y0)->(x1,y1) each `period`s, moving for
    `travel`s then dark for the rest of the cycle."""
    ph = f'((({T}) + {offset}) % {period})'
    p = f'clamp({ph} / {travel}, 0, 1)'
    ax = f'{x0 - 15} + ({x1} - {x0}) * {p}'
    ay = f'{y0 - 15} + ({y1} - {y0}) * {p}'
    al = f'(({ph}) &lt; {travel} ? (200 * (1 - {p} * 0.4)) : 0)'
    XML.append(f'''    <PartImage x="{x0 - 15}" y="{y0 - 15}" width="30" height="30" name="{name}" alpha="0">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Transform target="x" value="{ax}" />
      <Transform target="y" value="{ay}" />
      <Transform target="alpha" value="{al}" />
      <Image resource="{res}" />
    </PartImage>''')
    ANIM.append((name, res, f'({x0},{y0})->({x1},{y1})', 'linear travel',
                 f'{period}s cycle, {travel}s transit, +{offset}s phase',
                 'energy packet: core feeds the displays'))


# ================= Z-ORDER SCENE =================

# 00 backing plate
img('plate_back', 240, 240, 480, 480, 'z00_plate', variants=('dim',), plane=2)

# 02 rear gear train (peeks through chassis cutouts)
rot('gear_rear_l', 166, 306, 260, 'z02_rear_gear_l', 2.0, base='TH', plane=3,
    reason='primary rear drive; slow hypnotic base motion', cycle='180s/rot')
rot('gear_rear_m', 330, 176, 150, 'z02_rear_gear_m', 3.0, base='TH', ccw=True, plane=3,
    reason='meshed with rear L (36T:24T -> 1.5x speed, counter-rotating)',
    cycle='120s/rot')

# 04 structural chassis
img('chassis', 240, 240, 480, 480, 'z04_chassis', variants=('dim',), plane=5)

# 04b outer scale + side glow arcs
img('ring60', 240, 240, 480, 480, 'z04_ring60', variants=('dim',), plane=5)
img('arc_blue', 240, 240, 480, 480, 'z04_arc_blue', alpha=190, variants=('hide',),
    transforms=[('alpha', f'150 + 45 * sin({T} * 8.3) * sin({T} * 2.9)')])
img('arc_magenta', 240, 240, 480, 480, 'z04_arc_magenta', alpha=190, variants=('hide',),
    transforms=[('alpha', f'150 + 45 * sin({T} * 7.1) * sin({T} * 3.3)')])
ANIM.append(('z04_arc_blue', 'arc_blue', '(240,240)', 'alpha shimmer',
             'beat of 8.3/2.9 rad/s sines', 'electrical hum on left neon arc'))
ANIM.append(('z04_arc_magenta', 'arc_magenta', '(240,240)', 'alpha shimmer',
             'beat of 7.1/3.3 rad/s sines', 'electrical hum on right neon arc'))

# 05 indexing rings (stepped mechanical time)
img('ring_min', 240, 240, 286, 286, 'z05_ring_min',
    transforms=[('angle', '[MINUTE] * 6')], variants=('dim',))
ANIM.append(('z05_ring_min', 'ring_min', '(240,240)', 'CW stepped',
             '60 positions, 6 deg per minute', 'minute indexing ring'))
img('ring_hour', 240, 240, 252, 252, 'z05_ring_hour',
    transforms=[('angle', '([HOUR_0_11] + [MINUTE] / 60) * 30')], variants=('dim',))
ANIM.append(('z05_ring_hour', 'ring_hour', '(240,240)', 'CW creeping',
             '12 positions, 30 deg per hour', 'hour indexing ring'))

# 05 quadrant gear clusters (each pair counter-rotates)
rot('gear_a', 138, 148, 110, 'z05_nw_gear_a', 15, plane=7,
    reason='NW cluster driver', cycle='24s/rot')
rot('gear_c', 204, 196, 60, 'z05_nw_gear_c', 27.5, ccw=True, plane=7,
    reason='meshed with NW A (22T:12T ratio)', cycle='13s/rot')
rot('gear_a', 342, 148, 110, 'z05_ne_gear_a', 12, ccw=True, plane=7,
    reason='NE cluster driver (mirrors NW)', cycle='30s/rot')
rot('gear_c', 276, 196, 60, 'z05_ne_gear_c', 22, plane=7,
    reason='meshed with NE A', cycle='16s/rot')
# ratchet advances one tooth per second (stepped, no smooth interpolation)
img('ratchet', 135, 332, 90, 90, 'z05_ratchet',
    transforms=[('angle', 'floor([SECOND]) * 18')], variants=('dim',))
ANIM.append(('z05_ratchet', 'ratchet', '(135,332)', 'CW stepped',
             '18 deg per second (20 teeth)', 'ratchet driving the SEC display'))
rot('gear_d', 192, 368, 44, 'z05_sw_gear_d', 30, ccw=True, plane=7,
    reason='SW escapement follower', cycle='12s/rot')
rot('gear_b', 342, 332, 84, 'z05_se_gear_b', 9, plane=7,
    reason='SE cluster driver', cycle='40s/rot')
# eccentric cam: offset pivot creates uneven apparent motion
img('cam', 286, 368, 72, 72, 'z05_se_cam',
    transforms=[('angle', f'360 - {T} * 24')], variants=('dim',), pivot=(0.42, 0.5))
ANIM.append(('z05_se_cam', 'cam', '(286,368) pivot (0.42,0.5)', 'CCW eccentric',
             '15s/rot', 'cam wobble via offset pivot'))
# pause-reverse-resume mechanism (spec motion #18)
img('gear_d', 300, 296, 44, 44, 'z05_se_gear_d',
    transforms=[('angle', f'{T} * 9 + 25 * sin({T} * 0.5)')], variants=('dim',))
ANIM.append(('z05_se_gear_d', 'gear_d', '(300,296)', 'CW with periodic reversal',
             'base 40s/rot + sinusoidal override',
             'hunting oscillation: pauses, briefly reverses, resumes'))

# 07 pistons (antiphase pair) — rod slides under fixed sleeve
for i, (px, phase) in enumerate([(206, 0), (274, 3.1416)]):
    XML.append(f'''    <PartImage x="{px - 8}" y="300" width="16" height="60" name="z07_rod_{i}" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="45" />
      <Transform target="x" value="{px - 8} + 7 * {PAR_Y}" />
      <Transform target="y" value="300 - 9 * sin({T} * 3.1416 + {phase})" />
      <Image resource="piston_rod" />
    </PartImage>''')
    ANIM.append((f'z07_rod_{i}', 'piston_rod', f'({px},330)', 'reciprocating',
                 '2s stroke', f'piston pair, {"left" if i == 0 else "right"} (antiphase)'))
    img('piston_sleeve', px, 345, 36, 70, f'z07_sleeve_{i}', variants=('dim',), plane=7)

# 08/09 energy conduits (below panels & reactor so ends look socketed)
img('conduit_blue', 145, 240, 150, 46, 'z08_conduit_h_blue', variants=('hide',), plane=7)
img('conduit_magenta', 335, 240, 150, 46, 'z09_conduit_h_magenta', variants=('hide',), plane=7)
img('conduit_blue', 240, 130, 110, 40, 'z08_conduit_v_top', angle=90, variants=('hide',), plane=7)
img('conduit_violet', 240, 356, 110, 40, 'z09_conduit_v_bot', angle=90, variants=('hide',), plane=7)
img('conduit_blue', 112, 112, 130, 40, 'z08_conduit_nw', angle=45, variants=('hide',), plane=7)
img('conduit_magenta', 368, 112, 130, 40, 'z09_conduit_ne', angle=315, variants=('hide',), plane=7)
img('conduit_blue', 112, 368, 130, 40, 'z08_conduit_sw', angle=315, variants=('hide',), plane=7)
img('conduit_magenta', 368, 368, 130, 40, 'z09_conduit_se', angle=45, variants=('hide',), plane=7)

# electric arcs: the four diagonal conduits crackle in short staggered bursts.
# Two bolt shapes per color flip at 10Hz while the burst window (0.55s) is
# open, with rand() brightness jitter — reads as a live arc, not a pulse.
for cx, cy, ang, col, corner, off, per in [
        (112, 112, 45, 'blue', 'nw', 0.0, 2.3),
        (368, 112, 315, 'magenta', 'ne', 0.7, 2.9),
        (112, 368, 315, 'blue', 'sw', 1.5, 3.4),
        (368, 368, 45, 'magenta', 'se', 2.2, 3.7)]:
    ph = f'((({T}) + {off}) % {per})'
    flip = f'(floor(({ph}) * 10) % 2)'
    for suffix, gate in (('a', flip), ('b', f'(1 - {flip})')):
        alpha_expr = f'(({ph}) &lt; 0.55 ? (({gate}) * (150 + rand(0, 105))) : 0)'
        img(f'bolt_{col}_{suffix}', cx, cy, 130, 40, f'z09_bolt_{corner}_{suffix}',
            alpha=0, angle=ang, transforms=[('alpha', alpha_expr)],
            variants=('hide',), plane=7)
    ANIM.append((f'z09_bolt_{corner}_a/b', f'bolt_{col}_a/b', f'({cx},{cy}) {ang}deg',
                 'burst crackle', f'0.55s burst per {per}s, 10Hz shape flip',
                 f'{corner.upper()} conduit lightning arc'))

# sparks zipping outward along the diagonals (faster than display packets)
packet('packet_blue', 158, 158, 66, 66, 4, 0.7, 0.9, 'z09_spark_nw')
packet('packet_magenta', 322, 158, 414, 66, 5, 0.8, 2.1, 'z09_spark_ne')
packet('packet_blue', 158, 322, 66, 414, 4.5, 0.75, 3.2, 'z09_spark_sw')
packet('packet_magenta', 322, 322, 414, 414, 5.5, 0.85, 0.3, 'z09_spark_se')

# packets: core -> displays, staggered so conduits never fire together
packet('packet_blue', 210, 240, 100, 240, 5, 1.3, 0, 'z09_pk_blue')
packet('packet_magenta', 270, 240, 380, 240, 5, 1.3, 2.5, 'z09_pk_magenta')
packet('packet_violet', 240, 310, 240, 396, 6, 1.4, 1.2, 'z09_pk_violet')
packet('packet_blue', 240, 170, 240, 100, 7, 1.5, 3.7, 'z09_pk_turbine')

# turbine module at 12 o'clock
rot('fan', 240, 88, 84, 'z10_fan', 72, plane=8,
    reason='intake turbine; fastest continuous element', cycle='5s/rot')
img('turbine_housing', 240, 88, 130, 130, 'z10_turbine_housing', variants=('dim',), plane=8)

# 10-12 reactor stack
img('core_bloom', 240, 240, 300, 300, 'z10_core_bloom', alpha=160,
    transforms=[('alpha', f'150 + 70 * sin({T} * 1.5708)')], variants=('hide',), plane=9)
ANIM.append(('z10_core_bloom', 'core_bloom', '(240,240)', 'alpha breath',
             '4s cycle', 'reactor breathing (bloom)'))
img('reactor_housing', 240, 240, 210, 210, 'z10_reactor_housing', variants=('dim',), plane=8)
rot('ring_outer_rot', 240, 240, 168, 'z11_ring_outer', 6, plane=8,
    reason='containment ring', cycle='60s/rot')
rot('ring_inner_rot', 240, 240, 132, 'z11_ring_inner', 9, ccw=True, plane=9,
    reason='gyroscopic ring, counter-rotates against containment', cycle='40s/rot')
img('core_glow', 240, 240, 176, 176, 'z12_core',
    transforms=[('angle', f'{TH} * 1.2'),
                ('alpha', f'205 + 50 * sin({T} * 1.5708)')], variants=('hide',),
    pivot=(0.5, 0.5), plane=9)
ANIM.append(('z12_core', 'core_glow', '(240,240)', 'slow CW drift + alpha breath',
             '300s/rot drift, 4s breath', 'plasma core; filaments drift not flash'))

# outward energy pulse every 6s
XML.append(f'''    <PartImage x="140" y="140" width="200" height="200" name="z12_pulse" alpha="0">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Transform target="width" value="90 + 240 * clamp((({T}) % 6) / 1.6, 0, 1)" />
      <Transform target="height" value="90 + 240 * clamp((({T}) % 6) / 1.6, 0, 1)" />
      <Transform target="x" value="240 - (90 + 240 * clamp((({T}) % 6) / 1.6, 0, 1)) / 2" />
      <Transform target="y" value="240 - (90 + 240 * clamp((({T}) % 6) / 1.6, 0, 1)) / 2" />
      <Transform target="alpha" value="((({T}) % 6) &lt; 1.6 ? (150 * (1 - clamp((({T}) % 6) / 1.6, 0, 1))) : 0)" />
      <Image resource="pulse_ring" />
    </PartImage>''')
ANIM.append(('z12_pulse', 'pulse_ring', '(240,240)', 'radial expansion + fade',
             'every 6s, 1.6s travel', 'soft energy pulse leaving the core'))

# minute-boundary synchronization surge (<1s, restrained)
XML.append(f'''    <PartImage x="120" y="120" width="240" height="240" name="z12_minute_surge" alpha="0">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Transform target="alpha" value="({T} &lt; 0.9 ? (170 * (1 - {T} / 0.9)) : 0)" />
      <Image resource="core_bloom" />
    </PartImage>''')
ANIM.append(('z12_minute_surge', 'core_bloom', '(240,240)', 'alpha flash decay',
             'first 0.9s of every minute', 'synchronization ritual: core flare as minute advances'))

# 12b interactive: reactor tap surge (official TAP trigger; hidden when idle)
XML.append('''    <PartAnimatedImage x="120" y="120" width="240" height="240" name="z12_tap_surge">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <AnimationController play="TAP" repeat="FALSE" loopCount="1"
                           beforePlaying="HIDE" afterPlaying="HIDE" />
      <AnimatedImage resource="surge" format="WEBP" />
    </PartAnimatedImage>''')
ANIM.append(('z12_tap_surge', 'surge.webp', '(240,240) 240px box', 'frame sequence',
             '1.5s @ 12fps on TAP', 'reactor surge: rings contract, core fires 6 spokes'))

# 12c startup ignition (plays once when the face becomes visible)
XML.append('''    <PartAnimatedImage x="120" y="120" width="240" height="240" name="z12_ignite">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <AnimationController play="ON_VISIBLE" repeat="FALSE" loopCount="1"
                           beforePlaying="HIDE" afterPlaying="HIDE" />
      <AnimatedImage resource="ignite" format="WEBP" />
    </PartAnimatedImage>''')
ANIM.append(('z12_ignite', 'ignite.webp', '(240,240) 240px box', 'frame sequence',
             '1.5s @ 12fps on ON_VISIBLE', 'startup: rings sweep in, core ignites'))

# 17/18 foreground glass glints — fastest parallax plane
img('glints', 240, 240, 480, 480, 'z18_glints', alpha=210, variants=('hide',), plane=14)
ANIM.append(('z18_glints', 'glints', '(240,240)', 'parallax only',
             'wrist tilt', 'foreground reflections; deepest parallax cue'))

# 13-15 display housings + live time + SEC energy feed
img('energy_col', 240, 352, 20, 60, 'z13_energy_col', alpha=220,
    transforms=[('alpha', f'150 + 100 * sin({T} * 6.2832)')], variants=('hide',))
ANIM.append(('z13_energy_col', 'energy_col', '(240,352)', 'alpha throb',
             '1s cycle', 'energy column feeding SEC display'))
img('display_hours', 88, 240, 136, 96, 'z13_display_hours', variants=('dim',))
img('display_minutes', 392, 240, 136, 96, 'z14_display_minutes', variants=('dim',))
img('display_sec', 240, 404, 104, 76, 'z15_display_sec', variants=('dim',))

XML.append(f'''    <DigitalClock x="24" y="216" width="128" height="66">
      <TimeText format="hh" hourFormat="SYNC_TO_DEVICE" align="CENTER"
                x="0" y="0" width="128" height="66">
        <Font family="orbitron" size="46" weight="BOLD" color="{BLUE}" />
      </TimeText>
    </DigitalClock>
    <DigitalClock x="328" y="216" width="128" height="66">
      <TimeText format="mm" align="CENTER" x="0" y="0" width="128" height="66">
        <Font family="orbitron" size="46" weight="BOLD" color="{MAGENTA}" />
      </TimeText>
    </DigitalClock>
    <DigitalClock x="196" y="388" width="88" height="46">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <TimeText format="ss" align="CENTER" x="0" y="0" width="88" height="46">
        <Font family="orbitron" size="32" weight="BOLD" color="{VIOLET}" />
      </TimeText>
    </DigitalClock>''')

body = '\n\n'.join(XML)
xml = f'''<?xml version="1.0" encoding="utf-8"?>
<WatchFace width="480" height="480">
  <Metadata key="CLOCK_TYPE" value="DIGITAL" />
  <Metadata key="PREVIEW_TIME" value="10:09:38" />
  <Scene backgroundColor="#ff000000">

{body}

  </Scene>
</WatchFace>
'''
with open(OUT_XML, 'w') as fh:
    fh.write(xml)

with open(OUT_MAP, 'w') as fh:
    fh.write('# CHRONOVA animation map\n\n'
             'Generated by `scripts/gen_watchface.py` — single source of truth.\n\n'
             '| Group | Asset | Pivot/Path | Direction | Cycle | Why it moves |\n'
             '|---|---|---|---|---|---|\n')
    for row in ANIM:
        fh.write('| ' + ' | '.join(str(c) for c in row) + ' |\n')
    fh.write(f'\nTotal independently animated groups: **{len(ANIM)}**\n')

print(f'watchface.xml written ({len(xml)} bytes); {len(ANIM)} animated groups')
