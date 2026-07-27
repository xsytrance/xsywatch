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

# Component types that move continuously and must therefore be measurable.
# `analog_hand` is deliberately absent — see required_mechanisms().
MOVING_TYPES = {"rotating_image", "hr_balance", "seconds_rotor"}

# Mean absolute luma delta over a component box, first frame vs a later
# frame, above which the mechanism is accepted as having moved.
MOTION_REF_DELTA_MIN = 1.0

# The documented heart-rate fallback, in bpm. A reading here proves the
# face got no live data.
HR_FALLBACK_BPM = 70.0
HR_FALLBACK_TOLERANCE = 0.6

# Rows that need a human. The tool refuses to score these.
# Confirmed by the Checkpoint B rc2 re-review, ruling 3: the tool must never
# decide whether the face looks premium, restrained, readable or accepted.
OWNER_ROWS = [
    # -- Group A: normal visual inspection -----------------------------
    ("A", "Hour hand movement",
     "correctly positioned for the real time and not stuck"),
    ("A", "Minute hand movement",
     "correct for the current minute and visibly advancing; a 60 s capture "
     "cannot distinguish a slow hand from a stopped one"),
    ("A", "Normal time readability",
     "the time reads instantly at actual size, not on a monitor"),
    ("A", "Date readability",
     "the date is legible and sits correctly within its aperture"),
    ("A", "Parallax on wrist tilt",
     "background/sheen shift as the wrist tilts, with no edge clipping"),
    ("A", "Edge clipping",
     "nothing cut off at the rim and no gap revealed at any tilt angle"),
    ("A", "Command Satin visual quality",
     "the engraving remains readable and well-formed at actual scale"),
    ("A", "Reserve ticks",
     "more usable than the previous revision without becoming loud"),
    ("A", "No stripe or unintended ornament",
     "nothing entered the face that is not in the approved reference"),
    ("A", "Battery gauge plausibility",
     "needle position agrees with Settings battery %"),
    # -- Group B: AOD inspection ---------------------------------------
    ("B", "AOD visual restraint",
     "ambient frame reads as restrained, no bright sheen"),
    ("B", "AOD brightness",
     "comfortable in the ambient lighting: visible without being harsh"),
    ("B", "AOD missing layers or mechanics",
     "nothing absent in ambient that should be present"),
    ("B", "AOD hands and date visibility",
     "time and date remain legible in the dimmed ambient treatment"),
    ("B", "AOD post-cycle render visually intact",
     "inspect the post-cycle capture: all mechanics, hands, date and the "
     "engraving present, nothing dropped. A captured file is not proof the "
     "render is complete"),
    ("B", "AOD clipping or visual corruption",
     "no tearing, half-drawn layers or misregistration in either mode"),
    # -- Group C: heart-rate behaviour ---------------------------------
    ("C", "Heart rate agrees with the watch's own reading",
     "compare the implied bpm against the rate the watch itself displays, "
     "SIMULTANEOUSLY; the tool can prove the value is live, not that it is "
     "correct"),
    ("C", "Heart rate tracks after exertion",
     "record ~14s after brief safe exertion; the IMPLIED rate must rise, not "
     "merely differ from the 70.0 bpm fallback. The watch's own reading "
     "rising is not evidence the face received it"),
    ("C", "Heart rate falls back off-wrist",
     "record ~14s with the watch off the wrist; implied rate must collapse "
     "to exactly 70.0 bpm"),
    ("C", "No prompt or unexpected permission behaviour",
     "no consent dialog at install or activation, and nothing sensitive "
     "attributed to the package in Settings"),
    # -- Group D: final disposition ------------------------------------
    ("D", "Final owner disposition",
     "KEEP, CHANGE or REJECT — the judgement no measurement can make"),
    ("D", "Feels premium after real use",
     "after wearing it, not after looking at a render"),
    ("D", "Nothing distracting",
     "no element pulls the eye when it should not"),
    ("D", "No text or gauge too difficult to read",
     "every readable element is actually readable in real conditions"),
    ("D", "Reserve ticks are an improvement",
     "compared against the previous revision"),
    ("D", "Motion is satisfying rather than excessive",
     "the mechanics read as craft, not as busywork"),
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
        m.add("Runtime host — face is the active watch face", "PASS",
              f"WFF runtime reports resource-only package {pkg}")
    else:
        # ruling 3D: selection is an owner ACTION, but active-host state is
        # machine-measurable. Not knowing is a blocker, not a judgement.
        m.add("Runtime host — face is the active watch face", "BLOCKED",
              f"{pkg} is installed but NOT SELECTED — the active WFF runtime "
              f"does not name it. Select AURELIUS in the picker and re-run; "
              f"every on-panel row below is meaningless until then")


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


def ensure_awake(adb: Adb, tries: int = 6) -> str:
    """A capture of a sleeping panel is not a capture of the face.

    The Watch7 screen times out in seconds, which silently turned the
    first live run's normal-mode capture into a black frame and made
    `screenrecord` write a zero-byte file.
    """
    st = _wakefulness(adb)
    for _ in range(tries):
        if st == "Awake":
            return st
        adb.sh("input keyevent KEYCODE_WAKEUP")
        time.sleep(1.5)
        st = _wakefulness(adb)
    return st


def get_screen_timeout(adb: Adb) -> str:
    return adb.sh("settings get system screen_off_timeout").strip()


def set_screen_timeout(adb: Adb, ms: str) -> None:
    if ms and ms.lower() not in ("null", "none", ""):
        adb.sh(f"settings put system screen_off_timeout {ms}")


def is_black(p: Path) -> bool | None:
    """True if the frame is entirely black; None if it cannot be read."""
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.convert("L").getextrema() == (0, 0)
    except Exception:  # noqa: BLE001 - Pillow optional, unreadable file
        return None


def capture_png(adb: Adb, dest: Path) -> tuple[bool, str]:
    """Capture and PROVE it is not a black frame.

    The AOD doze row already treated a black frame as evidence of nothing.
    The normal-mode row did not, and passed on file existence alone — the
    same false-pass class the re-review flagged for AOD.
    """
    cap = adb.run("exec-out", "screencap", "-p", binary=True, timeout=120)
    if not cap.stdout:
        return False, "screencap returned nothing"
    dest.write_bytes(cap.stdout)
    black = is_black(dest)
    if black is True:
        return False, (f"{dest.name} is an entirely black frame — the panel "
                       f"was asleep or the capture pipeline returned nothing "
                       f"drawable; this is not evidence of the face")
    if black is None:
        return False, f"{dest.name} written but could not be read back"
    return True, f"{dest.name} captured, non-black"


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
    ensure_awake(adb)
    ok_after, after_detail = capture_png(adb, after)
    m.data["aod_cycles"] = {"count": cycles, "staged": staged,
                            "post_cycle_capture": ok_after}
    # ruling 3C: transition mechanics and visual integrity are different
    # claims. Wakefulness telemetry proves the former; the existence of a
    # PNG proves nothing at all about the latter.
    if staged == cycles:
        m.add(f"AOD — {staged}/{cycles} sleep/wake transitions", "PASS",
              f"every transition confirmed via mWakefulness telemetry")
    else:
        m.add(f"AOD — {staged}/{cycles} sleep/wake transitions", "FAIL",
              f"only {staged} of {cycles} transitions staged; see "
              f"{(out_dir / 'aod_cycles.log').name}")
    if ok_after:
        m.add("AOD — post-cycle screenshot captured", "PASS",
              f"{after_detail}; visual integrity is an OWNER row and is not "
              f"claimed here")
    else:
        m.add("AOD — post-cycle screenshot captured", "BLOCKED", after_detail)


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


def _box_series(frames: list[Path], box: tuple[int, int, int, int]) -> list:
    from PIL import Image
    x, y, w, h = box
    out = []
    for f in frames:
        with Image.open(f) as im:
            # tobytes() on an "L" image yields the same pixel sequence as
            # getdata(), without the deprecation, and iterates as ints
            out.append(im.convert("L").crop((x, y, x + w, y + h)).tobytes())
    return out


def _mean_abs(a: list, b: list) -> float:
    return sum(abs(p - q) for p, q in zip(a, b)) / max(1, len(a))


# Sample offsets for displacement-vs-first-frame. Deliberately NOT round
# fractions: an oscillator whose period divides the capture evenly returns
# to phase at 1/4, 1/2 and 3/4, and would measure as perfectly static at
# every one of them. A unit test caught exactly that.
REF_OFFSETS = (0.17, 0.31, 0.43, 0.58, 0.71, 0.89)

# A mechanism counts as moving if EITHER signal fires: displacement catches
# the slow tourbillon cage, interframe activity catches the fast oscillating
# balance wheel. Neither alone covers both.
MOTION_INTERFRAME_MIN = 0.5


def component_motion(series: list) -> dict:
    """Interframe activity plus displacement against the first frame.

    Interframe delta alone is a poor test for a slow mechanism: the
    tourbillon cage turns 6°/s, which is a fraction of a pixel between
    consecutive frames. Displacement alone is a poor test for an
    oscillator, which keeps returning to where it started. Both are
    measured and either is sufficient.
    """
    n = len(series)
    inter = [_mean_abs(series[i - 1], series[i]) for i in range(1, n)]
    refs = [_mean_abs(series[0], series[int(n * f)])
            for f in REF_OFFSETS if 0 < int(n * f) < n]
    return {
        "mean_interframe_delta": round(sum(inter) / max(1, len(inter)), 3),
        "max_reference_delta": round(max(refs) if refs else 0.0, 3),
        "near_static_pairs": sum(1 for d in inter if d < 0.1),
        "pairs": len(inter),
        "frames": n,
    }


def mechanism_moved(st: dict) -> bool:
    """Did this mechanism actually move during the capture?"""
    return (st["max_reference_delta"] >= MOTION_REF_DELTA_MIN
            or st["mean_interframe_delta"] >= MOTION_INTERFRAME_MIN)


def overall_motion_verdict(required: list[str], passed: list[str],
                           failed: list[str], frames: int,
                           seconds: int) -> tuple[str, str]:
    """Ruling 3A — the mechanical row passes only if EVERY mechanism moved.

    One moving gear is not evidence that the movement is running.
    """
    if not required:
        return "BLOCKED", ("the face contract declares no continuously "
                           "moving mechanism to measure")
    if failed:
        return "FAIL", (f"{len(passed)}/{len(required)} required mechanisms "
                        f"moved; NOT moving: {', '.join(sorted(failed))}")
    return "PASS", (f"all {len(required)} required mechanisms moved "
                    f"({', '.join(sorted(passed))}) across {frames} frames "
                    f"of a {seconds}s capture")


def rows_motion(adb: Adb, m: Matrix, out_dir: Path, face_toml: Path,
                seconds: int) -> Path | None:
    """Per-component measured motion — ruling 3A.

    The overall mechanical row passes only when EVERY required continuously
    moving mechanism passes. It must not pass because one gear moved.
    """
    comps = parse_components(face_toml)
    required = required_mechanisms(comps)

    def block(reason: str) -> None:
        for c in required:
            m.add(f"Motion — {c['name']} ({c['type']})", "BLOCKED", reason)
        m.add("Mechanical motion (all required mechanisms)", "BLOCKED", reason)

    # The panel must stay lit for the whole capture. The Watch7 screen
    # times out in seconds, which produced a zero-byte recording on the
    # first live run. Raise the timeout for the duration and put it back.
    prev_timeout = get_screen_timeout(adb)
    set_screen_timeout(adb, str((seconds + 120) * 1000))
    state = ensure_awake(adb)
    m.data["capture_wakefulness"] = state
    m.data["screen_off_timeout_restored_to"] = prev_timeout
    try:
        if state != "Awake":
            block(f"the panel would not stay awake (mWakefulness={state}); a "
                  f"recording of a sleeping screen is not motion evidence")
            return None
        remote = "/sdcard/motion.mp4"
        adb.sh(f"screenrecord --time-limit {seconds} --size 480x480 {remote}",
               timeout=seconds + 180)
        local = out_dir / "motion.mp4"
        adb.run("pull", remote, str(local), timeout=600)
        adb.sh(f"rm -f {remote}")
    finally:
        set_screen_timeout(adb, prev_timeout)

    if not local.exists():
        block("screenrecord produced no file")
        return None
    if local.stat().st_size == 0:
        block("screenrecord produced a ZERO-BYTE file — the display was "
              "asleep or the recorder never started")
        return None
    if not shutil.which("ffmpeg"):
        block(f"recording captured ({local.name}) but ffmpeg is not "
              f"installed, so per-component deltas cannot be computed")
        return local
    try:
        import PIL  # noqa: F401
    except ImportError:
        block("Pillow not installed")
        return local

    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(local),
                    "-vf", "fps=30", str(frames_dir / "f%04d.png")],
                   capture_output=True, timeout=900)
    fs = sorted(frames_dir.glob("*.png"))
    if len(fs) < 30:
        block(f"only {len(fs)} frames extracted from {local.name}")
        return local

    stats: dict[str, dict] = {}
    passed: list[str] = []
    failed: list[str] = []
    for c in required:
        st = component_motion(_box_series(fs, c["box"]))
        st["type"] = c["type"]
        if c.get("speed") is not None:
            st["declared_speed_deg_s"] = c["speed"]
        stats[c["name"]] = st
        ok_move = mechanism_moved(st)
        label = f"Motion — {c['name']} ({c['type']})"
        detail = (f"interframe Δ {st['mean_interframe_delta']} "
                  f"(min {MOTION_INTERFRAME_MIN}), displacement vs frame 0 "
                  f"Δ {st['max_reference_delta']} "
                  f"(min {MOTION_REF_DELTA_MIN}), "
                  f"{st['near_static_pairs']}/{st['pairs']} static pairs "
                  f"over {st['frames']} frames")
        if ok_move:
            passed.append(c["name"])
            m.add(label, "PASS", detail)
        else:
            failed.append(c["name"])
            m.add(label, "FAIL",
                  detail + " — this mechanism did not move during the capture")

    m.data["motion"] = stats
    m.data["motion_required"] = [c["name"] for c in required]
    result, detail = overall_motion_verdict(
        [c["name"] for c in required], passed, failed, len(fs), seconds)
    m.add("Mechanical motion (all required mechanisms)", result, detail)

    # Analog hands are deliberately NOT scored. They are Group A owner
    # rows (see OWNER_ROWS) rather than PENDING entries in the measured
    # table, so every owner judgement lives in exactly one place.
    m.data["analog_hands_not_scored"] = [
        c["name"] for c in comps if c.get("type") == "analog_hand"]
    return local


def parse_components(face_toml: Path) -> list[dict]:
    """Read the component contract: type, name, box, speed, direction.

    Read from `face.toml` rather than hard-coded so this works for any
    engine-migrated face, not just aurelius.
    """
    if not face_toml.exists():
        return []
    comps: list[dict] = []
    cur: dict | None = None
    for line in face_toml.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("[[components]]"):
            cur = {}
            comps.append(cur)
            continue
        if s.startswith("[[") or s.startswith("[") and not s.startswith("[["):
            if not s.startswith("[[components]]"):
                cur = None
        if cur is None or not s or s.startswith("#"):
            continue
        mm = re.match(r'(\w+)\s*=\s*"([^"]*)"', s)
        if mm:
            cur[mm.group(1)] = mm.group(2)
            continue
        mm = re.match(r"(\w+)\s*=\s*(-?\d+(?:\.\d+)?)\s*$", s)
        if mm:
            v = mm.group(2)
            cur[mm.group(1)] = float(v) if "." in v else int(v)
            continue
        mm = re.match(r"(\w+)\s*=\s*(true|false)\s*$", s)
        if mm:
            cur[mm.group(1)] = mm.group(2) == "true"
            continue
        bm = re.match(r"box\s*=\s*\{x\s*=\s*(\d+),\s*y\s*=\s*(\d+),\s*"
                      r"width\s*=\s*(\d+),\s*height\s*=\s*(\d+)\}", s)
        if bm:
            cur["box"] = tuple(int(g) for g in bm.groups())
    return [c for c in comps if c.get("type")]


def parse_boxes(face_toml: Path) -> dict[str, tuple[int, int, int, int]]:
    """name -> box, for components that declare one."""
    return {c["name"]: c["box"] for c in parse_components(face_toml)
            if c.get("name") and c.get("box")}


def required_mechanisms(comps: list[dict]) -> list[dict]:
    """The continuously-moving mechanisms that MUST show motion.

    Checkpoint B rc2 re-review, ruling 3A: the whole mechanical matrix must
    not pass because one gear moved. Analog hands are excluded — a 60 s
    capture cannot robustly distinguish an hour hand from a stopped one, so
    they stay owner rows rather than being scored on weak evidence.
    """
    return [c for c in comps
            if c.get("type") in MOVING_TYPES and c.get("box")]


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


def hr_verdict(freq_hz: float) -> tuple[str, str]:
    """Ruling 3E — what the measurement alone can and cannot establish.

    "Distinct from the documented fallback" is measurable and may pass
    automatically. Whether the value is CORRECT, rises with exertion, or
    collapses off-wrist are owner observations and are never decided here.
    """
    bpm = freq_hz * 60.0
    if abs(bpm - HR_FALLBACK_BPM) < HR_FALLBACK_TOLERANCE:
        return "BLOCKED", (
            f"{freq_hz:.4f} Hz = {bpm:.1f} bpm — indistinguishable from the "
            f"{HR_FALLBACK_BPM} bpm FALLBACK, so this capture does not show "
            f"live data reaching the face. Expected off-wrist; on the wrist "
            f"it is a finding. Re-capture on the wrist to settle it")
    return "PASS", (
        f"{freq_hz:.4f} Hz = {bpm:.1f} bpm — clear of the {HR_FALLBACK_BPM} "
        f"bpm fallback, so the runtime is supplying live data to a package "
        f"that declares no permission. Agreement with the watch's own "
        f"reading is an OWNER row")


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
    result, detail = hr_verdict(f)
    m.data["heart_rate"] = {"hz": f, "implied_bpm": round(f * 60.0, 1),
                            "fallback_bpm": HR_FALLBACK_BPM}
    m.add("Heart rate — live data distinct from the fallback", result, detail)


# --------------------------------------------------------------------------

def _rel(p: Path) -> str:
    """Repo-relative when possible, absolute otherwise — never raise."""
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


OWNER_FILE = "OWNER_OBSERVATIONS.json"
VALID_OWNER_RESULTS = ("PASS", "ISSUE", "NOT TESTED")


def load_owner_observations(out_parent: Path, apk_sha: str) -> dict:
    """Owner answers, kept OUT of the generated document.

    The matrix regenerates DEVICE_TEST_RESULTS.md on every run. Hand-editing
    owner verdicts into that file would destroy them the next time the
    harness ran, so they live in their own record and are merged in here.

    Fail-closed, as everywhere else: a row absent from the file stays
    PENDING, an unrecognised result is rejected rather than coerced, and an
    observation bound to a different APK is ignored — an observation of
    another build is not evidence for this one.
    """
    p = out_parent / OWNER_FILE
    if not p.exists():
        return {}
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARNING {OWNER_FILE} is unreadable ({e}); every owner row "
              f"stays PENDING")
        return {}
    if rec.get("apk_sha256") and apk_sha and rec["apk_sha256"] != apk_sha:
        print(f"WARNING {OWNER_FILE} is bound to APK "
              f"{str(rec['apk_sha256'])[:12]}…, not {apk_sha[:12]}… — "
              f"ignoring it; an observation of another build is not "
              f"evidence for this one")
        return {}
    out = {}
    for name, entry in (rec.get("observations") or {}).items():
        result = str(entry.get("result", "")).upper()
        if result not in VALID_OWNER_RESULTS:
            print(f"WARNING {OWNER_FILE}: {name!r} has result "
                  f"{entry.get('result')!r}, not one of "
                  f"{VALID_OWNER_RESULTS}; leaving it PENDING")
            continue
        out[name] = {"result": result,
                     "note": str(entry.get("note") or ""),
                     "date": str(entry.get("date") or "")}
    return out


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
    owner = load_owner_observations(dest.parent, apk_sha)
    answered = sum(1 for _, c, _ in OWNER_ROWS if c in owner)
    issues = [c for _, c, _ in OWNER_ROWS
              if owner.get(c, {}).get("result") == "ISSUE"]
    untested = [c for _, c, _ in OWNER_ROWS
                if owner.get(c, {}).get("result") == "NOT TESTED"]
    lines += [
        "",
        "## Owner rows — NOT scored by this tool",
        "",
        "These need a human looking at a physical watch. Results come from",
        f"`{OWNER_FILE}` and are recorded verbatim; a row with no recorded",
        "observation stays `PENDING — owner`. Nothing here is inferred from",
        "a measurement, and `NOT TESTED` is a final result, not a stand-in",
        "for PASS.",
        "",
        f"**{answered} of {len(OWNER_ROWS)} observed"
        + (f"; {len(issues)} ISSUE" if issues else "")
        + (f"; {len(untested)} NOT TESTED" if untested else "") + ".**",
        "",
        "| Group | Check | Result | Owner note | Criterion |",
        "|---|---|---|---|---|",
    ]
    for group, check, crit in OWNER_ROWS:
        o = owner.get(check)
        if o:
            res = f"**{o['result']}**"
            note = (o["note"] or "—").replace("|", "/")
        else:
            res = "**PENDING — owner**"
            note = "—"
        lines.append(f"| {group} | {check} | {res} | {note} | "
                     f"{crit.replace('|', '/')} |")
    if issues:
        lines += ["", "### Owner-reported ISSUES", ""]
        for name in issues:
            lines.append(f"- **{name}** — {owner[name]['note']}")
        lines += ["",
                  "An ISSUE row means this candidate is NOT acceptable as-is.",
                  "`device-validated` must not be closed while one stands."]
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


def rebuild_doc(out_dir: Path, face: str, version: str, apk: Path) -> int:
    """Regenerate the results document with no device attached.

    Owner observations arrive over days, not in one sitting. Regenerating
    must never mean re-deriving or retyping a machine result, so the
    measured rows are read back verbatim from matrix.json — and if an older
    matrix.json predates row persistence, from the tables already in the
    generated document. If neither is available this refuses rather than
    inventing an empty matrix.
    """
    mj = out_dir / "matrix.json"
    dest = out_dir.parent / "DEVICE_TEST_RESULTS.md"
    m = Matrix()
    data = {}
    if mj.exists():
        data = json.loads(mj.read_text(encoding="utf-8"))
        m.rows = [tuple(r) for r in data.get("rows", [])]
    if not m.rows and dest.exists():
        # older run: recover the measured rows from the document it wrote
        for line in dest.read_text(encoding="utf-8").splitlines():
            if not line.startswith("| ") or line.startswith("| Group "):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 3 and cells[1].startswith("**"):
                check, result, detail = cells
                result = result.strip("*")
                if result == "PENDING - owner" or "PENDING" in result:
                    continue
                m.rows.append((check, result, detail))
    if not m.rows:
        print("ERROR no saved measured rows in matrix.json and none "
              "recoverable from the document; re-run the matrix against the "
              "device rather than emitting an empty one", file=sys.stderr)
        return 2
    m.data = {k: v for k, v in data.items() if k != "rows"}
    apk_sha = (m.data.get("installed_apk_sha256")
               or (sha256_file(apk) if apk.exists() else "UNRESOLVED"))
    emit(m, dest, face, version, apk_sha, out_dir)
    print(f"rebuilt from {len(m.rows)} preserved measured row(s); no device "
          f"was contacted and no measured result was re-derived")
    return 0


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
    # ruling 3B: Checkpoint B requires at least sixty seconds of motion
    # evidence. The override exists for tests, not for shortening the gate.
    ap.add_argument("--record-seconds", type=int, default=60,
                    help="motion capture length; Checkpoint B requires >= 60")
    ap.add_argument("--skip-install", action="store_true",
                    help="test the package already on the device")
    ap.add_argument("--keep-frames", action="store_true",
                    help="keep the extracted PNG frames (~340 MB for a 60 s "
                         "capture). They are a derived intermediate and are "
                         "deleted by default; motion.mp4 is the evidence and "
                         "the frames re-extract from it with one ffmpeg call")
    ap.add_argument("--rebuild-doc", action="store_true",
                    help="regenerate DEVICE_TEST_RESULTS.md from the saved "
                         "measured rows plus the current "
                         "OWNER_OBSERVATIONS.json, with no device. Measured "
                         "rows are reused verbatim, never re-derived or "
                         "retyped")
    args = ap.parse_args()

    pkg = args.package or f"com.xsytrance.{args.face}"
    cand = REPO / "releases" / args.face / "candidates" / args.version
    apks = sorted(cand.glob("*.apk"))
    if len(apks) != 1:
        print(f"ERROR expected exactly one .apk in {cand}", file=sys.stderr)
        return 2
    apk = apks[0]

    short = args.version.split("-")[-1] if "-" in args.version else args.version
    out_dir = (REPO / "docs/reports/evidence/phase-4" / args.face /
               short / "matrix")

    if args.rebuild_doc:
        return rebuild_doc(out_dir, args.face, args.version, apk)

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

    ensure_awake(adb)
    ok_cap, cap_detail = capture_png(adb, out_dir / "normal.png")
    m.add("Normal-mode capture", "PASS" if ok_cap else "BLOCKED", cap_detail)

    if args.record_seconds < 60:
        m.add("Motion capture length", "BLOCKED",
              f"--record-seconds {args.record_seconds} is below the 60 s "
              f"Checkpoint B minimum; this run is not acceptance evidence")
    motion = rows_motion(adb, m, out_dir,
                         REPO / "watchfaces" / args.face / "engine/face.toml",
                         args.record_seconds)
    row_heart_rate(m, out_dir, motion)
    row_aod_cycles(adb, m, out_dir, args.cycles)
    row_doze_capture(adb, m, out_dir)
    row_touch(adb, m)
    row_stability(adb, m, pkg, out_dir)

    # Persist the MEASURED rows too, so the document can be regenerated
    # when owner observations arrive later without a device and without
    # anyone retyping a machine result.
    (out_dir / "matrix.json").write_text(
        json.dumps({"rows": [list(r) for r in m.rows], **m.data},
                   indent=2, sort_keys=True), encoding="utf-8")
    emit(m, out_dir.parent / "DEVICE_TEST_RESULTS.md",
         args.face, args.version, apk_sha or "UNRESOLVED", out_dir)

    frames_dir = out_dir / "frames"
    if frames_dir.exists() and not args.keep_frames:
        n = len(list(frames_dir.glob("*.png")))
        shutil.rmtree(frames_dir, ignore_errors=True)
        print(f"\nremoved {n} derived frame(s); re-extract with:\n"
              f"  ffmpeg -i {_rel(out_dir / 'motion.mp4')} -vf fps=30 "
              f"{_rel(frames_dir)}/f%04d.png")
    shutil.rmtree(work, ignore_errors=True)
    bad = sum(v for k, v in m.counts().items() if k in ("FAIL",))
    print(f"\n{len(m.rows)} measured rows, {len(OWNER_ROWS)} owner rows "
          f"outstanding, {bad} failure(s)")
    print("READINESS.json is NOT updated by this tool — re-derive it by hand.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
