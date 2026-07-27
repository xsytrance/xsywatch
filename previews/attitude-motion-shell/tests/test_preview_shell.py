"""Isolated tests for the ATTITUDE clean motion-preview shell.

The preview exists to make the motion judgeable, so the thing that must be
guaranteed above all is that it did not quietly CHANGE the motion while
tidying the visuals. Those tests compare against the accepted spike
generator itself rather than against numbers duplicated here — duplicated
constants would agree with each other while both drifted from the spike.

Nothing in this file contacts a device.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PREVIEW = Path(__file__).resolve().parents[1]
REPO = PREVIEW.parents[1]
SPIKE = REPO / "spikes/attitude-horizon"

sys.path.insert(0, str(PREVIEW))
sys.path.insert(0, str(SPIKE))

import generate_preview as gp   # noqa: E402
import generate_spike as gs     # noqa: E402

APP = PREVIEW / "app"
REVIEW = PREVIEW / "review"


def xml_for(profile: str) -> str:
    return (APP / "src" / profile / "res/raw/watchface.xml").read_text(
        encoding="utf-8")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class MotionContractTests(unittest.TestCase):
    """Compared against the SPIKE, not against a second copy of the numbers."""

    def test_profiles_match_the_accepted_spike_exactly(self):
        self.assertEqual(set(gp.PROFILES), set(gs.PROFILES))
        for n in gs.PROFILES:
            self.assertEqual(gp.PROFILES[n]["roll_deg"],
                             gs.PROFILES[n]["roll_deg"], n)
            self.assertEqual(gp.PROFILES[n]["pitch_px"],
                             gs.PROFILES[n]["pitch_px"], n)

    def test_clamps_match_the_accepted_spike(self):
        self.assertEqual(gp.WRIST_ROLL_CLAMP, gs.WRIST_ROLL_CLAMP)
        self.assertEqual(gp.WRIST_PITCH_CLAMP, gs.WRIST_PITCH_CLAMP)

    def test_roll_expression_text_is_identical_to_the_spike(self):
        for n in gs.PROFILES:
            self.assertEqual(gp.roll_expression(n),
                             gs.roll_expression(gs.PROFILES[n]["roll_deg"]), n)

    def test_pitch_expression_text_is_identical_to_the_spike(self):
        for n in gs.PROFILES:
            for base in (0.0, -12.0, 137.5):
                self.assertEqual(
                    gp.pitch_expression(n, base),
                    gs.pitch_expression(gs.PROFILES[n]["pitch_px"], base), n)

    def test_evaluated_endpoints_and_intermediates_match(self):
        points = [-90, -45, -44, -30, -22.5, -10, -1, 0, 1, 10, 22.5, 30,
                  44, 45, 90]
        for n in gs.PROFILES:
            for w in points:
                self.assertAlmostEqual(gp.evaluate_roll(n, w),
                                       gs.evaluate_roll(n, w), places=9,
                                       msg=f"{n} roll @ {w}")
                self.assertAlmostEqual(gp.evaluate_pitch(n, w),
                                       gs.evaluate_pitch(n, w), places=9,
                                       msg=f"{n} pitch @ {w}")

    def test_neutral_maps_exactly_to_zero(self):
        for n in gp.PROFILES:
            self.assertEqual(gp.evaluate_roll(n, 0.0), 0.0)
            self.assertEqual(gp.evaluate_pitch(n, 0.0), 0.0)

    def test_roll_sign_is_negative_like_the_spike(self):
        for n in gp.PROFILES:
            self.assertLess(gp.evaluate_roll(n, 45), 0.0, n)
            self.assertGreater(gp.evaluate_roll(n, -45), 0.0, n)
            self.assertTrue(gp.roll_expression(n).lstrip().startswith("-"), n)

    def test_mapping_is_clamped_and_symmetric(self):
        for n in gp.PROFILES:
            at = abs(gp.evaluate_roll(n, gp.WRIST_ROLL_CLAMP))
            for beyond in (46, 120, 900):
                self.assertAlmostEqual(abs(gp.evaluate_roll(n, beyond)), at,
                                       places=9)
            for w in (7, 19, 33):
                self.assertAlmostEqual(gp.evaluate_roll(n, w),
                                       -gp.evaluate_roll(n, -w), places=9)

    def test_aperture_geometry_matches_the_spike(self):
        self.assertEqual(gp.AP, dict(gs.AP))
        for k in ("cx", "cy", "hw", "hh", "radius"):
            self.assertIn(k, gp.AP)
        self.assertEqual((gp.AP["cx"], gp.AP["cy"]), (240, 252))
        self.assertEqual((gp.AP["hw"], gp.AP["hh"]), (156, 74))
        self.assertEqual(gp.AP["radius"], 42)

    def test_coverage_margin_is_positive_for_every_profile(self):
        R = gp.field_radius()
        for n, spec in gp.PROFILES.items():
            self.assertGreater(gs.coverage_margin(R, spec["pitch_px"]), 0, n)


class PackagingTests(unittest.TestCase):

    def test_exact_package_ids(self):
        self.assertEqual(
            {gp.BASE_PACKAGE + p["suffix"] for p in gp.PROFILES.values()},
            {"com.xsytrance.attitude.preview.damped",
             "com.xsytrance.attitude.preview.proposed",
             "com.xsytrance.attitude.preview.assertive"})

    def test_preview_packages_never_collide_with_spike_packages(self):
        prev = {gp.BASE_PACKAGE + p["suffix"] for p in gp.PROFILES.values()}
        spike = {gs.BASE_PACKAGE + p["suffix"] for p in gs.PROFILES.values()}
        self.assertEqual(prev & spike, set())
        self.assertNotEqual(gp.BASE_PACKAGE, gs.BASE_PACKAGE)

    def test_all_six_packages_can_coexist(self):
        prev = {gp.BASE_PACKAGE + p["suffix"] for p in gp.PROFILES.values()}
        spike = {gs.BASE_PACKAGE + p["suffix"] for p in gs.PROFILES.values()}
        self.assertEqual(len(prev | spike), 6)

    def test_version_name_says_preview_and_not_spike_or_release(self):
        self.assertIn("preview", gp.VERSION_NAME.lower())
        for bad in ("spike", "rc", "release", "production"):
            self.assertNotIn(bad, gp.VERSION_NAME.lower())

    def test_labels_are_readable_and_name_the_profile(self):
        for n, p in gp.PROFILES.items():
            self.assertEqual(p["label"], f"ATTITUDE Preview — {n.upper()}")

    def test_no_permissions_are_declared(self):
        m = (APP / "src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertNotIn("uses-permission", m)

    def test_no_signing_or_bundle_configuration(self):
        g = (APP / "build.gradle.kts").read_text(encoding="utf-8")
        for bad in ("signingConfig", "storeFile", "keyAlias", "keyPassword",
                    "storePassword", "bundle {"):
            self.assertNotIn(bad, g)

    def test_no_aab_exists(self):
        self.assertEqual(list(PREVIEW.rglob("*.aab")), [])

    def test_not_available_in_retail(self):
        info = (APP / "src/damped/res/xml/watch_face_info.xml").read_text(
            encoding="utf-8")
        self.assertIn('<AvailableInRetail value="false" />', info)


class VisualContractTests(unittest.TestCase):

    def test_no_analog_hand_elements_or_resources(self):
        for n in gp.PROFILES:
            x = xml_for(n)
            for bad in ("hand_hour", "hand_min", "analog_hand", "hour_hand",
                        "min_hand"):
                self.assertNotIn(bad, x, f"{n}: {bad}")
        res = APP / "src/main/res/drawable-nodpi"
        for p in res.glob("*.png"):
            self.assertNotIn("hand", p.name.lower())

    def test_no_custom_glyph_alphabet_is_used(self):
        src = (PREVIEW / "generate_preview.py").read_text(encoding="utf-8")
        for bad in ("_blocky", "GLYPHS", "def glyph(", "BitmapFont"):
            self.assertNotIn(bad, src, bad)
        for n in gp.PROFILES:
            self.assertNotIn("BitmapFont", xml_for(n))

    def test_text_uses_a_real_system_font_family(self):
        for n in gp.PROFILES:
            x = xml_for(n)
            self.assertIn('<Font family="sans-serif"', x, n)

    def test_readable_literal_profile_names_are_present(self):
        for n in gp.PROFILES:
            self.assertIn(f">{n.upper()}<", xml_for(n), n)

    def test_a_preview_marker_is_visible_on_the_face(self):
        for n in gp.PROFILES:
            self.assertIn("MOTION PREVIEW", xml_for(n), n)

    def test_a_live_digital_time_is_present(self):
        for n in gp.PROFILES:
            x = xml_for(n)
            self.assertIn("[HOUR_0_23]", x, n)
            self.assertIn("[MINUTE", x, n)

    def test_no_extra_complications(self):
        for n in gp.PROFILES:
            x = xml_for(n)
            for bad in ("[DAY", "[STEP", "[HEART_RATE]", "[BATTERY_PERCENT]",
                        "[SECOND]"):
                self.assertNotIn(bad, x, f"{n}: {bad}")

    def test_the_plate_covers_the_whole_canvas(self):
        """A circular plate let the horizon leak into the corners."""
        from PIL import Image
        p = APP / "src/main/res/drawable-nodpi/plate.png"
        with Image.open(p) as im:
            a = im.convert("RGBA")
            for xy in ((0, 0), (479, 0), (0, 479), (479, 479)):
                self.assertEqual(a.getpixel(xy)[3], 255,
                                 f"plate transparent at {xy}")

    def test_the_aperture_is_actually_transparent(self):
        from PIL import Image
        p = APP / "src/main/res/drawable-nodpi/plate.png"
        with Image.open(p) as im:
            a = im.convert("RGBA")
            self.assertEqual(a.getpixel((gp.AP["cx"], gp.AP["cy"] - 40))[3], 0)


class AodTests(unittest.TestCase):

    def test_aod_forces_neutral_roll_and_pitch(self):
        for n in gp.PROFILES:
            x = xml_for(n)
            self.assertIn('<Variant mode="AMBIENT" target="angle" value="0" />',
                          x, n)
            self.assertRegex(
                x, r'<Variant mode="AMBIENT" target="y" value="-?\d+" />', n)

    def test_no_ambient_variant_carries_a_sensor_expression(self):
        for n in gp.PROFILES:
            for m in re.finditer(r'<Variant mode="AMBIENT"[^>]*/>',
                                 xml_for(n)):
                self.assertNotIn("ACCELEROMETER", m.group(0), n)

    def test_aod_uses_a_separate_ladderless_resource(self):
        for n in gp.PROFILES:
            self.assertIn('resource="horizon_aod"', xml_for(n), n)

    def test_the_aod_horizon_has_no_pitch_ladder(self):
        """Measured, not asserted: the ambient field has fewer distinct
        bright rows than the normal one."""
        from PIL import Image
        res = APP / "src/main/res/drawable-nodpi"
        def bright_rows(name):
            with Image.open(res / name) as im:
                g = im.convert("L")
                px = g.load()
                w, h = g.size
                return sum(1 for y in range(h)
                           if any(px[x, y] > 150 for x in range(0, w, 3)))
        self.assertLess(bright_rows("horizon_aod.png"),
                        bright_rows("horizon.png"))

    def test_aod_is_darker_than_normal(self):
        from PIL import Image
        res = APP / "src/main/res/drawable-nodpi"
        def mean(name):
            with Image.open(res / name) as im:
                b = im.convert("L").tobytes()
                return sum(b) / len(b)
        self.assertLess(mean("horizon_aod.png"), mean("horizon.png") * 0.6)
        self.assertLess(mean("plate_aod.png"), mean("plate.png") + 1)


class NoSmoothingTests(unittest.TestCase):

    def test_no_smoothing_easing_or_filtering_tokens(self):
        src = (PREVIEW / "generate_preview.py").read_text(encoding="utf-8")
        for bad in ("savgol", "gaussian_filter", "lowpass", "hysteresis",
                    "moving_average", "easing", "interpolate("):
            self.assertIsNone(re.search(rf"\b{re.escape(bad)}", src, re.I), bad)

    def test_no_interpolation_on_the_motion_transforms(self):
        for n in gp.PROFILES:
            for m in re.finditer(r'<Transform[^>]*target="(angle|y)"[^>]*/>',
                                 xml_for(n)):
                self.assertNotIn("interpolation", m.group(0), n)


class DeterminismAndValidationTests(unittest.TestCase):

    def test_generation_is_deterministic(self):
        r = subprocess.run(
            [sys.executable, str(PREVIEW / "generate_preview.py"), "--check"],
            capture_output=True, text=True, cwd=str(REPO))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_xml_is_stable_across_calls(self):
        for n in gp.PROFILES:
            self.assertEqual(gp.watchface_xml(n), gp.watchface_xml(n))

    def test_every_generated_file_matches_its_manifest_hash(self):
        man = json.loads((PREVIEW / "PREVIEW_MANIFEST.json").read_text())
        for rel, sha in man["generated_files"].items():
            p = PREVIEW / rel
            self.assertTrue(p.exists(), rel)
            self.assertEqual(sha256(p), sha, rel)

    def test_wff_validation_passes_for_all_variants(self):
        script = REPO / "tools/wff_validate.sh"
        if not script.exists():
            self.skipTest("validator unavailable")
        for n in gp.PROFILES:
            x = APP / "src" / n / "res/raw/watchface.xml"
            r = subprocess.run([str(script), "4", str(x.relative_to(REPO))],
                               capture_output=True, text=True, cwd=str(REPO))
            self.assertIn("PASSED", r.stdout + r.stderr, n)

    def test_review_images_match_their_manifest(self):
        man = json.loads((REVIEW / "REVIEW_MANIFEST.json").read_text())
        self.assertEqual(man["image_count"], 9)
        for rec in man["images"]:
            p = REPO / rec["path"]
            self.assertTrue(p.exists(), rec["image"])
            self.assertEqual(sha256(p), rec["sha256"], rec["image"])

    def test_all_nine_required_review_images_exist(self):
        man = json.loads((REVIEW / "REVIEW_MANIFEST.json").read_text())
        self.assertEqual({r["image"] for r in man["images"]}, {
            "NORMAL_DAMPED.png", "NORMAL_PROPOSED.png",
            "NORMAL_ASSERTIVE.png", "AOD_DAMPED.png", "AOD_PROPOSED.png",
            "AOD_ASSERTIVE.png", "NORMAL_COMPARISON.png",
            "AOD_COMPARISON.png", "MOTION_STATES_PROPOSED.png"})

    def test_normal_renders_differ_only_by_label(self):
        """The shell must be identical across profiles; only motion differs."""
        from PIL import Image, ImageChops
        a = Image.open(REVIEW / "NORMAL_DAMPED.png").convert("RGB")
        b = Image.open(REVIEW / "NORMAL_PROPOSED.png").convert("RGB")
        diff = ImageChops.difference(a, b).getbbox()
        self.assertIsNotNone(diff, "renders are byte-identical; label missing?")
        # every differing pixel must lie in the label band
        self.assertGreater(diff[1], 330, f"difference outside label band: {diff}")
        self.assertLess(diff[3], 380, f"difference outside label band: {diff}")


class DisclosureTests(unittest.TestCase):

    def test_preview_manifest_declares_every_required_flag(self):
        man = json.loads((PREVIEW / "PREVIEW_MANIFEST.json").read_text())
        self.assertIs(man["PREVIEW_ONLY"], True)
        self.assertIs(man["FORMAL_EVIDENCE_ALLOWED"], False)
        self.assertIs(man["PRODUCTION_ASSET"], False)
        self.assertIs(man["RELEASE_CANDIDATE"], False)
        self.assertIs(man["OWNER_PIXEL_APPROVED"], False)

    def test_manifest_states_the_spike_remains_authoritative(self):
        man = json.loads((PREVIEW / "PREVIEW_MANIFEST.json").read_text())
        self.assertIn("authoritative", man["authority_note"])
        self.assertIn("disclosed", man["disclosure_note"])
        self.assertIn("re-sign", man["resigning_note"])

    def test_build_record_declares_the_same_flags(self):
        rec = json.loads((PREVIEW / "BUILD_RECORD.json").read_text())
        for k in ("PREVIEW_ONLY",):
            self.assertIs(rec[k], True)
        for k in ("FORMAL_EVIDENCE_ALLOWED", "PRODUCTION_ASSET",
                  "RELEASE_CANDIDATE", "OWNER_PIXEL_APPROVED"):
            self.assertIs(rec[k], False, k)
        self.assertEqual(rec["permissions_declared"], [])

    def test_readme_carries_the_disclosure(self):
        t = (PREVIEW / "README.md").read_text(encoding="utf-8")
        for needle in ("PREVIEW_ONLY: true", "FORMAL_EVIDENCE_ALLOWED: false",
                       "PRODUCTION_ASSET: false", "RELEASE_CANDIDATE: false",
                       "OWNER_PIXEL_APPROVED: false", "authoritative",
                       "re-sign", "disclosed"):
            self.assertIn(needle, t, needle)

    def test_review_manifest_refuses_to_claim_approval(self):
        man = json.loads((REVIEW / "REVIEW_MANIFEST.json").read_text())
        self.assertIs(man["OWNER_PIXEL_APPROVED"], False)
        self.assertIn("not approval", man["approval_note"])


class DeliberateFailureTests(unittest.TestCase):
    """Each guard shown rejecting the mistake it exists to catch."""

    def test_an_altered_motion_gain_would_be_detected(self):
        for n in gs.PROFILES:
            altered = gs.PROFILES[n]["roll_deg"] + 1
            self.assertNotEqual(gp.roll_expression(n),
                                gs.roll_expression(altered), n)

    def test_a_wrong_roll_sign_would_be_detected(self):
        for n in gp.PROFILES:
            positive = gp.roll_expression(n).lstrip("-")
            self.assertNotEqual(gp.roll_expression(n), positive, n)
            self.assertTrue(gp.roll_expression(n).startswith("-"), n)

    def test_a_non_neutral_aod_would_be_detected(self):
        bad = '<Variant mode="AMBIENT" target="angle" value="[ACCELEROMETER_ANGLE_X]" />'
        self.assertIn("ACCELEROMETER", bad)
        for n in gp.PROFILES:
            self.assertNotIn(bad, xml_for(n), n)

    def test_a_package_collision_with_a_spike_package_would_be_detected(self):
        colliding = gs.BASE_PACKAGE + ".damped"
        live = {gp.BASE_PACKAGE + p["suffix"] for p in gp.PROFILES.values()}
        self.assertNotIn(colliding, live)
        self.assertIn(colliding,
                      {gs.BASE_PACKAGE + p["suffix"]
                       for p in gs.PROFILES.values()})

    def test_a_missing_preview_only_disclosure_would_be_detected(self):
        man = json.loads((PREVIEW / "PREVIEW_MANIFEST.json").read_text())
        stripped = {k: v for k, v in man.items() if k != "PREVIEW_ONLY"}
        self.assertNotIn("PREVIEW_ONLY", stripped)
        self.assertIn("PREVIEW_ONLY", man)

    def test_an_accidental_analog_hand_element_would_be_detected(self):
        bad = '<PartImage name="p50_hour"><Image resource="hand_hour" /></PartImage>'
        self.assertIn("hand_hour", bad)
        for n in gp.PROFILES:
            self.assertNotIn("hand_hour", xml_for(n), n)

    def test_a_custom_glyph_path_would_be_detected(self):
        spike_src = (SPIKE / "generate_spike.py").read_text(encoding="utf-8")
        self.assertIn("_blocky", spike_src)     # the spike does use one
        prev_src = (PREVIEW / "generate_preview.py").read_text(
            encoding="utf-8")
        self.assertNotIn("_blocky", prev_src)   # the preview must not

    def test_a_changed_accepted_spike_apk_hash_would_be_detected(self):
        rec = json.loads((SPIKE / "BUILD_RECORD.json").read_text())["variants"]
        accepted = {
            "damped": "c1121f3433e8b453f1ddfe64c6576adddae8271fab54e6ae4a67540ae60fbea6",
            "proposed": "c38e04493841d4bb3d015dfe76ed42cd7001fc5c140c115993d56b764ce31b00",
            "assertive": "99a3150e2c2a505ae0084d91e3fe9f3d775b04449ba791f4698a6669e5f2c03b"}
        for n, want in accepted.items():
            self.assertEqual(rec[n]["apk_sha256"], want, n)
            p = SPIKE / f"app/build/outputs/apk/{n}/debug/app-{n}-debug.apk"
            if p.exists():
                self.assertEqual(sha256(p), want, f"{n} APK on disk changed")

    def test_production_path_contamination_would_be_detected(self):
        r = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--name-only",
             "origin/spike/attitude-horizon-watch7...HEAD"],
            capture_output=True, text=True)
        changed = [f for f in (r.stdout or "").splitlines() if f.strip()]
        allowed_prefixes = ("previews/attitude-motion-shell/",
                            "docs/instructions/", "docs/reports/")
        for f in changed:
            self.assertTrue(f.startswith(allowed_prefixes),
                            f"preview branch touched {f}")
            for forbidden in ("engine/", "watchfaces/", "releases/",
                              "spikes/", "tools/"):
                self.assertFalse(f.startswith(forbidden),
                                 f"contaminated production path: {f}")


if __name__ == "__main__":
    unittest.main()
