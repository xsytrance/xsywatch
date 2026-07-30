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
    "steel_hi":  (226, 234, 242),
    "steel":     (170, 178, 188),
    "steel_lo":  (86, 96, 110),
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

VARIANT = os.environ.get("MP_VARIANT", "muted")
PALETTE = PALETTE_BOLD if VARIANT == "bold" else PALETTE_MUTED
