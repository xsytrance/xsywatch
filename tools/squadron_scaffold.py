#!/usr/bin/env python3
"""Scaffold the ATTITUDE SQUADRON collection into buildable face projects.

    python3 tools/squadron_scaffold.py              # scaffold every variant
    python3 tools/squadron_scaffold.py --only pure
    python3 tools/squadron_scaffold.py --check      # verify, write nothing

One studio platform, one consumer template. For each variant this writes a
complete Gradle project under watchfaces/squadron-<slug>/, imports the
studio's exported assets with their hashes recorded, and emits an
engine/face.toml that tools/generate_face.py turns into watchface.xml.

The whole family therefore shares one technical foundation: the same
component list, the same live data bindings, the same isolated horizon
motion contract. A variant differs only in artwork and identity.

Development builds only. Debug signing, no release configuration, no store
metadata, package IDs namespaced under .dev so nothing can collide with a
shipped face.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STUDIO_DEFAULT = Path.home() / "AGENOR-Horology"
TEMPLATE = REPO / "watchfaces" / "ares-wargod"      # scaffolding donor only
PKG_PREFIX = "com.xsytrance.squadron"
VERSION_NAME = "0.1.0-dev"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def slug_dir(slug: str) -> Path:
    return REPO / "watchfaces" / f"squadron-{slug}"


def package(slug: str) -> str:
    return f"{PKG_PREFIX}.{slug.replace('-', '')}.dev"


# ---------------------------------------------------------------------
# project scaffolding
# ---------------------------------------------------------------------
GRADLE_APP = """plugins {{
    id("com.android.application")
}}

// {title} — ATTITUDE SQUADRON collection, development build.
//
// Debug signing only. No release signing block, no bundle configuration and
// no store metadata. The application ID is namespaced .dev so it can never
// collide with, or be mistaken for, a shipped package.
android {{
    namespace = "{pkg}"
    compileSdk = 36

    defaultConfig {{
        applicationId = "{pkg}"
        minSdk = 34
        targetSdk = 36
        versionCode = 1
        versionName = "{version}"
    }}
}}
"""

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-feature
        android:name="android.hardware.type.watch"
        android:required="true" />

    <!-- Required by the live readouts: BODY_SENSORS for [HEART_RATE],
         ACTIVITY_RECOGNITION for [STEP_COUNT]. Nothing else. -->
    <uses-permission android:name="android.permission.BODY_SENSORS" />
    <uses-permission android:name="android.permission.ACTIVITY_RECOGNITION" />

    <application
        android:label="{label}"
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

SETTINGS = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "%s"
include(":app")
"""


def scaffold_project(slug: str, meta: dict) -> Path:
    d = slug_dir(slug)
    for sub in ("app/src/main/res/raw", "app/src/main/res/values",
                "app/src/main/res/xml", "app/src/main/res/drawable",
                "engine", "gradle/wrapper"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    for f in ("gradlew", "gradlew.bat", "build.gradle.kts"):
        shutil.copy2(TEMPLATE / f, d / f)
    (d / "gradlew").chmod(0o755)
    for f in ("gradle-wrapper.jar", "gradle-wrapper.properties"):
        shutil.copy2(TEMPLATE / "gradle/wrapper" / f, d / "gradle/wrapper" / f)
    for f in ("values/integers.xml", "xml/watch_face_info.xml"):
        shutil.copy2(TEMPLATE / "app/src/main/res" / f,
                     d / "app/src/main/res" / f)
    camel = "Squadron" + "".join(w.capitalize() for w in slug.split("-"))
    (d / "settings.gradle.kts").write_text(SETTINGS % camel)
    (d / "app/build.gradle.kts").write_text(GRADLE_APP.format(
        title=meta["title"], pkg=package(slug), version=VERSION_NAME))
    (d / "app/src/main/AndroidManifest.xml").write_text(
        MANIFEST.format(label=meta["title"]))
    (d / "local.properties").write_text(f"sdk.dir={Path.home()}/Android/Sdk\n")
    return d


# ---------------------------------------------------------------------
# assets
# ---------------------------------------------------------------------
def import_assets(slug: str, meta: dict, studio: Path, d: Path,
                  check: bool) -> tuple[dict, list[str]]:
    export = studio / "phase3-squadron" / "export" / slug
    review = studio / "phase3-squadron" / "review"
    drawable = d / "app/src/main/res/drawable"
    imported, problems = {}, []

    for rel, m in sorted(meta["assets"].items()):
        src = export / rel
        if not src.exists():
            problems.append(f"{slug}: missing studio asset {rel}")
            continue
        actual = sha256(src)
        if actual != m["sha256"]:
            problems.append(f"{slug}: {rel} does not match the studio manifest")
            continue
        dest = drawable / Path(rel).name
        if check:
            if not dest.exists() or sha256(dest) != actual:
                problems.append(f"{slug}: {rel} drifted from the studio export")
        else:
            shutil.copy2(src, dest)
        imported[dest.name] = {"sha256": actual, "bytes": m["bytes"],
                               "width": m["width"], "height": m["height"]}

    prev = review / f"{slug}_NORMAL.png"
    if not prev.exists():
        problems.append(f"{slug}: no studio normal render to use as preview")
    else:
        dest = drawable / "preview.png"
        h = sha256(prev)
        if check:
            if not dest.exists() or sha256(dest) != h:
                problems.append(f"{slug}: preview drifted from the studio render")
        else:
            shutil.copy2(prev, dest)
        imported["preview.png"] = {"sha256": h, "bytes": prev.stat().st_size,
                                   "width": 480, "height": 480}

    if not check:
        stray = sorted(p.name for p in drawable.iterdir()
                       if p.is_file() and p.name not in imported)
        for x in stray:
            problems.append(f"{slug}: drawable {x} is not a studio asset")
    return imported, problems


# ---------------------------------------------------------------------
# face specification
# ---------------------------------------------------------------------
def face_toml(slug: str, meta: dict, platform: dict) -> str:
    ap = platform["aperture"]
    r = platform["horizon_field_radius_px"]
    fw = int(-(-r * 2 // 1))
    fw += fw % 2
    fx, fy = ap["cx"] - fw // 2, ap["cy"] - fw // 2
    prof = platform["motion_profiles"][platform["default_profile"]]
    ro = platform["readouts"]
    chars = "\n".join(
        f'"{c}" = ["{m["resource"]}", {m["width"]}]'
        for c, m in meta["bitmap_font_characters"].items())

    def box(key):
        b = ro[key]["box"]
        return f"{{x = {b[0]}, y = {b[1]}, width = {b[2]}, height = {b[3]}}}"

    return f'''# {meta["title"]} — ATTITUDE SQUADRON.
#
# GENERATED by tools/squadron_scaffold.py from the studio collection
# manifest. Edit the studio platform, not this file.
#
# Regenerate XML:  python3 tools/generate_face.py squadron-{slug}
#
# {meta["blurb"]}
#
# The whole collection shares this component list, these data bindings and
# this horizon motion contract. A variant differs only in artwork.
#
# Motion profiles: damped 14/14, proposed 22/26, assertive 30/34, roll-only,
# static. PROPOSED is the provisional default; changing it means editing
# the two gains in z00_horizon and regenerating. No artwork changes.

[face]
slug = "squadron-{slug}"
width = 480
height = 480
wff_version = 4
clock_type = "ANALOG"
preview_time = "10:09:35"
background_color = "#FF000000"

[identity]
package = "{package(slug)}"
version_code = 1
version_name = "{VERSION_NAME}"

[[fonts]]
name = "sqd"
height = {platform["bitmap_font"]["height"]}
[fonts.characters]
{chars}

# ---- scene, document order = z-order ---------------------------------

[[components]]
type = "horizon_field"
name = "z00_horizon"
resource = "sq_horizon"
box = {{x = {fx}, y = {fy}, width = {fw}, height = {fw}}}
roll_gain_deg = {prof["roll_deg"]}
pitch_gain_px = {prof["pitch_px"]}
roll_clamp_deg = 45
pitch_clamp_deg = 40
aod = {{alpha = 0, duration = 0.4, offset = 0.0, interpolation = "EASE_OUT"}}

# AOD neutrality is structural: the moving field is hidden and this frozen
# one replaces it, so nothing visible in ambient carries a sensor transform.
[[components]]
type = "static_image"
name = "z01_horizon_aod"
resource = "sq_horizon_aod"
box = {{x = {fx}, y = {fy}, width = {fw}, height = {fw}}}
alpha = 0
aod = {{alpha = 255, duration = 0.4, offset = 0.0, interpolation = "EASE_IN"}}

# Opaque everywhere but the aperture — this is what occludes the field.
[[components]]
type = "static_image"
name = "z02_plate"
resource = "sq_dial"
box = {{x = 0, y = 0, width = 480, height = 480}}
aod = {{alpha = 0, duration = 0.4, offset = 0.0, interpolation = "EASE_OUT"}}

[[components]]
type = "static_image"
name = "z03_plate_aod"
resource = "sq_dial_aod"
box = {{x = 0, y = 0, width = 480, height = 480}}
alpha = 0
aod = {{alpha = 255, duration = 0.4, offset = 0.0, interpolation = "EASE_IN"}}

[[components]]
type = "battery_needle"
name = "z10_resv"
resource = "sq_battery_needle"
box = {{x = 0, y = 0, width = 480, height = 480}}
start_deg = 298.0
sweep_deg = 124.0
aod = {{alpha = 0, duration = 0.4, offset = 0.1}}

# ---- live data. No fabricated fallbacks: an absent or unpermitted sensor
# ---- reads 0, which is the project's established fail-safe.

[[components]]
type = "text_line"
name = "z20_batt"
box = {box("battery")}
font = "sqd"
size = {ro["battery"]["size"]}
color = "#E2E7EC"
template = "%d%%"
expressions = ["[BATTERY_PERCENT]"]
align = "CENTER"
aod = {{alpha = 120, duration = 0.4, offset = 0.2}}

[[components]]
type = "date_text"
name = "z21_date"
box = {box("date")}
font = "sqd"
size = {ro["date"]["size"]}
color = "#E2E7EC"
template = "%d"
expression = "[DAY]"
aod = {{alpha = 140, duration = 0.4, offset = 0.2}}

[[components]]
type = "text_line"
name = "z22_steps"
box = {box("steps")}
font = "sqd"
size = {ro["steps"]["size"]}
color = "#E2E7EC"
template = "%d"
expressions = ["[STEP_COUNT]"]
align = "CENTER"
aod = {{alpha = 0, duration = 0.4, offset = 0.2}}

[[components]]
type = "text_line"
name = "z23_hr"
box = {box("hr")}
font = "sqd"
size = {ro["hr"]["size"]}
color = "#E2E7EC"
template = "%d"
expressions = ["[HEART_RATE]"]
align = "CENTER"
aod = {{alpha = 0, duration = 0.4, offset = 0.2}}

# ---- the signature: sculpted propeller-blade hands --------------------

[[components]]
type = "analog_hand"
name = "z30_hour"
resource = "sq_hand_hour"
which = "hour"
aod = {{alpha = 0, duration = 0.4, offset = 0.0, interpolation = "EASE_OUT"}}

[[components]]
type = "analog_hand"
name = "z31_minute"
resource = "sq_hand_minute"
which = "minute"
aod = {{alpha = 0, duration = 0.4, offset = 0.0, interpolation = "EASE_OUT"}}

[[components]]
type = "seconds_rotor"
name = "z32_second"
resource = "sq_hand_second"
box = {{x = 0, y = 0, width = 480, height = 480}}
aod = {{alpha = 0, duration = 0.4, offset = 0.0}}

[[components]]
type = "analog_hand"
name = "z34_hour_aod"
resource = "sq_hand_hour_aod"
which = "hour"
alpha = 0
aod = {{alpha = 255, duration = 0.4, offset = 0.0, interpolation = "EASE_IN"}}

[[components]]
type = "analog_hand"
name = "z35_minute_aod"
resource = "sq_hand_minute_aod"
which = "minute"
alpha = 0
aod = {{alpha = 255, duration = 0.4, offset = 0.0, interpolation = "EASE_IN"}}

# The pinion is the propeller spinner.
[[components]]
type = "static_image"
name = "z40_pinion"
resource = "sq_pinion"
box = {{x = 0, y = 0, width = 480, height = 480}}
aod = {{alpha = 0, duration = 0.4, offset = 0.0, interpolation = "EASE_OUT"}}

[[components]]
type = "static_image"
name = "z41_pinion_aod"
resource = "sq_pinion_aod"
box = {{x = 0, y = 0, width = 480, height = 480}}
alpha = 0
aod = {{alpha = 255, duration = 0.4, offset = 0.0, interpolation = "EASE_IN"}}
'''


README = """# {title}

{blurb}

Part of **ATTITUDE SQUADRON** — a collection of watch faces rooted in
vintage prop-fighter aircraft. Every face in the family shares one platform:
the same architecture, complication logic, live data bindings and horizon
motion contract. This variant differs in artwork and identity only.

**Development build, not a release candidate.** Debug signing only, no
bundle, no store metadata, package namespaced `.dev`.

| | |
|---|---|
| Package | `{pkg}` |
| Version | `{version}` (versionCode 1) |
| Dial mark | {brand} / {brand2} |
| Markers | {markers} |
| Horizon window | {window} |
| Dial texture | {texture} |
| Weathering | {wear}% |

## The signature

The hour and minute hands are sculpted propeller blades — a round shank with
collar rivets, an asymmetric paddle planform with the axis at 32% chord, a
hard camber split between lit and shaded faces, a lume stripe on the lit
face, a painted tip warning band and an opposed counterweight blade. The
pinion is the spinner hub.

## Regenerating

Artwork authority is the studio repository. Do not hand-edit `res/drawable`
or `res/raw/watchface.xml`; both are generated and both are checked.

```bash
python3 tools/squadron_scaffold.py --only {slug}
python3 tools/generate_face.py squadron-{slug}
tools/build_face.sh squadron-{slug}
```
"""


# Fields whose disagreement means the record is describing a different
# studio state than the one that produced these bytes.
LINEAGE_KEYS = ("schema", "collection", "flagship", "public_variants",
                "studio_repository", "studio_branch", "studio_commit",
                "studio_manifest_sha256", "platform")
VARIANT_KEYS = ("title", "public", "package")


def compare_import(committed: dict, produced: dict) -> list[str]:
    """Every way the committed import can disagree with the studio.

    Compares the COMPLETE authoritative document. An earlier version
    compared only the variant map, so a stale `studio_commit` — a record
    naming an authority that did not produce these bytes — passed silently.
    Lineage fields are exactly the ones that must fail loudest, because the
    artwork can be byte-correct while the provenance claim is false.
    """
    drift: list[str] = []
    for key in LINEAGE_KEYS:
        if committed.get(key) != produced.get(key):
            drift.append(f"{key}: committed {committed.get(key)!r} != "
                         f"studio {produced.get(key)!r}")
    cur_v = committed.get("variants", {})
    new_v = produced.get("variants", {})
    for slug in sorted(set(cur_v) | set(new_v)):
        if slug not in cur_v:
            drift.append(f"variants[{slug}]: missing from the record")
            continue
        if slug not in new_v:
            drift.append(f"variants[{slug}]: recorded but no longer in the "
                         "studio collection")
            continue
        a, b = cur_v[slug], new_v[slug]
        for field in VARIANT_KEYS:
            if a.get(field) != b.get(field):
                drift.append(f"variants[{slug}].{field}: {a.get(field)!r} "
                             f"!= {b.get(field)!r}")
        ra, rb = a.get("resources", {}), b.get("resources", {})
        for name in sorted(set(ra) | set(rb)):
            if ra.get(name) != rb.get(name):
                drift.append(f"variants[{slug}].resources[{name}] differs "
                             "from the studio export")
    return drift


def build_import_document(studio: Path, slugs=None) -> dict:
    """The authoritative import document this studio checkout implies."""
    collection = json.loads((studio / "phase3-squadron"
                             / "SQUADRON_MANIFEST.json").read_text())
    commit = subprocess.run(["git", "-C", str(studio), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    record = {}
    for slug in (slugs or collection["variants"]):
        meta = collection["variants"][slug]
        imported, _ = import_assets(slug, meta, studio, slug_dir(slug), True)
        record[slug] = {"title": meta["title"], "public": meta["public"],
                        "package": package(slug), "resources": imported}
    return {
        "schema": "agenor.squadron-import/1",
        "collection": collection["collection"],
        "flagship": collection["flagship"],
        "public_variants": collection["public_variants"],
        "studio_repository": "xsytrance/AGENOR-Horology",
        "studio_branch": "phase-3/attitude-squadron-collection",
        "studio_commit": commit,
        "studio_manifest_sha256": sha256(studio / "phase3-squadron"
                                         / "SQUADRON_MANIFEST.json"),
        "platform": collection["platform"],
        "variants": record,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--studio", default=str(STUDIO_DEFAULT))
    ap.add_argument("--only")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    studio = Path(args.studio).resolve()
    mpath = studio / "phase3-squadron" / "SQUADRON_MANIFEST.json"
    if not mpath.exists():
        print(f"ERROR studio manifest not found at {mpath}", file=sys.stderr)
        return 2
    collection = json.loads(mpath.read_text())
    platform = collection["platform"]
    slugs = [args.only] if args.only else list(collection["variants"])

    commit = subprocess.run(["git", "-C", str(studio), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    problems, record = [], {}

    for slug in slugs:
        meta = collection["variants"][slug]
        d = slug_dir(slug) if args.check else scaffold_project(slug, meta)
        imported, probs = import_assets(slug, meta, studio, d, args.check)
        problems += probs
        spec = face_toml(slug, meta, platform)
        spec_path = d / "engine" / "face.toml"
        if args.check:
            if not spec_path.exists() or spec_path.read_text() != spec:
                problems.append(f"{slug}: engine/face.toml differs from the "
                                "scaffold output")
        else:
            spec_path.write_text(spec)
            (d / "README.md").write_text(README.format(
                title=meta["title"], blurb=meta["blurb"], slug=slug,
                pkg=package(slug), version=VERSION_NAME,
                brand=meta["brand"], brand2=meta["brand2"],
                markers=meta["markers"], window=meta["window"],
                texture=meta["texture"], wear=int(meta["wear"] * 100)))
        record[slug] = {
            "title": meta["title"], "public": meta["public"],
            "package": package(slug), "resources": imported,
        }

    if problems:
        for p in problems:
            print(f"ERROR {p}", file=sys.stderr)
        return 1

    out = REPO / "watchfaces" / "SQUADRON_IMPORT.json"
    doc = {
        "schema": "agenor.squadron-import/1",
        "collection": collection["collection"],
        "flagship": collection["flagship"],
        "public_variants": collection["public_variants"],
        "studio_repository": "xsytrance/AGENOR-Horology",
        "studio_branch": "phase-3/attitude-squadron-collection",
        "studio_commit": commit,
        "studio_manifest_sha256": sha256(mpath),
        "platform": platform,
        "variants": record,
    }
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not out.exists():
            print("ERROR no committed SQUADRON_IMPORT.json", file=sys.stderr)
            return 1
        cur = json.loads(out.read_text())
        drift = compare_import(cur, doc)
        if drift:
            for x in drift:
                print(f"ERROR {x}", file=sys.stderr)
            print(f"ERROR {len(drift)} lineage/content difference(s); the "
                  "committed import does not describe this studio checkout",
                  file=sys.stderr)
            return 1
        if cur != doc:
            print("ERROR SQUADRON_IMPORT.json differs from the scaffold "
                  "output in a field the field-by-field comparison does not "
                  "cover — refusing to pass on an unexplained difference",
                  file=sys.stderr)
            return 1
        print(f"OK: complete import document matches studio {commit[:12]} "
              f"({len(record)} variants)")
        return 0
    out.write_text(text)
    print(f"scaffolded {len(record)} variants from studio {commit[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
