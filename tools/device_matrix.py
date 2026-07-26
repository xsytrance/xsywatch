#!/usr/bin/env python3
"""Physical Watch7 device matrix — run the automatable rows, refuse to invent the rest.

The Checkpoint B physical matrix has been executed by hand every time, which
is slow, fiddly while a watch is awake and waiting, and easy to get subtly
wrong. Most of it is not actually subjective: pulling the installed APK back
and hashing it, comparing packaged resources against repository bytes, ten
sleep/wake cycles, crash/ANR scanning, per-region motion analysis and touch
inertness are all measurable. This runs those, and emits a
DEVICE_TEST_RESULTS.md bound to the APK hash taken FROM THE DEVICE.

    python3 tools/device_matrix.py aurelius --version 2.0.0-rc2
    python3 tools/device_matrix.py aurelius --version 2.0.0-rc2 --serial 192.168.1.183:45079

What it will NOT do
-------------------
It never marks an owner row PASS. Parallax on wrist tilt, legibility at
actual scale, whether the reserve ticks read as usable, whether any stripe
or unintended ornament entered the face, and the two heart-rate recordings
(post-exertion tracking, off-wrist fallback) all require a human looking at
a physical object. Those rows are emitted as `PENDING — owner` and the
document says so in the same table as the measured rows, so an unfinished
matrix cannot be mistaken for a finished one.

Fail-closed, like the rest of the Phase-4 tooling: a row that cannot be run
is recorded as BLOCKED with the reason. Nothing is silently skipped, and no
row defaults to PASS.

This tool produces EVIDENCE. It deliberately does not touch READINESS.json —
gate states are re-derived by a human who has read the evidence. (The
readiness checker only catches a gate claiming more than its evidence
supports; it cannot notice a stale record, which is exactly how one sat
wrong for a session.)

Requires: adb on PATH, Pillow. ffmpeg is optional — without it the motion
and heart-rate rows are recorded as BLOCKED rather than guessed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Rows that need a human. The tool refuses to score these.
OWNER_ROWS = [
    ("Parallax on wrist tilt",
     "background/sheen shift as the wrist tilts, with no edge clipping"),
    ("Normal legibility at actual scale",
     "hands and date read instantly on the panel, not on a monitor"),
    ("Command Satin legibility",
     "the engraving remains readable at actual scale"),
    ("Reserve ticks",
     "more usable than the previous revision without becoming loud"),
    ("No stripe or unintended ornament",
     "nothing entered the face that is not in the approved reference"),
    ("AOD content restraint",
     "ambient frame reads as restrained, no bright sheen"),
    ("Battery gauge plausibility",
     "needle position agrees with Settings battery %"),
    ("Time vs reference clock",
     "analog time matches an independent clock"),
    ("Heart rate tracks after exertion",
     "record ~14s after deliberate exertion; implied HR must RISE, not merely "
     "differ from the 70.0 bpm fallback"),
    ("Heart rate falls back off-wrist",
     "record ~14s with the watch off the wrist; implied HR must collapse to "
     "exactly 70.0 bpm"),
]


class Adb:
    def __init__(self, serial: str | None):
        self.base = ["adb"] + (["-s", serial] if serial else [])

    def run(self, *args: str, timeout: int = 120,
            binary: bool = False) -> subprocess.CompletedProcess:
        return subprocess.run(self.base + list(args), timeout=timeout,
                              capture_output=True,
                              text=not binary)

    def sh(self, cmd: str, timeout: int = 120) -> str:
        r = self.run("shell", cmd, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")

    def devices(self) -> list[str]:
        out = self.run("devices").stdout or ""
        return [ln.split("\t")[0] for ln in out.splitlines()[1:]
                if "\tdevice" in ln]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class Matrix:
    """Collects rows. A row is (check, result, detail)."""

    def __init__(self):
        self.rows: list[tuple[str, str, str]] = []
        self.data: dict = {}

    def add(self, check: str, result: str, detail: str) -> None:
        self.rows.append((check, result, detail))
        print(f"{result:8} {check}" + (f" — {detail[:90]}" if detail else ""))

    def counts(self) -> dict[str, int]:
        c: dict[str, int] = {}
        for _, r, _ in self.rows:
            c[r] = c.get(r, 0) + 1
        return c


# --------------------------------------------------------------------------
# individual rows
# --------------------------------------------------------------------------

def row_device_identity(adb: Adb, m: Matrix) -> None:
    props = {}
    for k in ("ro.product.model", "ro.build.version.release",
              "ro.build.version.sdk", "ro.build.display.id"):
        props[k] = adb.sh(f"getprop {k}").strip()
    m.data["device"] = props
    if not props.get("ro.product.model"):
        m.add("Device identity", "BLOCKED", "getprop returned nothing")
        return
    m.add("Device identity", "PASS",
          f"{props['ro.product.model']}, Android "
          f"{props['ro.build.version.release']} / API "
          f"{props['ro.build.version.sdk']}")


def installed_apk_path(adb: Adb, pkg: str) -> str | None:
    out = adb.sh(f"pm path {pkg}")
    mm = re.search(r"package:(\S+base\.apk)", out)
    return mm.group(1) if mm else None


def pull_installed(adb: Adb, pkg: str, dest: Path) -> str | None:
    """Pull the installed base.apk back and hash it. Returns sha256."""
    remote = installed_apk_path(adb, pkg)
    if not remote:
        return None
    r = adb.run("pull", remote, str(dest), timeout=300)
    if not dest.exists():
        return None
    return sha256_file(dest)


def row_upgrade_continuity(adb: Adb, m: Matrix, pkg: str, apk: Path,
                           work: Path, do_install: bool) -> str | None:
    before = {}
    dump = adb.sh(f"dumpsys package {pkg}")
    for key, pat in (("versionCode", r"versionCode=(\d+)"),
                     ("versionName", r"versionName=(\S+)"),
                     ("minSdk", r"minSdk=(\d+)")):
        mm = re.search(pat, dump)
        before[key] = mm.group(1) if mm else None
    pre_sha = None
    if before.get("versionCode"):
        pre_sha = pull_installed(adb, pkg, work / "pre_base.apk")

    if do_install:
        r = adb.run("install", "-r", str(apk), timeout=600)
        out = (r.stdout or "") + (r.stderr or "")
        if "Success" not in out:
            m.add("Install / upgrade continuity", "FAIL",
                  f"adb install -r did not report Success: {out.strip()[:200]}")
            return None
    else:
        m.add("Install / upgrade continuity", "SKIPPED",
              "--skip-install given; the package already on the device is "
              "being tested as-is")

    dump = adb.sh(f"dumpsys package {pkg}")
    after = {}
    for key, pat in (("versionCode", r"versionCode=(\d+)"),
                     ("versionName", r"versionName=(\S+)"),
                     ("minSdk", r"minSdk=(\d+)")):
        mm = re.search(pat, dump)
        after[key] = mm.group(1) if mm else None
    m.data["version_before"] = before
    m.data["version_after"] = after
    m.data["pre_upgrade_apk_sha256"] = pre_sha

    if do_install:
        if not after.get("versionCode"):
            m.add("Install / upgrade continuity", "FAIL",
                  "package not present after install")
            return None
        detail = (f"versionCode {before.get('versionCode')} → "
                  f"{after.get('versionCode')}, versionName "
                  f"{before.get('versionName')} → {after.get('versionName')}, "
                  f"minSdk {before.get('minSdk')} → {after.get('minSdk')}; "
                  f"install -r Success, no uninstall, no data clear")

        if pre_sha:
            detail += f"; pre-upgrade installed APK {pre_sha[:12]}…"
        m.add("Install / upgrade continuity", "PASS", detail)

    # the authoritative hash: taken from the device, not the build dir
    post_sha = pull_installed(adb, pkg, work / "post_base.apk")
    if not post_sha:
        m.add("Installed-APK pullback hash", "BLOCKED",
              "could not resolve or pull /data/app base.apk")
        return None
    expect = sha256_file(apk)
    m.data["installed_apk_sha256"] = post_sha
    m.data["candidate_apk_sha256"] = expect
    if post_sha == expect:
        m.add("Installed-APK pullback hash", "PASS",
              f"installed bytes {post_sha[:12]}… are byte-identical to the "
              f"candidate — not a re-signed or re-packaged variant")
    else:
        m.add("Installed-APK pullback hash", "FAIL",
              f"installed {post_sha[:12]}… != candidate {expect[:12]}…")
    return post_sha


def row_runtime_host(adb: Adb, m: Matrix, pkg: str) -> None:
    out = adb.sh("dumpsys activity service "
                 "com.samsung.wear.watchface.runtime")
    if pkg in out:
        m.add("Runtime host", "PASS",
              f"WFF runtime reports resource-only package {pkg}")
    else:
        m.add("Runtime host", "PENDING — owner",
              f"{pkg} not named by the runtime dump. This is the picker "
              f"row: the face must be SELECTED on the watch. Select it and "
              f"re-run.")


def row_permissions(adb: Adb, m: Matrix, pkg: str) -> None:
    dump = adb.sh(f"dumpsys package {pkg}")
    block = re.search(r"requested permissions:\s*\n((?:\s+\S+.*\n)*)", dump)
    perms = []
    if block:
        perms = [ln.strip().split(":")[0]
                 for ln in block.group(1).splitlines() if ln.strip()]
    m.data["requested_permissions"] = perms
    if perms:
        m.add("Requested permissions", "PENDING — owner",
              f"package requests {perms} — rc2 is expected to request NONE; "
              f"a non-empty set needs an explicit decision, not a pass")
    else:
        m.add("Requested permissions", "PASS",
              "zero requested permissions; no sensitive permission is "
              "attributable to this package")


def row_resource_lineage(m: Matrix, installed: Path, inventory: Path) -> None:
    """Compare packaged bytes against the committed inventory."""
    if not installed.exists():
        m.add("Installed-resource lineage", "BLOCKED",
              "no installed APK was pulled back")
        return
    try:
        inv = json.loads(inventory.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        m.add("Installed-resource lineage", "BLOCKED",
              f"cannot read inventory: {e}")
        return

    with zipfile.ZipFile(installed) as z:
        by_base: dict[str, list[str]] = {}
        for n in z.namelist():
            if n.startswith("res/"):
                by_base.setdefault(n.rsplit("/", 1)[-1], []).append(n)
        identical, compiled, drift, ambiguous, absent = [], [], [], [], []
        identical_paths: set[str] = set()
        for entry in inv.get("resources", []):
            # resource_id is null for res/raw entries — never key on it alone
            label = entry.get("resource_id") or entry["path"]
            base = entry["path"].rsplit("/", 1)[-1]
            cands = by_base.get(base, [])
            if not cands:
                # values/*.xml are folded into resources.arsc by design
                (compiled if "/values" in entry["path"] else absent).append(
                    label)
                continue
            if len(cands) > 1:
                ambiguous.append(f"{label} → {cands}")
                continue
            packaged = z.read(cands[0])
            got = sha256_bytes(packaged)
            if got == entry["sha256"]:
                identical.append(label)
                identical_paths.add(entry["path"])
            elif packaged[:4] == b"\x03\x00\x08\x00":
                # Android binary XML magic — compiled at packaging
                compiled.append(label)
            else:
                drift.append(f"{label} ({cands[0]}): "
                             f"{got[:12]}… != {entry['sha256'][:12]}…")

    m.data["resource_lineage"] = {
        "identical": len(identical), "compiled": len(compiled),
        "drift": drift, "ambiguous": ambiguous, "absent": absent,
        "total": len(inv.get("resources", [])),
    }
    if drift or ambiguous or absent:
        m.add("Installed-resource lineage", "FAIL",
              f"{len(identical)} identical, {len(compiled)} compiled, "
              f"{len(drift)} DRIFT, {len(ambiguous)} ambiguous, "
              f"{len(absent)} absent")
        return
    # res/raw/watchface.xml defines every pixel and is stored verbatim, so
    # it must land in the identical bucket — not merely "not drifted".
    raw_verbatim = any(p.endswith("res/raw/watchface.xml")
                       for p in identical_paths)
    detail = (f"{len(identical)} byte-identical to repository source, 0 "
              f"drift; {len(compiled)} compiled at packaging (expected)")
    if raw_verbatim:
        m.add("Installed-resource lineage", "PASS",
              detail + "; res/raw/watchface.xml byte-identical")
    else:
        m.add("Installed-resource lineage", "PENDING — owner",
              detail + "; but res/raw/watchface.xml was NOT confirmed "
                       "verbatim — check the inventory covers it")


def _wakefulness(adb: Adb) -> str:
    mm = re.search(r"mWakefulness=(\w+)", adb.sh("dumpsys power"))
    return mm.group(1) if mm else "?"


def row_aod_cycles(adb: Adb, m: Matrix, out_dir: Path, cycles: int) -> None:
    log = []
    for i in range(cycles):
        adb.sh("input keyevent KEYCODE_SLEEP")
        time.sleep(2.0)
        dozing = _wakefulness(adb)
        adb.sh("input keyevent KEYCODE_WAKEUP")
        time.sleep(2.0)
        awake = _wakefulness(adb)
        log.append(f"cycle {i+1}: sleep→{dozing} wake→{awake}")
    (out_dir / "aod_cycles.log").write_text("\n".join(log) + "\n")
    staged = sum(1 for ln in log if "sleep→Asleep" in ln or "sleep→Dozing" in ln)
    after = out_dir / "after_aod_cycles.png"
    cap = adb.run("exec-out", "screencap", "-p", binary=True, timeout=120)
    if cap.stdout:
        after.write_bytes(cap.stdout)
    m.data["aod_cycles"] = {"count": cycles, "staged": staged}
    if staged == cycles and after.exists():
        m.add(f"AOD — {cycles} sleep/wake cycles", "PASS",
              f"{cycles}/{cycles} staged cleanly; complete render captured "
              f"afterwards ({after.name}) — inspect for resource loss")
    else:
        m.add(f"AOD — {cycles} sleep/wake cycles", "PENDING — owner",
              f"{staged}/{cycles} transitions confirmed via mWakefulness; "
              f"the panel state needs eyes")


def row_doze_capture(adb: Adb, m: Matrix, out_dir: Path) -> None:
    adb.sh("input keyevent KEYCODE_SLEEP")
    time.sleep(45)
    state = _wakefulness(adb)
    cap = adb.run("exec-out", "screencap", "-p", binary=True, timeout=120)
    p = out_dir / "aod_doze_screencap.png"
    if cap.stdout:
        p.write_bytes(cap.stdout)
    adb.sh("input keyevent KEYCODE_WAKEUP")
    if not p.exists():
        m.add("AOD — doze pixel capture", "BLOCKED", "screencap returned nothing")
        return
    try:
        from PIL import Image
        with Image.open(p) as im:
            ex = im.convert("L").getextrema()
    except Exception as e:  # noqa: BLE001 - Pillow optional at this row
        m.add("AOD — doze pixel capture", "BLOCKED", f"cannot read capture: {e}")
        return
    if ex == (0, 0):
        m.add("AOD — doze pixel capture", "NOT OBTAINABLE",
              f"black frame at mWakefulness={state} — the documented Watch7 "
              f"doze display-pipeline limitation, accepted since Phase 2. "
              f"AOD is proven by byte lineage instead, not by this capture")
    else:
        m.add("AOD — doze pixel capture", "PASS",
              f"non-black doze frame captured at mWakefulness={state}")


def row_motion(adb: Adb, m: Matrix, out_dir: Path, face_toml: Path,
               seconds: int) -> Path | None:
    remote = "/sdcard/motion.mp4"
    adb.sh(f"screenrecord --time-limit {seconds} --size 480x480 {remote}",
           timeout=seconds + 120)
    local = out_dir / "motion.mp4"
    adb.run("pull", remote, str(local), timeout=300)
    adb.sh(f"rm -f {remote}")
    if not local.exists():
        m.add("Smoothness / motion", "BLOCKED", "screenrecord produced no file")
        return None
    if not shutil.which("ffmpeg"):
        m.add("Smoothness / motion", "BLOCKED",
              f"recording captured ({local.name}) but ffmpeg is not "
              f"installed, so per-region deltas cannot be computed")
        return local

    boxes = parse_boxes(face_toml)
    frames = out_dir / "frames"
    frames.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(local),
                    "-vf", "fps=30", str(frames / "f%04d.png")],
                   capture_output=True, timeout=600)
    fs = sorted(frames.glob("*.png"))
    if len(fs) < 30:
        m.add("Smoothness / motion", "BLOCKED",
              f"only {len(fs)} frames extracted")
        return local
    try:
        from PIL import Image
    except ImportError:
        m.add("Smoothness / motion", "BLOCKED", "Pillow not installed")
        return local

    stats = {}
    for name, (x, y, w, h) in boxes.items():
        prev = None
        deltas = []
        for f in fs:
            with Image.open(f) as im:
                crop = im.convert("L").crop((x, y, x + w, y + h))
                px = list(crop.getdata())
            if prev is not None:
                deltas.append(sum(abs(a - b) for a, b in zip(px, prev))
                              / len(px))
            prev = px
        if deltas:
            near_static = sum(1 for d in deltas if d < 0.5)
            stats[name] = {"mean_delta": round(sum(deltas) / len(deltas), 3),
                           "near_static_pairs": near_static,
                           "pairs": len(deltas)}
    m.data["motion"] = stats
    moving = {k: v for k, v in stats.items() if v["mean_delta"] > 1.0}
    if moving:
        desc = ", ".join(f"{k} Δ{v['mean_delta']} "
                         f"({v['near_static_pairs']}/{v['pairs']} static)"
                         for k, v in sorted(stats.items()))
        m.add("Smoothness / motion", "PASS",
              f"{len(fs)} frames; per-region inter-frame deltas: {desc}")
    else:
        m.add("Smoothness / motion", "FAIL",
              f"no region shows motion across {len(fs)} frames — the face "
              f"may not be running")
    return local


def parse_boxes(face_toml: Path) -> dict[str, tuple[int, int, int, int]]:
    """Pull named layer boxes out of the face contract.

    Read from the contract rather than hard-coded so this works for any
    engine-migrated face, not just aurelius.
    """
    boxes: dict[str, tuple[int, int, int, int]] = {}
    if not face_toml.exists():
        return boxes
    name = None
    for line in face_toml.read_text(encoding="utf-8").splitlines():
        mm = re.match(r'\s*name\s*=\s*"([^"]+)"', line)
        if mm:
            name = mm.group(1)
            continue
        bm = re.search(r"box\s*=\s*\{x\s*=\s*(\d+),\s*y\s*=\s*(\d+),\s*"
                       r"width\s*=\s*(\d+),\s*height\s*=\s*(\d+)\}", line)
        if bm and name:
            boxes[name] = tuple(int(g) for g in bm.groups())  # type: ignore
            name = None
    return boxes


def row_touch(adb: Adb, m: Matrix, size: int = 480) -> None:
    before = adb.sh("dumpsys activity activities | grep topResumedActivity")
    for x, y in ((size // 2, size // 2), (size // 2 + 80, size // 2 - 20),
                 (120, 260)):
        adb.sh(f"input tap {x} {y}")
        time.sleep(0.6)
    after = adb.sh("dumpsys activity activities | grep topResumedActivity")
    m.data["touch"] = {"before": before.strip()[:200],
                       "after": after.strip()[:200]}
    if before.strip() and before.strip() == after.strip():
        m.add("Touch inertness", "PASS",
              f"three taps changed nothing; topResumedActivity unchanged")
    elif not before.strip():
        m.add("Touch inertness", "BLOCKED",
              "could not read topResumedActivity")
    else:
        m.add("Touch inertness", "FAIL",
              "the foreground activity changed after tapping the face")


def row_stability(adb: Adb, m: Matrix, pkg: str, out_dir: Path) -> None:
    crash = adb.sh("logcat -b crash -d", timeout=180)
    main = adb.sh("logcat -d -v brief", timeout=300)
    (out_dir / "logcat_crash.txt").write_text(crash)
    hits = [ln for ln in crash.splitlines()
            if pkg in ln or "watchface" in ln.lower()]
    fatal = [ln for ln in main.splitlines()
             if ("FATAL EXCEPTION" in ln or "ANR in" in ln)
             and (pkg in ln or "watchface" in ln.lower())]
    m.data["stability"] = {"crash_hits": len(hits), "fatal_or_anr": len(fatal)}
    if hits or fatal:
        m.add("Stability", "FAIL",
              f"{len(hits)} crash-buffer entries, {len(fatal)} FATAL/ANR "
              f"lines mentioning the face")
    else:
        m.add("Stability", "PASS",
              "zero crash-buffer entries and zero FATAL EXCEPTION / ANR "
              "lines mentioning the face or runtime")


def row_heart_rate(m: Matrix, out_dir: Path, motion: Path | None) -> None:
    """Delegate to the existing frequency tool rather than reimplement it."""
    frames = out_dir / "frames"
    tool = REPO / "tools" / "balance_frequency.py"
    if motion is None or not frames.exists() or not tool.exists():
        m.add("Heart rate — implied from balance frequency", "BLOCKED",
              "needs a recording, extracted frames and tools/balance_frequency.py")
        return
    r = subprocess.run([sys.executable, str(tool), str(frames)],
                       capture_output=True, text=True, timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    (out_dir / "balance_frequency.txt").write_text(out)
    hz = re.search(r"([0-9]+\.[0-9]+)\s*Hz", out)
    if not hz:
        m.add("Heart rate — implied from balance frequency", "BLOCKED",
              f"could not parse a frequency: {out.strip()[:160]}")
        return
    f = float(hz.group(1))
    bpm = f * 60.0
    m.data["heart_rate"] = {"hz": f, "implied_bpm": round(bpm, 1)}
    if abs(bpm - 70.0) < 0.6:
        m.add("Heart rate — implied from balance frequency", "PENDING — owner",
              f"{f:.4f} Hz = {bpm:.1f} bpm — indistinguishable from the 70.0 "
              f"bpm FALLBACK. On-wrist this means no live data reached the "
              f"face; off-wrist it is the expected result. Only the owner "
              f"knows which this recording was")
    else:
        m.add("Heart rate — implied from balance frequency", "PASS",
              f"{f:.4f} Hz = {bpm:.1f} bpm — live data, clear of the 70.0 bpm "
              f"fallback. Compare against the watch's own reading")


# --------------------------------------------------------------------------

def _rel(p: Path) -> str:
    """Repo-relative when possible, absolute otherwise — never raise."""
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def emit(m: Matrix, dest: Path, face: str, version: str, apk_sha: str,
         out_dir: Path) -> None:
    c = m.counts()
    dev = m.data.get("device", {})
    lines = [
        f"# {face} {version} — physical Watch7 device matrix",
        "",
        f"**Generated by** `tools/device_matrix.py` — the automatable rows are "
        f"measured, the owner rows are not scored.",
        "",
        f"**Device:** {dev.get('ro.product.model','?')}, Android "
        f"{dev.get('ro.build.version.release','?')} / API "
        f"{dev.get('ro.build.version.sdk','?')}",
        "",
        f"**Candidate APK (hashed FROM THE DEVICE, not the build directory):**",
        "",
        f"```\n{apk_sha}\n```",
        "",
        "## Measured rows",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for check, result, detail in m.rows:
        lines.append(f"| {check} | **{result}** | {detail.replace('|', '/')} |")
    lines += [
        "",
        "## Owner rows — NOT scored by this tool",
        "",
        "These need a human looking at a physical watch. They are listed as",
        "outstanding so an unfinished matrix cannot be mistaken for a",
        "finished one. Replace each `PENDING — owner` with a result and a",
        "note once observed.",
        "",
        "| Check | Result | Criterion |",
        "|---|---|---|",
    ]
    for check, crit in OWNER_ROWS:
        lines.append(f"| {check} | **PENDING — owner** | {crit} |")
    lines += [
        "",
        "## Summary",
        "",
        "| Result | Rows |",
        "|---|---|",
    ]
    for k in sorted(c):
        lines.append(f"| {k} | {c[k]} |")
    lines += [
        f"| PENDING — owner (not scored) | {len(OWNER_ROWS)} |",
        "",
        f"Artefacts under `{_rel(out_dir)}/`.",
        "",
        "## This does not move any gate",
        "",
        "This file is evidence. `READINESS.json` is re-derived by a human who",
        "has read it — the readiness checker only catches a gate claiming",
        "MORE than its evidence supports, so it cannot tell you this document",
        "now exists. After filling in the owner rows, re-derive the record and",
        "re-run `tools/check_candidate_readiness.py`.",
        "",
    ]
    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {_rel(dest)}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--version", required=True)
    ap.add_argument("--serial", help="adb serial, e.g. 192.168.1.183:45079")
    ap.add_argument("--package", default=None,
                    help="defaults to com.xsytrance.<face>")
    ap.add_argument("--cycles", type=int, default=10)
    ap.add_argument("--record-seconds", type=int, default=32)
    ap.add_argument("--skip-install", action="store_true",
                    help="test the package already on the device")
    args = ap.parse_args()

    pkg = args.package or f"com.xsytrance.{args.face}"
    cand = REPO / "releases" / args.face / "candidates" / args.version
    apks = sorted(cand.glob("*.apk"))
    if len(apks) != 1:
        print(f"ERROR expected exactly one .apk in {cand}", file=sys.stderr)
        return 2
    apk = apks[0]

    adb = Adb(args.serial)
    if not shutil.which("adb"):
        print("ERROR adb is not on PATH", file=sys.stderr)
        return 2
    devs = adb.devices()
    if not devs:
        print("ERROR no device. On the watch: Settings → Developer options → "
              "Wireless debugging, then `adb connect <ip>:<port>`.",
              file=sys.stderr)
        return 2
    if len(devs) > 1 and not args.serial:
        print(f"ERROR {len(devs)} devices attached ({devs}); pass --serial",
              file=sys.stderr)
        return 2

    short = args.version.split("-")[-1] if "-" in args.version else args.version
    out_dir = (REPO / "docs/reports/evidence/phase-4" / args.face /
               short / "matrix")
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())

    m = Matrix()
    print(f"=== {args.face} {args.version} on {devs[0]} ===\n")
    row_device_identity(adb, m)
    apk_sha = row_upgrade_continuity(adb, m, pkg, apk, work, not args.skip_install)
    row_runtime_host(adb, m, pkg)
    row_permissions(adb, m, pkg)
    row_resource_lineage(
        m, work / "post_base.apk",
        REPO / "watchfaces" / args.face / "visual/inventories/inventory.json")

    cap = adb.run("exec-out", "screencap", "-p", binary=True, timeout=120)
    if cap.stdout:
        (out_dir / "normal.png").write_bytes(cap.stdout)
        m.add("Normal-mode capture", "PASS", "normal.png captured")
    else:
        m.add("Normal-mode capture", "BLOCKED", "screencap returned nothing")

    motion = row_motion(adb, m, out_dir,
                        REPO / "watchfaces" / args.face / "engine/face.toml",
                        args.record_seconds)
    row_heart_rate(m, out_dir, motion)
    row_aod_cycles(adb, m, out_dir, args.cycles)
    row_doze_capture(adb, m, out_dir)
    row_touch(adb, m)
    row_stability(adb, m, pkg, out_dir)

    (out_dir / "matrix.json").write_text(
        json.dumps(m.data, indent=2, sort_keys=True), encoding="utf-8")
    emit(m, out_dir.parent / "DEVICE_TEST_RESULTS.md",
         args.face, args.version, apk_sha or "UNRESOLVED", out_dir)

    shutil.rmtree(work, ignore_errors=True)
    bad = sum(v for k, v in m.counts().items() if k in ("FAIL",))
    print(f"\n{len(m.rows)} measured rows, {len(OWNER_ROWS)} owner rows "
          f"outstanding, {bad} failure(s)")
    print("READINESS.json is NOT updated by this tool — re-derive it by hand.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
