#!/usr/bin/env python3
"""Generate (or verify) a face's committed watchface.xml from its engine spec.

Usage:
    python3 tools/generate_face.py <slug>            # write generated XML
    python3 tools/generate_face.py <slug> --check    # exit 1 on drift
    python3 tools/generate_face.py <slug> --stdout   # print, write nothing

Pipeline per face:
  1. load watchfaces/<slug>/engine/face.toml (authoritative);
  2. verify spec identity matches the Gradle project (package, versions);
  3. render deterministically (rendered twice; byte-equality asserted);
  4. structural validation incl. resource existence;
  5. write or compare watchfaces/<slug>/app/src/main/res/raw/watchface.xml.
"""

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "engine"))

from wffgen.render import render_face          # noqa: E402
from wffgen.spec import load_spec              # noqa: E402
from wffgen.validation import SpecError, validate_face  # noqa: E402


def gradle_identity(face_dir: Path) -> dict:
    t = (face_dir / "app/build.gradle.kts").read_text()
    out = {}
    for key, pat in [("package", r'applicationId\s*=\s*"([^"]+)"'),
                     ("version_code", r"versionCode\s*=\s*(\d+)"),
                     ("version_name", r'versionName\s*=\s*"([^"]+)"')]:
        m = re.search(pat, t)
        out[key] = m.group(1) if m else None
    return out


def available_resources(face_dir: Path) -> set[str]:
    return {p.stem for d in face_dir.glob("app/src/main/res/drawable*")
            for p in d.iterdir() if p.is_file()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--check", action="store_true",
                    help="verify committed XML matches generation; no writes")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--repo-root", default=str(REPO))
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    face_dir = root / "watchfaces" / args.slug
    spec_path = face_dir / "engine" / "face.toml"
    if not spec_path.exists():
        sys.exit(f"ERROR: {spec_path} not found — '{args.slug}' is not an "
                 "engine-managed face")

    spec = load_spec(spec_path)

    gradle = gradle_identity(face_dir)
    for key in ("package", "version_code", "version_name"):
        want, got = str(spec.identity.get(key)), str(gradle.get(key))
        if want != got:
            sys.exit(f"ERROR: spec identity {key}={want} does not match "
                     f"Gradle {got} — refusing to generate")

    xml_a = render_face(spec)
    xml_b = render_face(spec)
    if xml_a != xml_b:
        sys.exit("ERROR: nondeterministic generation (two renders differ) — "
                 "engine bug, do not commit")

    try:
        validate_face(spec, xml_a, available_resources(face_dir))
    except SpecError as e:
        sys.exit(f"ERROR: {e}")

    target = face_dir / "app/src/main/res/raw/watchface.xml"
    if args.stdout:
        print(xml_a, end="")
        return
    if args.check:
        current = target.read_text() if target.exists() else ""
        if current != xml_a:
            sys.exit(f"DRIFT: {target} does not match generation from "
                     f"{spec_path}.\nRun: python3 tools/generate_face.py "
                     f"{args.slug}")
        print(f"OK: {args.slug} committed XML matches deterministic generation")
        return
    target.write_text(xml_a)
    print(f"wrote {target.relative_to(root)} "
          f"({len(spec.components)} components)")


if __name__ == "__main__":
    main()
