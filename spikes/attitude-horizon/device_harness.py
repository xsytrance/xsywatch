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


# ---------------------------------------------------------------------
# Machine-evidence dispositions — one authoritative vocabulary.
#
# The blocking defect this replaces: finalize checked only that an
# analysis ENTRY EXISTED, not that it had succeeded. A mandatory resting
# analysis recorded BLOCKED (too few measurable frames) could therefore
# advance to PENDING_OWNER_REVIEW as though the machine evidence were
# complete. Presence is not validity.
# ---------------------------------------------------------------------
DISPOSITIONS = ("MEASURED", "PASS", "CLEAN", "NOT_OBTAINABLE", "ISSUE",
                "BLOCKED", "PARTIAL")

# Which dispositions are machine-complete, per evidence kind. Anything
# absent, unknown, malformed or contradictory fails closed.
ACCEPTABLE_DISPOSITIONS = {
    "video": {"PASS"},
    "motion_analysis": {"MEASURED"},
    "aod_cycles": {"PASS"},
    "logs": {"CLEAN"},
    "screenshot_normal": {"PASS"},
    # the ONLY place NOT_OBTAINABLE is machine-complete: the documented
    # Watch7 doze display-pipeline limitation
    "screenshot_aod": {"PASS", "NOT_OBTAINABLE"},
}

# Capture-duration policy (judgment call 1). Actual media duration is
# measured with ffprobe, never assumed from the intended duration.
DURATION_PASS_RATIO = 0.95
DURATION_PARTIAL_RATIO = 0.80      # below this is BLOCKED
# PARTIAL and BLOCKED both prevent machine-complete finalization; the
# distinction exists for diagnosis only.

# Extraction-integrity tolerance: the GREATER of two frames or 1% of the
# count expected from the ACTUAL media duration.
EXTRACT_TOLERANCE_FRAMES = 2
EXTRACT_TOLERANCE_RATIO = 0.01

DARK_THRESHOLD = 18          # a pixel this dark inside the aperture is uncovered
APERTURE_INSET = 4           # excludes rim anti-aliasing


class Blocked(Exception):
    """A fail-closed stop. Never a warning, never a default."""


class Finding:
    """A structured verification result — never a bare boolean.

    A boolean cannot say WHY, and a finalization that cannot say why it
    refused is not auditable.
    """

    def __init__(self, ok: bool, code: str, detail: str, **extra):
        self.ok = ok
        self.code = code
        self.detail = detail
        self.extra = extra

    def as_dict(self) -> dict:
        return {"ok": self.ok, "code": self.code, "detail": self.detail,
                **self.extra}

    def __repr__(self):
        return f"Finding({self.code}, ok={self.ok}, {self.detail!r})"


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


_APERTURE_CACHE: dict = {}


def _aperture_mask():
    """Precompute the inset aperture mask ONCE, cropped to its bbox.

    The old per-frame implementation walked all 230,400 pixels in pure
    Python. Scanning every frame of a 60 s capture that way is ~1,800
    frames x 230k pixels, which is why the previous version only checked a
    midpoint frame — and a midpoint frame is exactly where clipping is
    LEAST likely, because the extremes are at the ends.

    Coverage is not traded for speed here: the optimisation is a
    precomputed mask plus a bounding-box crop plus C-level Pillow ops, and
    every frame is still scanned.
    """
    if "mask" in _APERTURE_CACHE:
        return _APERTURE_CACHE["mask"], _APERTURE_CACHE["bbox"]
    from PIL import Image, ImageDraw
    ap = gs.AP
    m = Image.new("L", (gs.SIZE, gs.SIZE), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [ap["cx"] - ap["hw"] + APERTURE_INSET,
         ap["cy"] - ap["hh"] + APERTURE_INSET,
         ap["cx"] + ap["hw"] - APERTURE_INSET,
         ap["cy"] + ap["hh"] - APERTURE_INSET],
        radius=ap["radius"], fill=255)
    bbox = m.getbbox()
    mask = m.crop(bbox)
    _APERTURE_CACHE["mask"], _APERTURE_CACHE["bbox"] = mask, bbox
    _APERTURE_CACHE["pixels"] = mask.histogram()[255]
    return mask, bbox


def mask_edge_exposure(frame_path: Path) -> dict:
    """Uncovered aperture pixels in ONE frame. C-level, deterministic."""
    from PIL import Image, ImageChops
    mask, bbox = _aperture_mask()
    with Image.open(frame_path) as im:
        crop = im.convert("L").crop(bbox)
    dark = crop.point(lambda v: 255 if v < DARK_THRESHOLD else 0)
    masked = ImageChops.multiply(dark, mask)
    uncovered = masked.histogram()[255]
    total = _APERTURE_CACHE["pixels"]
    return {"aperture_pixels": total, "uncovered_pixels": uncovered,
            "uncovered_percentage": round(uncovered / max(1, total) * 100, 4),
            "exposed": uncovered > 0}


def scan_all_frames_for_exposure(frames: list[Path],
                                 measures: list | None = None) -> dict:
    """Scan EVERY extracted frame. No sampling, no interpolation.

    Judgment call 2: full coverage is mandatory, because clipping happens
    at the travel extremes and a sampling strategy that misses the extreme
    misses the only thing worth finding.
    """
    started = time.time()
    exposed: list[dict] = []
    worst = None
    scanned = 0
    for i, f in enumerate(frames):
        if not f.exists():
            raise Blocked(f"frame listed but missing during scan: {f}")
        r = mask_edge_exposure(f)
        scanned += 1
        if r["exposed"]:
            entry = {"index": i, "path": _rel(f), "sha256": sha256(f),
                     "uncovered_pixels": r["uncovered_pixels"],
                     "uncovered_percentage": r["uncovered_percentage"]}
            if measures and i < len(measures) and measures[i]:
                entry["measured_angle_deg"] = round(measures[i][0], 4)
                entry["measured_displacement_px"] = round(measures[i][1], 3)
            exposed.append(entry)
            if worst is None or r["uncovered_pixels"] > worst["uncovered_pixels"]:
                worst = entry
    runtime = time.time() - started
    return {
        "total_extracted_frames": len(frames),
        "scanned_frames": scanned,
        "scan_coverage_percentage": round(
            scanned / max(1, len(frames)) * 100, 4),
        "sampling_used": False,
        "scan_runtime_seconds": round(runtime, 3),
        "frames_per_second_scanned": round(scanned / runtime, 1)
        if runtime > 0 else None,
        "uncovered_frame_count": len(exposed),
        "max_uncovered_pixels": worst["uncovered_pixels"] if worst else 0,
        "max_uncovered_percentage": worst["uncovered_percentage"]
        if worst else 0.0,
        "first_exposed_frame": exposed[0] if exposed else None,
        "worst_exposed_frame": worst,
        "last_exposed_frame": exposed[-1] if exposed else None,
        "exposed": bool(exposed),
        "disposition": "ISSUE" if exposed else "CLEAN",
        "waivable_by_owner": False,
    }



# ---------------------------------------------------------------------
# Evidence verification — small functions, structured findings.
#
# finalize must independently REVALIDATE what it is about to summarise. It
# must not trust the index fields already stored in SESSION.json: a stored
# hash with no matching file on disk is not evidence.
# ---------------------------------------------------------------------

def _is_within(child: Path, parent: Path) -> bool:
    """True ancestry, not string prefix.

    A sibling named `SESSION-evil` textually starts with `SESSION`, so a
    prefix test would accept it as inside the session. Resolved ancestry
    does not.
    """
    try:
        return child.resolve().is_relative_to(parent.resolve())
    except (OSError, ValueError):
        return False


def _resolve(session: Path, rel: str, roots: list[Path] | None = None) -> Path:
    """Resolve a recorded path and reject escapes by real ancestry."""
    p = Path(rel)
    if not p.is_absolute():
        p = REPO / rel
    p = p.resolve()
    allowed = roots or [session, REPO / "spikes/attitude-horizon"]
    if not any(_is_within(p, r) for r in allowed):
        raise Blocked(f"path escapes the permitted evidence roots: {rel}")
    return p


def verify_disposition(kind: str, value, where: str) -> Finding:
    allowed = ACCEPTABLE_DISPOSITIONS.get(kind, set())
    if value is None:
        return Finding(False, "disposition-missing",
                       f"{where}: no disposition recorded")
    if value not in DISPOSITIONS:
        return Finding(False, "disposition-unknown",
                       f"{where}: unknown disposition {value!r}",
                       value=value)
    if value not in allowed:
        return Finding(False, "disposition-unacceptable",
                       f"{where}: disposition {value} is not machine-complete "
                       f"(acceptable: {sorted(allowed)})", value=value)
    return Finding(True, "disposition-ok", f"{where}: {value}", value=value)


def verify_raw_capture(session: Path, cid: str, rec: dict) -> list[Finding]:
    out: list[Finding] = []
    if rec.get("capture_id") != cid:
        out.append(Finding(False, "capture-id-mismatch",
                           f"{cid}: record claims capture_id "
                           f"{rec.get('capture_id')!r}"))
    files = rec.get("files") or []
    if not files:
        out.append(Finding(False, "raw-missing",
                           f"{cid}: no raw file recorded"))
        return out
    seen = set()
    for f in files:
        rel = f.get("path")
        if rel in seen:
            out.append(Finding(False, "raw-duplicate",
                               f"{cid}: duplicate raw record {rel}"))
            continue
        seen.add(rel)
        try:
            p = _resolve(session, rel)
        except Blocked as e:
            out.append(Finding(False, "raw-path-escape", str(e)))
            continue
        if not p.exists():
            out.append(Finding(False, "raw-file-missing",
                               f"{cid}: recorded raw file does not exist: "
                               f"{rel}. A stored SHA without a file is not "
                               f"evidence."))
            continue
        got = sha256(p)
        if got != f.get("sha256"):
            out.append(Finding(False, "raw-hash-drift",
                               f"{cid}: raw hash drift for {rel}",
                               recorded=f.get("sha256"), actual=got))
        if f.get("bytes") is not None and p.stat().st_size != f["bytes"]:
            out.append(Finding(False, "raw-size-drift",
                               f"{cid}: raw byte count drift for {rel}"))
    if not out:
        out.append(Finding(True, "raw-ok", f"{cid}: raw evidence verified"))
    return out


def _finite_positive(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and v == v and abs(v) != float("inf") and v > 0)


def verify_frame_manifest(session: Path, cid: str, s: dict,
                          raw_sha: str) -> tuple[dict | None, list[Finding]]:
    """Recompute every derived duration/extraction value from primitives.

    A stored disposition is a claim. The success fixture that prompted this
    recorded 40 frames of 1.33 s media while asserting a 30 s intended
    recording at ratio 1.0 — three fields that cannot all be true — and it
    passed, because verification read the stored disposition instead of
    deriving it.
    """
    out: list[Finding] = []
    idx = (s.get("frame_manifests") or {}).get(cid)
    if not idx:
        return None, [Finding(False, "manifest-index-missing",
                              f"{cid}: no frame-manifest index")]
    try:
        mp = _resolve(session, idx["manifest_path"])
    except Blocked as e:
        return None, [Finding(False, "manifest-path-escape", str(e))]
    if not mp.exists():
        return None, [Finding(False, "manifest-file-missing",
                              f"{cid}: frame manifest file does not exist")]
    if sha256(mp) != idx.get("manifest_sha256"):
        return None, [Finding(False, "manifest-hash-drift",
                              f"{cid}: frame manifest hash drift")]
    try:
        man = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [Finding(False, "manifest-malformed",
                              f"{cid}: manifest is not valid JSON ({e})")]

    if man.get("capture_id") != cid:
        out.append(Finding(False, "manifest-capture-mismatch",
                           f"{cid}: manifest names {man.get('capture_id')!r}"))
    if man.get("source_video_sha256") != raw_sha:
        out.append(Finding(False, "manifest-source-mismatch",
                           f"{cid}: manifest is not bound to the verified raw "
                           f"video"))

    for k in ("ffprobe_version", "ffprobe_command", "ffmpeg_version",
              "ffmpeg_command"):
        if not man.get(k):
            out.append(Finding(False, "manifest-field-missing",
                               f"{cid}: manifest missing {k}"))

    rc = man.get("ffmpeg_returncode")
    if rc != 0:
        out.append(Finding(False, "ffmpeg-returncode",
                           f"{cid}: ffmpeg return code {rc!r} is not 0",
                           returncode=rc))

    actual = man.get("actual_media_duration_s")
    intended = man.get("intended_duration_s")
    fps = man.get("extraction_fps")
    for label, val in (("actual_media_duration_s", actual),
                       ("intended_duration_s", intended),
                       ("extraction_fps", fps)):
        if not _finite_positive(val):
            out.append(Finding(False, "manifest-primitive-invalid",
                               f"{cid}: {label} is missing, non-numeric, "
                               f"NaN, infinite, zero or negative "
                               f"({val!r})"))
    frames = man.get("frames") or []
    if not frames:
        out.append(Finding(False, "manifest-zero-frames",
                           f"{cid}: manifest lists no frames"))
    if man.get("actual_frame_count") != len(frames):
        out.append(Finding(False, "manifest-count-mismatch",
                           f"{cid}: actual_frame_count "
                           f"{man.get('actual_frame_count')} != "
                           f"{len(frames)} listed"))

    if all(_finite_positive(v) for v in (actual, intended, fps)):
        exp = int(round(actual * fps))
        tol = extraction_tolerance(exp)
        delta = abs(len(frames) - exp)
        if man.get("expected_frame_count_from_media") != exp:
            out.append(Finding(False, "derived-expected-count",
                               f"{cid}: expected_frame_count_from_media "
                               f"{man.get('expected_frame_count_from_media')} "
                               f"!= recomputed {exp}"))
        if man.get("extraction_tolerance_frames") != tol:
            out.append(Finding(False, "derived-tolerance",
                               f"{cid}: extraction_tolerance_frames "
                               f"{man.get('extraction_tolerance_frames')} != "
                               f"recomputed {tol}"))
        if man.get("extraction_frame_delta") != delta:
            out.append(Finding(False, "derived-delta",
                               f"{cid}: extraction_frame_delta "
                               f"{man.get('extraction_frame_delta')} != "
                               f"recomputed {delta}"))
        ext_disp = "PASS" if delta <= tol else "BLOCKED"
        if man.get("extraction_disposition") != ext_disp:
            out.append(Finding(False, "derived-extraction-disposition",
                               f"{cid}: extraction_disposition "
                               f"{man.get('extraction_disposition')!r} != "
                               f"recomputed {ext_disp!r}"))
        if ext_disp != "PASS":
            out.append(Finding(False, "extraction-disposition",
                               f"{cid}: extraction is {ext_disp} "
                               f"(delta {delta} > tolerance {tol})"))

        rec_disp, rec_ratio = duration_disposition(actual, intended)
        if abs((man.get("duration_ratio") or -1) - rec_ratio) > 1e-4:
            out.append(Finding(False, "derived-duration-ratio",
                               f"{cid}: duration_ratio "
                               f"{man.get('duration_ratio')} != recomputed "
                               f"{rec_ratio}"))
        if man.get("capture_duration_disposition") != rec_disp:
            out.append(Finding(False, "derived-duration-disposition",
                               f"{cid}: capture_duration_disposition "
                               f"{man.get('capture_duration_disposition')!r} "
                               f"!= recomputed {rec_disp!r}"))
        if rec_disp != "PASS":
            out.append(Finding(False, "capture-duration",
                               f"{cid}: capture duration {rec_disp} "
                               f"(ratio {rec_ratio}) — PARTIAL and BLOCKED "
                               f"both prevent machine completion",
                               disposition=rec_disp, duration_ratio=rec_ratio))

    # the session index must not disagree with the verified manifest
    for k in ("capture_duration_disposition", "duration_ratio",
              "actual_frame_count", "source_video_sha256"):
        if k in idx and idx[k] != man.get(k):
            out.append(Finding(False, "index-manifest-disagreement",
                               f"{cid}: session index {k}={idx[k]!r} "
                               f"disagrees with the verified manifest "
                               f"{man.get(k)!r}"))

    if not out:
        out.append(Finding(True, "manifest-ok", f"{cid}: manifest verified"))
    return man, out


def verify_frames(session: Path, cid: str, man: dict) -> list[Finding]:
    out: list[Finding] = []
    seen = set()
    for entry in man.get("frames", []):
        rel = entry.get("path")
        if rel in seen:
            out.append(Finding(False, "frame-duplicate",
                               f"{cid}: duplicate frame path {rel}"))
            continue
        seen.add(rel)
        try:
            fp = _resolve(session, rel)
        except Blocked as e:
            out.append(Finding(False, "frame-path-escape", str(e)))
            continue
        if not _is_within(fp, session):
            out.append(Finding(False, "frame-outside-session",
                               f"{cid}: frame outside the session directory: "
                               f"{rel}"))
            continue
        if not fp.exists():
            out.append(Finding(False, "frame-missing",
                               f"{cid}: listed frame does not exist: {rel}"))
            continue
        if sha256(fp) != entry.get("sha256"):
            out.append(Finding(False, "frame-hash-drift",
                               f"{cid}: frame hash drift: {rel}"))
    if not out:
        out.append(Finding(True, "frames-ok",
                           f"{cid}: {len(seen)} frames verified"))
    return out


ANALYSIS_CODE_POLICY = (
    "FAIL-CLOSED: an analysis is valid only while its recorded "
    "analysis_code_sha256 equals the hash of the current harness "
    "implementation. If the harness changes after capture, the session "
    "blocks until the analysis is rerun and deliberately rebound. Presence "
    "of a code hash is not a binding.")


def verify_analysis(session: Path, cid: str, s: dict, raw_sha: str,
                    man_sha: str | None) -> tuple[dict | None, list[Finding]]:
    """Return the PARSED, hash-verified analysis document plus findings.

    The verified file — not the mutable SESSION.json index — is the source
    of truth for status, mask_scan, metrics and bindings. An index could
    otherwise claim `exposed: false` while the hash-verified analysis says
    `exposed: true`, hiding clipping from the machine issues.
    """
    out: list[Finding] = []
    idx = (s.get("analysis") or {}).get(cid)
    if not idx:
        return None, [Finding(False, "analysis-index-missing",
                              f"{cid}: no analysis recorded")]
    try:
        ap = _resolve(session, idx["path"])
    except Blocked as e:
        return None, [Finding(False, "analysis-path-escape", str(e))]
    if not ap.exists():
        return None, [Finding(False, "analysis-file-missing",
                              f"{cid}: analysis file does not exist: "
                              f"{idx['path']}. A placeholder index is not "
                              f"evidence.")]
    if sha256(ap) != idx.get("sha256"):
        return None, [Finding(False, "analysis-hash-drift",
                              f"{cid}: analysis file hash drift")]
    try:
        doc = json.loads(ap.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, [Finding(False, "analysis-malformed",
                              f"{cid}: analysis is not valid JSON ({e})")]

    if doc.get("capture_id") != cid:
        out.append(Finding(False, "analysis-capture-mismatch",
                           f"{cid}: analysis names "
                           f"{doc.get('capture_id')!r}"))
    st = doc.get("status")
    if st not in ("MEASURED",):
        out.append(Finding(False, "analysis-status",
                           f"{cid}: analysis status {st!r} is not MEASURED. "
                           f"Presence of an analysis record is not success.",
                           status=st))
    if idx.get("status") is not None and idx.get("status") != st:
        out.append(Finding(False, "analysis-index-disagreement",
                           f"{cid}: session index status "
                           f"{idx.get('status')!r} disagrees with the "
                           f"verified analysis {st!r}"))
    if doc.get("smoothing_applied") is not False:
        out.append(Finding(False, "analysis-smoothing",
                           f"{cid}: smoothing_applied is not false"))

    b = doc.get("binding") or {}
    sb = s.get("binding") or {}
    checks = [
        ("raw_capture_sha256", raw_sha),
        ("frame_manifest_sha256", man_sha),
        ("variant", sb.get("variant")),
        ("built_apk_sha256", sb.get("built_apk_sha256")),
        ("installed_pullback_sha256",
         (s.get("installed_verification") or {}).get("installed_apk_sha256")),
        ("device_model", sb.get("device_model")),
        ("android_version", sb.get("android_version")),
        ("api_level", sb.get("api_level")),
    ]
    for key, expected in checks:
        if expected is None:
            continue
        if b.get(key) != expected:
            out.append(Finding(False, "analysis-binding-mismatch",
                               f"{cid}: analysis binding {key} disagrees with "
                               f"the session", key=key,
                               recorded=b.get(key), expected=expected))

    code = b.get("analysis_code_sha256")
    if not code:
        out.append(Finding(False, "analysis-code-hash-missing",
                           f"{cid}: analysis-code hash not recorded"))
    elif code != analysis_code_hash():
        out.append(Finding(False, "analysis-code-hash-mismatch",
                           f"{cid}: analysis was produced by a different "
                           f"harness build. {ANALYSIS_CODE_POLICY}",
                           recorded=code, current=analysis_code_hash()))
    if not out:
        out.append(Finding(True, "analysis-ok", f"{cid}: analysis verified",
                           status=st))
    return doc, out


def verify_machine_findings(cid: str, rec: dict,
                            analysis_doc: dict | None) -> list[Finding]:
    """Findings, not merely record presence."""
    out: list[Finding] = []
    kind = rec.get("kind")
    if kind == "cycles":
        if rec.get("cycles_executed") != 10:
            out.append(Finding(False, "aod-cycle-count",
                               f"{cid}: {rec.get('cycles_executed')} cycles "
                               f"executed, exactly 10 required"))
        if rec.get("cycles_staged") != 10:
            out.append(Finding(False, "aod-cycles-partial",
                               f"{cid}: only {rec.get('cycles_staged')}/10 "
                               f"cycles staged — PARTIAL blocks completion"))
    if kind == "logs":
        if rec.get("crash_buffer_hits") or rec.get("fatal_or_anr_hits"):
            out.append(Finding(False, "crash-anr",
                               f"{cid}: crash/ANR findings present "
                               f"({rec.get('crash_buffer_hits')} crash, "
                               f"{rec.get('fatal_or_anr_hits')} fatal/ANR)"))
    # source of truth is the hash-verified analysis DOCUMENT, never the
    # mutable session index
    scan = (analysis_doc or {}).get("mask_scan") or {}
    if scan.get("exposed"):
        out.append(Finding(False, "mask-exposure",
                           f"{cid}: aperture clipping detected in "
                           f"{scan.get('uncovered_frame_count')} frame(s); "
                           f"an ISSUE that owner preference cannot waive"))
    if not out:
        out.append(Finding(True, "findings-ok", f"{cid}: no adverse findings"))
    return out


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
            "raw_sha256": digest, "instruction": instruction,
            "disposition": "PASS"})

    if cid in SCREENSHOT_CAPTURES:
        r = adb.run("exec-out", "screencap", "-p", binary=True, timeout=180)
        data = r.stdout or b""
        if not data:
            return _record_capture(session, cid, [], {
                "kind": "screenshot", "result": "NOT_OBTAINABLE",
                "disposition": "NOT_OBTAINABLE",
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
                "disposition": "NOT_OBTAINABLE",
                "reason": "doze returned an entirely black frame — the "
                          "documented Watch7 display-pipeline limitation. "
                          "Recorded as NOT_OBTAINABLE, never as PASS."})
        # a black NORMAL screenshot is a failure, not a limitation
        disp = "PASS"
        if black:
            disp = "BLOCKED"
        return _record_capture(session, cid, [local], {
            "kind": "screenshot", "result": "CAPTURED", "lossless": True,
            "is_black": black, "disposition": disp})

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
            "cycles_staged": staged, "cycle_log": log,
            "result": "PASS" if staged == 10 else "PARTIAL",
            "disposition": "PASS" if staged == 10 else "PARTIAL"})

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
        "result": "CLEAN" if not hits and not fatal else "FINDINGS",
        "disposition": "CLEAN" if not hits and not fatal else "ISSUE"})


def ffprobe_duration(src: Path) -> dict:
    """Measure the ACTUAL media duration. Never assume the intended one.

    A device recording can be short — the panel slept, the recorder was
    interrupted — and treating the intended duration as fact would hide
    exactly that. Extraction fidelity and capture completeness are two
    different questions and are answered separately.
    """
    if not shutil.which("ffprobe"):
        raise Blocked("ffprobe is not installed; actual media duration "
                      "cannot be measured and must not be assumed")
    ver = subprocess.run(["ffprobe", "-version"], capture_output=True,
                         text=True).stdout.splitlines()[0]
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(src)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise Blocked(f"ffprobe failed ({r.returncode}): "
                      f"{(r.stderr or '')[:300]}")
    try:
        dur = float((r.stdout or "").strip())
    except ValueError:
        raise Blocked(f"ffprobe returned an unparseable duration: "
                      f"{(r.stdout or '')[:120]!r}")
    return {"ffprobe_version": ver, "ffprobe_command": " ".join(cmd),
            "actual_media_duration_s": round(dur, 4)}


def extraction_tolerance(expected_from_media: int) -> int:
    """Greater of two frames or 1% of the media-derived expectation."""
    return max(EXTRACT_TOLERANCE_FRAMES,
               int(round(expected_from_media * EXTRACT_TOLERANCE_RATIO)))


def duration_disposition(actual_s: float, intended_s: float) -> tuple[str, float]:
    ratio = (actual_s / intended_s) if intended_s else 0.0
    if ratio >= DURATION_PASS_RATIO:
        d = "PASS"
    elif ratio >= DURATION_PARTIAL_RATIO:
        d = "PARTIAL"
    else:
        d = "BLOCKED"
    return d, round(ratio, 4)


def cmd_extract_frames(session: Path, cid: str) -> dict:
    s = load(session)
    rec = s["captures"].get(cid)
    if not rec:
        raise Blocked(f"no capture {cid!r} in this session")
    if rec.get("kind") != "video":
        raise Blocked(f"{cid} is not a video capture")
    src = REPO / rec["files"][0]["path"] if not Path(
        rec["files"][0]["path"]).is_absolute() else Path(
        rec["files"][0]["path"])
    if not src.exists():
        raise Blocked(f"raw capture missing: {src}")
    got = sha256(src)
    if got != rec["files"][0]["sha256"]:
        raise Blocked(f"raw capture hash changed since capture: {cid}")
    if not shutil.which("ffmpeg"):
        raise Blocked("ffmpeg is not installed; frame extraction is the "
                      "declared deterministic method and has no fallback")

    probe = ffprobe_duration(src)
    actual_s = probe["actual_media_duration_s"]
    intended_s = float(rec.get("intended_duration_s") or 0)
    expected_from_media = int(round(actual_s * EXTRACT_FPS))

    ver = subprocess.run(["ffmpeg", "-version"], capture_output=True,
                         text=True).stdout.splitlines()[0]
    out = session / "frames" / cid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
           "-vf", f"fps={EXTRACT_FPS}", str(out / "f%05d.png")]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    # the raw recording is never deleted or overwritten
    if proc.returncode != 0:
        raise Blocked(
            f"ffmpeg exited {proc.returncode} extracting {cid}; extraction "
            f"is BLOCKED.\nstderr excerpt: {(proc.stderr or '')[:400]}")
    frames = sorted(out.glob("*.png"))
    if not frames:
        raise Blocked(f"ffmpeg produced ZERO frames for {cid}; extraction "
                      f"is BLOCKED")

    tol = extraction_tolerance(expected_from_media)
    delta = abs(len(frames) - expected_from_media)
    if delta > tol:
        raise Blocked(
            f"{cid}: extracted {len(frames)} frames but the media duration "
            f"({actual_s}s) implies {expected_from_media} +/- {tol}. A count "
            f"outside the extraction tolerance indicates an extraction or "
            f"metadata integrity problem, not merely a short capture.")

    dur_disp, dur_ratio = duration_disposition(actual_s, intended_s)
    man = {
        "capture_id": cid,
        "source_video_path": rec["files"][0]["path"],
        "source_video_sha256": got,
        "ffmpeg_version": ver,
        "ffmpeg_command": " ".join(cmd),
        "ffmpeg_returncode": proc.returncode,
        "extraction_fps": EXTRACT_FPS,
        **probe,
        "intended_duration_s": intended_s,
        "duration_ratio": dur_ratio,
        "capture_duration_disposition": dur_disp,
        "expected_frame_count_from_media": expected_from_media,
        "extraction_tolerance_frames": tol,
        "extraction_frame_delta": delta,
        "extraction_disposition": "PASS",
        "actual_frame_count": len(frames),
        "frames": [{"path": _rel(f), "sha256": sha256(f)} for f in frames],
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
        "capture_duration_disposition": dur_disp,
        "duration_ratio": dur_ratio,
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

    measured, failed, per_frame = [], 0, []
    for f in frames:
        v = horizon_line(f) if f.exists() else None
        per_frame.append(v)
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
            # EVERY frame, not the midpoint: clipping occurs at the
            # extremes, which is exactly where a midpoint check cannot look
            body["mask_scan"] = scan_all_frames_for_exposure(frames, per_frame)
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
    s["analysis"][cid] = {"path": _rel(ap), "sha256": sha256(ap),
                          "status": body["status"],
                          "mask_scan": body.get("mask_scan")}
    save(session, s)
    return out


MANDATORY_CAPTURES = ("rest_surface_60s", "rest_wrist_60s",
                      "sweep_roll_l_to_r", "sweep_roll_r_to_l",
                      "sweep_pitch", "extremes_combined", "aod_cycles",
                      "screenshot_normal", "logs_crash_anr")


def verify_binary_bytes(session: Path, s: dict) -> list[Finding]:
    """Re-hash the installed pullback, built APK and source manifest.

    Comparing stored hash STRINGS proves only that two strings match. A
    deleted or modified pullback passes that test while the bytes it
    claims to describe no longer exist.
    """
    out: list[Finding] = []
    sb = s.get("binding") or {}
    v = s.get("installed_verification") or {}

    targets = [
        ("installed-pullback", v.get("pullback_path"),
         v.get("installed_apk_sha256"), [session]),
        ("built-apk", sb.get("built_apk_path"),
         sb.get("built_apk_sha256"), None),
        ("source-manifest", "spikes/attitude-horizon/SPIKE_MANIFEST.json",
         sb.get("spike_source_manifest_sha256"), None),
    ]
    for label, rel, expected, roots in targets:
        if not rel:
            out.append(Finding(False, f"{label}-path-missing",
                               f"{label}: no path recorded"))
            continue
        if not expected:
            out.append(Finding(False, f"{label}-hash-missing",
                               f"{label}: no hash recorded"))
            continue
        try:
            fp = _resolve(session, rel, roots)
        except Blocked as e:
            out.append(Finding(False, f"{label}-path-escape", str(e)))
            continue
        if not fp.exists():
            out.append(Finding(False, f"{label}-file-missing",
                               f"{label}: recorded file does not exist: "
                               f"{rel}"))
            continue
        got = sha256(fp)
        if got != expected:
            out.append(Finding(False, f"{label}-hash-drift",
                               f"{label}: bytes on disk do not match the "
                               f"recorded hash", path=rel,
                               recorded=expected, actual=got))
    # installed must equal the ACCEPTED built artifact, not merely itself
    if (v.get("installed_apk_sha256") and sb.get("built_apk_sha256")
            and v["installed_apk_sha256"] != sb["built_apk_sha256"]):
        out.append(Finding(False, "installed-not-accepted-build",
                           "installed pullback does not equal the accepted "
                           "built APK"))
    pkg = sb.get("package_id")
    variant = sb.get("variant")
    if pkg and variant and not pkg.endswith("." + variant):
        out.append(Finding(False, "variant-package-incoherent",
                           f"package {pkg} does not correspond to variant "
                           f"{variant}"))
    if not out:
        out.append(Finding(True, "binary-bytes-ok",
                           "installed, built and source bytes revalidated"))
    return out


KIND_FOR_CAPTURE = {
    "aod_cycles": "aod_cycles",
    "logs_crash_anr": "logs",
    "screenshot_normal": "screenshot_normal",
    "screenshot_aod": "screenshot_aod",
}


def cmd_finalize(session: Path) -> dict:
    """Independently revalidate the evidence before summarising it.

    The defect this replaces: finalize checked that an analysis ENTRY
    EXISTED and nothing more, so a mandatory analysis whose own status was
    BLOCKED could still advance to PENDING_OWNER_REVIEW. Presence is not
    validity, and a stored hash with no file behind it is not evidence.
    """
    s = load(session)
    integrity: list[dict] = []      # evidence cannot be trusted
    issues: list[dict] = []         # evidence is trustworthy and adverse
    not_obtainable: dict = {}
    verified_analyses: dict = {}    # parsed, hash-verified analysis docs

    def add(findings, bucket):
        for f in findings:
            if not f.ok:
                bucket.append(f.as_dict())

    # -- bindings and installed identity ------------------------------
    v = s.get("installed_verification") or {}
    sb = s.get("binding") or {}
    if v.get("status") != "VERIFIED":
        integrity.append(Finding(False, "install-unverified",
                                 "installed-APK pullback verification is "
                                 "missing or did not pass").as_dict())
    if v.get("installed_apk_sha256") != sb.get("built_apk_sha256"):
        integrity.append(Finding(False, "apk-hash-mismatch",
                                 "built and installed APK hashes differ"
                                 ).as_dict())
    add(verify_binary_bytes(session, s), integrity)
    for k in REQUIRED_BINDINGS:
        if not (s.get("binding") or {}).get(k):
            integrity.append(Finding(False, "binding-missing",
                                     f"required binding missing: {k}"
                                     ).as_dict())

    # -- per mandatory capture ----------------------------------------
    for cid in MANDATORY_CAPTURES:
        rec = (s.get("captures") or {}).get(cid)
        if not rec:
            integrity.append(Finding(False, "capture-missing",
                                     f"required capture missing: {cid}"
                                     ).as_dict())
            continue

        disp = rec.get("disposition")
        kind = KIND_FOR_CAPTURE.get(cid, "video")
        d = verify_disposition(kind, disp, cid)
        if disp == "NOT_OBTAINABLE":
            not_obtainable[cid] = rec.get("reason", "")
        if not d.ok:
            (issues if disp in ("ISSUE", "PARTIAL") else integrity).append(
                d.as_dict())

        raw_findings = verify_raw_capture(session, cid, rec)
        add(raw_findings, integrity)
        raw_sha = ((rec.get("files") or [{}])[0]).get("sha256")

        analysis_doc = None
        if cid in VIDEO_CAPTURES:
            man, man_findings = verify_frame_manifest(session, cid, s, raw_sha)
            for f in man_findings:
                if not f.ok:
                    (issues if f.code == "capture-duration"
                     else integrity).append(f.as_dict())
            man_sha = ((s.get("frame_manifests") or {}).get(cid) or {}).get(
                "manifest_sha256")
            if man:
                add(verify_frames(session, cid, man), integrity)
            analysis_doc, a_findings = verify_analysis(
                session, cid, s, raw_sha, man_sha)
            add(a_findings, integrity)
            if analysis_doc is not None:
                verified_analyses[cid] = analysis_doc

        add(verify_machine_findings(cid, rec, analysis_doc), issues)

    # -- optional AOD screenshot --------------------------------------
    aod = (s.get("captures") or {}).get("screenshot_aod")
    if aod:
        disp = aod.get("disposition")
        if disp == "NOT_OBTAINABLE":
            reason = (aod.get("reason") or "").lower()
            # NOT_OBTAINABLE is not a general escape hatch
            if not ("doze" in reason or "display-pipeline" in reason
                    or "display pipeline" in reason):
                integrity.append(Finding(
                    False, "aod-not-obtainable-unjustified",
                    "screenshot_aod claims NOT_OBTAINABLE for a reason other "
                    "than the documented doze/display-pipeline limitation: "
                    f"{aod.get('reason')!r}").as_dict())
            else:
                not_obtainable["screenshot_aod"] = aod.get("reason", "")
        else:
            d = verify_disposition("screenshot_aod", disp, "screenshot_aod")
            if not d.ok:
                integrity.append(d.as_dict())
            # a PRESENT screenshot claiming PASS is verified like any other
            add(verify_raw_capture(session, "screenshot_aod", aod), integrity)
            if aod.get("is_black"):
                integrity.append(Finding(
                    False, "aod-black-but-pass",
                    "screenshot_aod claims PASS but is an entirely black "
                    "frame").as_dict())

    # -- owner observations, always separate --------------------------
    owner_p = session / "OWNER_OBSERVATION.json"
    pending_owner: list[str] = []
    if owner_p.exists():
        od = json.loads(owner_p.read_text(encoding="utf-8"))
        pending_owner = [q for q, a in od["observations"].items()
                         if a["answer"] == "PENDING"]
    else:
        integrity.append(Finding(False, "owner-record-missing",
                                 "session owner-observation record missing"
                                 ).as_dict())

    if integrity:
        status = "BLOCKED_INTEGRITY"
    elif issues:
        status = "MACHINE_ISSUE"
    elif pending_owner:
        status = "PENDING_OWNER_REVIEW"
    else:
        status = "COMPLETE"

    doc = {
        "schema": "xsywatch.attitude-spike-device-result/2",
        "DISPOSABLE": True,
        "variant": (s.get("binding") or {}).get("variant"),
        "binding": s.get("binding"),
        "installed_verification": v,
        "machine_measured_results": verified_analyses,
        "machine_results_source": ("parsed, hash-verified analysis FILES — "
                                   "not the mutable SESSION.json index"),
        "analysis_code_policy": ANALYSIS_CODE_POLICY,
        "blocking_integrity_problems": integrity,
        "machine_issues": issues,
        "not_obtainable": not_obtainable,
        "pending_owner_observations": pending_owner,
        "status": status,
        "status_model": {
            "BLOCKED_INTEGRITY": "evidence cannot be trusted",
            "MACHINE_ISSUE": "evidence is trustworthy and adverse",
            "PENDING_OWNER_REVIEW": "machine evidence complete, owner has "
                                    "not yet answered",
            "COMPLETE": "machine evidence complete and owner has answered",
        },
        "status_rule": ("Machine evidence and owner judgement are separate "
                        "and never substitute for one another. Owner answers "
                        "can NEVER convert a failed or adverse machine "
                        "result into a pass, and clipping is explicitly not "
                        "waivable."),
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
            print(f"{m['actual_frame_count']} frames extracted "
                  f"(media-derived expectation "
                  f"{m['expected_frame_count_from_media']}, "
                  f"actual media duration "
                  f"{m['actual_media_duration_s']}s, "
                  f"capture duration {m['capture_duration_disposition']})")
        elif args.cmd == "analyze":
            print(json.dumps(cmd_analyze(session, args.capture), indent=2,
                             sort_keys=True))
        elif args.cmd == "finalize":
            d = cmd_finalize(session)
            print(json.dumps(d, indent=2, sort_keys=True))
            return 0 if d["status"] in ("PENDING_OWNER_REVIEW",
                                        "COMPLETE") else 1
        return 0
    except Blocked as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
