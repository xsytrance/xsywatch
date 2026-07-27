#!/usr/bin/env python3
"""DISPOSABLE spike device harness — PREPARED, NOT EXECUTED.

Nothing here installs or captures until the owner is home and explicitly
starts a session. Running it without `--run` prints the plan and exits.

    python3 spikes/attitude-horizon/device_harness.py                 # plan
    python3 spikes/attitude-horizon/device_harness.py --run --serial IP:PORT \
        --variant proposed

Every result is bound to variant, repository source commit, built APK
sha256, INSTALLED APK pullback sha256, device model, Android/API version
and timestamp. A capture that cannot be bound is not evidence and is
recorded as BLOCKED.

The analysis measures the horizon directly from the panel: for each column
inside the aperture it finds the sky/ground transition, fits a line, and
reports its angle and vertical offset. That is a measurement of what the
watch actually drew, not of what the expression was supposed to do.

WFF PROVIDES NO SMOOTHING, EASING OR FILTERING for these transforms. This
harness therefore reports raw frame-to-frame behaviour and must not apply
any smoothing of its own: if the horizon steps or jitters, that is the
finding, and inventing a filter here would hide the very thing the spike
exists to discover.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

import generate_spike as gs  # noqa: E402

OUT = HERE / "device-evidence"

CAPTURES = [
    ("rest_surface_60s", "60 s resting on a rigid, stable surface",
     "screenrecord 60 s, watch untouched on a table"),
    ("rest_wrist_60s", "60 s resting on the wearer's wrist",
     "screenrecord 60 s, arm still and supported"),
    ("sweep_roll_l_to_r", "slow left-to-right roll sweep",
     "screenrecord 30 s, one slow continuous roll"),
    ("sweep_roll_r_to_l", "slow right-to-left roll sweep",
     "screenrecord 30 s, one slow continuous roll the other way"),
    ("sweep_pitch", "slow upward then downward pitch sweep",
     "screenrecord 30 s, wrist tilted up then down"),
    ("extremes_combined", "combined pitch/roll extremes",
     "screenrecord 30 s, hold each of the four corner combinations"),
    ("aod_cycles", "ten normal/AOD sleep-wake cycles",
     "scripted keyevent SLEEP/WAKEUP x10 with wakefulness telemetry"),
    ("screenshot_normal", "normal screenshot", "screencap, panel awake"),
    ("screenshot_aod", "AOD/post-cycle screenshot",
     "screencap after the cycles; may be non-obtainable in doze"),
    ("logs_crash_anr", "crash and ANR logs",
     "logcat -b crash -d plus a FATAL/ANR scan of the main buffer"),
]

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
    "Should the final concept be two-axis reactive, roll-only, "
    "reduced-motion, static, or rejected?",
]


def sh(*args, timeout=120) -> str:
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


def source_commit() -> str:
    return sh("git", "-C", str(REPO), "rev-parse", "HEAD").strip()


def apk_path(variant: str) -> Path:
    return (HERE / "app/build/outputs/apk" / variant / "debug"
            / f"app-{variant}-debug.apk")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------
# Analysis — measures the drawn horizon, applies no smoothing
# ---------------------------------------------------------------------

def horizon_line(frame_path: Path) -> tuple[float, float] | None:
    """Measure (angle_deg, vertical_offset_px) of the drawn horizon.

    Scans columns inside the aperture for the sky-to-ground luminance
    transition and least-squares fits a line. Returns None if the
    transition cannot be found in enough columns, which is itself a
    finding rather than a value to guess at.
    """
    from PIL import Image
    ap = gs.AP
    with Image.open(frame_path) as im:
        g = im.convert("L")
        px = g.load()
        x0 = int(ap["cx"] - ap["hw"] * 0.72)
        x1 = int(ap["cx"] + ap["hw"] * 0.72)
        y0 = int(ap["cy"] - ap["hh"] * 0.92)
        y1 = int(ap["cy"] + ap["hh"] * 0.92)
        pts = []
        for x in range(x0, x1, 2):
            best_y, best_d = None, 0
            for y in range(y0 + 1, y1):
                d = px[x, y - 1] - px[x, y]     # sky is lighter than ground
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
    angle = math.degrees(math.atan(slope))
    return angle, my - ap["cy"]


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
    """What 'still enough at rest' means numerically."""
    angles = [a for a, _ in series]
    offsets = [o for _, o in series]
    ma, mo = median(angles), median(offsets)
    da = [abs(a - ma) for a in angles]
    do = [abs(o - mo) for o in offsets]
    steps = [abs(angles[i] - angles[i - 1]) for i in range(1, len(angles))]
    return {
        "frames": len(series),
        "median_angle_deg": round(ma, 3),
        "p95_abs_angular_deviation_deg": round(percentile(da, 0.95), 3),
        "max_angular_excursion_deg": round(max(da) if da else 0.0, 3),
        "median_vertical_displacement_px": round(mo, 2),
        "p95_abs_vertical_deviation_px": round(percentile(do, 0.95), 2),
        "max_vertical_excursion_px": round(max(do) if do else 0.0, 2),
        "max_frame_to_frame_step_deg": round(max(steps) if steps else 0.0, 3),
        "sign_changes": sum(1 for i in range(1, len(steps))
                            if (angles[i] - angles[i - 1]) *
                            (angles[i - 1] - angles[i - 2 if i > 1 else 0])
                            < 0),
        "note": ("no smoothing applied; WFF provides none for these "
                 "transforms, so raw stepping and oscillation are reported "
                 "as measured"),
    }


def sweep_behaviour(series: list[tuple[float, float]]) -> dict:
    """Direction, monotonicity and the clamp actually observed."""
    angles = [a for a, _ in series]
    if len(angles) < 4:
        return {"status": "BLOCKED", "reason": "too few measurable frames"}
    deltas = [angles[i] - angles[i - 1] for i in range(1, len(angles))]
    pos = sum(1 for d in deltas if d > 0.05)
    neg = sum(1 for d in deltas if d < -0.05)
    total = max(1, pos + neg)
    return {
        "frames": len(series),
        "response_direction": ("increasing" if pos > neg else "decreasing"),
        "monotonic_fraction": round(max(pos, neg) / total, 3),
        "observed_min_angle_deg": round(min(angles), 3),
        "observed_max_angle_deg": round(max(angles), 3),
        "observed_clamp_deg": round(max(abs(min(angles)), abs(max(angles))), 3),
    }


def mask_edge_exposure(frame_path: Path) -> dict:
    """Any pixel inside the aperture that the field failed to cover.

    The plate is opaque everywhere except the aperture, so a very dark
    pixel inside the aperture means the horizon field did not reach — the
    exact failure the coverage margin exists to prevent.
    """
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


def plan() -> dict:
    return {
        "schema": "xsywatch.attitude-spike-device-plan/1",
        "DISPOSABLE": True,
        "status": "PREPARED — NOT EXECUTED. No installation has occurred.",
        "precondition": ("owner is home, watch reachable over wireless adb, "
                         "and the owner has explicitly started the session"),
        "source_commit": source_commit(),
        "variants": {
            v: {
                "application_id": gs.BASE_PACKAGE + gs.PROFILES[v]["suffix"],
                "display_roll_max_deg": gs.PROFILES[v]["roll_deg"],
                "display_pitch_max_px": gs.PROFILES[v]["pitch_px"],
                "apk_path": str(apk_path(v).relative_to(REPO)),
                "apk_sha256": (sha256(apk_path(v))
                               if apk_path(v).exists() else None),
            } for v in sorted(gs.PROFILES)
        },
        "binding_required_per_result": [
            "variant", "repository source commit", "built APK sha256",
            "installed APK pullback sha256", "device model",
            "Android/API version", "timestamp",
        ],
        "captures": [{"id": c[0], "what": c[1], "how": c[2]}
                     for c in CAPTURES],
        "analysis": [
            "median horizon angle", "p95 absolute angular deviation at rest",
            "maximum angular excursion at rest",
            "median vertical displacement", "p95 absolute vertical deviation",
            "maximum vertical excursion", "response direction",
            "monotonicity", "observed clamp",
            "frame-to-frame stepping or oscillation",
            "mask-edge exposure", "AOD motion or neutrality",
        ],
        "no_smoothing_rule": (
            "WFF provides no smoothing, easing or filtering for these "
            "transforms. The harness applies none either — inventing one "
            "would conceal the jitter the spike exists to measure."),
        "owner_form": str((HERE / "OWNER_COMPARISON.json").relative_to(REPO)),
    }


def run(serial: str, variant: str) -> int:
    """Only reachable with an explicit --run and a serial."""
    if variant not in gs.PROFILES:
        print(f"ERROR unknown variant {variant}", file=sys.stderr)
        return 2
    apk = apk_path(variant)
    if not apk.exists():
        print(f"ERROR {apk} not built", file=sys.stderr)
        return 2
    devices = [ln.split("\t")[0] for ln in sh("adb", "devices").splitlines()[1:]
               if "\tdevice" in ln]
    if serial not in devices:
        print(f"BLOCKED {serial} not reachable; devices={devices}",
              file=sys.stderr)
        return 1
    print("The harness is prepared but intentionally does not auto-install.\n"
          "Installation is an owner-initiated step. To proceed manually:\n"
          f"  adb -s {serial} install -r {apk.relative_to(REPO)}\n"
          "then select the face and re-run captures individually.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true",
                    help="owner-initiated device session (still does not "
                         "auto-install)")
    ap.add_argument("--serial")
    ap.add_argument("--variant", default="proposed")
    ap.add_argument("--write-plan", action="store_true")
    args = ap.parse_args()

    if args.run:
        if not args.serial:
            print("ERROR --run requires --serial", file=sys.stderr)
            return 2
        return run(args.serial, args.variant)

    p = plan()
    if args.write_plan:
        OUT.mkdir(parents=True, exist_ok=True)
        dest = OUT / "DEVICE_TEST_PLAN.json"
        dest.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        print(f"wrote {dest.relative_to(REPO)}")
    print("PREPARED, NOT EXECUTED — no installation has occurred.")
    print(f"source commit : {p['source_commit'][:12]}…")
    for v, rec in p["variants"].items():
        h = rec["apk_sha256"]
        print(f"  {v:10s} {rec['application_id']:44s} "
              f"{h[:16] + '…' if h else 'NOT BUILT'}")
    print(f"{len(CAPTURES)} captures prepared; "
          f"{len(OWNER_QUESTIONS) + len(FINAL_QUESTIONS)} owner questions "
          f"pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
