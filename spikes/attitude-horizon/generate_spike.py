#!/usr/bin/env python3
"""DISPOSABLE Watch7 spike: reactive-horizon interaction test. NOT PRODUCT CODE.

═══════════════════════════════════════════════════════════════════════════
 THIS IS A THROWAWAY ENGINEERING EXPERIMENT.
 Nothing here may become production ATTITUDE code or artwork.
 The visuals are deliberately crude so no pixel can be mistaken for product.
═══════════════════════════════════════════════════════════════════════════

Its only purpose is to answer questions that cannot be answered offline:

  - does WFF expose accelerometer angles stable enough that a still wrist
    yields a still horizon, or does it jitter?
  - do simultaneous rotation and vertical translation compose correctly
    on-device?
  - is the response direction intuitive?
  - does the proposed gain feel premium or twitchy?
  - does AOD truly freeze neutral?
  - does a letterbox aperture stay covered at every reachable state?

    python3 spikes/attitude-horizon/generate_spike.py
    python3 spikes/attitude-horizon/generate_spike.py --check

Deliberately spike-LOCAL. It does not import or modify `engine/wffgen`,
because a disposable experiment must not put pressure on the shared engine.
The duplication is the point: this code is meant to be deleted.

Occlusion, not masking: WFF has no mask primitive for a PartImage, so the
horizon field is drawn first and a plate with a TRANSPARENT APERTURE is
drawn over it. Everything outside the aperture is opaque plate. That is why
the horizon field must be oversized — at the travel extremes the hole must
still be entirely covered.
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

SIZE = 480

# Aperture: SEXTANT-LIKE, not SEXTANT. Same family of geometry so the
# interaction question is answered for the provisional direction, but no
# product art, palette, typography or hands.
AP = {"cx": 240, "cy": 252, "hw": 156, "hh": 74, "radius": 42}

# Input clamps are shared by every profile.
WRIST_ROLL_CLAMP = 45.0
WRIST_PITCH_CLAMP = 40.0

SAFETY_PX = 18.0

PROFILES = {
    "damped":    {"roll_deg": 14.0, "pitch_px": 14.0, "suffix": ".damped"},
    "proposed":  {"roll_deg": 22.0, "pitch_px": 26.0, "suffix": ".proposed"},
    "assertive": {"roll_deg": 30.0, "pitch_px": 34.0, "suffix": ".assertive"},
}

BASE_PACKAGE = "com.xsytrance.attitude.spike"
LABEL = "ATTITUDE Horizon Spike"
VERSION_NAME = "0.0.1-spike"
VERSION_CODE = 1

# Deliberately drab: greyscale plus one muted amber. No brand palette.
PLATE = (30, 31, 33)
PLATE_EDGE = (18, 19, 20)
SKY = (104, 108, 112)
SKY_HI = (126, 130, 134)
GROUND = (128, 96, 44)
GROUND_LO = (96, 71, 32)
INK = (232, 232, 232)
DIM = (140, 142, 145)
AMBER = (198, 148, 62)


def conservative_bound() -> float:
    """Bounding-box half-diagonal of the aperture — the conservative figure
    the coverage proof uses, named as in the studio audit patch."""
    return math.hypot(AP["hw"], AP["hh"])


def required_field_radius(pitch_px: float) -> float:
    return conservative_bound() + pitch_px + SAFETY_PX


def coverage_margin(field_r: float, pitch_px: float) -> float:
    return field_r - (conservative_bound() + pitch_px)


def field_radius() -> float:
    """One shared field, sized for the MOST aggressive profile so all three
    are covered by the same resource."""
    return max(required_field_radius(p["pitch_px"]) for p in PROFILES.values())


# ---------------------------------------------------------------------
# Expressions — spike-local, mirroring the shape of the engine's helpers
# without importing them.
# ---------------------------------------------------------------------

def num(v: float) -> str:
    s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def roll_expression(roll_deg: float) -> str:
    """Displayed roll. NEGATIVE gain: when the wrist rolls one way the
    horizon rotates the other, so it reads as staying level against
    gravity. Whether that is what actually feels intuitive on the wrist is
    one of the questions the spike exists to answer.
    """
    return (f"-{num(roll_deg)} * clamp([ACCELEROMETER_ANGLE_X], "
            f"-{num(WRIST_ROLL_CLAMP)}, {num(WRIST_ROLL_CLAMP)}) "
            f"/ {num(WRIST_ROLL_CLAMP)}")


def pitch_expression(pitch_px: float, base_y: float) -> str:
    return (f"{num(base_y)} + {num(pitch_px)} * "
            f"clamp([ACCELEROMETER_ANGLE_Y], -{num(WRIST_PITCH_CLAMP)}, "
            f"{num(WRIST_PITCH_CLAMP)}) / {num(WRIST_PITCH_CLAMP)}")


def evaluate_roll(profile: str, wrist_deg: float) -> float:
    """Python mirror of roll_expression, for offline gates."""
    g = PROFILES[profile]["roll_deg"]
    w = max(-WRIST_ROLL_CLAMP, min(WRIST_ROLL_CLAMP, wrist_deg))
    return -g * w / WRIST_ROLL_CLAMP


def evaluate_pitch(profile: str, wrist_deg: float) -> float:
    g = PROFILES[profile]["pitch_px"]
    w = max(-WRIST_PITCH_CLAMP, min(WRIST_PITCH_CLAMP, wrist_deg))
    return g * w / WRIST_PITCH_CLAMP


# ---------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------

def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def make_horizon(path: Path) -> None:
    from PIL import Image, ImageDraw
    R = field_radius()
    D = int(math.ceil(R * 2))
    if D % 2:
        D += 1
    img = Image.new("RGBA", (D, D), GROUND + (255,))
    d = ImageDraw.Draw(img)
    mid = D // 2
    for y in range(mid):
        d.line([(0, y), (D, y)], fill=lerp(SKY_HI, SKY, y / mid) + (255,))
    for y in range(mid, D):
        d.line([(0, y), (D, y)],
               fill=lerp(GROUND, GROUND_LO, (y - mid) / mid) + (255,))
    d.line([(0, mid), (D, mid)], fill=INK + (255,), width=3)
    # crude pitch ladder
    for i in range(1, 8):
        dy = i * 24
        half = 70 - i * 6
        for sgn in (-1, 1):
            y = mid + sgn * dy
            if 0 < y < D:
                d.line([(mid - half, y), (mid - half * 0.35, y)],
                       fill=INK + (255,), width=2)
                d.line([(mid + half * 0.35, y), (mid + half, y)],
                       fill=INK + (255,), width=2)
    img.save(path)


def make_plate(path: Path, profile: str) -> None:
    """Opaque plate with a TRANSPARENT aperture. Drawn over the horizon."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, SIZE - 2, SIZE - 2], fill=PLATE + (255,))
    d.ellipse([2, 2, SIZE - 2, SIZE - 2], outline=PLATE_EDGE + (255,), width=6)

    # punch the aperture out
    hole = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(hole).rounded_rectangle(
        [AP["cx"] - AP["hw"], AP["cy"] - AP["hh"],
         AP["cx"] + AP["hw"], AP["cy"] + AP["hh"]],
        radius=AP["radius"], fill=(0, 0, 0, 255))
    img.paste((0, 0, 0, 0), (0, 0), hole)

    # aperture rim
    d.rounded_rectangle(
        [AP["cx"] - AP["hw"], AP["cy"] - AP["hh"],
         AP["cx"] + AP["hw"], AP["cy"] + AP["hh"]],
        radius=AP["radius"], outline=DIM + (255,), width=3)

    # fixed neutral index — opaque, so it sits over the moving horizon
    y = AP["cy"]
    d.rectangle([AP["cx"] - 4, y - 4, AP["cx"] + 4, y + 4],
                fill=AMBER + (255,))
    for sgn in (-1, 1):
        d.line([(AP["cx"] + sgn * 20, y), (AP["cx"] + sgn * 62, y)],
               fill=AMBER + (255,), width=3)

    # minimal reference ticks at 12/3/6/9
    for a_deg in (0, 90, 180, 270):
        a = math.radians(a_deg - 90)
        r0, r1 = 214, 228
        d.line([SIZE / 2 + r0 * math.cos(a), SIZE / 2 + r0 * math.sin(a),
                SIZE / 2 + r1 * math.cos(a), SIZE / 2 + r1 * math.sin(a)],
               fill=DIM + (255,), width=4)

    _blocky(d, SIZE / 2, 108, "SPIKE", 20, AMBER)
    _blocky(d, SIZE / 2, 380, profile.upper(), 15, DIM)
    _blocky(d, SIZE / 2, 404, "NOT PRODUCT", 10, DIM)
    img.save(path)


def _blocky(d, cx, cy, s, h, col):
    """Crude block lettering. Deliberately not the studio alphabet: the
    spike must not carry product typography."""
    w = h * 0.6
    gap = w * 0.42
    total = len(s) * w + (len(s) - 1) * gap
    x = cx - total / 2
    seg = {
        "A": "01111111", "C": "01100011", "E": "01100111", "F": "01100110",
        "I": "00001100", "K": "01101101", "M": "01110110", "N": "01110101",
        "O": "01111011", "P": "01100111", "R": "01101111", "S": "01001111",
        "T": "00001110", "U": "01111001", "D": "01111100", "SPACE": "0",
    }
    for ch in s:
        if ch == " ":
            x += w + gap
            continue
        bits = seg.get(ch, "01111111")
        # frame + a couple of bars: legible enough to identify, ugly enough
        # that nobody would ship it
        d.rectangle([x, cy - h / 2, x + w, cy + h / 2],
                    outline=col + (255,), width=2)
        if len(bits) > 4 and bits[4] == "1":
            d.line([(x, cy), (x + w, cy)], fill=col + (255,), width=2)
        x += w + gap


def make_hand(path: Path, length: int, width: int) -> None:
    """Plain placeholder bar. Not a designed hand set."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = SIZE // 2
    d.rectangle([cx - width // 2, cy - length, cx + width // 2, cy + 12],
                fill=INK + (255,))
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=AMBER + (255,))
    img.save(path)


# ---------------------------------------------------------------------
# WFF XML
# ---------------------------------------------------------------------

def watchface_xml(profile: str) -> str:
    R = field_radius()
    D = int(math.ceil(R * 2))
    if D % 2:
        D += 1
    fx = AP["cx"] - D / 2
    fy = AP["cy"] - D / 2
    roll = roll_expression(PROFILES[profile]["roll_deg"])
    pitch = pitch_expression(PROFILES[profile]["pitch_px"], fy)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!-- DISPOSABLE SPIKE - profile {profile} - NOT PRODUCT CODE -->
<WatchFace width="{SIZE}" height="{SIZE}">
  <Metadata key="CLOCK_TYPE" value="ANALOG" />
  <Metadata key="PREVIEW_TIME" value="10:09:30" />
  <Scene backgroundColor="#000000">
    <PartImage name="s10_horizon" x="{fx:.0f}" y="{fy:.0f}" width="{D}" height="{D}" alpha="255" pivotX="0.5" pivotY="0.5">
      <Variant mode="AMBIENT" target="angle" value="0" />
      <Variant mode="AMBIENT" target="y" value="{fy:.0f}" />
      <Transform target="angle" value="{roll}" />
      <Transform target="y" value="{pitch}" />
      <Image resource="horizon" />
    </PartImage>
    <PartImage name="s20_plate" x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="255">
      <Image resource="plate" />
    </PartImage>
    <PartImage name="s30_hour" x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="255" pivotX="0.5" pivotY="0.5">
      <Transform target="angle" value="([HOUR_0_11] + [MINUTE] / 60) * 30" />
      <Image resource="hand_hour" />
    </PartImage>
    <PartImage name="s31_minute" x="0" y="0" width="{SIZE}" height="{SIZE}" alpha="255" pivotX="0.5" pivotY="0.5">
      <Transform target="angle" value="[MINUTE] * 6" />
      <Image resource="hand_min" />
    </PartImage>
  </Scene>
</WatchFace>
"""


WATCH_FACE_INFO = """<?xml version="1.0" encoding="utf-8"?>
<!-- DISPOSABLE SPIKE - NOT PRODUCT CODE -->
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

MANIFEST = f"""<?xml version="1.0" encoding="utf-8"?>
<!-- DISPOSABLE SPIKE - NOT PRODUCT CODE. NO PERMISSIONS DECLARED. -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-feature
        android:name="android.hardware.type.watch"
        android:required="true" />

    <application
        android:label="{LABEL}"
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


def build_gradle() -> str:
    flavours = "\n".join(
        f"""        create("{n}") {{
            dimension = "profile"
            applicationIdSuffix = "{p['suffix']}"
            versionNameSuffix = "-{n}"
        }}""" for n, p in sorted(PROFILES.items()))
    return f"""// DISPOSABLE SPIKE - NOT PRODUCT CODE.
// Debug builds only. No release block, no signing config, no bundle config.
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

    // Deliberately absent: any signing block, any release buildType
    // customisation, any bundle block. The spike must not be able to
    // produce a signed or releasable artifact, and a gate asserts that
    // none of those tokens appears in this file.
    buildTypes {{
        debug {{ isMinifyEnabled = false }}
    }}
}}
"""


SETTINGS_GRADLE = """// DISPOSABLE SPIKE
pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}
rootProject.name = "attitude-horizon-spike"
include(":app")
"""

ROOT_GRADLE = """// DISPOSABLE SPIKE
plugins { id("com.android.application") version "9.2.1" apply false }
"""


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def generate() -> dict:
    main_res = APP / "src/main/res"
    (main_res / "drawable-nodpi").mkdir(parents=True, exist_ok=True)
    (main_res / "values").mkdir(parents=True, exist_ok=True)
    (main_res / "drawable").mkdir(parents=True, exist_ok=True)
    (APP / "src/main").mkdir(parents=True, exist_ok=True)

    make_horizon(main_res / "drawable-nodpi/horizon.png")
    make_hand(main_res / "drawable-nodpi/hand_hour.png", 104, 14)
    make_hand(main_res / "drawable-nodpi/hand_min.png", 152, 9)
    (main_res / "values/integers.xml").write_text(INTEGERS, encoding="utf-8")
    (APP / "src/main/AndroidManifest.xml").write_text(MANIFEST,
                                                      encoding="utf-8")

    for profile in sorted(PROFILES):
        fres = APP / "src" / profile / "res"
        (fres / "raw").mkdir(parents=True, exist_ok=True)
        (fres / "xml").mkdir(parents=True, exist_ok=True)
        (fres / "drawable-nodpi").mkdir(parents=True, exist_ok=True)
        (fres / "drawable").mkdir(parents=True, exist_ok=True)
        make_plate(fres / "drawable-nodpi/plate.png", profile)
        # preview: the plate is enough to identify the variant
        make_plate(fres / "drawable/preview.png", profile)
        (fres / "raw/watchface.xml").write_text(watchface_xml(profile),
                                                encoding="utf-8")
        (fres / "xml/watch_face_info.xml").write_text(WATCH_FACE_INFO,
                                                      encoding="utf-8")

    (APP / "build.gradle.kts").write_text(build_gradle(), encoding="utf-8")
    (HERE / "settings.gradle.kts").write_text(SETTINGS_GRADLE,
                                              encoding="utf-8")
    (HERE / "build.gradle.kts").write_text(ROOT_GRADLE, encoding="utf-8")

    R = field_radius()
    manifest = {
        "schema": "xsywatch.attitude-spike/1",
        "DISPOSABLE": True,
        "warning": ("Throwaway engineering experiment. Not product code, "
                    "not product artwork, not a release candidate. Nothing "
                    "here may be promoted into ATTITUDE."),
        "base_package": BASE_PACKAGE,
        "label": LABEL,
        "version_name": VERSION_NAME,
        "version_code": VERSION_CODE,
        "aperture": dict(AP),
        "conservative_aperture_bound_px": round(conservative_bound(), 2),
        "shared_field_radius_px": round(R, 2),
        "wrist_roll_clamp_deg": WRIST_ROLL_CLAMP,
        "wrist_pitch_clamp_deg": WRIST_PITCH_CLAMP,
        "safety_allowance_px": SAFETY_PX,
        "profiles": {
            n: {
                "display_roll_max_deg": p["roll_deg"],
                "display_pitch_max_px": p["pitch_px"],
                "application_id": BASE_PACKAGE + p["suffix"],
                "required_field_radius_px": round(
                    required_field_radius(p["pitch_px"]), 2),
                "coverage_margin_px": round(
                    coverage_margin(R, p["pitch_px"]), 2),
                "roll_expression": roll_expression(p["roll_deg"]),
            } for n, p in sorted(PROFILES.items())
        },
        "generated_files": {},
    }
    # Only GENERATED SOURCES. Build outputs live under app/build/ and
    # change on every build; hashing them would make the manifest
    # perpetually stale and the determinism gate meaningless.
    for p in sorted(APP.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(HERE)
        if "build" in rel.parts or "__pycache__" in rel.parts:
            continue
        manifest["generated_files"][str(rel)] = sha256(p)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and fail on any drift")
    args = ap.parse_args()

    out = HERE / "SPIKE_MANIFEST.json"
    before = json.loads(out.read_text(encoding="utf-8")) if out.exists() \
        else None
    manifest = generate()
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"

    if args.check:
        if before is None:
            print("ERROR no committed SPIKE_MANIFEST.json", file=sys.stderr)
            return 1
        if json.loads(text) != before:
            print("ERROR spike generation is not deterministic, or the "
                  "committed manifest is stale", file=sys.stderr)
            return 1
        print("OK: spike generation is deterministic and matches the manifest")
        return 0

    out.write_text(text, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO)}")
    for n, p in manifest["profiles"].items():
        print(f"  {n:10s} roll ±{p['display_roll_max_deg']:>4}°  "
              f"pitch ±{p['display_pitch_max_px']:>4}px  "
              f"margin {p['coverage_margin_px']:>6}px  {p['application_id']}")
    print(f"  shared field radius {manifest['shared_field_radius_px']} px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
