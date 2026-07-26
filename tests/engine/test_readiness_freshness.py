"""Deliberate-failure fixtures for readiness freshness enforcement.

Checkpoint B rc2 re-review, ruling 2. The original checker verified that no
gate claimed MORE than its evidence supported. It had no way to notice a
gate claiming LESS, or a `detail` string overtaken by events — which is how
READINESS sat asserting "no Galaxy Watch7 reachable" while a device session
was already committed, and still reported 0 inconsistencies.

Freshness is now machine-enforced for machine-derived facts: every
evidence-bearing gate pins a deterministic fingerprint over the sorted
repo-relative paths and SHA-256 values of its canonical evidence set, plus
the commit it was evaluated at and the checker schema that produced it.

These tests attack that in every direction the ruling names, and — equally
important — prove it does NOT fire on legitimate changes to human prose.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECKER = REPO / "tools/check_candidate_readiness.py"
LIVE = REPO / "releases/aurelius/candidates/2.0.0-rc2"

sys.path.insert(0, str(REPO / "tools"))
import check_candidate_readiness as ccr  # noqa: E402

EVIDENCE_FILES = (
    "docs/reports/PHASE_4_PERMISSION_INVESTIGATION.md",
    "docs/reports/PHASE_4_POLICY_AUDIT.md",
    "docs/reports/PHASE_4_TEST1_READINESS.md",
    "docs/reports/PHASE_4_SIGNING_PLAN.md",
    "docs/reports/PHASE_4_CHECKPOINT_B_CHATGPT_REVIEW.md",
    "docs/reports/evidence/phase-4/aurelius/rc2/DEVICE_EVIDENCE_BLOCKER.md",
    "docs/reports/evidence/phase-4/aurelius/rc2/INSTALL_AND_LINEAGE.md",
    "docs/reports/evidence/phase-4/aurelius/rc2/PERMISSION_TEST.md",
    "watchfaces/aurelius/visual/approvals/"
    "APPROVAL-0005-field-tourbillon-mk2-rc1.json",
)

RC2_DIR = "docs/reports/evidence/phase-4/aurelius/rc2"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class FreshnessTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not (LIVE / "READINESS.json").exists():
            raise unittest.SkipTest("no rc2 candidate to exercise")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        (self.root / "tools").mkdir(parents=True)
        shutil.copy(CHECKER, self.root / "tools")
        self.cand = self.root / "releases/aurelius/candidates/2.0.0-rc2"
        self.cand.parent.mkdir(parents=True)
        shutil.copytree(LIVE, self.cand)
        for rel in EVIDENCE_FILES:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            real = REPO / rel
            shutil.copy(real, p) if real.exists() else p.write_text("x\n")
        wear = REPO / "docs/reports/evidence/phase-4/aurelius/wear"
        if wear.exists():
            shutil.copytree(
                wear, self.root / "docs/reports/evidence/phase-4/aurelius/wear",
                dirs_exist_ok=True)
        self.apk = sha256(next(self.cand.glob("*.apk")))
        self.git(["init", "-q", "-b", "main"], ["add", "-A"],
                 ["commit", "-qm", "fixture"])
        self.restamp()

    # -- helpers ---------------------------------------------------------

    def git(self, *argsets):
        env = dict(os.environ)
        env.update({"GIT_AUTHOR_NAME": "f", "GIT_AUTHOR_EMAIL": "f@x.invalid",
                    "GIT_COMMITTER_NAME": "f",
                    "GIT_COMMITTER_EMAIL": "f@x.invalid"})
        for a in argsets:
            subprocess.run(["git", "-C", str(self.root), *a],
                           capture_output=True, env=env)

    def run_checker(self, *extra: str):
        r = subprocess.run(
            [sys.executable, str(self.root / "tools/check_candidate_readiness.py"),
             "aurelius", "--version", "2.0.0-rc2", *extra],
            capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def restamp(self):
        return self.run_checker("--stamp")

    def record(self) -> dict:
        return json.loads((self.cand / "READINESS.json").read_text())

    def write(self, r: dict) -> None:
        (self.cand / "READINESS.json").write_text(json.dumps(r, indent=2))

    # -- 0. valid, unchanged evidence PASSES -----------------------------

    def test_valid_unchanged_evidence_passes(self):
        """The gate must not be unfalsifiable in the other direction."""
        rc, out = self.run_checker()
        self.assertEqual(rc, 0, out)
        self.assertIn("internally honest", out)

    # -- 1. an evidence file changed after evaluation --------------------

    def test_evidence_file_changed_after_evaluation_is_rejected(self):
        p = self.root / RC2_DIR / "INSTALL_AND_LINEAGE.md"
        p.write_text(p.read_text() + "\nquietly appended\n")
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("evidence has CHANGED since evaluation", out)
        self.assertIn("installed-APK-hash-verified", out)

    # -- 2. a file ADDED under a fingerprinted directory -----------------

    def test_new_evidence_added_under_a_fingerprinted_directory(self):
        """A directory-cited gate must notice files appearing inside it."""
        r = self.record()
        before = r["states"]["owner-wear-complete"]["evidence_fingerprint"]
        d = self.root / "docs/reports/evidence/phase-4/aurelius/wear"
        (d / "sessions" / "smuggled.json").write_text('{"schema": "x"}')
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("evidence has CHANGED since evaluation", out)
        self.assertIn("owner-wear-complete", out)
        # and the fingerprint genuinely differs
        fp, _ = ccr.evidence_fingerprint(
            self.root, ["docs/reports/evidence/phase-4/aurelius/wear"])
        self.assertNotEqual(fp, before)

    # -- 3. an evidence file removed -------------------------------------

    def test_evidence_file_removed_is_rejected(self):
        (self.root / RC2_DIR / "PERMISSION_TEST.md").unlink()
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("evidence has CHANGED since evaluation", out)

    # -- 4. evaluated against another commit -----------------------------

    def test_readiness_evaluated_against_another_commit_is_rejected(self):
        r = self.record()
        r["states"]["permissions-verified"]["evaluated_at_commit"] = "b" * 40
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("not reachable from HEAD", out)
        self.assertIn("evaluated against another commit", out)

    def test_a_malformed_evaluated_at_commit_is_rejected(self):
        r = self.record()
        r["states"]["permissions-verified"]["evaluated_at_commit"] = "HEAD"
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("is not a full commit sha", out)

    # -- 5. a stale blocker detail ---------------------------------------

    def test_stale_blocker_detail_after_device_evidence_is_rejected(self):
        """The exact failure that motivated this ruling."""
        d = self.root / RC2_DIR
        (d / "DEVICE_TEST_RESULTS.md").write_text(
            f"# rc2 results\n\nInstalled APK: {self.apk}\nrows PASS\n")
        r = self.record()
        r["states"]["device-validated"].update({
            "state": "blocked",
            "detail": "no Galaxy Watch7 reachable; adb reported zero devices "
                      "throughout. The on-panel half is not done.",
            "evidence": [RC2_DIR],
        })
        self.write(r)
        self.restamp()          # fingerprint is now honest...
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)   # ...but the PROSE is not
        self.assertIn("STALE BLOCKER DETAIL", out)

    def test_a_truthful_blocked_detail_is_accepted(self):
        """Blocked is fine — asserting a disproven REASON is not."""
        r = self.record()
        r["states"]["device-validated"]["detail"] = (
            "the visual matrix has not been run; no DEVICE_TEST_RESULTS.md "
            "exists for rc2")
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 0, out)

    # -- 6. owner prose must not alter a machine-derived result ----------

    def test_owner_notes_do_not_alter_machine_derived_results(self):
        r = self.record()
        before = {k: v.get("evidence_fingerprint")
                  for k, v in r["states"].items()}
        r["states"]["device-validated"]["owner_note"] = (
            "Rod: looked at it on the wrist, felt good, still want the "
            "matrix run properly before I sign anything.")
        r["states"]["owner-pixel-approved"]["reviewer_note"] = (
            "architecture: proposed pending wear evidence")
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 0, out)
        after = {k: v.get("evidence_fingerprint")
                 for k, v in self.record()["states"].items()}
        self.assertEqual(before, after)

    def test_a_non_prose_owner_note_is_rejected(self):
        r = self.record()
        r["states"]["device-validated"]["owner_note"] = {"looks": "fine"}
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("owner_note must be prose", out)

    # -- 7. machine-derived fields are not hand-writable -----------------

    def test_hand_edited_machine_summary_is_rejected(self):
        r = self.record()
        r["states"]["permissions-verified"]["machine_summary"] = \
            "17 evidence file(s), fingerprint deadbeefcafe…"
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("machine_summary is hand-edited or stale", out)

    def test_a_wrong_checker_schema_is_rejected(self):
        r = self.record()
        r["states"]["permissions-verified"]["checker_schema"] = \
            "agenor.release-readiness-checker/1"
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("checker_schema", out)

    def test_a_fingerprint_without_evidence_is_rejected(self):
        r = self.record()
        r["states"]["publishable"]["evidence_fingerprint"] = "sha256:" + "0" * 64
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("cites no evidence", out)

    # -- determinism -----------------------------------------------------

    def test_the_fingerprint_is_deterministic_and_order_independent(self):
        a, na = ccr.evidence_fingerprint(
            self.root, [f"{RC2_DIR}/INSTALL_AND_LINEAGE.md",
                        f"{RC2_DIR}/PERMISSION_TEST.md"])
        b, nb = ccr.evidence_fingerprint(
            self.root, [f"{RC2_DIR}/PERMISSION_TEST.md",
                        f"{RC2_DIR}/INSTALL_AND_LINEAGE.md"])
        self.assertEqual(a, b)
        self.assertEqual((na, nb), (2, 2))


class CommittedRecordTests(unittest.TestCase):
    """The real repository's committed record — the true positive control.

    The scratch fixtures above re-stamp into their own history. This one
    does not: it asserts the record as committed, with the fingerprints as
    committed, against the real evidence bytes.
    """

    def test_the_committed_record_is_fresh_and_honest(self):
        r = subprocess.run(
            [sys.executable, str(CHECKER), "aurelius", "--version",
             "2.0.0-rc2"], capture_output=True, text=True, cwd=str(REPO))
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out)
        self.assertIn("internally honest", out)

    def test_every_evidence_bearing_gate_is_fingerprinted(self):
        rec = json.loads((LIVE / "READINESS.json").read_text())
        for name, entry in rec["states"].items():
            ev = entry.get("evidence") or []
            if not ev:
                continue
            self.assertIn("evidence_fingerprint", entry, name)
            self.assertIn("evaluated_at_commit", entry, name)
            self.assertEqual(entry.get("checker_schema"),
                             ccr.CHECKER_SCHEMA, name)


if __name__ == "__main__":
    unittest.main()
