#!/usr/bin/env python3
"""Consumer release-candidate lineage verifier.

Checkpoint B blocker 2: the rc1 candidate manifest attributed its
artifacts to a single `consumer_commit` that PREDATED the packaging work
which produced them. A commit that does not contain the build inputs
cannot be the snapshot the artifacts came from, and recording it as such
is a false provenance claim — the consumer equivalent of the studio's
producing/metadata split, which was already correct.

Three roles are now explicit and machine-checked:

  consumer_source_commit    contains EVERY input used to build the
                            candidate — face.toml, Gradle files and
                            wrapper, the Android manifest, the WFF XML and
                            resources, build_candidate.sh, the dex guard,
                            verify_candidate.py and every imported studio
                            resource. It need not contain the artifacts.
  consumer_artifact_commit  descends from the source commit; contains the
                            canonical APK, AAB and VERIFY record.
  candidate_metadata_commit descends from the artifact commit; contains
                            the final CANDIDATE and READINESS records. It
                            must be later, because a metadata file cannot
                            contain its own commit hash.

The source commit is then PROVED by rebuilding: two clean detached
worktrees are checked out at that exact commit, both are built, and both
artifact hashes must be byte-identical to each other AND equal to the
canonical committed artifacts. Ancestry alone would only prove ordering;
rebuilding proves the commit really produces those bytes.

    python3 tools/verify_lineage.py aurelius --version 2.0.0-rc2 \
        --source <sha> --artifact <sha> --metadata <sha> [--build] \
        [--report OUT.json]

Exit codes: 0 verified, 1 a lineage defect, 2 bad invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Every path whose bytes can change the produced artifacts. A candidate's
# declared source commit must contain all of them.
BUILD_INPUT_PATHS = [
    "tools/build_candidate.sh",
    "tools/dex_guard.py",
    "tools/verify_candidate.py",
    "tools/verify_lineage.py",
    "watchfaces/{face}/engine/face.toml",
    "watchfaces/{face}/engine/handoff.json",
    "watchfaces/{face}/app/build.gradle.kts",
    "watchfaces/{face}/build.gradle.kts",
    "watchfaces/{face}/settings.gradle.kts",
    "watchfaces/{face}/gradlew",
    "watchfaces/{face}/gradle/wrapper/gradle-wrapper.properties",
    "watchfaces/{face}/gradle/wrapper/gradle-wrapper.jar",
    "watchfaces/{face}/app/src/main/AndroidManifest.xml",
    "watchfaces/{face}/app/src/main/res/raw/watchface.xml",
]

# Whole trees that must be present and are hashed as a set.
BUILD_INPUT_TREES = [
    "watchfaces/{face}/app/src/main/res",
]

issues: list[str] = []


def err(msg: str) -> None:
    issues.append(msg)
    print(f"ERROR {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def git(*args: str, cwd: Path | None = None) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd or REPO),
                       capture_output=True, text=True)
    if r.returncode:
        raise subprocess.CalledProcessError(r.returncode, args, r.stdout,
                                            r.stderr)
    return r.stdout.strip()


def commit_exists(sha: str) -> bool:
    try:
        return git("cat-file", "-t", sha) == "commit"
    except subprocess.CalledProcessError:
        return False


def is_ancestor(a: str, b: str) -> bool:
    r = subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                       cwd=str(REPO), capture_output=True)
    return r.returncode == 0


def path_at(sha: str, path: str) -> str | None:
    """Blob sha of `path` at `sha`, or None if absent."""
    try:
        out = git("rev-parse", f"{sha}:{path}")
        return out
    except subprocess.CalledProcessError:
        return None


def tree_hash_at(sha: str, path: str) -> str | None:
    try:
        listing = git("ls-tree", "-r", sha, "--", path)
    except subprocess.CalledProcessError:
        return None
    if not listing:
        return None
    return hashlib.sha256(listing.encode()).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_in_worktree(sha: str, face: str, tag: str) -> dict:
    """Check out `sha` into a clean detached worktree and build there."""
    tmp = Path(tempfile.mkdtemp(prefix=f"rc-{tag}-"))
    wt = tmp / "wt"
    try:
        git("worktree", "add", "--detach", str(wt), sha)
        # local.properties is untracked; Gradle falls back to ANDROID_HOME.
        env = dict(os.environ)
        env.setdefault("ANDROID_HOME",
                       os.path.expanduser("~/Android/Sdk"))
        out = tmp / "out"
        out.mkdir()
        r = subprocess.run(
            ["bash", str(wt / "tools/build_candidate.sh"), "--clean",
             "--out", str(out)],
            cwd=str(wt), capture_output=True, text=True, env=env)
        if r.returncode:
            return {"ok": False,
                    "error": (r.stdout + r.stderr)[-3000:]}
        aab = sorted(out.glob("*.aab"))
        apk = sorted(out.glob("*.apk"))
        if not aab or not apk:
            return {"ok": False, "error": "build produced no artifacts"}
        return {"ok": True,
                "aab_sha256": sha256_file(aab[0]),
                "aab_size": aab[0].stat().st_size,
                "apk_sha256": sha256_file(apk[0]),
                "apk_size": apk[0].stat().st_size}
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=str(REPO), capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("face")
    ap.add_argument("--version", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--build", action="store_true",
                    help="rebuild twice from detached worktrees")
    ap.add_argument("--report")
    args = ap.parse_args()

    face = args.face
    cand = REPO / "releases" / face / "candidates" / args.version

    # A metadata file cannot contain its own commit hash, so the metadata
    # commit is RESOLVED from history rather than declared — the same way
    # tools/import_handoff.py resolves the studio metadata commit.
    if args.metadata == "auto":
        rel = f"releases/{face}/candidates/{args.version}/CANDIDATE.json"
        try:
            args.metadata = git("log", "-1", "--format=%H", "--", rel)
        except subprocess.CalledProcessError:
            args.metadata = ""
        if not args.metadata:
            print(f"ERROR could not resolve the metadata commit from "
                  f"git log -1 -- {rel}", file=sys.stderr)
            return 2
        print(f"      metadata commit resolved from history: "
              f"{args.metadata[:12]}")

    result: dict = {
        "face": face,
        "candidate_version": args.version,
        "roles": {
            "consumer_source_commit": args.source,
            "consumer_artifact_commit": args.artifact,
            "candidate_metadata_commit": args.metadata,
        },
    }

    # ---- the commits must exist -----------------------------------------
    for role, sha in result["roles"].items():
        if not commit_exists(sha):
            err(f"{role} {sha[:12]} does not exist in this repository")
    if issues:
        return _finish(result, args)

    # ---- ancestry --------------------------------------------------------
    if args.source == args.artifact:
        err("consumer_artifact_commit must be a LATER commit than the "
            "source commit: it contains artifacts the source commit does "
            "not")
    elif not is_ancestor(args.source, args.artifact):
        err(f"consumer_artifact_commit {args.artifact[:12]} does not "
            f"descend from consumer_source_commit {args.source[:12]}")
    else:
        ok(f"artifact {args.artifact[:12]} descends from source "
           f"{args.source[:12]}")

    if args.artifact == args.metadata:
        err("candidate_metadata_commit must be a LATER commit than the "
            "artifact commit: a metadata file cannot contain its own "
            "commit hash")
    elif not is_ancestor(args.artifact, args.metadata):
        err(f"candidate_metadata_commit {args.metadata[:12]} does not "
            f"descend from consumer_artifact_commit {args.artifact[:12]}")
    else:
        ok(f"metadata {args.metadata[:12]} descends from artifact "
           f"{args.artifact[:12]}")

    # ---- every build input must exist at the SOURCE commit --------------
    inputs: dict[str, str] = {}
    missing: list[str] = []
    for tpl in BUILD_INPUT_PATHS:
        p = tpl.format(face=face)
        blob = path_at(args.source, p)
        if blob is None:
            missing.append(p)
        else:
            inputs[p] = blob
    for tpl in BUILD_INPUT_TREES:
        p = tpl.format(face=face)
        th = tree_hash_at(args.source, p)
        if th is None:
            missing.append(p + " (tree)")
        else:
            inputs[p + "/**"] = th
    if missing:
        err(f"consumer_source_commit {args.source[:12]} is missing "
            f"{len(missing)} build input(s): {missing} — it cannot be the "
            f"snapshot these artifacts were built from")
    else:
        ok(f"all {len(inputs)} build inputs present at the source commit")
    result["build_inputs_at_source"] = inputs

    # ---- the source commit must carry the candidate's own identity ------
    gradle_blob = path_at(args.source,
                          f"watchfaces/{face}/app/build.gradle.kts")
    if gradle_blob:
        txt = git("cat-file", "-p", gradle_blob)
        if f'versionName = "{args.version}"' not in txt:
            err(f"consumer_source_commit does not declare versionName "
                f"{args.version!r} — a source commit that predates the "
                f"version bump cannot have produced this candidate")
        else:
            ok(f"source commit declares versionName {args.version}")
        result["source_gradle_blob"] = gradle_blob

    # ---- the artifact commit must contain the artifacts ------------------
    rel = f"releases/{face}/candidates/{args.version}"
    canonical: dict[str, str] = {}
    for name in sorted(p.name for p in cand.glob("*.aab")) + \
                sorted(p.name for p in cand.glob("*.apk")):
        blob = path_at(args.artifact, f"{rel}/{name}")
        if blob is None:
            err(f"consumer_artifact_commit does not contain {name}")
        else:
            canonical[name] = sha256_file(cand / name)
    if path_at(args.artifact, f"{rel}/VERIFY.json") is None:
        err("consumer_artifact_commit does not contain VERIFY.json")
    if not issues:
        ok(f"artifact commit contains the canonical artifacts and VERIFY")
    result["canonical_artifacts"] = canonical

    # ---- the metadata commit must contain the metadata -------------------
    for name in ("CANDIDATE.json", "READINESS.json"):
        if path_at(args.metadata, f"{rel}/{name}") is None:
            err(f"candidate_metadata_commit does not contain {name}")
    if not any("metadata_commit does not contain" in i for i in issues):
        ok("metadata commit contains CANDIDATE and READINESS")

    # ---- rebuild twice from the source commit ---------------------------
    if args.build:
        builds = []
        for i in (1, 2):
            print(f"  rebuilding from {args.source[:12]} (worktree {i})…")
            b = build_in_worktree(args.source, face, f"{args.version}-{i}")
            builds.append(b)
            if not b.get("ok"):
                err(f"rebuild {i} from the source commit failed: "
                    f"{b.get('error', '')[:400]}")
        result["rebuilds"] = builds
        if all(b.get("ok") for b in builds):
            b1, b2 = builds
            if b1["aab_sha256"] != b2["aab_sha256"]:
                err(f"the two rebuilds produced different AABs "
                    f"({b1['aab_sha256'][:12]} vs {b2['aab_sha256'][:12]})")
            elif b1["apk_sha256"] != b2["apk_sha256"]:
                err(f"the two rebuilds produced different APKs "
                    f"({b1['apk_sha256'][:12]} vs {b2['apk_sha256'][:12]})")
            else:
                ok(f"two detached worktree builds are byte-identical")
            for name, h in canonical.items():
                key = "aab_sha256" if name.endswith(".aab") else "apk_sha256"
                if b1.get(key) != h:
                    err(f"{name}: the committed canonical artifact "
                        f"({h[:12]}) does not match what the declared "
                        f"source commit rebuilds to ({b1.get(key, '?')[:12]})")
                else:
                    ok(f"{name} rebuilds to the canonical hash {h[:12]}…")
            result["reproducible"] = not issues

    return _finish(result, args)


def _finish(result: dict, args) -> int:
    result["problems"] = issues
    result["verified"] = not issues
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"report: {args.report}")
    print()
    print(f"{len(issues)} problem(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
