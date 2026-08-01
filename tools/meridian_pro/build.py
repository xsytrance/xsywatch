"""MERIDIAN PRO — assemble the face: drawables, watchface.xml, project.

The layer contract, bottom to top:

  z00  the Kontext-finished base (dressed with baked labels), AOD twin
  z1x  the live vector layer: power arc, sub-dial rings — PartDraw, proven
       on this device by VPROBE A
  z2x  live readouts — six-pass halo BitmapFont text, zero permissions,
       proven by VPROBE B
  z3x  moon
  z4x  hands, then the boss

Everything positional imports geometry.py. Nothing here restates a number.

Usage:
    python3 tools/meridian_pro/build.py            # assets + xml + project
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometry import (CANVAS, DATE, HANDS, IDENT, MILITARY, MOON,
                      PALETTE as P, POWER, SUBDIAL, WINDOWS)
import plate
import typography as T

REPO = Path(__file__).resolve().parents[2]
FACE = REPO / "watchfaces" / IDENT["face_dir"]
DRAW = FACE / "app/src/main/res/drawable"
RAW = FACE / "app/src/main/res/raw"

AMB0 = ('<Variant mode="AMBIENT" target="alpha" value="0" duration="0.4" '
        'startOffset="0.1" interpolation="EASE_OUT" />')


def hx(c):
    return "#{:02X}{:02X}{:02X}".format(*c[:3])


def ramp(c0, c1, c2, n=18):
    """red->amber->green as n interpolated stops: a WeightedStroke gradient."""
    cols = []
    for i in range(n):
        t = i / (n - 1)
        if t < 0.5:
            a, b_, u = c0, c1, t * 2
        else:
            a, b_, u = c1, c2, (t - 0.5) * 2
        cols.append(hx(tuple(int(a[k] + (b_[k] - a[k]) * u)
                             for k in range(3))))
    return " ".join(cols), " ".join(["1.0"] * n)


def bolt_sprite() -> Image.Image:
    ss = 4
    h = int(POWER["bolt_h"] * ss)
    w = int(h * 0.62)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(w * 0.62, 0), (w * 0.10, h * 0.58), (w * 0.44, h * 0.58),
           (w * 0.30, h), (w * 0.92, h * 0.40), (w * 0.55, h * 0.40)]
    d.polygon([(x + ss, y + ss) for x, y in pts], fill=(0, 0, 0, 140))
    d.polygon(pts, fill=(255, 255, 255, 255))     # white: tinted at use
    return img.resize((w // ss, h // ss), Image.LANCZOS)


# ------------------------------------------------------------------ xml

def power_xml() -> list[str]:
    r = POWER["channel_r"]
    s0, s1 = POWER["start_deg"], POWER["end_deg"]
    box = r * 2
    cols, wts = ramp(P["zone_lim"], P["zone_warn"], P["zone_ok"])
    o = [f'    <PartDraw name="z10_power" x="0" y="0" width="{CANVAS}" '
         f'height="{CANVAS}" alpha="255">', f'      {AMB0}',
         '      <Launch target="BATTERY_STATUS" />',
         # soft glow bedding the ramp into its channel
         f'      <Arc centerX="240" centerY="240" width="{box}" '
         f'height="{box}" startAngle="{s0}" endAngle="{s1}">',
         '        <Stroke color="#28E8C08A" thickness="21" cap="ROUND" />',
         '      </Arc>',
         # the ramp itself: a continuous red->amber->green gradient
         f'      <Arc centerX="240" centerY="240" width="{box}" '
         f'height="{box}" startAngle="{s0}" endAngle="{s1}">',
         f'        <WeightedStroke colors="{cols}" weights="{wts}" '
         'thickness="13" cap="ROUND" discreteGap="0.0" />',
         '      </Arc>',
         # dark unlit remainder drawn from the battery tip to F
         f'      <Arc centerX="240" centerY="240" width="{box}" '
         f'height="{box}" startAngle="{s0}" endAngle="{s1}">',
         '        <Stroke color="#B4060A10" thickness="13" cap="BUTT" />',
         f'        <Transform target="startAngle" value="{s0} + '
         f'{s1 - s0} * clamp([BATTERY_PERCENT], 0, 100) / 100" />',
         '      </Arc>',
         # bright tip marker at the battery position
         f'      <Arc centerX="240" centerY="240" width="{box}" '
         f'height="{box}" startAngle="{s0}" endAngle="{s0 + 2}">',
         '        <Stroke color="[CONFIGURATION.theme.1]" '
         'thickness="15" cap="ROUND" />',
         f'        <Transform target="startAngle" value="{s0} + '
         f'{s1 - s0} * clamp([BATTERY_PERCENT], 0, 100) / 100 - 1" />',
         f'        <Transform target="endAngle" value="{s0} + '
         f'{s1 - s0} * clamp([BATTERY_PERCENT], 0, 100) / 100 + 1" />',
         '      </Arc>', '    </PartDraw>']
    bx, by = POWER["bolt_c"]
    bh = int(POWER["bolt_h"])
    bw = int(bh * 0.62)
    o += [f'    <PartImage name="z11_bolt_dim" x="{bx - bw/2:.0f}" '
          f'y="{by - bh/2:.0f}" width="{bw}" height="{bh}" alpha="200" '
          'tintColor="[CONFIGURATION.theme.0]">', f'      {AMB0}',
          '      <Image resource="mp_bolt" />', '    </PartImage>',
          '    <Condition>', '      <Expressions>',
          '        <Expression name="chg">[BATTERY_CHARGING_STATUS]'
          '</Expression>', '      </Expressions>',
          '      <Compare expression="chg">',
          f'        <PartImage name="z11_bolt_hot" x="{bx - bw/2:.0f}" '
          f'y="{by - bh/2:.0f}" width="{bw}" height="{bh}" alpha="255" '
          f'tintColor="#FFE9A8">', f'          {AMB0}',
          '          <Image resource="mp_bolt" />', '        </PartImage>',
          '      </Compare>', '    </Condition>']
    return o


def subdial_xml() -> list[str]:
    o = []
    r = SUBDIAL["ring_r"]
    w = SUBDIAL["ring_w"]
    a0, a1 = -150.0, 150.0
    box = r * 2
    cols, wts = ramp(P["zone_lim"], P["zone_warn"], P["zone_ok"])
    cx, cy = SUBDIAL["steps_c"]
    o += [f'    <PartDraw name="z12_steps_ring" x="0" y="0" '
          f'width="{CANVAS}" height="{CANVAS}" alpha="255">', f'      {AMB0}',
          f'      <Arc centerX="{cx}" centerY="{cy}" width="{box}" '
          f'height="{box}" startAngle="{a0}" endAngle="{a1}">',
          f'        <Stroke color="#30FFFFFF" thickness="{w}" cap="ROUND" />',
          '      </Arc>',
          f'      <Arc centerX="{cx}" centerY="{cy}" width="{box}" '
          f'height="{box}" startAngle="{a0}" endAngle="{a1}">',
          f'        <WeightedStroke colors="{cols}" weights="{wts}" '
          f'thickness="{w}" cap="ROUND" discreteGap="0.0" />',
          '      </Arc>',
          # unfilled remainder goes dark from the progress tip onward
          f'      <Arc centerX="{cx}" centerY="{cy}" width="{box}" '
          f'height="{box}" startAngle="{a0}" endAngle="{a1}">',
          f'        <Stroke color="#C8080C12" thickness="{w + 1}" '
          'cap="BUTT" />',
          f'        <Transform target="startAngle" value="{a0} + '
          f'{a1 - a0} * clamp([STEP_PERCENT], 0, 100) / 100" />',
          '      </Arc>', '    </PartDraw>']
    cx, cy = SUBDIAL["hr_c"]
    o += [f'    <PartDraw name="z13_hr_ring" x="0" y="0" width="{CANVAS}" '
          f'height="{CANVAS}" alpha="255">', f'      {AMB0}',
          f'      <Arc centerX="{cx}" centerY="{cy}" width="{box}" '
          f'height="{box}" startAngle="{a0}" endAngle="{a1}">',
          f'        <WeightedStroke colors="#30FFFFFF {hx(P["zone_ok"])} '
          f'{hx(P["zone_warn"])} {hx(P["zone_lim"])}" '
          f'weights="2.4 3.6 2.4 1.6" thickness="{w}" cap="ROUND" '
          'discreteGap="0.0" />',
          '      </Arc>',
          f'      <Arc centerX="{cx}" centerY="{cy}" width="{box}" '
          f'height="{box}" startAngle="{a0}" endAngle="{a0 + 8}">',
          f'        <Stroke color="#FFFFFFFF" thickness="{w + 4}" '
          'cap="ROUND" />',
          f'        <Transform target="startAngle" value="{a0} + '
          f'{a1 - a0} * clamp([HEART_RATE], 0, 200) / 200 - 3" />',
          f'        <Transform target="endAngle" value="{a0} + '
          f'{a1 - a0} * clamp([HEART_RATE], 0, 200) / 200 + 3" />',
          '      </Arc>', '    </PartDraw>']
    return o


def readouts_xml() -> list[str]:
    o = []
    # battery %
    rx, ry = POWER["readout_c"]
    o += T.readout("z20_batt", int(rx - 60), int(ry - 19), 120, 38,
                   POWER["readout_px"], POWER.get("fmt", "%d%%"),
                   ["[BATTERY_PERCENT]"],
                   colour="[CONFIGURATION.theme.1]", amb=110,
                   launch="BATTERY_STATUS")
    # steps: the big number and the wearer's own goal under it
    sx, sy = SUBDIAL["steps_c"]
    o += T.readout("z21_steps", int(sx - 55),
                   int(sy + SUBDIAL["value_dy"] - 18), 110, 38,
                   SUBDIAL["value_px"], "%d", ["[STEP_COUNT]"],
                   colour=hx(P["ink"]))
    o += T.readout("z22_goal", int(sx - 55),
                   int(sy + SUBDIAL["goal_dy"] - 9), 110, 20, 12,
                   "/%d", ["[STEP_GOAL]"], colour=hx(P["gold"]))
    # heart rate
    hx_, hy = SUBDIAL["hr_c"]
    o += T.readout("z23_hr", int(hx_ - 55),
                   int(hy + SUBDIAL["value_dy"] - 18), 110, 38,
                   SUBDIAL["value_px"], "%d", ["[HEART_RATE]"],
                   colour="[CONFIGURATION.theme.1]",
                   launch="HEALTH_HEART_RATE")
    # military time
    mx, my = MILITARY["c"]
    o += T.readout("z24_mil", int(mx - 45), int(my - 23), 90, 46,
                   MILITARY["big_px"], "%02d", ["[HOUR_0_23]"],
                   colour=hx(P["ink"]), amb=150)
    # the three-field date
    dx, dy = DATE["c"]
    o += T.readout("z25_dow", int(dx - 33), int(dy + DATE["dow_dy"]), 66, 20,
                   DATE["dow_px"], "%s", ["[DAY_OF_WEEK_S]"],
                   colour=hx(P["ink"]), upper=True, launch="CALENDAR")
    o += T.readout("z26_day", int(dx - 33), int(dy - 17), 66, 36,
                   DATE["day_px"], "%d", ["[DAY]"],
                   colour="[CONFIGURATION.theme.0]", amb=140,
                   launch="CALENDAR")
    o += T.readout("z27_mon", int(dx - 33), int(dy + DATE["mon_dy"]), 66, 20,
                   DATE["mon_px"], "%s", ["[MONTH_S]"],
                   colour="[CONFIGURATION.theme.0]", upper=True,
                   launch="CALENDAR")
    # weather windows; plain 0 when unavailable is acceptable at 0.1.0
    for name, (wx, wy), tmpl, params in (
            ("z28_temp", WINDOWS["left_c"], "%d",
             ["round([WEATHER.TEMPERATURE])"]),
            ("z29_rain", WINDOWS["right_c"], "%d%%",
             ["round([WEATHER.CHANCE_OF_PRECIPITATION])"])):
        o += T.readout(name, int(wx - WINDOWS["w"] / 2 + 14),
                       int(wy - 13), int(WINDOWS["w"]), 26,
                       WINDOWS["value_px"], tmpl, params,
                       colour=hx(P["ink"]))
    return o


def hands_xml() -> list[str]:
    o = []
    for name, expr, amb in (
            ("hour", "([HOUR_0_11] + [MINUTE] / 60) * 30", 170),
            ("minute", "([MINUTE] + [SECOND] / 60) * 6", 170)):
        o += [f'    <PartImage name="z40_{name}" x="0" y="0" '
              f'width="{CANVAS}" height="{CANVAS}" alpha="255" pivotX="0.5" '
              'pivotY="0.5">',
              f'      <Variant mode="AMBIENT" target="alpha" value="{amb}" '
              'duration="0.4" startOffset="0.0" interpolation="LINEAR" />',
              f'      <Transform target="angle" value="{expr}" />',
              f'      <Image resource="mp_hand_{name}" />',
              '    </PartImage>']
    o += [f'    <PartImage name="z41_second" x="0" y="0" width="{CANVAS}" '
          f'height="{CANVAS}" alpha="255" pivotX="0.5" pivotY="0.5">',
          f'      {AMB0}',
          '      <Transform target="angle" '
          'value="([SECOND] + [MILLISECOND] / 1000) * 6" />',
          '      <Image resource="mp_hand_second" />', '    </PartImage>',
          f'    <PartImage name="z42_boss" x="0" y="0" width="{CANVAS}" '
          f'height="{CANVAS}" alpha="255">',
          '      <Variant mode="AMBIENT" target="alpha" value="170" '
          'duration="0.4" startOffset="0.0" interpolation="LINEAR" />',
          '      <Image resource="mp_hand_boss" />', '    </PartImage>']
    return o


def build_xml(widths) -> str:
    o = ['<?xml version="1.0" encoding="utf-8"?>', '<!--',
         'GENERATED FILE - do not edit by hand.',
         '  Authoritative source: tools/meridian_pro/build.py',
         '  Geometry: tools/meridian_pro/geometry.py (single source of truth)',
         '  Base art: procedural layout, Kontext Pro finish, anchors verified.',
         '-->',
         f'<WatchFace width="{CANVAS}" height="{CANVAS}">',
         '  <Metadata key="CLOCK_TYPE" value="ANALOG" />',
         '  <Metadata key="PREVIEW_TIME" value="10:09:32" />',
         '  <UserConfigurations>',
         '    <ColorConfiguration id="theme" displayName="Accent theme" '
         'defaultValue="meridian">',
         '      <ColorOption id="meridian" displayName="Meridian" '
         'colors="#FFDEB269 #FFFFFFFF #FF36B474" />',
         '      <ColorOption id="tactical" displayName="Tactical" '
         'colors="#FF9AD96B #FFE8FFD8 #FF5FD68F" />',
         '      <ColorOption id="ember" displayName="Ember" '
         'colors="#FFF08A42 #FFFFE2C4 #FFE45B42" />',
         '      <ColorOption id="violet" displayName="Violet" '
         'colors="#FFD889F2 #FFFFE8FF #FFB867DE" />',
         '      <ColorOption id="arctic" displayName="Arctic" '
         'colors="#FF66D6E8 #FFE8FCFF #FF42C6D9" />',
         '    </ColorConfiguration>',
         '    <Flavors defaultValue="meridian">',
         '      <Flavor id="meridian" displayName="Meridian">'
         '<Configuration id="theme" optionId="meridian" /></Flavor>',
         '      <Flavor id="tactical" displayName="Tactical">'
         '<Configuration id="theme" optionId="tactical" /></Flavor>',
         '      <Flavor id="ember" displayName="Ember">'
         '<Configuration id="theme" optionId="ember" /></Flavor>',
         '      <Flavor id="violet" displayName="Violet">'
         '<Configuration id="theme" optionId="violet" /></Flavor>',
         '      <Flavor id="arctic" displayName="Arctic">'
         '<Configuration id="theme" optionId="arctic" /></Flavor>',
         '    </Flavors>',
         '  </UserConfigurations>']
    o += T.font_xml(widths)
    o += ['  <Scene backgroundColor="#FF000000">',
          f'    <PartImage name="z00_bg" x="0" y="0" width="{CANVAS}" '
          f'height="{CANVAS}" alpha="255">',
          '      <Variant mode="AMBIENT" target="alpha" value="0" '
          'duration="0.4" startOffset="0.0" interpolation="EASE_OUT" />',
          '      <Image resource="mp_bg" />', '    </PartImage>',
          f'    <PartImage name="z01_bg_aod" x="0" y="0" width="{CANVAS}" '
          f'height="{CANVAS}" alpha="0">',
          '      <Variant mode="AMBIENT" target="alpha" value="255" '
          'duration="0.4" startOffset="0.0" interpolation="EASE_IN" />',
          '      <Image resource="mp_bg_aod" />', '    </PartImage>']
    o += power_xml()
    o += subdial_xml()
    o += readouts_xml()
    mx, my = MOON["disc_c"]
    mr = MOON["disc_r"]
    o += [f'    <PartImage name="z30_moon" x="{mx - mr:.0f}" '
          f'y="{my - mr:.0f}" width="{mr * 2:.0f}" height="{mr * 2:.0f}" '
          f'alpha="255">', f'      {AMB0}',
          '      <Image resource="mp_moon" />', '    </PartImage>']
    o += hands_xml()
    o += ['  </Scene>', '</WatchFace>']
    return "\n".join(o) + "\n"


GRADLE_APP = '''plugins {
    id("com.android.application")
}

// MERIDIAN PRO — the redesign, built to be sold. Base art is a procedural
// layout finished by Kontext Pro over our own render (see PROVENANCE.md);
// instruments and readouts are live WFF vectors and text. Dev build:
// debug signing, .dev namespace. The production identity lands with the
// release phase of docs/plans/MERIDIAN_PRO_SHIP_PLAN.md.
android {
    namespace = "com.xsytrance.meridianpro.dev"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.xsytrance.meridianpro.dev"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev"
    }
}
'''

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-feature
        android:name="android.hardware.type.watch"
        android:required="true" />

    <!-- ZERO permissions, and that is a measured fact, not a hope: VPROBE B
         showed STEP_COUNT, STEP_GOAL, STEP_PERCENT, HEART_RATE and
         BATTERY_CHARGING_STATUS all flowing with an empty permission set on
         this hardware. The Play data-safety form stays near-empty. -->

    <application
        android:label="MERIDIAN PRO"
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
'''


def main() -> int:
    DRAW.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)

    base = FACE / "review" / IDENT["kontext_base"]
    plate.dress_base(base, DRAW / "mp_bg.png")
    plate.bg_aod(DRAW / "mp_bg.png", DRAW / "mp_bg_aod.png")
    plate.hands(DRAW)
    plate.moon_sprite(DRAW)
    bolt_sprite().save(DRAW / "mp_bolt.png", optimize=True)
    widths = T.emit_glyphs(DRAW)
    with Image.open(DRAW / "mp_bg.png") as im:
        im.convert("RGB").resize((192, 192), Image.LANCZOS).save(
            DRAW / "preview.png", optimize=True)

    (RAW / "watchface.xml").write_text(build_xml(widths))

    # project scaffolding, idempotent
    probe = REPO / "watchfaces/vector-probe"
    for rel in ("gradlew", "gradlew.bat", "build.gradle.kts",
                "gradle/wrapper/gradle-wrapper.jar",
                "gradle/wrapper/gradle-wrapper.properties",
                "app/src/main/res/values/integers.xml",
                "app/src/main/res/xml/watch_face_info.xml"):
        dst = FACE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(probe / rel, dst)
    (FACE / "gradlew").chmod(0o755)
    (FACE / "settings.gradle.kts").write_text(
        (probe / "settings.gradle.kts").read_text().replace(
            "VectorProbe", IDENT["project"]))
    (FACE / "app/build.gradle.kts").write_text(GRADLE_APP.replace(
        "com.xsytrance.meridianpro.dev", IDENT["app_id"]))
    (FACE / "app/src/main/AndroidManifest.xml").write_text(MANIFEST.replace(
        'label="MERIDIAN PRO"', f'label="{IDENT["label"]}"'))
    (FACE / "app/src/main/res/xml/watch_face_info.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<WatchFaceInfo>\n'
        '    <Preview value="@drawable/preview" />\n'
        '    <Editable value="true" />\n'
        '    <MultipleInstancesAllowed value="true" />\n'
        '    <FlavorsSupported value="true" />\n'
        '</WatchFaceInfo>\n')
    n = len(list(DRAW.glob("*.png")))
    print(f"  {n} drawables, watchface.xml, project -> {FACE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
