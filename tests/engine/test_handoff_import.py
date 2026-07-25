"""Lineage tests for tools/import_handoff.py (Phase-3 review blocker 3).

The importer must prove that imported bytes exist at the DECLARED
`source_commit` — not merely in the studio working tree — and must be
atomic: any failure leaves the consumer resource tree and manifest
byte-identical.

Each test builds a throwaway studio Git repo (regular blobs plus a
hand-written Git-LFS pointer) and a throwaway consumer tree.
"""

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
imp = importlib.import_module("import_handoff")

FACE = "aurelius"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lfs_pointer(payload: bytes) -> bytes:
    return ("version https://git-lfs.github.com/spec/v1\n"
            f"oid sha256:{sha(payload)}\n"
            f"size {len(payload)}\n").encode()


class Studio:
    """Temp studio repo: e1 = ordinary blob, e2 = LFS-pointer export."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="studio-"))
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        (self.dir / "exports").mkdir()
        (self.dir / "scripts").mkdir()
        (self.dir / "specs").mkdir()

        self.e1_bytes = b"\x89PNG-one-payload"
        self.e2_payload = b"\x89PNG-two-payload-larger"
        (self.dir / "exports/e1.png").write_bytes(self.e1_bytes)
        (self.dir / "exports/e2.png").write_bytes(lfs_pointer(self.e2_payload))
        (self.dir / "scripts/build.py").write_text("# producer\n")
        (self.dir / "specs/SPEC.md").write_text("# spec\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "producing commit")
        self.producing = self.rev("HEAD")
        # A real git-lfs checkout smudges the pointer into payload bytes in
        # the working tree while the committed object stays a pointer.
        (self.dir / "exports/e2.png").write_bytes(self.e2_payload)

        self.meta_rel = "exports/handoff_metadata.json"
        (self.dir / self.meta_rel).write_text(json.dumps(
            self.metadata(self.producing), indent=2))
        self.git("add", "-A")
        self.git("commit", "-qm", "stamp metadata")
        self.metadata_commit = self.rev("HEAD")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.dir,
                              capture_output=True, check=False)

    def rev(self, ref):
        return subprocess.run(["git", "rev-parse", ref], cwd=self.dir,
                              capture_output=True, text=True,
                              check=True).stdout.strip()

    def entry(self, name, payload_sha, res):
        return {
            "asset_id": f"gears/Asset_{name}", "sha256": payload_sha,
            "source_paths": ["scripts/build.py"], "spec_path": "specs/SPEC.md",
            "export_type": "static-image",
            "export_file": f"exports/{name}.png", "resource_name": res,
            "dimensions": [10, 10], "color_space": "srgb",
            "alpha": "straight", "pivot": [0.5, 0.5], "frames": 1,
            "frame_seconds": None, "loop": "none", "aod_safe": True,
            "license": "original", "lifecycle": "candidate",
            "consumer_component": f"z_{res}", "regenerate": "make",
        }

    def metadata(self, commit):
        return {"face": FACE, "generation": "test", "source_commit": commit,
                "exports": [self.entry("e1", sha(self.e1_bytes), "res_one"),
                            self.entry("e2", sha(self.e2_payload),
                                       "res_two")]}

    def write_metadata(self, meta, commit_it=True, msg="update metadata"):
        (self.dir / self.meta_rel).write_text(json.dumps(meta, indent=2))
        if commit_it:
            self.git("add", "-A")
            self.git("commit", "-qm", msg)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class Consumer:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="consumer-"))
        self.res = self.dir / f"watchfaces/{FACE}/app/src/main/res/drawable-nodpi"
        self.res.mkdir(parents=True)
        (self.dir / f"watchfaces/{FACE}/engine").mkdir(parents=True)
        self.manifest = self.dir / f"watchfaces/{FACE}/engine/handoff.json"
        # pre-existing resources that must survive any failed import
        for name in ("res_one", "res_two"):
            (self.res / f"{name}.png").write_bytes(f"OLD-{name}".encode())
        self.manifest.write_text('{"contract": "old"}\n')
        self._snapshot = self.snapshot()

    def snapshot(self):
        snap = {p.name: p.read_bytes() for p in sorted(self.res.iterdir())}
        snap["__manifest__"] = self.manifest.read_bytes()
        return snap

    def unchanged(self):
        return self.snapshot() == self._snapshot

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class HandoffImportLineageTests(unittest.TestCase):

    def setUp(self):
        self.studio = Studio()
        self.consumer = Consumer()
        self.addCleanup(self.studio.close)
        self.addCleanup(self.consumer.close)
        patcher = mock.patch.object(imp, "REPO", self.consumer.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_import(self, dry=False):
        argv = ["import_handoff.py", FACE, "--studio", str(self.studio.dir),
                "--metadata", self.studio.meta_rel]
        if dry:
            argv.append("--dry-run")
        with mock.patch.object(sys, "argv", argv):
            return imp.main()

    # -- positive control ----------------------------------------------

    def test_valid_import_succeeds_and_records_both_commits(self):
        self.assertEqual(self.run_import(), 0)
        man = json.loads(self.consumer.manifest.read_text())
        self.assertEqual(man["source_commit"], self.studio.producing)
        self.assertEqual(man["metadata_commit"], self.studio.metadata_commit)
        self.assertEqual(len(man["assets"]), 2)
        self.assertEqual((self.consumer.res / "res_one.png").read_bytes(),
                         self.studio.e1_bytes)

    def test_dry_run_changes_nothing(self):
        self.assertEqual(self.run_import(dry=True), 0)
        self.assertTrue(self.consumer.unchanged())

    # -- 1. dirty working tree differing from the declared commit -------

    def test_dirty_working_tree_rejected(self):
        (self.studio.dir / "exports/e1.png").write_bytes(b"TAMPERED-LATER")
        self.assertEqual(self.run_import(), 1)
        self.assertTrue(self.consumer.unchanged(),
                        "a dirty studio checkout must not reach the consumer")

    def test_dirty_tree_with_matching_metadata_still_rejected(self):
        """The pre-review hole: metadata + working tree agree with each
        other, but the bytes are NOT in the declared commit."""
        tampered = b"TAMPERED-BUT-SELF-CONSISTENT"
        (self.studio.dir / "exports/e1.png").write_bytes(tampered)
        meta = self.studio.metadata(self.studio.producing)
        meta["exports"][0]["sha256"] = sha(tampered)
        self.studio.write_metadata(meta)
        rc = self.run_import()
        self.assertEqual(rc, 1)
        self.assertTrue(self.consumer.unchanged())

    # -- 2. metadata pointing at the wrong historical commit ------------

    def test_wrong_historical_commit_rejected(self):
        (self.studio.dir / "exports/e3.png").write_bytes(b"later-only")
        self.studio.git("add", "-A")
        self.studio.git("commit", "-qm", "later export")
        later = self.studio.rev("HEAD")
        meta = self.studio.metadata(self.studio.producing)
        meta["exports"].append(self.studio.entry("e3", sha(b"later-only"),
                                                 "res_three"))
        self.studio.write_metadata(meta)
        self.assertEqual(self.run_import(), 1)
        self.assertTrue(self.consumer.unchanged())
        # attributing to the later commit is what makes it valid
        meta["source_commit"] = later
        self.studio.write_metadata(meta)
        (self.consumer.res / "res_three.png").write_bytes(b"OLD")
        self.assertEqual(self.run_import(), 0)

    # -- 3/4. missing source_paths / spec_path at the commit ------------

    def test_missing_source_path_rejected(self):
        meta = self.studio.metadata(self.studio.producing)
        meta["exports"][0]["source_paths"] = ["scripts/does_not_exist.py"]
        self.studio.write_metadata(meta)
        self.assertEqual(self.run_import(), 1)
        self.assertTrue(self.consumer.unchanged())

    def test_missing_spec_path_rejected(self):
        meta = self.studio.metadata(self.studio.producing)
        meta["exports"][1]["spec_path"] = "specs/NOPE.md"
        self.studio.write_metadata(meta)
        self.assertEqual(self.run_import(), 1)
        self.assertTrue(self.consumer.unchanged())

    # -- 5. LFS pointer OID mismatch ------------------------------------

    def test_lfs_oid_mismatch_rejected(self):
        meta = self.studio.metadata(self.studio.producing)
        meta["exports"][1]["sha256"] = "b" * 64
        self.studio.write_metadata(meta)
        self.assertEqual(self.run_import(), 1)
        self.assertTrue(self.consumer.unchanged())

    def test_lfs_pointer_oid_is_what_gets_verified(self):
        """e2 is a pointer: its declared sha is the payload's, which never
        appears in the repo as bytes — proving pointer-aware verification."""
        committed = subprocess.run(
            ["git", "cat-file", "-p", f"{self.studio.producing}:exports/e2.png"],
            cwd=self.studio.dir, capture_output=True, check=True).stdout
        self.assertIn(b"git-lfs", committed)
        self.assertNotEqual(sha(committed), sha(self.studio.e2_payload),
                            "the committed object is a pointer, not payload")
        self.assertEqual(self.run_import(), 0)

    # -- 6. late failure leaves the consumer tree byte-identical --------

    def test_late_failure_rolls_back_completely(self):
        real_copy = shutil.copy2
        calls = {"n": 0}

        def flaky(src, dst, *a, **kw):
            # 1-2 = staging copies, 3 = first replace, 4 = fail mid-replace
            calls["n"] += 1
            if calls["n"] >= 4:
                raise OSError("simulated failure during replace")
            return real_copy(src, dst, *a, **kw)

        with mock.patch.object(imp.shutil, "copy2", side_effect=flaky):
            rc = self.run_import()
        self.assertEqual(rc, 1)
        self.assertTrue(self.consumer.unchanged(),
                        "a failure during replace must roll back every file "
                        "and leave the manifest untouched")

    def test_uncommitted_metadata_rejected(self):
        """Metadata that is not committed has no resolvable stamping
        commit, so the producing/stamping relationship cannot be proven."""
        loose = "exports/uncommitted_metadata.json"
        (self.studio.dir / loose).write_text(
            json.dumps(self.studio.metadata(self.studio.producing), indent=2))
        argv = ["import_handoff.py", FACE, "--studio", str(self.studio.dir),
                "--metadata", loose]
        with mock.patch.object(sys, "argv", argv):
            rc = imp.main()
        self.assertEqual(rc, 1)
        self.assertTrue(self.consumer.unchanged())


if __name__ == "__main__":
    unittest.main()
