#!/usr/bin/env python3
"""Official Wear OS WO-P7 always-on-display luminance gate.

The requirement (Wear OS app quality guidelines, WO-P7 "Always on Display
- Watch Face Format", checked 2026-07-26):

    Has an Always on Display mode and illuminates no more than 15% of
    pixels. This is calculated as the average value across the watch face,
    with a fully-opaque white pixel having a value of 100% and a black
    pixel 0%. RGB colors are interpolated linearly between these two
    values. This check is repeated at approximately 10 minute intervals
    from the start to the end of a whole day, and every calculation must
    satisfy the 15% limit.

    https://developer.android.com/docs/quality-guidelines/wear-app-quality

This is NOT the house heuristic. The repository previously reported "lit
pixels above 15/255" on a single frame, which counts pixels rather than
averaging luminance and samples one instant rather than a day. The two
numbers are not comparable and the house figure is not compliance
evidence.

    python3 tools/aod_luminance.py aurelius                  # full gate
    python3 tools/aod_luminance.py aurelius --quick          # 1h steps
    python3 tools/aod_luminance.py aurelius --report DIR     # write evidence

Exit codes: 0 pass, 1 over the limit, 2 bad invocation.

Interpretation notes, stated because the wording admits more than one
reading and this gate deliberately takes the strictest:

  * "average value ... RGB interpolated linearly between black and white"
    is computed three ways — the unweighted channel mean on encoded sRGB,
    Rec.709 luma on encoded sRGB, and Rec.709 luma after linearising sRGB.
    The gate uses the LARGEST of the three. Claiming compliance on the
    most flattering reading would be exactly the sort of unearned claim
    this gate exists to prevent.
  * "across the watch face" is computed over the circular display disc,
    excluding the black canvas corners a round watch never shows.
    Excluding guaranteed-black pixels RAISES the average, so this is the
    stricter region; the full-square figure is reported alongside.
  * the AOD state pins second and millisecond to zero (device-observed
    ambient behaviour), so the time-dependent content across a day is the
    hour and minute hands and anything driven by them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import visuallib as V                                  # noqa: E402

LIMIT_PCT = 15.0
DISC_R = 240.0


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


_LIN = [_srgb_to_linear(i / 255.0) for i in range(256)]


def luminance_variants(img, region: str = "disc") -> dict:
    """Mean luminance in percent, three readings of the requirement."""
    im = img.convert("RGB")
    px = im.load()
    w, h = im.size
    cx, cy = w / 2.0, h / 2.0
    r2 = DISC_R * DISC_R
    n = 0
    s_mean = s_709 = s_lin = 0.0
    for y in range(h):
        dy = y + 0.5 - cy
        for x in range(w):
            if region == "disc":
                dx = x + 0.5 - cx
                if dx * dx + dy * dy > r2:
                    continue
            r, g, b = px[x, y]
            n += 1
            s_mean += (r + g + b) / 3.0
            s_709 += 0.2126 * r + 0.7152 * g + 0.0722 * b
            s_lin += (0.2126 * _LIN[r] + 0.7152 * _LIN[g]
                      + 0.0722 * _LIN[b]) * 255.0
    if n == 0:
        return {"channel_mean_srgb": 0.0, "rec709_srgb": 0.0,
                "rec709_linear": 0.0, "max": 0.0, "pixels": 0}
    out = {
        "channel_mean_srgb": 100.0 * s_mean / (n * 255.0),
        "rec709_srgb": 100.0 * s_709 / (n * 255.0),
        "rec709_linear": 100.0 * s_lin / (n * 255.0),
        "pixels": n,
    }
    out["max"] = max(out["channel_mean_srgb"], out["rec709_srgb"],
                     out["rec709_linear"])
    return out


def render_aod(scene, contract, *, hour: int, minute: int, day: int,
               battery: float, heart_rate: float):
    """Render the AOD state with the given time-dependent inputs."""
    base = contract.state(contract.raw["goldens"]["aod_state"])
    name = f"_wop7_{hour:02d}{minute:02d}_{day}_{int(battery)}_{int(heart_rate)}"
    raw = dict(base["raw"])
    raw.update({"hour_0_11": hour % 12, "minute": minute, "day": day,
                "battery_percent": battery, "heart_rate": heart_rate,
                "ambient": True})
    contract.raw["states"][name] = raw
    try:
        return V.render_state(scene, contract, name)
    finally:
        contract.raw["states"].pop(name, None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--interval", type=int, default=10,
                    help="sampling interval in minutes (default 10, as WO-P7)")
    ap.add_argument("--quick", action="store_true",
                    help="60-minute interval and no sensitivity sweep")
    ap.add_argument("--report", help="directory for the evidence JSON")
    ap.add_argument("--limit", type=float, default=LIMIT_PCT)
    args = ap.parse_args()

    interval = 60 if args.quick else args.interval
    if 1440 % interval:
        print(f"ERROR interval {interval} does not divide a day", file=sys.stderr)
        return 2

    scene = V.Scene.load(args.face)
    contract = V.VisualContract.load(args.face)
    base = contract.state(contract.raw["goldens"]["aod_state"])["raw"]
    day0 = int(base["day"])
    batt0 = float(base["battery_percent"])
    hr0 = float(base["heart_rate"])

    samples = []
    worst = None
    minutes = list(range(0, 1440, interval))
    for m in minutes:
        hh, mm = divmod(m, 60)
        img = render_aod(scene, contract, hour=hh, minute=mm, day=day0,
                         battery=batt0, heart_rate=hr0)
        disc = luminance_variants(img, "disc")
        full = luminance_variants(img, "full")
        rec = {"time": f"{hh:02d}:{mm:02d}", "minute_of_day": m,
               "disc": disc, "full_square": full,
               "gate_value_pct": disc["max"],
               "pass": disc["max"] <= args.limit}
        samples.append(rec)
        if worst is None or rec["gate_value_pct"] > worst["gate_value_pct"]:
            worst = rec
        print(f"  {rec['time']}  {rec['gate_value_pct']:6.3f}%  "
              f"{'ok' if rec['pass'] else 'OVER'}")

    # Sensitivity: inputs that change AOD pixels but are not time-of-day.
    sensitivity = []
    if not args.quick:
        wt = worst["minute_of_day"]
        hh, mm = divmod(wt, 60)
        for label, kwargs in (
            *[(f"day={d}", {"day": d}) for d in (1, 8, 11, 22, 28, 31)],
            *[(f"battery={b}", {"battery": float(b)})
              for b in (0, 15, 50, 80, 95, 100)],
            ("heart_rate=0 (fallback)", {"heart_rate": 0.0}),
            ("heart_rate=200", {"heart_rate": 200.0}),
        ):
            kw = {"hour": hh, "minute": mm, "day": day0, "battery": batt0,
                  "heart_rate": hr0}
            kw.update(kwargs)
            img = render_aod(scene, contract, **kw)
            v = luminance_variants(img, "disc")
            sensitivity.append({"at_time": worst["time"], "vary": label,
                                "gate_value_pct": v["max"],
                                "pass": v["max"] <= args.limit})

    all_vals = [s["gate_value_pct"] for s in samples] + \
               [s["gate_value_pct"] for s in sensitivity]
    maximum = max(all_vals)
    ok = maximum <= args.limit

    result = {
        "requirement": "WO-P7 (Wear OS app quality guidelines)",
        "source": "https://developer.android.com/docs/quality-guidelines/wear-app-quality",
        "checked": "2026-07-26",
        "face": args.face,
        "visual_version": (contract.raw["goldens"].get("proposed_version")
                           or contract.raw["goldens"]["approved_version"]),
        "limit_pct": args.limit,
        "metric": ("mean luminance across the watch-face disc; white=100%, "
                   "black=0%; strictest of channel-mean-sRGB, Rec.709-sRGB "
                   "and Rec.709-linear"),
        "region": "circular display disc (r=240), corners excluded",
        "sampling": {"interval_minutes": interval,
                     "samples": len(samples),
                     "covers": "00:00 to 23:59 inclusive of a whole day"},
        "fixed_inputs": {"day": day0, "battery_percent": batt0,
                         "heart_rate": hr0,
                         "note": ("second and millisecond are pinned to 0 in "
                                  "ambient, matching observed Watch7 "
                                  "behaviour; the time-dependent AOD content "
                                  "across a day is therefore the hour and "
                                  "minute hands and anything they drive")},
        "samples": samples,
        "sensitivity": sensitivity,
        "max_pct": maximum,
        "worst_time_sample": worst,
        "pass": ok,
        "reproduce": f"python3 tools/aod_luminance.py {args.face}",
    }

    if args.report:
        d = Path(args.report)
        d.mkdir(parents=True, exist_ok=True)
        (d / "wo_p7_luminance.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"report: {d / 'wo_p7_luminance.json'}")

    print()
    print(f"samples          : {len(samples)} at {interval}-minute intervals")
    if sensitivity:
        print(f"sensitivity runs : {len(sensitivity)}")
    print(f"worst time       : {worst['time']} "
          f"({worst['gate_value_pct']:.3f}%)")
    print(f"maximum overall  : {maximum:.3f}%   limit {args.limit}%")
    print("WO-P7: PASS" if ok else "WO-P7: FAIL — over the 15% limit")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
