"""Deliberate-failure fixtures for the device-matrix harness.

The harness automates rows that were previously executed by hand. That is
only an improvement if it cannot quietly report success — a tool that says
PASS when the packaged bytes are wrong is worse than no tool, because it
launders a bad result through an authoritative-looking document.

These tests therefore attack it in the two directions that matter:

  1. it must catch a WARBIRD-class substitution — a resource with the right
     NAME and the wrong BYTES, which is the exact regression the Phase-2
     device session caught by accident and Phase-3 hardened against;
  2. it must never score an owner row, because a matrix that scores its own
     subjective rows is a matrix nobody looked at.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import device_matrix as dm  # noqa: E402

CAND = REPO / "releases/aurelius/candidates/2.0.0-rc2"
INVENTORY = REPO / "watchfaces/aurelius/visual/inventories/inventory.json"


def candidate_apk() -> Path:
    apks = sorted(CAND.glob("*.apk"))
    return apks[0] if apks else None


class BoxParsingTests(unittest.TestCase):
    def test_boxes_come_from_the_contract_not_hard_coding(self):
        boxes = dm.parse_boxes(REPO / "watchfaces/aurelius/engine/face.toml")
        self.assertIn("z21_bal", boxes)
        # must agree with the box balance_frequency.py measures
        self.assertEqual(boxes["z21_bal"], (194, 316, 92, 92))
        self.assertIn("z10_gl", boxes)
        self.assertIn("z22_cage", boxes)

    def test_a_missing_contract_yields_no_boxes_rather_than_raising(self):
        self.assertEqual(dm.parse_boxes(Path("/nonexistent/face.toml")), {})


class ResourceLineageTests(unittest.TestCase):
    """The row that would have caught the Phase-2 asset divergence."""

    @classmethod
    def setUpClass(cls):
        if candidate_apk() is None:
            raise unittest.SkipTest("no rc2 candidate APK to exercise")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def lineage(self, apk: Path) -> dm.Matrix:
        m = dm.Matrix()
        dm.row_resource_lineage(m, apk, INVENTORY)
        return m

    def result(self, m: dm.Matrix) -> str:
        return m.rows[-1][1]

    # -- positive control ------------------------------------------------

    def test_the_real_candidate_passes(self):
        m = self.lineage(candidate_apk())
        self.assertEqual(self.result(m), "PASS", m.rows)
        d = m.data["resource_lineage"]
        self.assertEqual(d["drift"], [])
        self.assertEqual(d["total"], 60)
        # independently reproduces the hand-derived device result
        self.assertEqual(d["identical"], 58)
        self.assertEqual(d["compiled"], 2)

    # -- 1. WARBIRD-class substitution: right name, wrong bytes ----------

    def test_same_name_wrong_bytes_is_caught(self):
        src = candidate_apk()
        tampered = self.tmp / "tampered.apk"
        with zipfile.ZipFile(src) as zin, \
                zipfile.ZipFile(tampered, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.endswith("balance.png"):
                    data = data + b"\x00tampered"
                zout.writestr(item, data)
        m = self.lineage(tampered)
        self.assertEqual(self.result(m), "FAIL", m.rows)
        self.assertTrue(any("balance" in d
                            for d in m.data["resource_lineage"]["drift"]))

    # -- 2. the file that defines every pixel must be verbatim -----------

    def test_a_mutated_raw_watchface_xml_is_caught(self):
        src = candidate_apk()
        tampered = self.tmp / "rawxml.apk"
        with zipfile.ZipFile(src) as zin, \
                zipfile.ZipFile(tampered, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "res/raw/watchface.xml":
                    data = data.replace(b"<WatchFace", b"<WatchFace ")
                zout.writestr(item, data)
        m = self.lineage(tampered)
        self.assertEqual(self.result(m), "FAIL", m.rows)

    # -- 3. a dropped resource is absent, not silently ignored -----------

    def test_a_missing_resource_is_reported_absent(self):
        src = candidate_apk()
        stripped = self.tmp / "stripped.apk"
        with zipfile.ZipFile(src) as zin, \
                zipfile.ZipFile(stripped, "w") as zout:
            for item in zin.infolist():
                if item.filename.endswith("cage.png"):
                    continue
                zout.writestr(item, zin.read(item.filename))
        m = self.lineage(stripped)
        self.assertEqual(self.result(m), "FAIL", m.rows)
        self.assertIn("cage", m.data["resource_lineage"]["absent"])

    # -- 4. an unreadable input is BLOCKED, never PASS -------------------

    def test_a_missing_apk_is_blocked_not_passed(self):
        m = self.lineage(self.tmp / "does-not-exist.apk")
        self.assertEqual(self.result(m), "BLOCKED", m.rows)

    def test_an_unreadable_inventory_is_blocked_not_passed(self):
        bad = self.tmp / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        m = dm.Matrix()
        dm.row_resource_lineage(m, candidate_apk(), bad)
        self.assertEqual(m.rows[-1][1], "BLOCKED", m.rows)


class OwnerRowTests(unittest.TestCase):
    """A matrix that scores its own subjective rows is a matrix nobody read."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_every_owner_row_is_emitted_pending_and_never_passed(self):
        m = dm.Matrix()
        m.add("something measured", "PASS", "detail")
        out_dir = REPO / "docs/reports/evidence/phase-4/aurelius/rc2/matrix"
        dest = self.tmp / "DEVICE_TEST_RESULTS.md"
        dm.emit(m, dest, "aurelius", "2.0.0-rc2", "a" * 64, out_dir)
        text = dest.read_text(encoding="utf-8")
        for check, _ in dm.OWNER_ROWS:
            self.assertIn(check, text)
        # each owner row carries a PENDING marker, and there are as many
        # PENDING rows as there are owner rows
        self.assertEqual(text.count("**PENDING — owner**"), len(dm.OWNER_ROWS))

    def test_the_document_is_bound_to_the_device_derived_hash(self):
        m = dm.Matrix()
        dest = self.tmp / "DEVICE_TEST_RESULTS.md"
        dm.emit(m, dest, "aurelius", "2.0.0-rc2", "b" * 64, self.tmp)
        # the readiness checker requires the APK hash to appear verbatim
        self.assertIn("b" * 64, dest.read_text(encoding="utf-8"))

    def test_the_subjective_rows_include_the_two_outstanding_hr_recordings(self):
        names = [c for c, _ in dm.OWNER_ROWS]
        self.assertTrue(any("exertion" in n for n in names))
        self.assertTrue(any("off-wrist" in n for n in names))

    def test_the_document_says_it_does_not_move_a_gate(self):
        m = dm.Matrix()
        dest = self.tmp / "DEVICE_TEST_RESULTS.md"
        dm.emit(m, dest, "aurelius", "2.0.0-rc2", "c" * 64, self.tmp)
        self.assertIn("does not move any gate",
                      dest.read_text(encoding="utf-8").lower())


class HeartRateRowTests(unittest.TestCase):
    """The fallback is 70.0 bpm exactly; a reading there proves nothing."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_no_recording_is_blocked_not_passed(self):
        m = dm.Matrix()
        dm.row_heart_rate(m, self.tmp, None)
        self.assertEqual(m.rows[-1][1], "BLOCKED", m.rows)


if __name__ == "__main__":
    unittest.main()
