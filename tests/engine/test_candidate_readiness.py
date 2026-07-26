"""Deliberate-failure fixtures for the fail-closed readiness gate.

Checkpoint B blocker 5: the candidate validator accepted evidence whenever
the referenced PATH EXISTED. An empty wear directory and a
DEVICE_EVIDENCE_BLOCKER.md both satisfied it. Path existence is not
readiness.

Every test here proves the gate REJECTS a specific way of claiming a gate
is closed when it is not.

Run: python3 -m unittest discover -s tests/engine
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECKER = REPO / "tools/check_candidate_readiness.py"
LIVE = REPO / "releases/aurelius/candidates/2.0.0-rc2"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class ReadinessGateTests(unittest.TestCase):
    """Each test copies the real candidate into a scratch repo, corrupts
    one claim, and requires the checker to catch it."""

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
        # evidence roots referenced by the record
        for rel in ("docs/reports", "docs/reports/evidence/phase-4/aurelius/wear",
                    "docs/reports/evidence/phase-4/aurelius/rc2",
                    "watchfaces/aurelius/visual/approvals"):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        for rel in ("docs/reports/PHASE_4_PERMISSION_INVESTIGATION.md",
                    "docs/reports/PHASE_4_POLICY_AUDIT.md",
                    "docs/reports/PHASE_4_TEST1_READINESS.md",
                    "docs/reports/PHASE_4_SIGNING_PLAN.md",
                    "docs/reports/PHASE_4_CHECKPOINT_B_CHATGPT_REVIEW.md",
                    "docs/reports/evidence/phase-4/aurelius/rc2/"
                    "DEVICE_EVIDENCE_BLOCKER.md",
                    "watchfaces/aurelius/visual/approvals/"
                    "APPROVAL-0005-field-tourbillon-mk2-rc1.json"):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("placeholder\n")
        self.apk = sha256(next(self.cand.glob("*.apk")))
        self.aab = sha256(next(self.cand.glob("*.aab")))

    # -- helpers ---------------------------------------------------------

    def record(self) -> dict:
        return json.loads((self.cand / "READINESS.json").read_text())

    def write(self, r: dict) -> None:
        (self.cand / "READINESS.json").write_text(json.dumps(r, indent=2))

    def run_checker(self):
        r = subprocess.run(
            [sys.executable, str(self.root / "tools/check_candidate_readiness.py"),
             "aurelius", "--version", "2.0.0-rc2"],
            capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def session(self, apk: str, contexts, **obs) -> dict:
        o = {"date": "2026-07-27", "duration_hours": 9.0,
             "contexts": contexts, "aod_readability": "legible",
             "charging_sleep_wake": "woke cleanly", "disposition": "keep"}
        o.update(obs)
        return {"schema": "agenor.wear-session/1",
                "artifact": {"apk_sha256": apk}, "observations": o}

    def add_sessions(self, sessions):
        d = self.root / "docs/reports/evidence/phase-4/aurelius/wear/sessions"
        d.mkdir(parents=True, exist_ok=True)
        for i, s in enumerate(sessions):
            (d / f"s{i}.json").write_text(json.dumps(s))
        return "docs/reports/evidence/phase-4/aurelius/wear/sessions"

    def good_device_evidence(self) -> str:
        """A directory with real results and no blocker document."""
        d = self.root / "docs/reports/evidence/phase-4/aurelius/rc2-passed"
        d.mkdir(parents=True, exist_ok=True)
        (d / "DEVICE_TEST_RESULTS.md").write_text(
            f"# rc2 device results\n\nInstalled APK sha256: {self.apk}\n"
            f"All matrix rows PASS.\n")
        return "docs/reports/evidence/phase-4/aurelius/rc2-passed"

    def claim(self, name, **kw):
        r = self.record()
        r["states"][name].update({"state": "complete",
                                  "artifact_sha256": self.apk, **kw})
        self.write(r)
        return r

    # -- positive control ------------------------------------------------

    def test_the_committed_record_is_honest(self):
        rc, out = self.run_checker()
        self.assertEqual(rc, 0, out)
        self.assertIn("internally honest", out)

    # -- 1. an empty wear directory is not wear evidence -----------------

    def test_empty_wear_directory_is_rejected(self):
        d = self.root / "docs/reports/evidence/phase-4/aurelius/wear/sessions"
        d.mkdir(parents=True, exist_ok=True)
        self.claim("owner-wear-complete", detail="claimed",
                   evidence=["docs/reports/evidence/phase-4/aurelius/wear/"
                             "sessions"])
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("empty directory is not evidence", out)

    # -- 2. a blocker document is not device validation ------------------

    def test_blocker_document_is_not_device_validation(self):
        self.claim("device-validated", detail="claimed",
                   evidence=["docs/reports/evidence/phase-4/aurelius/rc2"])
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("blocker document", out)

    # -- 3. a session for the wrong APK is invalid -----------------------

    def test_wear_session_bound_to_the_wrong_apk_is_rejected(self):
        ev = self.add_sessions([
            self.session("0" * 64, ["office", "home", "outdoor", "low-light"])])
        r = self.record()
        r["states"]["device-validated"]["state"] = "complete"
        r["states"]["device-validated"]["artifact_sha256"] = self.apk
        r["states"]["device-validated"]["evidence"] = [
            self.good_device_evidence()]
        r["states"]["owner-wear-complete"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": [ev], "detail": "claimed"})
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("bound to a different APK", out)

    # -- 4. incomplete environmental coverage is invalid -----------------

    def test_incomplete_wear_context_coverage_is_rejected(self):
        ev = self.add_sessions([self.session(self.apk, ["office"])])
        r = self.record()
        r["states"]["device-validated"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": [self.good_device_evidence()],
             "detail": "claimed"})
        r["states"]["owner-wear-complete"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": [ev], "detail": "claimed"})
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("context coverage incomplete", out)

    # -- 5. a mismatched installed-APK hash is rejected ------------------

    def test_mismatched_installed_apk_hash_is_rejected(self):
        r = self.record()
        r["states"]["device-validated"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": [self.good_device_evidence()],
             "detail": "claimed"})
        r["states"]["installed-APK-hash-verified"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": ["docs/reports"], "value": "f" * 64,
             "detail": "claimed"})
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("!= the candidate artifact", out)

    # -- 6. publishable may not open before its predecessors -------------

    def test_publishable_cannot_open_early(self):
        self.claim("publishable", detail="claimed",
                   evidence=["docs/reports"])
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("interlock that must never open early", out)

    # -- 7. a gate cannot close before its prerequisite -------------------

    def test_gate_cannot_close_before_its_prerequisite(self):
        self.claim("owner-pixel-approved", detail="claimed",
                   evidence=["docs/reports"])
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("prerequisite owner-wear-complete", out)

    # -- 8. a complete gate must reference this candidate's artifact -----

    def test_complete_state_must_reference_the_candidate_artifact(self):
        r = self.record()
        r["states"]["dex-gate-passed"]["artifact_sha256"] = "a" * 64
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("does not reference this", out)

    # -- 9. a complete gate must reference evidence that exists ----------

    def test_complete_state_with_a_missing_evidence_path_is_rejected(self):
        r = self.record()
        r["states"]["dex-gate-passed"]["evidence"] = ["docs/nope/absent.json"]
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("evidence path does not exist", out)

    # -- 10. artifact hash drift is caught -------------------------------

    def test_readiness_bound_to_the_wrong_artifact_is_rejected(self):
        r = self.record()
        r["artifact"]["apk_sha256"] = "b" * 64
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("does not match the committed APK", out)

    # -- 11. an unknown state value is rejected --------------------------

    def test_unknown_state_value_is_rejected(self):
        r = self.record()
        r["states"]["policy-ready"]["state"] = "probably-fine"
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("is not one of", out)

    # -- 12. publication status must stay honest -------------------------

    def test_published_status_on_an_unapproved_candidate_is_rejected(self):
        r = self.record()
        r["publication_status"] = "published"
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("must be 'not published'", out)

    # -- 13. a missing required state is rejected ------------------------

    def test_missing_required_state_is_rejected(self):
        r = self.record()
        del r["states"]["signing-authorized"]
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("missing required state", out)

    # -- 14. a fully-satisfied wear claim is ACCEPTED --------------------

    def test_a_genuinely_complete_wear_claim_is_accepted(self):
        """The gate must not be unfalsifiable in the other direction: real
        evidence covering every required context, bound to this APK, must
        pass."""
        ev = self.add_sessions([
            self.session(self.apk, ["office", "home"]),
            self.session(self.apk, ["outdoor", "low-light"]),
        ])
        r = self.record()
        r["states"]["device-validated"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": [self.good_device_evidence()], "detail": "real"})
        r["states"]["owner-wear-complete"].update(
            {"state": "complete", "artifact_sha256": self.apk,
             "evidence": [ev], "detail": "real"})
        self.write(r)
        rc, out = self.run_checker()
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()


class ProvenanceConsistencyTests(ReadinessGateTests):
    """Blocker 3: CANDIDATE.json recorded the AI-model licence position as
    an unresolved owner action while PROVENANCE.json concluded the
    repository-wide warning is not applicable. A manifest cannot state
    both."""

    def prov(self) -> dict:
        return json.loads((self.cand / "PROVENANCE.json").read_text())

    def write_prov(self, d: dict) -> None:
        (self.cand / "PROVENANCE.json").write_text(json.dumps(d, indent=2))

    def cnd(self) -> dict:
        return json.loads((self.cand / "CANDIDATE.json").read_text())

    def write_cnd(self, d: dict) -> None:
        (self.cand / "CANDIDATE.json").write_text(json.dumps(d, indent=2))

    def rebind(self) -> None:
        """Keep the candidate's provenance hash binding truthful."""
        d = self.cnd()
        d["provenance_sha256"] = sha256(self.cand / "PROVENANCE.json")
        self.write_cnd(d)

    # -- positive control ------------------------------------------------

    def test_agreeing_records_pass(self):
        rc, out = self.run_checker()
        self.assertEqual(rc, 0, out)

    # -- 1. candidate says unresolved, provenance says not applicable ----

    def test_candidate_unresolved_while_provenance_clean_is_rejected(self):
        d = self.cnd()
        d.setdefault("licensing_provenance", {})["open_owner_action"] = (
            "AI-model licence position for commercial sale of generated "
            "artwork remains unresolved (docs/LICENSING.md)")
        self.write_cnd(d)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("cannot state both", out)

    # -- 2. candidate says closed while provenance is unresolved ---------

    def test_candidate_closed_while_provenance_unresolved_is_rejected(self):
        p = self.prov()
        p["assets_with_ai_checkpoint_pixels"] = ["plates/AureliusMk2_PlateNormal"]
        p["repository_wide_warning"]["status"] = "APPLIES to this candidate"
        self.write_prov(p)
        self.rebind()
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("claims candidate provenance is closed", out)

    def test_donor_pixels_also_block_a_closed_claim(self):
        p = self.prov()
        p["assets_with_donor_image_pixels"] = ["plates/AureliusMk2_PlateAOD"]
        p["repository_wide_warning"]["status"] = "APPLIES to this candidate"
        self.write_prov(p)
        self.rebind()
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("claims candidate provenance is closed", out)

    # -- 3. mismatched provenance hash -----------------------------------

    def test_mismatched_provenance_hash_is_rejected(self):
        d = self.cnd()
        d["provenance_sha256"] = "c" * 64
        self.write_cnd(d)
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("binds provenance", out)

    # -- 4. provenance for a different candidate version -----------------

    def test_provenance_for_another_version_is_rejected(self):
        p = self.prov()
        p["candidate_version"] = "9.9.9"
        self.write_prov(p)
        self.rebind()
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("PROVENANCE.json is for", out)

    # -- 5. missing provenance record ------------------------------------

    def test_missing_provenance_record_is_rejected(self):
        (self.cand / "PROVENANCE.json").unlink()
        rc, out = self.run_checker()
        self.assertEqual(rc, 1)
        self.assertIn("no PROVENANCE.json", out)

    # -- the repository-wide warning must not be deleted -----------------

    def test_repository_wide_warning_is_preserved_not_deleted(self):
        """Scoping the legacy warning must not remove it."""
        lic = REPO / "docs/LICENSING.md"
        self.assertTrue(lic.exists(),
                        "docs/LICENSING.md must not be deleted")
        p = json.loads((LIVE / "PROVENANCE.json").read_text())
        w = p["repository_wide_warning"]
        self.assertEqual(w["source"], "docs/LICENSING.md")
        self.assertIn("NOT APPLICABLE", w["status"].upper())
        self.assertIn("not deleted or weakened", w["scope_note"].lower()
                      .replace("is not", "not"))
