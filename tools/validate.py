#!/usr/bin/env python3
"""AGENOR repo-wide validation.

Checks (severity ERROR fails the run; WARN is reported but passes):
  source:    every watchfaces/<slug> has the required project files
  wff:       watchface.xml parses as XML
  metadata:  applicationId/versionCode/versionName present; no duplicate IDs
  releases:  every release has APK + RELEASE.md + manifest entry; checksum match;
             APK package matches the source project's applicationId
  previews:  releases missing preview images (WARN)
  secrets:   no keystores/credential files anywhere tracked
  paths:     no absolute /home/ paths in python/gradle/xml source
             (external ~/AI donor refs are WARN, documented provenance)
  hygiene:   no build/ or .gradle/ dirs tracked; no unexpected binaries at root
  size:      tracked files > 8 MB (WARN), > 40 MB (ERROR)

Usage: python3 tools/validate.py   (exit 0 = no ERRORs)
"""

import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
issues: list[tuple[str, str]] = []  # (severity, message)


def err(msg: str) -> None:
    issues.append(("ERROR", msg))


def warn(msg: str) -> None:
    issues.append(("WARN", msg))


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return [ROOT / line for line in out.splitlines()]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_sources() -> dict[str, dict]:
    faces = {}
    for d in sorted((ROOT / "watchfaces").iterdir()):
        if not d.is_dir():
            continue
        slug = d.name
        required = ["settings.gradle.kts", "app/build.gradle.kts",
                    "app/src/main/AndroidManifest.xml",
                    "app/src/main/res/raw/watchface.xml", "gradlew", "README.md"]
        for r in required:
            if not (d / r).exists():
                err(f"source[{slug}]: missing {r}")
        wff = d / "app/src/main/res/raw/watchface.xml"
        if wff.exists():
            try:
                ET.parse(wff)
            except ET.ParseError as e:
                err(f"wff[{slug}]: watchface.xml does not parse: {e}")
        gradle = d / "app/build.gradle.kts"
        meta = {}
        if gradle.exists():
            t = gradle.read_text()
            for key, pat in [("applicationId", r'applicationId\s*=\s*"([^"]+)"'),
                             ("versionCode", r"versionCode\s*=\s*(\d+)"),
                             ("versionName", r'versionName\s*=\s*"([^"]+)"')]:
                m = re.search(pat, t)
                if m:
                    meta[key] = m.group(1)
                else:
                    err(f"metadata[{slug}]: {key} not found in app/build.gradle.kts")
        faces[slug] = meta
    ids: dict[str, str] = {}
    for slug, meta in faces.items():
        app_id = meta.get("applicationId")
        if app_id:
            if app_id in ids:
                err(f"metadata: duplicate applicationId {app_id} ({ids[app_id]}, {slug})")
            ids[app_id] = slug
    return faces


def check_releases(faces: dict[str, dict]) -> None:
    man_path = ROOT / "releases/MANIFEST.json"
    if not man_path.exists():
        err("releases: MANIFEST.json missing")
        return
    manifest = {e["slug"]: e for e in json.loads(man_path.read_text())["releases"]}
    for d in sorted((ROOT / "releases").iterdir()):
        if not d.is_dir():
            continue
        slug = d.name
        cur = d / "current"
        apks = list(cur.glob("*.apk"))
        if not apks:
            err(f"releases[{slug}]: no APK in current/")
            continue
        apk = apks[0]
        if not (cur / "RELEASE.md").exists():
            err(f"releases[{slug}]: RELEASE.md missing")
        entry = manifest.get(slug)
        if not entry:
            err(f"releases[{slug}]: not in MANIFEST.json (regenerate)")
        elif entry["sha256"] != sha256(apk):
            err(f"releases[{slug}]: checksum mismatch vs MANIFEST.json (regenerate)")
        if not list(cur.glob("preview.*")):
            warn(f"releases[{slug}]: no preview image")
        if slug not in faces:
            err(f"releases[{slug}]: APK present but no source project in watchfaces/")
        elif entry and faces[slug].get("applicationId") not in (None, entry["package"]):
            err(f"releases[{slug}]: APK package {entry['package']} != source "
                f"applicationId {faces[slug]['applicationId']}")
    for slug in faces:
        if not (ROOT / "releases" / slug).exists():
            warn(f"source[{slug}]: no release yet (source-only face)")


SECRET_PATTERNS = re.compile(r"\.(jks|keystore|p12|pepk|pem)$|keystore\.properties$")
TEXT_EXT = {".py", ".kts", ".xml", ".gradle", ".properties", ".sh", ".md"}


def check_files(files: list[Path]) -> None:
    for f in files:
        rel = f.relative_to(ROOT)
        s = str(rel)
        if SECRET_PATTERNS.search(s):
            err(f"secrets: {rel} looks like signing/credential material")
        if re.search(r"(^|/)(build|\.gradle|\.kotlin)/", s):
            err(f"hygiene: generated/cache path tracked: {rel}")
        if not f.exists():
            continue
        size = f.stat().st_size
        if size > 40 * 1024 * 1024:
            err(f"size: {rel} is {size/1e6:.0f} MB (>40 MB)")
        elif size > 8 * 1024 * 1024:
            warn(f"size: {rel} is {size/1e6:.1f} MB (>8 MB)")
        if f.suffix in TEXT_EXT and "docs/" not in s and s != "tools/validate.py":
            try:
                t = f.read_text(errors="ignore")
            except OSError:
                continue
            for m in re.finditer(r"/home/\w+/[^\s'\"]*", t):
                path = m.group(0)
                if "/AI/" in path or "ComfyUI" in path:
                    warn(f"paths: {rel}: external donor ref {path} (documented provenance)")
                else:
                    err(f"paths: {rel}: absolute local path {path}")
    for f in ROOT.iterdir():
        if f.is_file() and f.suffix in {".apk", ".aab", ".png", ".jpg"}:
            err(f"hygiene: binary at repo root: {f.name} (belongs in releases/)")


def main() -> None:
    files = tracked_files()
    faces = check_sources()
    check_releases(faces)
    check_files(files)
    errors = [m for s, m in issues if s == "ERROR"]
    warns = [m for s, m in issues if s == "WARN"]
    for s, m in issues:
        print(f"{s:5} {m}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s) — "
          f"{len(faces)} source faces checked")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
