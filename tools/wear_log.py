#!/usr/bin/env python3
"""Owner wear-log helper — append a Phase-4 wear session by answering
prompts, so AGENOR never hand-edits an evidence file.

    python3 tools/wear_log.py                # interactive, guided
    python3 tools/wear_log.py --show         # print sessions recorded so far
    python3 tools/wear_log.py --validate     # schema/consistency check

Every answer is optional: press Enter to leave a field blank and it is
recorded as null. A blank field is honest evidence ("not observed"); an
invented one is not. Nothing here fabricates or defaults a subjective
judgement.

Writes one JSON file per session under
docs/reports/evidence/phase-4/aurelius/wear/sessions/ and regenerates the
human-readable WEAR_LOG.md roll-up.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WEAR = REPO / "docs/reports/evidence/phase-4/aurelius/wear"
SESSIONS = WEAR / "sessions"

# The artifact every Phase-4 wear observation is bound to. Checkpoint A
# wear happens on the tested Phase-3 build; Checkpoint B rebinds to the
# release candidate.
BOUND_ARTIFACT = {
    "apk_sha256": ("5a1271ab95c9fdbc04c1b8b5781a40cea2cb4c"
                   "a11f279c69cb70aeb23f50474a"),
    "package": "com.xsytrance.aurelius",
    "version_name": "1.0",
    "version_code": 1,
    "visual_version": "field-tourbillon-mk2-r2",
    "approval_id": "APPROVAL-0004",
    "device": "Samsung Galaxy Watch7 44 mm (SM-L310, Android 16 / API 36)",
}

CONTEXTS = ["office", "home", "outdoor", "transit", "exercise", "low-light"]

# (key, prompt, kind). kind: text | int | float | choice:a/b/c | multi
FIELDS = [
    ("date", "Date of the session (YYYY-MM-DD)", "date"),
    ("duration_hours", "Roughly how many hours worn", "float"),
    ("contexts", f"Contexts ({', '.join(CONTEXTS)}) — comma separated",
     "multi"),
    ("normal_readability",
     "Normal-mode readability — could you read the time at a glance", "text"),
    ("aod_readability",
     "AOD readability and perceived brightness", "text"),
    ("date_usability", "Date aperture — legible and useful", "text"),
    ("reserve_gauge_usability",
     "Reserve gauge — could you read the battery level", "text"),
    ("motion_smoothness", "Motion smoothness — any stutter", "text"),
    ("motion_distracting",
     "Did the animation become distracting over time", "text"),
    ("parallax_impression", "Parallax / sheen impression on the wrist",
     "text"),
    ("picker_activation",
     "Picker preview and activation behaviour", "text"),
    ("charging_sleep_wake",
     "Charging, and sleep/wake behaviour", "text"),
    ("battery_start_pct", "Battery % at start (blank if not noted)", "int"),
    ("battery_end_pct", "Battery % at end (blank if not noted)", "int"),
    ("battery_caveats",
     "Battery caveats — what else was running, GPS, workouts, calls, "
     "screen-on time", "text"),
    ("stale_or_missing_data",
     "Any stale or missing data (HR, battery, date)", "text"),
    ("accidental_interaction",
     "Accidental taps or interaction surprises", "text"),
    ("glare_clipping_contrast",
     "Glare, clipping, contrast or visual-hierarchy findings", "text"),
    ("still_feels_premium",
     "Does it still feel premium after repeated use", "text"),
    ("disposition", "Overall disposition", "choice:keep/investigate/change"),
    ("notes", "Anything else", "text"),
]


def _ask(prompt: str, kind: str):
    while True:
        raw = input(f"{prompt}\n  > ").strip()
        if not raw:
            return None
        if kind == "text":
            return raw
        if kind == "date":
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                return raw
            print("  ! expected YYYY-MM-DD")
            continue
        if kind == "int":
            try:
                return int(raw)
            except ValueError:
                print("  ! expected a whole number")
                continue
        if kind == "float":
            try:
                return float(raw)
            except ValueError:
                print("  ! expected a number")
                continue
        if kind == "multi":
            vals = [v.strip().lower() for v in raw.split(",") if v.strip()]
            bad = [v for v in vals if v not in CONTEXTS]
            if bad:
                print(f"  ! unknown context(s): {', '.join(bad)}")
                continue
            return vals
        if kind.startswith("choice:"):
            opts = kind.split(":", 1)[1].split("/")
            if raw.lower() in opts:
                return raw.lower()
            print(f"  ! expected one of {', '.join(opts)}")
            continue


def add() -> int:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    print(__doc__.split("Writes one JSON")[0].rstrip())
    print(f"\nBound artifact: {BOUND_ARTIFACT['visual_version']} / "
          f"APK {BOUND_ARTIFACT['apk_sha256'][:12]}…\n"
          f"Press Enter to skip any question.\n")
    rec = {"schema": "agenor.wear-session/1",
           "recorded_utc": datetime.now(timezone.utc)
           .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "observer": "AGENOR (product owner)",
           "artifact": dict(BOUND_ARTIFACT),
           "observations": {}}
    for key, prompt, kind in FIELDS:
        rec["observations"][key] = _ask(prompt, kind)
    date = rec["observations"].get("date") or "undated"
    n = 1
    while (SESSIONS / f"{date}-{n:02d}.json").exists():
        n += 1
    out = SESSIONS / f"{date}-{n:02d}.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)}")
    render()
    print("Commit it with:  git add docs/reports/evidence/phase-4 && "
          "git commit")
    return 0


def _sessions() -> list:
    if not SESSIONS.is_dir():
        return []
    out = []
    for p in sorted(SESSIONS.glob("*.json")):
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    return out


def render() -> None:
    """Regenerate the human-readable roll-up from the session files."""
    rows = _sessions()
    lines = [
        "# AURELIUS — Phase-4 owner wear log",
        "",
        "Generated by `tools/wear_log.py`. **Do not hand-edit** — edit or add",
        "a session under `sessions/` (or re-run the tool) and it is rebuilt.",
        "",
        f"Bound artifact: `{BOUND_ARTIFACT['visual_version']}` · "
        f"APK `{BOUND_ARTIFACT['apk_sha256'][:16]}…` · "
        f"`{BOUND_ARTIFACT['package']}` {BOUND_ARTIFACT['version_name']} "
        f"(versionCode {BOUND_ARTIFACT['version_code']}) · "
        f"{BOUND_ARTIFACT['device']}",
        "",
        f"Sessions recorded: **{len(rows)}**",
        "",
    ]
    if not rows:
        lines += [
            "> No wear sessions recorded yet. Every subjective field below is",
            "> deliberately empty: Phase-4 scope forbids inventing owner",
            "> observations. Run `python3 tools/wear_log.py` after wearing",
            "> the watch.",
            "",
        ]
    for p, rec in rows:
        o = rec["observations"]
        lines.append(f"## {o.get('date') or 'undated'} — {p.name}")
        lines.append("")
        bs, be = o.get("battery_start_pct"), o.get("battery_end_pct")
        if bs is not None and be is not None:
            lines.append(f"Battery {bs}% → {be}% "
                         f"(**experiential, not a controlled measurement** — "
                         f"see caveats)")
            lines.append("")
        for key, prompt, _kind in FIELDS:
            v = o.get(key)
            if isinstance(v, list):
                v = ", ".join(v) if v else None
            lines.append(f"- **{prompt}** — "
                         f"{v if v not in (None, '') else '_not recorded_'}")
        lines.append("")
    # Trailing "" entries above give section spacing; strip them so the
    # file ends with exactly one newline (git diff --check / CI).
    while lines and not lines[-1]:
        lines.pop()
    (WEAR / "WEAR_LOG.md").write_text("\n".join(lines) + "\n",
                                      encoding="utf-8")


def validate() -> int:
    problems = []
    for p, rec in _sessions():
        if rec.get("schema") != "agenor.wear-session/1":
            problems.append(f"{p.name}: unknown schema {rec.get('schema')!r}")
        art = rec.get("artifact", {})
        if art.get("apk_sha256") != BOUND_ARTIFACT["apk_sha256"]:
            problems.append(
                f"{p.name}: artifact apk_sha256 does not match the bound "
                f"Phase-4 artifact — a wear observation must name the exact "
                f"build it was made on")
        o = rec.get("observations", {})
        unknown = set(o) - {k for k, _, _ in FIELDS}
        if unknown:
            problems.append(f"{p.name}: unknown fields {sorted(unknown)}")
        d = o.get("disposition")
        if d is not None and d not in ("keep", "investigate", "change"):
            problems.append(f"{p.name}: disposition {d!r} is not "
                            f"keep|investigate|change")
    for msg in problems:
        print(f"ERROR {msg}")
    print(f"{len(problems)} error(s) across {len(_sessions())} session(s)")
    return 1 if problems else 0


def show() -> int:
    rows = _sessions()
    if not rows:
        print("no wear sessions recorded yet")
        return 0
    for p, rec in rows:
        o = rec["observations"]
        print(f"{p.name}: {o.get('date')} · {o.get('duration_hours')}h · "
              f"{', '.join(o.get('contexts') or []) or '-'} · "
              f"disposition={o.get('disposition') or '-'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--show", action="store_true")
    g.add_argument("--validate", action="store_true")
    g.add_argument("--render", action="store_true",
                   help="regenerate WEAR_LOG.md from sessions/")
    a = ap.parse_args()
    if a.show:
        return show()
    if a.validate:
        return validate()
    if a.render:
        render()
        print("regenerated WEAR_LOG.md")
        return 0
    return add()


if __name__ == "__main__":
    sys.exit(main())
