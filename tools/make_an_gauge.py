#!/usr/bin/env python3
"""AN-standard aircraft instruments, drawn procedurally.

THE REFERENCE

North American P-51D Mustang, and specifically the AN (Army-Navy) engine
instruments in its cockpit — the tachometer, manifold pressure, oil and fuel
gauges. Chosen over the Spitfire's RAF panel or an F-14's for one practical
reason: **AN instruments are a written specification, not just a look.** That
makes "model it closely" a checkable exercise rather than a matter of taste,
and it makes the grammar below documentable and repeatable across faces.

THE GRAMMAR — twelve elements, in draw order

Each is a real feature of a real instrument, not a flourish. This list IS the
technique; anything that follows it reads as an aircraft gauge, and anything
that omits half of it reads as a generic dial with ticks.

   1  WELL          the recess the instrument sits in: a dark disc with an
                    inner shadow at the top, because the panel is lit from
                    above and the rim casts into the well
   2  DIAL FACE     matte, near-black, very slightly graded. Never glossy —
                    gloss on a real panel is glare, and glare is dangerous
   3  RANGE ARCS    green normal / yellow caution / red limit. THE SINGLE
                    MOST RECOGNISABLE FEATURE OF AN AIRCRAFT GAUGE, and the
                    only one that carries meaning rather than decoration
   4  GRADUATIONS   majors long and thick, four minors between them. Five
                    divisions per major is the AN convention
   5  REDLINE       a radial bar at the never-exceed value, drawn over the
                    arcs, always red however the rest is recoloured
   6  NUMERALS      only at majors, and only as many as fit. A cluttered
                    scale is unreadable at a glance, which is the whole job
   7  INDEX MARK    a luminous triangle at the scale origin. Radium then,
                    tritium later; here it is simply the brightest thing on
                    the dial
   8  LEGEND        the quantity and its unit, small, low on the face
   9  COUNTER       the digital window. AUTHENTIC — an altimeter carries a
                    drum counter for thousands beside a pointer for hundreds,
                    so a big number inside a round gauge is period-correct
                    rather than a modern intrusion
  10  POINTER       a thin shaft that widens to a spade near the tip, with a
                    counterbalance tail through the hub
  11  HUB           a domed cap with a highlight, hiding the pointer's root
  12  GLASS         one soft diagonal highlight at low alpha, and a vignette

RECOLOURING

The owner's brief was to keep the real thing's structure and change the
colours to suit the face. So the arcs keep their MEANING and their ORDER —
safe, caution, limit — while their hues move onto the dial's palette. Red
stays red: it is the one colour on an instrument that must not be restyled,
because it means "stop" everywhere in aviation and always has.

Usage:
    python3 tools/make_an_gauge.py --demo        # labelled anatomy sheet
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parent.parent
# Barlow Condensed, not DejaVu. A condensed grotesque is what instrument
# lettering actually is, and the condensation pays twice: it looks right, and
# it fits more digits into the counter window, which is the one thing that
# was capping the steps readout.
import os
_HOME = os.path.expanduser("~/.local/share/fonts")
FONT = f"{_HOME}/BarlowCondensed-Bold.ttf"
FONT_R = f"{_HOME}/BarlowCondensed-Medium.ttf"
if not os.path.exists(FONT):                       # fall back, never fail
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SS = 4

# COMMODORE's palette. Structure is the P-51's; the hues are the watch's.
# SAMPLED OFF THE PLATE, not invented. cm_dial's wing emblem is #D6AA47 and
# its field is #202F3E; the first pass guessed a lemon amber and a neutral
# charcoal and read as a different watch bolted onto this one.
PALETTE = {
    "well":     (18, 27, 37, 255),         # navy-tinted, like the plate
    "face":     (13, 22, 32, 255),
    "face_lo":  (7, 12, 18, 255),
    "grad":     (200, 212, 224, 255),      # off-white, not stark
    "grad_dim": (124, 140, 158, 255),
    "ink":      (214, 170, 71, 255),       # the wing gold exactly
    "counter":  (235, 196, 104, 255),      # a shade up, for the big readout
    "lume":     (176, 214, 194, 255),
    "pointer":  (232, 86, 60, 255),        # hot, and unique on the dial
    "arc_ok":   (47, 122, 102, 255),
    "arc_warn": (200, 154, 60, 255),       # the gold family, not "yellow"
    "arc_lim":  (184, 64, 47, 255),        # red stays red
    "bezel":    (92, 104, 116, 255),       # the plate's steel
    "screw":    (156, 168, 182, 255),
    "emboss_lo": (0, 0, 0, 150),           # text depth: cut below
    "emboss_hi": (255, 255, 255, 46),      # and catch light above
}

# AN convention: the scale occupies a sweep with a gap at the bottom, so the
# two ends never touch and the origin is unambiguous.
START_DEG = 235.0
SWEEP_DEG = 250.0


def shade(img, fn):
    """Composite semi-transparent work instead of stamping it.

    ImageDraw REPLACES a pixel, alpha included — it does not blend. So a
    "shadow" drawn at alpha 150 straight onto an opaque surface does not
    darken it, it PUNCHES A HOLE to alpha 150 and the plate shows through.
    That is exactly what happened to the fuel readout's window: its interior
    measured alpha 245 with a band of 92 along the top where the inner shadow
    was, and the plate's RESERVE wording read straight through it.

    Anything translucent therefore goes onto its own layer and is composited.
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


def engrave(d, xy, text, font, fill, p, anchor="mm", depth=1.0, img=None):
    """Text with depth, instead of text laid flat on the dial.

    Real instrument lettering is either etched into the face or raised off
    it; either way it catches light on one edge and casts into the other.
    Flat fill is the single thing that most makes a drawn dial look drawn.
    So: a dark pass offset down, a faint light pass offset up, the fill on
    top. It is three draws and it is most of the difference.
    """
    x, y = xy
    o = max(1.0, depth * SS * 0.9)
    if img is not None:
        shade(img, lambda dd: (
            dd.text((x, y + o), text, font=font, fill=p["emboss_lo"],
                    anchor=anchor),
            dd.text((x, y - o * 0.7), text, font=font, fill=p["emboss_hi"],
                    anchor=anchor)))
    else:
        d.text((x, y + o), text, font=font, fill=p["emboss_lo"], anchor=anchor)
        d.text((x, y - o * 0.7), text, font=font, fill=p["emboss_hi"],
               anchor=anchor)
    d.text((x, y), text, font=font, fill=fill, anchor=anchor)


def _at(c, r, deg):
    a = math.radians(deg - 90.0)
    return (c + math.cos(a) * r, c + math.sin(a) * r)


def _arc_box(c, r):
    return [c - r, c - r, c + r, c + r]


def gauge(size: int, label: str, unit: str, numerals: list[tuple[float, str]],
          arcs: list[tuple[float, float, str]], redline: float | None,
          pal: dict | None = None, counter: str | None = None,
          bezel: bool = True) -> Image.Image:
    """One instrument.

    `numerals` and `arcs` are positioned in SCALE FRACTION (0..1), not
    degrees, so a gauge can be re-scaled without moving its markings by hand.
    """
    p = dict(PALETTE, **(pal or {}))
    S = size * SS
    c = S / 2.0
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    r_out = c * 0.995
    r_face = c * (0.88 if bezel else 0.98)
    r_grad = r_face * 0.94          # outer end of the graduations
    r_maj = r_face * 0.80           # inner end, majors
    r_min = r_face * 0.87           # inner end, minors
    r_arc = r_face * 0.72           # the range arcs sit inside the ticks
    w_arc = max(2, int(r_face * 0.085))

    # 1 WELL — dark disc, with the rim shadowing into the top of it
    if bezel:
        d.ellipse(_arc_box(c, r_out), fill=p["well"])
        def _well(dd):
            for i in range(10, 0, -1):
                rr = r_face + (r_out - r_face) * i / 10.0
                dd.arc(_arc_box(c, rr), 190, 350,
                       fill=(0, 0, 0, int(120 * i / 10.0)),
                       width=max(1, int(SS * 1.2)))
        shade(img, _well)
        d = ImageDraw.Draw(img)

    # 2 DIAL FACE — matte, graded very slightly darker at the bottom
    d.ellipse(_arc_box(c, r_face), fill=p["face"])
    grad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(24):
        t = i / 23.0
        gd.rectangle([0, int(S * (0.5 + t * 0.5)), S, S],
                     fill=(*p["face_lo"][:3], int(7)))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse(_arc_box(c, r_face), fill=255)
    img.paste(Image.alpha_composite(img, grad), (0, 0), mask)
    d = ImageDraw.Draw(img)

    # 3 RANGE ARCS — the feature that says "aircraft" before anything else
    for f0, f1, key in arcs:
        a0 = START_DEG + SWEEP_DEG * f0 - 90.0
        a1 = START_DEG + SWEEP_DEG * f1 - 90.0
        d.arc(_arc_box(c, r_arc), a0, a1, fill=p[key], width=w_arc)

    # 4 GRADUATIONS — five divisions per major, AN convention
    majors = 10
    for i in range(majors * 5 + 1):
        f = i / (majors * 5.0)
        deg = START_DEG + SWEEP_DEG * f
        is_major = i % 5 == 0
        d.line([_at(c, r_maj if is_major else r_min, deg),
                _at(c, r_grad, deg)],
               fill=p["grad"] if is_major else p["grad_dim"],
               width=max(1, int(SS * (1.7 if is_major else 0.9))))

    # 5 REDLINE — over the arcs, and always red
    if redline is not None:
        deg = START_DEG + SWEEP_DEG * redline
        d.line([_at(c, r_arc - w_arc, deg), _at(c, r_grad, deg)],
               fill=p["arc_lim"], width=max(2, int(SS * 2.4)))

    # 6 NUMERALS — majors only, and only where they fit
    try:
        f_num = ImageFont.truetype(FONT, max(6, int(size * 0.115)) * SS)
        f_leg = ImageFont.truetype(FONT_R, max(5, int(size * 0.070)) * SS)
    except OSError:
        f_num = f_leg = ImageFont.load_default()
    for f, txt in numerals:
        deg = START_DEG + SWEEP_DEG * f
        engrave(d, _at(c, r_maj * 0.80, deg), txt, f_num, p["ink"], p)

    # 7 INDEX MARK — luminous triangle at the origin
    deg = START_DEG
    tip = _at(c, r_maj * 0.94, deg)
    b1 = _at(c, r_grad, deg - 3.4)
    b2 = _at(c, r_grad, deg + 3.4)
    d.polygon([tip, b1, b2], fill=p["lume"])

    # 8 LEGEND — quantity and unit, low on the face and out of the way
    # The sweep leaves a gap at the bottom of the dial with no graduations
    # in it. That gap is the only part of the face with nothing competing
    # for it, so the legend goes there.
    if label:
        engrave(d, (c, c * 1.30), label, f_leg, p["ink"], p, depth=0.7)
    if unit:
        engrave(d, (c, c * 1.42), unit, f_leg, p["grad_dim"], p,
                depth=0.7)
    return img, (c, r_face, r_maj, p)


def pointer(size: int, frac: float, pal: dict | None = None) -> Image.Image:
    """10 POINTER + 11 HUB.

    Drawn at the scale origin so the face spec rotates it by value; the
    watch's own Transform does the moving. The spade near the tip is what
    distinguishes an aircraft pointer from a clock hand — it gives the eye a
    definite point to read against a graduation.
    """
    p = dict(PALETTE, **(pal or {}))
    S = size * SS
    c = S / 2.0
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r_face = c * 0.88
    tip = r_face * 0.86
    spade = r_face * 0.60
    tail = r_face * 0.13
    w_shaft = max(1, int(r_face * 0.020))
    w_spade = max(2, int(r_face * 0.052))

    # a soft drop shadow, so the pointer floats above the arcs
    off = max(1, int(r_face * 0.012))
    d.polygon([(c + off, c - tip + off),
               (c - w_spade + off, c - spade + off),
               (c + w_spade + off, c - spade + off)], fill=(0, 0, 0, 100))
    # counterbalance tail through the hub
    d.line([(c, c + tail), (c, c - spade)], fill=p["pointer"], width=w_shaft)
    # the spade
    d.polygon([(c, c - tip), (c - w_spade, c - spade), (c + w_spade, c - spade)],
              fill=p["pointer"])

    # 11 HUB — domed cap with a highlight, hiding the root
    rh = r_face * 0.13
    d.ellipse([c - rh, c - rh, c + rh, c + rh], fill=(38, 44, 54, 255),
              outline=p["bezel"], width=max(1, int(SS)))
    d.ellipse([c - rh * 0.45, c - rh * 0.72, c + rh * 0.1, c - rh * 0.2],
              fill=(255, 255, 255, 60))
    return img.resize((size, size), Image.LANCZOS)


def finish(img, geom, size: int, counter: str | None, bezel: bool,
           window: str | None = None):
    """9 COUNTER, 12 GLASS, and the bezel screws."""
    c, r_face, r_maj, p = geom
    S = img.size[0]
    d = ImageDraw.Draw(img)

    # 9 COUNTER — the big readout, in a recessed window like an altimeter's
    # `window` sizes the recess for a placeholder without drawing digits:
    # on the watch the number is LIVE TEXT the face draws, so only the hole
    # it sits in is baked into the art.
    slot = counter if counter is not None else window
    if slot is not None:
        try:
            # Sized to the DIGIT COUNT, not to a constant: "8420" and "72"
            # must both sit inside the same window without touching the
            # graduations, and a fixed size makes one of them wrong.
            room = r_maj * 1.86   # a real counter window, not a chip
            fs = max(7, int(size * 0.21))
            while fs > 8:
                f_c = ImageFont.truetype(FONT, fs * SS)
                if d.textlength(slot, font=f_c) <= room:
                    break
                fs -= 1
            f_c = ImageFont.truetype(FONT, fs * SS)
        except OSError:
            f_c = ImageFont.load_default()
        cy = c * 0.72                      # above the hub, clear of it
        bb = d.textbbox((c, cy), slot, font=f_c, anchor="mm")
        pad = int(SS * 2.5)
        box = [bb[0] - pad * 2, bb[1] - pad, bb[2] + pad * 2, bb[3] + pad]
        # A cut window, not a dark patch: the aperture is punched through the
        # dial, so its top edge shadows inward and its bottom edge catches
        # the light coming down the panel.
        shade(img, lambda dd: (
            dd.rounded_rectangle(box, radius=pad, fill=(0, 0, 0, 215)),
            dd.line([(box[0] + pad, box[1]), (box[2] - pad, box[1])],
                    fill=(0, 0, 0, 235), width=max(1, int(SS * 1.6))),
            dd.line([(box[0] + pad, box[3]), (box[2] - pad, box[3])],
                    fill=(255, 255, 255, 40), width=max(1, int(SS * 1.1)))))
        d = ImageDraw.Draw(img)
        if counter is not None:
            engrave(d, (c, cy), counter, f_c, p["counter"], p, depth=1.4)

    # 12 GLASS — one diagonal highlight, low alpha, clipped to the face
    gl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(gl).polygon(
        [(0, S * 0.30), (S, 0), (S, S * 0.16), (0, S * 0.52)],
        fill=(255, 255, 255, 16))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse(_arc_box(c, r_face), fill=255)
    img.paste(Image.alpha_composite(img, gl), (0, 0), m)

    if bezel:
        d = ImageDraw.Draw(img)
        for deg in (45, 135, 225, 315):
            x, y = _at(c, (c * 0.995 + r_face) / 2.0, deg)
            rs = c * 0.045
            d.ellipse([x - rs, y - rs, x + rs, y + rs], fill=p["screw"])
            d.line([(x - rs * 0.6, y), (x + rs * 0.6, y)],
                   fill=(40, 46, 56, 255), width=max(1, int(SS)))
    return img.resize((size, size), Image.LANCZOS)


# The two instruments this face carries, described the way a real panel
# would describe them: a range, the arcs that qualify it, and a redline.
INSTRUMENTS = {
    "steps": dict(
        label="STEPS", unit="X100",
        numerals=[(0.0, "0"), (1.0, "20")],
        # sedentary is the "limit" here and the goal is the safe band, which
        # inverts a real gauge on purpose: the meaning is what is preserved,
        # not the direction
        arcs=[(0.0, 0.35, "arc_lim"), (0.35, 0.70, "arc_warn"),
              (0.70, 1.0, "arc_ok")],
        redline=None),
    "bpm": dict(
        label="PULSE", unit="BPM",
        numerals=[(0.0, "0"), (1.0, "200")],
        arcs=[(0.20, 0.50, "arc_ok"), (0.50, 0.80, "arc_warn"),
              (0.80, 1.0, "arc_lim")],
        redline=0.90),
}


def build(key: str, size: int, counter: str | None = None,
          bezel: bool = True, window: str | None = None):
    spec = INSTRUMENTS[key]
    img, geom = gauge(size, spec["label"], spec["unit"], spec["numerals"],
                      spec["arcs"], spec["redline"], counter=counter,
                      bezel=bezel)
    return (finish(img, geom, size, counter, bezel, window),
            pointer(size, 0.0))


# Where the counter sits inside the dial, as a fraction of the sprite. The
# face needs this to place its live text over the baked recess, and it must
# come from the same constant the art was drawn with or the two drift.
COUNTER_CY = 0.36       # c * 0.72 expressed against the full sprite


def fuel_arc(canvas: int, cx: float, cy: float, r: float, start: float,
             sweep: float, pal: dict | None = None) -> Image.Image:
    """A FUEL GAUGE, drawn as an arc across the top of the dial.

    Not every aircraft instrument is a full circle. Fuel is very often a
    sector sweeping E to F across the top of a panel, and that is lucky here:
    the round sub-dial positions are taken, and the one clear band left on
    this plate is exactly this arc — inside the hour markers, outside the
    wordmark, all of it dead navy.

    The grammar is the same twelve elements as a round instrument, minus the
    ones a sector does not have (no well, no hub). What it keeps is the part
    that matters: E to 1/8 is RED because that is reserve, 1/8 to 1/4 amber,
    and the rest green. A fuel gauge that does not tell you when to worry is
    just a bar chart.
    """
    p = dict(PALETTE, **(pal or {}))
    S = canvas * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    CX, CY, R = cx * SS, cy * SS, r * SS
    w_arc = max(2, int(R * 0.055))

    def at(frac, rad):
        a = math.radians(start + sweep * frac - 90.0)
        return (CX + math.cos(a) * rad, CY + math.sin(a) * rad)

    box = [CX - R, CY - R, CX + R, CY + R]
    for f0, f1, key in ((0.0, 0.125, "arc_lim"), (0.125, 0.25, "arc_warn"),
                        (0.25, 1.0, "arc_ok")):
        d.arc(box, start + sweep * f0 - 90, start + sweep * f1 - 90,
              fill=p[key], width=w_arc)

    # graduations: majors at E, 1/4, 1/2, 3/4, F with four minors between
    for i in range(4 * 4 + 1):
        f = i / 16.0
        major = i % 4 == 0
        r0 = R + w_arc * (0.6 if major else 0.6)
        r1 = R + w_arc * (2.5 if major else 1.7)
        d.line([at(f, r0), at(f, r1)],
               fill=p["grad"] if major else p["grad_dim"],
               width=max(1, int(SS * (1.8 if major else 1.0))))

    # the reserve end gets the luminous index, because that is the end you
    # need to find at a glance in the dark
    tip = at(0.0, R - w_arc * 1.2)
    b1 = at(0.0, R - w_arc * 0.1)
    b2 = at(0.028, R - w_arc * 0.6)
    d.polygon([tip, b1, b2], fill=p["lume"])

    try:
        f_lab = ImageFont.truetype(FONT, max(7, int(canvas * 0.036)) * SS)
    except OSError:
        f_lab = ImageFont.load_default()
    # Inside the arc, not outside it: outboard of r=152 the ends of the
    # sweep run straight into the 10 and 2 o'clock hour markers.
    for f, txt in ((0.0, "E"), (1.0, "F")):
        engrave(d, at(f, R - w_arc * 2.6), txt, f_lab, p["ink"], p, depth=0.9)
    return img.resize((canvas, canvas), Image.LANCZOS)


def fuel_needle(canvas: int, cx: float, cy: float, r_tip: float,
                pal: dict | None = None, r_tail: float | None = None
                ) -> Image.Image:
    """A FUEL POINTER, which is not the same shape as a tachometer's.

    The spade this started as belongs on an instrument you read a precise
    value off — altimeter, tach, manifold pressure — where the widened tip
    brackets a graduation. A fuel pointer is the opposite: a slender blade,
    WIDEST AT THE PIVOT AND TAPERING TO A SHARP POINT at the scale, with a
    counterweight boss at its root. You are reading a rough quantity against
    a coloured band, not a number, so the tip wants to be a point rather than
    a bracket.

    It rides just inside its own scale rather than reaching the hub. A sector
    pointer does geometrically pivot at the arc's centre — the middle of the
    watch here — but drawn full length it sweeps across the wordmark.
    """
    p = dict(PALETTE, **(pal or {}))
    S = canvas * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    CX, CY = cx * SS, cy * SS
    tip = r_tip * SS
    root = (r_tail if r_tail is not None else r_tip * 0.74) * SS
    half = max(2.0, SS * 3.1)          # half-width at the root
    boss = max(2.5, SS * 4.0)

    blade = [(CX, CY - tip),                    # the point
             (CX - half, CY - root),
             (CX + half, CY - root)]
    o = SS * 1.6
    d.polygon([(x + o, y + o) for x, y in blade], fill=(0, 0, 0, 125))
    d.ellipse([CX - boss + o, CY - root - boss + o,
               CX + boss + o, CY - root + boss + o], fill=(0, 0, 0, 110))
    d.polygon(blade, fill=p["pointer"])
    # counterweight boss, with a highlight so it reads as turned metal
    d.ellipse([CX - boss, CY - root - boss, CX + boss, CY - root + boss],
              fill=p["pointer"])
    d.ellipse([CX - boss * 0.42, CY - root - boss * 0.62,
               CX + boss * 0.1, CY - root - boss * 0.05],
              fill=(255, 255, 255, 90))
    return img.resize((canvas, canvas), Image.LANCZOS)


def counter_window(canvas: int, cx: float, cy: float, w: float, h: float,
                   pal: dict | None = None) -> Image.Image:
    """A framed, recessed readout window, matching the plate's date aperture.

    The battery number read as thrown on, and the reason was that it had no
    container. Every other number on this face sits in something: the
    sub-dial readouts in a recess cut into their own gauge face, the date in
    a brass-framed aperture punched through the plate. The fuel readout was
    floating on bare textured navy with only a drop shadow to hold it, and a
    shadow says "above" without saying "in".

    So it gets the plate's OWN window idiom, sampled from cm_dial's date
    aperture: a warm grey frame around a brushed bronze interior, lighter
    along the top edge where the bevel catches light and darker at the
    bottom. Matching an idiom the face already owns is what makes an addition
    look designed in rather than dropped on.
    """
    p = dict(PALETTE, **(pal or {}))
    S = canvas * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    X, Y = cx * SS, cy * SS
    W, H = w * SS / 2.0, h * SS / 2.0
    r = max(2, int(SS * 2.5))
    fr = max(2, int(SS * 1.4))

    box = [X - W, Y - H, X + W, Y + H]
    # frame, then a lighter top edge and darker bottom so it reads as bevel
    d.rounded_rectangle(box, radius=r, fill=(120, 113, 106, 255))
    d.arc(box, 180, 360, fill=(146, 138, 133, 255), width=fr)
    d.arc(box, 0, 180, fill=(88, 82, 76, 255), width=fr)
    # brushed bronze interior, sampled off the plate's date window
    inner = [X - W + fr * 1.6, Y - H + fr * 1.6, X + W - fr * 1.6,
             Y + H - fr * 1.6]
    d.rounded_rectangle(inner, radius=max(1, r - fr), fill=(73, 69, 64, 255))
    def _inside(dd):
        for i in range(int(inner[0]), int(inner[2]), max(1, SS)):
            if (i // max(1, SS)) % 2:
                dd.line([(i, inner[1]), (i, inner[3])],
                        fill=(66, 62, 57, 120), width=1)
        # the aperture is punched THROUGH, so its top edge casts inward
        for i in range(6):
            a = int(150 * (1 - i / 6.0))
            dd.line([(inner[0] + r, inner[1] + i * SS * 0.6),
                     (inner[2] - r, inner[1] + i * SS * 0.6)],
                    fill=(0, 0, 0, a), width=max(1, int(SS * 0.7)))
    shade(img, _inside)
    return img.resize((canvas, canvas), Image.LANCZOS)


def power_bolt(canvas: int, cx: float, cy: float, h: float,
               pal: dict | None = None) -> Image.Image:
    """A lightning bolt, so the top instrument says WHAT it is measuring.

    The plate already reads RESERVE, which is the aviation word for reserve
    fuel and says nothing about a battery. The gauge is a fuel gauge by
    design and a battery gauge by function, and one glyph resolves that
    without a word of explanation in any language.
    """
    p = dict(PALETTE, **(pal or {}))
    S = canvas * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    X, Y, H = cx * SS, cy * SS, h * SS
    w = H * 0.46
    pts = [(X + w * 0.18, Y - H / 2),
           (X - w * 0.52, Y + H * 0.10),
           (X - w * 0.04, Y + H * 0.10),
           (X - w * 0.22, Y + H / 2),
           (X + w * 0.52, Y - H * 0.14),
           (X + w * 0.02, Y - H * 0.14)]
    o = SS * 1.2
    d.polygon([(x + o, y + o) for x, y in pts], fill=(0, 0, 0, 150))
    d.polygon(pts, fill=p["counter"])
    return img.resize((canvas, canvas), Image.LANCZOS)


GLYPH_H = 44           # native cell; the face scales it down per readout


def bitmap_glyphs(out_dir, prefix="cp"):
    """The live-readout font, as WFF BitmapFont characters.

    WHY THESE ARE WHITE. A BitmapFont carries a `color` attribute and the
    runtime tints every glyph with it, so any colour baked in here is thrown
    away. That is also why the readouts look flat: one flat fill is all a
    single PartText can produce. Depth comes from the FACE drawing the number
    twice — a dark pass offset down, the gold on top — which is two ordinary
    PartText parts and no new construct.

    All glyphs share one measured vertical cell so digits sit on a common
    baseline; cropping each to its own ink box and rescaling makes a "1"
    as tall as an "8" and the readout wobbles as the value changes.
    """
    from PIL import Image, ImageDraw, ImageFont
    chars = [str(i) for i in range(10)] + ["%"]
    safe = {"%": "pct"}
    f = ImageFont.truetype(FONT, GLYPH_H * SS)
    boxes = [f.getbbox(c) for c in chars]
    top, bot = min(b[1] for b in boxes), max(b[3] for b in boxes)
    cell = bot - top
    scale = GLYPH_H / cell
    bear = round(SS * 1.1)
    widths = {}
    for ch in chars:
        b = f.getbbox(ch)
        w = max(1, b[2] - b[0])
        img = Image.new("RGBA", (w + 2 * bear, cell), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((bear - b[0], -top), ch, font=f,
                                 fill=(255, 255, 255, 255))
        img = img.resize((max(1, round(img.width * scale)), GLYPH_H),
                         Image.LANCZOS)
        img.save(out_dir / f"{prefix}_{safe.get(ch, ch)}.png", optimize=True)
        widths[ch] = img.width
    return widths


def demo(out: Path) -> None:
    """A labelled anatomy sheet, large, so the technique can be judged before
    it is shrunk to 78px and becomes a matter of faith."""
    big = 380
    def at(key, counter, frac):
        f, pt = build(key, big, counter=counter)
        out = f.copy()
        out.alpha_composite(pt.rotate(-(START_DEG + SWEEP_DEG * frac),
                                      resample=Image.BICUBIC))
        return out
    shown = at("bpm", "72", 72 / 200.0)
    shown2 = at("steps", "8420", 8420 / 20000.0)

    W, H = big * 2 + 150, big + 150
    sheet = Image.new("RGB", (W, H), (12, 13, 15))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT, 20)
    fs = ImageFont.truetype(FONT_R, 14)
    d.text((W / 2, 26),
           "AN-STANDARD INSTRUMENT GRAMMAR  —  P-51D, recoloured to COMMODORE",
           font=f, fill=(228, 234, 240), anchor="mm")
    sheet.paste(shown.convert("RGB"), (50, 70))
    sheet.paste(shown2.convert("RGB"), (big + 100, 70))
    for x, t in ((50 + big / 2, "PULSE  —  arcs carry heart-rate zones"),
                 (big + 100 + big / 2, "STEPS  —  arcs carry goal progress")):
        d.text((x, 70 + big + 22), t, font=fs, fill=(186, 194, 202),
               anchor="mm")
    d.text((W / 2, H - 34),
           "green normal / amber caution / red limit  ·  spade pointer  ·  "
           "luminous index  ·  counter window  ·  redline at 180 bpm",
           font=fs, fill=(150, 158, 168), anchor="mm")
    sheet.save(out)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default="/tmp/dl/AN-gauge-anatomy.png")
    a = ap.parse_args(argv)
    if a.demo:
        demo(Path(a.out))
        print(f"  anatomy sheet -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
