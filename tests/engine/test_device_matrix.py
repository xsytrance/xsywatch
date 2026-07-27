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
import re
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


FACE_TOML = REPO / "watchfaces/aurelius/engine/face.toml"


class BoxParsingTests(unittest.TestCase):
    def test_boxes_come_from_the_contract_not_hard_coding(self):
        boxes = dm.parse_boxes(FACE_TOML)
        self.assertIn("z21_bal", boxes)
        # must agree with the box balance_frequency.py measures
        self.assertEqual(boxes["z21_bal"], (194, 316, 92, 92))
        self.assertIn("z10_gl", boxes)
        self.assertIn("z22_cage", boxes)

    def test_a_missing_contract_yields_no_boxes_rather_than_raising(self):
        self.assertEqual(dm.parse_boxes(Path("/nonexistent/face.toml")), {})

    def test_components_carry_type_and_declared_speed(self):
        comps = {c["name"]: c for c in dm.parse_components(FACE_TOML)
                 if c.get("name")}
        self.assertEqual(comps["z10_gl"]["type"], "rotating_image")
        self.assertEqual(comps["z10_gl"]["speed"], 40)
        self.assertEqual(comps["z11_gr"]["speed"], 24)
        self.assertTrue(comps["z11_gr"].get("reverse"))
        self.assertEqual(comps["z21_bal"]["type"], "hr_balance")
        self.assertEqual(comps["z22_cage"]["type"], "seconds_rotor")


class RequiredMechanismTests(unittest.TestCase):
    """Ruling 3A — the whole matrix must not pass because one gear moved."""

    def setUp(self):
        self.comps = dm.parse_components(FACE_TOML)
        self.required = {c["name"] for c in dm.required_mechanisms(self.comps)}

    def test_all_four_aurelius_mechanisms_are_required(self):
        self.assertEqual(self.required,
                         {"z10_gl", "z11_gr", "z21_bal", "z22_cage"})

    def test_analog_hands_are_not_scored_as_required_motion(self):
        hands = {c["name"] for c in self.comps
                 if c.get("type") == "analog_hand" and c.get("name")}
        self.assertTrue(hands)
        self.assertFalse(hands & self.required)

    def test_static_and_decorative_components_are_not_required(self):
        for name in ("z52_hub", "z30_date", "z40_sheen", "z31_resv"):
            self.assertNotIn(name, self.required)


class MotionMeasurementTests(unittest.TestCase):
    """A slow mechanism must not read as static."""

    def test_a_static_series_shows_no_motion(self):
        series = [[10] * 100 for _ in range(90)]
        st = dm.component_motion(series)
        self.assertEqual(st["max_reference_delta"], 0.0)
        self.assertFalse(dm.mechanism_moved(st))

    def test_a_fast_mechanism_shows_motion(self):
        series = [[(i * 40) % 256] * 100 for i in range(90)]
        self.assertTrue(dm.mechanism_moved(dm.component_motion(series)))

    def test_a_slow_mechanism_is_caught_by_displacement_not_interframe(self):
        """The tourbillon cage turns 6 deg/s — sub-pixel between frames.

        Interframe delta alone would call it static; displacement against
        the first frame must not.
        """
        series = [[int(i * 0.2)] * 100 for i in range(90)]
        st = dm.component_motion(series)
        self.assertLess(st["mean_interframe_delta"],
                        dm.MOTION_INTERFRAME_MIN)
        self.assertGreater(st["max_reference_delta"],
                           dm.MOTION_REF_DELTA_MIN)
        self.assertTrue(dm.mechanism_moved(st))

    def test_an_oscillator_returning_to_phase_still_registers(self):
        """A balance wheel whose period divides the capture evenly returns
        to phase at 1/4, 1/2 and 3/4 — round sample offsets would measure
        it as perfectly static. It must still register as moving."""
        import math
        series = [[int(128 + 100 * math.sin(i * 2 * math.pi / 30))] * 100
                  for i in range(120)]
        st = dm.component_motion(series)
        self.assertTrue(dm.mechanism_moved(st),
                        f"oscillator read as static: {st}")

    def test_the_reference_offsets_are_not_round_fractions(self):
        """Guards the fix: 1/4, 1/2, 3/4 alias with common periods."""
        for f in dm.REF_OFFSETS:
            for bad in (0.25, 0.5, 0.75):
                self.assertNotAlmostEqual(f, bad, places=3)


class OverallMotionVerdictTests(unittest.TestCase):
    """Ruling 3A — one moving gear is not a working movement."""

    ALL = ["z10_gl", "z11_gr", "z21_bal", "z22_cage"]

    def test_all_moving_passes(self):
        r, d = dm.overall_motion_verdict(self.ALL, self.ALL, [], 1800, 60)
        self.assertEqual(r, "PASS")
        self.assertIn("all 4", d)

    def test_one_static_mechanism_fails_the_whole_row(self):
        r, d = dm.overall_motion_verdict(
            self.ALL, ["z10_gl", "z11_gr", "z21_bal"], ["z22_cage"], 1800, 60)
        self.assertEqual(r, "FAIL")
        self.assertIn("z22_cage", d)

    def test_only_one_moving_does_not_pass(self):
        """The exact weakness the ruling identified."""
        r, _ = dm.overall_motion_verdict(
            self.ALL, ["z10_gl"], ["z11_gr", "z21_bal", "z22_cage"], 1800, 60)
        self.assertEqual(r, "FAIL")

    def test_no_declared_mechanism_is_blocked_not_passed(self):
        r, _ = dm.overall_motion_verdict([], [], [], 1800, 60)
        self.assertEqual(r, "BLOCKED")


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
        for _, check, _ in dm.OWNER_ROWS:
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
        names = [c for _, c, _ in dm.OWNER_ROWS]
        self.assertTrue(any("exertion" in n for n in names))
        self.assertTrue(any("off-wrist" in n for n in names))

    def test_the_document_says_it_does_not_move_a_gate(self):
        m = dm.Matrix()
        dest = self.tmp / "DEVICE_TEST_RESULTS.md"
        dm.emit(m, dest, "aurelius", "2.0.0-rc2", "c" * 64, self.tmp)
        self.assertIn("does not move any gate",
                      dest.read_text(encoding="utf-8").lower())


class FakeAdb:
    """Canned adb responses, so the row logic is testable without a watch."""

    def __init__(self, shell_out: str = "", screencap: bytes = b""):
        self.shell_out = shell_out
        self.screencap = screencap
        self.calls: list[str] = []

    def sh(self, cmd: str, timeout: int = 120) -> str:
        self.calls.append(cmd)
        if "dumpsys power" in cmd:
            return "mWakefulness=Asleep"
        return self.shell_out

    def run(self, *args, timeout: int = 120, binary: bool = False):
        class R:
            pass
        r = R()
        r.stdout = self.screencap if binary else ""
        r.stderr = ""
        return r


class RuntimeSelectionTests(unittest.TestCase):
    """Ruling 3D — active-host state is measurable, not a judgement."""

    def test_face_not_selected_is_blocked_not_pending_owner(self):
        m = dm.Matrix()
        dm.row_runtime_host(FakeAdb("some other package"), m,
                            "com.xsytrance.aurelius")
        result, detail = m.rows[-1][1], m.rows[-1][2]
        self.assertEqual(result, "BLOCKED")
        self.assertNotIn("PENDING", result)
        self.assertIn("NOT SELECTED", detail)

    def test_face_selected_passes(self):
        m = dm.Matrix()
        dm.row_runtime_host(
            FakeAdb("Resource only package name com.xsytrance.aurelius"),
            m, "com.xsytrance.aurelius")
        self.assertEqual(m.rows[-1][1], "PASS")


class AodRowSplitTests(unittest.TestCase):
    """Ruling 3C — a captured PNG is not proof the render is intact."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._sleep = dm.time.sleep
        dm.time.sleep = lambda *_: None
        self.addCleanup(lambda: setattr(dm.time, "sleep", self._sleep))

    def test_transitions_and_capture_are_separate_rows(self):
        m = dm.Matrix()
        dm.row_aod_cycles(FakeAdb(screencap=b"\x89PNG fake"), m, self.tmp, 3)
        labels = [r[0] for r in m.rows]
        self.assertTrue(any("sleep/wake transitions" in x for x in labels))
        self.assertTrue(any("post-cycle screenshot captured" in x
                            for x in labels))

    def test_no_row_claims_the_render_is_visually_intact(self):
        m = dm.Matrix()
        dm.row_aod_cycles(FakeAdb(screencap=b"\x89PNG fake"), m, self.tmp, 2)
        for check, result, detail in m.rows:
            if result == "PASS":
                self.assertNotIn("visually intact", check.lower())
                self.assertNotIn("complete render", detail.lower())
        # it is an owner row instead
        self.assertTrue(any("visually intact" in c.lower()
                            for _, c, _ in dm.OWNER_ROWS))

    def test_a_missing_capture_is_blocked_not_passed(self):
        m = dm.Matrix()
        dm.row_aod_cycles(FakeAdb(screencap=b""), m, self.tmp, 2)
        cap = [r for r in m.rows if "screenshot captured" in r[0]][0]
        self.assertEqual(cap[1], "BLOCKED")


class BlackFrameTests(unittest.TestCase):
    """A capture of a sleeping panel is not a capture of the face.

    Caught on the first live run: the Watch7 screen times out in seconds,
    so `normal.png` came back an entirely black 1975-byte frame — the same
    size as the known-black doze capture — and the row reported PASS on
    file existence alone. That is the exact false-pass class the re-review
    flagged for AOD, sitting unnoticed in the normal-mode row.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def png(self, colour) -> bytes:
        from PIL import Image
        import io
        buf = io.BytesIO()
        Image.new("RGB", (48, 48), colour).save(buf, "PNG")
        return buf.getvalue()

    def test_a_black_capture_is_rejected(self):
        ok, detail = dm.capture_png(
            FakeAdb(screencap=self.png((0, 0, 0))), self.tmp / "n.png")
        self.assertFalse(ok)
        self.assertIn("black", detail.lower())

    def test_a_real_capture_is_accepted(self):
        ok, detail = dm.capture_png(
            FakeAdb(screencap=self.png((90, 100, 70))), self.tmp / "n.png")
        self.assertTrue(ok, detail)
        self.assertIn("non-black", detail)

    def test_an_empty_screencap_is_rejected(self):
        ok, detail = dm.capture_png(FakeAdb(screencap=b""),
                                    self.tmp / "n.png")
        self.assertFalse(ok)

    def test_unreadable_bytes_are_rejected_not_passed(self):
        ok, detail = dm.capture_png(FakeAdb(screencap=b"not a png"),
                                    self.tmp / "n.png")
        self.assertFalse(ok)

    def test_is_black_returns_none_for_unreadable(self):
        p = self.tmp / "junk.png"
        p.write_bytes(b"nope")
        self.assertIsNone(dm.is_black(p))


class OwnerObservationTests(unittest.TestCase):
    """Owner answers live outside the generated document.

    The matrix regenerates DEVICE_TEST_RESULTS.md on every run, so verdicts
    hand-edited into it would be destroyed by the next run. They live in
    OWNER_OBSERVATIONS.json and are merged in — fail-closed, so anything
    unrecognised stays PENDING rather than being coerced into a result.
    """

    APK = "a" * 64

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, obs, apk=None):
        (self.tmp / dm.OWNER_FILE).write_text(json.dumps({
            "schema": "agenor.owner-observations/1",
            "apk_sha256": apk if apk is not None else self.APK,
            "observations": obs}), encoding="utf-8")

    def test_absent_file_leaves_every_row_pending(self):
        self.assertEqual(dm.load_owner_observations(self.tmp, self.APK), {})

    def test_a_recorded_result_is_returned_verbatim(self):
        self.write({"Reserve ticks": {"result": "PASS", "note": "good"}})
        o = dm.load_owner_observations(self.tmp, self.APK)
        self.assertEqual(o["Reserve ticks"]["result"], "PASS")
        self.assertEqual(o["Reserve ticks"]["note"], "good")

    def test_an_unrecognised_result_is_rejected_not_coerced(self):
        self.write({"Reserve ticks": {"result": "probably fine"}})
        self.assertNotIn("Reserve ticks",
                         dm.load_owner_observations(self.tmp, self.APK))

    def test_not_tested_is_preserved_and_never_becomes_pass(self):
        self.write({"Battery gauge plausibility": {"result": "NOT TESTED"}})
        o = dm.load_owner_observations(self.tmp, self.APK)
        self.assertEqual(o["Battery gauge plausibility"]["result"],
                         "NOT TESTED")

    def test_observations_bound_to_another_apk_are_ignored(self):
        """An observation of another build is not evidence for this one."""
        self.write({"Reserve ticks": {"result": "PASS"}}, apk="b" * 64)
        self.assertEqual(dm.load_owner_observations(self.tmp, self.APK), {})

    def test_unreadable_file_leaves_rows_pending_rather_than_raising(self):
        (self.tmp / dm.OWNER_FILE).write_text("{not json", encoding="utf-8")
        self.assertEqual(dm.load_owner_observations(self.tmp, self.APK), {})

    def test_an_issue_row_is_surfaced_in_the_document(self):
        self.write({"Date readability": {
            "result": "ISSUE", "note": "grey on grey"}})
        m = dm.Matrix()
        m.add("measured", "PASS", "x")
        dest = self.tmp / "DEVICE_TEST_RESULTS.md"
        dm.emit(m, dest, "aurelius", "2.0.0-rc2", self.APK, self.tmp)
        text = dest.read_text(encoding="utf-8")
        self.assertIn("Owner-reported ISSUES", text)
        self.assertIn("grey on grey", text)
        self.assertIn("NOT acceptable as-is", text)

    def test_unobserved_rows_still_render_as_pending(self):
        self.write({"Reserve ticks": {"result": "PASS"}})
        m = dm.Matrix()
        dest = self.tmp / "DEVICE_TEST_RESULTS.md"
        dm.emit(m, dest, "aurelius", "2.0.0-rc2", self.APK, self.tmp)
        text = dest.read_text(encoding="utf-8")
        self.assertIn("PENDING — owner", text)
        self.assertIn("1 of 26 observed", text)


class HeartRateRowTests(unittest.TestCase):
    """The fallback is 70.0 bpm exactly; a reading there proves nothing."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_no_recording_is_blocked_not_passed(self):
        m = dm.Matrix()
        dm.row_heart_rate(m, self.tmp, None)
        self.assertEqual(m.rows[-1][1], "BLOCKED", m.rows)

    def test_live_data_distinct_from_fallback_may_pass(self):
        # the measured rc2 result: 1.7300 Hz = 103.8 bpm
        result, detail = dm.hr_verdict(1.73)
        self.assertEqual(result, "PASS")
        self.assertIn("103.8", detail)

    def test_a_reading_at_the_fallback_is_blocked(self):
        result, detail = dm.hr_verdict(dm.HR_FALLBACK_BPM / 60.0)
        self.assertEqual(result, "BLOCKED")
        self.assertIn("FALLBACK", detail)

    def test_context_interpretation_stays_with_the_owner(self):
        names = [c.lower() for _, c, _ in dm.OWNER_ROWS]
        self.assertTrue(any("exertion" in n for n in names))
        self.assertTrue(any("off-wrist" in n for n in names))
        self.assertTrue(any("agrees with the watch" in n for n in names))
        self.assertTrue(any("prompt" in n for n in names))


class CaptureDurationTests(unittest.TestCase):
    """Ruling 3B — Checkpoint B requires at least sixty seconds."""

    def test_the_default_record_length_is_sixty_seconds(self):
        src = (REPO / "tools/device_matrix.py").read_text(encoding="utf-8")
        mm = re.search(r'"--record-seconds",\s*type=int,\s*default=(\d+)', src)
        self.assertIsNotNone(mm, "could not find the --record-seconds default")
        self.assertEqual(int(mm.group(1)), 60)


if __name__ == "__main__":
    unittest.main()
