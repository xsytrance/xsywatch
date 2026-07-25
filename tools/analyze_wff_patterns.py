#!/usr/bin/env python3
"""Audit WFF patterns across all committed watchface.xml files (Phase 2 §4.2).

Deterministic: same tree in → byte-identical reports out (no timestamps).

Outputs:
    docs/reports/PHASE_2_COMPONENT_AUDIT.json   (machine-readable)
    docs/reports/PHASE_2_COMPONENT_AUDIT.md     (human-readable, cites paths+counts)

Usage: python3 tools/analyze_wff_patterns.py [--repo-root PATH]
"""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

DATA_SOURCE_RE = re.compile(r"\[([A-Z_0-9]+)\]")


def normalize_expression(expr: str) -> str:
    """Reduce an expression to its structural shape: numbers -> N."""
    e = re.sub(r"\s+", " ", expr.strip())
    e = re.sub(r"(?<![A-Z_0-9])\d+(?:\.\d+)?", "N", e)
    return e


def wff_version(face_dir: Path) -> str:
    """WFF version from the manifest meta-data, following @integer indirection."""
    man = face_dir / "app/src/main/AndroidManifest.xml"
    if not man.exists():
        return "unknown"
    t = man.read_text()
    m = re.search(r'watchface\.format\.version"\s*android:value="([^"]+)"', t)
    if not m:
        return "unknown"
    val = m.group(1)
    ref = re.match(r"@integer/(\w+)", val)
    if not ref:
        return val
    for values in face_dir.glob("app/src/main/res/values*/*.xml"):
        i = re.search(rf'<integer name="{ref.group(1)}">(\d+)</integer>',
                      values.read_text())
        if i:
            return i.group(1)
    return "unknown"


def audit_face(face_dir: Path, root: Path) -> dict:
    wff = face_dir / "app/src/main/res/raw/watchface.xml"
    tree = ET.parse(wff)
    top = tree.getroot()
    all_elems = list(top.iter())

    tags = Counter(e.tag for e in all_elems)
    meta = {e.get("key"): e.get("value") for e in top.iter("Metadata")}

    variants = Counter()
    anim_params = Counter()
    for v in top.iter("Variant"):
        variants[f"mode={v.get('mode')} target={v.get('target')}"] += 1
        anim_params[f"duration={v.get('duration')} interp={v.get('interpolation')}"] += 1

    exprs = []
    for e in all_elems:
        for attr in ("value", "expression"):
            val = e.get(attr)
            if val and "[" in val:
                exprs.append((e.tag, e.get("target") or "", val))
    sources = sorted({m for _, _, v in exprs for m in DATA_SOURCE_RE.findall(v)})
    norm_exprs = Counter(normalize_expression(v) for _, _, v in exprs)

    rotating = [e.get("name") or "?" for e in all_elems if e.tag == "Transform"
                and e.get("target") == "angle"]
    rot_parents = [p.get("name") for p in all_elems
                   if any(c.tag == "Transform" and c.get("target") == "angle"
                          for c in p)]

    fonts = {bf.get("name"): len(list(bf.iter("Character")))
             for bf in top.iter("BitmapFont") if bf.get("name")}

    referenced = sorted({e.get("resource") for e in all_elems if e.get("resource")})
    res_dirs = list(face_dir.glob("app/src/main/res/drawable*"))
    present = sorted({p.stem for d in res_dirs for p in d.iterdir() if p.is_file()})
    unused = sorted(set(present) - set(referenced) - {"preview"})
    missing = sorted(set(referenced) - set(present))

    named = [e.get("name") for e in all_elems if e.get("name")]
    z_named = [n for n in named if re.match(r"z\d", n or "")]

    unsafe = []
    for p in all_elems:
        if p.tag.startswith("Part"):
            has_angle = any(c.tag == "Transform" and c.get("target") == "angle" for c in p)
            if has_angle and not (p.get("pivotX") and p.get("pivotY")):
                unsafe.append(f"{p.get('name')}: angle transform without explicit pivot")
    for _, _, v in exprs:
        if "HEART_RATE" in v and "clamp" not in v:
            unsafe.append(f"unclamped HEART_RATE expression: {v[:60]}")
    if missing:
        unsafe.append(f"missing referenced resources: {missing}")

    return {
        "face": face_dir.name,
        "path": str(wff.relative_to(root)),
        "wff_version": wff_version(face_dir),
        "clock_type": meta.get("CLOCK_TYPE", "unspecified"),
        "element_count": len(all_elems),
        "tag_counts": dict(sorted(tags.items())),
        "variant_patterns": dict(sorted(variants.items())),
        "animation_params": dict(sorted(anim_params.items())),
        "group_count": tags.get("Group", 0),
        "reference_count": tags.get("Reference", 0),
        "data_sources": sources,
        "expressions_normalized": dict(sorted(norm_exprs.items())),
        "rotating_parts": sorted(x for x in rot_parents if x),
        "bitmap_fonts": fonts,
        "resources_referenced": referenced,
        "resources_unused": unused,
        "resources_missing": missing,
        "named_elements": len(named),
        "z_prefixed_names": len(z_named),
        "unsafe_patterns": sorted(set(unsafe)),
    }


def cross_face(faces: list[dict]) -> dict:
    expr_faces: dict[str, list[str]] = {}
    for f in faces:
        for e in f["expressions_normalized"]:
            expr_faces.setdefault(e, []).append(f["face"])
    shared = {e: sorted(fs) for e, fs in expr_faces.items() if len(fs) >= 2}
    src_faces: dict[str, list[str]] = {}
    for f in faces:
        for s in f["data_sources"]:
            src_faces.setdefault(s, []).append(f["face"])
    return {
        "shared_normalized_expressions": dict(sorted(shared.items())),
        "data_source_usage": {k: sorted(v) for k, v in sorted(src_faces.items())},
    }


def classify(faces: list[dict], cross: dict) -> dict:
    extract, similar, oneoff = [], [], []
    for expr, fs in cross["shared_normalized_expressions"].items():
        row = {"pattern": expr, "faces": fs, "count": len(fs)}
        (extract if len(fs) >= 3 else similar).append(row)
    for f in faces:
        for e, n in f["expressions_normalized"].items():
            if e not in cross["shared_normalized_expressions"]:
                oneoff.append({"pattern": e, "faces": [f["face"]], "count": 1})
    unsafe = [{"face": f["face"], "issues": f["unsafe_patterns"]}
              for f in faces if f["unsafe_patterns"]]
    return {
        "extract_now": sorted(extract, key=lambda r: (-r["count"], r["pattern"])),
        "similar_keep_face_specific": sorted(similar, key=lambda r: r["pattern"]),
        "one_off_do_not_abstract": sorted(oneoff, key=lambda r: (r["faces"][0], r["pattern"])),
        "unsafe_needs_cleanup": unsafe,
    }


def render_md(faces, cross, cls) -> str:
    L = ["# Phase 2 Component Audit — all committed watchfaces",
         "",
         "Generated deterministically by `tools/analyze_wff_patterns.py`; do not edit by hand.",
         "Machine-readable twin: `PHASE_2_COMPONENT_AUDIT.json`.",
         "", "## Per-face summary", "",
         "| Face | WFF | Clock | Elems | Groups | Refs | Rotating parts | Fonts | Unused res | Unsafe |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for f in faces:
        L.append(f"| {f['face']} | {f['wff_version']} | {f['clock_type']} | "
                 f"{f['element_count']} | {f['group_count']} | {f['reference_count']} | "
                 f"{len(f['rotating_parts'])} | {len(f['bitmap_fonts'])} | "
                 f"{len(f['resources_unused'])} | {len(f['unsafe_patterns'])} |")
    L += ["", "## Data-source usage (which faces bind which data)", ""]
    for src, fs in cross["data_source_usage"].items():
        L.append(f"- `[{src}]` — {len(fs)} face(s): {', '.join(fs)}")
    L += ["", "## 1. Components suitable for immediate extraction (pattern in ≥3 faces)", ""]
    for r in cls["extract_now"]:
        L.append(f"- ({r['count']} faces: {', '.join(r['faces'])}) `{r['pattern']}`")
    L += ["", "## 2. Similar but face-specific (2 faces — do not force-share yet)", ""]
    for r in cls["similar_keep_face_specific"]:
        L.append(f"- ({', '.join(r['faces'])}) `{r['pattern']}`")
    L += ["", "## 3. One-off patterns (not worth abstracting)", "",
          f"{len(cls['one_off_do_not_abstract'])} single-face expression shapes "
          "(full list in the JSON; deliberately not abstracted)."]
    L += ["", "## 4. Unsafe/inconsistent patterns needing later cleanup", ""]
    if cls["unsafe_needs_cleanup"]:
        for row in cls["unsafe_needs_cleanup"]:
            for i in row["issues"]:
                L.append(f"- **{row['face']}**: {i}")
    else:
        L.append("- none detected")
    L += ["", "## Per-face detail", ""]
    for f in faces:
        L += [f"### {f['face']} (`{f['path']}`)", "",
              f"- WFF {f['wff_version']}, {f['clock_type']}, {f['element_count']} elements, "
              f"{f['named_elements']} named ({f['z_prefixed_names']} z-prefixed)",
              f"- data sources: {', '.join('`['+s+']`' for s in f['data_sources']) or 'none'}",
              f"- rotating parts: {', '.join(f['rotating_parts']) or 'none'}",
              f"- bitmap fonts: {', '.join(f'{k}({v} glyphs)' for k, v in f['bitmap_fonts'].items()) or 'none'}",
              f"- unused resources: {', '.join(f['resources_unused']) or 'none'}",
              f"- missing resources: {', '.join(f['resources_missing']) or 'none'}", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    faces = [audit_face(d, root)
             for d in sorted((root / "watchfaces").iterdir())
             if (d / "app/src/main/res/raw/watchface.xml").exists()]
    cross = cross_face(faces)
    cls = classify(faces, cross)
    out = {"faces": faces, "cross_face": cross, "classification": cls}
    (root / "docs/reports/PHASE_2_COMPONENT_AUDIT.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n")
    (root / "docs/reports/PHASE_2_COMPONENT_AUDIT.md").write_text(
        render_md(faces, cross, cls))
    print(f"audited {len(faces)} faces -> PHASE_2_COMPONENT_AUDIT.{{json,md}}")


if __name__ == "__main__":
    main()
