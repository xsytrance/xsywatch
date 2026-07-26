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
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

STATES = ("unknown", "blocked", "failed", "waived", "proposed", "complete")

# state -> the states that must be complete before it may be complete
#
# Checkpoint B rc2 re-review, ruling 1: the direction
# `installed-APK-hash-verified -> device-validated` was backwards. An
# installed-byte pullback is INDEPENDENT evidence and a prerequisite for
# trusting the broader visual matrix — it is not downstream of it. The
# corrected graph makes the full matrix depend on proof that the intended
# bytes are actually installed, which is the causal order.
#
# This is not a relaxation to improve a score. It is the reviewer's ruling
# on a question deliberately left open rather than decided locally.
REQUIRES: dict[str, tuple[str, ...]] = {
    "assembled": (),
    "consumer-lineage-verified": ("assembled",),
    "dex-gate-passed": ("assembled",),
    "permissions-verified": ("assembled",),
    "installed-APK-hash-verified": ("consumer-lineage-verified",),
    "installed-resource-lineage-verified": ("installed-APK-hash-verified",),
    "device-validated": ("installed-resource-lineage-verified",
                         "permissions-verified"),
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

# Checkpoint B rc2 re-review, ruling 2: freshness is machine-enforced for
# machine-derived facts. It must not depend on a human remembering to
# rewrite stale prose — READINESS sat asserting "no Galaxy Watch7
# reachable" while a device session was already committed, and the checker
# reported 0 inconsistencies because it only ever caught a gate claiming
# MORE than its evidence supports.
CHECKER_SCHEMA = "agenor.release-readiness-checker/2"

# Fields that hold human judgement. They are never machine-generated,
# never machine-verified, and changing one must not alter a derived result.
SUBJECTIVE_FIELDS = ("owner_note", "reviewer_note", "waiver_rationale")

# Directory entries never contribute to an evidence fingerprint.
FINGERPRINT_EXCLUDE = {"__pycache__", ".git", ".DS_Store"}

# A `blocked` gate must not assert a blocker condition that its own
# canonical evidence set disproves. Each rule is (pattern asserting the
# condition, human description, predicate that the condition is GONE).
NO_DEVICE_CLAIM = re.compile(
    r"no\s+(?:\w+\s+){0,3}device[s]?\s+(?:was\s+|were\s+|is\s+|are\s+)?"
    r"reachable"
    r"|adb\s+reported\s+zero\s+devices"
    r"|zero\s+devices\s+throughout"
    r"|requires\s+the\s+device:"
    r"|no\s+Galaxy\s+Watch7\s+reachable",
    re.I)


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO)).replace("\\", "/")


def enumerate_evidence(repo: Path, rels: list[str]) -> list[Path]:
    """Every evidence file a gate cites, recursively, deterministically.

    Enumerated from the working tree rather than the index: on a clean
    checkout (CI, and any honest commit) the two are identical, but walking
    the tree also catches a file ADDED under a fingerprinted directory,
    which is one of the drift modes the ruling requires be rejected.
    """
    files: list[Path] = []
    for rel in rels:
        p = repo / rel
        if p.is_dir():
            for q in p.rglob("*"):
                if not q.is_file():
                    continue
                parts = q.relative_to(repo).parts
                if any(x in FINGERPRINT_EXCLUDE for x in parts):
                    continue
                files.append(q)
        elif p.is_file():
            files.append(p)
    return sorted(set(files), key=lambda q: str(q.relative_to(repo)))


def evidence_fingerprint(repo: Path, rels: list[str]) -> tuple[str, int]:
    """Deterministic fingerprint over sorted repo-relative path + sha256."""
    h = hashlib.sha256()
    files = enumerate_evidence(repo, rels)
    for f in files:
        h.update(str(f.relative_to(repo)).replace("\\", "/").encode("utf-8"))
        h.update(b"\0")
        h.update(sha256(f).encode("ascii"))
        h.update(b"\0")
    return f"sha256:{h.hexdigest()}", len(files)


def machine_summary(fingerprint: str, count: int) -> str:
    """Machine-derived, never hand-written."""
    return (f"{count} evidence file(s), fingerprint "
            f"{fingerprint.split(':')[1][:12]}…")


def _git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args],
                           capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def git_available(repo: Path) -> bool:
    return _git(repo, "rev-parse", "--git-dir")[0] == 0


def commit_is_reachable(repo: Path, sha: str) -> bool:
    """The commit a gate was evaluated at must exist and be an ancestor.

    A record evaluated against a commit this branch cannot see is not a
    record of this branch's evidence.
    """
    if _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")[0] != 0:
        return False
    return _git(repo, "merge-base", "--is-ancestor", sha, "HEAD")[0] == 0


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


def device_session_proven(repo: Path, ev: list[str], apk_sha: str) -> bool:
    """Does the canonical evidence set itself disprove 'no device'?"""
    for f in enumerate_evidence(repo, ev):
        if f.name == "DEVICE_TEST_RESULTS.md":
            return True
        if f.suffix.lower() in (".md", ".json", ".txt"):
            try:
                if apk_sha and apk_sha in f.read_text(encoding="utf-8",
                                                      errors="replace"):
                    return True
            except OSError:
                continue
    return False


def check_freshness(repo: Path, name: str, entry: dict, apk_sha: str) -> None:
    """Reject a record whose evidence moved under it.

    This is the half the original checker could not see. It verified that
    no gate claimed MORE than its evidence supported; it had no way to
    notice a gate claiming LESS, or a `detail` overtaken by events.
    """
    ev = _ev(entry)
    if not ev:
        # nothing cited: freshness is vacuous, but a stamped fingerprint
        # with no evidence behind it is a lie about what was checked
        if entry.get("evidence_fingerprint"):
            err(f"{name}: records an evidence_fingerprint but cites no "
                f"evidence")
        return

    fp, count = evidence_fingerprint(repo, ev)
    recorded = entry.get("evidence_fingerprint")
    if not recorded:
        err(f"{name}: no evidence_fingerprint — evidence-bearing gates must "
            f"pin the bytes they were evaluated against "
            f"(re-run with --stamp)")
    elif recorded != fp:
        err(f"{name}: evidence has CHANGED since evaluation — recorded "
            f"{str(recorded).split(':')[-1][:12]}… but the cited evidence "
            f"now fingerprints {fp.split(':')[1][:12]}… ({count} file(s)). "
            f"A file was changed, added, removed or drifted; re-evaluate, "
            f"do not re-stamp blindly")

    schema = entry.get("checker_schema")
    if schema != CHECKER_SCHEMA:
        err(f"{name}: checker_schema {schema!r} != {CHECKER_SCHEMA!r} — the "
            f"record was produced by a different gate definition")

    at = entry.get("evaluated_at_commit")
    if not at:
        err(f"{name}: no evaluated_at_commit")
    elif not re.fullmatch(r"[0-9a-f]{40}", str(at)):
        err(f"{name}: evaluated_at_commit {at!r} is not a full commit sha")
    elif git_available(repo) and not commit_is_reachable(repo, str(at)):
        err(f"{name}: evaluated_at_commit {str(at)[:12]}… is not reachable "
            f"from HEAD — this record was evaluated against another commit")

    ms = entry.get("machine_summary")
    if ms is not None and ms != machine_summary(fp, count):
        err(f"{name}: machine_summary is hand-edited or stale "
            f"({ms!r}) — it is machine-derived and must not be written "
            f"by hand")

    # subjective prose is preserved, never generated, never verified
    for f in SUBJECTIVE_FIELDS:
        if f in entry and not isinstance(entry[f], str):
            err(f"{name}: {f} must be prose, got {type(entry[f]).__name__}")
    if entry.get("state") == "waived" and not entry.get("waiver_rationale"):
        err(f"{name}: a waived gate must carry an explicit waiver_rationale")

    # a blocked gate must not assert a condition its evidence disproves
    if entry.get("state") == "blocked":
        detail = str(entry.get("detail", ""))
        if NO_DEVICE_CLAIM.search(detail) and device_session_proven(
                repo, ev, apk_sha):
            err(f"{name}: STALE BLOCKER DETAIL — the record claims the "
                f"device was unreachable, but its own canonical evidence "
                f"set proves a device session occurred. Re-derive the "
                f"detail from the evidence")


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
    ap.add_argument("--stamp", action="store_true",
                    help="re-derive evidence fingerprints, evaluated_at_commit "
                         "and machine_summary from the CURRENT evidence, then "
                         "verify. An explicit human action: it pins what is "
                         "there now, it does not decide that what is there is "
                         "sufficient")
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

    if args.stamp:
        head = _git(REPO, "rev-parse", "HEAD")[1]
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            print("ERROR --stamp needs a git repository to record "
                  "evaluated_at_commit", file=sys.stderr)
            return 2
        for entry in states.values():
            ev = _ev(entry)
            if not ev:
                for k in ("evidence_fingerprint", "machine_summary",
                          "evaluated_at_commit", "checker_schema"):
                    entry.pop(k, None)
                continue
            fp, count = evidence_fingerprint(REPO, ev)
            entry["evidence_fingerprint"] = fp
            entry["machine_summary"] = machine_summary(fp, count)
            entry["evaluated_at_commit"] = head
            entry["checker_schema"] = CHECKER_SCHEMA
        # the summary is machine-derived; regenerating it here is what stops
        # it going stale the way the gate details did
        buckets: dict[str, list[str]] = {}
        for n, e in states.items():
            buckets.setdefault(str(e.get("state")), []).append(n)
        r["summary"] = {k: sorted(v) for k, v in sorted(buckets.items())}
        rp.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
        print(f"stamped {rp.relative_to(REPO)} at {head[:12]}… — "
              f"pinned what is there NOW; it does not decide sufficiency\n")

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

        # freshness applies to every state, not only `complete` — a stale
        # `blocked` record is exactly the failure this was added for
        check_freshness(REPO, name, entry, apk_sha)

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

    # --- candidate provenance must agree with the provenance record -----
    # Blocker 3: CANDIDATE.json claimed the AI-model licence position was an
    # unresolved owner action while PROVENANCE.json concluded the
    # repository-wide warning is not applicable to this candidate. A
    # manifest cannot state both.
    prov_p = cand / "PROVENANCE.json"
    cand_p = cand / "CANDIDATE.json"
    if not prov_p.exists():
        err("no PROVENANCE.json — candidate-specific artwork provenance "
            "must be closed, not inherited from a repository-wide warning")
    elif cand_p.exists():
        prov = json.loads(prov_p.read_text(encoding="utf-8"))
        cnd = json.loads(cand_p.read_text(encoding="utf-8"))
        if prov.get("candidate_version") != args.version:
            err(f"PROVENANCE.json is for "
                f"{prov.get('candidate_version')!r}, not {args.version!r}")
        bound = cnd.get("provenance_sha256")
        actual = sha256(prov_p)
        if bound is not None and bound != actual:
            err(f"CANDIDATE.json binds provenance {str(bound)[:12]}… but "
                f"PROVENANCE.json hashes to {actual[:12]}…")
        prov_clean = (not prov.get("assets_with_ai_checkpoint_pixels")
                      and not prov.get("assets_with_donor_image_pixels")
                      and not prov.get("assets_unresolved"))
        warn_status = str(prov.get("repository_wide_warning", {})
                          .get("status", ""))
        prov_says_na = "NOT APPLICABLE" in warn_status.upper()
        claimed = str(cnd.get("artwork_provenance", {}).get("status", ""))
        blob = json.dumps(cnd)
        candidate_says_unresolved = (
            "AI-model licence position for commercial sale" in blob
            or "AI-model license position for commercial sale" in blob
            or "unresolved" in claimed.lower())
        if prov_clean and prov_says_na and candidate_says_unresolved:
            err("CANDIDATE.json still records AI/artwork provenance as an "
                "unresolved owner action while PROVENANCE.json concludes "
                "the repository-wide warning is NOT APPLICABLE to this "
                "candidate — the manifest cannot state both")
        if (not prov_clean or not prov_says_na) and "closed" in claimed.lower():
            err("CANDIDATE.json claims candidate provenance is closed while "
                "PROVENANCE.json reports unresolved assets or an applicable "
                "repository-wide warning")

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
