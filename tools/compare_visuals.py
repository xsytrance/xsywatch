#!/usr/bin/env python3
"""Visual comparison gate (ADR-009 §4).

Compares two renders/captures and emits metrics, a diff heat-map, and a
pass/fail exit status.

Modes:
  exact     (default) — any pixel difference fails. For deterministic
            reference-render reruns and golden verification.
  device    — calibrated perceptual thresholds from the face contract
            (states.toml [compare.device_profile]), for physical-device
            screenshots. Thresholds are evidence-calibrated and sit far
            below WARBIRD-substitution-scale deltas.

Masks: grayscale PNG, white = compared, black = ignored. Every mask is
checked against the face-disc coverage policy
(states.toml [compare.mask_policy].min_disc_coverage) — an over-broad mask
is itself a failure (deliberate-failure fixture #8).

Usage:
  compare_visuals.py A.png B.png [--mode exact|device] [--mask m.png]
                     [--face aurelius] [--report DIR]

Exit codes: 0 pass; 1 visual difference beyond policy; 2 mask policy
violation or bad invocation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visuallib as V  # noqa: E402


def disc_coverage(mask_img) -> float:
    """Fraction of the 480×480 face disc (r=240) the mask keeps."""
    w, h = mask_img.size
    cx, cy, r = w / 2, h / 2, min(w, h) / 2
    px = mask_img.load()
    disc = kept = 0
    for y in range(h):
        dy2 = (y + 0.5 - cy) ** 2
        for x in range(w):
            if (x + 0.5 - cx) ** 2 + dy2 <= r * r:
                disc += 1
                if px[x, y] >= 128:
                    kept += 1
    return kept / disc if disc else 0.0


def compare(a_path: Path, b_path: Path, mode: str, mask_path: Path | None,
            face: str, report_dir: Path | None) -> int:
    from PIL import Image, ImageChops

    contract = V.VisualContract.load(face)
    policy = contract.raw["compare"]

    a = Image.open(a_path).convert("RGBA")
    b = Image.open(b_path).convert("RGBA")
    result = {
        "a": {"path": str(a_path), "sha256": V.sha256_file(a_path)},
        "b": {"path": str(b_path), "sha256": V.sha256_file(b_path)},
        "mode": mode,
        "mask": None,
        "thresholds": None,
    }
    if a.size != b.size:
        result["verdict"] = "FAIL"
        result["reason"] = f"size mismatch {a.size} vs {b.size}"
        _emit(result, report_dir, None)
        return 1

    mask = None
    if mask_path:
        mask = Image.open(mask_path).convert("L")
        if mask.size != a.size:
            print(f"FAIL: mask size {mask.size} != image size {a.size}")
            return 2
        cov = disc_coverage(mask)
        min_cov = policy["mask_policy"]["min_disc_coverage"]
        result["mask"] = {"path": str(mask_path),
                          "sha256": V.sha256_file(mask_path),
                          "disc_coverage": round(cov, 4),
                          "min_disc_coverage": min_cov}
        if cov < min_cov:
            result["verdict"] = "FAIL"
            result["reason"] = (f"mask keeps only {cov:.1%} of the face "
                                f"disc; policy requires ≥{min_cov:.0%}")
            _emit(result, report_dir, None)
            return 2

    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    px = diff.load()
    mpx = mask.load() if mask else None
    w, h = diff.size
    compared = changed = 0
    max_delta = 0
    sum_delta = 0
    for y in range(h):
        for x in range(w):
            if mpx is not None and mpx[x, y] < 128:
                continue
            compared += 1
            d = max(px[x, y])
            if d:
                changed += 1
                sum_delta += d
                if d > max_delta:
                    max_delta = d

    pct = 100.0 * changed / compared if compared else 0.0
    mean_delta = sum_delta / compared if compared else 0.0
    result["metrics"] = {
        "compared_pixels": compared,
        "changed_pixels": changed,
        "changed_pixel_pct": round(pct, 4),
        "max_channel_delta": max_delta,
        "mean_channel_delta": round(mean_delta, 4),
    }

    if mode == "exact":
        ok = changed == 0
        result["thresholds"] = {"mode": "exact (zero tolerance)"}
    else:
        t = policy["device_profile"]
        result["thresholds"] = t
        ok = (pct <= t["max_changed_pixel_pct"]
              and mean_delta <= t["max_mean_channel_delta"]
              and max_delta <= t["max_channel_delta"])
    result["verdict"] = "PASS" if ok else "FAIL"
    _emit(result, report_dir, diff)
    return 0 if ok else 1


def _emit(result: dict, report_dir: Path | None, diff) -> None:
    print(json.dumps(result, indent=2, sort_keys=True))
    if report_dir is None:
        return
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "compare.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    if diff is not None:
        from PIL import Image
        # Heat-map: amplify deltas so subtle drift is visible in review.
        heat = diff.point(lambda p: min(255, p * 8))
        heat.save(report_dir / "diff_heatmap.png", format="PNG",
                  optimize=False)
        print(f"report: {report_dir}/compare.json, diff_heatmap.png")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--mode", choices=("exact", "device"), default="exact")
    ap.add_argument("--mask", type=Path)
    ap.add_argument("--face", default="aurelius")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    return compare(args.a, args.b, args.mode, args.mask, args.face,
                   args.report)


if __name__ == "__main__":
    raise SystemExit(main())
