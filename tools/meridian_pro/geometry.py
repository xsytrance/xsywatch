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

CANVAS = 480
CX = CY = CANVAS / 2

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
}

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

# ---------------------------------------------------------------- time
MILITARY = {
    "c": (128.0, 236.0),         # "17" with "24H" beneath
    "big_px": 36,
    "star_r": 19.0,
    "star_dy": 56.0,
    "small_px": 11,
}

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
}

# ---------------------------------------------------------------- moon
MOON = {
    # a wide arch scene between the steel wings, not a porthole
    "c": (240.0, 334.0),
    "arch_w": 112.0,
    "arch_h": 64.0,
    "disc_r": 21.0,              # the moon itself, upper middle of the arch
    "disc_c": (240.0, 326.0),
}

# The two framed windows under the moon. Sunrise/sunset is impossible (no
# location source at any format version) so these carry temperature and
# precipitation chance.
WINDOWS = {
    "left_c": (187.0, 396.0),
    "right_c": (293.0, 396.0),
    "w": 88.0,
    "h": 36.0,
    "value_px": 19,
    "icon_dx": -30.0,
}

# ---------------------------------------------------------------- hands
HANDS = {
    "c": (CX, CY),
    "hour_l": 118.0,
    "minute_l": 168.0,
    "second_l": 182.0,
    "boss_r": 11.0,
}

# ---------------------------------------------------------------- plate
# The milled steel centre plate: a cruciform union of simple shapes. The
# silhouette is defined HERE, as data, so the sprite drawer and any later
# coverage gate agree about where steel is.
PLATE = {
    # (kind, params) — unioned in order
    "shapes": [
        ("disc",  dict(c=(240.0, 240.0), r=116.0)),          # hands hub
        ("rrect", dict(c=(240.0, 168.0), w=198.0, h=98.0, rad=30.0)),  # top tongue
        ("disc",  dict(c=(152.0, 322.0), r=66.0)),           # steps boss
        ("disc",  dict(c=(328.0, 322.0), r=66.0)),           # hr boss
        ("rrect", dict(c=(240.0, 368.0), w=204.0, h=100.0, rad=34.0)),  # bottom tongue
        ("rrect", dict(c=(344.0, 236.0), w=96.0, h=108.0, rad=20.0)),  # date arm
    ],
    # the raised bridge, a second steel level over the base plate
    "bridge": [
        ("disc",  dict(c=(240.0, 240.0), r=92.0)),
        ("rrect", dict(c=(240.0, 186.0), w=152.0, h=66.0, rad=22.0)),
        ("rrect", dict(c=(240.0, 306.0), w=214.0, h=64.0, rad=30.0)),
        ("rrect", dict(c=(240.0, 352.0), w=124.0, h=52.0, rad=20.0)),
    ],
    "screws": [
        (240.0, 112.0), (156.0, 172.0), (324.0, 172.0),
        (150.0, 250.0), (330.0, 250.0),
        (184.0, 412.0), (296.0, 412.0),
    ],
    "screw_r": 5.0,
    "rivet_r": 2.4,               # the little domes along every panel edge
    "rivet_inset": 7.0,
    "rivet_spacing": 15.0,
    "bevel_px": 3.0,
}

# ------------------------------------------------------------- palette
# COMMODORE navy family, sampled not invented; steel from the concept.
# Themes swap this dict wholesale in phase 7.
PALETTE = {
    "dial_hi":   (30, 42, 58),
    "dial_lo":   (12, 19, 30),
    "bezel_hi":  (24, 33, 46),
    "bezel_lo":  (10, 16, 25),
    "gold":      (214, 170, 71),
    "gold_hi":   (235, 196, 104),
    "steel_hi":  (232, 236, 240),
    "steel":     (154, 163, 173),
    "steel_lo":  (58, 66, 76),
    "well":      (12, 20, 31),
    "lume":      (201, 232, 212),
    "ink":       (226, 232, 238),
    "zone_ok":   (47, 122, 102),
    "zone_warn": (200, 154, 60),
    "zone_lim":  (184, 64, 47),
    "second":    (232, 86, 60),
}
