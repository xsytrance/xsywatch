#!/usr/bin/env python3
"""Release-candidate artifact inspection and cross-source consistency gate.

Checks that one identity is stated consistently everywhere it appears —
engine/face.toml, app/build.gradle.kts, AndroidManifest.xml, the generated
WFF XML, and the bytes actually inside the packaged .aab and .apk — and
writes the candidate manifest.

    python3 tools/verify_candidate.py aurelius --version 2.0.0-rc1 \
        --aab <path.aab> --apk <path.apk> [--write-manifest]

Exit codes: 0 all consistent, 1 an inconsistency, 2 bad invocation.

Nothing here signs anything, and it refuses to record a candidate as
published.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

issues: list[str] = []


def err(msg: str) -> None:
    issues.append(msg)
    print(f"ERROR {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def aapt2() -> str | None:
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not home:
        return None
    cands = sorted((Path(home) / "build-tools").glob("*/aapt2"), reverse=True)
    return str(cands[0]) if cands else shutil.which("aapt2")


def badging(tool: str, apk: Path) -> dict | None:
    r = subprocess.run([tool, "dump", "badging", str(apk)],
                       capture_output=True, text=True)
    if r.returncode:
        return None
    m = re.search(r"package: name='([^']+)' versionCode='(\d+)' "
                  r"versionName='([^']*)'", r.stdout)
    t = re.search(r"targetSdkVersion:'(\d+)'", r.stdout)
    s = re.search(r"minSdkVersion:'(\d+)'", r.stdout)
    if not m:
        return None
    return {"package": m.group(1), "versionCode": int(m.group(2)),
            "versionName": m.group(3),
            "targetSdk": int(t.group(1)) if t else None,
            "minSdk": int(s.group(1)) if s else None}


def describe_signing(path: Path, bundle: bool = False) -> str:
    """Signing state, via apksigner where available.

    Absence of META-INF/*.RSA proves nothing on a modern APK: Signature
    Scheme v2/v3 keeps the signature block in the ZIP central directory.
    """
    if bundle:
        with zipfile.ZipFile(path) as z:
            has = any(n.startswith("META-INF/")
                      and n.endswith((".RSA", ".DSA", ".EC"))
                      for n in z.namelist())
        return ("signed" if has
                else "unsigned — no upload key exists (ADR-010 §5)")
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    signer = None
    if home:
        c = sorted((Path(home) / "build-tools").glob("*/apksigner"),
                   reverse=True)
        signer = str(c[0]) if c else None
    if signer:
        env = dict(os.environ)
        jh = env.get("JAVA_HOME")
        if jh:
            env["PATH"] = f"{jh}/bin:" + env.get("PATH", "")
        r = subprocess.run([signer, "verify", "--print-certs", str(path)],
                           capture_output=True, text=True, env=env)
        if r.returncode == 0:
            m = re.search(r"Signer #1 certificate DN: (.+)", r.stdout)
            dn = m.group(1).strip() if m else "unknown DN"
            kind = "debug" if "Android Debug" in dn else "NON-DEBUG"
            return f"{kind} ({dn})"
        if "DOES NOT VERIFY" in (r.stdout + r.stderr):
            return "unsigned"
    with zipfile.ZipFile(path) as z:
        has = any(n.startswith("META-INF/")
                  and n.endswith((".RSA", ".DSA", ".EC"))
                  for n in z.namelist())
    return "v1-signed" if has else "signing state undetermined"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--version", required=True)
    ap.add_argument("--aab", required=True)
    ap.add_argument("--apk", required=True)
    ap.add_argument("--write-manifest", action="store_true")
    args = ap.parse_args()

    face_dir = REPO / "watchfaces" / args.face
    aab, apk = Path(args.aab), Path(args.apk)
    for p in (aab, apk):
        if not p.exists():
            print(f"ERROR missing artifact {p}", file=sys.stderr)
            return 2

    # ---- declared identity, from every source that states it -----------
    import tomllib
    with open(face_dir / "engine/face.toml", "rb") as fh:
        spec = tomllib.load(fh)
    ident = spec["identity"]
    gradle_txt = (face_dir / "app/build.gradle.kts").read_text()

    def g(pat):
        m = re.search(pat, gradle_txt)
        return m.group(1) if m else None

    gradle = {
        "package": g(r'applicationId\s*=\s*"([^"]+)"'),
        "versionCode": g(r"versionCode\s*=\s*(\d+)"),
        "versionName": g(r'versionName\s*=\s*"([^"]+)"'),
        "minSdk": g(r"minSdk\s*=\s*(\d+)"),
        "targetSdk": g(r"targetSdk\s*=\s*(\d+)"),
        "compileSdk": g(r"compileSdk\s*=\s*(\d+)"),
        "namespace": g(r'namespace\s*=\s*"([^"]+)"'),
    }

    # face.toml <-> gradle
    if str(ident["package"]) != gradle["package"]:
        err(f"face.toml package {ident['package']} != gradle "
            f"{gradle['package']}")
    else:
        ok(f"package consistent: {gradle['package']}")
    if str(ident["version_code"]) != gradle["versionCode"]:
        err(f"face.toml version_code {ident['version_code']} != gradle "
            f"{gradle['versionCode']}")
    else:
        ok(f"versionCode consistent: {gradle['versionCode']}")
    if str(ident["version_name"]) != gradle["versionName"]:
        err(f"face.toml version_name {ident['version_name']} != gradle "
            f"{gradle['versionName']}")
    else:
        ok(f"versionName consistent: {gradle['versionName']}")
    if gradle["namespace"] != gradle["package"]:
        err(f"namespace {gradle['namespace']} != applicationId "
            f"{gradle['package']}")
    if gradle["versionName"] != args.version:
        err(f"gradle versionName {gradle['versionName']} != requested "
            f"candidate version {args.version}")

    # ---- WFF version: spec, manifest resource, generated XML ----------
    wff_spec = spec["face"]["wff_version"]
    man = (face_dir / "app/src/main/AndroidManifest.xml").read_text()
    if 'android:name="com.google.wear.watchface.format.version"' not in man:
        err("AndroidManifest does not declare the WFF format version")
    res_int = None
    for xml in (face_dir / "app/src/main/res").rglob("*.xml"):
        m = re.search(r'<integer name="wff_version">(\d+)</integer>',
                      xml.read_text(errors="ignore"))
        if m:
            res_int = int(m.group(1))
            break
    if res_int is None:
        err("could not resolve @integer/wff_version")
    elif res_int != wff_spec:
        err(f"@integer/wff_version {res_int} != face.toml {wff_spec}")
    else:
        ok(f"WFF version consistent: {wff_spec}")

    # WFF v4 requires Wear OS 6 / API 36
    floors = {1: 33, 2: 34, 3: 35, 4: 36}
    need = floors.get(int(wff_spec))
    if need and gradle["minSdk"] and int(gradle["minSdk"]) < need:
        err(f"minSdk {gradle['minSdk']} is below the API {need} floor for "
            f"WFF v{wff_spec} — the package would install on devices that "
            f"cannot render it")
    elif need:
        ok(f"minSdk {gradle['minSdk']} satisfies the WFF v{wff_spec} floor "
           f"(API {need})")

    # ---- APK: real metadata from aapt2 ---------------------------------
    tool = aapt2()
    apk_meta = badging(tool, apk) if tool else None
    if apk_meta is None:
        err("aapt2 unavailable or could not read the APK")
    else:
        for label, want, got in (
            ("package", gradle["package"], apk_meta["package"]),
            ("versionCode", int(gradle["versionCode"]), apk_meta["versionCode"]),
            ("versionName", gradle["versionName"], apk_meta["versionName"]),
            ("targetSdk", int(gradle["targetSdk"]), apk_meta["targetSdk"]),
            ("minSdk", int(gradle["minSdk"]), apk_meta["minSdk"]),
        ):
            if want != got:
                err(f"APK {label}={got!r} != source {want!r}")
        if not issues:
            ok(f"APK metadata matches source: {apk_meta}")

    # ---- packaged bytes match the repository ---------------------------
    repo_xml = face_dir / "app/src/main/res/raw/watchface.xml"
    with zipfile.ZipFile(apk) as z:
        names = z.namelist()
        if "res/raw/watchface.xml" in names:
            pk = hashlib.sha256(z.read("res/raw/watchface.xml")).hexdigest()
            if pk != sha256(repo_xml):
                err("packaged watchface.xml differs from the repository copy")
            else:
                ok("packaged watchface.xml is byte-identical to source")
        else:
            err("APK contains no res/raw/watchface.xml")

    # ---- the bundle must contain no dex (WFF requirement) --------------
    with zipfile.ZipFile(aab) as z:
        names = z.namelist()
        dex = [n for n in names if n.endswith(".dex")]
        if dex:
            err(f"bundle contains dex, which Play rejects for a watch face: "
                f"{dex}")
        else:
            ok("bundle contains no dex")
        if not any(n.startswith("base/manifest/") for n in names):
            err("bundle has no base/manifest")
        if not any(n.startswith("base/res/") for n in names):
            err("bundle has no base/res")
        if "base/res/raw/watchface.xml" in names:
            bk = hashlib.sha256(
                z.read("base/res/raw/watchface.xml")).hexdigest()
            if bk != sha256(repo_xml):
                err("bundle watchface.xml differs from the repository copy")
            else:
                ok("bundle watchface.xml is byte-identical to source")
        else:
            err("bundle contains no base/res/raw/watchface.xml")

    # ---- signing state --------------------------------------------------
    # A v1 JAR signature lives in META-INF/*.RSA, but APK Signature Scheme
    # v2/v3 stores the block in the ZIP central directory instead, so an
    # absent META-INF entry does NOT mean unsigned. Ask apksigner.
    apk_signing = describe_signing(apk)
    aab_signing = describe_signing(aab, bundle=True)
    ok(f"signing — apk: {apk_signing}, aab: {aab_signing}")
    if "production" in apk_signing or "release" in apk_signing:
        err("the device-test APK appears to carry a non-debug signature; "
            "Phase 4 must not create production signing material")

    result = {
        "face": args.face,
        "candidate_version": args.version,
        "identity": {
            "package": gradle["package"],
            "versionCode": int(gradle["versionCode"]),
            "versionName": gradle["versionName"],
            "minSdk": int(gradle["minSdk"]),
            "targetSdk": int(gradle["targetSdk"]),
            "compileSdk": int(gradle["compileSdk"]),
            "wff_version": wff_spec,
        },
        "artifacts": {
            "aab": {"name": aab.name, "sha256": sha256(aab),
                    "size_bytes": aab.stat().st_size,
                    "signing": aab_signing, "contains_dex": False},
            "apk_debug": {"name": apk.name, "sha256": sha256(apk),
                          "size_bytes": apk.stat().st_size,
                          "signing": apk_signing},
        },
        "publication_status": "not published",
        "consistent": not issues,
        "problems": issues,
    }

    if args.write_manifest:
        out = REPO / "releases" / args.face / "candidates" / args.version
        out.mkdir(parents=True, exist_ok=True)
        (out / "VERIFY.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"wrote {out / 'VERIFY.json'}")

    print()
    print(f"{len(issues)} problem(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
