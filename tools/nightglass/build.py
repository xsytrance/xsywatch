"""Build MERIDIAN NIGHTGLASS — a quiet night-flight instrument for Wear OS.

Everything is deterministic and original: Pillow draws the static instrument
and sprites; Watch Face Format owns all live values, motion and interaction.
Run from the repository root:

    python3 tools/nightglass/build.py
"""

from __future__ import annotations

import math
import random
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[2]
FACE = REPO / "watchfaces/meridian-nightglass"
DRAW = FACE / "app/src/main/res/drawable"
RAW = FACE / "app/src/main/res/raw"
SS, C, S = 4, 240, 1920
SEED = 0x4E474C

sys.path.insert(0, str(REPO / "tools/meridian_pro"))
import typography as T  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def fnt(px: int, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, px * SS)


def at(r: float, deg: float):
    a = math.radians(deg - 90)
    return ((C + math.cos(a) * r) * SS, (C + math.sin(a) * r) * SS)


def text(d, xy, value, px, fill, bold=False, anchor="mm", spacing=0):
    font = fnt(px, bold)
    x, y = xy[0] * SS, xy[1] * SS
    if spacing <= 0:
        d.text((x, y), value, font=font, fill=fill, anchor=anchor)
        return
    widths = [d.textlength(ch, font=font) for ch in value]
    total = sum(widths) + spacing * SS * max(0, len(value) - 1)
    cur = x - total / 2
    for ch, width in zip(value, widths):
        d.text((cur, y), ch, font=font, fill=fill, anchor="lm")
        cur += width + spacing * SS


def steel_ring(d, box, width=2):
    x0, y0, x1, y1 = [v * SS for v in box]
    d.ellipse([x0, y0 + SS, x1, y1 + SS], outline=(0, 0, 0, 150),
              width=(width + 2) * SS)
    d.arc([x0, y0, x1, y1], 170, 350, fill=(156, 184, 192, 180),
          width=width * SS)
    d.arc([x0, y0, x1, y1], -10, 170, fill=(35, 52, 61, 230),
          width=width * SS)


def background() -> Image.Image:
    rng = random.Random(SEED)
    im = Image.new("RGBA", (S, S), (3, 8, 12, 255))
    d = ImageDraw.Draw(im)

    # Smoked ceramic bezel and deep sapphire dial.
    for r in range(240, 0, -1):
        t = r / 240
        if r > 211:
            col = (9 + int(11 * t), 16 + int(15 * t), 20 + int(18 * t), 255)
        else:
            col = (4 + int(7 * t), 14 + int(18 * t), 22 + int(26 * t), 255)
        rr = r * SS
        d.ellipse([C * SS - rr, C * SS - rr, C * SS + rr, C * SS + rr],
                  fill=col)

    # Ceramic grain is quiet, only visible close-up.
    for _ in range(2200):
        a = rng.random() * math.tau
        r = math.sqrt(rng.random()) * 238 * SS
        x, y = C * SS + math.cos(a) * r, C * SS + math.sin(a) * r
        lum = rng.choice((10, 16, 22, 30))
        d.point((x, y), fill=(110, 150, 160, lum))

    # Bezel lips.
    for r, color, width in (
            (237, (120, 152, 160, 150), 1),
            (211, (0, 0, 0, 230), 3),
            (207, (72, 118, 132, 110), 1)):
        rr = r * SS
        d.ellipse([C * SS - rr, C * SS - rr, C * SS + rr, C * SS + rr],
                  outline=color, width=width * SS)

    # Outer minute rail. Cardinal marks carry the sapphire signature.
    for minute in range(60):
        deg = minute * 6
        major = minute % 5 == 0
        r0 = 218 if major else 222
        col = (86, 226, 228, 235) if minute % 15 == 0 else \
              ((194, 209, 210, 180) if major else (110, 139, 145, 90))
        d.line([at(r0, deg), at(230, deg)], fill=col,
               width=(3 if minute % 15 == 0 else 2 if major else 1) * SS)

    # Cyan orientation pip and warm heading numerals.
    pip = at(201, 0)
    d.polygon([(pip[0], pip[1] - 7 * SS),
               (pip[0] - 6 * SS, pip[1] + 4 * SS),
               (pip[0] + 6 * SS, pip[1] + 4 * SS)],
              fill=(89, 232, 232, 255))
    for deg, label in ((45, "NE"), (135, "SE"), (225, "SW"), (315, "NW")):
        x, y = at(192, deg)
        text(d, (x / SS, y / SS), label, 10, (202, 148, 78, 210), True)

    # Subtle avionics grid and central artificial-horizon instrument.
    for off in (-80, -40, 40, 80):
        d.line([(C + off) * SS, 92 * SS, (C + off) * SS, 388 * SS],
               fill=(76, 181, 190, 18), width=SS)
        d.line([92 * SS, (C + off) * SS, 388 * SS, (C + off) * SS],
               fill=(76, 181, 190, 18), width=SS)
    steel_ring(d, (164, 169, 316, 321), 2)
    d.ellipse([171 * SS, 176 * SS, 309 * SS, 314 * SS],
              fill=(5, 16, 25, 245), outline=(40, 98, 112, 190), width=SS)
    d.rectangle([174 * SS, 245 * SS, 306 * SS, 314 * SS],
                fill=(21, 17, 18, 170))
    d.line([(181 * SS, 245 * SS), (299 * SS, 245 * SS)],
           fill=(216, 158, 76, 190), width=2 * SS)
    for dy, half in ((-28, 24), (-14, 14), (14, 14), (28, 24)):
        d.line([(C - half) * SS, (245 + dy) * SS,
                (C + half) * SS, (245 + dy) * SS],
               fill=(102, 202, 207, 90), width=SS)
    d.polygon([(220 * SS, 246 * SS), (240 * SS, 237 * SS),
               (260 * SS, 246 * SS), (254 * SS, 249 * SS),
               (240 * SS, 244 * SS), (226 * SS, 249 * SS)],
              fill=(222, 177, 96, 230))

    # Battery channel.
    d.arc([72 * SS, 72 * SS, 408 * SS, 408 * SS], 208, 332,
          fill=(0, 0, 0, 200), width=20 * SS)
    d.arc([72 * SS, 72 * SS, 408 * SS, 408 * SS], 208, 332,
          fill=(43, 87, 97, 130), width=2 * SS)
    text(d, (240, 111), "FUEL", 9, (104, 176, 182, 210), True, spacing=2)

    # Identity occupies the calm space above the hands.
    text(d, (240, 148), "NIGHTGLASS", 19, (224, 233, 232, 245), True,
         spacing=1.5)
    text(d, (240, 164), "MERIDIAN / FLIGHT SYSTEM", 7,
         (202, 148, 78, 220), True, spacing=.7)

    # Left 24-hour instrument.
    d.rounded_rectangle([92 * SS, 196 * SS, 151 * SS, 271 * SS],
                        radius=12 * SS, fill=(4, 12, 18, 235),
                        outline=(58, 111, 122, 180), width=SS)
    text(d, (121.5, 258), "ZULU", 8, (88, 212, 216, 220), True, spacing=1)

    # Date cassette.
    d.rounded_rectangle([329 * SS, 194 * SS, 388 * SS, 274 * SS],
                        radius=12 * SS, fill=(5, 12, 18, 245),
                        outline=(195, 145, 75, 210), width=2 * SS)
    d.rounded_rectangle([337 * SS, 218 * SS, 380 * SS, 252 * SS],
                        radius=4 * SS, fill=(1, 5, 8, 255),
                        outline=(68, 92, 96, 220), width=SS)

    # Twin lower instruments, deliberately separated from the horizon.
    for cx, label, accent in ((151, "DISTANCE", (82, 225, 218, 230)),
                              (329, "PULSE", (230, 151, 73, 230))):
        steel_ring(d, (cx - 56, 292, cx + 56, 404), 2)
        d.ellipse([(cx - 50) * SS, 298 * SS, (cx + 50) * SS, 398 * SS],
                  fill=(2, 10, 16, 250), outline=(41, 75, 84, 220), width=SS)
        for deg in range(-135, 136, 45):
            p0 = ((cx + math.cos(math.radians(deg - 90)) * 41) * SS,
                  (348 + math.sin(math.radians(deg - 90)) * 41) * SS)
            p1 = ((cx + math.cos(math.radians(deg - 90)) * 46) * SS,
                  (348 + math.sin(math.radians(deg - 90)) * 46) * SS)
            d.line([p0, p1], fill=accent, width=2 * SS)
        text(d, (cx, 374), label, 7, accent, True, spacing=.8)

    # Weather strip—small, secondary, and honest.
    d.rounded_rectangle([178 * SS, 410 * SS, 302 * SS, 440 * SS],
                        radius=9 * SS, fill=(3, 10, 15, 245),
                        outline=(42, 82, 91, 200), width=SS)
    d.line([(240 * SS, 414 * SS), (240 * SS, 436 * SS)],
           fill=(54, 91, 98, 180), width=SS)
    text(d, (191, 425), "TEMP", 6, (91, 190, 195, 200), True)
    text(d, (252, 425), "RAIN", 6, (91, 190, 195, 200), True)

    # Four restrained fastener points.
    for deg in (45, 135, 225, 315):
        x, y = at(184, deg)
        r = 3 * SS
        d.ellipse([x-r, y-r, x+r, y+r], fill=(76, 92, 98, 255),
                  outline=(172, 188, 188, 160), width=SS)
        d.line([(x-r*.55, y), (x+r*.55, y)], fill=(12, 20, 24, 255), width=SS)

    return im.resize((480, 480), Image.Resampling.LANCZOS)


def hands():
    cx = cy = C * SS

    def hand(length, width, cyan=False):
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        L, W = length * SS, width * SS
        body = [(cx-W/2, cy+18*SS), (cx-W*.36, cy-L*.72),
                (cx, cy-L), (cx+W*.36, cy-L*.72), (cx+W/2, cy+18*SS)]
        d.polygon([(x+2*SS, y+2*SS) for x, y in body], fill=(0, 0, 0, 110))
        d.polygon(body, fill=(181, 135, 72, 255))
        inner = [(cx-W*.24, cy+9*SS), (cx-W*.16, cy-L*.68),
                 (cx, cy-L*.88), (cx+W*.16, cy-L*.68),
                 (cx+W*.24, cy+9*SS)]
        d.polygon(inner, fill=(10, 27, 37, 255))
        lume = (97, 232, 228, 255) if cyan else (218, 231, 211, 255)
        d.line([(cx, cy-8*SS), (cx, cy-L*.72)], fill=lume,
               width=max(2, int(W*.22)))
        return im.resize((480, 480), Image.Resampling.LANCZOS)

    second = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(second)
    sd.line([(cx, cy+34*SS), (cx, cy-181*SS)], fill=(232, 139, 58, 255),
            width=2*SS)
    sd.ellipse([cx-4*SS, cy-174*SS, cx+4*SS, cy-166*SS],
               fill=(104, 236, 232, 255))
    boss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(boss)
    bd.ellipse([(C-13)*SS, (C-13)*SS, (C+13)*SS, (C+13)*SS],
               fill=(186, 139, 74, 255))
    bd.ellipse([(C-9)*SS, (C-9)*SS, (C+9)*SS, (C+9)*SS],
               fill=(38, 73, 82, 255), outline=(117, 225, 220, 230), width=SS)
    return {
        "ng_hour.png": hand(108, 24),
        "ng_minute.png": hand(169, 18, True),
        "ng_second.png": second.resize((480, 480), Image.Resampling.LANCZOS),
        "ng_boss.png": boss.resize((480, 480), Image.Resampling.LANCZOS),
    }


def aod() -> Image.Image:
    im = Image.new("RGBA", (480, 480), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    d.ellipse([42, 42, 438, 438], outline=(30, 62, 67, 255), width=1)
    for h in range(12):
        x0, y0 = at(204, h * 30)
        x1, y1 = at(220, h * 30)
        d.line([x0/SS, y0/SS, x1/SS, y1/SS],
               fill=(62, 108, 110, 255), width=2)
    return im


def xml() -> str:
    widths = T.emit_glyphs(DRAW, prefix="ng")
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<WatchFace width="480" height="480">',
        '  <Metadata key="CLOCK_TYPE" value="ANALOG" />',
        '  <Metadata key="PREVIEW_TIME" value="10:09:32" />',
        '  <UserConfigurations>',
        '    <ColorConfiguration id="glow" displayName="Night lighting" defaultValue="sapphire">',
        '      <ColorOption id="sapphire" displayName="Sapphire" colors="#FF59E8E6 #FFE8FFFF #FFCA944E" />',
        '      <ColorOption id="radar" displayName="Radar" colors="#FF7BE082 #FFE9FFE8 #FFD9B45C" />',
        '      <ColorOption id="amber" displayName="Amber" colors="#FFF0A34D #FFFFE7C1 #FF62D8D4" />',
        '      <ColorOption id="ice" displayName="Ice" colors="#FF88CFFF #FFF2FAFF #FFC6A86A" />',
        '      <ColorOption id="stealth" displayName="Stealth" colors="#FF9AA8AB #FFF1F4F4 #FFCF8D52" />',
        '    </ColorConfiguration>',
        '    <Flavors defaultValue="sapphire">',
    ]
    for ident, label in (("sapphire", "Sapphire"), ("radar", "Radar"),
                         ("amber", "Amber"), ("ice", "Ice"),
                         ("stealth", "Stealth")):
        out.append(f'      <Flavor id="{ident}" displayName="{label}">'
                   f'<Configuration id="glow" optionId="{ident}" /></Flavor>')
    out += ['    </Flavors>', '  </UserConfigurations>']
    out += T.font_xml(widths, family="ng", prefix="ng")
    out += [
        '  <Scene backgroundColor="#FF000000">',
        '    <PartImage name="base" x="0" y="0" width="480" height="480">',
        '      <Variant mode="AMBIENT" target="alpha" value="0" duration="0.3" />',
        '      <Image resource="ng_bg" />',
        '    </PartImage>',
        '    <PartImage name="aod" x="0" y="0" width="480" height="480" alpha="0">',
        '      <Variant mode="AMBIENT" target="alpha" value="255" duration="0.3" />',
        '      <Image resource="ng_aod" />',
        '    </PartImage>',
        '    <PartDraw name="battery_arc" x="0" y="0" width="480" height="480">',
        '      <Variant mode="AMBIENT" target="alpha" value="0" duration="0.2" />',
        '      <Launch target="BATTERY_STATUS" />',
        '      <Arc centerX="240" centerY="240" width="336" height="336" startAngle="-62" endAngle="62">',
        '        <Stroke color="#33152B31" thickness="10" cap="ROUND" />',
        '      </Arc>',
        '      <Arc centerX="240" centerY="240" width="336" height="336" startAngle="-62" endAngle="62">',
        '        <Stroke color="[CONFIGURATION.glow.0]" thickness="7" cap="ROUND" />',
        '        <Transform target="endAngle" value="-62 + 124 * clamp([BATTERY_PERCENT], 0, 100) / 100" />',
        '      </Arc>',
        '    </PartDraw>',
        '    <PartDraw name="steps_arc" x="0" y="0" width="480" height="480">',
        '      <Variant mode="AMBIENT" target="alpha" value="0" duration="0.2" />',
        '      <Arc centerX="151" centerY="348" width="82" height="82" startAngle="-135" endAngle="135">',
        '        <Stroke color="[CONFIGURATION.glow.0]" thickness="6" cap="ROUND" />',
        '        <Transform target="endAngle" value="-135 + 270 * clamp([STEP_PERCENT], 0, 100) / 100" />',
        '      </Arc>',
        '    </PartDraw>',
        '    <PartDraw name="hr_arc" x="0" y="0" width="480" height="480">',
        '      <Variant mode="AMBIENT" target="alpha" value="0" duration="0.2" />',
        '      <Launch target="HEALTH_HEART_RATE" />',
        '      <Arc centerX="329" centerY="348" width="82" height="82" startAngle="-135" endAngle="135">',
        '        <Stroke color="[CONFIGURATION.glow.2]" thickness="6" cap="ROUND" />',
        '        <Transform target="endAngle" value="-135 + 270 * clamp([HEART_RATE], 0, 200) / 200" />',
        '      </Arc>',
        '    </PartDraw>',
    ]
    # Live information; halo passes preserve readability over hands.
    out += T.readout("fuel", 196, 113, 88, 32, 25, "%d%%",
                     ["[BATTERY_PERCENT]"], "[CONFIGURATION.glow.1]",
                     amb=100, family="ng", launch="BATTERY_STATUS")
    out += T.readout("zulu", 96, 211, 51, 38, 30, "%02d",
                     ["[HOUR_0_23]"], "[CONFIGURATION.glow.1]",
                     amb=120, family="ng")
    out += T.readout("dow", 331, 198, 55, 18, 12, "%s",
                     ["[DAY_OF_WEEK_S]"], "[CONFIGURATION.glow.0]",
                     family="ng", upper=True, launch="CALENDAR")
    out += T.readout("day", 333, 218, 51, 34, 28, "%d", ["[DAY]"],
                     "[CONFIGURATION.glow.1]", amb=120, family="ng",
                     launch="CALENDAR")
    out += T.readout("mon", 332, 253, 54, 18, 12, "%s", ["[MONTH_S]"],
                     "[CONFIGURATION.glow.2]", family="ng", upper=True,
                     launch="CALENDAR")
    out += T.readout("steps", 111, 326, 80, 37, 30, "%d", ["[STEP_COUNT]"],
                     "[CONFIGURATION.glow.1]", family="ng")
    out += T.readout("goal", 117, 379, 68, 17, 10, "/%d", ["[STEP_GOAL]"],
                     "[CONFIGURATION.glow.0]", family="ng")
    out += T.readout("hr", 289, 326, 80, 37, 30, "%d", ["[HEART_RATE]"],
                     "[CONFIGURATION.glow.1]", family="ng",
                     launch="HEALTH_HEART_RATE")
    out += T.readout("temp", 198, 413, 38, 24, 15, "%d",
                     ["round([WEATHER.TEMPERATURE])"],
                     "[CONFIGURATION.glow.1]", family="ng")
    out += T.readout("rain", 259, 413, 38, 24, 15, "%d%%",
                     ["round([WEATHER.CHANCE_OF_PRECIPITATION])"],
                     "[CONFIGURATION.glow.1]", family="ng")
    for name, expression, ambient in (
            ("hour", "([HOUR_0_11] + [MINUTE] / 60) * 30", 170),
            ("minute", "([MINUTE] + [SECOND] / 60) * 6", 170),
            ("second", "([SECOND] + [MILLISECOND] / 1000) * 6", 0)):
        out += [
            f'    <PartImage name="{name}_hand" x="0" y="0" width="480" height="480" pivotX="0.5" pivotY="0.5">',
            f'      <Variant mode="AMBIENT" target="alpha" value="{ambient}" duration="0.2" />',
            f'      <Transform target="angle" value="{expression}" />',
            f'      <Image resource="ng_{name}" />',
            '    </PartImage>',
        ]
    out += [
        '    <PartImage name="boss" x="0" y="0" width="480" height="480">',
        '      <Variant mode="AMBIENT" target="alpha" value="160" duration="0.2" />',
        '      <Image resource="ng_boss" />',
        '    </PartImage>',
        '  </Scene>',
        '</WatchFace>',
    ]
    return "\n".join(out) + "\n"


def scaffold():
    probe = REPO / "watchfaces/vector-probe"
    for rel in ("gradlew", "gradlew.bat", "build.gradle.kts",
                "gradle/wrapper/gradle-wrapper.jar",
                "gradle/wrapper/gradle-wrapper.properties",
                "app/src/main/res/values/integers.xml"):
        dst = FACE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(probe / rel, dst)
    (FACE / "gradlew").chmod(0o755)
    (FACE / "settings.gradle.kts").write_text(
        'pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }\n'
        'dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }\n'
        'rootProject.name = "MeridianNightglass"\ninclude(":app")\n')
    (FACE / "app/build.gradle.kts").write_text(
        'plugins { id("com.android.application") }\n'
        'android {\n'
        '    namespace = "com.xsytrance.meridian.nightglass.dev"\n'
        '    compileSdk = 36\n'
        '    defaultConfig {\n'
        '        applicationId = "com.xsytrance.meridian.nightglass.dev"\n'
        '        minSdk = 34\n        targetSdk = 36\n'
        '        versionCode = 1\n        versionName = "0.1.0-dev"\n'
        '    }\n}\n')
    (FACE / "app/src/main/AndroidManifest.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <uses-feature android:name="android.hardware.type.watch" android:required="true" />\n'
        '  <application android:label="MERIDIAN NIGHTGLASS" android:icon="@drawable/preview" android:hasCode="false">\n'
        '    <property android:name="com.google.wear.watchface.format.version" android:value="@integer/wff_version" />\n'
        '    <meta-data android:name="com.google.android.wearable.standalone" android:value="true" />\n'
        '  </application>\n</manifest>\n')
    info = FACE / "app/src/main/res/xml/watch_face_info.xml"
    info.parent.mkdir(parents=True, exist_ok=True)
    info.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<WatchFaceInfo>\n'
        '  <Preview value="@drawable/preview" />\n'
        '  <Editable value="true" />\n'
        '  <MultipleInstancesAllowed value="true" />\n'
        '  <FlavorsSupported value="true" />\n'
        '</WatchFaceInfo>\n')


def main():
    DRAW.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    scaffold()
    bg = background()
    bg.save(DRAW / "ng_bg.png", optimize=True)
    bg.resize((192, 192), Image.Resampling.LANCZOS).convert("RGB").save(
        DRAW / "preview.png", optimize=True)
    aod().save(DRAW / "ng_aod.png", optimize=True)
    for name, image in hands().items():
        image.save(DRAW / name, optimize=True)
    (RAW / "watchface.xml").write_text(xml())
    print(f"built source -> {FACE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
