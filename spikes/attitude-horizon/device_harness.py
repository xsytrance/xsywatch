#!/usr/bin/env python3
"""DISPOSABLE spike device harness — executable, fail-closed, never installs.

═══════════════════════════════════════════════════════════════════════════
 THIS HARNESS CANNOT INSTALL ANYTHING.
 There is no adb install path in this file, and a test proves it by
 capturing every command the harness can emit. The owner installs the
 chosen APK manually, outside the harness.
═══════════════════════════════════════════════════════════════════════════

    device_harness.py plan
    device_harness.py session-init     --serial SER --variant proposed
    device_harness.py verify-installed --session DIR
    device_harness.py capture          --session DIR --capture rest_surface_60s
    device_harness.py extract-frames   --session DIR --capture rest_surface_60s
    device_harness.py analyze          --session DIR --capture rest_surface_60s
    device_harness.py finalize         --session DIR

Fail-closed throughout. A missing binding blocks the session; no capture may
run before the installed APK is pulled back and its hash matched against the
accepted build; a result that cannot be bound to raw bytes is not evidence.

NO SMOOTHING, FILTERING OR EASING is applied anywhere. WFF provides none for
these transforms, so inventing one here would conceal the jitter the spike
exists to measure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

import generate_spike as gs  # noqa: E402

SESSIONS = HERE / "device-evidence/sessions"
EXTRACT_FPS = 30

# Commands the harness is permitted to emit. Anything resembling an install
# is absent by construction, and test_no_install_path_exists proves it.
FORBIDDEN_COMMAND_TOKENS = ("install", "install-multiple", "pm install",
                            "install-existing", "cmd package install")

VIDEO_CAPTURES = {
    "rest_surface_60s": (60, "Place the watch on a rigid, stable surface. "
                             "Do not touch it for 60 seconds."),
    "rest_wrist_60s": (60, "Wear the watch. Rest your arm, supported and "
                           "still, for 60 seconds."),
    "sweep_roll_l_to_r": (30, "Slowly roll the wrist fully LEFT to fully "
                              "RIGHT, once, over 30 seconds."),
    "sweep_roll_r_to_l": (30, "Slowly roll the wrist fully RIGHT to fully "
                              "LEFT, once, over 30 seconds."),
    "sweep_pitch": (30, "Slowly tilt the wrist UP, then DOWN, over 30 "
                        "seconds."),
    "extremes_combined": (30, "Hold each of the four pitch/roll corner "
                              "combinations for about 7 seconds."),
}
SCREENSHOT_CAPTURES = ("screenshot_normal", "screenshot_aod")
OTHER_CAPTURES = ("aod_cycles", "logs_crash_anr")
ALL_CAPTURES = (tuple(VIDEO_CAPTURES) + SCREENSHOT_CAPTURES + OTHER_CAPTURES)

REQUIRED_BINDINGS = (
    "variant", "package_id", "repo_head_at_session_creation",
    "spike_source_manifest_sha256", "built_apk_path", "built_apk_sha256",
    "device_serial", "device_manufacturer", "device_model",
    "android_version", "api_level", "session_timestamp",
)

OWNER_QUESTIONS = [
    "Does the horizon remain still enough at rest?",
    "Does roll direction feel intuitive?",
    "Does pitch direction feel intuitive?",
    "Is the motion too weak, premium, or too aggressive?",
    "Does it feel responsive or gimmicky?",
    "Does the letterbox geometry make pitch travel feel excessive?",
    "Is any mask edge or empty pixel visible?",
    "Does AOD remain neutral?",
]

FINAL_QUESTIONS = [
    "Which profile is preferred?",
    "Is DAMPED too weak?",
    "Does PROPOSED feel premium?",
    "Does ASSERTIVE feel excessive?",
    "Should pitch remain at all?",
    "Is roll direction intuitive?",
    "Is pitch direction intuitive?",
    "Should the final horizon be two-axis reactive, roll-only, "
    "reduced-motion, static, or rejected?",
]

FINAL_HORIZON_ANSWERS = ["two-axis reactive", "roll-only", "reduced-motion",
                         "static", "rejected"]


class Blocked(Exception):
    """A fail-closed stop. Never a warning, never a default."""


# ---------------------------------------------------------------------
# adb layer — injectable so every path is testable without a device
# ---------------------------------------------------------------------

class Adb:
    """Thin adb wrapper. Deliberately has no install method."""

    def __init__(self, serial: str):
        self.serial = serial
        self.log: list[list[str]] = []

    def _guard(self, args: list[str]) -> None:
        joined = " ".join(args).lower()
        for tok in FORBIDDEN_COMMAND_TOKENS:
            if re.search(rf"(^|\s){re.escape(tok)}(\s|$)", joined):
                raise Blocked(
                    f"refusing to emit an installation command: {joined!r}. "
                    f"Installation is a manual owner step, outside this "
                    f"harness.")

    def run(self, *args: str, timeout: int = 180, binary: bool = False):
        cmd = ["adb", "-s", self.serial, *args]
        self._guard(list(args))
        self.log.append(cmd)
        return subprocess.run(cmd, capture_output=True, timeout=timeout,
                              text=not binary)

    def sh(self, cmd: str, timeout: int = 180) -> str:
        r = self.run("shell", cmd, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")

    def out(self, *args: str, timeout: int = 180) -> str:
        r = self.run(*args, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")

    def devices(self) -> list[str]:
        r = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        return [ln.split("\t")[0] for ln in (r.stdout or "").splitlines()[1:]
                if "\tdevice" in ln]


def _rel(p: Path) -> str:
    """Repo-relative when possible, absolute otherwise — never raise.

    Sessions may legitimately live outside the repository (a scratch
    directory during testing), so path recording must not assume otherwise.
    """
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def repo_head() -> str:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return (r.stdout or "").strip() or "unknown"


def apk_path(variant: str) -> Path:
    return (HERE / "app/build/outputs/apk" / variant / "debug"
            / f"app-{variant}-debug.apk")


def analysis_code_hash() -> str:
    return sha256(Path(__file__))


def load(session: Path) -> dict:
    p = session / "SESSION.json"
    if not p.exists():
        raise Blocked(f"no SESSION.json in {session}")
    return json.loads(p.read_text(encoding="utf-8"))


def save(session: Path, doc: dict) -> None:
    (session / "SESSION.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_bindings(s: dict) -> None:
    missing = [k for k in REQUIRED_BINDINGS if not s.get("binding", {}).get(k)]
    if missing:
        raise Blocked(f"session bindings missing: {missing}. A capture "
                      f"without full binding is not evidence.")


def require_verified_install(s: dict) -> None:
    v = s.get("installed_verification") or {}
    if v.get("status") != "VERIFIED":
        raise Blocked(
            "installed-APK verification has not passed. Run "
            "`verify-installed` first: no capture may proceed until the "
            "installed bytes are pulled back and matched against the "
            "accepted build.")


# ---------------------------------------------------------------------
# Analysis primitives — raw, unsmoothed
# ---------------------------------------------------------------------

def horizon_line(frame_path: Path) -> tuple[float, float] | None:
    """(angle_deg, vertical_offset_px) of the drawn horizon, or None.

    Scans columns inside the aperture for the sky-to-ground luminance
    transition and least-squares fits a line. None means "not measurable",
    which is reported as such rather than guessed.
    """
    from PIL import Image
    ap = gs.AP
    with Image.open(frame_path) as im:
        px = im.convert("L").load()
        x0 = int(ap["cx"] - ap["hw"] * 0.72)
        x1 = int(ap["cx"] + ap["hw"] * 0.72)
        y0 = int(ap["cy"] - ap["hh"] * 0.92)
        y1 = int(ap["cy"] + ap["hh"] * 0.92)
        pts = []
        for x in range(x0, x1, 2):
            best_y, best_d = None, 0
            for y in range(y0 + 1, y1):
                d = px[x, y - 1] - px[x, y]      # sky lighter than ground
                if d > best_d:
                    best_d, best_y = d, y
            if best_y is not None and best_d > 12:
                pts.append((x, best_y))
    if len(pts) < 12:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    slope = num / den if den else 0.0
    return math.degrees(math.atan(slope)), my - ap["cy"]


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    k = (len(s) - 1) * q
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def median(xs: list[float]) -> float:
    return percentile(xs, 0.5)


def rest_stability(series: list[tuple[float, float]]) -> dict:
    angles = [a for a, _ in series]
    offsets = [o for _, o in series]
    ma, mo = median(angles), median(offsets)
    da = [abs(a - ma) for a in angles]
    do = [abs(o - mo) for o in offsets]
    steps = [angles[i] - angles[i - 1] for i in range(1, len(angles))]
    sign_changes = sum(1 for i in range(1, len(steps))
                       if steps[i] * steps[i - 1] < 0)
    return {
        "measurable_frames": len(series),
        "median_angle_deg": round(ma, 4),
        "p95_abs_angular_deviation_deg": round(percentile(da, 0.95), 4),
        "max_angular_excursion_deg": round(max(da) if da else 0.0, 4),
        "median_vertical_displacement_px": round(mo, 3),
        "p95_abs_vertical_deviation_px": round(percentile(do, 0.95), 3),
        "max_vertical_excursion_px": round(max(do) if do else 0.0, 3),
        "max_frame_to_frame_angular_step_deg": round(
            max((abs(s) for s in steps), default=0.0), 4),
        "sign_changes": sign_changes,
        "oscillation_rate_per_frame": round(
            sign_changes / max(1, len(steps)), 4),
        "smoothing_applied": False,
    }


def sweep_behaviour(series: list[tuple[float, float]]) -> dict:
    angles = [a for a, _ in series]
    if len(angles) < 4:
        return {"status": "BLOCKED",
                "reason": f"only {len(angles)} measurable frames"}
    deltas = [angles[i] - angles[i - 1] for i in range(1, len(angles))]
    pos = sum(1 for d in deltas if d > 0.05)
    neg = sum(1 for d in deltas if d < -0.05)
    total = max(1, pos + neg)
    big = [abs(d) for d in deltas]
    p95 = percentile(big, 0.95)
    return {
        "measurable_frames": len(series),
        "response_direction": "increasing" if pos > neg else "decreasing",
        "monotonic_fraction": round(max(pos, neg) / total, 4),
        "observed_min_angle_deg": round(min(angles), 4),
        "observed_max_angle_deg": round(max(angles), 4),
        "observed_clamp_deg": round(max(abs(min(angles)), abs(max(angles))), 4),
        "discontinuities": sum(1 for d in big if d > max(1.0, p95 * 3)),
        "smoothing_applied": False,
    }


def aod_neutrality(series: list[tuple[float, float]]) -> dict:
    if not series:
        return {"status": "NOT_OBTAINABLE",
                "reason": "no measurable horizon in the AOD samples"}
    angles = [a for a, _ in series]
    offs = [o for _, o in series]
    return {
        "measurable_frames": len(series),
        "measured_angle_deg": round(median(angles), 4),
        "measured_displacement_px": round(median(offs), 3),
        "max_abs_angle_deg": round(max(abs(a) for a in angles), 4),
        "max_abs_displacement_px": round(max(abs(o) for o in offs), 3),
        "remains_neutral": (max(abs(a) for a in angles) < 1.0
                            and max(abs(o) for o in offs) < 2.0),
        "detected_movement": (max(angles) - min(angles) > 0.5
                              or max(offs) - min(offs) > 1.0),
        "smoothing_applied": False,
    }


def mask_edge_exposure(frame_path: Path) -> dict:
    """Any aperture pixel the horizon field failed to cover."""
    from PIL import Image, ImageDraw
    ap = gs.AP
    with Image.open(frame_path) as im:
        g = im.convert("L")
    mask = Image.new("L", g.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [ap["cx"] - ap["hw"] + 4, ap["cy"] - ap["hh"] + 4,
         ap["cx"] + ap["hw"] - 4, ap["cy"] + ap["hh"] - 4],
        radius=ap["radius"], fill=255)
    gp, mp = g.load(), mask.load()
    dark = total = 0
    for y in range(g.size[1]):
        for x in range(g.size[0]):
            if mp[x, y]:
                total += 1
                if gp[x, y] < 18:
                    dark += 1
    return {"aperture_pixels": total, "uncovered_pixels": dark,
            "uncovered_percentage": round(dark / max(1, total) * 100, 4),
            "exposed": dark > 0}


# ---------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------

def cmd_session_init(adb: Adb, variant: str, stamp: str | None = None) -> Path:
    if variant not in gs.PROFILES:
        raise Blocked(f"unknown variant {variant!r}")
    apk = apk_path(variant)
    if not apk.exists():
        raise Blocked(f"built APK missing: {apk}. Build before a session.")
    if adb.serial not in adb.devices():
        raise Blocked(f"device {adb.serial} not reachable")

    props = {}
    for key, out in (("manufacturer", "ro.product.manufacturer"),
                     ("model", "ro.product.model"),
                     ("android_version", "ro.build.version.release"),
                     ("api_level", "ro.build.version.sdk")):
        props[key] = adb.sh(f"getprop {out}").strip()
    for k in ("model", "android_version", "api_level"):
        if not props.get(k):
            raise Blocked(f"device identity incomplete: {k} unavailable")

    ts = stamp or time.strftime("%Y%m%dT%H%M%S")
    session = SESSIONS / f"{ts}-{variant}"
    for sub in ("raw", "frames", "analysis", "pullback"):
        (session / sub).mkdir(parents=True, exist_ok=True)

    doc = {
        "schema": "xsywatch.attitude-spike-session/1",
        "DISPOSABLE": True,
        "status": "INITIALISED",
        "binding": {
            "variant": variant,
            "package_id": gs.BASE_PACKAGE + gs.PROFILES[variant]["suffix"],
            "repo_head_at_session_creation": repo_head(),
            "spike_source_manifest_sha256": sha256(
                HERE / "SPIKE_MANIFEST.json"),
            "built_apk_path": _rel(apk),
            "built_apk_sha256": sha256(apk),
            "device_serial": adb.serial,
            "device_manufacturer": props["manufacturer"],
            "device_model": props["model"],
            "android_version": props["android_version"],
            "api_level": props["api_level"],
            "session_timestamp": ts,
        },
        "profile": {
            "display_roll_max_deg": gs.PROFILES[variant]["roll_deg"],
            "display_pitch_max_px": gs.PROFILES[variant]["pitch_px"],
            "wrist_roll_clamp_deg": gs.WRIST_ROLL_CLAMP,
            "wrist_pitch_clamp_deg": gs.WRIST_PITCH_CLAMP,
        },
        "installed_verification": {"status": "PENDING"},
        "captures": {},
        "frame_manifests": {},
        "analysis": {},
        "install_policy": ("MANUAL AND OWNER-INITIATED. This harness has no "
                           "install path and refuses to emit one."),
        "manual_install_command": f"adb -s {adb.serial} install -r "
                                  f"{_rel(apk)}",
    }
    require_bindings(doc)
    save(session, doc)
    _write_owner_record(session, variant)
    return session


def _write_owner_record(session: Path, variant: str) -> None:
    """Session-specific, fail-closed. Never touches another profile."""
    doc = {
        "schema": "xsywatch.attitude-spike-owner-session/1",
        "DISPOSABLE": True,
        "variant": variant,
        "package_id": gs.BASE_PACKAGE + gs.PROFILES[variant]["suffix"],
        "status": "PENDING",
        "rule": ("FAIL-CLOSED. Every answer starts PENDING and stays PENDING "
                 "until AGENOR gives it explicitly. Nothing is inferred from "
                 "a measurement, from another profile, or from silence."),
        "scope_note": ("This record covers ONLY this profile. Answers must "
                       "never be copied across profiles."),
        "observations": {q: {"answer": "PENDING", "note": ""}
                         for q in OWNER_QUESTIONS},
    }
    (session / "OWNER_OBSERVATION.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_verify_installed(adb: Adb, session: Path) -> dict:
    s = load(session)
    require_bindings(s)
    pkg = s["binding"]["package_id"]
    out = adb.sh(f"pm path {pkg}")
    paths = re.findall(r"package:(\S+)", out)
    if not paths:
        raise Blocked(f"{pkg} is not installed. Install it manually first: "
                      f"{s['manual_install_command']}")
    bases = [p for p in paths if p.endswith("base.apk")]
    if len(bases) != 1:
        raise Blocked(f"ambiguous installed package paths for {pkg}: {paths}")
    remote = bases[0]
    dest = session / "pullback" / "installed_base.apk"
    adb.run("pull", remote, str(dest), timeout=600)
    if not dest.exists():
        raise Blocked(f"could not pull {remote}")
    got = sha256(dest)
    expected = s["binding"]["built_apk_sha256"]
    rec = {
        "status": "VERIFIED" if got == expected else "MISMATCH",
        "package_path_on_device": remote,
        "pullback_path": _rel(dest),
        "installed_apk_sha256": got,
        "built_apk_sha256": expected,
    }
    s["installed_verification"] = rec
    s["status"] = "VERIFIED" if got == expected else "BLOCKED"
    save(session, s)
    if got != expected:
        raise Blocked(
            f"installed bytes do not match the accepted build.\n"
            f"  built    {expected}\n  installed {got}\n"
            f"The session is blocked: evidence from an unidentified build is "
            f"not evidence for this one.")
    return rec


def _record_capture(session: Path, cid: str, files: list[Path],
                    meta: dict) -> dict:
    s = load(session)
    rec = {
        "capture_id": cid,
        "files": [{"path": _rel(p), "sha256": sha256(p),
                   "bytes": p.stat().st_size} for p in files],
        **meta,
    }
    s["captures"][cid] = rec
    save(session, s)
    return rec


def cmd_capture(adb: Adb, session: Path, cid: str,
                countdown: int = 5) -> dict:
    if cid not in ALL_CAPTURES:
        raise Blocked(f"unknown capture {cid!r}; known: {list(ALL_CAPTURES)}")
    s = load(session)
    require_bindings(s)
    require_verified_install(s)
    raw = session / "raw"

    if cid in VIDEO_CAPTURES:
        secs, instruction = VIDEO_CAPTURES[cid]
        print(f"\n{instruction}\n")
        for i in range(countdown, 0, -1):
            print(f"  starting in {i}…")
            time.sleep(1)
        remote = f"/sdcard/{cid}.mp4"
        cmdline = f"screenrecord --time-limit {secs} --size 480x480 {remote}"
        adb.sh(cmdline, timeout=secs + 180)
        local = raw / f"{cid}.mp4"
        adb.run("pull", remote, str(local), timeout=600)
        if not local.exists() or local.stat().st_size == 0:
            raise Blocked(f"{cid}: recording is missing or zero bytes; the "
                          f"panel was asleep or the recorder never started")
        # only remove the device-side file AFTER a successful pull and hash
        digest = sha256(local)
        adb.sh(f"rm -f {remote}")
        return _record_capture(session, cid, [local], {
            "kind": "video", "device_side_filename": remote,
            "adb_command": cmdline, "intended_duration_s": secs,
            "raw_sha256": digest, "instruction": instruction})

    if cid in SCREENSHOT_CAPTURES:
        r = adb.run("exec-out", "screencap", "-p", binary=True, timeout=180)
        data = r.stdout or b""
        if not data:
            return _record_capture(session, cid, [], {
                "kind": "screenshot", "result": "NOT_OBTAINABLE",
                "reason": "screencap returned nothing"})
        local = raw / f"{cid}.png"
        local.write_bytes(data)
        black = False
        try:
            from PIL import Image
            with Image.open(local) as im:
                black = im.convert("L").getextrema() == (0, 0)
        except Exception:  # noqa: BLE001
            pass
        if black and cid == "screenshot_aod":
            return _record_capture(session, cid, [local], {
                "kind": "screenshot", "result": "NOT_OBTAINABLE",
                "reason": "doze returned an entirely black frame — the "
                          "documented Watch7 display-pipeline limitation. "
                          "Recorded as NOT_OBTAINABLE, never as PASS."})
        return _record_capture(session, cid, [local], {
            "kind": "screenshot", "result": "CAPTURED", "lossless": True})

    if cid == "aod_cycles":
        log = []
        for i in range(10):
            adb.sh("input keyevent KEYCODE_SLEEP")
            time.sleep(2)
            a = adb.sh("dumpsys power")
            m = re.search(r"mWakefulness=(\w+)", a)
            asleep = m.group(1) if m else "?"
            adb.sh("input keyevent KEYCODE_WAKEUP")
            time.sleep(2)
            b = adb.sh("dumpsys power")
            m2 = re.search(r"mWakefulness=(\w+)", b)
            log.append({"cycle": i + 1,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "sleep_state": asleep,
                        "wake_state": m2.group(1) if m2 else "?"})
        p = raw / "aod_cycles.json"
        p.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
        staged = sum(1 for e in log if e["sleep_state"] in ("Asleep", "Dozing"))
        return _record_capture(session, cid, [p], {
            "kind": "cycles", "cycles_executed": len(log),
            "cycles_staged": staged,
            "result": "PASS" if staged == 10 else "PARTIAL"})

    # logs_crash_anr
    crash = adb.out("logcat", "-b", "crash", "-d", timeout=300)
    main = adb.out("logcat", "-d", "-v", "brief", timeout=600)
    pc = raw / "logcat_crash.txt"
    pm = raw / "logcat_main.txt"
    pc.write_text(crash, encoding="utf-8")
    pm.write_text(main, encoding="utf-8")
    pkg = s["binding"]["package_id"]
    hits = [ln for ln in crash.splitlines() if pkg in ln]
    fatal = [ln for ln in main.splitlines()
             if ("FATAL EXCEPTION" in ln or "ANR in" in ln) and pkg in ln]
    return _record_capture(session, cid, [pc, pm], {
        "kind": "logs", "crash_buffer_hits": len(hits),
        "fatal_or_anr_hits": len(fatal),
        "result": "CLEAN" if not hits and not fatal else "FINDINGS"})


def cmd_extract_frames(session: Path, cid: str) -> dict:
    s = load(session)
    rec = s["captures"].get(cid)
    if not rec:
        raise Blocked(f"no capture {cid!r} in this session")
    if rec.get("kind") != "video":
        raise Blocked(f"{cid} is not a video capture")
    src = REPO / rec["files"][0]["path"]
    if not src.exists():
        raise Blocked(f"raw capture missing: {src}")
    got = sha256(src)
    if got != rec["files"][0]["sha256"]:
        raise Blocked(f"raw capture hash changed since capture: {cid}")
    if not shutil.which("ffmpeg"):
        raise Blocked("ffmpeg is not installed; frame extraction is the "
                      "declared deterministic method and has no fallback")
    ver = subprocess.run(["ffmpeg", "-version"], capture_output=True,
                         text=True).stdout.splitlines()[0]
    out = session / "frames" / cid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
           "-vf", f"fps={EXTRACT_FPS}", str(out / "f%05d.png")]
    subprocess.run(cmd, capture_output=True, timeout=1800)
    frames = sorted(out.glob("*.png"))
    expected = int(rec.get("intended_duration_s", 0)) * EXTRACT_FPS
    man = {
        "capture_id": cid,
        "source_video_path": rec["files"][0]["path"],
        "source_video_sha256": got,
        "ffmpeg_version": ver,
        "ffmpeg_command": " ".join(cmd),
        "extraction_fps": EXTRACT_FPS,
        "expected_frame_count": expected,
        "actual_frame_count": len(frames),
        "frames": [{"path": _rel(f), "sha256": sha256(f)}
                   for f in frames],
    }
    mp = session / "frames" / f"{cid}_FRAMES.json"
    mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n",
                  encoding="utf-8")
    s = load(session)
    s["frame_manifests"][cid] = {
        "manifest_path": _rel(mp),
        "manifest_sha256": sha256(mp),
        "source_video_sha256": got,
        "actual_frame_count": len(frames),
    }
    save(session, s)
    return man


def cmd_analyze(session: Path, cid: str) -> dict:
    s = load(session)
    require_bindings(s)
    require_verified_install(s)
    rec = s["captures"].get(cid)
    if not rec:
        raise Blocked(f"no capture {cid!r}")
    fm = s["frame_manifests"].get(cid)
    if rec.get("kind") == "video" and not fm:
        raise Blocked(f"no frame manifest for {cid}; run extract-frames")

    frames: list[Path] = []
    if fm:
        mp = REPO / fm["manifest_path"]
        if sha256(mp) != fm["manifest_sha256"]:
            raise Blocked(f"frame manifest for {cid} changed since extraction")
        man = json.loads(mp.read_text(encoding="utf-8"))
        if man["source_video_sha256"] != rec["files"][0]["sha256"]:
            raise Blocked(f"frame manifest for {cid} is not bound to the raw "
                          f"capture it claims")
        frames = [REPO / f["path"] for f in man["frames"]]
    elif rec.get("files"):
        frames = [REPO / f["path"] for f in rec["files"]
                  if f["path"].endswith(".png")]

    measured, failed = [], 0
    for f in frames:
        v = horizon_line(f) if f.exists() else None
        if v is None:
            failed += 1
        else:
            measured.append(v)

    body: dict
    if cid.startswith("rest_"):
        if len(measured) < 30:
            body = {"status": "BLOCKED",
                    "reason": f"only {len(measured)} measurable frames; "
                              f"too few for a stability claim"}
        else:
            body = {"status": "MEASURED", **rest_stability(measured)}
    elif cid.startswith("sweep_") or cid == "extremes_combined":
        body = {"status": "MEASURED", **sweep_behaviour(measured)}
        if frames:
            body["mask_edge_exposure"] = mask_edge_exposure(frames[len(frames) // 2])
    elif cid in ("screenshot_aod", "aod_cycles"):
        body = {"status": "MEASURED", **aod_neutrality(measured)}
    else:
        body = {"status": "MEASURED", "measurable_frames": len(measured)}

    out = {
        "capture_id": cid,
        "failed_measurement_frames": failed,
        **body,
        "binding": {
            "raw_capture_sha256": (rec["files"][0]["sha256"]
                                   if rec.get("files") else None),
            "frame_manifest_sha256": (fm or {}).get("manifest_sha256"),
            "analysis_code_sha256": analysis_code_hash(),
            "variant": s["binding"]["variant"],
            "built_apk_sha256": s["binding"]["built_apk_sha256"],
            "installed_pullback_sha256":
                s["installed_verification"]["installed_apk_sha256"],
            "device_model": s["binding"]["device_model"],
            "android_version": s["binding"]["android_version"],
            "api_level": s["binding"]["api_level"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "smoothing_applied": False,
    }
    if not out["binding"]["raw_capture_sha256"] and body.get(
            "status") == "MEASURED":
        raise Blocked(f"analysis of {cid} is not bound to a raw capture")
    ap = session / "analysis" / f"{cid}.json"
    ap.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n",
                  encoding="utf-8")
    s = load(session)
    s["analysis"][cid] = {"path": _rel(ap),
                          "sha256": sha256(ap), "status": body["status"]}
    save(session, s)
    return out


MANDATORY_CAPTURES = ("rest_surface_60s", "rest_wrist_60s",
                      "sweep_roll_l_to_r", "sweep_roll_r_to_l",
                      "sweep_pitch", "extremes_combined", "aod_cycles",
                      "screenshot_normal", "logs_crash_anr")


def cmd_finalize(session: Path) -> dict:
    s = load(session)
    problems: list[str] = []

    v = s.get("installed_verification") or {}
    if v.get("status") != "VERIFIED":
        problems.append("installed-APK pullback verification is missing or "
                        "did not pass")
    if v.get("installed_apk_sha256") != s.get("binding", {}).get(
            "built_apk_sha256"):
        problems.append("built and installed APK hashes differ")
    for k in REQUIRED_BINDINGS:
        if not s.get("binding", {}).get(k):
            problems.append(f"required binding missing: {k}")

    for cid in MANDATORY_CAPTURES:
        rec = s["captures"].get(cid)
        if not rec:
            problems.append(f"required capture missing: {cid}")
            continue
        if rec.get("kind") in ("video", "screenshot") and rec.get("files"):
            if not rec["files"][0].get("sha256"):
                problems.append(f"raw hash missing for {cid}")
        if cid in VIDEO_CAPTURES and cid not in s.get("frame_manifests", {}):
            problems.append(f"derived frames missing for {cid}")
        if cid in VIDEO_CAPTURES and cid not in s.get("analysis", {}):
            problems.append(f"analysis missing for {cid}")
    if "logs_crash_anr" not in s["captures"]:
        problems.append("crash/ANR evidence missing")

    for cid, fm in s.get("frame_manifests", {}).items():
        raw = (s["captures"].get(cid) or {}).get("files") or [{}]
        if fm.get("source_video_sha256") != raw[0].get("sha256"):
            problems.append(f"derived frames for {cid} not bound to raw data")

    owner_p = session / "OWNER_OBSERVATION.json"
    pending_owner = []
    if owner_p.exists():
        od = json.loads(owner_p.read_text(encoding="utf-8"))
        pending_owner = [q for q, a in od["observations"].items()
                         if a["answer"] == "PENDING"]
    else:
        problems.append("session owner-observation record missing")

    machine_ok = not problems
    doc = {
        "schema": "xsywatch.attitude-spike-device-result/1",
        "DISPOSABLE": True,
        "variant": s.get("binding", {}).get("variant"),
        "binding": s.get("binding"),
        "installed_verification": v,
        "machine_measured_results": {
            cid: a for cid, a in s.get("analysis", {}).items()},
        "not_obtainable": {
            cid: rec.get("reason", "")
            for cid, rec in s["captures"].items()
            if rec.get("result") == "NOT_OBTAINABLE"},
        "owner_observations_answered": [] if pending_owner else "all",
        "pending_owner_observations": pending_owner,
        "blocking_problems": problems,
        "status": ("BLOCKED" if not machine_ok
                   else ("PENDING_OWNER_REVIEW" if pending_owner
                         else "COMPLETE")),
        "status_rule": ("Machine evidence completeness and owner judgement "
                        "are separate. A session is never COMPLETE while "
                        "owner answers are PENDING, and owner answers are "
                        "never inferred from measurements."),
        "smoothing_applied": False,
    }
    p = session / "DEVICE_RESULT.json"
    p.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8")
    return doc


def cmd_plan() -> dict:
    return {
        "schema": "xsywatch.attitude-spike-device-plan/2",
        "DISPOSABLE": True,
        "status": "PREPARED — NOT EXECUTED. No installation has occurred.",
        "install_policy": "MANUAL, owner-initiated, outside this harness. "
                          "The harness has no install path.",
        "repo_head": repo_head(),
        "variants": {
            v: {"application_id": gs.BASE_PACKAGE + gs.PROFILES[v]["suffix"],
                "apk_path": _rel(apk_path(v)),
                "apk_sha256": (sha256(apk_path(v))
                               if apk_path(v).exists() else None)}
            for v in sorted(gs.PROFILES)},
        "captures": list(ALL_CAPTURES),
        "mandatory_captures": list(MANDATORY_CAPTURES),
        "required_bindings": list(REQUIRED_BINDINGS),
        "extraction": {"tool": "ffmpeg", "fps": EXTRACT_FPS},
        "no_smoothing_rule": ("WFF provides no smoothing, easing or "
                              "filtering for these transforms; the harness "
                              "applies none either."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("plan")
    p = sub.add_parser("session-init")
    p.add_argument("--serial", required=True)
    p.add_argument("--variant", required=True)
    for name in ("verify-installed", "finalize"):
        q = sub.add_parser(name)
        q.add_argument("--session", required=True)
    for name in ("capture", "extract-frames", "analyze"):
        q = sub.add_parser(name)
        q.add_argument("--session", required=True)
        q.add_argument("--capture", required=True)
    args = ap.parse_args()

    try:
        if args.cmd in (None, "plan"):
            print(json.dumps(cmd_plan(), indent=2, sort_keys=True))
            return 0
        if args.cmd == "session-init":
            s = cmd_session_init(Adb(args.serial), args.variant)
            print(f"session {_rel(s)}")
            print("NOTHING INSTALLED. Install manually, then run "
                  "verify-installed.")
            return 0
        session = Path(args.session)
        if args.cmd == "verify-installed":
            print(json.dumps(cmd_verify_installed(
                Adb(load(session)["binding"]["device_serial"]), session),
                indent=2, sort_keys=True))
        elif args.cmd == "capture":
            print(json.dumps(cmd_capture(
                Adb(load(session)["binding"]["device_serial"]), session,
                args.capture), indent=2, sort_keys=True))
        elif args.cmd == "extract-frames":
            m = cmd_extract_frames(session, args.capture)
            print(f"{m['actual_frame_count']} frames "
                  f"(expected {m['expected_frame_count']})")
        elif args.cmd == "analyze":
            print(json.dumps(cmd_analyze(session, args.capture), indent=2,
                             sort_keys=True))
        elif args.cmd == "finalize":
            d = cmd_finalize(session)
            print(json.dumps(d, indent=2, sort_keys=True))
            return 0 if d["status"] != "BLOCKED" else 1
        return 0
    except Blocked as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
