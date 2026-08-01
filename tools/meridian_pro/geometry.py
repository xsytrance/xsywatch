"""MERIDIAN PRO — the single source of truth for every coordinate.

Every drift bug this project has had came from two copies of a number: the
weather clip that drifted from its overlay, the date that was centred on the
wrong point because the text copied the base face instead of measuring the
hole. So this module is the only place a centre, radius or box is written.
The sprite drawers, the XML emitter, the centring gate and the renderer all
import it; none of them restate it.

Everything is expressed on the 480x480 canvas of the 44 mm Watch 7. The
40 mm (432) build scales uniformly by 0.9 — vectors natively, sprites by
resize — which is why nothing here is allowed to be resolution-dependent
except through CANVAS.

Layout follows the owner's concept sheet (previews/MERIDIAN_PRO_CONCEPT.png):
a minute-numeral bezel, applied indices inside it, a milled steel centre
plate carrying the battery arc up top, two ringed sub-dials low left and
right, military time left, a three-field date right, and a moon well with
two framed readout windows at the bottom.
"""

from __future__ import annotations

import os

CANVAS = 480
CX = CY = CANVAS / 2

# MP_VARIANT selects the palette and, for "baron", a sibling product:
# muted (default) | bold — the two MERIDIAN PRO temperaments;
# baron — MERIDIAN BARON, the warbird colourway in its own face dir.
VARIANT = os.environ.get("MP_VARIANT", "muted")

# ---------------------------------------------------------------- bezel
# The rotating-bezel look: a navy band with engraved minute numerals every
# five, minor ticks between, and the lume triangle at zero.
BEZEL = {
    "outer_r": 240.0,
    "inner_r": 203.0,
    "numeral_r": 221.0,          # centreline the 05..55 sit on
    "numeral_px": 27,
    "tick_outer_r": 238.0,
    "tick_inner_r": 232.0,
    "tick_major_inner_r": 229.0,
    # applied trapezoid indices BETWEEN the numerals (concept item 1)
    "applique_r": 221.0,
    "applique_w": 13.0,          # tangential width
    "applique_l": 22.0,          # radial length
}

# the navy chapter ring between bezel and dial carries aircraft panel work
PANEL = {
    "seam_radii": (197.0, 183.0),
    "rivet_r": 190.0,
    "rivet_every_deg": 15.0,
    "rivet_offset_deg": 7.5,
}

# ------------------------------------------------------------- chapter
# Applied metal indices with lume, on the dial just inside the bezel.
CHAPTER = {
    "ring_r": 192.0,             # centreline of the batons
    "baton_l": 24.0,             # radial length
    "baton_w": 9.0,
    "lume_w": 4.0,
    "twelve_gap": 5.0,           # the 12 index is a double baton
}

# ----------------------------------------------------------- power arc
# The battery zone arc across the top of the plate. E-to-F reading, red
# reserve at the LEFT end, sweeping clockwise to full green at the right.
POWER = {
    "r": 168.0,
    "start_deg": -62.0,          # degrees from 12 o'clock, cw positive
    "end_deg": 62.0,
    "track_w": 11.0,
    "sweep_w": 7.0,
    "readout_c": (240.0, 121.0), # the % number
    "readout_px": 34,
    "bolt_c": (207.0, 121.0),    # charging bolt, left of the number
    "bolt_h": 26.0,
    "label_c": (240.0, 144.0),   # BATTERY legend
    # the recessed channel the arc lives in, baked into the layout
    "channel_r": 168.0,
    "channel_w": 22.0,
    # printf template for the readout; None housing = number sits open
    "fmt": "%d%%",
    "housing": None,
}
if VARIANT == "baron":
    # the readout lives INSIDE a gauge pod (owner: "recessed inside
    # something"), and loses its % sign
    POWER.update(
        fmt="%d",
        # sized for the RENDERED opening, not the geometric one — Kontext
        # thickens the window rims by ~4 px top and bottom (it widens
        # everything it is given), so the content fits 112..146
        # measured layout: glyphs 115.5-134.5 + halo, label 138.5-145.5,
        # 2.5 px apart, ~3 px clear of both rendered bevels
        readout_c=(240.0, 125.0),
        readout_px=26,
        bolt_c=(209.0, 125.0),
        bolt_h=20.0,
        label_c=(240.0, 142.0),
        label_px=9,
        # the gauge window punched into the turret; w/h/rad are the
        # interior opening itself
        housing=dict(c=(240.0, 130.0), w=98.0, h=40.0, rad=20.0),
    )

# ------------------------------------------------------------ wordmark
WORDMARK = {
    # MERIDIAN sits on its own inset navy plate with corner screws
    "plate_c": (240.0, 181.0),
    "plate_w": 168.0,
    "plate_h": 54.0,
    "plate_rad": 12.0,
    "meridian_c": (240.0, 173.0),
    "meridian_px": 24,
    "sub_c": (240.0, 194.0),
    "sub_px": 10,
}

# ------------------------------------------------------------ subdials
# Two ringed instruments, low left and right, per the AN grammar. Their
# zone rings are PartDraw arcs at runtime; only the well and bezel of each
# is baked into the plate.
SUBDIAL = {
    "steps_c": (152.0, 322.0),
    "hr_c": (328.0, 322.0),
    "well_r": 52.0,              # recess punched through the plate
    "ring_r": 42.0,
    "ring_w": 11.0,              # thick, inner-edge, like the concept
    "value_px": 34,
    "value_dy": -10.0,           # number rides high; caption + goal below
    "caption_dy": 16.0,
    "goal_dy": 30.0,
    "label_px": 10,
}
if VARIANT == "baron":
    # smaller numerals, tighter rings: the instruments sit IN their wells
    # instead of reading as overlays (owner's call, 2026-07-30)
    SUBDIAL.update(value_px=25, value_dy=-8.0, ring_r=39.0, ring_w=9.0)

# ---------------------------------------------------------------- time
MILITARY = {
    "c": (128.0, 236.0),         # "17" with "24H" beneath
    "big_px": 36,
    "star_r": 19.0,              # 0 = no star (baron: it crowded the
    "star_dy": 56.0,             # steps dial; owner cut it 2026-07-30)
    "small_px": 11,
}
if VARIANT == "baron":
    MILITARY.update(star_r=0.0)

DATE = {
    # three-field WED / 27 / MAY; the day gets its own black inset box
    "c": (344.0, 236.0),
    "frame_w": 68.0,
    "frame_h": 82.0,
    "day_box_w": 52.0,
    "day_box_h": 38.0,
    "dow_px": 15,
    "day_px": 30,
    "mon_px": 15,
    "dow_dy": -36.0,             # top of the dow text box, from centre
    "mon_dy": 20.0,              # top of the month text box
}
if VARIANT == "baron":
    # a taller frame and spread fields: WED and MAY get air from the day
    # box (the Eye of Thundera's note, owner agreed 2026-07-30)
    DATE.update(frame_h=90.0, dow_px=14, mon_px=14,
                dow_dy=-41.0, mon_dy=21.0)

# ---------------------------------------------------------------- moon
MOON = {
    # A contained astronomical aperture.  The prototype's 112 px opening
    # physically cut into both sub-dials and read as a black rectangle.
    "c": (240.0, 347.0),
    "arch_w": 82.0,
    "arch_h": 54.0,
    "disc_r": 18.0,
    "disc_c": (240.0, 341.0),
}

# The two framed windows under the moon. Sunrise/sunset is impossible (no
# location source at any format version) so these carry temperature and
# precipitation chance.
WINDOWS = {
    "left_c": (194.0, 407.0),
    "right_c": (286.0, 407.0),
    "w": 76.0,
    "h": 32.0,
    "value_px": 17,
    "icon_dx": -25.0,
}

# ---------------------------------------------------------------- hands
HANDS = {
    "c": (CX, CY),
    "hour_l": 118.0,
    "minute_l": 168.0,
    "second_l": 182.0,
    "boss_r": 11.0,
    # propeller blade (length, max width) and the counter-blade length.
    # PRO's sizes are the post-wrist-test compromise (blades were masking
    # the 06:35 complications); BARON reverses that call on purpose — the
    # propellers ARE the face, as ordered.
    "hour_blade": (94.0, 36.0),
    "minute_blade": (140.0, 28.0),
    "counter_l": 26.0,
}
if VARIANT == "baron":
    # turboprop family (tools/propeller.py): LONG slender blades per the
    # owner's reference — not the stubby paddle, his call 2026-07-30
    HANDS.update(hour_blade=(122.0, 31.0), minute_blade=(178.0, 25.0),
                 counter_l=30.0, boss_r=13.0,
                 blade_style="turboprop", lume_w=3.2)

# ---------------------------------------------------------------- plate
# The milled steel centre plate: a cruciform union of simple shapes. The
# silhouette is defined HERE, as data, so the sprite drawer and any later
# coverage gate agree about where steel is.
PLATE = {
    # (kind, params) — unioned in order
    "shapes": [
        ("disc",  dict(c=(240.0, 240.0), r=112.0)),
        ("rrect", dict(c=(240.0, 168.0), w=188.0, h=90.0, rad=34.0)),
        ("disc",  dict(c=(152.0, 322.0), r=62.0)),
        ("disc",  dict(c=(328.0, 322.0), r=62.0)),
        ("rrect", dict(c=(240.0, 378.0), w=180.0, h=92.0, rad=36.0)),
        ("rrect", dict(c=(344.0, 236.0), w=88.0, h=104.0, rad=22.0)),
    ],
    # the raised bridge, a second steel level over the base plate
    "bridge": [
        ("disc",  dict(c=(240.0, 240.0), r=78.0)),
        ("rrect", dict(c=(240.0, 188.0), w=154.0, h=56.0, rad=24.0)),
        ("rrect", dict(c=(240.0, 282.0), w=176.0, h=50.0, rad=24.0)),
    ],
    "screws": [
        (240.0, 112.0), (156.0, 172.0), (324.0, 172.0),
        (150.0, 250.0), (330.0, 250.0),
        (184.0, 412.0), (296.0, 412.0),
    ],
    "screw_r": 5.0,
    "rivet_r": 2.4,               # the little domes along every panel edge
    "rivet_inset": 7.0,
    "rivet_spacing": 24.0,
    "bevel_px": 3.0,
}
if VARIANT == "baron":
    # the plate rises into a turret that carries the battery gauge — the
    # recess is cut into plate steel, nothing applied, nothing popping
    # over the top edge (owner's call, 2026-07-30)
    PLATE["shapes"] = PLATE["shapes"] + [
        ("rrect", dict(c=(240.0, 140.0), w=140.0, h=68.0, rad=30.0))]
    # the top-centre screw would sit inside the gauge window; flank it
    PLATE["screws"] = [(181.0, 130.0), (299.0, 130.0)] + \
        [s for s in PLATE["screws"] if s != (240.0, 112.0)]

# ------------------------------------------------------------- palette
# COMMODORE navy family, sampled not invented; steel from the concept.
# Themes swap this dict wholesale in phase 7.
PALETTE_BOLD = {
    # RE-SAMPLED FROM THE CONCEPT SHEET 2026-07-29 after the owner's call:
    # the build had drifted dark-and-gold; the concept is brighter
    # steel-blue. Navy anchors measured off the hero dial itself.
    "dial_hi":   (48, 72, 100),
    "dial_lo":   (16, 28, 44),
    "bezel_hi":  (59, 81, 105),
    "bezel_lo":  (26, 40, 58),
    "gold":      (222, 178, 105),
    "gold_hi":   (240, 200, 124),
    # Slate titanium keeps the dial mechanical without becoming a bright
    # slab behind every readout. Highlights remain bright only on bevels.
    "steel_hi":  (202, 216, 226),
    "steel":     (112, 126, 140),
    "steel_lo":  (48, 60, 74),
    "well":      (14, 24, 38),
    "lume":      (208, 232, 214),
    "ink":       (236, 241, 246),
    "zone_ok":   (54, 180, 116),
    "zone_warn": (238, 178, 64),
    "zone_lim":  (226, 84, 66),
    "second":    (236, 92, 70),
}

PALETTE_MUTED = {
    # The concept's own temperament: softer saturation, dustier navy,
    # gentler gold, matte zones. The owner: "the concept was a bit more
    # muted." Bold stays available as PALETTE_BOLD (MP_VARIANT=bold).
    "dial_hi":   (46, 68, 94),
    "dial_lo":   (34, 52, 74),
    "bezel_hi":  (64, 86, 110),
    "bezel_lo":  (46, 64, 86),
    "gold":      (196, 164, 116),
    "gold_hi":   (224, 190, 130),
    "steel_hi":  (214, 222, 230),
    "steel":     (158, 168, 179),
    "steel_lo":  (84, 94, 108),
    "well":      (22, 34, 50),
    "lume":      (196, 220, 202),
    "ink":       (224, 230, 237),
    "zone_ok":   (74, 160, 112),
    "zone_warn": (216, 168, 84),
    "zone_lim":  (206, 92, 78),
    "second":    (224, 96, 76),
}

PALETTE_BARON = {
    # MERIDIAN BARON — the warbird: crimson lacquered aircraft skin where
    # PRO has navy, black anodized bezel, polished silver plates, the gold
    # kept. Red/black/silver/gold, as ordered.
    "dial_hi":   (112, 26, 28),
    "dial_lo":   (62, 14, 16),
    "bezel_hi":  (52, 52, 58),
    "bezel_lo":  (20, 20, 24),
    "gold":      (214, 170, 98),
    "gold_hi":   (242, 202, 126),
    "steel_hi":  (236, 240, 244),
    "steel":     (172, 178, 186),
    "steel_lo":  (94, 100, 110),
    "well":      (18, 13, 13),
    "lume":      (238, 226, 198),
    "ink":       (242, 239, 234),
    "zone_ok":   (86, 168, 106),
    "zone_warn": (224, 172, 78),
    "zone_lim":  (228, 66, 54),
    "second":    (230, 72, 58),
    # blade lacquer and boss heart; PRO reads its navy defaults via
    # P.get() so only BARON needs these keys
    "hand_fill": (24, 18, 18),
    "boss_dark": (32, 22, 22),
    # the inset window/wordmark plates: black lacquer, not PRO's navy
    "inset":     (16, 12, 12),
}

PALETTE = {"bold": PALETTE_BOLD,
           "baron": PALETTE_BARON}.get(VARIANT, PALETTE_MUTED)

# ------------------------------------------------------------- identity
# Everything brand-shaped keys off this dict so build.py and
# kontext_pass.py never restate a name or a path.
IDENT = {
    "baron": dict(face_dir="meridian-baron", sub="BARON",
                  app_id="com.xsytrance.meridianbaron.dev",
                  label="MERIDIAN BARON", project="MeridianBaron",
                  kontext_base="BARON4-kontext.png"),
}.get(VARIANT, dict(face_dir="meridian-pro", sub="COMMODORE",
                    app_id="com.xsytrance.meridianpro.dev",
                    label="MERIDIAN PRO", project="MeridianPro",
                    kontext_base="PRO3-kontext.png"))
