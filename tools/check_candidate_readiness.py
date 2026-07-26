#!/usr/bin/env python3
"""Fail-closed release-candidate readiness gate.

Checkpoint B blocker 5: the candidate validator accepted evidence when the
referenced PATH EXISTED. An empty wear directory and a
DEVICE_EVIDENCE_BLOCKER.md therefore both satisfied it, even though the
required evidence was entirely absent. Path existence is not completion.

This gate reads READINESS.json and re-derives every claimed state from the
evidence itself. A state may only be `complete` when the evidence exists,
parses, passes, covers what it must, and is bound to THIS candidate's
artifact hash.

    python3 tools/check_candidate_readiness.py aurelius --version 2.0.0-rc2

Exit codes: 0 the record is internally honest, 1 a claim is not supported
by its evidence, 2 bad invocation.

Note what "0" means: it does NOT mean the candidate is publishable. It
means every claim in the record is true. A record honestly reporting five
blocked gates exits 0 — and `publishable` stays false.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

STATES = ("unknown", "blocked", "failed", "waived", "proposed", "complete")

# state -> the states that must be complete before it may be complete
REQUIRES: dict[str, tuple[str, ...]] = {
    "assembled": (),
    "consumer-lineage-verified": ("assembled",),
    "dex-gate-passed": ("assembled",),
    "permissions-verified": ("assembled",),
    "device-validated": ("assembled",),
    "installed-APK-hash-verified": ("device-validated",),
    "installed-resource-lineage-verified": ("installed-APK-hash-verified",),
    "owner-wear-complete": ("device-validated",),
    "owner-pixel-approved": ("owner-wear-complete",),
    "architecture-approved": (
        "consumer-lineage-verified", "dex-gate-passed",
        "permissions-verified", "installed-resource-lineage-verified",
        "owner-pixel-approved"),
    "policy-ready": ("permissions-verified",),
    "signing-authorized": ("architecture-approved", "policy-ready"),
    "publishable": ("architecture-approved", "policy-ready",
                    "signing-authorized", "owner-pixel-approved",
                    "owner-wear-complete"),
}

REQUIRED_WEAR_CONTEXTS = {"office", "home", "outdoor", "low-light"}

issues: list[str] = []


def err(msg: str) -> None:
    issues.append(msg)
    print(f"ERROR {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def note(msg: str) -> None:
    print(f"      {msg}")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _ev(entry: dict) -> list[str]:
    e = entry.get("evidence") or []
    return [e] if isinstance(e, str) else list(e)


def check_wear(entry: dict, apk_sha: str) -> None:
    """An empty directory is not wear evidence."""
    paths = _ev(entry)
    sessions: list[dict] = []
    for rel in paths:
        p = REPO / rel
        if not p.exists():
            err(f"owner-wear-complete: evidence path does not exist: {rel}")
            return
        files = sorted(p.glob("*.json")) if p.is_dir() else [p]
        for f in files:
            try:
                sessions.append(json.loads(f.read_text(encoding="utf-8")))
            except json.JSONDecodeError as e:
                err(f"owner-wear-complete: {f.name} is not valid JSON ({e})")
                return
    if not sessions:
        err("owner-wear-complete claims complete but no wear session files "
            "exist — an empty directory is not evidence")
        return

    bad = [s for s in sessions
           if s.get("artifact", {}).get("apk_sha256") != apk_sha]
    if bad:
        err(f"owner-wear-complete: {len(bad)} session(s) are bound to a "
            f"different APK than this candidate ({apk_sha[:12]}…) — an "
            f"observation of another build is not evidence for this one")
        return

    contexts: set[str] = set()
    aod = charging = disposition = False
    for s in sessions:
        o = s.get("observations", {})
        contexts |= set(o.get("contexts") or [])
        if o.get("aod_readability"):
            aod = True
        if o.get("charging_sleep_wake"):
            charging = True
        if o.get("disposition"):
            disposition = True
    missing = REQUIRED_WEAR_CONTEXTS - contexts
    if missing:
        err(f"owner-wear-complete: required context coverage incomplete — "
            f"missing {sorted(missing)} (have {sorted(contexts)})")
    if not aod:
        err("owner-wear-complete: no session records sustained AOD "
            "readability")
    if not charging:
        err("owner-wear-complete: no session records a charging transition")
    if not disposition:
        err("owner-wear-complete: no session records a final owner "
            "disposition")
    if not issues:
        ok(f"owner-wear-complete: {len(sessions)} session(s), contexts "
           f"{sorted(contexts)}, all bound to {apk_sha[:12]}…")


def check_device(entry: dict, apk_sha: str) -> None:
    """A blocker document is not device validation."""
    for rel in _ev(entry):
        p = REPO / rel
        if not p.exists():
            err(f"device-validated: evidence path does not exist: {rel}")
            return
        names = ([q.name for q in p.rglob("*")] if p.is_dir() else [p.name])
        if any("BLOCKER" in n.upper() for n in names):
            err(f"device-validated claims complete but the evidence still "
                f"contains a blocker document ({rel}) — a record of why "
                f"validation could not happen is not validation")
            return
        results = ([q for q in p.rglob("DEVICE_TEST_RESULTS.md")]
                   if p.is_dir() else [])
        if not results:
            err(f"device-validated: no DEVICE_TEST_RESULTS.md under {rel}")
            return
        for r in results:
            txt = r.read_text(encoding="utf-8", errors="replace")
            if apk_sha not in txt:
                err(f"device-validated: {r.name} does not reference this "
                    f"candidate's APK hash {apk_sha[:12]}… — device "
                    f"evidence must name the exact build it was taken on")
                return
    ok("device-validated: results present and bound to the candidate APK")


def check_hash_claim(entry: dict, expect: str, label: str) -> None:
    got = entry.get("value") or entry.get("hash")
    if got != expect:
        err(f"{label}: recorded hash {str(got)[:12]}… != the candidate "
            f"artifact {expect[:12]}…")
    else:
        ok(f"{label}: matches the candidate artifact")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--version", required=True)
    ap.add_argument("--json", action="store_true",
                    help="print the resolved state table as JSON")
    args = ap.parse_args()

    cand = REPO / "releases" / args.face / "candidates" / args.version
    rp = cand / "READINESS.json"
    if not rp.exists():
        print(f"ERROR no READINESS.json at {rp}", file=sys.stderr)
        return 2
    r = json.loads(rp.read_text(encoding="utf-8"))

    if r.get("candidate_version") != args.version:
        err(f"READINESS.json is for {r.get('candidate_version')!r}, not "
            f"{args.version!r}")

    # --- the artifact hashes this record must be bound to ---------------
    apks = sorted(cand.glob("*.apk"))
    aabs = sorted(cand.glob("*.aab"))
    if len(apks) != 1 or len(aabs) != 1:
        err(f"expected exactly one .apk and one .aab in {cand}")
        return _finish(r, args)
    apk_sha, aab_sha = sha256(apks[0]), sha256(aabs[0])
    if r.get("artifact", {}).get("apk_sha256") != apk_sha:
        err(f"READINESS.json apk_sha256 does not match the committed APK "
            f"({apk_sha[:12]}…)")
    if r.get("artifact", {}).get("aab_sha256") != aab_sha:
        err(f"READINESS.json aab_sha256 does not match the committed AAB "
            f"({aab_sha[:12]}…)")

    states: dict[str, dict] = r.get("states", {})
    missing = set(REQUIRES) - set(states)
    if missing:
        err(f"READINESS.json is missing required state(s): {sorted(missing)}")
    extra = set(states) - set(REQUIRES)
    if extra:
        err(f"READINESS.json declares unknown state(s): {sorted(extra)}")

    for name, entry in sorted(states.items()):
        before = len(issues)
        st = entry.get("state")
        if st not in STATES:
            err(f"{name}: state {st!r} is not one of {STATES}")
            continue

        # every non-unknown state must say why
        if st != "unknown" and not entry.get("detail"):
            err(f"{name}: state {st!r} must carry a `detail` explaining it")

        if st == "complete":
            # 1. predecessors
            for dep in REQUIRES.get(name, ()):
                dep_state = states.get(dep, {}).get("state")
                if dep_state != "complete":
                    err(f"{name} is `complete` but its prerequisite {dep} "
                        f"is {dep_state!r} — a gate cannot close before the "
                        f"gates it depends on")
            # 2. must reference the candidate artifact
            if entry.get("artifact_sha256") not in (apk_sha, aab_sha):
                err(f"{name} is `complete` but does not reference this "
                    f"candidate's artifact hash")
            # 3. must reference evidence that exists
            ev = _ev(entry)
            if not ev:
                err(f"{name} is `complete` but references no evidence")
            for rel in ev:
                if not (REPO / rel).exists():
                    err(f"{name}: evidence path does not exist: {rel}")

        # content checks, regardless of claimed state
        if name == "owner-wear-complete" and st == "complete":
            check_wear(entry, apk_sha)
        if name == "device-validated" and st == "complete":
            check_device(entry, apk_sha)
        if name == "installed-APK-hash-verified" and st == "complete":
            check_hash_claim(entry, apk_sha, name)
        if name == "dex-gate-passed" and st == "complete":
            v = cand / "VERIFY.json"
            if not v.exists():
                err("dex-gate-passed: no VERIFY.json to support it")
            else:
                g = json.loads(v.read_text()).get("dex_gate")
                if not g or not g.get("passed"):
                    err("dex-gate-passed: VERIFY.json carries no passing "
                        "dex-gate evidence")
        if name == "permissions-verified" and st == "complete":
            v = cand / "VERIFY.json"
            if v.exists():
                perms = json.loads(v.read_text()).get(
                    "manifest_permissions", {}).get("apk")
                if perms is None:
                    err("permissions-verified: VERIFY.json records no APK "
                        "permission set")

        if st == "complete":
            if len(issues) == before:
                ok(f"{name}: complete")
            else:
                print(f"      {name}: claimed complete but the evidence "
                      f"does not support it (see errors above)")
        else:
            note(f"{name}: {st}" + (f" — {entry.get('detail','')[:80]}"
                                    if entry.get("detail") else ""))

    # --- publishable is the hard interlock -------------------------------
    pub = states.get("publishable", {}).get("state")
    if pub == "complete":
        for dep in REQUIRES["publishable"]:
            if states.get(dep, {}).get("state") != "complete":
                err(f"publishable is `complete` while {dep} is not — this "
                    f"is the interlock that must never open early")
    if r.get("publication_status") != "not published":
        err(f"publication_status must be 'not published' while a candidate "
            f"is unapproved, got {r.get('publication_status')!r}")

    return _finish(r, args)


def _finish(r: dict, args) -> int:
    if args.json:
        print(json.dumps({k: v.get("state")
                          for k, v in r.get("states", {}).items()},
                         indent=2, sort_keys=True))
    complete = sum(1 for v in r.get("states", {}).values()
                   if v.get("state") == "complete")
    total = len(REQUIRES)
    print()
    word = "inconsistency" if len(issues) == 1 else "inconsistencies"
    print(f"{complete}/{total} gates complete; {len(issues)} {word}")
    if not issues:
        print("READINESS record is internally honest "
              "(this does NOT mean the candidate is publishable)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
