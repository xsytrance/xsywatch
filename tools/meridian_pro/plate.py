"""MERIDIAN PRO — the procedural dial: base, bezel, indices, milled plate.

Every pixel here is drawn from geometry.py's numbers with seeded arithmetic.
No model, no prompt, no reference pixels — original by construction, which
is the property that makes this face sellable.

House lessons applied throughout:
  - translucent work is COMPOSITED, never stamped (ImageDraw replaces alpha;
    a "shadow" drawn straight onto opaque steel punches a hole in it);
  - anything meant to be tinted later carries its shading in ALPHA;
  - text with depth is engraved (dark pass low, light pass high, fill on
    top) because flat fill is what makes a drawn dial look drawn.
"""

from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from geometry import (BEZEL, CANVAS, CHAPTER, CX, CY, DATE, MILITARY, MOON,
                      PALETTE as P, PLATE, SUBDIAL, WINDOWS, WORDMARK)

SS = 4
S = CANVAS * SS
SEED = 0x4D5250       # "MRP"

_F = os.path.expanduser("~/.local/share/fonts")
FONT_BOLD = f"{_F}/BarlowCondensed-Bold.ttf"
FONT_SEMI = f"{_F}/BarlowCondensed-SemiBold.ttf"
for _p in (FONT_BOLD, FONT_SEMI):
    if not os.path.exists(_p):
        FONT_BOLD = FONT_SEMI = \
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(px: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_SEMI, px * SS)


def shade(img: Image.Image, fn) -> None:
    """Composite translucent drawing instead of stamping it."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


def engrave(img, xy, text, f, fill, anchor="mm", depth=1.0):
    d = ImageDraw.Draw(img)
    x, y = xy
    o = max(1.0, depth * SS * 0.9)
    shade(img, lambda dd: (
        dd.text((x, y + o), text, font=f, fill=(0, 0, 0, 160), anchor=anchor),
        dd.text((x, y - o * 0.7), text, font=f, fill=(255, 255, 255, 42),
                anchor=anchor)))
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)


def _at(cx, cy, r, deg):
    a = math.radians(deg - 90.0)
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


def rotated_paste(canvas: Image.Image, sprite: Image.Image, centre, deg):
    """Paste a sprite rotated about its own centre at a canvas point."""
    rot = sprite.rotate(-deg, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(rot, (int(centre[0] - rot.width / 2),
                                 int(centre[1] - rot.height / 2)))


# ---------------------------------------------------------------- base

def dial_base() -> Image.Image:
    """The navy field under everything: radial falloff plus a whisper of
    circular brushing. The brushing is what stops a flat fill reading as a
    phone wallpaper — concentric strokes a couple of luminance points apart,
    the way spun metal picks up light."""
    rng = random.Random(SEED)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    hi, lo = P["dial_hi"], P["dial_lo"]
    steps = 120
    for i in range(steps, 0, -1):
        t = i / steps
        r = (BEZEL["outer_r"] * SS) * t
        col = tuple(int(lo[k] + (hi[k] - lo[k]) * (1 - t * t)) for k in range(3))
        d.ellipse([CX * SS - r, CY * SS - r, CX * SS + r, CY * SS + r],
                  fill=(*col, 255))
    def brush(dd):
        for _ in range(650):
            r = rng.uniform(30, BEZEL["inner_r"] - 4) * SS
            a0 = rng.uniform(0, 360)
            span = rng.uniform(6, 40)
            lum = rng.choice((255, 0))
            dd.arc([CX * SS - r, CY * SS - r, CX * SS + r, CY * SS + r],
                   a0, a0 + span, fill=(lum, lum, lum, rng.randint(4, 10)),
                   width=SS)
    shade(img, brush)
    return img


# --------------------------------------------------------------- bezel

def bezel(img: Image.Image) -> None:
    """The minute bezel: darker navy band, engraved gold numerals every five
    rotated tangentially, minor ticks between, lume triangle at zero."""
    d = ImageDraw.Draw(img)
    ro, ri = BEZEL["outer_r"] * SS, BEZEL["inner_r"] * SS
    cx, cy = CX * SS, CY * SS

    # the band, graded top-lit like a real coin-edge bezel
    band = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=(*P["bezel_hi"], 255))
    bd.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=(0, 0, 0, 0))
    grad = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(0, S, SS):
        gd.rectangle([0, y, S, y + SS], fill=int(50 * y / S))
    dark = Image.new("RGBA", (S, S), (*P["bezel_lo"], 255))
    band = Image.composite(dark, band, ImageChops_multiply_mask(grad, band))
    img.alpha_composite(band)

    # rim highlights: a machined edge catches light on top, loses it below
    shade(img, lambda dd: (
        dd.arc([cx - ro + SS, cy - ro + SS, cx + ro - SS, cy + ro - SS],
               160, 380, fill=(255, 255, 255, 46), width=2 * SS),
        dd.arc([cx - ri, cy - ri, cx + ri, cy + ri],
               -20, 200, fill=(0, 0, 0, 120), width=2 * SS),
        dd.arc([cx - ri, cy - ri, cx + ri, cy + ri],
               160, 380, fill=(255, 255, 255, 30), width=SS)))

    # ticks: minors every minute, majors every five (under the numerals)
    for m in range(60):
        deg = m * 6
        major = m % 5 == 0
        r1 = BEZEL["tick_outer_r"] * SS
        r0 = (BEZEL["tick_major_inner_r"] if major
              else BEZEL["tick_inner_r"]) * SS
        col = (*P["gold"], 235) if major else (*P["ink"], 120)
        d.line([_at(cx, cy, r0, deg), _at(cx, cy, r1, deg)],
               fill=col, width=(2 if major else 1) * SS)

    # numerals 05..55, engraved, each rotated to lie along the band
    f = font(BEZEL["numeral_px"])
    for m in range(5, 60, 5):
        deg = m * 6
        txt = f"{m:02d}"
        pad = 6 * SS
        w = int(f.getlength(txt)) + pad * 2
        h = BEZEL["numeral_px"] * SS + pad * 2
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        engrave(tile, (w / 2, h / 2), txt, f, (*P["gold"], 255), depth=1.2)
        # on the bottom half the tangential rotation turns glyphs on their
        # heads; real bezels (and the concept) flip them to read outward
        show = deg + (180 if 90 < deg < 270 else 0)
        rotated_paste(img, tile, _at(cx, cy, BEZEL["numeral_r"] * SS, deg),
                      show)

    # zero: the lume triangle, brightest thing on the bezel
    tip = _at(cx, cy, (BEZEL["inner_r"] + 6) * SS, 0)
    b1 = _at(cx, cy, BEZEL["numeral_r"] * SS + 9 * SS, -3.2)
    b2 = _at(cx, cy, BEZEL["numeral_r"] * SS + 9 * SS, 3.2)
    shade(img, lambda dd: dd.polygon(
        [tip, b1, b2], fill=(0, 0, 0, 140)))
    d.polygon([(tip[0], tip[1] - SS), (b1[0], b1[1] - SS),
               (b2[0], b2[1] - SS)], fill=(*P["lume"], 255))


def ImageChops_multiply_mask(grad: Image.Image, band: Image.Image):
    """Mask for the bezel's vertical grade, clipped to the band's alpha."""
    from PIL import ImageChops
    return ImageChops.multiply(grad, band.getchannel("A"))


# ------------------------------------------------------------- chapter

def indices(img: Image.Image) -> None:
    """Applied metal batons with a lume core at every hour, double at 12.
    Applied means they cast: a soft shadow offset down-right sells the
    couple of tenths of a millimetre they stand off the dial."""
    cx, cy = CX * SS, CY * SS
    for h in range(12):
        deg = h * 30
        offsets = ((-CHAPTER["twelve_gap"] / 2, CHAPTER["twelve_gap"] / 2)
                   if h == 0 else (0,))
        for off in offsets:
            w = CHAPTER["baton_w"] * SS
            l = CHAPTER["baton_l"] * SS
            tile = Image.new("RGBA", (int(w * 3), int(l * 1.6)), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            x0, y0 = w, l * 0.3
            # shadow first, composited
            shade(tile, lambda dd: dd.rounded_rectangle(
                [x0 + SS, y0 + SS, x0 + w + SS, y0 + l + SS],
                radius=2 * SS, fill=(0, 0, 0, 110)))
            # steel body, top-lit
            td.rounded_rectangle([x0, y0, x0 + w, y0 + l], radius=2 * SS,
                                 fill=(*P["steel"], 255))
            td.rounded_rectangle([x0, y0, x0 + w, y0 + l * 0.45],
                                 radius=2 * SS, fill=(*P["steel_hi"], 90))
            td.line([x0, y0 + l, x0 + w, y0 + l], fill=(*P["steel_lo"], 220),
                    width=SS)
            # lume core
            lw = CHAPTER["lume_w"] * SS
            td.rounded_rectangle(
                [x0 + (w - lw) / 2, y0 + 2.5 * SS,
                 x0 + (w + lw) / 2, y0 + l - 2.5 * SS],
                radius=SS, fill=(*P["lume"], 255))
            centre = _at(cx + off * SS * math.cos(math.radians(deg)),
                         cy + off * SS * math.sin(math.radians(deg)),
                         CHAPTER["ring_r"] * SS, deg)
            rotated_paste(img, tile, centre, deg)


# ---------------------------------------------------------------- plate

def _silhouette() -> Image.Image:
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    for kind, p in PLATE["shapes"]:
        if kind == "disc":
            c, r = p["c"], p["r"] * SS
            d.ellipse([c[0] * SS - r, c[1] * SS - r,
                       c[0] * SS + r, c[1] * SS + r], fill=255)
        else:
            c, w, h, rad = p["c"], p["w"] * SS, p["h"] * SS, p["rad"] * SS
            d.rounded_rectangle([c[0] * SS - w / 2, c[1] * SS - h / 2,
                                 c[0] * SS + w / 2, c[1] * SS + h / 2],
                                radius=rad, fill=255)
    # Metaball smoothing: blur the union and re-threshold. Every internal
    # corner where two shapes meet rounds into a fillet, which is what a
    # milled part actually has — no CNC leaves a knife-edge inside corner.
    m = m.filter(ImageFilter.GaussianBlur(6 * SS)).point(
        lambda v: 255 if v >= 128 else 0)
    return m


def centre_plate(img: Image.Image) -> None:
    """The milled steel plate, then its punched openings.

    Order matters and is the whole trick: steel body -> brushing -> bevel
    (light above, dark below, from the silhouette's own edge) -> drop
    shadow under the plate onto the dial -> screws -> THEN the wells and
    windows are punched, each with its own inner shadow, so every opening
    reads as a hole through metal rather than a dark sticker on it.
    """
    rng = random.Random(SEED ^ 0xB1)
    sil = _silhouette()

    # drop shadow onto the dial, from the silhouette, composited
    sh = sil.filter(ImageFilter.GaussianBlur(3 * SS))
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    shadow.putalpha(sh.point(lambda v: v * 140 // 255))
    img.alpha_composite(shadow)

    # steel body with vertical brushing
    steel = Image.new("RGBA", (S, S), (*P["steel"], 255))
    sd = ImageDraw.Draw(steel)
    for x in range(0, S, SS):
        if rng.random() < 0.8:
            lum = rng.randint(-16, 16)
            col = tuple(max(0, min(255, P["steel"][k] + lum)) for k in range(3))
            sd.line([(x, 0), (x, S)], fill=(*col, 255), width=SS)
    # gentle top-light, composited — stamped, these rows REPLACE the RGB
    # and the plate comes out white, which is exactly the shade() lesson
    light = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    for y in range(0, S, SS):
        t = y / S
        a = int(24 - 38 * t)
        if a > 0:
            ld.line([(0, y), (S, y)], fill=(255, 255, 255, a), width=SS)
        elif a < -6:
            ld.line([(0, y), (S, y)], fill=(0, 0, 0, min(40, -a)), width=SS)
    steel.alpha_composite(light)

    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    body.paste(steel, (0, 0), sil)

    # bevel from the silhouette's own edges: outline light shifted up-left,
    # dark shifted down-right
    edge = sil.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 24 else 0)
    b = int(PLATE["bevel_px"] * SS / 2)
    hi = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hi.paste(Image.new("RGBA", (S, S), (*P["steel_hi"], 150)), (-b, -b), edge)
    lo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    lo.paste(Image.new("RGBA", (S, S), (*P["steel_lo"], 190)), (b, b), edge)
    body.alpha_composite(lo)
    body.alpha_composite(hi)
    body.putalpha(sil)

    img.alpha_composite(body)
    d = ImageDraw.Draw(img)

    # screws: slotted, each at a random angle, seeded
    for sx, sy in PLATE["screws"]:
        r = PLATE["screw_r"] * SS
        x, y = sx * SS, sy * SS
        shade(img, lambda dd, x=x, y=y, r=r: dd.ellipse(
            [x - r - SS, y - r - SS, x + r + SS, y + r + SS],
            fill=(0, 0, 0, 90)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*P["steel_lo"], 255))
        d.ellipse([x - r + SS, y - r + SS, x + r - SS, y + r - SS],
                  fill=(*P["steel"], 255))
        ang = rng.uniform(0, math.pi)
        dx, dy = math.cos(ang) * (r - SS), math.sin(ang) * (r - SS)
        d.line([x - dx, y - dy, x + dx, y + dy], fill=(30, 36, 44, 255),
               width=SS)
        d.ellipse([x - r * 0.55, y - r, x + r * 0.15, y - r * 0.3],
                  fill=(255, 255, 255, 60))

    # ---- punched openings ----------------------------------------------
    def punch(cx_, cy_, rw, rh=None, rad=None):
        """Cut a well/window and give it the inward top shadow of a real
        counterbore. rh=None -> circle of radius rw."""
        x, y = cx_ * SS, cy_ * SS
        cut = Image.new("L", (S, S), 0)
        cd = ImageDraw.Draw(cut)
        if rh is None:
            cd.ellipse([x - rw * SS, y - rw * SS, x + rw * SS, y + rw * SS],
                       fill=255)
        else:
            cd.rounded_rectangle([x - rw * SS / 2, y - rh * SS / 2,
                                  x + rw * SS / 2, y + rh * SS / 2],
                                 radius=(rad or 8) * SS, fill=255)
        well = Image.new("RGBA", (S, S), (*P["well"], 255))
        img.paste(well, (0, 0), cut)
        # counterbore edge + inward shadow, composited
        er = cut.filter(ImageFilter.FIND_EDGES).point(
            lambda v: 255 if v > 24 else 0)
        ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ring.paste(Image.new("RGBA", (S, S), (0, 0, 0, 220)), (0, -SS), er)
        ring.paste(Image.new("RGBA", (S, S), (*P["steel_hi"], 70)), (0, SS), er)
        ring.putalpha(Image.composite(ring.getchannel("A"),
                                      Image.new("L", (S, S), 0),
                                      er.filter(ImageFilter.MaxFilter(3))))
        img.alpha_composite(ring)
        grad_sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        gsd = ImageDraw.Draw(grad_sh)
        if rh is None:
            gsd.pieslice([x - rw * SS, y - rw * SS, x + rw * SS, y + rw * SS],
                         180, 360, fill=(0, 0, 0, 95))
        else:
            gsd.rectangle([x - rw * SS / 2, y - rh * SS / 2,
                           x + rw * SS / 2, y - rh * SS / 2 + 5 * SS],
                          fill=(0, 0, 0, 95))
        grad_sh.putalpha(Image.composite(
            grad_sh.getchannel("A"), Image.new("L", (S, S), 0), cut))
        img.alpha_composite(grad_sh.filter(ImageFilter.GaussianBlur(SS)))

    punch(*SUBDIAL["steps_c"], SUBDIAL["well_r"])
    punch(*SUBDIAL["hr_c"], SUBDIAL["well_r"])
    for cc in (SUBDIAL["steps_c"], SUBDIAL["hr_c"]):
        x, y = cc[0] * SS, cc[1] * SS
        r = SUBDIAL["well_r"] * SS
        d.ellipse([x - r - 2.5 * SS, y - r - 2.5 * SS,
                   x + r + 2.5 * SS, y + r + 2.5 * SS],
                  outline=(*P["steel_lo"], 255), width=int(SS * 1.6))
        shade(img, lambda dd, x=x, y=y, r=r: dd.arc(
            [x - r - 2.5 * SS, y - r - 2.5 * SS,
             x + r + 2.5 * SS, y + r + 2.5 * SS],
            160, 380, fill=(255, 255, 255, 70), width=SS))
    punch(*MOON["c"], MOON["well_r"])
    punch(*WINDOWS["left_c"], WINDOWS["w"], WINDOWS["h"], 9)
    punch(*WINDOWS["right_c"], WINDOWS["w"], WINDOWS["h"], 9)
    punch(*DATE["c"], DATE["frame_w"], DATE["frame_h"], 12)

    # gold frame around the date window, the concept's balancing accent
    x, y = DATE["c"][0] * SS, DATE["c"][1] * SS
    w, h = DATE["frame_w"] * SS, DATE["frame_h"] * SS
    d.rounded_rectangle([x - w / 2 - SS, y - h / 2 - SS,
                         x + w / 2 + SS, y + h / 2 + SS],
                        radius=13 * SS, outline=(*P["gold"], 230),
                        width=int(SS * 1.4))


# ------------------------------------------------------------ wordmark

def wordmark(img: Image.Image) -> None:
    f1 = font(WORDMARK["meridian_px"])
    f2 = font(WORDMARK["sub_px"], bold=False)
    c = WORDMARK["meridian_c"]
    engrave(img, (c[0] * SS, c[1] * SS), "M E R I D I A N", f1,
            (48, 56, 66, 255), depth=1.3)
    c2 = WORDMARK["sub_c"]
    engrave(img, (c2[0] * SS, c2[1] * SS), "C O M M O D O R E", f2,
            (*P["gold"], 255), depth=0.8)


def compose_phase12() -> Image.Image:
    img = dial_base()
    bezel(img)
    indices(img)
    centre_plate(img)
    wordmark(img)
    return img.resize((CANVAS, CANVAS), Image.LANCZOS)
