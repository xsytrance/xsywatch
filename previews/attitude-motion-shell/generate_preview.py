#!/usr/bin/env python3
"""ATTITUDE clean motion-preview shell — PREVIEW ONLY, NOT FORMAL EVIDENCE.

═══════════════════════════════════════════════════════════════════════════
 PREVIEW_ONLY. Not a production asset, not a release candidate, and never
 a substitute for the pullback-verified accepted spike builds.
 The accepted spike APKs and the formal device harness remain authoritative
 for all formal testing. Nothing here may be fed into that harness.
═══════════════════════════════════════════════════════════════════════════

Why this exists: the disposable spike is deliberately crude, and on the
wrist its block lettering and placeholder hands made the motion harder to
judge, not easier. This shell strips the noise so the horizon behaviour can
be seen — while changing nothing about the motion itself.

    python3 previews/attitude-motion-shell/generate_preview.py
    python3 previews/attitude-motion-shell/generate_preview.py --check

THE MOTION CONTRACT IS IMPORTED, NOT RETYPED. Clamps, gains, roll sign and
the expression text all come from the accepted spike generator by direct
import, so the two cannot drift apart. This module reads that file and
never writes to it.

No analog hands: they obstructed the aperture in the spike. Time is a real
digital readout using WFF's standard `sans-serif` family, so the glyphs are
the system's readable text rather than a hand-built alphabet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
APP = HERE / "app"
REVIEW = HERE / "review"

# The accepted spike is the single source of the motion contract.
sys.path.insert(0, str(REPO / "spikes/attitude-horizon"))
import generate_spike as gs  # noqa: E402

SIZE = gs.SIZE                      # 480
AP = dict(gs.AP)                    # identical aperture geometry
WRIST_ROLL_CLAMP = gs.WRIST_ROLL_CLAMP
WRIST_PITCH_CLAMP = gs.WRIST_PITCH_CLAMP
SAFETY_PX = gs.SAFETY_PX

BASE_PACKAGE = "com.xsytrance.attitude.preview"
VERSION_NAME = "0.0.1-preview"
VERSION_CODE = 1

PROFILES = {
    name: {"roll_deg": spec["roll_deg"], "pitch_px": spec["pitch_px"],
           "suffix": spec["suffix"],
           "label": f"ATTITUDE Preview — {name.upper()}"}
    for name, spec in gs.PROFILES.items()
}

# ---------------------------------------------------------------------
# Palette — calm, desaturated, instrument-like. No neon, no glow.
# ---------------------------------------------------------------------
FIELD = (11, 12, 13)            # matte near-black outside the aperture
RING = (30, 33, 36)             # extremely restrained concentric detail
RIM = (58, 63, 68)              # aperture rim
RIM_LIT = (92, 99, 106)

SKY = (43, 66, 88)              # deep desaturated aviation blue
SKY_HI = (55, 82, 108)
GROUND = (90, 69, 48)           # warm restrained umber/bronze
GROUND_LO = (64, 49, 34)
HORIZON = (232, 230, 226)       # crisp neutral
LADDER = (196, 200, 204)

DATUM = (214, 168, 92)          # restrained amber, fixed reference
INK = (226, 230, 234)
DIM = (120, 128, 136)

AOD_SKY = (16, 22, 29)
AOD_GROUND = (26, 21, 15)
AOD_HORIZON = (120, 126, 132)
AOD_INK = (150, 158, 166)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def field_radius() -> float:
    """Identical sizing rule to the spike: one field covers every profile."""
    return gs.field_radius()


def roll_expression(profile: str) -> str:
    """Delegated to the accepted spike — same formula, same sign."""
    return gs.roll_expression(PROFILES[profile]["roll_deg"])


def pitch_expression(profile: str, base_y: float) -> str:
    return gs.pitch_expression(PROFILES[profile]["pitch_px"], base_y)


def evaluate_roll(profile: str, wrist_deg: float) -> float:
    return gs.evaluate_roll(profile, wrist_deg)


def evaluate_pitch(profile: str, wrist_deg: float) -> float:
    return gs.evaluate_pitch(profile, wrist_deg)


# ---------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------

def _aperture(d, inset=0, **kw):
    d.rounded_rectangle(
        [AP["cx"] - AP["hw"] + inset, AP["cy"] - AP["hh"] + inset,
         AP["cx"] + AP["hw"] - inset, AP["cy"] + AP["hh"] - inset],
        radius=max(2, AP["radius"] - inset), **kw)


def make_horizon(path: Path, aod: bool = False) -> None:
    """Oversized sky/ground field. Rotated and translated beneath the plate."""
    from PIL import Image, ImageDraw
    R = field_radius()
    D = int(math.ceil(R * 2))
    if D % 2:
        D += 1
    sky, sky_hi = (AOD_SKY, AOD_SKY) if aod else (SKY, SKY_HI)
    gnd, gnd_lo = (AOD_GROUND, AOD_GROUND) if aod else (GROUND, GROUND_LO)
    line = AOD_HORIZON if aod else HORIZON

    img = Image.new("RGBA", (D, D), gnd + (255,))
    d = ImageDraw.Draw(img)
    mid = D // 2
    for y in range(mid):
        d.line([(0, y), (D, y)], fill=lerp(sky_hi, sky, y / mid) + (255,))
    for y in range(mid, D):
        d.line([(0, y), (D, y)],
               fill=lerp(gnd, gnd_lo, (y - mid) / mid) + (255,))
    d.line([(0, mid), (D, mid)], fill=line + (255,), width=2)

    if not aod:
        # sparse, thin pitch ladder — enough to read pitch, not to clutter
        for i in (1, 2, 3):
            dy = i * 30
            half = 54 - i * 10
            for sgn in (-1, 1):
                y = mid + sgn * dy
                d.line([(mid - half, y), (mid - half * 0.42, y)],
                       fill=LADDER + (255,), width=1)
                d.line([(mid + half * 0.42, y), (mid + half, y)],
                       fill=LADDER + (255,), width=1)
    img.save(path)


def _draw_datum(d):
    """Small FIXED aircraft datum. Stationary; the horizon moves under it."""
    cx, cy = AP["cx"], AP["cy"]
    d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=DATUM + (255,))
    for sgn in (-1, 1):
        d.line([(cx + sgn * 12, cy), (cx + sgn * 34, cy)],
               fill=DATUM + (255,), width=2)
        d.line([(cx + sgn * 34, cy), (cx + sgn * 34, cy + 5)],
               fill=DATUM + (255,), width=2)


def make_plate(path: Path, aod: bool = False) -> None:
    """Opaque field with a TRANSPARENT aperture, drawn over the horizon."""
    from PIL import Image, ImageDraw
    # The plate must fill the ENTIRE canvas, not an inscribed circle: the
    # oversized horizon field extends past a 240px radius at the travel
    # extremes and would otherwise leak into the corners. The round display
    # crops the corners anyway; the plate must not rely on that.
    base = (6, 7, 8) if aod else FIELD
    img = Image.new("RGBA", (SIZE, SIZE), base + (255,))
    d = ImageDraw.Draw(img)

    if not aod:
        # extremely restrained concentric detail
        for r in (232, 196):
            d.ellipse([SIZE / 2 - r, SIZE / 2 - r, SIZE / 2 + r, SIZE / 2 + r],
                      outline=RING + (255,), width=1)

    # punch the aperture
    hole = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    _aperture(ImageDraw.Draw(hole), fill=(0, 0, 0, 255))
    img.paste((0, 0, 0, 0), (0, 0), hole)

    _aperture(d, outline=(RIM if not aod else (40, 44, 48)) + (255,),
              width=2)
    if not aod:
        _aperture(d, inset=2, outline=RIM_LIT + (110,), width=1)

    _draw_datum(d)
    img.save(path)


def make_preview_icon(path: Path, profile: str) -> None:
    from PIL import Image
    make_plate(path)                      # simple, quiet, no text baked in
    with Image.open(path) as im:
        im.convert("RGB").save(path)


# ---------------------------------------------------------------------
# WFF XML — real system-font text, no custom alphabet, no analog hands
# ---------------------------------------------------------------------

def watchface_xml(profile: str) -> str:
    R = field_radius()
    D = int(math.ceil(R * 2))
    if D % 2:
        D += 1
    fx = AP["cx"] - D / 2
    fy = AP["cy"] - D / 2
    roll = roll_expression(profile)
    pitch = pitch_expression(profile, fy)
    label = profile.upper()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!-- ATTITUDE motion PREVIEW shell - profile {profile} -->
<!-- PREVIEW ONLY. Not production, not a release candidate, not formal evidence. -->
<WatchFace width="{SIZE}" height="{SIZE}">
  <Metadata key="CLOCK_TYPE" value="DIGITAL" />
  <Metadata key="PREVIEW_TIME" value="10:09:30" />
  <Scene backgroundColor="#000000">

    <PartImage name="p10_horizon" x="{fx:.0f}" y="{fy:.0f}" width="{D}" height="{D}" alpha="255" pivotX="0.5" pivotY="0.5">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Variant mode="AMBIENT" target="angle" value="0" />
      <Variant mode="AMBIENT" target="y" value="{fy:.0f}" />
      <Transform target="angle" value="{roll}" />
      <Transform target="y" value="{pitch}" />
      <Image resource="horizon" />
    </PartImage>

    <PartImage name="p11_horizon_aod" x="{fx:.0f}" y="{fy:.0f}" width="{D}" height="{D}" alpha="0" pivotX="0.5" pivotY="0.5">
      <Variant mode="AMBIENT" target="alpha" value="255" />
      <Variant mode="AMBIENT" target="angle" value="0" />
      <Variant mode="AMBIENT" target="y" value="{fy:.0f}" />
      <Transform target="angle" value="{roll}" />
      <Transform target="y" value="{pitch}" />
      <Image resource="horizon_aod" />
    </PartImage>

    <PartImage name="p20_plate" x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Image resource="plate" />
    </PartImage>

    <PartImage name="p21_plate_aod" x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="0">
      <Variant mode="AMBIENT" target="alpha" value="255" />
      <Image resource="plate_aod" />
    </PartImage>

    <PartText name="p30_time" x="90" y="96" width="300" height="64" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="190" />
      <Text align="CENTER">
        <Font family="sans-serif" size="46" weight="NORMAL" color="#E2E6EA">
          <Template>%s:%s<Parameter expression="[HOUR_0_23]" /><Parameter expression="[MINUTE_Z]" /></Template>
        </Font>
      </Text>
    </PartText>

    <PartText name="p31_title" x="150" y="158" width="180" height="26" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Text align="CENTER">
        <Font family="sans-serif" size="14" weight="NORMAL" color="#6C757E">ATTITUDE</Font>
      </Text>
    </PartText>

    <PartText name="p40_profile" x="120" y="352" width="240" height="34" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="200" />
      <Text align="CENTER">
        <Font family="sans-serif" size="22" weight="NORMAL" color="#D6A85C">{label}</Font>
      </Text>
    </PartText>

    <PartText name="p41_disclaimer" x="120" y="386" width="240" height="26" alpha="255">
      <Variant mode="AMBIENT" target="alpha" value="0" />
      <Text align="CENTER">
        <Font family="sans-serif" size="13" weight="NORMAL" color="#78828B">MOTION PREVIEW</Font>
      </Text>
    </PartText>

  </Scene>
</WatchFace>
"""


WATCH_FACE_INFO = """<?xml version="1.0" encoding="utf-8"?>
<!-- ATTITUDE motion PREVIEW shell - not for retail -->
<WatchFaceInfo>
    <Preview value="@drawable/preview" />
    <Category value="CATEGORY_EMPTY" />
    <AvailableInRetail value="false" />
    <MultipleInstancesAllowed value="false" />
    <Editable value="false" />
</WatchFaceInfo>
"""

INTEGERS = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <integer name="wff_version">4</integer>
</resources>
"""


# One shared manifest; the per-flavour name is a STRING RESOURCE, which is
# the idiomatic way to vary a label across product flavours. Gradle requires
# a main manifest to exist, so flavour-only manifests do not work here.
MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<!-- ATTITUDE motion PREVIEW shell. PREVIEW ONLY. NO PERMISSIONS DECLARED. -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-feature
        android:name="android.hardware.type.watch"
        android:required="true" />

    <application
        android:label="@string/face_label"
        android:icon="@drawable/preview"
        android:hasCode="false">

        <property
            android:name="com.google.wear.watchface.format.version"
            android:value="@integer/wff_version" />

        <meta-data
            android:name="com.google.android.wearable.standalone"
            android:value="true" />
    </application>
</manifest>
"""


def strings_xml(profile: str) -> str:
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<resources>\n'
            f'    <string name="face_label">'
            f'{PROFILES[profile]["label"]}</string>\n'
            f'</resources>\n')


def build_gradle() -> str:
    flavours = "\n".join(
        f"""        create("{n}") {{
            dimension = "profile"
            applicationIdSuffix = "{p['suffix']}"
            versionNameSuffix = "-{n}"
        }}""" for n, p in sorted(PROFILES.items()))
    return f"""// ATTITUDE motion PREVIEW shell. PREVIEW ONLY.
// Debug builds only. No release block, no bundle block, and deliberately
// no signing material of any kind.
plugins {{ id("com.android.application") }}

android {{
    namespace = "{BASE_PACKAGE}"
    compileSdk = 36

    defaultConfig {{
        applicationId = "{BASE_PACKAGE}"
        minSdk = 33
        targetSdk = 36
        versionCode = {VERSION_CODE}
        versionName = "{VERSION_NAME}"
    }}

    flavorDimensions += "profile"
    productFlavors {{
{flavours}
    }}

    buildTypes {{
        debug {{ isMinifyEnabled = false }}
    }}
}}
"""


SETTINGS_GRADLE = """// ATTITUDE motion PREVIEW shell
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}
rootProject.name = "attitude-motion-preview"
include(":app")
"""

ROOT_GRADLE = """// ATTITUDE motion PREVIEW shell
plugins { id("com.android.application") version "9.2.1" apply false }
"""


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def generate() -> dict:
    main_res = APP / "src/main/res"
    (main_res / "drawable-nodpi").mkdir(parents=True, exist_ok=True)
    (main_res / "values").mkdir(parents=True, exist_ok=True)
    (APP / "src/main").mkdir(parents=True, exist_ok=True)

    make_horizon(main_res / "drawable-nodpi/horizon.png", aod=False)
    make_horizon(main_res / "drawable-nodpi/horizon_aod.png", aod=True)
    make_plate(main_res / "drawable-nodpi/plate.png", aod=False)
    make_plate(main_res / "drawable-nodpi/plate_aod.png", aod=True)
    (main_res / "values/integers.xml").write_text(INTEGERS, encoding="utf-8")
    (APP / "src/main/AndroidManifest.xml").write_text(MANIFEST,
                                                      encoding="utf-8")

    for profile in sorted(PROFILES):
        fres = APP / "src" / profile / "res"
        (fres / "raw").mkdir(parents=True, exist_ok=True)
        (fres / "xml").mkdir(parents=True, exist_ok=True)
        (fres / "drawable").mkdir(parents=True, exist_ok=True)
        (APP / "src" / profile).mkdir(parents=True, exist_ok=True)
        make_preview_icon(fres / "drawable/preview.png", profile)
        (fres / "raw/watchface.xml").write_text(watchface_xml(profile),
                                                encoding="utf-8")
        (fres / "xml/watch_face_info.xml").write_text(WATCH_FACE_INFO,
                                                      encoding="utf-8")
        (fres / "values").mkdir(parents=True, exist_ok=True)
        (fres / "values/strings.xml").write_text(strings_xml(profile),
                                                 encoding="utf-8")

    (APP / "build.gradle.kts").write_text(build_gradle(), encoding="utf-8")
    (HERE / "settings.gradle.kts").write_text(SETTINGS_GRADLE,
                                              encoding="utf-8")
    (HERE / "build.gradle.kts").write_text(ROOT_GRADLE, encoding="utf-8")

    R = field_radius()
    man = {
        "schema": "xsywatch.attitude-motion-preview/1",
        "PREVIEW_ONLY": True,
        "FORMAL_EVIDENCE_ALLOWED": False,
        "PRODUCTION_ASSET": False,
        "RELEASE_CANDIDATE": False,
        "OWNER_PIXEL_APPROVED": False,
        "authority_note": (
            "The accepted spike APKs and the formal device harness remain "
            "authoritative for all formal testing. These preview packages "
            "must never be fed into that harness as though they were "
            "validated spike builds."),
        "disclosure_note": (
            "Subjective impressions formed from this preview must be "
            "disclosed before any later formal owner observations, exactly "
            "as the phone-mediated spike preview was."),
        "resigning_note": (
            "Phone-mediated installers may repackage or re-sign. These "
            "preview packages are never a substitute for pullback-verified "
            "accepted spike builds."),
        "base_package": BASE_PACKAGE,
        "version_name": VERSION_NAME,
        "version_code": VERSION_CODE,
        "analog_hands": False,
        "custom_glyph_alphabet": False,
        "text_method": ("WFF standard <Font family=\"sans-serif\"> — real "
                        "system text, not a hand-built alphabet"),
        "aperture": AP,
        "aperture_matches_spike": AP == dict(gs.AP),
        "field_radius_px": round(R, 2),
        "motion_contract_source": (
            "imported from spikes/attitude-horizon/generate_spike.py; "
            "clamps, gains, roll sign and expression text are the same "
            "code, not a retyped copy"),
        "wrist_roll_clamp_deg": WRIST_ROLL_CLAMP,
        "wrist_pitch_clamp_deg": WRIST_PITCH_CLAMP,
        "profiles": {
            n: {
                "application_id": BASE_PACKAGE + p["suffix"],
                "label": p["label"],
                "display_roll_max_deg": p["roll_deg"],
                "display_pitch_max_px": p["pitch_px"],
                "roll_expression": roll_expression(n),
                "coverage_margin_px": round(
                    gs.coverage_margin(R, p["pitch_px"]), 2),
            } for n, p in sorted(PROFILES.items())
        },
        "generated_files": {},
    }
    for p in sorted(APP.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(HERE)
        if "build" in rel.parts or "__pycache__" in rel.parts:
            continue
        man["generated_files"][str(rel)] = sha256(p)
    return man


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    out = HERE / "PREVIEW_MANIFEST.json"
    before = json.loads(out.read_text(encoding="utf-8")) if out.exists() \
        else None
    man = generate()
    text = json.dumps(man, indent=2, sort_keys=True) + "\n"

    if args.check:
        if before is None:
            print("ERROR no committed PREVIEW_MANIFEST.json", file=sys.stderr)
            return 1
        if json.loads(text) != before:
            print("ERROR preview generation is not deterministic, or the "
                  "committed manifest is stale", file=sys.stderr)
            return 1
        print("OK: preview generation is deterministic and matches")
        return 0

    out.write_text(text, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO)}")
    for n, p in man["profiles"].items():
        print(f"  {n:10s} roll ±{p['display_roll_max_deg']:>4}°  "
              f"pitch ±{p['display_pitch_max_px']:>4}px  "
              f"margin {p['coverage_margin_px']:>5}px  "
              f"{p['application_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
