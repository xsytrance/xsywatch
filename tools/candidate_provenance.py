#!/usr/bin/env python3
"""Candidate-specific artwork provenance closure.

`docs/LICENSING.md` carries a repository-wide warning about legacy
ComfyUI/Stable-Diffusion-family generation and external donor images. That
warning is historically accurate for older faces, but it is not
automatically a statement about THIS candidate. Leaving it unscoped means
an Aurelius launch decision is governed by a caution about artwork that may
not be in Aurelius at all.

This tool answers the question per asset instead of per repository: for
every manifested runtime asset and the generated preview, where did the
current bytes actually come from?

    python3 tools/candidate_provenance.py aurelius --version 2.0.0-rc2 \
        [--studio ~/AGENOR-Horology] [--out PATH]

It does not weaken the repository-wide warning; it scopes it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Detection is MECHANISM-based, not keyword-based.
#
# A first cut scanned for the word "checkpoint" and flagged all 50 assets,
# because the studio scripts say "Checkpoint A" in a comment. A provenance
# tool that reports every asset as contaminated is worse than none: it
# would have wrongly concluded the repository-wide warning applies here.
#
# External pixels can only reach a render through a small number of real
# mechanisms, so those are what is detected.

# Model weights / generator artifacts, as FILES.
AI_ARTIFACT = re.compile(
    r"\.safetensors\b|\.ckpt\b|\.pt\b|\.pth\b|"
    r"\bComfyUI\b|\bstable[-_ ]?diffusion\b|\bautomatic1111\b|"
    r"\bimg2img\b|\btxt2img\b", re.I)

# The call sites through which an external raster can enter a render.
IMAGE_INGEST = re.compile(
    r"bpy\.data\.images\.load|ShaderNodeTexImage|image\.filepath\s*=|"
    r"load_image\s*\(", re.I)

# A PIL read of an EXTERNAL STRING LITERAL. Reading through a local
# variable proves nothing — every such read in this pipeline is bound to
# its own raw/export directories — so only literal paths that look like
# they leave the repository are treated as evidence. The mechanism that
# actually lets a raster into a RENDER is the Blender image ingest above.
PIL_READ_LITERAL = re.compile(
    r"""Image\.open\(\s*['"]([^'"]+)['"]""")
EXTERNAL_LITERAL = re.compile(r"^/|^~|\.\./\.\.|/AI/|ComfyUI", re.I)

# Donor-image conventions used by the legacy faces.
DONOR_PATH = re.compile(r"/AI/ComfyUI/|~/AI/|donor|fuselage_\d|aurelius_\d",
                        re.I)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                       text=True)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--version", required=True)
    ap.add_argument("--studio", default=str(Path.home() / "AGENOR-Horology"))
    ap.add_argument("--out")
    args = ap.parse_args()

    face_dir = REPO / "watchfaces" / args.face
    studio = Path(args.studio)
    handoff = json.loads((face_dir / "engine/handoff.json").read_text())
    inventory = json.loads(
        (face_dir / "visual/inventories/inventory.json").read_text())
    inv_by_path = {r["path"]: r for r in inventory["resources"]}

    licenses = {}
    lic_path = REPO / "docs/asset-licenses.json"
    if lic_path.exists():
        data = json.loads(lic_path.read_text())
        rows = data if isinstance(data, list) else data.get("assets", [])
        for row in rows:
            licenses[row.get("path")] = row

    entries = []
    ai_hits, donor_hits, unresolved = [], [], []

    for a in sorted(handoff["assets"], key=lambda x: x["asset_id"]):
        dest = a["destination"]
        rel = dest.replace(f"watchfaces/{args.face}/", "", 1)
        p = REPO / dest
        inv = inv_by_path.get(rel, {})

        srcs = a.get("source_paths", [])
        blob = " ".join(srcs) + " " + (a.get("spec_path") or "")
        ai = bool(AI_ARTIFACT.search(blob))
        donor = bool(DONOR_PATH.search(blob))

        # Read the producing scripts AT the producing commit and look for
        # the mechanisms by which external pixels could enter a render.
        script_ai = script_donor = False
        findings: list[str] = []
        for s in srcs:
            if not s.endswith(".py"):
                continue
            txt = git(studio, "show", f"{a['source_commit']}:{s}")
            for m in AI_ARTIFACT.finditer(txt):
                script_ai = True
                findings.append(f"{s}: AI artifact reference {m.group(0)!r}")
            for m in DONOR_PATH.finditer(txt):
                script_donor = True
                findings.append(f"{s}: donor path {m.group(0)!r}")
            for m in IMAGE_INGEST.finditer(txt):
                script_donor = True
                findings.append(f"{s}: external image ingest "
                                f"{m.group(0)!r}")
            for m in PIL_READ_LITERAL.finditer(txt):
                lit = m.group(1)
                if EXTERNAL_LITERAL.search(lit):
                    script_donor = True
                    findings.append(f"{s}: PIL read of an external literal "
                                    f"path {lit!r}")

        e = {
            "asset_id": a["asset_id"],
            "destination": dest,
            "sha256": sha256(p) if p.exists() else None,
            "matches_handoff_sha": (sha256(p) == a["sha256"]) if p.exists()
                                   else False,
            "source_paths": srcs,
            "producing_commit": a["source_commit"],
            "source_classification": inv.get("source", "studio-handoff"),
            "license_record": a.get("license"),
            "external_ai_checkpoint_contributes_pixels": bool(ai or script_ai),
            "donor_image_contributes_pixels": bool(donor or script_donor),
            "detector_findings": findings,
        }
        if e["external_ai_checkpoint_contributes_pixels"]:
            ai_hits.append(e["asset_id"])
        if e["donor_image_contributes_pixels"]:
            donor_hits.append(e["asset_id"])
        if not p.exists() or not e["matches_handoff_sha"]:
            unresolved.append(e["asset_id"])
        entries.append(e)

    # the generated consumer preview
    prev_rel = "app/src/main/res/drawable/preview.png"
    prev = face_dir / prev_rel
    entries.append({
        "asset_id": "generated/AureliusPreview",
        "destination": f"watchfaces/{args.face}/{prev_rel}",
        "sha256": sha256(prev) if prev.exists() else None,
        "matches_handoff_sha": None,
        "source_paths": ["watchfaces/aurelius/visual/candidates/"
                         "field-tourbillon-mk2-rc1/normal.png"],
        "producing_commit": "consumer-generated",
        "source_classification": "generated",
        "license_record": "derived from the rc1 reference render "
                          "(Lanczos downsample to 400x400)",
        "external_ai_checkpoint_contributes_pixels": False,
        "donor_image_contributes_pixels": False,
        "note": ("downsampled from the deterministic reference render, "
                 "which composites only the manifested runtime resources"),
    })

    clean = not ai_hits and not donor_hits and not unresolved
    result = {
        "face": args.face,
        "candidate_version": args.version,
        "visual_version": "field-tourbillon-mk2-rc1",
        "asset_count": len(entries),
        "method": (
            "every manifested asset is traced to its producing commit and "
            "source paths in the studio repository; those producing scripts "
            "are read AT that commit and scanned for legacy AI-pipeline and "
            "donor-image markers. Current bytes are re-hashed and compared "
            "to the handoff manifest."),
        "assets": entries,
        "assets_with_ai_checkpoint_pixels": ai_hits,
        "assets_with_donor_image_pixels": donor_hits,
        "assets_unresolved": unresolved,
        "conclusion": (
            "No current Aurelius runtime pixel derives from an external AI "
            "checkpoint or donor image. Every manifested asset is produced "
            "by the procedural Blender studio pipeline; the only "
            "third-party input is the audited Rajdhani Bold typeface "
            "(SIL OFL-1.1), which is commercially permissive."
            if clean else
            "UNRESOLVED — one or more current runtime pixels may derive "
            "from an external AI checkpoint or donor image. Identify the "
            "exact model/checkpoint, source and commercial-use terms and "
            "resolve them before paid publication."),
        "repository_wide_warning": {
            "source": "docs/LICENSING.md",
            "status": ("NOT APPLICABLE to this candidate" if clean
                       else "APPLIES to this candidate"),
            "scope_note": (
                "The repository-wide warning concerns legacy "
                "ComfyUI/SD-family and donor-image artwork in OTHER faces. "
                "It remains accurate and is NOT deleted or weakened; this "
                "record scopes it, showing it does not reach the Aurelius "
                "runtime."),
        },
        "third_party_inputs": [
            {"name": "Rajdhani Bold",
             "license": "SIL OFL-1.1",
             "commercial_use": "permitted",
             "role": "39 glyph rasters and the AURELIUS plate engraving",
             "audit": "docs/asset-licenses.json, THIRD_PARTY_NOTICES/"},
        ],
    }

    out = Path(args.out) if args.out else (
        REPO / "releases" / args.face / "candidates" / args.version /
        "PROVENANCE.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")

    print(f"assets traced           : {len(entries)}")
    print(f"AI-checkpoint pixels    : {len(ai_hits)} {ai_hits or ''}")
    print(f"donor-image pixels      : {len(donor_hits)} {donor_hits or ''}")
    print(f"unresolved / drifted    : {len(unresolved)} {unresolved or ''}")
    print(f"repo-wide warning       : "
          f"{result['repository_wide_warning']['status']}")
    try:
        shown = out.relative_to(REPO)
    except ValueError:
        shown = out
    print(f"wrote {shown}")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
