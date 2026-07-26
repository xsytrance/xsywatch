"""Deliberate-failure fixtures for the consumer lineage verifier.

Checkpoint B blocker 2: rc1's CANDIDATE.json attributed its artifacts to a
single `consumer_commit` that PREDATED the packaging work which produced
them. Ancestry alone would not have caught it either — 399ba12 IS an
ancestor of the artifacts. What catches it is requiring the declared
source commit to contain every build input and to rebuild to the canonical
bytes.

These tests build throwaway git repositories with deliberately wrong
lineage and require the verifier to reject each one. They do not run
Gradle; `--build` is exercised for real against the committed candidate in
the closing verification, which is recorded in LINEAGE.json.

Run: python3 -m unittest discover -s tests/engine
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools/verify_lineage.py"
LIVE = REPO / "releases/aurelius/candidates/2.0.0-rc2"

FACE = "aurelius"
VERSION = "2.0.0-rc2"


def run(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                       text=True)
    if r.returncode:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


class LineageRejectionTests(unittest.TestCase):
    """A scratch repository whose shape mirrors the real one."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        run(self.root, "init", "-q", "-b", "main")
        run(self.root, "config", "user.email", "t@example.com")
        run(self.root, "config", "user.name", "t")
        (self.root / "tools").mkdir()
        shutil.copy(TOOL, self.root / "tools")
        for extra in ("build_candidate.sh", "dex_guard.py",
                      "verify_candidate.py"):
            (self.root / "tools" / extra).write_text("#\n")

        f = self.root / f"watchfaces/{FACE}"
        (f / "engine").mkdir(parents=True)
        (f / "app/src/main/res/raw").mkdir(parents=True)
        (f / "gradle/wrapper").mkdir(parents=True)
        (f / "engine/face.toml").write_text("x\n")
        (f / "engine/handoff.json").write_text("{}\n")
        (f / "app/build.gradle.kts").write_text(
            f'versionName = "{VERSION}"\n')
        (f / "build.gradle.kts").write_text("x\n")
        (f / "settings.gradle.kts").write_text("x\n")
        (f / "gradlew").write_text("x\n")
        (f / "gradle/wrapper/gradle-wrapper.properties").write_text("x\n")
        (f / "gradle/wrapper/gradle-wrapper.jar").write_text("x\n")
        (f / "app/src/main/AndroidManifest.xml").write_text("<manifest/>\n")
        (f / "app/src/main/res/raw/watchface.xml").write_text("<w/>\n")

        self.cand = self.root / f"releases/{FACE}/candidates/{VERSION}"
        self.cand.mkdir(parents=True)

        run(self.root, "add", "-A")
        run(self.root, "commit", "-qm", "source")
        self.source = run(self.root, "rev-parse", "HEAD")

        (self.cand / f"{FACE}-{VERSION}.aab").write_bytes(b"AAB")
        (self.cand / f"{FACE}-{VERSION}-debug.apk").write_bytes(b"APK")
        (self.cand / "VERIFY.json").write_text("{}\n")
        run(self.root, "add", "-A")
        run(self.root, "commit", "-qm", "artifacts")
        self.artifact = run(self.root, "rev-parse", "HEAD")

        (self.cand / "CANDIDATE.json").write_text("{}\n")
        (self.cand / "READINESS.json").write_text("{}\n")
        run(self.root, "add", "-A")
        run(self.root, "commit", "-qm", "metadata")
        self.metadata = run(self.root, "rev-parse", "HEAD")

    def verify(self, source=None, artifact=None, metadata=None):
        r = subprocess.run(
            [sys.executable, str(self.root / "tools/verify_lineage.py"),
             FACE, "--version", VERSION,
             "--source", source or self.source,
             "--artifact", artifact or self.artifact,
             "--metadata", metadata or self.metadata],
            capture_output=True, text=True, cwd=str(self.root))
        return r.returncode, r.stdout + r.stderr

    # -- positive control ------------------------------------------------

    def test_correct_lineage_verifies(self):
        rc, out = self.verify()
        self.assertEqual(rc, 0, out)

    # -- 1. a stale source commit ----------------------------------------

    def test_stale_source_commit_is_rejected(self):
        """The rc1 defect exactly.

        A LATER candidate (rc9) is built after a version bump, but its
        record names the EARLIER commit as the source. That commit is a
        genuine ancestor, so ancestry alone accepts it — what rejects it is
        that the commit does not declare the version it claims to have
        produced."""
        f = self.root / f"watchfaces/{FACE}/app/build.gradle.kts"
        f.write_text('versionName = "2.0.0-rc9"\n')
        newer_cand = self.root / f"releases/{FACE}/candidates/2.0.0-rc9"
        newer_cand.mkdir(parents=True)
        (newer_cand / f"{FACE}-2.0.0-rc9.aab").write_bytes(b"AAB9")
        (newer_cand / f"{FACE}-2.0.0-rc9-debug.apk").write_bytes(b"APK9")
        (newer_cand / "VERIFY.json").write_text("{}\n")
        run(self.root, "add", "-A")
        run(self.root, "commit", "-qm", "rc9 bump + artifacts")
        art9 = run(self.root, "rev-parse", "HEAD")
        (newer_cand / "CANDIDATE.json").write_text("{}\n")
        (newer_cand / "READINESS.json").write_text("{}\n")
        run(self.root, "add", "-A")
        run(self.root, "commit", "-qm", "rc9 metadata")
        meta9 = run(self.root, "rev-parse", "HEAD")

        r = subprocess.run(
            [sys.executable, str(self.root / "tools/verify_lineage.py"),
             FACE, "--version", "2.0.0-rc9",
             "--source", self.source,      # stale: declares rc2, not rc9
             "--artifact", art9, "--metadata", meta9],
            capture_output=True, text=True, cwd=str(self.root))
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 1, out)
        self.assertIn("does not declare versionName", out)
        self.assertIn("cannot have produced this candidate", out)

    # -- 2. the source commit is missing a build input -------------------

    def test_source_commit_missing_a_build_input_is_rejected(self):
        run(self.root, "rm", "-q", "tools/dex_guard.py")
        run(self.root, "commit", "-qm", "drop the dex guard")
        broken = run(self.root, "rev-parse", "HEAD")
        rc, out = self.verify(source=broken, artifact=broken,
                              metadata=broken)
        self.assertEqual(rc, 1)
        self.assertIn("missing 1 build input", out)
        self.assertIn("dex_guard.py", out)

    # -- 3. the artifact commit does not descend from source -------------

    def test_artifact_commit_not_descending_from_source_is_rejected(self):
        run(self.root, "checkout", "-q", "-b", "side", self.source + "^{}")
        run(self.root, "checkout", "-q", "--orphan", "unrelated")
        (self.root / "x.txt").write_text("x\n")
        run(self.root, "add", "x.txt")
        run(self.root, "commit", "-qm", "unrelated")
        orphan = run(self.root, "rev-parse", "HEAD")
        rc, out = self.verify(artifact=orphan, metadata=orphan)
        self.assertEqual(rc, 1)
        self.assertIn("does not descend from consumer_source_commit", out)

    # -- 4. the metadata commit does not descend from the artifact -------

    def test_metadata_commit_not_descending_from_artifact_is_rejected(self):
        rc, out = self.verify(metadata=self.source)
        self.assertEqual(rc, 1)
        self.assertIn("does not descend from consumer_artifact_commit", out)

    def test_metadata_commit_equal_to_artifact_is_rejected(self):
        """A metadata file cannot contain its own commit hash, so the
        roles cannot collapse into one commit."""
        rc, out = self.verify(metadata=self.artifact)
        self.assertEqual(rc, 1)
        self.assertIn("must be a LATER commit than the artifact", out)

    def test_artifact_commit_equal_to_source_is_rejected(self):
        rc, out = self.verify(artifact=self.source)
        self.assertEqual(rc, 1)
        self.assertIn("must be a LATER commit than the source", out)

    # -- 5. the artifact commit lacks the artifacts ----------------------

    def test_artifact_commit_without_the_artifacts_is_rejected(self):
        rc, out = self.verify(artifact=self.source + "")
        self.assertEqual(rc, 1)

    # -- 6. a nonexistent commit -----------------------------------------

    def test_nonexistent_commit_is_rejected(self):
        rc, out = self.verify(source="0" * 40)
        self.assertEqual(rc, 1)
        self.assertIn("does not exist", out)


class CommittedLineageTests(unittest.TestCase):
    """The committed rc2 record must carry the three roles, not the single
    stale field rc1 used."""

    def test_rc2_declares_the_three_roles(self):
        p = LIVE / "CANDIDATE.json"
        if not p.exists():
            self.skipTest("no rc2 candidate")
        d = json.loads(p.read_text())
        for k in ("consumer_source_commit", "consumer_artifact_commit",
                  "candidate_metadata_commit"):
            self.assertIn(k, d)
        self.assertNotIn("consumer_commit", d,
                         "the stale single-role field must be gone")

    def test_rc2_lineage_record_proves_a_rebuild(self):
        p = LIVE / "LINEAGE.json"
        if not p.exists():
            self.skipTest("no rc2 lineage record")
        d = json.loads(p.read_text())
        rb = d["rebuilds"]
        self.assertTrue(rb["byte_identical_across_builds"])
        self.assertTrue(rb["equals_canonical_artifacts"])
        self.assertEqual(rb["build_1"]["aab_sha256"],
                         rb["build_2"]["aab_sha256"])
        self.assertEqual(rb["build_1"]["aab_sha256"],
                         d["canonical_artifacts"][f"aurelius-{VERSION}.aab"])

    def test_rc1_remains_preserved_with_its_original_record(self):
        """The superseded candidate is evidence. Its false
        consumer_commit is deliberately NOT rewritten."""
        p = REPO / "releases/aurelius/candidates/2.0.0-rc1/CANDIDATE.json"
        if not p.exists():
            self.skipTest("rc1 not present")
        d = json.loads(p.read_text())
        self.assertIn("consumer_commit", d,
                      "rc1's original record must not be retro-fixed")
        self.assertTrue(
            (REPO / "releases/aurelius/candidates/2.0.0-rc1/SUPERSEDED.md")
            .exists(), "rc1 must be marked superseded")


if __name__ == "__main__":
    unittest.main()
