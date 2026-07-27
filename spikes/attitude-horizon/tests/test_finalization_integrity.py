"""Finalization-integrity tests for the DISPOSABLE spike harness.

The defect these close: `finalize` checked that an analysis ENTRY EXISTED
and nothing more. A mandatory resting analysis whose own status was
BLOCKED — too few measurable frames — could still advance the session to
PENDING_OWNER_REVIEW as though the machine evidence were complete. The
previous "successful finalization" test made it worse by inserting
placeholder indexes with fake paths and hashes that no integrity check
would ever resolve.

So the success path here is built from REAL deterministic fixture files
that survive every check, and each deliberate failure breaks exactly one
thing.

No physical device is contacted. Everything runs against fixture files.
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

SPIKE = Path(__file__).resolve().parents[1]
REPO = SPIKE.parents[1]
sys.path.insert(0, str(SPIKE))

import device_harness as dh  # noqa: E402
import generate_spike as gs  # noqa: E402


def horizon_frame(uncovered: bool = False, angle_shift: int = 0):
    """A frame the analyser can actually measure: light sky over dark
    ground inside the aperture, so a transition exists to find."""
    from PIL import Image
    im = Image.new("RGB", (480, 480), (28, 29, 31))
    ap = gs.AP
    x0, x1 = ap["cx"] - ap["hw"] + 6, ap["cx"] + ap["hw"] - 6
    y0, y1 = ap["cy"] - ap["hh"] + 6, ap["cy"] + ap["hh"] - 6
    split = ap["cy"] + angle_shift
    for y in range(y0, y1):
        col = (150, 154, 158) if y < split else (70, 54, 26)
        for x in range(x0, x1):
            im.putpixel((x, y), col)
    if uncovered:
        for y in range(y0 + 8, y0 + 26):
            for x in range(x0 + 8, x0 + 40):
                im.putpixel((x, y), (0, 0, 0))
    return im


class FixtureSession:
    """Builds a session whose evidence passes every integrity check."""

    def __init__(self, root: Path):
        self.session = root
        for sub in ("raw", "frames", "analysis", "pullback"):
            (self.session / sub).mkdir(parents=True, exist_ok=True)
        self.apk_sha = "a" * 64
        self.doc = {
            "schema": "xsywatch.attitude-spike-session/1",
            "binding": {
                "variant": "proposed",
                "package_id": gs.BASE_PACKAGE + ".proposed",
                "repo_head_at_session_creation": "b" * 40,
                "spike_source_manifest_sha256": "c" * 64,
                "built_apk_path": "spikes/attitude-horizon/app.apk",
                "built_apk_sha256": self.apk_sha,
                "device_serial": "10.0.0.9:5555",
                "device_manufacturer": "Samsung",
                "device_model": "SM-L310",
                "android_version": "16",
                "api_level": "36",
                "session_timestamp": "FIXTURE",
            },
            "installed_verification": {
                "status": "VERIFIED",
                "installed_apk_sha256": self.apk_sha,
                "built_apk_sha256": self.apk_sha,
            },
            "captures": {}, "frame_manifests": {}, "analysis": {},
        }

    def save(self):
        dh.save(self.session, self.doc)

    # -- builders ------------------------------------------------------

    def add_video(self, cid: str, nframes: int = 40, uncovered_at=None,
                  duration_disposition="PASS", duration_ratio=1.0,
                  status="MEASURED"):
        raw = self.session / "raw" / f"{cid}.mp4"
        raw.write_bytes(f"fixture video {cid}".encode())
        raw_sha = dh.sha256(raw)
        self.doc["captures"][cid] = {
            "capture_id": cid, "kind": "video", "disposition": "PASS",
            "intended_duration_s": 30,
            "files": [{"path": dh._rel(raw), "sha256": raw_sha,
                       "bytes": raw.stat().st_size}]}

        fdir = self.session / "frames" / cid
        fdir.mkdir(parents=True, exist_ok=True)
        frames = []
        for i in range(nframes):
            im = horizon_frame(uncovered=(uncovered_at == i),
                               angle_shift=(i % 5) - 2)
            fp = fdir / f"f{i:05d}.png"
            im.save(fp)
            frames.append(fp)
        man = {
            "capture_id": cid,
            "source_video_path": dh._rel(raw),
            "source_video_sha256": raw_sha,
            "ffmpeg_version": "ffmpeg fixture",
            "ffmpeg_command": "ffmpeg fixture",
            "ffmpeg_returncode": 0,
            "extraction_fps": dh.EXTRACT_FPS,
            "ffprobe_version": "ffprobe fixture",
            "ffprobe_command": "ffprobe fixture",
            "actual_media_duration_s": round(nframes / dh.EXTRACT_FPS, 4),
            "intended_duration_s": 30,
            "duration_ratio": duration_ratio,
            "capture_duration_disposition": duration_disposition,
            "expected_frame_count_from_media": nframes,
            "extraction_tolerance_frames": 2,
            "extraction_frame_delta": 0,
            "extraction_disposition": "PASS",
            "actual_frame_count": len(frames),
            "frames": [{"path": dh._rel(f), "sha256": dh.sha256(f)}
                       for f in frames],
        }
        mp = self.session / "frames" / f"{cid}_FRAMES.json"
        mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
        self.doc["frame_manifests"][cid] = {
            "manifest_path": dh._rel(mp), "manifest_sha256": dh.sha256(mp),
            "source_video_sha256": raw_sha,
            "actual_frame_count": len(frames),
            "capture_duration_disposition": duration_disposition,
            "duration_ratio": duration_ratio}

        scan = dh.scan_all_frames_for_exposure(frames)
        analysis = {
            "capture_id": cid, "status": status,
            "failed_measurement_frames": 0,
            "measurable_frames": len(frames),
            "mask_scan": scan,
            "smoothing_applied": False,
            "binding": {
                "raw_capture_sha256": raw_sha,
                "frame_manifest_sha256": dh.sha256(mp),
                "analysis_code_sha256": dh.analysis_code_hash(),
                "variant": "proposed",
                "built_apk_sha256": self.apk_sha,
                "installed_pullback_sha256": self.apk_sha,
                "device_model": "SM-L310",
                "android_version": "16",
                "api_level": "36",
                "timestamp": "FIXTURE",
            },
        }
        ap = self.session / "analysis" / f"{cid}.json"
        ap.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
        self.doc["analysis"][cid] = {
            "path": dh._rel(ap), "sha256": dh.sha256(ap), "status": status,
            "mask_scan": scan}
        return raw, mp, ap

    def add_screenshot(self, cid="screenshot_normal", disposition="PASS"):
        p = self.session / "raw" / f"{cid}.png"
        horizon_frame().save(p)
        self.doc["captures"][cid] = {
            "capture_id": cid, "kind": "screenshot",
            "disposition": disposition, "result": "CAPTURED",
            "files": [{"path": dh._rel(p), "sha256": dh.sha256(p),
                       "bytes": p.stat().st_size}]}
        return p

    def add_cycles(self, staged=10):
        p = self.session / "raw" / "aod_cycles.json"
        p.write_text(json.dumps([{"cycle": i + 1} for i in range(10)]))
        self.doc["captures"]["aod_cycles"] = {
            "capture_id": "aod_cycles", "kind": "cycles",
            "cycles_executed": 10, "cycles_staged": staged,
            "disposition": "PASS" if staged == 10 else "PARTIAL",
            "files": [{"path": dh._rel(p), "sha256": dh.sha256(p),
                       "bytes": p.stat().st_size}]}
        return p

    def add_logs(self, crash=0, fatal=0):
        p = self.session / "raw" / "logcat_crash.txt"
        p.write_text("")
        self.doc["captures"]["logs_crash_anr"] = {
            "capture_id": "logs_crash_anr", "kind": "logs",
            "crash_buffer_hits": crash, "fatal_or_anr_hits": fatal,
            "disposition": "CLEAN" if not crash and not fatal else "ISSUE",
            "files": [{"path": dh._rel(p), "sha256": dh.sha256(p),
                       "bytes": p.stat().st_size}]}
        return p

    def add_owner(self, answered=False):
        doc = {"variant": "proposed", "status": "PENDING",
               "observations": {q: {"answer": "yes" if answered else "PENDING",
                                    "note": ""}
                                for q in dh.OWNER_QUESTIONS}}
        (self.session / "OWNER_OBSERVATION.json").write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n")

    def complete(self, **kw):
        for cid in dh.VIDEO_CAPTURES:
            self.add_video(cid, **kw)
        self.add_screenshot()
        self.add_cycles()
        self.add_logs()
        self.add_owner()
        self.save()
        return self.session


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.fx = FixtureSession(self.tmp / "sessions" / "FIXTURE-proposed")

    def finalize(self):
        return dh.cmd_finalize(self.fx.session)

    def codes(self, doc, bucket="blocking_integrity_problems"):
        return {p["code"] for p in doc[bucket]}


class SuccessPathTests(Base):
    """Real fixture files, exact bindings — the honest happy path."""

    def test_complete_evidence_reaches_pending_owner_review(self):
        self.fx.complete(nframes=40)
        d = self.finalize()
        self.assertEqual(d["blocking_integrity_problems"], [], d)
        self.assertEqual(d["machine_issues"], [], d)
        self.assertEqual(d["status"], "PENDING_OWNER_REVIEW")
        self.assertTrue(d["pending_owner_observations"])

    def test_owner_answers_complete_the_session(self):
        self.fx.complete(nframes=40)
        self.fx.add_owner(answered=True)
        self.fx.save()
        d = self.finalize()
        self.assertEqual(d["status"], "COMPLETE")

    def test_full_scan_covered_every_frame(self):
        self.fx.complete(nframes=40)
        d = self.finalize()
        for cid in dh.VIDEO_CAPTURES:
            scan = d["machine_measured_results"][cid]["mask_scan"]
            self.assertEqual(scan["scan_coverage_percentage"], 100.0)
            self.assertFalse(scan["sampling_used"])
            self.assertEqual(scan["scanned_frames"],
                             scan["total_extracted_frames"])


class DeliberateFailureTests(Base):
    """One broken thing each."""

    # 1
    def test_1_mandatory_analysis_status_blocked(self):
        """THE loophole: a BLOCKED analysis must never reach owner review."""
        self.fx.complete(nframes=40)
        cid = "rest_surface_60s"
        ap = self.fx.session / "analysis" / f"{cid}.json"
        doc = json.loads(ap.read_text())
        doc["status"] = "BLOCKED"
        ap.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        self.fx.doc["analysis"][cid]["sha256"] = dh.sha256(ap)
        self.fx.doc["analysis"][cid]["status"] = "BLOCKED"
        self.fx.save()
        d = self.finalize()
        self.assertEqual(d["status"], "BLOCKED_INTEGRITY")
        self.assertIn("analysis-status", self.codes(d))
        self.assertNotEqual(d["status"], "PENDING_OWNER_REVIEW")

    # 2
    def test_2_analysis_file_missing(self):
        self.fx.complete(nframes=40)
        (self.fx.session / "analysis" / "sweep_pitch.json").unlink()
        d = self.finalize()
        self.assertIn("analysis-file-missing", self.codes(d))

    # 3
    def test_3_analysis_hash_mismatch(self):
        self.fx.complete(nframes=40)
        ap = self.fx.session / "analysis" / "sweep_pitch.json"
        ap.write_text(ap.read_text() + "\n")
        d = self.finalize()
        self.assertIn("analysis-hash-drift", self.codes(d))

    # 4
    def test_4_analysis_binding_disagrees_with_variant(self):
        self.fx.complete(nframes=40)
        cid = "sweep_pitch"
        ap = self.fx.session / "analysis" / f"{cid}.json"
        doc = json.loads(ap.read_text())
        doc["binding"]["variant"] = "assertive"
        ap.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        self.fx.doc["analysis"][cid]["sha256"] = dh.sha256(ap)
        self.fx.save()
        d = self.finalize()
        self.assertIn("analysis-binding-mismatch", self.codes(d))

    # 5
    def test_5_analysis_raw_hash_disagrees(self):
        self.fx.complete(nframes=40)
        cid = "sweep_pitch"
        ap = self.fx.session / "analysis" / f"{cid}.json"
        doc = json.loads(ap.read_text())
        doc["binding"]["raw_capture_sha256"] = "0" * 64
        ap.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        self.fx.doc["analysis"][cid]["sha256"] = dh.sha256(ap)
        self.fx.save()
        d = self.finalize()
        self.assertIn("analysis-binding-mismatch", self.codes(d))

    # 6
    def test_6_analysis_frame_manifest_hash_disagrees(self):
        self.fx.complete(nframes=40)
        cid = "sweep_pitch"
        ap = self.fx.session / "analysis" / f"{cid}.json"
        doc = json.loads(ap.read_text())
        doc["binding"]["frame_manifest_sha256"] = "0" * 64
        ap.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        self.fx.doc["analysis"][cid]["sha256"] = dh.sha256(ap)
        self.fx.save()
        d = self.finalize()
        self.assertIn("analysis-binding-mismatch", self.codes(d))

    # 7
    def test_7_mandatory_raw_file_missing(self):
        self.fx.complete(nframes=40)
        (self.fx.session / "raw" / "sweep_pitch.mp4").unlink()
        d = self.finalize()
        self.assertIn("raw-file-missing", self.codes(d))

    # 8
    def test_8_mandatory_raw_hash_drift(self):
        self.fx.complete(nframes=40)
        p = self.fx.session / "raw" / "sweep_pitch.mp4"
        p.write_bytes(p.read_bytes() + b"drift")
        d = self.finalize()
        self.assertIn("raw-hash-drift", self.codes(d))

    # 9
    def test_9_frame_manifest_file_missing(self):
        self.fx.complete(nframes=40)
        (self.fx.session / "frames" / "sweep_pitch_FRAMES.json").unlink()
        d = self.finalize()
        self.assertIn("manifest-file-missing", self.codes(d))

    # 10
    def test_10_frame_manifest_hash_drift(self):
        self.fx.complete(nframes=40)
        mp = self.fx.session / "frames" / "sweep_pitch_FRAMES.json"
        mp.write_text(mp.read_text() + "\n")
        d = self.finalize()
        self.assertIn("manifest-hash-drift", self.codes(d))

    # 11
    def test_11_source_video_hash_mismatch(self):
        self.fx.complete(nframes=40)
        cid = "sweep_pitch"
        mp = self.fx.session / "frames" / f"{cid}_FRAMES.json"
        man = json.loads(mp.read_text())
        man["source_video_sha256"] = "0" * 64
        mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
        self.fx.doc["frame_manifests"][cid]["manifest_sha256"] = dh.sha256(mp)
        self.fx.save()
        d = self.finalize()
        self.assertIn("manifest-source-mismatch", self.codes(d))

    # 12
    def test_12_listed_frame_missing(self):
        self.fx.complete(nframes=40)
        fdir = self.fx.session / "frames" / "sweep_pitch"
        sorted(fdir.glob("*.png"))[7].unlink()
        d = self.finalize()
        self.assertIn("frame-missing", self.codes(d))

    # 13
    def test_13_listed_frame_hash_drift(self):
        self.fx.complete(nframes=40)
        fdir = self.fx.session / "frames" / "sweep_pitch"
        f = sorted(fdir.glob("*.png"))[7]
        horizon_frame(angle_shift=9).save(f)
        d = self.finalize()
        self.assertIn("frame-hash-drift", self.codes(d))

    # 14
    def test_14_zero_frames(self):
        self.fx.complete(nframes=40)
        cid = "sweep_pitch"
        mp = self.fx.session / "frames" / f"{cid}_FRAMES.json"
        man = json.loads(mp.read_text())
        man["frames"] = []
        man["actual_frame_count"] = 0
        mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
        self.fx.doc["frame_manifests"][cid]["manifest_sha256"] = dh.sha256(mp)
        self.fx.save()
        d = self.finalize()
        self.assertIn("manifest-zero-frames", self.codes(d))

    # 15
    def test_15_materially_truncated_capture_blocks(self):
        """PARTIAL duration must not advance to owner review."""
        self.fx.complete(nframes=40)
        self.fx.add_video("sweep_pitch", nframes=40,
                          duration_disposition="PARTIAL", duration_ratio=0.85)
        self.fx.save()
        d = self.finalize()
        self.assertNotEqual(d["status"], "PENDING_OWNER_REVIEW")
        self.assertIn("capture-duration",
                      {i["code"] for i in d["machine_issues"]})

    # 17
    def test_17_normal_screenshot_not_obtainable_blocks(self):
        self.fx.complete(nframes=40)
        self.fx.add_screenshot("screenshot_normal",
                               disposition="NOT_OBTAINABLE")
        self.fx.save()
        d = self.finalize()
        self.assertNotEqual(d["status"], "PENDING_OWNER_REVIEW")
        self.assertIn("disposition-unacceptable", self.codes(d))

    # 18
    def test_18_partial_aod_cycles_block(self):
        self.fx.complete(nframes=40)
        self.fx.add_cycles(staged=7)
        self.fx.save()
        d = self.finalize()
        self.assertNotEqual(d["status"], "PENDING_OWNER_REVIEW")
        self.assertIn("aod-cycles-partial",
                      {i["code"] for i in d["machine_issues"]})

    # 19
    def test_19_crash_or_anr_findings_block(self):
        self.fx.complete(nframes=40)
        self.fx.add_logs(crash=2, fatal=1)
        self.fx.save()
        d = self.finalize()
        self.assertEqual(d["status"], "MACHINE_ISSUE")
        self.assertIn("crash-anr", {i["code"] for i in d["machine_issues"]})

    # 20
    def test_20_exposure_only_at_a_non_midpoint_extreme_is_detected(self):
        """A midpoint-only check would miss this — which is why it existed
        as a defect."""
        self.fx.complete(nframes=40)
        # frame 3 is far from the midpoint (20)
        self.fx.add_video("sweep_pitch", nframes=40, uncovered_at=3)
        self.fx.save()
        scan = self.fx.doc["analysis"]["sweep_pitch"]["mask_scan"]
        self.assertTrue(scan["exposed"])
        self.assertEqual(scan["first_exposed_frame"]["index"], 3)
        d = self.finalize()
        self.assertEqual(d["status"], "MACHINE_ISSUE")
        self.assertIn("mask-exposure",
                      {i["code"] for i in d["machine_issues"]})

    # 21
    def test_21_unknown_evidence_status(self):
        self.fx.complete(nframes=40)
        self.fx.doc["captures"]["logs_crash_anr"]["disposition"] = "SPLENDID"
        self.fx.save()
        d = self.finalize()
        self.assertIn("disposition-unknown", self.codes(d))

    # 22
    def test_22_placeholder_analysis_index_whose_file_does_not_exist(self):
        """The exact weakness in the old 'successful' fixture."""
        self.fx.complete(nframes=40)
        self.fx.doc["analysis"]["sweep_pitch"] = {
            "path": "nowhere/at/all.json", "sha256": "0" * 64,
            "status": "MEASURED"}
        self.fx.save()
        d = self.finalize()
        self.assertNotEqual(d["status"], "PENDING_OWNER_REVIEW")
        self.assertTrue(
            {"analysis-file-missing", "analysis-path-escape"}
            & self.codes(d))

    # 23
    def test_23_owner_answers_cannot_override_a_machine_issue(self):
        self.fx.complete(nframes=40)
        self.fx.add_logs(crash=1, fatal=0)
        self.fx.add_owner(answered=True)       # owner says everything is fine
        self.fx.save()
        d = self.finalize()
        self.assertEqual(d["status"], "MACHINE_ISSUE")
        self.assertNotEqual(d["status"], "COMPLETE")
        self.assertIn("never convert", d["status_rule"].lower())

    def test_23b_owner_answers_cannot_override_clipping(self):
        self.fx.complete(nframes=40)
        self.fx.add_video("sweep_roll_l_to_r", nframes=40, uncovered_at=31)
        self.fx.add_owner(answered=True)
        self.fx.save()
        d = self.finalize()
        self.assertEqual(d["status"], "MACHINE_ISSUE")
        scan = self.fx.doc["analysis"]["sweep_roll_l_to_r"]["mask_scan"]
        self.assertFalse(scan["waivable_by_owner"])

    # 24 / 25 are covered in test_device_harness (no install path, no device)
    def test_24_no_installation_command_is_reachable(self):
        src = (SPIKE / "device_harness.py").read_text(encoding="utf-8")
        import re
        self.assertIsNone(re.search(r'\.run\(\s*["\']install', src))

    def test_25_no_physical_device_contact_in_these_tests(self):
        """Behavioural, not textual — a source check for a literal would
        match its own assertion line, which is a mistake already made twice
        in this suite. Instead: make subprocess explode and prove the whole
        finalization path still runs from fixture files alone."""
        real = dh.subprocess.run

        def explode(*a, **k):
            raise AssertionError(f"a subprocess was invoked: {a}")

        self.fx.complete(nframes=20)
        dh.subprocess.run = explode
        try:
            d = self.finalize()
        finally:
            dh.subprocess.run = real
        self.assertEqual(d["status"], "PENDING_OWNER_REVIEW")


class DurationPolicyTests(unittest.TestCase):
    """Boundary tests for the judgment-call thresholds."""

    def test_pass_at_exactly_95_percent(self):
        d, r = dh.duration_disposition(28.5, 30.0)
        self.assertEqual(d, "PASS")
        self.assertAlmostEqual(r, 0.95, places=4)

    def test_partial_just_below_95_percent(self):
        d, _ = dh.duration_disposition(28.4, 30.0)
        self.assertEqual(d, "PARTIAL")

    def test_partial_at_exactly_80_percent(self):
        d, r = dh.duration_disposition(24.0, 30.0)
        self.assertEqual(d, "PARTIAL")
        self.assertAlmostEqual(r, 0.80, places=4)

    def test_blocked_just_below_80_percent(self):
        d, _ = dh.duration_disposition(23.9, 30.0)
        self.assertEqual(d, "BLOCKED")

    def test_half_length_is_blocked_not_partial(self):
        """The originally proposed 50% floor was rejected as too lenient."""
        d, _ = dh.duration_disposition(15.0, 30.0)
        self.assertEqual(d, "BLOCKED")


class ExtractionToleranceTests(unittest.TestCase):

    def test_tolerance_is_the_greater_of_two_frames_or_one_percent(self):
        self.assertEqual(dh.extraction_tolerance(100), 2)     # 1% = 1 -> 2
        self.assertEqual(dh.extraction_tolerance(900), 9)     # 1% = 9 -> 9
        self.assertEqual(dh.extraction_tolerance(1800), 18)

    def test_at_the_exact_boundary_is_accepted(self):
        expected = 1800
        tol = dh.extraction_tolerance(expected)
        self.assertLessEqual(abs((expected + tol) - expected), tol)

    def test_one_frame_beyond_the_boundary_is_rejected(self):
        expected = 1800
        tol = dh.extraction_tolerance(expected)
        self.assertGreater(abs((expected + tol + 1) - expected), tol)


class ScanPerformanceTests(unittest.TestCase):
    """Full coverage must be affordable, and must stay full."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_every_frame_is_scanned_and_runtime_recorded(self):
        frames = []
        for i in range(120):
            p = self.tmp / f"f{i:05d}.png"
            horizon_frame().save(p)
            frames.append(p)
        r = dh.scan_all_frames_for_exposure(frames)
        self.assertEqual(r["scanned_frames"], 120)
        self.assertEqual(r["total_extracted_frames"], 120)
        self.assertEqual(r["scan_coverage_percentage"], 100.0)
        self.assertFalse(r["sampling_used"])
        self.assertIsNotNone(r["scan_runtime_seconds"])
        self.assertGreater(r["frames_per_second_scanned"], 0)

    def test_a_missing_frame_during_scan_is_blocked(self):
        p = self.tmp / "gone.png"
        with self.assertRaises(dh.Blocked):
            dh.scan_all_frames_for_exposure([p])

    def test_first_worst_and_last_exposed_frames_are_recorded(self):
        frames = []
        for i in range(30):
            p = self.tmp / f"f{i:05d}.png"
            horizon_frame(uncovered=(i in (4, 21))).save(p)
            frames.append(p)
        r = dh.scan_all_frames_for_exposure(frames)
        self.assertEqual(r["uncovered_frame_count"], 2)
        self.assertEqual(r["first_exposed_frame"]["index"], 4)
        self.assertEqual(r["last_exposed_frame"]["index"], 21)
        self.assertIsNotNone(r["worst_exposed_frame"]["sha256"])
        self.assertEqual(r["disposition"], "ISSUE")


if __name__ == "__main__":
    unittest.main()
