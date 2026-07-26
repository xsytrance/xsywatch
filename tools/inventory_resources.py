#!/usr/bin/env python3
"""Deterministic runtime-resource inventory for engine-managed faces
(ADR-009 §3).

Binds every runtime resource byte of a face to its visual version:
path, Android resource id, dimensions, color mode/alpha, size, SHA-256,
source classification, handoff asset id, consuming components, and
normal/AOD usage — plus drift analysis (missing, unexpected, duplicate,
unreferenced resources).

Usage:
  inventory_resources.py <face>            # regenerate committed inventory
  inventory_resources.py <face> --check    # CI gate: fail on any drift

Output (committed):
  watchfaces/<face>/visual/inventories/inventory.json   (deterministic)
  watchfaces/<face>/visual/inventories/inventory.md     (human summary)

Exit codes: 0 clean; 1 drift/inconsistency (details on stdout).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visuallib as V  # noqa: E402

# Legacy Phase-1 files that ship in the APK but are not referenced by the
# WFF XML. Grandfathered: present in the immutable release APK; removing
# them is a (visual-neutral) change that must go through normal review.
UNREFERENCED_ALLOWLIST = {
    "aurelius": [
        # TTF fonts superseded by the BitmapFont pipeline in Phase 1.
        "app/src/main/res/font/marcellus.ttf",
        "app/src/main/res/font/marcellus_sc.ttf",
        "app/src/main/res/font/rajdhani_bold.ttf",
        # Tourbillon well parts baked into bg.png by the Phase-1 builder;
        # the standalone exports were never referenced by the shipped XML
        # (verified against the immutable release APK, which also carries
        # them unused). Discovered by this inventory tool, Phase 3.
        "app/src/main/res/drawable-nodpi/tourb_base.png",
        "app/src/main/res/drawable-nodpi/tourb_disc.png",
        "app/src/main/res/drawable-nodpi/tourb_rim.png",
    ],
}

# Non-drawable structural resources every face has.
STRUCTURAL = [
    "app/src/main/res/raw/watchface.xml",
    "app/src/main/res/xml/watch_face_info.xml",
    "app/src/main/res/values/integers.xml",
    "app/src/main/res/drawable/preview.png",
]


def build_inventory(face: str) -> dict:
    from PIL import Image

    face_dir = V.REPO / "watchfaces" / face
    res_dir = face_dir / "app/src/main/res"
    scene = V.Scene.load(face)

    # -- which resources does the XML reference, and who consumes them ----
    consumers: dict[str, list[str]] = defaultdict(list)
    usage: dict[str, dict] = defaultdict(lambda: {"normal": False,
                                                  "aod": False})
    for lay in scene.layers:
        normal_visible = lay.alpha > 0 or "alpha" in lay.transforms
        aod_visible = (lay.ambient_alpha if lay.ambient_alpha is not None
                       else lay.alpha) > 0
        if lay.resource:
            consumers[lay.resource].append(lay.name)
            usage[lay.resource]["normal"] |= normal_visible
            usage[lay.resource]["aod"] |= aod_visible
        if lay.text:
            fam = scene.fonts[lay.text["family"]]
            for res, _w, _h in fam.values():
                consumers[res].append(f"{lay.name} (font "
                                      f"{lay.text['family']})")
                usage[res]["normal"] |= normal_visible
                usage[res]["aod"] |= aod_visible

    # -- handoff classification -------------------------------------------
    handoff_by_dest: dict[str, str] = {}
    handoff_path = face_dir / "engine/handoff.json"
    if handoff_path.exists():
        for entry in V.load_json(handoff_path).get("assets", []):
            dest = entry.get("destination")
            if dest:
                rel = str(Path(dest).relative_to(f"watchfaces/{face}")) \
                    if dest.startswith("watchfaces/") else dest
                handoff_by_dest[rel] = entry["asset_id"]

    # -- walk the res tree -------------------------------------------------
    records = []
    referenced = set(consumers)
    seen_resources = set()
    sha_to_paths = defaultdict(list)
    problems = {"missing": [], "unreferenced": [], "duplicates": []}

    for p in sorted(res_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(face_dir))
        sha = V.sha256_file(p)
        sha_to_paths[sha].append(rel)
        rec = {
            "path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha,
            "kind": p.parent.name,
            "resource_id": p.stem if p.suffix == ".png" else None,
            "classification": ("studio-handoff" if rel in handoff_by_dest
                               else "legacy"),
            "handoff_asset_id": handoff_by_dest.get(rel),
            "consumers": [],
            "used_normal": False,
            "used_aod": False,
            "referenced": False,
        }
        if p.suffix == ".png":
            with Image.open(p) as im:
                rec["dimensions"] = list(im.size)
                rec["mode"] = im.mode
                rec["alpha"] = "straight" if im.mode == "RGBA" else "none"
        if rec["resource_id"] and rec["resource_id"] in referenced:
            rid = rec["resource_id"]
            seen_resources.add(rid)
            rec["referenced"] = True
            rec["consumers"] = sorted(set(consumers[rid]))
            rec["used_normal"] = usage[rid]["normal"]
            rec["used_aod"] = usage[rid]["aod"]
        elif rel in STRUCTURAL:
            rec["referenced"] = True
            rec["classification"] = "structural"
            rec["consumers"] = ["build/packaging"]
        elif rel in UNREFERENCED_ALLOWLIST.get(face, []):
            rec["classification"] = "legacy-unreferenced-allowlisted"
        else:
            problems["unreferenced"].append(rel)
        records.append(rec)

    for rid in sorted(referenced - seen_resources):
        problems["missing"].append(
            f"resource {rid!r} referenced by "
            f"{sorted(set(consumers[rid]))} has no file under res/")

    for sha, paths in sorted(sha_to_paths.items()):
        if len(paths) > 1:
            problems["duplicates"].append(paths)

    return {
        "face": face,
        "contract_version": V.VisualContract.load(face)
                             .raw["meta"]["contract_version"],
        "xml_sha256": scene.xml_sha256,
        "resource_count": len(records),
        "resources": records,
        "problems": problems,
    }


def render_markdown(inv: dict) -> str:
    lines = [f"# Resource inventory — {inv['face']}", "",
             f"Committed XML sha256: `{inv['xml_sha256']}`  ",
             f"Resources: {inv['resource_count']}", "",
             "| path | dims | sha256 (12) | class | consumers | N | A |",
             "|---|---|---|---|---|---|---|"]
    for r in inv["resources"]:
        dims = "×".join(map(str, r.get("dimensions", []))) or "—"
        cons = ", ".join(r["consumers"][:3]) or "—"
        if len(r["consumers"]) > 3:
            cons += f" +{len(r['consumers']) - 3}"
        lines.append(
            f"| {r['path']} | {dims} | `{r['sha256'][:12]}` "
            f"| {r['classification']} | {cons} "
            f"| {'✓' if r['used_normal'] else ''} "
            f"| {'✓' if r['used_aod'] else ''} |")
    p = inv["problems"]
    lines += ["", "## Problems", ""]
    if not any(p.values()):
        lines.append("None — inventory is clean.")
    for k in ("missing", "unreferenced", "duplicates"):
        for item in p[k]:
            lines.append(f"- **{k}**: {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("face")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    inv = build_inventory(a.face)
    inv_dir = V.REPO / "watchfaces" / a.face / "visual" / "inventories"
    problems = inv["problems"]
    hard_fail = bool(problems["missing"] or problems["unreferenced"])

    if a.check:
        committed_path = inv_dir / "inventory.json"
        if not committed_path.exists():
            print(f"FAIL: no committed inventory at {committed_path}")
            return 1
        committed = V.load_json(committed_path)
        if committed != inv:
            print("FAIL: committed inventory drifted from the live tree —")
            live = {r["path"]: r["sha256"] for r in inv["resources"]}
            old = {r["path"]: r["sha256"] for r in committed["resources"]}
            for path in sorted(set(live) | set(old)):
                if path not in old:
                    print(f"  + new file: {path}")
                elif path not in live:
                    print(f"  - removed file: {path}")
                elif live[path] != old[path]:
                    print(f"  ~ bytes changed: {path}")
            if committed.get("xml_sha256") != inv["xml_sha256"]:
                print("  ~ watchface.xml changed")
            print("  regenerate + review: "
                  "python3 tools/inventory_resources.py " + a.face)
            return 1
        if hard_fail:
            print("FAIL: inventory has hard problems:", problems)
            return 1
        print(f"OK: inventory matches the tree "
              f"({inv['resource_count']} resources, clean)")
        return 0

    V.dump_json_deterministic(inv, inv_dir / "inventory.json")
    (inv_dir / "inventory.md").write_text(render_markdown(inv),
                                          encoding="utf-8")
    print(f"wrote {inv_dir}/inventory.json (+.md); "
          f"{inv['resource_count']} resources")
    for k, items in problems.items():
        for item in items:
            print(f"  {k}: {item}")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
