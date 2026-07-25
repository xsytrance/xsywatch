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


def check_engine(root: Path) -> None:
    """Engine-managed faces: generated-XML drift, determinism, fixtures,
    and immutable-release pins."""
    import subprocess as sp

    engine_dir = root / "engine"
    for spec in sorted(root.glob("watchfaces/*/engine/face.toml")):
        slug = spec.parents[1].name
        if not engine_dir.is_dir():
            err(f"engine[{slug}]: face.toml exists but engine/ is missing")
            continue
        r = sp.run([sys.executable, str(root / "tools/generate_face.py"),
                    slug, "--check", "--repo-root", str(root)],
                   capture_output=True, text=True)
        if r.returncode != 0:
            msg = (r.stdout + r.stderr).strip().splitlines()
            err(f"engine[{slug}]: {msg[0] if msg else 'generation check failed'}")

    fixtures = root / "tests/engine/fixtures"
    if engine_dir.is_dir() and fixtures.is_dir():
        sys.path.insert(0, str(engine_dir))
        try:
            from wffgen.render import render_face
            from wffgen.spec import load_spec
            from wffgen.validation import SpecError, validate_face
            import xml.etree.ElementTree as _ET
            for f in sorted(fixtures.glob("fixture_*.toml")):
                try:
                    spec = load_spec(f)
                    a, b = render_face(spec), render_face(spec)
                    if a != b:
                        err(f"engine fixture {f.name}: nondeterministic generation")
                    res = {e.get("resource") for e in _ET.fromstring(a).iter()
                           if e.get("resource")}
                    validate_face(spec, a, res)
                except SpecError as e:
                    err(f"engine fixture {f.name}: {e.problems[0]}")
                except Exception as e:  # noqa: BLE001 — report, don't crash
                    err(f"engine fixture {f.name}: {e}")
        finally:
            sys.path.remove(str(engine_dir))

    for pin in sorted(root.glob("releases/*/*/.immutable")):
        chan_dir = pin.parent
        apks = sorted(chan_dir.glob("*.apk"))
        if len(apks) != 1:
            err(f"immutable[{chan_dir.relative_to(root)}]: expected 1 APK")
            continue
        if sha256(apks[0]) != pin.read_text().strip():
            err(f"immutable[{chan_dir.relative_to(root)}]: {apks[0].name} bytes "
                "changed but this release is pinned immutable")


HANDOFF_EXPORT_TYPES = {"static-image", "sprite-strip", "sprite-grid",
                        "mask", "font-glyphs"}
HANDOFF_LIFECYCLES = {"experimental", "candidate", "approved", "deprecated"}
HANDOFF_REQUIRED = ("asset_id", "source_repo", "source_commit", "source_paths",
                    "spec_path", "export_type", "destination", "dimensions",
                    "color_space", "alpha", "pivot", "frames", "frame_seconds",
                    "loop", "aod_safe", "license", "sha256", "lifecycle",
                    "consumer_component", "regenerate")


def check_handoff(root: Path) -> None:
    """Asset-handoff manifests: complete stdlib enforcement of the schema
    contract in docs/asset-handoff.schema.json (docs/ASSET_HANDOFF_CONTRACT.md).

    The synthetic-example exception is narrow: entries with "example": true
    may have destination == null and sha256 == null; every other constraint
    still applies to them.
    """
    for man_path in sorted(root.glob("watchfaces/*/engine/handoff.json")):
        rel = man_path.relative_to(root)
        slug = man_path.parents[1].name
        try:
            man = json.loads(man_path.read_text())
        except json.JSONDecodeError as e:
            err(f"handoff[{rel}]: invalid JSON: {e}")
            continue
        if man.get("contract") != "docs/ASSET_HANDOFF_CONTRACT.md":
            err(f"handoff[{rel}]: missing/wrong contract reference")
        for a in man.get("assets", []):
            aid = a.get("asset_id", "<missing asset_id>")

            def bad(msg: str) -> None:
                err(f"handoff[{rel}] {aid}: {msg}")

            for key in HANDOFF_REQUIRED:
                if key not in a:
                    bad(f"missing field {key}")
            if not re.fullmatch(r"[a-z0-9-]+/[A-Za-z0-9_]+",
                                str(a.get("asset_id", ""))):
                bad(f"asset_id {a.get('asset_id')!r} violates pattern "
                    "<class>/<PartName>")
            if a.get("source_repo") != "xsytrance/AGENOR-Horology":
                bad("unexpected source_repo")
            if not re.fullmatch(r"[0-9a-f]{40}", str(a.get("source_commit", ""))):
                bad("source_commit is not a full 40-char SHA")
            sp = a.get("source_paths")
            if (not isinstance(sp, list) or not sp
                    or not all(isinstance(s, str) and s for s in sp)):
                bad("source_paths must be a nonempty list of nonempty strings")
            if not (isinstance(a.get("spec_path"), str) and a.get("spec_path")):
                bad("spec_path must be a nonempty string")
            if a.get("export_type") not in HANDOFF_EXPORT_TYPES:
                bad(f"bad export_type {a.get('export_type')!r}")
            dims = a.get("dimensions")
            if (not isinstance(dims, list) or len(dims) != 2
                    or not all(isinstance(d, int) and not isinstance(d, bool)
                               and d >= 1 for d in dims)):
                bad(f"dimensions {dims!r} must be [w, h] positive integers")
            if a.get("color_space") != "srgb":
                bad(f"bad color_space {a.get('color_space')!r} (allowed: srgb)")
            if a.get("alpha") not in ("straight", "premultiplied", "none"):
                bad(f"bad alpha {a.get('alpha')!r}")
            piv = a.get("pivot")
            if (not isinstance(piv, list) or len(piv) != 2
                    or not all(isinstance(p, (int, float))
                               and not isinstance(p, bool)
                               and 0 <= p <= 1 for p in piv)):
                bad(f"pivot {piv!r} must be [x, y] numbers in 0..1")
            frames = a.get("frames")
            if (not isinstance(frames, int) or isinstance(frames, bool)
                    or frames < 1):
                bad(f"frames {frames!r} must be an integer >= 1")
            fs = a.get("frame_seconds")
            if fs is not None and (not isinstance(fs, (int, float))
                                   or isinstance(fs, bool) or fs <= 0):
                bad(f"frame_seconds {fs!r} must be a positive number or null")
            if isinstance(frames, int) and frames > 1 and fs is None:
                bad("animated export (frames > 1) requires frame_seconds")
            if a.get("loop") not in ("perfect", "pingpong", "none"):
                bad(f"bad loop {a.get('loop')!r}")
            if not isinstance(a.get("aod_safe"), bool):
                bad("aod_safe must be a boolean")
            if not (isinstance(a.get("license"), str) and a.get("license")):
                bad("license must be a nonempty provenance string")
            if a.get("lifecycle") not in HANDOFF_LIFECYCLES:
                bad(f"bad lifecycle {a.get('lifecycle')!r}")
            if not (isinstance(a.get("consumer_component"), str)
                    and a.get("consumer_component")):
                bad("consumer_component must be a nonempty string")
            if not (isinstance(a.get("regenerate"), str) and a.get("regenerate")):
                bad("regenerate must be a nonempty command string")

            is_example = a.get("example") is True
            dest = a.get("destination")
            sha = a.get("sha256")
            if sha is not None and not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
                bad("sha256 is not 64 lowercase hex chars")
            if dest is None:
                if not is_example:
                    bad("null destination on a non-example entry")
                continue
            if not isinstance(dest, str):
                bad(f"destination {dest!r} must be a string path")
                continue
            # Containment: inside THIS face's res/ tree, no traversal.
            required_prefix = f"watchfaces/{slug}/app/src/main/res/"
            norm = str(Path(dest).as_posix())
            if ".." in Path(dest).parts or Path(dest).is_absolute():
                bad(f"destination {dest} uses path traversal / absolute path")
            elif not norm.startswith(required_prefix):
                bad(f"destination {dest} is outside {required_prefix}")
            dest_path = root / dest
            if not dest_path.exists():
                bad(f"destination {dest} does not exist")
                continue
            if sha is None:
                bad("real destination requires a sha256 (null allowed only "
                    "with a null-destination example entry)")
            elif sha256(dest_path) != sha:
                bad(f"sha256 mismatch for {dest} — bytes changed without a "
                    "manifest update")


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


def check_visual(root: Path) -> None:
    """Visual-lineage gate, stdlib portion (ADR-009).

    Hash-level enforcement: approved goldens may only exist/change with a
    matching owner-approved record; committed inventory must be covered by
    an approval record; record schema completeness. Pixel-level checks
    (deterministic re-render, comparison, mask coverage) live in
    tests/visual/ and CI, which have the pinned Pillow dependency.
    """
    import tomllib

    for states_path in sorted(root.glob("watchfaces/*/visual/states.toml")):
        vdir = states_path.parent
        face = vdir.parent.name
        with open(states_path, "rb") as fh:
            contract = tomllib.load(fh)
        approved_version = contract["goldens"]["approved_version"]

        # --- load and schema-check approval records -----------------------
        records = []
        required = {"approval_id", "face", "visual_version",
                    "previous_visual_version", "previous_goldens",
                    "proposed_goldens", "inventory_sha256",
                    "changed_resources", "handoff_asset_ids", "metrics",
                    "previews", "rationale", "owner", "architecture_review",
                    "device_evidence"}
        for rp in sorted(vdir.glob("approvals/*.json")):
            try:
                rec = json.loads(rp.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                err(f"visual[{face}]: {rp.name}: invalid JSON ({e})")
                continue
            missing = required - set(rec)
            if missing:
                err(f"visual[{face}]: {rp.name}: missing fields "
                    f"{sorted(missing)}")
                continue
            owner = rec["owner"]
            if owner.get("status") not in ("proposed", "approved",
                                           "rejected"):
                err(f"visual[{face}]: {rp.name}: owner.status must be "
                    f"proposed|approved|rejected")
                continue
            for kind, sha in (rec["proposed_goldens"] or {}).items():
                if not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
                    err(f"visual[{face}]: {rp.name}: proposed_goldens."
                        f"{kind} is not a sha256")
            records.append(rec)

        # --- approved goldens require a matching approved record ----------
        gdir = vdir / "goldens" / approved_version
        approved_recs = [r for r in records
                         if r["visual_version"] == approved_version
                         and r["owner"]["status"] == "approved"]
        if not gdir.is_dir():
            err(f"visual[{face}]: approved goldens missing: {gdir}")
        elif not approved_recs:
            err(f"visual[{face}]: goldens/{approved_version} exists with no "
                f"owner-approved record in approvals/ (ADR-009 §5)")
        else:
            rec = approved_recs[-1]
            for kind in ("normal", "aod"):
                gp = gdir / f"{kind}.png"
                if not gp.exists():
                    err(f"visual[{face}]: missing golden {gp.name} in "
                        f"{approved_version}")
                    continue
                actual = sha256(gp)
                recorded = rec["proposed_goldens"].get(kind)
                if actual != recorded:
                    err(f"visual[{face}]: {kind} golden hash {actual[:12]}… "
                        f"does not match approved record "
                        f"{rec['approval_id']} ({str(recorded)[:12]}…) — "
                        f"approved goldens may not change without a new "
                        f"approved record")
            meta_p = gdir / "METADATA.json"
            if meta_p.exists():
                meta = json.loads(meta_p.read_text(encoding="utf-8"))
                for kind in ("normal", "aod"):
                    mrec = meta.get("renders", {}).get(kind, {})
                    gp = gdir / f"{kind}.png"
                    if gp.exists() and mrec.get("sha256") != sha256(gp):
                        err(f"visual[{face}]: METADATA.json {kind} sha "
                            f"disagrees with the committed golden bytes")
            else:
                warn(f"visual[{face}]: goldens/{approved_version} has no "
                     f"METADATA.json")

        # --- committed inventory must be covered by some record -----------
        inv_p = vdir / "inventories" / "inventory.json"
        if not inv_p.exists():
            err(f"visual[{face}]: no committed resource inventory "
                f"(tools/inventory_resources.py {face})")
        else:
            if records:
                inv_sha = sha256(inv_p)
                if not any(r["inventory_sha256"] == inv_sha
                           for r in records):
                    err(f"visual[{face}]: committed inventory "
                        f"({inv_sha[:12]}…) is not bound to any approval "
                        f"record — resource changes need a proposed/"
                        f"approved visual record (ADR-009 §5)")
            # --- committed inventory must match the live tree bytes -------
            # (the WARBIRD failure class: same name, wrong bytes)
            inv = json.loads(inv_p.read_text(encoding="utf-8"))
            face_dir = vdir.parent
            listed = set()
            for r in inv.get("resources", []):
                p = face_dir / r["path"]
                listed.add(r["path"])
                if not p.exists():
                    err(f"visual[{face}]: inventoried resource missing "
                        f"from tree: {r['path']}")
                elif sha256(p) != r["sha256"]:
                    err(f"visual[{face}]: resource bytes drifted from "
                        f"committed inventory: {r['path']} (same-name/"
                        f"wrong-bytes — WARBIRD failure class, ADR-009 §3)")
            res_root = face_dir / "app/src/main/res"
            if res_root.is_dir():
                for p in sorted(res_root.rglob("*")):
                    if p.is_file():
                        rel = str(p.relative_to(face_dir))
                        if rel not in listed:
                            err(f"visual[{face}]: uninventoried runtime "
                                f"resource: {rel} (regenerate + review "
                                f"the inventory)")


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
    check_engine(root)
    check_handoff(root)
    check_visual(root)

    errors = [m for s, m in issues if s == "ERROR"]
    warns = [m for s, m in issues if s == "WARN"]
    for s, m in issues:
        print(f"{s:5} {m}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s) — "
          f"{len(faces)} source faces checked, aapt2={'yes' if aapt2 else 'MISSING'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
