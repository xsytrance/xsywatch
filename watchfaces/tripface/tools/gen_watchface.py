import os as _os
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
"""Generate res/raw/watchface.xml — EQ-bar digit clock + animated bars/rings."""
import random

OUT = _ROOT + '/app/src/main/res/raw/watchface.xml'
GREENS = ['#9BE821', '#C6FF4A', '#5A8C12']
rnd = random.Random(7)

T = '([SECOND] + [MILLISECOND] / 1000)'  # smooth clock-time seconds

# Live heart rate with fallback to 70bpm when the sensor has no reading yet.
# NB: this lands in XML attributes, so the comparison must be entity-escaped.
BPM = '(clamp(([HEART_RATE] &lt; 30 ? 70 : [HEART_RATE]), 40, 220))'
BEAT = f'abs(sin({T} * {BPM} * 0.05236))'  # one full pulse per beat (pi/60)

# --- 13 fake-EQ bars, baseline y=432, growing upward ---
bars = []
n = 13
bw, gap = 12, 6
total = n * (bw + gap) - gap
x0 = (480 - total) // 2
for i in range(n):
    x = x0 + i * (bw + gap)
    hmax = rnd.randint(34, 62)
    f = round(rnd.uniform(1.3, 3.1), 2)
    p = round(rnd.uniform(0, 6.28), 2)
    col = GREENS[i % 3]
    # bounce speed follows the wearer's live heart rate (70bpm = 1x)
    h = f'({hmax} * (0.18 + 0.82 * abs(sin({T} * {f} * ({BPM} / 70) + {p}))))'
    bars.append(f'''      <PartDraw x="{x}" y="380" width="{bw}" height="70" name="bar{i}">
        <Transform target="height" value="{h}" />
        <Transform target="y" value="432 - {h}" />
        <Rectangle x="0" y="0" width="{bw}" height="70">
          <Fill color="{col}" />
        </Rectangle>
      </PartDraw>''')
bars_xml = '\n'.join(bars)

# --- EQ-digit clock: 4 conditional slots + colon, 12h with leading zero ---
# Compare's expression attribute must NAME an Expression (XSD keyref), so each
# numeral gets its own boolean expression.
SLOTS = [
    ('ht', 56,  'floor([HOUR_1_12] / 10)', (0, 1),  1.7, 0.4),
    ('ho', 140, '([HOUR_1_12] % 10)',      range(10), 2.1, 2.2),
    ('mt', 246, 'floor([MINUTE] / 10)',    range(6), 1.9, 4.1),
    ('mo', 330, '([MINUTE] % 10)',         range(10), 2.4, 5.3),
]
DY = 288
slots_xml = []
for name, x, expr, values, f, p in SLOTS:
    exprs = '\n'.join(
        f'          <Expression name="{name}_is_{v}"><![CDATA[({expr}) == {v}]]></Expression>'
        for v in values)
    branches = '\n'.join(
        f'''        <Compare expression="{name}_is_{v}">
          <PartImage x="0" y="0" width="80" height="104" name="{name}_{v}">
            <Image resource="eqd{v}" />
          </PartImage>
        </Compare>''' for v in values)
    slots_xml.append(f'''    <Group x="{x}" y="{DY}" width="80" height="104" name="slot_{name}" alpha="255">
      <Transform target="alpha" value="200 + 55 * abs(sin({T} * {f} + {p}))" />
      <Condition>
        <Expressions>
{exprs}
        </Expressions>
{branches}
        <Default>
          <PartImage x="0" y="0" width="80" height="104" name="{name}_def">
            <Image resource="eqd0" />
          </PartImage>
        </Default>
      </Condition>
    </Group>''')
slots_xml = '\n'.join(slots_xml)

# --- Mini LED readouts: heart rate (3 digits) and steps (5 digits) ---
def mini_slots(prefix, x0, y0, count, value_expr, f, p, res='md'):
    """A row of `count` mini digits (22x30, 2px gap) reading value_expr."""
    groups = []
    for i in range(count):
        div = 10 ** (count - 1 - i)
        expr = f'(floor(({value_expr}) / {div}) % 10)'
        name = f'{prefix}{i}'
        exprs = '\n'.join(
            f'          <Expression name="{name}_is_{v}"><![CDATA[({expr}) == {v}]]></Expression>'
            for v in range(10))
        branches = '\n'.join(
            f'''        <Compare expression="{name}_is_{v}">
          <PartImage x="0" y="0" width="22" height="30" name="{name}_{v}">
            <Image resource="{res}{v}" />
          </PartImage>
        </Compare>''' for v in range(10))
        groups.append(f'''    <Group x="{x0 + i * 24}" y="{y0}" width="22" height="30" name="slot_{name}" alpha="255">
      <Transform target="alpha" value="200 + 55 * abs(sin({T} * {f} + {p}))" />
      <Condition>
        <Expressions>
{exprs}
        </Expressions>
{branches}
        <Default>
          <PartImage x="0" y="0" width="22" height="30" name="{name}_def">
            <Image resource="{res}0" />
          </PartImage>
        </Default>
      </Condition>
    </Group>''')
    return '\n'.join(groups)

RY = 240  # readout row, between the pendant and the big clock
hr_xml = f'''    <!-- Heart rate: pixel heart beating at the live BPM + mini readout -->
    <PartImage x="60" y="{RY - 9}" width="150" height="48" name="hr_pad" alpha="220">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Image resource="padsmall" />
    </PartImage>
    <PartImage x="76" y="{RY + 2}" width="28" height="24" name="hr_heart" alpha="255">
      <Transform target="alpha" value="90 + 165 * {BEAT}" />
      <Image resource="ledheart" />
    </PartImage>
{mini_slots('hr', 112, RY, 3, f'clamp([HEART_RATE], 0, 999)', 1.5, 0.9, res='mdr')}
'''

steps_xml = f'''    <!-- Steps: LED odometer + goal arc charging the rim -->
    <PartImage x="252" y="{RY - 9}" width="170" height="48" name="st_pad" alpha="220">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Image resource="padsmall" />
    </PartImage>
    <PartImage x="266" y="{RY + 3}" width="28" height="24" name="st_feet" alpha="235">
      <Image resource="ledfeet" />
    </PartImage>
{mini_slots('st', 300, RY, 5, 'clamp([STEP_COUNT], 0, 99999)', 1.2, 3.7, res='mda')}
    <PartDraw x="0" y="0" width="480" height="480" name="step_arc" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Arc centerX="240" centerY="240" width="462" height="462" startAngle="0" endAngle="360">
        <Stroke color="#33502A08" thickness="7" cap="ROUND" />
      </Arc>
      <Arc centerX="240" centerY="240" width="462" height="462" startAngle="0" endAngle="0">
        <Transform target="endAngle" value="clamp([STEP_PERCENT], 0, 100) * 3.6" />
        <Stroke color="#FFA528" thickness="7" cap="ROUND" />
      </Arc>
    </PartDraw>
'''

xml = f'''<?xml version="1.0" encoding="utf-8"?>
<WatchFace width="480" height="480">
  <Metadata key="CLOCK_TYPE" value="DIGITAL" />
  <Metadata key="PREVIEW_TIME" value="10:08:32" />
  <Scene backgroundColor="#ff000000">

    <!-- Artwork background; dims heavily in ambient to stay AMOLED-friendly -->
    <PartImage x="0" y="0" width="480" height="480" name="bg" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="60" />
      <Image resource="bg" />
    </PartImage>

    <!-- Counter-rotating psychedelic rings -->
    <PartImage x="0" y="0" width="480" height="480" name="ring_outer" alpha="210"
               pivotX="0.5" pivotY="0.5">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Transform target="angle" value="{T} * 6" />
      <Image resource="ring" />
    </PartImage>
    <PartImage x="30" y="30" width="420" height="420" name="ring_inner" alpha="90"
               pivotX="0.5" pivotY="0.5">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Transform target="angle" value="360 - {T} * 9" />
      <Image resource="ring" />
    </PartImage>

    <!-- Fake-EQ bars: sine-driven, each with its own frequency and phase -->
    <Group x="0" y="0" width="480" height="480" name="eq" alpha="235">
      <Variant mode="AMBIENT" target="alpha" value="0" />
{bars_xml}
    </Group>

    <!-- Soft shadow pad so the digits pop over the art -->
    <PartImage x="50" y="278" width="380" height="124" name="clockpad" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Image resource="clockpad" />
    </PartImage>

    <!-- EQ-bar digit clock -->
{slots_xml}

{hr_xml}
{steps_xml}

    <!-- Pulsing colon -->
    <PartImage x="224" y="{DY}" width="18" height="104" name="colon" alpha="255">
      <Transform target="alpha" value="120 + 135 * abs(sin({T} * 3.1416))" />
      <Image resource="eqcolon" />
    </PartImage>

  </Scene>
</WatchFace>
'''
with open(OUT, 'w') as fh:
    fh.write(xml)
print('watchface.xml written,', len(xml), 'bytes')
