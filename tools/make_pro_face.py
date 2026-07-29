#!/usr/bin/env python3
"""Assemble a MERIDIAN PRO face from the procedural window layers.

The layers come from tools/make_pro_window.py. This turns them into a
watchface.xml: the state ladder, the parallax gains, the scroll cycles and
the wrist response — and then the instruments, hands and hub carried over
from the base face so PRO is a whole watch rather than a window demo.

WHAT PRO CHANGES, IN ONE LINE EACH

  The horizon banks. The world is sky+ground rotating together under a
  <Gyro angle>, and the furniture is drawn afterwards and never moved. This
  is the entire reason the line exists.

  The window has depth. Five layers move at five different rates — near
  cloud fastest, far cloud slower, the world barely at all — which is what
  makes an aperture read as a view rather than a picture. The glass moves
  the OTHER WAY, because droplets are on the canopy and the world is behind
  it; counter-motion is what tells the eye which is which.

  Weather is a tint, not a picture. Sixteen states, each a pair of hex
  colours and a cloud alpha over the same white sprites.

WHY EVERY CONSTRUCT HERE IS AN OLD ONE

The probe went black, and a face that fails to inflate says nothing about
why. So this introduces no new element: per-part <Gyro> (not <Group>, which
is schema-legal but never shipped here), <Transform> on angle/x/y, and
<Condition>/<Compare> — all already running on five faces.

TWO PLATFORM RULES OBSERVED

  Loop periods must divide 3600. The time base is seconds within the hour,
  which snaps 3599.999 to 0, so a cycle that does not close on the hour
  jumps once an hour. Every period below is a divisor.

  A Compare needs at least one child, and Default is optional
  (minOccurs="0", checked). So the states that draw no precipitation simply
  have no branch, rather than an empty one.

Usage:
    python3 tools/make_pro_face.py --face commodore
"""

from __future__ import annotations

import argparse
import math
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_pro_window import cfg, world_size  # noqa: E402

TITLE = {"commodore": "MERIDIAN COMMODORE PRO", "balsa": "MERIDIAN BALSA PRO",
         "pure": "MERIDIAN PURE PRO", "hayate": "MERIDIAN HAYATE PRO"}

# Seconds within the hour. Every scroll period must divide 3600.
T = "([MINUTE] * 60 + [SECOND] + [MILLISECOND] / 1000)"

# Per-layer wrist response. Angle is the bank; x/y are the parallax shift.
# The ordering is the whole trick: the world barely moves, near cloud moves
# most, and the glass moves NEGATIVE — against the view — because it is on
# the canopy rather than in the world.
#             bank°   x    y
GAIN = {
    "world":   (26.0, 3.0, 4.0),
    "sun":     (0.0, -5.0, -7.0),
    "cloudf":  (0.0,  8.0, 10.0),
    "cloudn":  (0.0, 14.0, 17.0),
    "precip":  (0.0,  6.0,  8.0),
    "glass":   (0.0, -9.0, -11.0),
}


def gyro(kind: str) -> str:
    """A <Gyro> guarded on ACCELEROMETER_IS_SUPPORTED, so a watch without the
    sensor sits at the neutral pose instead of being permanently offset."""
    a, gx, gy = GAIN[kind]
    sup = "[ACCELEROMETER_IS_SUPPORTED]"
    ang = (f'({sup} ? (0 - {a} * clamp([ACCELEROMETER_ANGLE_X], -45, 45) '
           f'/ 45) : 0)') if a else "0"
    x = (f'({sup} ? ({gx} * clamp([ACCELEROMETER_ANGLE_X], -40, 40) / 40) '
         f': 0)') if gx else "0"
    y = (f'({sup} ? ({gy} * clamp([ACCELEROMETER_ANGLE_Y], -40, 40) / 40) '
         f': 0)') if gy else "0"
    return f'<Gyro angle="{ang}" x="{x}" y="{y}" />'


# The ladder, most specific first — WFF renders the first matching Compare.
# (key, expression, sky, ground, cloud alpha, cloud tint)
WX = "[WEATHER.IS_AVAILABLE]"
P = "[WEATHER.CHANCE_OF_PRECIPITATION]"
TEMP = "[WEATHER.TEMPERATURE]"
NIGHT = f"{WX} &amp;&amp; ![WEATHER.IS_DAY]"
DAY = f"{WX} &amp;&amp; [WEATHER.IS_DAY]"

STATES = [
    # --- night ---------------------------------------------------------
    ("n_snow",  f"{NIGHT} &amp;&amp; {P} &gt;= 50 &amp;&amp; {TEMP} &lt;= 2",
     "#1A2233", "#3A4152", 0.55, "#7E8899"),
    ("n_rain",  f"{NIGHT} &amp;&amp; {P} &gt;= 50",
     "#0F1725", "#14161C", 0.60, "#4A5260"),
    ("n_cloud", f"{NIGHT} &amp;&amp; {P} &gt;= 15",
     "#0E1626", "#0B0E15", 0.45, "#3E4654"),
    ("n_clear", NIGHT, "#0C1420", "#080B12", 0.20, "#2A3140"),
    # --- day -----------------------------------------------------------
    ("d_freeze", f"{DAY} &amp;&amp; {TEMP} &lt;= -5",
     "#9FC4DE", "#D6E2EC", 0.45, "#EAF2F8"),
    ("d_snow_h", f"{DAY} &amp;&amp; {P} &gt; 75 &amp;&amp; {TEMP} &lt;= 2",
     "#8E9AA8", "#C6CDD4", 0.85, "#E2E8EE"),
    ("d_snow_l", f"{DAY} &amp;&amp; {P} &gt;= 50 &amp;&amp; {TEMP} &lt;= 2",
     "#9AA8B8", "#C8CDD2", 0.60, "#DDE4EA"),
    ("d_storm",  f"{DAY} &amp;&amp; {P} &gt;= 92",
     "#39414C", "#2A2A26", 0.92, "#69737F"),
    ("d_rain_h", f"{DAY} &amp;&amp; {P} &gt;= 80",
     "#48525E", "#33342E", 0.88, "#7A838F"),
    ("d_rain_l", f"{DAY} &amp;&amp; {P} &gt;= 65",
     "#5A6470", "#3C3A34", 0.78, "#8B939D"),
    ("d_scorch", f"{DAY} &amp;&amp; {TEMP} &gt;= 32",
     "#E4A445", "#8A6030", 0.18, "#F0D2A0"),
    ("d_over",   f"{DAY} &amp;&amp; {P} &gt;= 55",
     "#5E6A78", "#3E4038", 0.95, "#98A2AE"),
    ("d_vcloud", f"{DAY} &amp;&amp; {P} &gt;= 40",
     "#6E8496", "#4E5040", 0.80, "#B4BEC8"),
    ("d_cloud",  f"{DAY} &amp;&amp; {P} &gt;= 25",
     "#4E8CC0", "#6A5A3C", 0.55, "#D2DAE2"),
    ("d_hazy",   f"{DAY} &amp;&amp; {P} &gt;= 12",
     "#5E9AC8", "#74603C", 0.44, "#DCE4EC"),
    ("d_sunny",  DAY, "#3E96DC", "#7A5C34", 0.30, "#E8EEF4"),
]

# Precipitation is a separate, shorter ladder: several sky states share one
# tile, and a state with no precipitation gets no branch at all.
PRECIP = [
    ("snow", f"{WX} &amp;&amp; {P} &gt;= 50 &amp;&amp; {TEMP} &lt;= 2",
     "ov_snow", 6.0, False),
    ("storm", f"{WX} &amp;&amp; {P} &gt;= 92", "ov_storm", 1.2, True),
    ("rain_h", f"{WX} &amp;&amp; {P} &gt;= 80", "ov_storm", 1.5, False),
    ("rain", f"{WX} &amp;&amp; {P} &gt;= 50", "ov_rain", 1.5, False),
]

AMB = ('<Variant mode="AMBIENT" target="alpha" value="0" duration="0.4" '
       'startOffset="0.1" interpolation="EASE_OUT" />')


# Sub-dial centres, taken from the base face's own well positions so the new
# instruments land where the plate expects them, and the size measured
# against the real aperture rather than its bounding box.
DIALS = {
    "steps": dict(centre=(144.5, 301.5), size=96, src="STEP_COUNT",
                  lo=0, hi=20000, digits=19),
    "bpm":   dict(centre=(343.5, 303.5), size=96, src="HEART_RATE",
                  lo=0, hi=200, digits=27),
}
START_DEG, SWEEP_DEG = 235.0, 250.0

# The fuel sweep, kept identical to the base face's reserve needle mapping so
# the needle lands where the plate always expected it to.
FUEL_START, FUEL_SWEEP, FUEL_R = -48.0, 96.0, 152.0
# The readout sits BELOW the arc's apex (r=152 puts that at y=88) and above
# the plate's RESERVE at y=116 — a 26px band, so the number is centred in it
# rather than straddling the arc as it did at first.
# The readout now sits in a framed window BELOW the arc rather than in the
# 24px slot above the plate's RESERVE. That slot was never big enough for a
# framed aperture, and the frame is what stops the number floating.
# Cost, stated plainly: the window covers the plate's RESERVE wording and its
# wing emblem. RESERVE is misleading for a battery anyway — it is the
# aviation term for reserve FUEL — and the bolt now carries that meaning.
FUEL_WIN = (240.0, 126.0, 86.0, 37.0)      # cx, cy, w, h
FUEL_TEXT_CY = 126.0
BOLT_X = 215.0
COUNTER_CY = 0.36        # must match make_an_gauge.COUNTER_CY


def readout(name: str, x: int, y: int, w: int, h: int, size: int,
            src: str, fmt: str = "%d", colour: str = "#EBC468",
            amb: int = 0) -> list[str]:
    """One number, drawn as a shadow pass and a fill pass."""
    def part(tag, dx, dy, col, alpha):
        return [f'    <PartText name="{name}{tag}" x="{x + dx}" '
                f'y="{y + dy}" width="{w}" height="{h}" alpha="{alpha}">',
                f'      <Variant mode="AMBIENT" target="alpha" value="{amb}" '
                'duration="0.4" startOffset="0.2" interpolation="LINEAR" />',
                f'      <Text align="CENTER"><BitmapFont family="pro" '
                f'size="{size}" color="{col}"><Template>{fmt}'
                f'<Parameter expression="[{src}]" /></Template>'
                '</BitmapFont></Text>',
                '    </PartText>']

    # A DROP SHADOW ALONE WAS NOT ENOUGH. One offset copy gives an edge on
    # two sides and leaves the other two sitting flat on whatever is behind,
    # and on a busy plate that still reads as pasted on. What makes a bright
    # numeral lift off a background is a CONTINUOUS DARK OUTLINE — so the
    # number is drawn on all four diagonals to close the halo, then once more
    # further down for the cast shadow, then the fill.
    d = max(2, round(size * 0.11))
    o = []
    for dx, dy in ((-d, -d), (d, -d), (-d, d), (d, d)):
        o += part(f"_h{dx}_{dy}".replace("-", "n"), dx, dy, "#000000", 120)
    o += part("_sh", 0, int(d * 1.7), "#000000", 205)
    return o + part("", 0, 0, colour, 255)


def instruments(pre: str) -> list[str]:
    """The AN gauges, their needles, and the big live readouts.

    THE NUMBERS ARE THE POINT. Heart rate goes from 18px to 27 and the date
    from 19 to 24; steps only reaches 19 because five digits have to fit the
    counter window, and a number that overflows its window is worse than a
    smaller one. Two digits of pulse can be read at arm's length now, which
    four digits of steps never will be at this dial size.
    """
    o = []
    # --- fuel: the scale, then the needle over it ----------------------
    o += [f'    <PartImage name="z11_fuel_arc" x="0" y="0" width="480" '
          f'height="480" alpha="255">',
          f'      {AMB}',
          f'      <Image resource="{pre}_fuel_arc" />',
          '    </PartImage>',
          f'    <PartImage name="z11_fuel_needle" x="0" y="0" width="480" '
          f'height="480" alpha="255" pivotX="0.5" pivotY="0.5">',
          f'      {AMB}',
          f'      <Transform target="angle" value="{FUEL_START} + '
          f'{FUEL_SWEEP} * clamp([BATTERY_PERCENT], 0, 100) / 100" />',
          f'      <Image resource="{pre}_fuel_needle" />',
          '    </PartImage>']

    for key, c in DIALS.items():
        cx, cy = c["centre"]
        n = c["size"]
        x, y = int(round(cx - n / 2)), int(round(cy - n / 2))
        o += [f'    <PartImage name="z12_{key}_gauge" x="{x}" y="{y}" '
              f'width="{n}" height="{n}" alpha="255">',
              f'      {AMB}',
              f'      <Image resource="{pre}_gauge_{key}" />',
              '    </PartImage>']
        o += [f'    <PartImage name="z14_{key}_needle" x="{x}" y="{y}" '
              f'width="{n}" height="{n}" alpha="255" pivotX="0.5" '
              f'pivotY="0.5">',
              f'      {AMB}',
              f'      <Transform target="angle" value="{START_DEG} + '
              f'{SWEEP_DEG} * clamp([{c["src"]}], {c["lo"]}, {c["hi"]}) '
              f'/ {c["hi"]}" />',
              f'      <Image resource="{pre}_ptr_{key}" />',
              '    </PartImage>']
        # The live number, centred on the baked counter recess, and drawn
        # TWICE. A BitmapFont glyph is tinted flat by the runtime, so a
        # single PartText can only ever be a flat fill — which is exactly
        # why the readouts looked pasted on. A dark pass offset down-right
        # with the gold over it gives the digits an edge to sit on, using
        # two ordinary parts and no construct the line has not shipped.
        h = int(c["digits"] * 1.5)
        ty = int(round(y + n * COUNTER_CY - h / 2))
        o += readout(f"z21_{key}", x, ty, n, h, c["digits"], c["src"])

    # reserve and date, also enlarged — "all of the important numbers"
    # No percent sign: the owner asked for it gone, and a fuel gauge does
    # not carry one — a real one reads in gallons or in fractions of a tank.
    # Inside the window, so the digits have something to sit in. 24 fits the
    # 29px interior with room either side.
    o += readout("z20_reserve", 226, int(FUEL_TEXT_CY - 16), 68, 32, 24,
                 "BATTERY_PERCENT", colour="#EBC468", amb=130)
    # Aperture interior measured off the plate: x 327..386, y 212..251,
    # so its centre is (356.5, 232.5). The base face centred its date on
    # (352, 243) — four pixels left and ten low — and PRO inherited that
    # until it was measured rather than copied.
    o += readout("z23_date", 324, 216, 65, 33, 24, "DAY",
                 colour="#D6AA47", amb=150)
    return o


def build_xml(face: str) -> str:
    c = cfg(face)
    pre = c["prefix"]
    N = world_size(face)
    cx, cy = c["centre"]
    wx, wy = int(round(cx - N / 2)), int(round(cy - N / 2))
    o = []
    a = o.append

    a('<?xml version="1.0" encoding="utf-8"?>')
    a('<!--')
    a('GENERATED FILE - do not edit by hand.')
    a('  Authoritative source: tools/make_pro_face.py')
    a('  Layers:               tools/make_pro_window.py')
    a(f'  Regenerate: python3 tools/make_pro_face.py, face {face}')
    a('')
    a('The window is nine procedural layers, not one generated picture. The')
    a('world (sky + ground) banks under a Gyro and the furniture is drawn')
    a('after it and never moves, so the attitude indicator reads the right')
    a('way round. Every scroll period divides 3600.')
    a('-->')
    a('<WatchFace width="480" height="480">')
    a('  <Metadata key="CLOCK_TYPE" value="ANALOG" />')
    a('  <Metadata key="PREVIEW_TIME" value="10:09:32" />')

    base = REPO / f"watchfaces/{face}/app/src/main/res/raw/watchface.xml"
    src = base.read_text()
    # The "pro" family replaces the carried-over "cmd": Barlow Condensed
    # rather than DejaVu, because instrument lettering is a condensed
    # grotesque and because the condensation buys digits in the counter
    # window. Widths come from the glyphs that were actually rendered.
    a('  <BitmapFonts>')
    a('    <BitmapFont name="pro">')
    for ch, w in sorted(FONT_WIDTHS.items()):
        nm = "pct" if ch == "%" else ch
        a(f'      <Character name="{ch}" resource="cp_{nm}" width="{w}" '
          f'height="{GLYPH_H}" />')
    a('    </BitmapFont>')
    a('  </BitmapFonts>')
    a('  <Scene backgroundColor="#FF000000">')

    # plate
    a(f'    <PartImage name="z00_plate" x="0" y="0" width="480" height="480" '
      f'alpha="255">')
    a(f'      {AMB}')
    a(f'      <Image resource="{pre}_dial" />')
    a('    </PartImage>')
    a(f'    <PartImage name="z01_plate_aod" x="0" y="0" width="480" '
      f'height="480" alpha="0">')
    a('      <Variant mode="AMBIENT" target="alpha" value="255" '
      'duration="0.4" startOffset="0.0" interpolation="EASE_IN" />')
    a(f'      <Image resource="{pre}_dial_aod" />')
    a('    </PartImage>')

    def world_part(name, res, tint, extra=""):
        return [
            f'        <PartImage name="{name}" x="{wx}" y="{wy}" '
            f'width="{N}" height="{N}" alpha="255" pivotX="0.5" '
            f'pivotY="0.5" tintColor="{tint}">',
            f'          {AMB}',
            f'          {gyro("world")}',
            *( [f'          {extra}'] if extra else [] ),
            f'          <Image resource="{res}" />',
            '        </PartImage>']

    # ---- the world: sky + ground, banking together --------------------
    a('    <Condition>')
    a('      <Expressions>')
    for k, e, *_ in STATES:
        a(f'        <Expression name="w_{k}">{e}</Expression>')
    a('      </Expressions>')
    for i, (k, e, skc, gdc, ca, ct) in enumerate(STATES):
        a(f'      <Compare expression="w_{k}">')
        o.extend(world_part(f'z10_{k}_sky', 'pw_sky', skc))
        o.extend(world_part(f'z11_{k}_gnd', 'pw_ground', gdc))
        o.extend(world_part(f'z13_{k}_hzn', 'pw_horizon', '#DCEAF5'))
        if k.startswith("n_"):
            o.extend(world_part(f'z12_{k}_stars', 'pw_stars', '#FFFFFF'))
        a('      </Compare>')
    a('    </Condition>')

    # ---- sun / moon ---------------------------------------------------
    # Placed along a daylight arc: across the window and up over noon.
    frac = "clamp(([HOUR_0_23] + [MINUTE] / 60 - 6) / 12, 0, 1)"
    sx = f'{wx} + {N * 0.25:.1f} + {N * 0.50:.1f} * {frac} - {N / 2:.1f}'
    # The arc has to sit in the visible upper half of the APERTURE, not of
    # the world square — the world is drawn larger than the window so it can
    # rotate, so an arc centred on it puts the sun behind the surround.
    sy = (f'{wy} + {N * 0.475:.1f} - {N * 0.115:.1f} * sin(3.14159 * {frac})'
          f' - {N / 2:.1f}')
    a('    <Condition>')
    a('      <Expressions>')
    a(f'        <Expression name="c_night">{NIGHT}</Expression>')
    a(f'        <Expression name="c_day">{DAY}</Expression>')
    a('      </Expressions>')
    a('      <Compare expression="c_night">')
    a(f'        <PartImage name="z20_moon" x="{wx}" y="{wy}" width="{N}" '
      f'height="{N}" alpha="235" tintColor="#D8E2F0">')
    a(f'          {AMB}')
    a(f'          {gyro("sun")}')
    a('          <Image resource="pw_moon" />')
    a('        </PartImage>')
    a('      </Compare>')
    a('      <Compare expression="c_day">')
    a(f'        <PartImage name="z21_sun" x="{wx}" y="{wy}" width="{N}" '
      f'height="{N}" alpha="255" tintColor="#FFEEBB">')
    a(f'          {AMB}')
    a(f'          {gyro("sun")}')
    a(f'          <Transform target="x" value="{sx}" />')
    a(f'          <Transform target="y" value="{sy}" />')
    a('          <Image resource="pw_sun" />')
    a('        </PartImage>')
    a('      </Compare>')
    a('    </Condition>')

    # ---- cloud layers: two depths, two speeds -------------------------
    a('    <Condition>')
    a('      <Expressions>')
    for k, e, *_ in STATES:
        a(f'        <Expression name="c_{k}">{e}</Expression>')
    a('      </Expressions>')
    for k, e, skc, gdc, ca, ct in STATES:
        a(f'      <Compare expression="c_{k}">')
        for tag, res, per, gain, mul in (
                ("far", "pw_cloud_far", 120.0, "cloudf", 0.72),
                ("near", "pw_cloud_near", 60.0, "cloudn", 1.0)):
            alpha = max(0, min(255, int(255 * ca * mul)))
            if alpha < 4:
                continue
            a(f'        <PartImage name="z30_{k}_{tag}" x="{wx}" y="{wy}" '
              f'width="{N * 2}" height="{N}" alpha="{alpha}" '
              f'tintColor="{ct}">')
            a(f'          {AMB}')
            a(f'          {gyro(gain)}')
            a(f'          <Transform target="x" value="{wx} - {N} * '
              f'fract({T} / {per})" />')
            a(f'          <Image resource="{res}" />')
            a('        </PartImage>')
        a('      </Compare>')
    a('    </Condition>')

    # ---- precipitation, and the glass it lands on ---------------------
    bw, bh = c["box"]
    ox, oy = c["origin"]
    tile = 40
    a('    <Condition>')
    a('      <Expressions>')
    for k, e, *_ in PRECIP:
        a(f'        <Expression name="p_{k}">{e}</Expression>')
    a('      </Expressions>')
    for k, e, res, per, flash in PRECIP:
        a(f'      <Compare expression="p_{k}">')
        a(f'        <PartImage name="z40_{k}" x="{ox}" y="{oy - tile}" '
          f'width="{bw}" height="{bh + tile}" alpha="255" pivotX="0.5" '
          f'pivotY="0.5">')
        a(f'          {AMB}')
        a(f'          {gyro("precip")}')
        a(f'          <Transform target="y" value="{oy - tile} + {tile}.0 * '
          f'fract({T} / {per})" />')
        a(f'          <Image resource="{pre}_{res}" />')
        a('        </PartImage>')
        if flash:
            a(f'        <PartImage name="z41_{k}_flash" x="{ox}" y="{oy}" '
              f'width="{bw}" height="{bh}" alpha="255">')
            a(f'          {AMB}')
            a(f'          <Transform target="alpha" value="255 * '
              f'pow(1 - fract({T} / 24.0), 14.0)" />')
            a(f'          <Image resource="{pre}_ov_flash" />')
            a('        </PartImage>')
        # droplets on the canopy, counter-moving against the view
        a(f'        <PartImage name="z42_{k}_glass" x="{wx}" y="{wy}" '
          f'width="{N}" height="{N}" alpha="150">')
        a(f'          {AMB}')
        a(f'          {gyro("glass")}')
        a('          <Image resource="pw_glass" />')
        a('        </PartImage>')
        a('      </Compare>')
    a('    </Condition>')

    # ---- frost, cold only ---------------------------------------------
    a('    <Condition>')
    a('      <Expressions>')
    a(f'        <Expression name="f_cold">{WX} &amp;&amp; {TEMP} '
      f'&lt;= -1</Expression>')
    a('      </Expressions>')
    a('      <Compare expression="f_cold">')
    a(f'        <PartImage name="z45_frost" x="{wx}" y="{wy}" width="{N}" '
      f'height="{N}" alpha="190" tintColor="#CFE6F5">')
    a(f'          {AMB}')
    a(f'          {gyro("glass")}')
    a('          <Image resource="pw_frost" />')
    a('        </PartImage>')
    a('      </Compare>')
    a('    </Condition>')

    # ---- the mask, then the furniture that must never move ------------
    a(f'    <PartImage name="z50_surround" x="0" y="0" width="480" '
      f'height="480" alpha="255">')
    a(f'      {AMB}')
    a('      <Image resource="pw_surround" />')
    a('    </PartImage>')
    a(f'    <PartImage name="z51_furniture" x="{wx}" y="{wy}" width="{N}" '
      f'height="{N}" alpha="255">')
    a(f'      {AMB}')
    a('      <Image resource="pw_furn" />')
    a('    </PartImage>')

    # ---- the instruments ----------------------------------------------
    # The sub-dials are NOT carried over. They are redrawn as AN-standard
    # aircraft instruments (tools/make_an_gauge.py) at 96px rather than the
    # base face's 61/63, because the readouts were unreadable outdoors and
    # the limit on their size was never the plate — it was a bounding box.
    # The real aperture is an arch, and measuring it gave 60-66px of
    # clearance from each sub-dial centre where the box implied about 25.
    tail = src[src.index('    <PartImage name="z10_airscrew"'):
               src.index('  </Scene>')]
    drop = ("z11_reserve", "z12_gauge_steps", "z13_gauge_bpm",
            "z14_steps_needle", "z15_bpm_needle", "z20_reserve_pct",
            "z21_steps", "z22_bpm", "z23_date")
    kept, skip = [], False
    for line in tail.splitlines():
        st = line.strip()
        if st.startswith("<Part") and any(f'name="{n}"' in st for n in drop):
            skip = True
        if not skip:
            kept.append(line)
        if skip and (st.startswith("</Part") or st.endswith("/>")
                     and st.startswith("<Part")):
            skip = False
    a("\n".join(kept).rstrip())
    o.extend(instruments(pre))
    a('  </Scene>')
    a('</WatchFace>')
    return "\n".join(o) + "\n"


FONT_WIDTHS: dict = {}
GLYPH_H = 44


def an_gauges(face: str, dd: Path) -> None:
    """Draw the sub-dials as AN-standard aircraft instruments.

    The brief was to model a real aircraft's gauges as closely as possible
    and recolour them to the face. The reference is the P-51D's AN engine
    instruments, and the twelve-element grammar lives in
    tools/make_an_gauge.py — that module IS the documentation.

    Only the recess of the counter window is baked; the number itself is
    live text the face draws over it, so it has to be drawn from the same
    COUNTER_CY constant both ends use or the digits drift out of the hole.
    """
    import make_an_gauge as G
    slots = {"steps": "88888", "bpm": "888"}
    for key, spec in DIALS.items():
        gimg, pimg = G.build(key, spec["size"], counter=None,
                             window=slots[key])
        pre = cfg(face)["prefix"]
        gimg.save(dd / f"{pre}_gauge_{key}.png", optimize=True)
        pimg.save(dd / f"{pre}_ptr_{key}.png", optimize=True)
    # The fuel gauge: an arc across the top of the dial rather than a third
    # round well, because the round positions are taken and the one clear
    # band left on this plate is exactly this sweep — inside the hour
    # markers, above the wordmark, all of it dead navy at r=150.
    pre = cfg(face)["prefix"]
    arc = G.fuel_arc(480, 240, 240, FUEL_R, FUEL_START, FUEL_SWEEP)
    # The bolt goes LEFT of the readout and the readout shifts right by half
    # its width, so the pair reads as one group centred on the dial rather
    # than a number with something stuck beside it.
    arc.alpha_composite(G.counter_window(480, *FUEL_WIN))
    arc.alpha_composite(G.power_bolt(480, BOLT_X, FUEL_TEXT_CY, 19))
    arc.save(dd / f"{pre}_fuel_arc.png", optimize=True)
    G.fuel_needle(480, 240, 240, FUEL_R - 5,
                  r_tail=FUEL_R - 46).save(
        dd / f"{pre}_fuel_needle.png", optimize=True)

    global FONT_WIDTHS, GLYPH_H
    FONT_WIDTHS = G.bitmap_glyphs(dd, prefix="cp")
    GLYPH_H = G.GLYPH_H
    print("  sub-dials redrawn as AN aircraft instruments at "
          f"{DIALS['steps']['size']}px")
    print(f"  {len(FONT_WIDTHS)} Barlow Condensed glyphs for the readouts")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--face", default="commodore")
    a = ap.parse_args(argv)
    face = a.face

    dst = REPO / f"watchfaces/{face}-pro"
    draw = dst / "app/src/main/res/raw"
    draw.mkdir(parents=True, exist_ok=True)
    # ORDER MATTERS, and getting it wrong once cost a whole render: the
    # base face is copied FIRST and the PRO instruments generated over the
    # top. Generating first meant COMMODORE's own 61px cm_gauge_*.png
    # overwrote the AN gauges on the way past, and the face came out with
    # empty wells and floating numbers.
    sd = REPO / f"watchfaces/{face}/app/src/main/res/drawable"
    dd = dst / "app/src/main/res/drawable"
    dd.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sd.iterdir():
        if p.name.startswith(("m_",)) or any(
                k in p.name for k in ("_dial", "_hour", "_minute", "_hub",
                                      "_disc", "_gauge", "_ptr", "_needle",
                                      "_ov_")) or p.name == "preview.png":
            shutil.copy2(p, dd / p.name)
            n += 1
    # now the PRO instruments, over the top of what was just copied, and
    # the XML after them because it declares the glyph widths they produce
    an_gauges(face, dd)
    (draw / "watchface.xml").write_text(build_xml(face))

    # The launcher icon starts as the base face's, so the project builds
    # before it has ever been rendered. Once a render exists it is used
    # instead — a PRO face advertising COMMODORE's window in the picker is
    # exactly the confusion the separate package exists to avoid.
    shot = dst / "review/FACE_NORMAL.png"
    if shot.exists():
        from PIL import Image
        with Image.open(shot) as im:
            im.convert("RGB").resize((192, 192), Image.LANCZOS).save(
                dd / "preview.png", optimize=True)
        print("  preview.png regenerated from the PRO render")

    print(f"  watchface.xml -> {(draw / 'watchface.xml').relative_to(REPO)}")
    print(f"  {n} instrument drawables carried over from {face}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
