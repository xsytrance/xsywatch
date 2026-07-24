#!/usr/bin/env python3
"""Regenerate releases/MANIFEST.json and per-channel RELEASE.md files.

Manifest schema (channel-safe, ADR-006 as amended by the Phase-1 review):

    {
      "generated": "...", "device_target": "...", "signing": "...",
      "faces": {
        "<slug>": { "channels": {
            "current":  { ...release entry... },
            "v1.0":     { ...release entry... }
        }}
      }
    }

Identity is (slug, channel). Each releases/<slug>/<channel>/ directory must
contain exactly one APK. Real APK metadata is read via aapt2 — never invented;
fields that cannot be determined are explicit "unknown" markers. Per-channel
provenance fields (source_commit_of_build, provenance_note, archived_on) are
carried over from the existing manifest when present.

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
CARRIED_FIELDS = ("source_commit_of_build", "provenance_note", "archived_on",
                  "original_filename", "build_date_approx_file_mtime")


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


def load_previous(rel_root: Path) -> dict:
    man = rel_root / "MANIFEST.json"
    if not man.exists():
        return {}
    try:
        data = json.loads(man.read_text())
    except json.JSONDecodeError:
        return {}
    carried: dict[tuple, dict] = {}
    if "faces" in data:  # current schema
        for slug, face in data["faces"].items():
            for channel, e in face.get("channels", {}).items():
                carried[(slug, channel)] = e
    elif "releases" in data:  # legacy flat schema (pre-review)
        for e in data["releases"]:
            carried[(e["slug"], e.get("channel", "current"))] = e
    return carried


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    root = Path(args.repo_root)
    rel_root = root / "releases"
    aapt2 = find_aapt2()
    if not aapt2:
        sys.exit("aapt2 not found — set ANDROID_HOME (need build-tools)")

    previous = load_previous(rel_root)
    faces: dict[str, dict] = {}

    for face_dir in sorted(d for d in rel_root.iterdir() if d.is_dir()):
        slug = face_dir.name
        for chan_dir in sorted(d for d in face_dir.iterdir() if d.is_dir()):
            channel = chan_dir.name
            apks = sorted(chan_dir.glob("*.apk"))
            if len(apks) != 1:
                sys.exit(f"releases/{slug}/{channel}: expected exactly 1 APK, "
                         f"found {len(apks)} — fix before regenerating")
            apk = apks[0]
            meta = apk_badging(aapt2, apk)
            previews = sorted(p.name for p in chan_dir.glob("preview.*"))
            old = previous.get((slug, channel), {})
            entry = {
                "apk": str(apk.relative_to(root)),
                "sha256": sha256(apk),
                "size_bytes": apk.stat().st_size,
                "label": meta["label"],
                "package": meta["package"],
                "versionCode": meta["versionCode"],
                "versionName": meta["versionName"],
                "targetSdk": meta["targetSdk"],
                "preview": previews[0] if previews else None,
                "source_dir": f"watchfaces/{slug}",
            }
            for k in CARRIED_FIELDS:
                entry[k] = old.get(k, UNKNOWN if k == "source_commit_of_build" else old.get(k))
            stamp = chan_dir / ".archived_on"
            if stamp.exists():
                entry["archived_on"] = stamp.read_text().strip()
            entry = {k: v for k, v in entry.items() if v is not None or k in
                     ("preview", "versionCode", "targetSdk")}
            # Versioned channels must be named after the APK inside them.
            if channel != "current" and channel != f"v{meta['versionName']}":
                sys.exit(f"releases/{slug}/{channel}: directory name does not match "
                         f"APK versionName '{meta['versionName']}'")
            faces.setdefault(slug, {"channels": {}})["channels"][channel] = entry

            (chan_dir / "RELEASE.md").write_text(
f"""# {meta['label']} — release metadata ({channel})

| Field | Value |
|---|---|
| Slug / channel | {slug} / {channel} |
| APK | {apk.name} |
| SHA-256 | `{entry['sha256']}` |
| Size | {entry['size_bytes']:,} bytes |
| Package | {meta['package']} |
| Version | {meta['versionName']} (versionCode {meta['versionCode']}) |
| Target | Galaxy Watch7 44mm, targetSdk {meta['targetSdk']} |
| Signing | debug (sideload only) |
| Source project | watchfaces/{slug} |
| Source commit of this build | {entry.get('source_commit_of_build', UNKNOWN)} |
| Preview | {entry.get('preview') or 'MISSING — regenerate at next release'} |
{f"| Archived on | {entry['archived_on']} |" if entry.get('archived_on') else ''}
Known limitations: see `docs/KNOWN_LIMITATIONS.md`.
""")

    manifest = {
        "generated": dt.date.today().isoformat(),
        "schema": 2,
        "device_target": "Samsung Galaxy Watch7 44mm (480x480), Wear OS, WFF",
        "signing": "debug (sideload only)",
        "faces": faces,
    }
    (rel_root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    n = sum(len(f["channels"]) for f in faces.values())
    print(f"wrote MANIFEST.json (schema 2): {len(faces)} faces, {n} (slug,channel) entries")


if __name__ == "__main__":
    main()
