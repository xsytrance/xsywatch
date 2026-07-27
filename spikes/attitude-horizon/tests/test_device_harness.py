"""Offline tests for the DISPOSABLE spike device harness.

Every path is exercised against a FAKE adb, so the whole workflow is proved
without touching a watch. No test in this file contacts a device.

The point is fail-closed behaviour: each deliberate-failure fixture shows a
specific way a session could produce a confident-looking result that is not
actually evidence, and proves the harness refuses instead.
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


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class FakeAdb(dh.Adb):
    """Scripted adb. Records every command; installs nothing, ever."""

    def __init__(self, serial="10.0.0.9:5555", *, present=True,
                 pm_paths=None, props=None, screencap=b"", pull_bytes=None,
                 devices_list=None):
        super().__init__(serial)
        self.present = present
        self.pm_paths = pm_paths if pm_paths is not None else \
            [f"/data/app/~~x/{gs.BASE_PACKAGE}.proposed-1/base.apk"]
        self.props = props or {"manufacturer": "Samsung", "model": "SM-L310",
                               "android_version": "16", "api_level": "36"}
        self.screencap = screencap
        self.pull_bytes = pull_bytes
        self.devices_list = devices_list

    def devices(self):
        if self.devices_list is not None:
            return self.devices_list
        return [self.serial] if self.present else []

    def sh(self, cmd, timeout=180):
        self._guard(["shell", cmd])
        self.log.append(["adb", "-s", self.serial, "shell", cmd])
        if "getprop ro.product.manufacturer" in cmd:
            return self.props.get("manufacturer", "")
        if "getprop ro.product.model" in cmd:
            return self.props.get("model", "")
        if "getprop ro.build.version.release" in cmd:
            return self.props.get("android_version", "")
        if "getprop ro.build.version.sdk" in cmd:
            return self.props.get("api_level", "")
        if cmd.startswith("pm path"):
            return "\n".join(f"package:{p}" for p in self.pm_paths)
        if "dumpsys power" in cmd:
            return "mWakefulness=Asleep"
        return ""

    def out(self, *args, timeout=180):
        self._guard(list(args))
        self.log.append(["adb", "-s", self.serial, *args])
        return ""

    def run(self, *args, timeout=180, binary=False):
        self._guard(list(args))
        self.log.append(["adb", "-s", self.serial, *args])

        class R:
            pass
        r = R()
        r.stdout = b"" if binary else ""
        r.stderr = ""
        if args and args[0] == "exec-out":
            r.stdout = self.screencap
        if args and args[0] == "pull" and self.pull_bytes is not None:
            Path(args[2]).parent.mkdir(parents=True, exist_ok=True)
            Path(args[2]).write_bytes(self.pull_bytes)
        return r


def built_apk_bytes() -> bytes | None:
    p = dh.apk_path("proposed")
    return p.read_bytes() if p.exists() else None


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._sessions = dh.SESSIONS
        dh.SESSIONS = self.tmp / "sessions"
        self.addCleanup(lambda: setattr(dh, "SESSIONS", self._sessions))
        self._sleep = dh.time.sleep
        dh.time.sleep = lambda *_: None
        self.addCleanup(lambda: setattr(dh.time, "sleep", self._sleep))
        if not dh.apk_path("proposed").exists():
            self.skipTest("spike APKs not built")

    def init_session(self, adb=None, variant="proposed") -> Path:
        return dh.cmd_session_init(adb or FakeAdb(), variant, stamp="TEST")

    def verified_session(self) -> tuple[Path, FakeAdb]:
        adb = FakeAdb(pull_bytes=built_apk_bytes())
        s = self.init_session(adb)
        dh.cmd_verify_installed(adb, s)
        return s, adb


class NoInstallPathTests(Base):
    """B3 — the single most important guarantee."""

    def test_the_source_constructs_no_install_invocation(self):
        """Precise, not keyword-matching: the word `install` legitimately
        appears in the FORBIDDEN token list that PREVENTS installs, and in
        the manual command printed for the owner. What must not exist is a
        CONSTRUCTED adb install call."""
        import re as _re
        src = (SPIKE / "device_harness.py").read_text(encoding="utf-8")
        for pattern in (r'\.run\(\s*["\']install',
                        r'adb["\']\s*,\s*["\']install',
                        r'\.sh\(\s*f?["\']\s*pm install',
                        r'subprocess\.run\(\[\s*["\']adb["\']\s*,'
                        r'\s*["\']install'):
            self.assertIsNone(_re.search(pattern, src),
                              f"constructed install call matching {pattern}")

    def test_the_guard_token_list_is_actually_wired_in(self):
        src = (SPIKE / "device_harness.py").read_text(encoding="utf-8")
        self.assertIn("FORBIDDEN_COMMAND_TOKENS", src)
        self.assertIn("self._guard", src)

    def test_every_emitted_command_is_install_free(self):
        """Drive the whole workflow and inspect every command emitted."""
        s, adb = self.verified_session()
        for cid in ("screenshot_normal", "aod_cycles", "logs_crash_anr"):
            try:
                dh.cmd_capture(adb, s, cid)
            except dh.Blocked:
                pass
        self.assertTrue(adb.log)
        for cmd in adb.log:
            joined = " ".join(cmd).lower()
            for tok in dh.FORBIDDEN_COMMAND_TOKENS:
                self.assertNotIn(f" {tok} ", f" {joined} ",
                                 f"harness emitted: {joined}")

    def test_the_guard_rejects_an_install_command_outright(self):
        adb = FakeAdb()
        with self.assertRaises(dh.Blocked):
            adb.run("install", "-r", "x.apk")
        with self.assertRaises(dh.Blocked):
            adb.sh("pm install /data/x.apk")

    def test_the_manual_command_is_printed_not_executed(self):
        s = self.init_session()
        doc = dh.load(s)
        self.assertIn("install -r", doc["manual_install_command"])
        self.assertIn("MANUAL", doc["install_policy"])


class SessionInitTests(Base):

    def test_session_records_every_required_binding(self):
        s = self.init_session()
        b = dh.load(s)["binding"]
        for k in dh.REQUIRED_BINDINGS:
            self.assertTrue(b.get(k), k)

    def test_unknown_variant_is_blocked(self):
        with self.assertRaises(dh.Blocked):
            dh.cmd_session_init(FakeAdb(), "nonexistent")

    def test_unreachable_device_is_blocked(self):
        with self.assertRaises(dh.Blocked):
            dh.cmd_session_init(FakeAdb(present=False), "proposed")

    def test_missing_device_model_is_blocked(self):
        adb = FakeAdb(props={"manufacturer": "Samsung", "model": "",
                             "android_version": "16", "api_level": "36"})
        with self.assertRaises(dh.Blocked):
            dh.cmd_session_init(adb, "proposed")

    def test_missing_android_version_is_blocked(self):
        adb = FakeAdb(props={"manufacturer": "S", "model": "SM-L310",
                             "android_version": "", "api_level": "36"})
        with self.assertRaises(dh.Blocked):
            dh.cmd_session_init(adb, "proposed")

    def test_missing_api_level_is_blocked(self):
        adb = FakeAdb(props={"manufacturer": "S", "model": "SM-L310",
                             "android_version": "16", "api_level": ""})
        with self.assertRaises(dh.Blocked):
            dh.cmd_session_init(adb, "proposed")

    def test_session_variant_and_package_agree(self):
        for v in gs.PROFILES:
            s = dh.cmd_session_init(FakeAdb(), v, stamp=f"T-{v}")
            b = dh.load(s)["binding"]
            self.assertEqual(b["variant"], v)
            self.assertEqual(b["package_id"],
                             gs.BASE_PACKAGE + gs.PROFILES[v]["suffix"])

    def test_owner_record_is_created_pending(self):
        s = self.init_session()
        d = json.loads((s / "OWNER_OBSERVATION.json").read_text())
        self.assertEqual(d["status"], "PENDING")
        self.assertTrue(all(a["answer"] == "PENDING"
                            for a in d["observations"].values()))


class VerifyInstalledTests(Base):

    def test_matching_pullback_verifies(self):
        s, _ = self.verified_session()
        v = dh.load(s)["installed_verification"]
        self.assertEqual(v["status"], "VERIFIED")
        self.assertEqual(v["installed_apk_sha256"], v["built_apk_sha256"])

    def test_hash_mismatch_blocks_the_session(self):
        adb = FakeAdb(pull_bytes=b"a different apk entirely")
        s = self.init_session(adb)
        with self.assertRaises(dh.Blocked):
            dh.cmd_verify_installed(adb, s)
        self.assertEqual(dh.load(s)["status"], "BLOCKED")

    def test_missing_pullback_is_blocked(self):
        adb = FakeAdb(pull_bytes=None)     # pull writes nothing
        s = self.init_session(adb)
        with self.assertRaises(dh.Blocked):
            dh.cmd_verify_installed(adb, s)

    def test_package_not_installed_is_blocked(self):
        adb = FakeAdb(pm_paths=[])
        s = self.init_session(adb)
        with self.assertRaises(dh.Blocked):
            dh.cmd_verify_installed(adb, s)

    def test_ambiguous_package_paths_are_blocked(self):
        adb = FakeAdb(pm_paths=["/data/app/a/base.apk",
                                "/data/app/b/base.apk"],
                      pull_bytes=built_apk_bytes())
        s = self.init_session(adb)
        with self.assertRaises(dh.Blocked):
            dh.cmd_verify_installed(adb, s)

    def test_wrong_package_for_variant_is_blocked(self):
        """A damped session must not accept the proposed package."""
        adb = FakeAdb(pm_paths=[], pull_bytes=built_apk_bytes())
        s = dh.cmd_session_init(adb, "damped", stamp="T-wrong")
        self.assertEqual(dh.load(s)["binding"]["package_id"],
                         gs.BASE_PACKAGE + ".damped")
        with self.assertRaises(dh.Blocked):
            dh.cmd_verify_installed(adb, s)


class CaptureOrderingTests(Base):

    def test_capture_before_verification_is_blocked(self):
        adb = FakeAdb()
        s = self.init_session(adb)
        with self.assertRaises(dh.Blocked):
            dh.cmd_capture(adb, s, "screenshot_normal")

    def test_unknown_capture_id_is_blocked(self):
        s, adb = self.verified_session()
        with self.assertRaises(dh.Blocked):
            dh.cmd_capture(adb, s, "not_a_capture")

    def test_all_planned_capture_ids_exist(self):
        self.assertEqual(set(dh.ALL_CAPTURES), {
            "rest_surface_60s", "rest_wrist_60s", "sweep_roll_l_to_r",
            "sweep_roll_r_to_l", "sweep_pitch", "extremes_combined",
            "aod_cycles", "screenshot_normal", "screenshot_aod",
            "logs_crash_anr"})

    def test_black_aod_screenshot_is_not_obtainable_not_pass(self):
        from PIL import Image
        import io
        buf = io.BytesIO()
        Image.new("RGB", (480, 480), (0, 0, 0)).save(buf, "PNG")
        s, _ = self.verified_session()
        adb = FakeAdb(screencap=buf.getvalue(), pull_bytes=built_apk_bytes())
        rec = dh.cmd_capture(adb, s, "screenshot_aod")
        self.assertEqual(rec["result"], "NOT_OBTAINABLE")
        self.assertNotEqual(rec["result"], "PASS")

    def test_aod_cycles_runs_exactly_ten(self):
        s, adb = self.verified_session()
        rec = dh.cmd_capture(adb, s, "aod_cycles")
        self.assertEqual(rec["cycles_executed"], 10)


class FrameExtractionTests(Base):

    def make_video_capture(self, s, cid="rest_surface_60s", nframes=90):
        """Synthesise a raw capture + frames without a device."""
        from PIL import Image
        raw = s / "raw" / f"{cid}.mp4"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"fake video bytes")
        doc = dh.load(s)
        doc["captures"][cid] = {
            "capture_id": cid, "kind": "video", "intended_duration_s": 3,
            "files": [{"path": dh._rel(raw),
                       "sha256": dh.sha256(raw), "bytes": raw.stat().st_size}]}
        frames_dir = s / "frames" / cid
        frames_dir.mkdir(parents=True, exist_ok=True)
        frames = []
        for i in range(nframes):
            im = Image.new("RGB", (480, 480), (20, 20, 20))
            ap = gs.AP
            for y in range(ap["cy"] - ap["hh"], ap["cy"]):
                for x in range(ap["cx"] - 100, ap["cx"] + 100):
                    im.putpixel((x, y), (120, 124, 128))
            for y in range(ap["cy"], ap["cy"] + ap["hh"]):
                for x in range(ap["cx"] - 100, ap["cx"] + 100):
                    im.putpixel((x, y), (60, 46, 22))
            p = frames_dir / f"f{i:05d}.png"
            im.save(p)
            frames.append(p)
        man = {"capture_id": cid,
               "source_video_path": dh._rel(raw),
               "source_video_sha256": dh.sha256(raw),
               "ffmpeg_version": "fixture", "ffmpeg_command": "fixture",
               "extraction_fps": dh.EXTRACT_FPS,
               "expected_frame_count": nframes,
               "actual_frame_count": len(frames),
               "frames": [{"path": dh._rel(f),
                           "sha256": dh.sha256(f)} for f in frames]}
        mp = s / "frames" / f"{cid}_FRAMES.json"
        mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
        doc["frame_manifests"][cid] = {
            "manifest_path": dh._rel(mp),
            "manifest_sha256": dh.sha256(mp),
            "source_video_sha256": dh.sha256(raw),
            "actual_frame_count": len(frames)}
        dh.save(s, doc)
        return raw, mp

    def test_extract_requires_an_existing_capture(self):
        s, _ = self.verified_session()
        with self.assertRaises(dh.Blocked):
            dh.cmd_extract_frames(s, "rest_surface_60s")

    def test_missing_raw_capture_is_blocked(self):
        s, _ = self.verified_session()
        raw, _ = self.make_video_capture(s)
        raw.unlink()
        with self.assertRaises(dh.Blocked):
            dh.cmd_extract_frames(s, "rest_surface_60s")

    def test_changed_raw_capture_hash_is_blocked(self):
        s, _ = self.verified_session()
        raw, _ = self.make_video_capture(s)
        raw.write_bytes(b"different bytes now")
        with self.assertRaises(dh.Blocked):
            dh.cmd_extract_frames(s, "rest_surface_60s")

    def test_frame_manifest_records_the_binding_fields(self):
        s, _ = self.verified_session()
        _, mp = self.make_video_capture(s)
        man = json.loads(mp.read_text())
        for k in ("source_video_sha256", "ffmpeg_version", "ffmpeg_command",
                  "extraction_fps", "expected_frame_count",
                  "actual_frame_count", "frames"):
            self.assertIn(k, man)


class AnalysisTests(FrameExtractionTests):

    def test_missing_frame_manifest_is_blocked(self):
        s, _ = self.verified_session()
        raw = s / "raw" / "rest_surface_60s.mp4"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"x")
        doc = dh.load(s)
        doc["captures"]["rest_surface_60s"] = {
            "capture_id": "rest_surface_60s", "kind": "video",
            "files": [{"path": dh._rel(raw),
                       "sha256": dh.sha256(raw), "bytes": 1}]}
        dh.save(s, doc)
        with self.assertRaises(dh.Blocked):
            dh.cmd_analyze(s, "rest_surface_60s")

    def test_frame_manifest_not_bound_to_raw_is_blocked(self):
        s, _ = self.verified_session()
        _, mp = self.make_video_capture(s)
        man = json.loads(mp.read_text())
        man["source_video_sha256"] = "0" * 64
        mp.write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
        doc = dh.load(s)
        doc["frame_manifests"]["rest_surface_60s"]["manifest_sha256"] = \
            dh.sha256(mp)
        dh.save(s, doc)
        with self.assertRaises(dh.Blocked):
            dh.cmd_analyze(s, "rest_surface_60s")

    def test_too_few_measurable_frames_is_blocked_not_reported(self):
        s, _ = self.verified_session()
        self.make_video_capture(s, nframes=5)
        out = dh.cmd_analyze(s, "rest_surface_60s")
        self.assertEqual(out["status"], "BLOCKED")
        self.assertIn("too few", out["reason"])

    def test_successful_rest_analysis_reports_every_metric(self):
        s, _ = self.verified_session()
        self.make_video_capture(s, nframes=60)
        out = dh.cmd_analyze(s, "rest_surface_60s")
        self.assertEqual(out["status"], "MEASURED")
        for k in ("measurable_frames", "median_angle_deg",
                  "p95_abs_angular_deviation_deg",
                  "max_angular_excursion_deg",
                  "median_vertical_displacement_px",
                  "p95_abs_vertical_deviation_px",
                  "max_vertical_excursion_px",
                  "max_frame_to_frame_angular_step_deg", "sign_changes"):
            self.assertIn(k, out, k)
        self.assertIs(out["smoothing_applied"], False)

    def test_analysis_is_bound_to_raw_and_device(self):
        s, _ = self.verified_session()
        self.make_video_capture(s, nframes=60)
        b = dh.cmd_analyze(s, "rest_surface_60s")["binding"]
        for k in ("raw_capture_sha256", "frame_manifest_sha256",
                  "analysis_code_sha256", "variant", "built_apk_sha256",
                  "installed_pullback_sha256", "device_model",
                  "android_version", "api_level", "timestamp"):
            self.assertTrue(b.get(k), k)

    def test_analysis_before_verification_is_blocked(self):
        adb = FakeAdb()
        s = self.init_session(adb)
        with self.assertRaises(dh.Blocked):
            dh.cmd_analyze(s, "rest_surface_60s")

    def test_an_aod_series_that_moves_is_detected(self):
        moving = [(0.0, 0.0), (3.5, 6.0), (-4.0, -7.0)]
        r = dh.aod_neutrality(moving)
        self.assertFalse(r["remains_neutral"])
        self.assertTrue(r["detected_movement"])

    def test_a_static_aod_series_is_neutral(self):
        still = [(0.02, 0.1), (0.0, 0.0), (-0.01, 0.05)]
        r = dh.aod_neutrality(still)
        self.assertTrue(r["remains_neutral"])
        self.assertFalse(r["detected_movement"])

    def test_uncovered_aperture_pixels_are_detected(self):
        from PIL import Image
        p = self.tmp / "black.png"
        Image.new("RGB", (480, 480), (0, 0, 0)).save(p)
        r = dh.mask_edge_exposure(p)
        self.assertTrue(r["exposed"])
        self.assertGreater(r["uncovered_pixels"], 0)

    def test_a_covered_aperture_reports_no_exposure(self):
        from PIL import Image
        p = self.tmp / "covered.png"
        Image.new("RGB", (480, 480), (120, 120, 120)).save(p)
        self.assertFalse(dh.mask_edge_exposure(p)["exposed"])

    def test_sweep_reports_direction_and_clamp(self):
        rising = [(float(i) * 0.5, 0.0) for i in range(40)]
        r = dh.sweep_behaviour(rising)
        self.assertEqual(r["response_direction"], "increasing")
        self.assertGreater(r["monotonic_fraction"], 0.9)
        self.assertAlmostEqual(r["observed_clamp_deg"], 19.5, places=3)

    def test_no_analysis_applies_smoothing(self):
        """Word-boundary matched: a bare substring like `ema(` also matches
        `getextrema(`, which has nothing to do with smoothing."""
        import re as _re
        src = (SPIKE / "device_harness.py").read_text(encoding="utf-8")
        for bad in ("savgol", "gaussian_filter", "lowpass", "butterworth",
                    "moving_average", "savitzky"):
            self.assertIsNone(_re.search(rf"\b{bad}", src, _re.I), bad)
        self.assertIsNone(_re.search(r"\bema\s*\(", src))
        self.assertIn("NO SMOOTHING", src.upper())
        for fn in (dh.rest_stability, dh.sweep_behaviour, dh.aod_neutrality):
            self.assertIn("smoothing_applied", str(fn.__code__.co_consts))


class FinalizeTests(AnalysisTests):

    def test_finalize_blocks_without_verification(self):
        adb = FakeAdb()
        s = self.init_session(adb)
        d = dh.cmd_finalize(s)
        self.assertEqual(d["status"], "BLOCKED")
        self.assertTrue(any("verification" in p
                            for p in d["blocking_problems"]))

    def test_finalize_blocks_with_missing_mandatory_captures(self):
        s, _ = self.verified_session()
        d = dh.cmd_finalize(s)
        self.assertEqual(d["status"], "BLOCKED")
        self.assertTrue(any("required capture missing" in p
                            for p in d["blocking_problems"]))

    def test_finalize_blocks_on_hash_mismatch(self):
        s, _ = self.verified_session()
        doc = dh.load(s)
        doc["installed_verification"]["installed_apk_sha256"] = "f" * 64
        dh.save(s, doc)
        d = dh.cmd_finalize(s)
        self.assertEqual(d["status"], "BLOCKED")

    def test_finalize_separates_machine_from_owner(self):
        s, _ = self.verified_session()
        d = dh.cmd_finalize(s)
        for k in ("machine_measured_results", "not_obtainable",
                  "pending_owner_observations"):
            self.assertIn(k, d)

    def test_owner_answers_are_never_inferred(self):
        s, _ = self.verified_session()
        d = dh.cmd_finalize(s)
        self.assertTrue(d["pending_owner_observations"])
        self.assertIn("never inferred", d["status_rule"])

    def test_status_is_pending_owner_review_when_machine_complete(self):
        """Machine-complete but owner-pending must NOT read as COMPLETE."""
        s, _ = self.verified_session()
        doc = dh.load(s)
        for cid in dh.MANDATORY_CAPTURES:
            raw = s / "raw" / f"{cid}.bin"
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(b"x")
            doc["captures"][cid] = {
                "capture_id": cid,
                "kind": "video" if cid in dh.VIDEO_CAPTURES else "logs",
                "files": [{"path": dh._rel(raw),
                           "sha256": dh.sha256(raw), "bytes": 1}]}
            if cid in dh.VIDEO_CAPTURES:
                doc["frame_manifests"][cid] = {
                    "manifest_path": "x", "manifest_sha256": "y",
                    "source_video_sha256": dh.sha256(raw),
                    "actual_frame_count": 1}
                doc["analysis"][cid] = {"path": "a", "sha256": "b",
                                        "status": "MEASURED"}
        dh.save(s, doc)
        d = dh.cmd_finalize(s)
        self.assertEqual(d["status"], "PENDING_OWNER_REVIEW")
        self.assertNotEqual(d["status"], "COMPLETE")


class OwnerRecordTests(Base):

    def test_no_cross_profile_answer_leakage(self):
        a = dh.cmd_session_init(FakeAdb(), "damped", stamp="T-a")
        b = dh.cmd_session_init(FakeAdb(), "assertive", stamp="T-b")
        pa = a / "OWNER_OBSERVATION.json"
        da = json.loads(pa.read_text())
        q = dh.OWNER_QUESTIONS[0]
        da["observations"][q] = {"answer": "yes", "note": "damped only"}
        pa.write_text(json.dumps(da, indent=2, sort_keys=True) + "\n")
        db = json.loads((b / "OWNER_OBSERVATION.json").read_text())
        self.assertEqual(db["observations"][q]["answer"], "PENDING")
        self.assertEqual(db["variant"], "assertive")

    def test_template_form_covers_the_final_comparison(self):
        p = SPIKE / "OWNER_COMPARISON.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        joined = " ".join(d["final_decisions"]).lower()
        for needle in ("preferred", "damped", "premium", "excessive",
                       "pitch", "roll"):
            self.assertIn(needle, joined, needle)
        self.assertEqual(set(d["allowed_final_concept_answers"]),
                         set(dh.FINAL_HORIZON_ANSWERS))
        for v in d["profiles"].values():
            self.assertTrue(all(a["answer"] == "PENDING"
                                for a in v["observations"].values()))


class NoDeviceContactTests(unittest.TestCase):
    """Nothing in this suite may reach a real watch."""

    def test_no_real_subprocess_is_needed_for_the_workflow(self):
        """Behavioural, not textual — the previous version asserted a
        literal that its own assertion line contained, so it matched
        itself. This instead makes subprocess.run explode and proves the
        fake-driven workflow still completes without it."""
        import tempfile as _tf
        if not dh.apk_path("proposed").exists():
            self.skipTest("spike APKs not built")
        tmp = Path(_tf.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        real_run, real_sessions = subprocess.run, dh.SESSIONS
        dh.SESSIONS = tmp / "sessions"

        def explode(*a, **k):
            raise AssertionError(f"real subprocess invoked: {a}")

        dh.subprocess.run = explode
        try:
            adb = FakeAdb(pull_bytes=built_apk_bytes())
            # repo_head() would shell out, so the fake session stamps it
            s = dh.SESSIONS / "T-fake"
            for sub in ("raw", "frames", "analysis", "pullback"):
                (s / sub).mkdir(parents=True, exist_ok=True)
            dh.save(s, {"binding": {k: "x" for k in dh.REQUIRED_BINDINGS},
                        "captures": {}, "frame_manifests": {}, "analysis": {},
                        "installed_verification": {"status": "VERIFIED"}})
            dh.require_bindings(dh.load(s))
            dh.require_verified_install(dh.load(s))
        finally:
            dh.subprocess.run = real_run
            dh.SESSIONS = real_sessions

    def test_apks_are_untouched_by_the_harness(self):
        rec = json.loads((SPIKE / "BUILD_RECORD.json").read_text())
        for v, r in rec["variants"].items():
            p = dh.apk_path(v)
            if p.exists():
                self.assertEqual(sha256_bytes(p.read_bytes()),
                                 r["apk_sha256"], v)


if __name__ == "__main__":
    unittest.main()
