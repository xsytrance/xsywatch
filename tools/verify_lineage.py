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
import re
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


LFS_POINTER = re.compile(
    rb"^version https://git-lfs\.github\.com/spec/v1\s+oid sha256:([0-9a-f]{64})\s+size (\d+)",
    re.M)


def blob_bytes(sha: str, path: str) -> bytes | None:
    """Raw bytes of `path` as stored in commit `sha` (may be an LFS
    pointer rather than the payload)."""
    r = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=str(REPO),
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def object_identity(sha: str, path: str) -> dict | None:
    """The authoritative content hash of `path` AT commit `sha`.

    Ordinary blob -> sha256 of the stored bytes.
    Git-LFS pointer -> the declared `oid sha256:`, with the smudged
    payload verified separately so a pointer cannot claim an OID its
    payload does not have.
    """
    raw = blob_bytes(sha, path)
    if raw is None:
        return None
    m = LFS_POINTER.match(raw)
    if m:
        oid = m.group(1).decode()
        declared_size = int(m.group(2))
        payload = None
        r = subprocess.run(["git", "cat-file", "--filters", f"{sha}:{path}"],
                           cwd=str(REPO), capture_output=True)
        if r.returncode == 0:
            payload = r.stdout
        out = {"storage": "lfs", "sha256": oid,
               "declared_size": declared_size,
               "payload_verified": False}
        if payload is not None:
            if payload == raw:
                # No LFS smudge filter in this checkout (e.g. a CI runner
                # without git-lfs). The pointer's OID can still be checked
                # against the canonical hash; the payload simply cannot be
                # re-hashed here. Report that honestly instead of failing
                # a correct repository.
                out["payload_verified"] = None
                out["payload_note"] = ("LFS smudge unavailable in this "
                                       "checkout; OID checked, payload "
                                       "not re-hashed")
            else:
                actual = hashlib.sha256(payload).hexdigest()
                out["payload_sha256"] = actual
                out["payload_size"] = len(payload)
                out["payload_verified"] = (actual == oid
                                           and len(payload) == declared_size)
        return out
    return {"storage": "blob", "sha256": hashlib.sha256(raw).hexdigest(),
            "declared_size": len(raw), "payload_verified": True}


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

    # The COMMIT OBJECT is authoritative, not the working tree. Hashing the
    # current file would let a later edit be attributed to an earlier
    # artifact commit: create commit A, change the AAB afterwards, rebuild
    # metadata around the new bytes, keep naming A, and a tree-hashing
    # verifier still passes.
    canonical: dict[str, str] = {}
    objects: dict[str, dict] = {}
    tracked = sorted(git("ls-tree", "--name-only", args.artifact,
                         f"{rel}/").splitlines())
    tracked_names = {Path(t).name for t in tracked}
    # The CANONICAL SET is defined by the artifact commit, not by whatever
    # happens to be on disk. The working tree is then required to match it.
    committed_arts = sorted(n for n in tracked_names
                            if n.endswith((".aab", ".apk")))
    on_disk = sorted({p.name for p in cand.glob("*.aab")}
                     | {p.name for p in cand.glob("*.apk")})

    for name in committed_arts:
        ident = object_identity(args.artifact, f"{rel}/{name}")
        if ident is None:
            err(f"consumer_artifact_commit does not contain {name}")
            continue
        objects[name] = ident
        canonical[name] = ident["sha256"]
        if ident["storage"] == "lfs" and ident["payload_verified"] is False:
            err(f"{name}: LFS pointer at the artifact commit declares oid "
                f"{ident['sha256'][:12]}… but its payload hashes to "
                f"{ident.get('payload_sha256', 'unavailable')[:12]}… "
                f"(or the size disagrees)")
        # the file on disk NOW must equal the object at that commit
        disk = cand / name
        if not disk.exists():
            err(f"{name}: named at the artifact commit but absent from the "
                f"candidate directory")
        else:
            live = sha256_file(disk)
            if live != ident["sha256"]:
                err(f"{name}: current bytes {live[:12]}… differ from the "
                    f"object stored at consumer_artifact_commit "
                    f"{ident['sha256'][:12]}… — the artifact changed after "
                    f"the commit it is attributed to")

    # exactly the canonical set, no unexpected replacement carrying the
    # same role
    uncommitted = sorted(set(on_disk) - set(committed_arts))
    absent = sorted(set(committed_arts) - set(on_disk))
    if uncommitted:
        err(f"candidate directory holds artifact(s) {uncommitted} that are "
            f"NOT in the artifact commit — an unexpected replacement "
            f"carrying the same role")
    if absent:
        err(f"artifact commit names {absent} but the candidate directory "
            f"is missing them")
    n_aab = sum(1 for n in committed_arts if n.endswith(".aab"))
    n_apk = sum(1 for n in committed_arts if n.endswith(".apk"))
    if n_aab != 1 or n_apk != 1:
        err(f"artifact commit must contain exactly one .aab and one .apk, "
            f"found {n_aab} and {n_apk}")

    v_ident = object_identity(args.artifact, f"{rel}/VERIFY.json")
    if v_ident is None:
        err("consumer_artifact_commit does not contain VERIFY.json")
    elif (cand / "VERIFY.json").exists():
        if sha256_file(cand / "VERIFY.json") != v_ident["sha256"]:
            err("VERIFY.json changed after the artifact commit it is "
                "attributed to")
    if not issues:
        ok(f"artifact commit holds exactly the canonical set; every byte "
           f"matches the committed object")
    result["canonical_artifacts"] = canonical
    result["artifact_objects"] = objects

    # ---- metadata: the COMMITTED blobs are authoritative ------------------
    # Existence is not enough. Each record is read from the resolved
    # metadata commit, parsed, and required to equal the current file —
    # otherwise later or dirty metadata could be attributed to an earlier
    # metadata commit.
    meta_objects: dict[str, dict] = {}
    for name in ("CANDIDATE.json", "READINESS.json", "LINEAGE.json",
                 "PROVENANCE.json"):
        raw = blob_bytes(args.metadata, f"{rel}/{name}")
        if raw is None:
            err(f"candidate_metadata_commit does not contain {name}")
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            err(f"{name} at the metadata commit is not valid JSON ({e})")
            continue
        h = hashlib.sha256(raw).hexdigest()
        meta_objects[name] = {"sha256": h, "keys": len(parsed)}
        disk = cand / name
        if not disk.exists():
            err(f"{name}: present at the metadata commit but absent from "
                f"the candidate directory")
        elif sha256_file(disk) != h:
            err(f"{name}: current bytes differ from the blob at the "
                f"resolved metadata commit — later or dirty metadata "
                f"cannot be attributed to an earlier commit")
        # the record must be about THIS candidate
        ver = parsed.get("candidate_version")
        if ver is not None and ver != args.version:
            err(f"{name} at the metadata commit declares version {ver!r}, "
                f"not {args.version!r}")
    if not any(k in i for i in issues
               for k in ("metadata commit", "metadata_commit")):
        ok(f"metadata commit holds {len(meta_objects)} parsed records, all "
           f"byte-identical to the working tree")
    result["metadata_objects"] = meta_objects

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
