#!/usr/bin/env python3
"""Import the MERIDIAN V1 studio export into this face's res/drawable.

    python3 watchfaces/attitude-meridian/tools/import_studio_export.py
    python3 .../import_studio_export.py --check     # verify, write nothing

The studio repository is the authority for MERIDIAN artwork. This tool
copies its exported assets in and records their SHA-256 values, so drift
between the studio export and the installed face is detectable rather than
discovered on the wrist.

Nothing here generates art. If a hash does not match the studio manifest
the import fails; regenerate in the studio, do not patch pixels here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

FACE = Path(__file__).resolve().parents[1]
REPO = FACE.parents[1]
DRAWABLE = FACE / "app/src/main/res/drawable"
STUDIO_DEFAULT = Path.home() / "AGENOR-Horology"
MANIFEST = FACE / "engine" / "STUDIO_IMPORT.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def studio_commit(studio: Path) -> str:
    import subprocess
    r = subprocess.run(["git", "-C", str(studio), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--studio", default=str(STUDIO_DEFAULT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    studio = Path(args.studio).resolve()
    export = studio / "phase2-meridian" / "export"
    studio_manifest_path = (studio / "phase2-meridian"
                            / "MERIDIAN_V1_ASSET_MANIFEST.json")
    if not export.is_dir():
        print(f"ERROR: studio export not found at {export}", file=sys.stderr)
        return 2
    studio_manifest = json.loads(studio_manifest_path.read_text())
    declared = studio_manifest["export_assets"]

    imported: dict[str, dict] = {}
    problems: list[str] = []
    DRAWABLE.mkdir(parents=True, exist_ok=True)

    for rel, meta in sorted(declared.items()):
        src = export / rel
        if not src.exists():
            problems.append(f"missing from studio export: {rel}")
            continue
        actual = sha256(src)
        if actual != meta["sha256"]:
            problems.append(f"studio export {rel} does not match the studio "
                            f"manifest ({actual[:12]} != {meta['sha256'][:12]})")
            continue
        # Android resource names: flat directory, lowercase, no subfolders.
        dest = DRAWABLE / Path(rel).name
        if args.check:
            if not dest.exists() or sha256(dest) != actual:
                problems.append(f"imported resource drifted from studio: {rel}")
        else:
            shutil.copy2(src, dest)
        imported[dest.name] = {"sha256": actual, "bytes": meta["bytes"],
                               "width": meta["width"], "height": meta["height"],
                               "studio_path": f"phase2-meridian/export/{rel}"}

    # The launcher/picker preview is the studio's own normal render, copied
    # rather than re-rendered so what the picker shows is what was reviewed.
    prev_src = studio / "phase2-meridian/review/MERIDIAN_V1_NORMAL.png"
    prev_meta = studio_manifest["review_images"]["MERIDIAN_V1_NORMAL.png"]
    if sha256(prev_src) != prev_meta["sha256"]:
        problems.append("MERIDIAN_V1_NORMAL.png does not match the studio "
                        "manifest")
    else:
        dest = DRAWABLE / "preview.png"
        if args.check:
            if not dest.exists() or sha256(dest) != prev_meta["sha256"]:
                problems.append("preview.png drifted from the studio render")
        else:
            shutil.copy2(prev_src, dest)
        imported["preview.png"] = {
            "sha256": prev_meta["sha256"], "bytes": prev_meta["bytes"],
            "width": prev_meta["width"], "height": prev_meta["height"],
            "studio_path": "phase2-meridian/review/MERIDIAN_V1_NORMAL.png"}

    stray = sorted(p.name for p in DRAWABLE.iterdir()
                   if p.is_file() and p.name not in imported
)
    if stray:
        problems.append(f"res/drawable holds files the studio did not "
                        f"export: {stray}")

    if problems:
        for p in problems:
            print(f"ERROR {p}", file=sys.stderr)
        return 1

    record = {
        "schema": "agenor.meridian-studio-import/1",
        "studio_repository": "xsytrance/AGENOR-Horology",
        "studio_branch": "phase-2/attitude-meridian-fast-track",
        "studio_commit": studio_commit(studio),
        "studio_manifest_sha256": sha256(studio_manifest_path),
        "studio_asset_manifest_schema": studio_manifest["schema"],
        "bitmap_font": studio_manifest["bitmap_font"],
        "readouts": studio_manifest["readouts"],
        "design_contract": studio_manifest["design_contract"],
        "resources": imported,
    }
    if args.check:
        current = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
        for key in ("resources", "bitmap_font", "readouts"):
            if current.get(key) != record[key]:
                print(f"ERROR committed STUDIO_IMPORT.json {key} differs from "
                      "the studio export", file=sys.stderr)
                return 1
        print(f"OK: {len(imported)} resources match the studio export")
        return 0

    MANIFEST.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"imported {len(imported)} resources from {export}")
    print(f"studio commit {record['studio_commit'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
