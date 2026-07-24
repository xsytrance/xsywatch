#!/usr/bin/env python3
"""AGENOR repo-wide validation.

ERROR fails the run (exit 1); WARN is reported but passes.

  source:    every watchfaces/<slug> has the required project files
  wff:       watchface.xml parses as XML
  metadata:  applicationId/versionCode/versionName present; no duplicate IDs
  releases:  every (slug, channel) dir has exactly one APK + RELEASE.md +
             manifest entry; manifest identity is (slug, channel) and unique;
             APK metadata is read directly via aapt2 and compared against the
             manifest AND the source project (package always; versions for
             the 'current' channel); checksums match; versioned channel dirs
             match the APK versionName inside them
  previews:  releases missing preview images (WARN)
  licenses:  every tracked font/HDRI/etc (ASSET_EXTS) must have an entry in
             docs/asset-licenses.json with matching sha256, a license id,
             permission flags, and an existing notice file when required;
             stale/missing entries are ERRORs
  secrets:   no keystores/credential files tracked
  paths:     no absolute /home/ paths in source (external AI donor refs WARN)
  hygiene:   no build/.gradle dirs tracked; no binaries at repo root
  size:      tracked files > 8 MB WARN, > 40 MB ERROR

Usage: python3 tools/validate.py [--repo-root PATH]
"""

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

issues: list[tuple[str, str]] = []


def err(msg: str) -> None:
    issues.append(("ERROR", msg))


def warn(msg: str) -> None:
    issues.append(("WARN", msg))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_aapt2() -> str | None:
    sdk = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/Android/Sdk")
    candidates = sorted(glob.glob(f"{sdk}/build-tools/*/aapt2"))
    return candidates[-1] if candidates else None


def apk_badging(aapt2: str, apk: Path) -> dict | None:
    r = subprocess.run([aapt2, "dump", "badging", str(apk)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    m = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", r.stdout)
    tgt = re.search(r"targetSdkVersion:'([^']+)'", r.stdout)
    if not m:
        return None
    return {"package": m.group(1), "versionCode": int(m.group(2)),
            "versionName": m.group(3), "targetSdk": int(tgt.group(1)) if tgt else None}


def check_sources(root: Path) -> dict[str, dict]:
    faces: dict[str, dict] = {}
    wf_root = root / "watchfaces"
    if not wf_root.is_dir():
        err("source: watchfaces/ missing")
        return faces
    for d in sorted(p for p in wf_root.iterdir() if p.is_dir()):
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
        meta: dict = {}
        gradle = d / "app/build.gradle.kts"
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


def check_releases(root: Path, faces: dict[str, dict], aapt2: str | None) -> None:
    rel_root = root / "releases"
    if not rel_root.is_dir():
        warn("releases: no releases/ directory")
        return
    man_path = rel_root / "MANIFEST.json"
    if not man_path.exists():
        err("releases: MANIFEST.json missing")
        return
    data = json.loads(man_path.read_text())
    if data.get("schema") != 2 or "faces" not in data:
        err("releases: MANIFEST.json is not schema 2 (channel-safe) — regenerate")
        return
    manifest: dict[tuple, dict] = {}
    for slug, face in data["faces"].items():
        for channel, e in face.get("channels", {}).items():
            key = (slug, channel)
            if key in manifest:
                err(f"releases: duplicate manifest identity {key}")
            manifest[key] = e

    seen: set[tuple] = set()
    for face_dir in sorted(d for d in rel_root.iterdir() if d.is_dir()):
        slug = face_dir.name
        if slug not in faces:
            err(f"releases[{slug}]: APK present but no source project in watchfaces/")
        for chan_dir in sorted(d for d in face_dir.iterdir() if d.is_dir()):
            channel = chan_dir.name
            key = (slug, channel)
            seen.add(key)
            apks = sorted(chan_dir.glob("*.apk"))
            if len(apks) != 1:
                err(f"releases[{slug}/{channel}]: expected exactly 1 APK, found {len(apks)}")
                continue
            apk = apks[0]
            if not (chan_dir / "RELEASE.md").exists():
                err(f"releases[{slug}/{channel}]: RELEASE.md missing")
            if not sorted(chan_dir.glob("preview.*")):
                warn(f"releases[{slug}/{channel}]: no preview image")
            entry = manifest.get(key)
            if not entry:
                err(f"releases[{slug}/{channel}]: not in MANIFEST.json (regenerate)")
                continue
            if entry["sha256"] != sha256(apk):
                err(f"releases[{slug}/{channel}]: checksum mismatch vs MANIFEST.json")
            # Real APK metadata via aapt2 — the authority.
            if aapt2 is None:
                err("releases: aapt2 not found — APK metadata cannot be verified "
                    "(install Android build-tools / set ANDROID_HOME)")
                continue
            b = apk_badging(aapt2, apk)
            if b is None:
                err(f"releases[{slug}/{channel}]: aapt2 could not read {apk.name}")
                continue
            for field in ("package", "versionCode", "versionName", "targetSdk"):
                if entry.get(field) != b[field]:
                    err(f"releases[{slug}/{channel}]: manifest {field}="
                        f"{entry.get(field)!r} but APK says {b[field]!r}")
            src = faces.get(slug, {})
            if src.get("applicationId") and b["package"] != src["applicationId"]:
                err(f"releases[{slug}/{channel}]: APK package {b['package']} != "
                    f"source applicationId {src['applicationId']}")
            if channel == "current":
                for f_src, f_apk in (("versionCode", "versionCode"), ("versionName", "versionName")):
                    if src.get(f_src) and str(b[f_apk]) != str(src[f_src]):
                        err(f"releases[{slug}/current]: APK {f_apk}={b[f_apk]} != "
                            f"source {f_src}={src[f_src]} (source moved on without a release?)")
            else:
                if channel != f"v{b['versionName']}":
                    err(f"releases[{slug}/{channel}]: channel dir does not match "
                        f"APK versionName '{b['versionName']}'")
    for key in manifest:
        if key not in seen:
            err(f"releases: manifest entry {key} has no directory on disk")
    for slug in faces:
        if not (rel_root / slug).exists():
            warn(f"source[{slug}]: no release yet (source-only face)")


ASSET_EXTS = {".ttf", ".otf", ".woff", ".woff2", ".hdr", ".exr"}


def check_asset_licenses(root: Path, files: list[Path]) -> None:
    inv_path = root / "docs/asset-licenses.json"
    tracked_assets = {f for f in files
                      if f.suffix.lower() in ASSET_EXTS and f.exists()}
    if not inv_path.exists():
        if tracked_assets:
            err(f"licenses: {len(tracked_assets)} tracked asset files but "
                "docs/asset-licenses.json is missing")
        return
    inv = json.loads(inv_path.read_text())
    entries = {root / a["path"]: a for a in inv.get("assets", [])}
    for f in sorted(tracked_assets):
        rel = f.relative_to(root)
        a = entries.get(f)
        if a is None:
            err(f"licenses: {rel} has no entry in docs/asset-licenses.json — "
                "record provenance + license before committing third-party assets")
            continue
        if a.get("sha256") != sha256(f):
            err(f"licenses: {rel} bytes differ from the inventoried sha256 — "
                "re-verify provenance and update the entry")
        if not a.get("license"):
            err(f"licenses: {rel} entry has no license identifier")
        for flag in ("redistribution_permitted", "commercial_use_permitted"):
            if not isinstance(a.get(flag), bool):
                err(f"licenses: {rel} entry missing boolean {flag}")
        notice = a.get("notice_file")
        if notice:
            if not (root / notice).exists():
                err(f"licenses: {rel} notice file {notice} does not exist")
        elif a.get("license") == "OFL-1.1":
            err(f"licenses: {rel} is OFL-1.1 but has no notice_file "
                "(OFL requires the license text to accompany distribution)")
    for path in entries:
        if path not in tracked_assets:
            err(f"licenses: stale inventory entry for {path.relative_to(root)} "
                "(file not tracked) — remove or fix the entry")


SECRET_PATTERNS = re.compile(r"\.(jks|keystore|p12|pepk|pem)$|keystore\.properties$")
TEXT_EXT = {".py", ".kts", ".xml", ".gradle", ".properties", ".sh", ".md"}


def check_files(root: Path, files: list[Path]) -> None:
    for f in files:
        rel = f.relative_to(root)
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
    for f in root.iterdir():
        if f.is_file() and f.suffix in {".apk", ".aab", ".png", ".jpg"}:
            err(f"hygiene: binary at repo root: {f.name} (belongs in releases/)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()

    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                         text=True, check=True).stdout
    files = [root / line for line in out.splitlines()]

    aapt2 = find_aapt2()
    faces = check_sources(root)
    check_releases(root, faces, aapt2)
    check_asset_licenses(root, files)
    check_files(root, files)

    errors = [m for s, m in issues if s == "ERROR"]
    warns = [m for s, m in issues if s == "WARN"]
    for s, m in issues:
        print(f"{s:5} {m}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s) — "
          f"{len(faces)} source faces checked, aapt2={'yes' if aapt2 else 'MISSING'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
