#!/usr/bin/env python3
"""Package a built watchface into releases/<slug>/ — safely.

Guarantees (ADR-006 as amended by the Phase-1 review):
  * the existing `current` release is ARCHIVED to releases/<slug>/v<its version>/
    before anything replaces it — nothing is ever overwritten silently;
  * an existing immutable v<X.Y.Z> directory is never touched unless
    --force-rearchive is given (documented, destructive, prints loudly);
  * the new APK's package/versionCode/versionName (read via aapt2) must match
    the source project's Gradle metadata, or packaging refuses;
  * packaging the same versionName that is already `current` refuses unless
    --force-same-version (dev-only; replaces current WITHOUT archiving);
  * previews are discovered across app/src/main/res/drawable*/ — zero
    candidates is an error (no stale preview is silently retained), multiple
    *distinct* candidates is an ambiguity error (identical copies are fine);
  * the manifest is regenerated afterwards (schema 2, channel-safe).

Usage:
  python3 tools/package_release.py <slug> [--repo-root PATH]
        [--force-same-version] [--force-rearchive] [--no-preview]
"""

import argparse
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg: str) -> None:
    sys.exit(f"ERROR: {msg}")


def find_aapt2() -> str:
    sdk = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/Android/Sdk")
    candidates = sorted(glob.glob(f"{sdk}/build-tools/*/aapt2"))
    if not candidates:
        die("aapt2 not found — set ANDROID_HOME (need build-tools)")
    return candidates[-1]


def apk_badging(aapt2: str, apk: Path) -> dict:
    r = subprocess.run([aapt2, "dump", "badging", str(apk)],
                       capture_output=True, text=True)
    m = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'",
                  r.stdout)
    if r.returncode != 0 or not m:
        die(f"aapt2 could not read {apk}")
    return {"package": m.group(1), "versionCode": m.group(2), "versionName": m.group(3)}


def gradle_meta(gradle: Path) -> dict:
    t = gradle.read_text()
    meta = {}
    for key, pat in [("applicationId", r'applicationId\s*=\s*"([^"]+)"'),
                     ("versionCode", r"versionCode\s*=\s*(\d+)"),
                     ("versionName", r'versionName\s*=\s*"([^"]+)"')]:
        m = re.search(pat, t)
        if not m:
            die(f"{key} not found in {gradle}")
        meta[key] = m.group(1)
    return meta


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_preview(face: Path, allow_missing: bool) -> Path | None:
    exts = ("png", "jpg", "jpeg", "webp")
    candidates = []
    for d in sorted(face.glob("app/src/main/res/drawable*")):
        for ext in exts:
            candidates.extend(sorted(d.glob(f"preview.{ext}")))
    if not candidates:
        if allow_missing:
            print("WARN: no preview found (--no-preview given) — release will "
                  "carry no preview image")
            return None
        die("no preview.(png|jpg|jpeg|webp) found under app/src/main/res/drawable*/ "
            "— generate one, or pass --no-preview to release without "
            "(a stale preview is never silently reused)")
    distinct = {sha256(c): c for c in candidates}
    if len(distinct) > 1:
        listing = "\n  ".join(str(c) for c in candidates)
        die(f"ambiguous previews (multiple distinct images):\n  {listing}\n"
            "Remove or reconcile them so exactly one preview is canonical.")
    return candidates[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--force-same-version", action="store_true",
                    help="dev-only: replace current in place when the version was not bumped")
    ap.add_argument("--force-rearchive", action="store_true",
                    help="DESTRUCTIVE: allow overwriting an existing immutable vX.Y.Z archive")
    ap.add_argument("--no-preview", action="store_true",
                    help="allow releasing without a preview image")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    face = root / "watchfaces" / args.slug
    if not face.is_dir():
        die(f"unknown face '{args.slug}' — available: "
            f"{', '.join(sorted(p.name for p in (root/'watchfaces').iterdir()))}")
    built = face / "app/build/outputs/apk/debug/app-debug.apk"
    if not built.exists():
        die(f"no built APK at {built} — run tools/build_face.sh {args.slug} first")

    aapt2 = find_aapt2()
    apk_meta = apk_badging(aapt2, built)
    src_meta = gradle_meta(face / "app/build.gradle.kts")
    for a, s in (("package", "applicationId"), ("versionCode", "versionCode"),
                 ("versionName", "versionName")):
        if apk_meta[a] != src_meta[s]:
            die(f"built APK {a}={apk_meta[a]} does not match source {s}={src_meta[s]} "
                "— rebuild from current source before packaging")
    new_version = apk_meta["versionName"]
    preview = discover_preview(face, args.no_preview)

    rel = root / "releases" / args.slug
    current = rel / "current"
    if current.exists():
        cur_apks = sorted(current.glob("*.apk"))
        if len(cur_apks) != 1:
            die(f"{current} contains {len(cur_apks)} APKs — repair before packaging")
        cur_meta = apk_badging(aapt2, cur_apks[0])
        old_version = cur_meta["versionName"]
        if old_version == new_version:
            if not args.force_same_version:
                die(f"current release is already versionName={old_version} — bump the "
                    "version, or pass --force-same-version to replace current in "
                    "place (no archive will be made)")
            print(f"WARN: --force-same-version — replacing current v{old_version} "
                  "in place, previous bytes will be LOST from the working tree")
            shutil.rmtree(current)
        else:
            archive = rel / f"v{old_version}"
            if archive.exists():
                if not args.force_rearchive:
                    die(f"archive {archive} already exists — immutable versions are "
                        "never overwritten (pass --force-rearchive only if you truly "
                        "must replace it)")
                print(f"WARN: --force-rearchive — overwriting immutable {archive}")
                shutil.rmtree(archive)
            current.rename(archive)
            import datetime as dt
            print(f"archived previous current (v{old_version}) -> {archive.relative_to(root)}")
            # record archive date for the manifest to carry over
            stamp = archive / ".archived_on"
            stamp.write_text(dt.date.today().isoformat() + "\n")

    current.mkdir(parents=True)
    shutil.copy2(built, current / f"{args.slug}.apk")
    if preview is not None:
        shutil.copy2(preview, current / f"preview{preview.suffix.lower()}")

    subprocess.run([sys.executable, str(root / "tools/gen_release_manifest.py"),
                    "--repo-root", str(root)], check=True)
    print(f"packaged {args.slug} v{new_version} -> {current.relative_to(root)}")
    print("Next: set source_commit_of_build in releases/MANIFEST.json (or via "
          "RELEASE.md), run tools/validate.py, then commit.")


if __name__ == "__main__":
    main()
