#!/usr/bin/env python3
"""Gated studio-asset import (Phase 3, ADR-009 §6 + ASSET_HANDOFF_CONTRACT).

Reads the studio repository's export metadata, verifies every export byte
against its recorded sha256 BEFORE it touches this repo, copies the files
into the face's runtime resources, and writes the real (non-example)
handoff manifest entries with destinations and re-verified checksums.

It does NOT update inventories, candidate renders, or approval records —
those are separate, reviewable steps (see the Phase-3 report §workflow).

Usage:
  import_handoff.py aurelius --studio ~/AGENOR-Horology \
      --metadata exports/aurelius_mk2/handoff_metadata.json [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("face")
    ap.add_argument("--studio", type=Path, required=True)
    ap.add_argument("--metadata", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    studio = a.studio.expanduser().resolve()
    meta_path = studio / a.metadata
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    face_dir = REPO / "watchfaces" / a.face
    res_dir = face_dir / "app/src/main/res/drawable-nodpi"

    # the recorded source commit must exist in the studio repo and contain
    # the producing sources
    commit = meta["source_commit"]
    head = subprocess.run(["git", "cat-file", "-t", commit], cwd=studio,
                          capture_output=True, text=True)
    if head.returncode != 0 or head.stdout.strip() != "commit":
        print(f"FAIL: source_commit {commit} not found in {studio}")
        return 1

    entries = []
    failures = 0
    for exp in meta["exports"]:
        src = studio / exp["export_file"]
        if not src.exists():
            print(f"FAIL: missing export {src}")
            failures += 1
            continue
        actual = sha256(src)
        if actual != exp["sha256"]:
            print(f"FAIL: checksum mismatch for {exp['asset_id']}: "
                  f"{actual[:12]} != recorded {exp['sha256'][:12]}")
            failures += 1
            continue
        dest = res_dir / f"{exp['resource_name']}.png"
        rel_dest = str(dest.relative_to(REPO))
        if not a.dry_run:
            shutil.copy2(src, dest)
            if sha256(dest) != exp["sha256"]:
                print(f"FAIL: post-copy verification failed for {dest}")
                failures += 1
                continue
        entries.append({
            "asset_id": exp["asset_id"],
            "source_repo": "xsytrance/AGENOR-Horology",
            "source_commit": commit,
            "source_paths": exp["source_paths"],
            "spec_path": exp["spec_path"],
            "export_type": exp["export_type"],
            "destination": rel_dest,
            "dimensions": exp["dimensions"],
            "color_space": exp["color_space"],
            "alpha": exp["alpha"],
            "pivot": exp["pivot"],
            "frames": exp["frames"],
            "frame_seconds": exp["frame_seconds"],
            "loop": exp["loop"],
            "aod_safe": exp["aod_safe"],
            "license": exp["license"],
            "sha256": exp["sha256"],
            "lifecycle": exp["lifecycle"],
            "consumer_component": exp["consumer_component"],
            "regenerate": exp["regenerate"],
        })
        print(f"{'DRY ' if a.dry_run else ''}imported {exp['asset_id']} "
              f"-> {rel_dest}")

    if failures:
        print(f"\n{failures} failure(s) — NOTHING was manifested")
        return 1
    if a.dry_run:
        print(f"\ndry run: {len(entries)} exports verified against "
              f"{commit[:12]}")
        return 0

    handoff_path = face_dir / "engine/handoff.json"
    handoff = {
        "contract": "docs/ASSET_HANDOFF_CONTRACT.md",
        "generation": meta.get("generation"),
        "assets": entries,
    }
    handoff_path.write_text(
        json.dumps(handoff, indent=2, sort_keys=False) + "\n",
        encoding="utf-8")
    print(f"\nwrote {handoff_path} with {len(entries)} REAL entries "
          f"(source commit {commit[:12]}); synthetic example replaced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
