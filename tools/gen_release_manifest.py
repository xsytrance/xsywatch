#!/usr/bin/env python3
"""Regenerate releases/MANIFEST.json and each releases/<slug>/*/RELEASE.md.

Reads real APK metadata via aapt2 (never invents values). Fields that cannot
be determined are emitted as explicit "unknown" markers.

Usage: python3 tools/gen_release_manifest.py [--repo-root PATH]
"""

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

UNKNOWN = "unknown — not recorded at build time"


def find_aapt2() -> str | None:
    sdk = os.environ.get("ANDROID_HOME") or os.path.expanduser("~/Android/Sdk")
    candidates = sorted(glob.glob(f"{sdk}/build-tools/*/aapt2"))
    return candidates[-1] if candidates else None


def apk_badging(aapt2: str, apk: Path) -> dict:
    out = subprocess.run([aapt2, "dump", "badging", str(apk)],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", out)
    tgt = re.search(r"targetSdkVersion:'([^']+)'", out)
    label = re.search(r"application-label:'([^']+)'", out)
    return {
        "package": m.group(1) if m else UNKNOWN,
        "versionCode": int(m.group(2)) if m else None,
        "versionName": m.group(3) if m else UNKNOWN,
        "targetSdk": int(tgt.group(1)) if tgt else None,
        "label": label.group(1) if label else UNKNOWN,
    }


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Facts established during the Phase-1 audit; edit when new releases are cut.
PROVENANCE = {
    "introduced_commit": "d8ed43bfefe2eaf947b3f3993bc8aa15ebe90534",
    "introduced_note": ("APK first committed 2026-07-24 (repo commit d8ed43b). "
                        "Producing source predates the repo's source import; "
                        "build date below is the file mtime (approximate)."),
    "original_filenames": {
        "bushido": "xsywatch-bushido.apk", "ares-wargod": "ares-wargod.apk",
        "aurelius": "aurelius.apk", "bone-watch": "bone-watch.apk",
        "hellforge": "hellforge.apk", "pinball": "pinball.apk",
        "pulseface": "pulseface.apk",
    },
    "source_dirs": {
        "bushido": "watchfaces/bushido", "ares-wargod": "watchfaces/ares-wargod",
        "aurelius": "watchfaces/aurelius", "bone-watch": "watchfaces/bone-watch",
        "hellforge": "watchfaces/hellforge", "pinball": "watchfaces/pinball",
        "pulseface": "watchfaces/pulseface",
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    root = Path(args.repo_root)
    rel_root = root / "releases"
    aapt2 = find_aapt2()
    if not aapt2:
        sys.exit("aapt2 not found — set ANDROID_HOME (need build-tools)")

    manifest = {
        "generated": dt.date.today().isoformat(),
        "device_target": "Samsung Galaxy Watch7 44mm (480x480), Wear OS, WFF v4",
        "signing": "debug (sideload only)",
        "releases": [],
    }

    for apk in sorted(rel_root.glob("*/*/*.apk")):
        slug = apk.parent.parent.name
        channel = apk.parent.name  # current or vX.Y.Z
        meta = apk_badging(aapt2, apk)
        previews = [p.name for p in apk.parent.glob("preview.*")]
        mtime = dt.datetime.fromtimestamp(apk.stat().st_mtime).date().isoformat()
        entry = {
            "slug": slug,
            "channel": channel,
            "apk": str(apk.relative_to(root)),
            "sha256": sha256(apk),
            "size_bytes": apk.stat().st_size,
            "label": meta["label"],
            "package": meta["package"],
            "versionCode": meta["versionCode"],
            "versionName": meta["versionName"],
            "targetSdk": meta["targetSdk"],
            "build_date_approx_file_mtime": mtime,
            "preview": previews[0] if previews else None,
            "original_filename": PROVENANCE["original_filenames"].get(slug, UNKNOWN),
            "source_dir": PROVENANCE["source_dirs"].get(slug, UNKNOWN),
            "source_commit_of_build": UNKNOWN,
        }
        manifest["releases"].append(entry)

        release_md = apk.parent / "RELEASE.md"
        release_md.write_text(f"""# {meta['label']} — release metadata ({channel})

| Field | Value |
|---|---|
| Slug | {slug} |
| APK | {apk.name} (original name: {entry['original_filename']}) |
| SHA-256 | `{entry['sha256']}` |
| Size | {entry['size_bytes']:,} bytes |
| Package | {meta['package']} |
| Version | {meta['versionName']} (versionCode {meta['versionCode']}) |
| Target | Galaxy Watch7 44mm, WFF v4, targetSdk {meta['targetSdk']} |
| Signing | debug (sideload only) |
| Build date | {mtime} (file mtime — approximate) |
| Source project | {entry['source_dir']} |
| Source commit of this build | {entry['source_commit_of_build']} |
| Preview | {entry['preview'] or 'MISSING — regenerate at next release'} |
| Introduced to repo | commit `{PROVENANCE['introduced_commit'][:7]}` |

Known limitations: see `docs/KNOWN_LIMITATIONS.md`.
""")

    (rel_root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {rel_root/'MANIFEST.json'} ({len(manifest['releases'])} releases) "
          f"and per-release RELEASE.md files")


if __name__ == "__main__":
    main()
