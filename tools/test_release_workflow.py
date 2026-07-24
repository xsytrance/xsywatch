#!/usr/bin/env python3
"""Self-test for the release workflow and validator (Phase-1 review §blocker-2.8).

Builds a sandboxed copy of the repo (git-initialized, pulseface only) and proves:

  T1  packaging an initial release creates releases/pulseface/current (v1.0)
  T2  re-packaging the SAME version refuses (no silent overwrite)
  T3  after a real version bump + Gradle rebuild, packaging archives the old
      current under v1.0 (bytes identical to what was released) and installs
      v1.0.1 as current; manifest carries both (slug,channel) entries
  T4  validation passes on the two-channel state
  T5  corrupting the current APK        -> validation FAILS
  T6  tampering manifest versionName    -> validation FAILS
  T7  bumping source versionName only   -> validation FAILS (source/release drift)
  T8  adding a tracked font w/o license -> validation FAILS
  T9  wrong sha256 in license inventory -> validation FAILS
  T10 ambiguous distinct previews       -> packaging refuses

Requires: JDK 21 (JAVA_HOME or Android Studio JBR), ANDROID_HOME with
build-tools, network/gradle cache for the sandbox rebuild, and a prebuilt
pulseface app-debug.apk (run tools/build_face.sh pulseface first).

Usage: python3 tools/test_release_workflow.py
Exit 0 only if every expectation holds. Sandbox is kept on failure for autopsy.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
results: list[tuple[str, bool, str]] = []


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)


def record(tid: str, ok: bool, note: str) -> None:
    results.append((tid, ok, note))
    print(f"  {tid}: {'PASS' if ok else 'FAIL'} — {note}")


def validate(sandbox: Path) -> int:
    return run([PY, str(sandbox / "tools/validate.py"),
                "--repo-root", str(sandbox)], cwd=sandbox).returncode


def package(sandbox: Path, *extra) -> subprocess.CompletedProcess:
    return run([PY, str(sandbox / "tools/package_release.py"), "pulseface",
                "--repo-root", str(sandbox), *extra], cwd=sandbox)


def main() -> None:
    built = REPO / "watchfaces/pulseface/app/build/outputs/apk/debug/app-debug.apk"
    if not built.exists():
        sys.exit("prerequisite missing: run tools/build_face.sh pulseface first")

    sandbox = Path(tempfile.mkdtemp(prefix="agenor-relworkflow-"))
    print(f"sandbox: {sandbox}")

    # -- assemble sandbox repo ------------------------------------------------
    (sandbox / "docs").mkdir()
    shutil.copytree(REPO / "tools", sandbox / "tools",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO / "THIRD_PARTY_NOTICES", sandbox / "THIRD_PARTY_NOTICES")
    shutil.copytree(REPO / "watchfaces/pulseface", sandbox / "watchfaces/pulseface",
                    ignore=shutil.ignore_patterns("build", ".gradle", "__pycache__"))
    inv = json.loads((REPO / "docs/asset-licenses.json").read_text())
    inv["assets"] = [a for a in inv["assets"] if a["path"].startswith("watchfaces/pulseface/")]
    (sandbox / "docs/asset-licenses.json").write_text(json.dumps(inv, indent=2))
    # minimal README so source checks pass; gitignore mirrors the real one
    shutil.copy2(REPO / ".gitignore", sandbox / ".gitignore")
    sdk = os.environ.get("ANDROID_HOME", os.path.expanduser("~/Android/Sdk"))
    (sandbox / "watchfaces/pulseface/local.properties").write_text(f"sdk.dir={sdk}\n")
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"]):
        r = run(cmd, cwd=sandbox)
        if r.returncode:
            sys.exit(f"sandbox git setup failed: {r.stderr}")
    outdir = sandbox / "watchfaces/pulseface/app/build/outputs/apk/debug"
    outdir.mkdir(parents=True)
    shutil.copy2(built, outdir / "app-debug.apk")
    v1_sha = sha256(outdir / "app-debug.apk")

    # -- T1: initial packaging -----------------------------------------------
    r = package(sandbox)
    cur_apk = sandbox / "releases/pulseface/current/pulseface.apk"
    record("T1", r.returncode == 0 and cur_apk.exists() and sha256(cur_apk) == v1_sha,
           "initial release packaged to current (v1.0)")

    # -- T2: same version refused --------------------------------------------
    r = package(sandbox)
    record("T2", r.returncode != 0 and "bump the" in (r.stdout + r.stderr),
           "re-packaging same version refused")

    # -- T3: bump, rebuild, package => archive + new current -------------------
    gradle_file = sandbox / "watchfaces/pulseface/app/build.gradle.kts"
    t = gradle_file.read_text()
    t = re.sub(r"versionCode\s*=\s*1\b", "versionCode = 2", t, count=1)
    t = re.sub(r'versionName\s*=\s*"1\.0"', 'versionName = "1.0.1"', t, count=1)
    gradle_file.write_text(t)
    env = dict(os.environ,
               JAVA_HOME=os.environ.get("JAVA_HOME",
                                        os.path.expanduser("~/Android/android-studio/jbr")))
    r = run(["./gradlew", "--console=plain", "-q", "assembleDebug"],
            cwd=sandbox / "watchfaces/pulseface", env=env)
    if r.returncode:
        sys.exit(f"sandbox rebuild failed:\n{r.stdout}\n{r.stderr}")
    v2_sha = sha256(outdir / "app-debug.apk")
    r = package(sandbox)
    arch_apk = sandbox / "releases/pulseface/v1.0/pulseface.apk"
    man = json.loads((sandbox / "releases/MANIFEST.json").read_text())
    chans = man["faces"].get("pulseface", {}).get("channels", {})
    ok = (r.returncode == 0
          and arch_apk.exists() and sha256(arch_apk) == v1_sha
          and sha256(cur_apk) == v2_sha
          and set(chans) == {"current", "v1.0"}
          and chans["current"]["versionName"] == "1.0.1"
          and chans["v1.0"]["versionName"] == "1.0")
    record("T3", ok, "v1.0 archived byte-identical; v1.0.1 is current; manifest has both channels")

    # -- T4: validation passes on two-channel state ---------------------------
    run(["git", "add", "-A"], cwd=sandbox)
    record("T4", validate(sandbox) == 0, "validation passes with current + v1.0")

    # -- tamper fixtures (each must FAIL validation, then be restored) --------
    orig = cur_apk.read_bytes()
    cur_apk.write_bytes(orig[:100] + bytes([orig[100] ^ 0xFF]) + orig[101:])
    record("T5", validate(sandbox) != 0, "corrupted current APK detected")
    cur_apk.write_bytes(orig)

    man_path = sandbox / "releases/MANIFEST.json"
    man_orig = man_path.read_text()
    man_path.write_text(man_orig.replace('"versionName": "1.0.1"', '"versionName": "9.9.9"'))
    record("T6", validate(sandbox) != 0, "manifest versionName tamper detected")
    man_path.write_text(man_orig)

    g_orig = gradle_file.read_text()
    gradle_file.write_text(g_orig.replace('versionName = "1.0.1"', 'versionName = "9.9"'))
    record("T7", validate(sandbox) != 0, "source-vs-release version drift detected")
    gradle_file.write_text(g_orig)

    rogue = sandbox / "watchfaces/pulseface/app/src/main/res/font"
    rogue.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sandbox / "watchfaces/pulseface/tools/fonts/orbitron.ttf",
                 rogue / "rogue.ttf")
    run(["git", "add", "-A"], cwd=sandbox)
    record("T8", validate(sandbox) != 0, "unlicensed tracked font detected")
    run(["git", "rm", "-q", "-f", "app/src/main/res/font/rogue.ttf"],
        cwd=sandbox / "watchfaces/pulseface")

    inv_path = sandbox / "docs/asset-licenses.json"
    inv_orig = inv_path.read_text()
    bad = json.loads(inv_orig)
    bad["assets"][0]["sha256"] = "0" * 64
    inv_path.write_text(json.dumps(bad, indent=2))
    record("T9", validate(sandbox) != 0, "license-inventory sha mismatch detected")
    inv_path.write_text(inv_orig)

    # -- T10: ambiguous previews refuse packaging -----------------------------
    res = sandbox / "watchfaces/pulseface/app/src/main/res"
    alt = res / "drawable-nodpi/preview.png"
    alt.parent.mkdir(exist_ok=True)
    existing = next(iter(sorted(res.glob("drawable*/preview.png"))))
    data = bytearray(existing.read_bytes())
    data[-1] ^= 0xFF  # distinct content
    alt.write_bytes(bytes(data))
    r = package(sandbox, "--force-same-version")
    record("T10", r.returncode != 0 and "ambiguous" in (r.stdout + r.stderr),
           "ambiguous distinct previews refused")
    alt.unlink()

    # -- summary --------------------------------------------------------------
    failed = [t for t, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print(f"FAILED: {', '.join(failed)} — sandbox kept at {sandbox}")
        sys.exit(1)
    shutil.rmtree(sandbox)
    print("all release-workflow fixtures behaved as required; sandbox removed")


if __name__ == "__main__":
    main()
