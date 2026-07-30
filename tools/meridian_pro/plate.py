"""MERIDIAN PRO — the procedural layout, v2: the concept's structures.

v1 gave Kontext a bare simplified plate and the result read as a diagram.
v2 draws every structure the concept actually has — the two-level bridge,
rivet rows on every panel edge, the bezel's applied indices, the power
arc's recessed channel, the wordmark's own inset plate, the arch starfield,
framed icon windows, the day's black inset box — so the generator has real
hardware to make real. Kontext glosses; it is not allowed to invent.

House rules throughout: translucent work composited (never stamped), text
engraved, every coordinate imported from geometry.py.
"""

from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from geometry import (BEZEL, CANVAS, CHAPTER, CX, CY, DATE, MILITARY, MOON,
                      PALETTE as P, PANEL, PLATE, POWER, SUBDIAL, WINDOWS,
                      WORDMARK)

SS = 4
S = CANVAS * SS
SEED = 0x4D5250

_F = os.path.expanduser("~/.local/share/fonts")
FONT_BOLD = f"{_F}/BarlowCondensed-Bold.ttf"
FONT_SEMI = f"{_F}/BarlowCondensed-SemiBold.ttf"
for _p in (FONT_BOLD, FONT_SEMI):
    if not os.path.exists(_p):
        FONT_BOLD = FONT_SEMI = \
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(px, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_SEMI, px * SS)


def shade(img, fn):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


def engrave(img, xy, text, f, fill, anchor="mm", depth=1.0):
    d = ImageDraw.Draw(img)
    x, y = xy
    o = max(1.0, depth * SS * 0.9)
    shade(img, lambda dd: (
        dd.text((x, y + o), text, font=f, fill=(0, 0, 0, 170), anchor=anchor),
        dd.text((x, y - o * 0.7), text, font=f, fill=(255, 255, 255, 42),
                anchor=anchor)))
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)


def _at(cx, cy, r, deg):
    a = math.radians(deg - 90.0)
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


def rotated_paste(canvas, sprite, centre, deg):
    rot = sprite.rotate(-deg, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(rot, (int(centre[0] - rot.width / 2),
                                 int(centre[1] - rot.height / 2)))


# ---------------------------------------------------------------- base

def dial_base():
    rng = random.Random(SEED)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    hi, lo = P["dial_hi"], P["dial_lo"]
    # Nearly flat dusty slate — the concept has NO black rim vignette; its
    # chapter ring is LIGHTER than this build's ever was. Gentle centre dip
    # only.
    for i in range(120, 0, -1):
        tt = i / 120
        r = (BEZEL["outer_r"] * SS) * tt
        col = tuple(int(hi[k] + (lo[k] - hi[k]) * (1 - tt) * 0.6)
                    for k in range(3))
        d.ellipse([CX * SS - r, CY * SS - r, CX * SS + r, CY * SS + r],
                  fill=(*col, 255))
    def brush(dd):
        for _ in range(650):
            r = rng.uniform(30, BEZEL["inner_r"] - 4) * SS
            a0 = rng.uniform(0, 360)
            dd.arc([CX * SS - r, CY * SS - r, CX * SS + r, CY * SS + r],
                   a0, a0 + rng.uniform(6, 40),
                   fill=(rng.choice((255, 0)),) * 3 + (rng.randint(4, 10),),
                   width=SS)
    shade(img, brush)
    return img


# --------------------------------------------------------------- bezel

def _rivet(img, x, y, rng, r=None):
    r = (r or PLATE["rivet_r"]) * SS
    d = ImageDraw.Draw(img)
    shade(img, lambda dd: dd.ellipse(
        [x - r, y - r + SS, x + r, y + r + SS], fill=(0, 0, 0, 110)))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(*P["steel"], 255))
    d.ellipse([x - r * 0.6, y - r, x + r * 0.2, y - r * 0.2],
              fill=(255, 255, 255, 120))
    d.arc([x - r, y - r, x + r, y + r], 20, 200,
          fill=(*P["steel_lo"], 200), width=max(1, SS // 2))


def bezel(img):
    d = ImageDraw.Draw(img)
    rng = random.Random(SEED ^ 0xBE)
    ro, ri = BEZEL["outer_r"] * SS, BEZEL["inner_r"] * SS
    cx, cy = CX * SS, CY * SS

    band = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.ellipse([cx - ro, cy - ro, cx + ro, cy + ro],
               fill=(*P["bezel_hi"], 255))
    bd.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=(0, 0, 0, 0))
    grad = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(0, S, SS):
        gd.rectangle([0, y, S, y + SS], fill=int(22 * y / S))
    dark = Image.new("RGBA", (S, S), (*P["bezel_lo"], 255))
    band = Image.composite(dark, band,
                           ImageChops.multiply(grad, band.getchannel("A")))
    img.alpha_composite(band)

    shade(img, lambda dd: (
        dd.arc([cx - ro + SS, cy - ro + SS, cx + ro - SS, cy + ro - SS],
               160, 380, fill=(255, 255, 255, 46), width=2 * SS),
        dd.arc([cx - ri, cy - ri, cx + ri, cy + ri], -20, 200,
               fill=(0, 0, 0, 70), width=2 * SS),
        dd.arc([cx - ri, cy - ri, cx + ri, cy + ri], 160, 380,
               fill=(255, 255, 255, 30), width=SS)))

    for m in range(60):
        deg = m * 6
        major = m % 5 == 0
        r1 = BEZEL["tick_outer_r"] * SS
        r0 = (BEZEL["tick_major_inner_r"] if major
              else BEZEL["tick_inner_r"]) * SS
        d.line([_at(cx, cy, r0, deg), _at(cx, cy, r1, deg)],
               fill=(184, 156, 114, 150) if major else (*P["ink"], 90),
               width=(2 if major else 1) * SS)

    # numerals 05..55 plus the gold 12 at the top (gap item 2)
    f = font(BEZEL["numeral_px"])
    marks = [(m * 6, f"{m:02d}") for m in range(5, 60, 5)] + [(0, "12")]
    for deg, txt in marks:
        pad = 6 * SS
        w = int(f.getlength(txt)) + pad * 2
        h = BEZEL["numeral_px"] * SS + pad * 2
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        # muted like the concept: soft desaturated gold, gentler engrave
        engrave(tile, (w / 2, h / 2), txt, f,
                (206, 176, 128, 235) if txt == "12" else (184, 156, 114, 215),
                depth=0.7)
        show = deg + (180 if 90 < deg < 270 else 0)
        rotated_paste(img, tile, _at(cx, cy, BEZEL["numeral_r"] * SS, deg),
                      show)

    # applied trapezoid indices with lume, between the numerals (item 1)
    aw = BEZEL["applique_w"] * SS
    al = BEZEL["applique_l"] * SS
    for k in range(12):
        deg = 15 + k * 30
        tile = Image.new("RGBA", (int(aw * 2.4), int(al * 1.8)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        x0, y0 = aw * 0.7, al * 0.35
        top_w, bot_w = aw * 0.72, aw
        poly = [(x0 + (bot_w - top_w) / 2, y0),
                (x0 + (bot_w + top_w) / 2, y0),
                (x0 + bot_w, y0 + al), (x0, y0 + al)]
        shade(tile, lambda dd, p=poly: dd.polygon(
            [(px + SS, py + SS) for px, py in p], fill=(0, 0, 0, 120)))
        td.polygon(poly, fill=(*P["steel"], 255))
        td.line(poly[:2], fill=(*P["steel_hi"], 220), width=SS)
        td.line(poly[2:4], fill=(*P["steel_lo"], 220), width=SS)
        cxp = x0 + bot_w / 2
        cyp = y0 + al / 2
        td.rounded_rectangle([cxp - top_w * 0.28, y0 + 3 * SS,
                              cxp + top_w * 0.28, y0 + al - 3 * SS],
                             radius=SS, fill=(*P["lume"], 255))
        rotated_paste(img, tile, _at(cx, cy, BEZEL["applique_r"] * SS, deg),
                      deg)

    # panel seams + rivets on the chapter ring (item 1)
    for r_ in PANEL["seam_radii"]:
        rr = r_ * SS
        shade(img, lambda dd, rr=rr: (
            dd.arc([cx - rr, cy - rr, cx + rr, cy + rr], 0, 360,
                   fill=(0, 0, 0, 90), width=SS),
            dd.arc([cx - rr - SS, cy - rr - SS, cx + rr + SS, cy + rr + SS],
                   0, 360, fill=(255, 255, 255, 22), width=SS)))
    deg = PANEL["rivet_offset_deg"]
    while deg < 360:
        x, y = _at(cx, cy, PANEL["rivet_r"] * SS, deg)
        _rivet(img, x, y, rng)
        deg += PANEL["rivet_every_deg"]


# ------------------------------------------------------------- chapter

def indices(img):
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
            shade(tile, lambda dd: dd.rounded_rectangle(
                [x0 + SS, y0 + SS, x0 + w + SS, y0 + l + SS],
                radius=2 * SS, fill=(0, 0, 0, 110)))
            td.rounded_rectangle([x0, y0, x0 + w, y0 + l], radius=2 * SS,
                                 fill=(*P["steel"], 255))
            td.rounded_rectangle([x0, y0, x0 + w, y0 + l * 0.45],
                                 radius=2 * SS, fill=(*P["steel_hi"], 90))
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

def _mask_for(shapes):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    for kind, p in shapes:
        if kind == "disc":
            c, r = p["c"], p["r"] * SS
            d.ellipse([c[0] * SS - r, c[1] * SS - r,
                       c[0] * SS + r, c[1] * SS + r], fill=255)
        else:
            c, w, h, rad = p["c"], p["w"] * SS, p["h"] * SS, p["rad"] * SS
            d.rounded_rectangle([c[0] * SS - w / 2, c[1] * SS - h / 2,
                                 c[0] * SS + w / 2, c[1] * SS + h / 2],
                                radius=rad, fill=255)
    return m.filter(ImageFilter.GaussianBlur(6 * SS)).point(
        lambda v: 255 if v >= 128 else 0)


def _perimeter_points(shapes, inset, spacing):
    """Rivet positions sampled from the geometry itself, never traced off
    pixels — the contour and the art cannot drift apart."""
    pts = []
    for kind, p in shapes:
        if kind == "disc":
            c, r = p["c"], p["r"] - inset
            n = max(6, int(2 * math.pi * r / spacing))
            for i in range(n):
                a = 2 * math.pi * i / n
                pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
        else:
            c, w, h = p["c"], p["w"] / 2 - inset, p["h"] / 2 - inset
            per = 4 * (w + h)
            n = max(8, int(per / spacing))
            for i in range(n):
                t = per * i / n
                if t < 2 * w:
                    pts.append((c[0] - w + t, c[1] - h))
                elif t < 2 * w + 2 * h:
                    pts.append((c[0] + w, c[1] - h + (t - 2 * w)))
                elif t < 4 * w + 2 * h:
                    pts.append((c[0] + w - (t - 2 * w - 2 * h), c[1] + h))
                else:
                    pts.append((c[0] - w, c[1] + h - (t - 4 * w - 2 * h)))
    return pts


def _steel_level(sil, base_lum=0, brush_vertical=True):
    rng = random.Random(SEED ^ (0xB1 + base_lum))
    steel = Image.new(
        "RGBA", (S, S),
        tuple(min(255, v + base_lum) for v in P["steel"]) + (255,))
    sd = ImageDraw.Draw(steel)
    for i in range(0, S, SS):
        if rng.random() < 0.8:
            lum = rng.randint(-16, 16)
            col = tuple(max(0, min(255, P["steel"][k] + base_lum + lum))
                        for k in range(3))
            if brush_vertical:
                sd.line([(i, 0), (i, S)], fill=(*col, 255), width=SS)
            else:
                sd.line([(0, i), (S, i)], fill=(*col, 255), width=SS)
    light = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    for y in range(0, S, SS):
        a = int(24 - 38 * (y / S))
        if a > 0:
            ld.line([(0, y), (S, y)], fill=(255, 255, 255, a), width=SS)
        elif a < -6:
            ld.line([(0, y), (S, y)], fill=(0, 0, 0, min(40, -a)), width=SS)
    steel.alpha_composite(light)

    body = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    body.paste(steel, (0, 0), sil)
    edge = sil.filter(ImageFilter.FIND_EDGES).point(
        lambda v: 255 if v > 24 else 0)
    b = int(PLATE["bevel_px"] * SS / 2)
    lo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    lo.paste(Image.new("RGBA", (S, S), (*P["steel_lo"], 190)), (b, b), edge)
    hi = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hi.paste(Image.new("RGBA", (S, S), (*P["steel_hi"], 150)), (-b, -b), edge)
    body.alpha_composite(lo)
    body.alpha_composite(hi)
    body.putalpha(sil)
    return body


def centre_plate(img):
    rng = random.Random(SEED ^ 0xB1)
    d = ImageDraw.Draw(img)

    base_sil = _mask_for(PLATE["shapes"])
    bridge_sil = _mask_for(PLATE["bridge"])

    sh = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    sh.putalpha(base_sil.filter(ImageFilter.GaussianBlur(3 * SS)).point(
        lambda v: v * 90 // 255))
    img.alpha_composite(sh)
    img.alpha_composite(_steel_level(base_sil, 0, True))

    # the power arc's recessed channel, cut into the base (item 3)
    ch_r, ch_w = POWER["channel_r"] * SS, POWER["channel_w"] * SS
    cx, cy = CX * SS, CY * SS
    a0, a1 = POWER["start_deg"] - 90, POWER["end_deg"] - 90
    shade(img, lambda dd: dd.arc(
        [cx - ch_r, cy - ch_r, cx + ch_r, cy + ch_r], a0, a1,
        fill=(0, 0, 0, 150), width=int(ch_w)))
    shade(img, lambda dd: (
        dd.arc([cx - ch_r - ch_w / 2, cy - ch_r - ch_w / 2,
                cx + ch_r + ch_w / 2, cy + ch_r + ch_w / 2], a0, a1,
               fill=(255, 255, 255, 40), width=SS),
        dd.arc([cx - ch_r + ch_w / 2, cy - ch_r + ch_w / 2,
                cx + ch_r - ch_w / 2, cy + ch_r - ch_w / 2], a0, a1,
               fill=(0, 0, 0, 160), width=SS)))

    # bridge shadow, then the raised bridge itself (item 6)
    bs = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    bs.putalpha(bridge_sil.filter(ImageFilter.GaussianBlur(2.5 * SS)).point(
        lambda v: v * 75 // 255))
    img.alpha_composite(bs)
    img.alpha_composite(_steel_level(bridge_sil, 12, False))

    # circular graining on the hub
    hub_r = 64.0
    grain_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain_layer)
    for _ in range(240):
        r = rng.uniform(8, hub_r) * SS
        a = rng.uniform(0, 360)
        gd.arc([cx - r, cy - r, cx + r, cy + r], a, a + rng.uniform(20, 90),
               fill=(rng.choice((255, 0)),) * 3 + (rng.randint(6, 14),),
               width=SS)
    hub_mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(hub_mask).ellipse(
        [cx - hub_r * SS, cy - hub_r * SS, cx + hub_r * SS, cy + hub_r * SS],
        fill=255)
    grain_layer.putalpha(ImageChops.multiply(
        grain_layer.getchannel("A"), hub_mask))
    img.alpha_composite(grain_layer)
    shade(img, lambda dd: dd.ellipse(
        [cx - hub_r * SS, cy - hub_r * SS, cx + hub_r * SS, cy + hub_r * SS],
        outline=(0, 0, 0, 100), width=SS))

    # the light polished centre disc and ring the concept has
    cr = 44 * SS
    d.ellipse([cx - cr - 8 * SS, cy - cr - 8 * SS,
               cx + cr + 8 * SS, cy + cr + 8 * SS],
              outline=(*P["steel_hi"], 220), width=int(2.2 * SS))
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
              fill=(206, 214, 224, 255))
    shade(img, lambda dd: (
        dd.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                   outline=(0, 0, 0, 90), width=SS),
        dd.pieslice([cx - cr, cy - cr, cx + cr, cy + cr], 200, 340,
                    fill=(255, 255, 255, 40)),
        dd.pieslice([cx - cr, cy - cr, cx + cr, cy + cr], 20, 160,
                    fill=(0, 0, 0, 30))))

    # rivets along both levels (item 6)
    for shapes, inset in ((PLATE["shapes"], PLATE["rivet_inset"]),
                          (PLATE["bridge"], PLATE["rivet_inset"] - 1)):
        for x, y in _perimeter_points(shapes, inset, PLATE["rivet_spacing"]):
            xs, ys = x * SS, y * SS
            if 0 <= xs < S and 0 <= ys < S and \
                    base_sil.getpixel((int(xs), int(ys))) == 255:
                _rivet(img, xs, ys, rng)

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
        dx_, dy_ = math.cos(ang) * (r - SS), math.sin(ang) * (r - SS)
        d.line([x - dx_, y - dy_, x + dx_, y + dy_], fill=(30, 36, 44, 255),
               width=SS)

    # ---- punched openings ---------------------------------------------
    def punch(cx_, cy_, rw, rh=None, rad=None, fill=None):
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
        img.paste(Image.new("RGBA", (S, S), fill or (*P["well"], 255)),
                  (0, 0), cut)
        er = cut.filter(ImageFilter.FIND_EDGES).point(
            lambda v: 255 if v > 24 else 0)
        ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ring.paste(Image.new("RGBA", (S, S), (0, 0, 0, 150)), (0, -SS), er)
        ring.paste(Image.new("RGBA", (S, S), (*P["steel_hi"], 70)), (0, SS),
                   er)
        ring.putalpha(ImageChops.multiply(
            ring.getchannel("A"), er.filter(ImageFilter.MaxFilter(3))))
        img.alpha_composite(ring)
        gsh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        gd_ = ImageDraw.Draw(gsh)
        if rh is None:
            gd_.pieslice([x - rw * SS, y - rw * SS, x + rw * SS, y + rw * SS],
                         180, 360, fill=(0, 0, 0, 60))
        else:
            gd_.rectangle([x - rw * SS / 2, y - rh * SS / 2,
                           x + rw * SS / 2, y - rh * SS / 2 + 5 * SS],
                          fill=(0, 0, 0, 60))
        gsh.putalpha(ImageChops.multiply(gsh.getchannel("A"), cut))
        img.alpha_composite(gsh.filter(ImageFilter.GaussianBlur(SS)))
        return cut

    # sub-dial wells with riveted rims (item 7)
    for cc in (SUBDIAL["steps_c"], SUBDIAL["hr_c"]):
        punch(*cc, SUBDIAL["well_r"])
        x, y = cc[0] * SS, cc[1] * SS
        r = SUBDIAL["well_r"] * SS
        d.ellipse([x - r - 3 * SS, y - r - 3 * SS, x + r + 3 * SS,
                   y + r + 3 * SS], outline=(*P["steel_lo"], 255),
                  width=int(SS * 1.8))
        shade(img, lambda dd, x=x, y=y, r=r: dd.arc(
            [x - r - 3 * SS, y - r - 3 * SS, x + r + 3 * SS, y + r + 3 * SS],
            160, 380, fill=(255, 255, 255, 80), width=SS))
        for i in range(22):
            a = 2 * math.pi * i / 22
            _rivet(img, x + math.cos(a) * (r + 7 * SS),
                   y + math.sin(a) * (r + 7 * SS), rng, r=1.9)

    # arch moon scene with a baked starfield (item 9)
    mx, my = MOON["c"]
    aw, ah = MOON["arch_w"], MOON["arch_h"]
    arch = punch(mx, my, aw, ah, rad=ah / 2.1, fill=(6, 10, 18, 255))
    stars_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd_ = ImageDraw.Draw(stars_layer)
    for _ in range(70):
        x = rng.uniform(mx - aw / 2, mx + aw / 2) * SS
        y = rng.uniform(my - ah / 2, my + ah / 2) * SS
        rr = rng.choice((1, 1, 2)) * SS * 0.5
        sd_.ellipse([x - rr, y - rr, x + rr, y + rr],
                    fill=(255, 255, 255, rng.randint(70, 220)))
    for i in range(3):
        yb = (my + ah / 2 - 8 - i * 5) * SS
        sd_.ellipse([(mx - aw / 2 + 8 + i * 14) * SS, yb - 3 * SS,
                     (mx - aw / 2 + 42 + i * 18) * SS, yb + 3 * SS],
                    fill=(150, 160, 175, 60))
    stars_layer.putalpha(ImageChops.multiply(
        stars_layer.getchannel("A"), arch))
    img.alpha_composite(stars_layer)

    # framed readout windows (item 10)
    for cc in (WINDOWS["left_c"], WINDOWS["right_c"]):
        punch(*cc, WINDOWS["w"], WINDOWS["h"], 9, fill=(14, 22, 34, 255))
        x, y = cc[0] * SS, cc[1] * SS
        w_, h_ = WINDOWS["w"] * SS, WINDOWS["h"] * SS
        d.rounded_rectangle([x - w_ / 2 - 2 * SS, y - h_ / 2 - 2 * SS,
                             x + w_ / 2 + 2 * SS, y + h_ / 2 + 2 * SS],
                            radius=11 * SS, outline=(*P["steel_lo"], 255),
                            width=int(SS * 1.6))
        shade(img, lambda dd, x=x, y=y, w_=w_, h_=h_: dd.rounded_rectangle(
            [x - w_ / 2 - 2 * SS, y - h_ / 2 - 2 * SS,
             x + w_ / 2 + 2 * SS, y + h_ / 2 + 2 * SS],
            radius=11 * SS, outline=(255, 255, 255, 60), width=SS))

    # date: navy window, gold frame, black inner day-box (item 13)
    dx, dy = DATE["c"]
    punch(dx, dy, DATE["frame_w"], DATE["frame_h"], 12,
          fill=(16, 25, 38, 255))
    x, y = dx * SS, dy * SS
    w_, h_ = DATE["frame_w"] * SS, DATE["frame_h"] * SS
    d.rounded_rectangle([x - w_ / 2 - SS, y - h_ / 2 - SS,
                         x + w_ / 2 + SS, y + h_ / 2 + SS],
                        radius=13 * SS, outline=(*P["gold"], 235),
                        width=int(SS * 1.5))
    bw, bh = DATE["day_box_w"] * SS, DATE["day_box_h"] * SS
    d.rounded_rectangle([x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2],
                        radius=4 * SS, fill=(4, 6, 10, 255),
                        outline=(*P["gold"], 140), width=SS)

    # the wordmark's own inset navy plate with corner rivets (item 5)
    wx, wy = WORDMARK["plate_c"]
    ww, wh = WORDMARK["plate_w"], WORDMARK["plate_h"]
    punch(wx, wy, ww, wh, WORDMARK["plate_rad"], fill=(18, 28, 42, 255))
    x, y = wx * SS, wy * SS
    d.rounded_rectangle([x - ww * SS / 2 - SS, y - wh * SS / 2 - SS,
                         x + ww * SS / 2 + SS, y + wh * SS / 2 + SS],
                        radius=(WORDMARK["plate_rad"] + 1) * SS,
                        outline=(*P["steel_hi"], 160), width=SS)
    for sx_, sy_ in ((wx - ww / 2 + 8, wy - wh / 2 + 8),
                     (wx + ww / 2 - 8, wy - wh / 2 + 8),
                     (wx - ww / 2 + 8, wy + wh / 2 - 8),
                     (wx + ww / 2 - 8, wy + wh / 2 - 8)):
        _rivet(img, sx_ * SS, sy_ * SS, rng, r=2.2)


def wordmark(img):
    f1 = font(WORDMARK["meridian_px"])
    f2 = font(WORDMARK["sub_px"], bold=False)
    c = WORDMARK["meridian_c"]
    engrave(img, (c[0] * SS, c[1] * SS), "M E R I D I A N", f1,
            (*P["ink"], 255), depth=1.1)
    c2 = WORDMARK["sub_c"]
    engrave(img, (c2[0] * SS, c2[1] * SS), "C O M M O D O R E", f2,
            (*P["gold"], 255), depth=0.7)


def compose_phase12():
    img = dial_base()
    bezel(img)
    indices(img)
    centre_plate(img)
    wordmark(img)
    return img.resize((CANVAS, CANVAS), Image.LANCZOS)


# ------------------------------------------------- post-Kontext dressing

def dress_base(kontext_png, out_png):
    """Captions inside the wells, icons inside the windows, the star, the
    heart, the BATTERY legend — baked after generation so Kontext can never
    typeset. It invents letterforms."""
    img = Image.open(kontext_png).convert("RGBA")
    up = img.resize((S, S), Image.LANCZOS)
    f_lab = font(12, bold=False)
    f_tiny = font(10, bold=False)
    gold = (*P["gold"], 255)
    dim = (168, 178, 190, 255)
    d = ImageDraw.Draw(up)

    bezel_numerals_over(up)
    engrave(up, (POWER["label_c"][0] * SS, POWER["label_c"][1] * SS),
            "B A T T E R Y", f_tiny, dim, depth=0.8)

    for cc, lab in ((SUBDIAL["steps_c"], "STEPS"), (SUBDIAL["hr_c"], "BPM")):
        engrave(up, (cc[0] * SS, (cc[1] + SUBDIAL["caption_dy"]) * SS),
                lab, f_tiny, dim, depth=0.6)

    # the red heart under BPM (item 8)
    hx_, hy_ = SUBDIAL["hr_c"]
    hx_, hy_ = hx_ * SS, (hy_ + SUBDIAL["goal_dy"]) * SS
    r = 5.5 * SS
    heart = [(hx_, hy_ + r), (hx_ - r, hy_ - r * 0.2),
             (hx_ - r * 0.5, hy_ - r), (hx_, hy_ - r * 0.35),
             (hx_ + r * 0.5, hy_ - r), (hx_ + r, hy_ - r * 0.2)]
    shade(up, lambda dd: dd.polygon(
        [(x + SS, y + SS) for x, y in heart], fill=(0, 0, 0, 140)))
    d.polygon(heart, fill=(226, 64, 64, 255))

    # military caption + the bold star (item 12)
    mx, my = MILITARY["c"]
    engrave(up, (mx * SS, (my + 26) * SS), "24H", f_lab, gold, depth=0.8)
    cx, cy = mx * SS, (my + MILITARY["star_dy"]) * SS
    r = MILITARY["star_r"] * SS
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.42
        a = math.radians(i * 36 - 90)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    shade(up, lambda dd: dd.polygon(
        [(x + SS, y + SS) for x, y in pts], fill=(0, 0, 0, 130)))
    d.polygon(pts, fill=(*P["ink"], 235))
    d.line(pts + [pts[0]], fill=(90, 100, 112, 255), width=SS)

    # gold icons inside the windows (item 10)
    for cc, kind in ((WINDOWS["left_c"], "temp"),
                     (WINDOWS["right_c"], "rain")):
        ix = (cc[0] + WINDOWS["icon_dx"]) * SS
        iy = cc[1] * SS
        if kind == "temp":
            d.rounded_rectangle([ix - 1.6 * SS, iy - 7 * SS, ix + 1.6 * SS,
                                 iy + 3 * SS], radius=1.6 * SS, outline=gold,
                                width=SS)
            d.ellipse([ix - 3.4 * SS, iy + 1.5 * SS, ix + 3.4 * SS,
                       iy + 8 * SS], fill=gold)
        else:
            d.polygon([(ix, iy - 7 * SS), (ix - 4.6 * SS, iy + 2 * SS),
                       (ix + 4.6 * SS, iy + 2 * SS)], fill=gold)
            d.ellipse([ix - 4.6 * SS, iy - 1 * SS, ix + 4.6 * SS,
                       iy + 8 * SS], fill=gold)
    up.resize((CANVAS, CANVAS), Image.LANCZOS).save(out_png, optimize=True)


def bezel_numerals_over(up):
    """Redraw the minute numerals over the generated base in the concept's
    light champagne. Kontext kept re-brightening whatever the layout held;
    drawing them post-generation makes the colour a constant."""
    cx, cy = CX * SS, CY * SS
    f = font(BEZEL["numeral_px"])
    marks = [(m * 6, f"{m:02d}") for m in range(5, 60, 5)] + [(0, "12")]
    for deg, txt in marks:
        pad = 6 * SS
        w = int(f.getlength(txt)) + pad * 2
        h = BEZEL["numeral_px"] * SS + pad * 2
        tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        td.text((w / 2, h / 2 + SS), txt, font=f, fill=(0, 0, 0, 120),
                anchor="mm")
        td.text((w / 2, h / 2), txt, font=f,
                fill=(228, 210, 172, 235) if txt == "12"
                else (216, 198, 162, 220), anchor="mm")
        show = deg + (180 if 90 < deg < 270 else 0)
        rotated_paste(up, tile, _at(cx, cy, BEZEL["numeral_r"] * SS, deg),
                      show)


def bg_aod(base_png, out_png):
    """AOD base v2: SPARSE, not dimmed. A full-art dial at 18% still lights
    virtually every pixel, which fails the on-pixel-ratio burn-in gate a
    commercial release must pass (AURELIUS ran at 4% of the 15% budget). So
    ambient is black with only the orientation skeleton: the lume of the
    twelve indices, a hairline chapter circle, and the lume triangle. The
    dim hands, 24H, day and battery readouts stay live on top and the total
    stays far inside budget."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    cx, cy = CX * SS, CY * SS
    rr = CHAPTER["ring_r"] * SS
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
              outline=(70, 78, 88, 255), width=SS)
    lume = tuple(int(v * 0.55) for v in P["lume"]) + (255,)
    for h in range(12):
        deg = h * 30
        w = CHAPTER["lume_w"] * SS
        l = CHAPTER["baton_l"] * SS * 0.8
        tile = Image.new("RGBA", (int(w * 4), int(l * 1.5)), (0, 0, 0, 0))
        ImageDraw.Draw(tile).rounded_rectangle(
            [w * 1.5, l * 0.25, w * 2.5, l * 0.25 + l], radius=SS, fill=lume)
        rotated_paste(img, tile, _at(cx, cy, rr, deg), deg)
    tip = _at(cx, cy, (BEZEL["numeral_r"] - 6) * SS, 0)
    d.polygon([tip, (tip[0] - 5 * SS, tip[1] - 12 * SS),
               (tip[0] + 5 * SS, tip[1] - 12 * SS)], fill=lume)
    img.resize((CANVAS, CANVAS), Image.LANCZOS).save(out_png, optimize=True)


# ---------------------------------------------------------------- hands

def hands(out_dir):
    """Dauphine: navy lacquer inside a gold rim, gold tip segment, white
    lume core, two-stage shadow (item 11)."""
    from geometry import HANDS
    cx, cy = HANDS["c"][0] * SS, HANDS["c"][1] * SS

    def propeller(length, max_w):
        """A propeller blade, as ordered: narrow at the hub, swelling wide
        through the middle, rounded at the tip, with a short counter-blade
        behind the boss. Navy lacquer in a gold edge, wide lume spine."""
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        L = length * SS
        W = max_w * SS
        import math as _m
        def profile(tt):          # width along the blade
            # broad through the middle, tapering to a POINT at 0.86L —
            # the concept's blade — with a thin gold needle beyond it
            if tt < 0.45:
                return W * (0.35 + 0.65 * (tt / 0.45) ** 0.8)
            if tt < 0.86:
                return W * (1.0 - 0.98 * ((tt - 0.45) / 0.41) ** 1.15)
            return W * 0.02
        n = 26
        left, right = [], []
        for i in range(n + 1):
            tt = i / n
            y = cy - L * tt
            w2 = profile(tt) / 2 if tt < 0.995 else 0.5
            left.append((cx - w2, y)); right.append((cx + w2, y))
        body = left + right[::-1]
        for off, a in ((3 * SS, 60), (1.5 * SS, 90)):
            shade(img, lambda dd, off=off, a=a: dd.polygon(
                [(x + off, y + off) for x, y in body], fill=(0, 0, 0, a)))
        # counter-blade
        cb = 26 * SS
        d.polygon([(cx - W * 0.28, cy), (cx, cy + cb), (cx + W * 0.28, cy)],
                  fill=(*P["gold"], 255))
        d.polygon(body, fill=(*P["gold"], 255))
        inner = []
        for i in range(n + 1):
            tt = i / n
            y = cy - L * tt
            w2 = max(0.5, profile(tt) / 2 - 4.8 * SS)
            inner.append((cx - w2, y))
        for i in range(n, -1, -1):
            tt = i / n
            y = cy - L * tt
            w2 = max(0.5, profile(tt) / 2 - 4.8 * SS)
            inner.append((cx + w2, y))
        d.polygon(inner, fill=(38, 56, 82, 255))
        # the gold needle tip beyond the blade point
        d.line([(cx, cy - L * 0.84), (cx, cy - L * 1.06)],
               fill=(*P["gold"], 255), width=int(3 * SS))
        d.polygon([(cx, cy - L * 1.10), (cx - 2.5 * SS, cy - L * 1.04),
                   (cx + 2.5 * SS, cy - L * 1.04)], fill=(*P["gold_hi"], 255))
        # wide lume spine
        d.rounded_rectangle([cx - 4.4 * SS, cy - L * 0.80, cx + 4.4 * SS,
                             cy - L * 0.30], radius=3 * SS,
                            fill=(*P["lume"], 255))
        d.line([(cx, cy - L * 0.28), (cx, cy + cb * 0.6)],
               fill=(255, 255, 255, 55), width=SS)
        return img

    h = propeller(102, 44)
    m = propeller(148, 34)
    s_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(s_img)
    L = 182 * SS
    shade(s_img, lambda dd: dd.line(
        [(cx + 2 * SS, cy + 34 * SS), (cx + 2 * SS, cy - L)],
        fill=(0, 0, 0, 110), width=2 * SS))
    d.line([(cx, cy + 34 * SS), (cx, cy - L)], fill=(*P["gold"], 255),
           width=2 * SS)
    d.polygon([(cx, cy - L), (cx - 3 * SS, cy - L + 16 * SS),
               (cx + 3 * SS, cy - L + 16 * SS)], fill=(*P["gold_hi"], 255))
    rr = 6 * SS
    d.ellipse([cx - rr, cy + 22 * SS, cx + rr, cy + 22 * SS + 2 * rr],
              outline=(*P["gold"], 255), width=2 * SS)
    boss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(boss)
    br = 11 * SS
    bd.ellipse([cx - br - 2 * SS, cy - br - 2 * SS, cx + br + 2 * SS,
                cy + br + 2 * SS], fill=(*P["gold"], 255))
    bd.ellipse([cx - br, cy - br, cx + br, cy + br], fill=(*P["steel"], 255))
    bd.ellipse([cx - br * 0.45, cy - br * 0.7, cx + br * 0.1,
                cy - br * 0.1], fill=(255, 255, 255, 90))
    bd.ellipse([cx - br * 0.4, cy - br * 0.4, cx + br * 0.4, cy + br * 0.4],
               fill=(16, 26, 40, 255))
    for name, im in (("hour", h), ("minute", m), ("second", s_img),
                     ("boss", boss)):
        im.resize((CANVAS, CANVAS), Image.LANCZOS).save(
            out_dir / f"mp_hand_{name}.png", optimize=True)


def moon_sprite(out_dir):
    rng = random.Random(SEED ^ 0x40)
    r = MOON["disc_r"] * SS
    Simg = int(r * 2 + 8 * SS)
    img = Image.new("RGBA", (Simg, Simg), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = Simg / 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=(206, 210, 216, 255))
    for _ in range(22):
        cr = rng.uniform(0.06, 0.17) * r
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0, r * 0.8)
        x, y = c + math.cos(a) * rr, c + math.sin(a) * rr
        d.ellipse([x - cr, y - cr, x + cr, y + cr],
                  fill=(178, 183, 190, 255))
        d.arc([x - cr, y - cr, x + cr, y + cr], 120, 320,
              fill=(150, 156, 164, 255), width=SS)
    shade(img, lambda dd: dd.pieslice(
        [c - r, c - r, c + r, c + r], 110, 250, fill=(0, 0, 0, 60)))
    img.resize((Simg // SS, Simg // SS), Image.LANCZOS).save(
        out_dir / "mp_moon.png", optimize=True)
