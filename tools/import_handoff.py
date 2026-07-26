#!/usr/bin/env python3
"""Gated studio-asset import (Phase 3, ADR-009 §6 + ASSET_HANDOFF_CONTRACT).

Lineage guarantee (Phase-3 review blocker 3): every export is verified
against the **exact Git snapshot** named by `source_commit` — not against
the studio working tree. A dirty checkout, an amended export, or metadata
attributed to the wrong historical commit are all rejected.

Per export, at `<source_commit>`:
  * `<commit>:<export_path>` must exist;
    - Git-LFS pointer  -> its `oid sha256:<hex>` must equal the handoff sha256
    - ordinary blob    -> sha256 of the blob bytes must equal it
  * every `source_paths` entry must exist at that commit;
  * `spec_path` must exist at that commit.

Commit roles are explicit and machine-checked:
  * **producing commit** (`source_commit`) — contains the export bytes and
    the producing sources; this is what the manifest attributes assets to.
  * **metadata commit** — where the studio's `handoff_metadata.json`
    itself lives. A metadata file cannot contain its own commit hash, so
    it is necessarily stamped in a later commit; the importer resolves it
    with `git log -1 -- <metadata>` and requires the producing commit to
    be an ancestor of (or identical to) it.

The import is two-phase and fail-safe: the whole set is verified, staged
in a temporary directory, and re-verified there; consumer resources and
the manifest are replaced only after every entry passes. Any failure —
including one in the final replace phase — leaves the consumer resource
tree and manifest byte-identical to how they started.

Usage:
  import_handoff.py aurelius --studio ~/AGENOR-Horology \
      --metadata exports/aurelius_mk2/handoff_metadata.json [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LFS_OID_RE = re.compile(r"^oid sha256:([0-9a-f]{64})\s*$", re.M)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(studio: Path, *args: str, binary: bool = False):
    """Run git in the studio repo; returns (ok, stdout)."""
    r = subprocess.run(["git", *args], cwd=studio, capture_output=True)
    if r.returncode != 0:
        return False, r.stderr.decode(errors="replace").strip()
    return True, (r.stdout if binary else
                  r.stdout.decode(errors="replace").strip())


def object_exists(studio: Path, commit: str, path: str) -> bool:
    ok, _ = git(studio, "cat-file", "-e", f"{commit}:{path}")
    return ok


def content_sha_at_commit(studio: Path, commit: str,
                          path: str) -> tuple[str | None, str, str]:
    """Return (sha256, kind, detail) for <commit>:<path>.

    kind is 'lfs' (pointer OID) or 'blob' (hash of the stored bytes).
    """
    ok, raw = git(studio, "cat-file", "-p", f"{commit}:{path}", binary=True)
    if not ok:
        return None, "missing", str(raw)
    if raw[:80].startswith(b"version https://git-lfs.github.com/spec/v1"):
        m = LFS_OID_RE.search(raw.decode(errors="replace"))
        if not m:
            return None, "lfs", "LFS pointer without a sha256 oid"
        return m.group(1), "lfs", "pointer oid"
    return sha256_bytes(raw), "blob", "blob content"


def resolve_metadata_commit(studio: Path, metadata_rel: str) -> str | None:
    ok, out = git(studio, "log", "-1", "--format=%H", "--", metadata_rel)
    return out if ok and out else None


def is_ancestor(studio: Path, older: str, newer: str) -> bool:
    if older == newer:
        return True
    ok, _ = git(studio, "merge-base", "--is-ancestor", older, newer)
    return ok


def verify_entry(studio: Path, exp: dict, commit: str) -> list[str]:
    """All lineage checks for one export. Returns a list of problems."""
    problems: list[str] = []
    aid = exp.get("asset_id", "<no asset_id>")
    export_path = exp.get("export_file")
    declared = exp.get("sha256")

    if not export_path or not declared:
        return [f"{aid}: metadata missing export_file/sha256"]

    actual, kind, detail = content_sha_at_commit(studio, commit, export_path)
    if actual is None:
        problems.append(f"{aid}: {export_path} does not exist at "
                        f"{commit[:12]} ({kind}: {detail})")
    elif actual != declared:
        problems.append(
            f"{aid}: {export_path} at {commit[:12]} has {kind} sha256 "
            f"{actual[:12]}… but the handoff declares {declared[:12]}… "
            f"(the declared commit does not contain these bytes)")

    for sp in exp.get("source_paths") or []:
        if not object_exists(studio, commit, sp):
            problems.append(f"{aid}: source path {sp} does not exist at "
                            f"{commit[:12]}")
    spec = exp.get("spec_path")
    if spec and not object_exists(studio, commit, spec):
        problems.append(f"{aid}: spec_path {spec} does not exist at "
                        f"{commit[:12]}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("face")
    ap.add_argument("--studio", type=Path, required=True)
    ap.add_argument("--metadata", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    studio = a.studio.expanduser().resolve()
    metadata_rel = str(a.metadata)
    meta_path = studio / metadata_rel
    if not meta_path.exists():
        print(f"FAIL: metadata not found: {meta_path}")
        return 1

    # --- the COMMITTED metadata blob is authoritative -------------------
    # Resolving metadata_commit and then parsing working-tree bytes would
    # let an uncommitted edit (license, lifecycle, pivot, dimensions,
    # component, regenerate, or the export set itself) enter the manifest
    # while still being attributed to the older commit. The blob at
    # metadata_commit is parsed instead, and any working-tree divergence
    # is rejected outright.
    metadata_commit = resolve_metadata_commit(studio, metadata_rel)
    if metadata_commit is None:
        print(f"FAIL: {metadata_rel} is not committed in {studio}; its "
              f"stamping commit cannot be resolved")
        return 1
    ok, committed_blob = git(studio, "cat-file", "-p",
                             f"{metadata_commit}:{metadata_rel}", binary=True)
    if not ok:
        print(f"FAIL: cannot read {metadata_rel} at "
              f"{metadata_commit[:12]}: {committed_blob}")
        return 1
    worktree_blob = meta_path.read_bytes()
    if worktree_blob != committed_blob:
        print(f"FAIL: working-tree {metadata_rel} differs from the blob at "
              f"its stamping commit {metadata_commit[:12]} — uncommitted "
              f"metadata edits cannot be imported (commit them, which "
              f"moves metadata_commit, or restore the file)")
        return 1
    try:
        meta = json.loads(committed_blob.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"FAIL: committed metadata blob is not valid JSON: {e}")
        return 1
    face_dir = REPO / "watchfaces" / a.face
    res_dir = face_dir / "app/src/main/res/drawable-nodpi"
    handoff_path = face_dir / "engine/handoff.json"

    commit = meta.get("source_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        print(f"FAIL: metadata source_commit {commit!r} is not a full SHA")
        return 1
    ok, kind = git(studio, "cat-file", "-t", commit)
    if not ok or kind != "commit":
        print(f"FAIL: producing commit {commit[:12]} not found in {studio}")
        return 1

    # --- commit-role resolution ---------------------------------------
    if not is_ancestor(studio, commit, metadata_commit):
        print(f"FAIL: producing commit {commit[:12]} is not an ancestor of "
              f"the metadata stamping commit {metadata_commit[:12]} — the "
              f"metadata cannot describe exports from that commit")
        return 1
    print(f"producing commit : {commit}")
    print(f"metadata commit  : {metadata_commit}"
          f"{' (same)' if metadata_commit == commit else ''}")

    # --- phase 1: verify EVERY entry against the commit snapshot -------
    exports = meta.get("exports", [])
    problems: list[str] = []
    for exp in exports:
        problems.extend(verify_entry(studio, exp, commit))
    if problems:
        print(f"\nFAIL: {len(problems)} lineage problem(s); nothing imported:")
        for p in problems[:40]:
            print(f"  - {p}")
        if len(problems) > 40:
            print(f"  … and {len(problems) - 40} more")
        return 1
    print(f"verified {len(exports)} exports against {commit[:12]} "
          f"(git object snapshot, LFS-aware)")

    if a.dry_run:
        print("dry run: no files staged or replaced")
        return 0

    # --- phase 2: stage, re-verify staged bytes ------------------------
    entries = []
    with tempfile.TemporaryDirectory(prefix="handoff-stage-") as td:
        stage = Path(td)
        staged: list[tuple[Path, Path]] = []
        for exp in exports:
            # The working tree is consulted ONLY to obtain LFS-smudged
            # payload bytes, and only after the committed object's OID has
            # already been verified above; the bytes must still hash to
            # that verified value.
            src = studio / exp["export_file"]
            if not src.exists():
                print(f"FAIL: working-tree export missing (LFS not pulled?): "
                      f"{src}")
                return 1
            if sha256_file(src) != exp["sha256"]:
                print(f"FAIL: working-tree bytes for {exp['asset_id']} differ "
                      f"from the verified commit snapshot — refusing to "
                      f"import a dirty checkout")
                return 1
            dest = res_dir / f"{exp['resource_name']}.png"
            tmp = stage / f"{exp['resource_name']}.png"
            shutil.copy2(src, tmp)
            if sha256_file(tmp) != exp["sha256"]:
                print(f"FAIL: staged copy of {exp['asset_id']} is corrupt")
                return 1
            staged.append((tmp, dest))
            entries.append({
                "asset_id": exp["asset_id"],
                "source_repo": "xsytrance/AGENOR-Horology",
                "source_commit": commit,
                "source_paths": exp["source_paths"],
                "spec_path": exp["spec_path"],
                "export_type": exp["export_type"],
                "destination": str(dest.relative_to(REPO)),
                "dimensions": exp["dimensions"],
                "color_space": exp["color_space"],
                "alpha": exp["alpha"],
                "pivot": exp["pivot"],
                "frames": exp["frames"],
                "frame_seconds": exp["frame_seconds"],
                "loop": exp["loop"],
                "aod_safe": exp["aod_safe"],
                "license": exp["license"],
                "sha256": exp["sha256"],
                "lifecycle": exp["lifecycle"],
                "consumer_component": exp["consumer_component"],
                "regenerate": exp["regenerate"],
            })

        # --- phase 3: atomic replace with rollback --------------------
        # Originals are snapshotted in memory and restored with plain
        # writes, so rollback cannot depend on the same copy machinery
        # that just failed.
        originals: dict[Path, bytes | None] = {
            dest: (dest.read_bytes() if dest.exists() else None)
            for _tmp, dest in staged}
        original_manifest = (handoff_path.read_bytes()
                             if handoff_path.exists() else None)
        try:
            for tmp, dest in staged:
                shutil.copy2(tmp, dest)
            handoff = {
                "contract": "docs/ASSET_HANDOFF_CONTRACT.md",
                "generation": meta.get("generation"),
                "source_commit": commit,
                "metadata_commit": metadata_commit,
                "assets": entries,
            }
            handoff_path.write_text(
                json.dumps(handoff, indent=2, sort_keys=False) + "\n",
                encoding="utf-8")
        except Exception as e:
            for dest, data in originals.items():
                if data is None:
                    dest.unlink(missing_ok=True)
                else:
                    dest.write_bytes(data)
            if original_manifest is not None:
                handoff_path.write_bytes(original_manifest)
            else:
                handoff_path.unlink(missing_ok=True)
            print(f"FAIL: import aborted; consumer tree rolled back ({e})")
            return 1

    print(f"imported {len(entries)} exports -> {res_dir}")
    print(f"wrote {handoff_path} (producing commit {commit[:12]}, "
          f"metadata commit {metadata_commit[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
