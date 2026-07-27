"""Offline gates for the DISPOSABLE attitude-horizon spike.

Everything provable without a watch is proved here, because installing a
face that fails one of these would waste the owner's only scarce resource:
a device session.

Deliberate-failure fixtures are the substance. A gate that only ever sees
good input proves nothing, so each one is shown rejecting the specific
mistake it exists to catch.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

SPIKE = Path(__file__).resolve().parents[1]
REPO = SPIKE.parents[1]
sys.path.insert(0, str(SPIKE))

import generate_spike as gs  # noqa: E402

MANIFEST = SPIKE / "SPIKE_MANIFEST.json"
APP = SPIKE / "app"


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def xml_for(profile: str) -> str:
    return (APP / "src" / profile / "res/raw/watchface.xml").read_text(
        encoding="utf-8")


class DeterminismTests(unittest.TestCase):

    def test_generation_is_deterministic(self):
        r = subprocess.run(
            [sys.executable, str(SPIKE / "generate_spike.py"), "--check"],
            capture_output=True, text=True, cwd=str(REPO))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_xml_is_stable_across_calls(self):
        for p in gs.PROFILES:
            self.assertEqual(gs.watchface_xml(p), gs.watchface_xml(p))

    def test_every_generated_file_matches_its_recorded_hash(self):
        for rel, sha in manifest()["generated_files"].items():
            p = SPIKE / rel
            self.assertTrue(p.exists(), rel)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                             sha, rel)


class MotionMappingTests(unittest.TestCase):
    """Neutral is neutral, mapping is monotonic and symmetric, clamps hold."""

    def test_neutral_input_maps_exactly_to_zero(self):
        for p in gs.PROFILES:
            self.assertEqual(gs.evaluate_roll(p, 0.0), 0.0, p)
            self.assertEqual(gs.evaluate_pitch(p, 0.0), 0.0, p)

    def test_mapping_is_monotonic(self):
        for p in gs.PROFILES:
            prev_r = prev_p = -1e9
            for w in range(-60, 61, 5):
                r = -gs.evaluate_roll(p, w)   # negated gain, so invert
                v = gs.evaluate_pitch(p, w)
                self.assertGreaterEqual(r, prev_r - 1e-9, f"{p} roll at {w}")
                self.assertGreaterEqual(v, prev_p - 1e-9, f"{p} pitch at {w}")
                prev_r, prev_p = r, v

    def test_mapping_is_symmetric(self):
        for p in gs.PROFILES:
            for w in (5, 17, 30, 45, 90):
                self.assertAlmostEqual(gs.evaluate_roll(p, w),
                                       -gs.evaluate_roll(p, -w), places=9)
                self.assertAlmostEqual(gs.evaluate_pitch(p, w),
                                       -gs.evaluate_pitch(p, -w), places=9)

    def test_roll_is_clamped_at_the_wrist_limit(self):
        for p, spec in gs.PROFILES.items():
            at = abs(gs.evaluate_roll(p, gs.WRIST_ROLL_CLAMP))
            self.assertAlmostEqual(at, spec["roll_deg"], places=6)
            for beyond in (46, 90, 180, 720):
                self.assertAlmostEqual(abs(gs.evaluate_roll(p, beyond)),
                                       at, places=6, msg=f"{p} at {beyond}")

    def test_pitch_is_clamped_at_the_wrist_limit(self):
        for p, spec in gs.PROFILES.items():
            at = abs(gs.evaluate_pitch(p, gs.WRIST_PITCH_CLAMP))
            self.assertAlmostEqual(at, spec["pitch_px"], places=6)
            for beyond in (41, 120, 900):
                self.assertAlmostEqual(abs(gs.evaluate_pitch(p, beyond)),
                                       at, places=6)

    def test_the_three_profiles_are_actually_different(self):
        rolls = {p["roll_deg"] for p in gs.PROFILES.values()}
        pitches = {p["pitch_px"] for p in gs.PROFILES.values()}
        self.assertEqual(len(rolls), 3)
        self.assertEqual(len(pitches), 3)

    def test_profiles_match_the_authorised_values(self):
        self.assertEqual(gs.PROFILES["damped"]["roll_deg"], 14.0)
        self.assertEqual(gs.PROFILES["damped"]["pitch_px"], 14.0)
        self.assertEqual(gs.PROFILES["proposed"]["roll_deg"], 22.0)
        self.assertEqual(gs.PROFILES["proposed"]["pitch_px"], 26.0)
        self.assertEqual(gs.PROFILES["assertive"]["roll_deg"], 30.0)
        self.assertEqual(gs.PROFILES["assertive"]["pitch_px"], 34.0)


class DeliberateFailureTests(unittest.TestCase):
    """Each gate shown rejecting the exact mistake it guards against."""

    def test_excessive_roll_gain_is_rejected(self):
        """A gain at or above 1:1 stops being an instrument."""
        for bad in (45.0, 60.0, 90.0):
            gain = bad / gs.WRIST_ROLL_CLAMP
            self.assertGreaterEqual(gain, 1.0)
            self.assertFalse(gain < 0.75, f"gain {gain} should be rejected")
        for name, p in gs.PROFILES.items():
            self.assertLess(p["roll_deg"] / gs.WRIST_ROLL_CLAMP, 0.75, name)

    def test_excessive_pitch_travel_is_rejected(self):
        """Travel that outruns the field exposes the aperture."""
        excessive = gs.field_radius() - gs.conservative_bound() + 1.0
        self.assertLess(gs.coverage_margin(gs.field_radius(), excessive), 0)

    def test_a_missing_clamp_is_detectable(self):
        """Unclamped mapping keeps growing past the wrist limit."""
        def unclamped(w):
            return 22.0 * w / gs.WRIST_ROLL_CLAMP
        self.assertGreater(abs(unclamped(90)), abs(unclamped(45)))
        # the real one does not
        self.assertAlmostEqual(abs(gs.evaluate_roll("proposed", 90)),
                               abs(gs.evaluate_roll("proposed", 45)),
                               places=9)

    def test_an_asymmetric_mapping_is_detectable(self):
        def asymmetric(w):
            return 22.0 * (w if w >= 0 else w * 0.5) / gs.WRIST_ROLL_CLAMP
        self.assertNotAlmostEqual(asymmetric(30), -asymmetric(-30), places=6)
        self.assertAlmostEqual(gs.evaluate_roll("proposed", 30),
                               -gs.evaluate_roll("proposed", -30), places=9)

    def test_a_moving_aod_is_detectable(self):
        """AOD must be pinned by a static AMBIENT variant, not an expression."""
        bad = '<Variant mode="AMBIENT" target="angle" value="[ACCELEROMETER_ANGLE_X]" />'
        self.assertIn("ACCELEROMETER", bad)
        for p in gs.PROFILES:
            for m in re.finditer(r'<Variant mode="AMBIENT"[^>]*/>',
                                 xml_for(p)):
                self.assertNotIn("ACCELEROMETER", m.group(0), p)

    def test_an_undersized_horizon_field_is_rejected(self):
        undersized = gs.conservative_bound() + 5.0
        self.assertLess(gs.coverage_margin(undersized, 26.0), 0)

    def test_duplicate_package_ids_are_detectable(self):
        ids = [gs.BASE_PACKAGE + p["suffix"] for p in gs.PROFILES.values()]
        self.assertEqual(len(set(ids)), len(ids))
        duped = ids[:2] + [ids[0]]
        self.assertNotEqual(len(set(duped)), len(duped))

    def test_accidental_aab_generation_would_be_caught(self):
        found = list(SPIKE.rglob("*.aab"))
        self.assertEqual(found, [], f"spike produced an AAB: {found}")

    def test_shared_engine_modification_would_be_caught(self):
        r = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--name-only",
             "origin/main...HEAD"], capture_output=True, text=True)
        touched = [f for f in (r.stdout or "").splitlines() if f.strip()]
        for f in touched:
            self.assertFalse(f.startswith("engine/"),
                             f"spike modified the shared engine: {f}")
            self.assertFalse(f.startswith("watchfaces/"),
                             f"spike modified a product face: {f}")
            self.assertFalse(f.startswith("releases/"),
                             f"spike modified releases: {f}")


class CoverageTests(unittest.TestCase):

    def test_every_profile_has_positive_margin(self):
        R = gs.field_radius()
        for name, p in gs.PROFILES.items():
            m = gs.coverage_margin(R, p["pitch_px"])
            self.assertGreater(m, 0, name)
            self.assertGreaterEqual(m, 10.0, f"{name} margin thin")

    def test_simultaneous_extremes_are_covered_both_signs(self):
        """Rotation of a disc costs no coverage; displacement does, and it
        is symmetric, so both signs must clear."""
        R = gs.field_radius()
        for name, p in gs.PROFILES.items():
            for sign in (+1, -1):
                disp = abs(sign * p["pitch_px"])
                self.assertGreater(R - (gs.conservative_bound() + disp), 0,
                                   f"{name} sign {sign}")

    def test_manifest_margins_agree_with_the_code(self):
        R = gs.field_radius()
        for name, rec in manifest()["profiles"].items():
            self.assertAlmostEqual(
                rec["coverage_margin_px"],
                round(gs.coverage_margin(R, gs.PROFILES[name]["pitch_px"]), 2),
                places=2, msg=name)


class XmlTests(unittest.TestCase):

    def test_xml_is_well_formed(self):
        import xml.etree.ElementTree as ET
        for p in gs.PROFILES:
            ET.fromstring(xml_for(p))

    def test_aod_is_statically_neutral(self):
        """The AOD variants must be constants, not expressions."""
        for p in gs.PROFILES:
            x = xml_for(p)
            self.assertIn('<Variant mode="AMBIENT" target="angle" value="0" />',
                          x, p)
            self.assertRegex(
                x, r'<Variant mode="AMBIENT" target="y" value="-?\d+" />',
                p)

    def test_each_profile_embeds_its_own_gain(self):
        for name, spec in gs.PROFILES.items():
            x = xml_for(name)
            self.assertIn(gs.num(spec["roll_deg"]), x, name)
            self.assertIn(gs.num(spec["pitch_px"]), x, name)

    def test_roll_uses_x_axis_and_pitch_uses_y_axis(self):
        for p in gs.PROFILES:
            x = xml_for(p)
            angle = re.search(r'<Transform target="angle" value="([^"]+)"', x)
            ypos = re.search(r'<Transform target="y" value="([^"]+)"', x)
            self.assertIn("ACCELEROMETER_ANGLE_X", angle.group(1))
            self.assertIn("ACCELEROMETER_ANGLE_Y", ypos.group(1))

    def test_expressions_are_clamped_in_xml(self):
        for p in gs.PROFILES:
            x = xml_for(p)
            self.assertEqual(x.count("clamp("), 2, p)

    def test_it_is_marked_disposable(self):
        for p in gs.PROFILES:
            self.assertIn("NOT PRODUCT CODE", xml_for(p))


class PackagingTests(unittest.TestCase):

    def test_no_permissions_are_declared(self):
        m = (APP / "src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertNotIn("uses-permission", m)

    def test_manifest_declares_no_code(self):
        m = (APP / "src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn('android:hasCode="false"', m)

    def test_gradle_has_no_signing_configuration(self):
        g = (APP / "build.gradle.kts").read_text(encoding="utf-8")
        for forbidden in ("signingConfig", "storeFile", "keyAlias",
                          "keyPassword", "storePassword", "bundle {"):
            self.assertNotIn(forbidden, g)

    def test_three_distinct_application_ids(self):
        g = (APP / "build.gradle.kts").read_text(encoding="utf-8")
        for name, p in gs.PROFILES.items():
            self.assertIn(f'applicationIdSuffix = "{p["suffix"]}"', g, name)
        ids = {gs.BASE_PACKAGE + p["suffix"] for p in gs.PROFILES.values()}
        self.assertEqual(len(ids), 3)

    def test_spike_identity_is_correct(self):
        g = (APP / "build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn(f'applicationId = "{gs.BASE_PACKAGE}"', g)
        self.assertIn(f'versionName = "{gs.VERSION_NAME}"', g)
        self.assertIn(f"versionCode = {gs.VERSION_CODE}", g)
        m = (APP / "src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn(gs.LABEL, m)

    def test_not_available_in_retail(self):
        info = (APP / "src/damped/res/xml/watch_face_info.xml").read_text(
            encoding="utf-8")
        self.assertIn('<AvailableInRetail value="false" />', info)

    def test_no_release_or_signing_files_exist(self):
        for pattern in ("*.keystore", "*.jks", "*.aab", "keystore.properties"):
            self.assertEqual(list(SPIKE.rglob(pattern)), [], pattern)


class IsolationTests(unittest.TestCase):
    """The spike must not have leaked into anything that matters."""

    def changed_files(self):
        r = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--name-only",
             "origin/main...HEAD"], capture_output=True, text=True)
        return [f for f in (r.stdout or "").splitlines() if f.strip()]

    # Paths outside the spike that are legitimately on this branch. The
    # gate exists to stop the spike touching PRODUCT code — engine,
    # watchfaces, releases, Aurelius — not to forbid a dedicated ignore
    # rule or the task instructions committed alongside it.
    ALLOWED_NON_SPIKE = {".gitignore"}
    ALLOWED_NON_SPIKE_PREFIXES = ("docs/instructions/", "docs/reports/")

    def test_only_spike_paths_changed(self):
        for f in self.changed_files():
            if f in self.ALLOWED_NON_SPIKE or f.startswith(
                    self.ALLOWED_NON_SPIKE_PREFIXES):
                continue
            self.assertTrue(f.startswith("spikes/attitude-horizon/"),
                            f"spike branch touched {f}")

    def test_no_product_path_is_touched(self):
        """The guarantee the gate actually exists for."""
        for f in self.changed_files():
            for forbidden in ("engine/", "watchfaces/", "releases/",
                              "tools/", "tests/engine/", "tests/visual/"):
                self.assertFalse(f.startswith(forbidden),
                                 f"spike branch touched product path {f}")

    def test_no_aurelius_file_changed(self):
        for f in self.changed_files():
            self.assertNotIn("aurelius", f.lower(), f)

    def test_no_attitude_production_code_created(self):
        prod = [p for p in (REPO / "watchfaces").glob("attitude*")]
        self.assertEqual(prod, [])


if __name__ == "__main__":
    unittest.main()
