"""ATTITUDE — MERIDIAN development face: build gates.

These are the checks the fast-track brief asks for. They are deliberately
behavioural: each one is written so that reverting the thing it protects
makes it fail. Tests that only restate their own source line prove nothing.
"""

import hashlib
import json
import math
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine"))

from wffgen.render import render_face          # noqa: E402
from wffgen.spec import load_spec              # noqa: E402

SLUG = "attitude-meridian"
FACE = REPO / "watchfaces" / SLUG
SPEC = FACE / "engine" / "face.toml"
XML = FACE / "app/src/main/res/raw/watchface.xml"
DRAWABLE = FACE / "app/src/main/res/drawable"
IMPORT = json.loads((FACE / "engine" / "STUDIO_IMPORT.json").read_text())
PACKAGE = "com.xsytrance.attitude.meridian.dev"

# The named development motion profiles, from the studio design contract.
PROFILES = IMPORT["design_contract"]["motion_module"]["profiles"]
DEFAULT_PROFILE = IMPORT["design_contract"]["motion_module"]["default_profile"]
AP = IMPORT["design_contract"]["aperture"]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parts(root):
    return {e.get("name"): e for e in root.iter()
            if e.tag.startswith("Part") and e.get("name")}


class TestPackageIsolation(unittest.TestCase):
    """This build must not be able to collide with anything already shipped
    or with the disposable spike and preview packages."""

    def test_application_id_is_development_namespaced(self):
        gradle = (FACE / "app/build.gradle.kts").read_text()
        self.assertIn(f'applicationId = "{PACKAGE}"', gradle)
        self.assertIn(f'namespace = "{PACKAGE}"', gradle)
        self.assertTrue(PACKAGE.endswith(".dev"))

    def test_application_id_is_unique_across_the_repository(self):
        found = {}
        for g in REPO.glob("watchfaces/*/app/build.gradle.kts"):
            m = re.search(r'applicationId\s*=\s*"([^"]+)"', g.read_text())
            if m:
                found.setdefault(m.group(1), []).append(g.parts[-3])
        self.assertEqual(found.get(PACKAGE), [SLUG],
                         f"{PACKAGE} is not uniquely owned by {SLUG}")
        for pkg, owners in found.items():
            self.assertEqual(len(owners), 1,
                             f"application ID {pkg} claimed by {owners}")

    def test_does_not_reuse_aurelius_spike_or_preview_identity(self):
        forbidden = ("com.xsytrance.aurelius",
                     "com.xsytrance.attitude.spike",
                     "com.xsytrance.attitude.preview")
        for f in forbidden:
            self.assertNotEqual(PACKAGE, f)
            self.assertFalse(PACKAGE.startswith(f + "."), f)


class TestLiveData(unittest.TestCase):
    """Every readout must bind a live WFF source. A face that renders a
    plausible constant is worse than one that renders nothing."""

    REQUIRED = {
        "z20_batt": "[BATTERY_PERCENT]",
        "z21_date": "[DAY]",
        "z22_steps": "[STEP_COUNT]",
        "z23_hr": "[HEART_RATE]",
    }

    def setUp(self):
        self.root = ET.fromstring(XML.read_text())
        self.parts = parts(self.root)

    def test_every_readout_binds_its_live_source(self):
        for name, source in self.REQUIRED.items():
            part = self.parts.get(name)
            self.assertIsNotNone(part, f"missing readout {name}")
            exprs = [p.get("expression") for p in part.iter("Parameter")]
            self.assertTrue(exprs, f"{name} has no Parameter")
            self.assertTrue(any(source in (e or "") for e in exprs),
                            f"{name} does not read {source}: {exprs}")

    def test_no_readout_is_a_constant(self):
        for name in self.REQUIRED:
            for p in self.parts[name].iter("Parameter"):
                expr = p.get("expression") or ""
                self.assertRegex(
                    expr, r"\[[A-Z_0-9]+\]",
                    f"{name} expression {expr!r} contains no data source — "
                    "this is a hard-coded value")

    def test_health_readouts_do_not_substitute_a_plausible_number(self):
        """The established fail-safe for a numeric readout is to show the
        raw source, so an absent or unpermitted sensor reads 0. A ternary
        fallback would print an invented resting heart rate instead."""
        for name in ("z23_hr", "z22_steps"):
            for p in self.parts[name].iter("Parameter"):
                expr = p.get("expression") or ""
                self.assertNotIn("?", expr,
                                 f"{name} substitutes a fallback value: {expr}")

    def test_permissions_are_exactly_those_the_readouts_require(self):
        man = (FACE / "app/src/main/AndroidManifest.xml").read_text()
        declared = set(re.findall(r'uses-permission android:name="([^"]+)"',
                                  man))
        self.assertEqual(declared, {"android.permission.BODY_SENSORS",
                                    "android.permission.ACTIVITY_RECOGNITION"})


class TestMotionModule(unittest.TestCase):
    def setUp(self):
        self.root = ET.fromstring(XML.read_text())
        self.horizon = parts(self.root)["z00_horizon"]
        self.transforms = {t.get("target"): t.get("value")
                           for t in self.horizon.iter("Transform")}

    def test_all_five_named_profiles_are_defined(self):
        self.assertEqual(set(PROFILES),
                         {"damped", "proposed", "assertive", "roll-only",
                          "static"})

    def test_default_is_the_provisional_proposed_profile(self):
        self.assertEqual(DEFAULT_PROFILE, "proposed")
        prof = PROFILES["proposed"]
        self.assertIn(f"{prof['roll_deg']} *", self.transforms["angle"])
        self.assertIn(f"{prof['pitch_px']} *", self.transforms["y"])

    def test_roll_counter_rotates_so_the_horizon_stays_level(self):
        """A positive gain would swing the horizon the same way as the
        wrist, which is the opposite of an attitude indicator."""
        self.assertRegex(self.transforms["angle"], r"^0 - ")

    def test_motion_reads_the_accelerometer_on_both_axes(self):
        self.assertIn("[ACCELEROMETER_ANGLE_X]", self.transforms["angle"])
        self.assertIn("[ACCELEROMETER_ANGLE_Y]", self.transforms["y"])

    def test_pitch_translates_from_the_declared_layout_position(self):
        self.assertTrue(
            self.transforms["y"].startswith(self.horizon.get("y") + " "),
            f"pitch base {self.transforms['y'][:12]!r} is not the layout y")

    def test_changing_the_profile_needs_no_artwork_change(self):
        """Swap in the assertive gains and confirm nothing but the two
        transform values moves. This is the isolation claim, tested."""
        text = SPEC.read_text()
        swapped = (text.replace("roll_gain_deg = 22.0", "roll_gain_deg = 30.0")
                       .replace("pitch_gain_px = 26.0", "pitch_gain_px = 34.0"))
        self.assertNotEqual(text, swapped)
        tmp = SPEC.parent / ".profile_swap_test.toml"
        try:
            tmp.write_text(swapped)
            other = ET.fromstring(render_face(load_spec(tmp)))
        finally:
            tmp.unlink(missing_ok=True)
        base_parts, other_parts = parts(self.root), parts(other)
        self.assertEqual(set(base_parts), set(other_parts))
        differing = set()
        for name in base_parts:
            a = ET.tostring(base_parts[name])
            b = ET.tostring(other_parts[name])
            if a != b:
                differing.add(name)
        self.assertEqual(differing, {"z00_horizon"},
                         "changing the motion profile disturbed layers other "
                         "than the horizon field")
        res_a = {e.get("resource") for e in self.root.iter("Image")}
        res_b = {e.get("resource") for e in other.iter("Image")}
        self.assertEqual(res_a, res_b, "profile change altered resources")


class TestAmbient(unittest.TestCase):
    def setUp(self):
        self.root = ET.fromstring(XML.read_text())
        self.parts = parts(self.root)

    def _ambient_alpha(self, name):
        v = self.parts[name].find("Variant")
        return int(v.get("value"))

    def test_the_moving_horizon_is_hidden_in_ambient(self):
        self.assertEqual(self._ambient_alpha("z00_horizon"), 0)

    def test_a_frozen_ambient_horizon_replaces_it(self):
        aod = self.parts["z01_horizon_aod"]
        self.assertEqual(aod.get("alpha"), "0")
        self.assertEqual(self._ambient_alpha("z01_horizon_aod"), 255)
        self.assertEqual([t.get("target") for t in aod.iter("Transform")], [],
                         "the ambient horizon carries a transform — it must "
                         "be frozen")

    def test_no_ambient_layer_reads_the_accelerometer(self):
        """Neutral AOD motion is structural: anything visible in ambient
        must carry no sensor-driven transform at all."""
        for name, part in self.parts.items():
            if self._ambient_alpha(name) == 0:
                continue
            for t in part.iter("Transform"):
                self.assertNotIn("ACCELEROMETER", t.get("value") or "",
                                 f"{name} is visible in AOD and moves with "
                                 "the wrist")

    def test_no_seconds_animation_in_ambient(self):
        self.assertEqual(self._ambient_alpha("z32_second"), 0)

    def test_hands_are_the_brightest_ambient_layer(self):
        hands = max(self._ambient_alpha(n)
                    for n in ("z34_hour_aod", "z35_minute_aod"))
        others = [self._ambient_alpha(n) for n in self.parts
                  if n not in ("z34_hour_aod", "z35_minute_aod")
                  and self._ambient_alpha(n) > 0]
        self.assertTrue(all(a <= hands for a in others),
                        f"an ambient layer is brighter than the hands: "
                        f"{others} vs {hands}")

    def test_ambient_time_is_still_readable(self):
        for n in ("z34_hour_aod", "z35_minute_aod"):
            targets = [t.get("target") for t in self.parts[n].iter("Transform")]
            self.assertIn("angle", targets, f"{n} does not tell the time")


class TestStudioAssets(unittest.TestCase):
    def test_every_drawable_matches_the_studio_export_hash(self):
        for name, meta in IMPORT["resources"].items():
            p = DRAWABLE / name
            self.assertTrue(p.exists(), f"missing drawable {name}")
            self.assertEqual(sha256(p), meta["sha256"],
                             f"{name} differs from the studio export")

    def test_no_drawable_exists_outside_the_studio_export(self):
        on_disk = {p.name for p in DRAWABLE.iterdir() if p.is_file()}
        self.assertEqual(on_disk, set(IMPORT["resources"]),
                         "res/drawable contains art the studio did not export")

    def test_every_referenced_resource_is_a_recorded_studio_asset(self):
        root = ET.fromstring(XML.read_text())
        referenced = {e.get("resource") for e in root.iter()
                      if e.get("resource")}
        available = {Path(n).stem for n in IMPORT["resources"]}
        self.assertEqual(referenced - available, set())

    def test_readout_boxes_match_the_studio_layout_contract(self):
        """The studio renders the owner reviewed and the installed face must
        place the readouts identically."""
        root = ET.fromstring(XML.read_text())
        p = parts(root)
        by_key = {"battery": "z20_batt", "date": "z21_date",
                  "steps": "z22_steps", "hr": "z23_hr"}
        for key, name in by_key.items():
            want = IMPORT["readouts"][key]
            got = [int(p[name].get(a)) for a in ("x", "y", "width", "height")]
            self.assertEqual(got, list(want["box"]), f"{key} box drifted")
            size = p[name].find(".//BitmapFont").get("size")
            self.assertEqual(int(size), want["size"], f"{key} size drifted")


class TestGeometry(unittest.TestCase):
    """Pixel checks on the shipped art, not on a re-derivation of it."""

    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("Pillow not available")
        cls.Image = Image
        root = ET.fromstring(XML.read_text())
        cls.parts = parts(root)

    def test_the_plate_covers_everything_except_the_aperture(self):
        with self.Image.open(DRAWABLE / "meridian_dial.png") as im:
            a = im.convert("RGBA").getchannel("A")
            leaks = [(x, y) for y in range(im.height) for x in range(im.width)
                     if a.getpixel((x, y)) < 255
                     and math.hypot(x - AP["cx"], y - AP["cy"]) > AP["r"] + 1]
        self.assertEqual(leaks, [], f"{len(leaks)} uncovered plate pixels")

    def test_no_uncovered_horizon_pixels_at_the_proposed_extremes(self):
        """At every supported extreme of the default profile the field must
        still fill the aperture, or the porthole shows dial through it."""
        with self.Image.open(DRAWABLE / "meridian_horizon.png") as im:
            fw, fh = im.size
        box = self.parts["z00_horizon"]
        fx, fy = int(box.get("x")), int(box.get("y"))
        prof = PROFILES[DEFAULT_PROFILE]
        for roll in (-prof["roll_deg"], 0.0, prof["roll_deg"]):
            for pitch in (-prof["pitch_px"], 0.0, prof["pitch_px"]):
                cx, cy = fx + fw / 2, fy + fh / 2 + pitch
                # rotation about the field centre does not change the radius
                # of the inscribed disc, so the covered region is a circle
                covered_r = min(fw, fh) / 2
                worst = math.hypot(AP["cx"] - cx, AP["cy"] - cy) + AP["r"]
                self.assertLessEqual(
                    worst, covered_r,
                    f"aperture uncovered at roll {roll}, pitch {pitch}: "
                    f"needs {worst:.1f}px, field gives {covered_r:.1f}px")

    def test_the_aperture_is_where_the_design_contract_says(self):
        """The chamfer is drawn over the rim of the punched hole, so the
        visible opening is slightly smaller than the geometric radius. It
        must be centred exactly and must not be materially smaller."""
        with self.Image.open(DRAWABLE / "meridian_dial.png") as im:
            a = im.convert("RGBA").getchannel("A")
            clear = [(x, y) for y in range(im.height) for x in range(im.width)
                     if a.getpixel((x, y)) == 0]
        xs, ys = [p[0] for p in clear], [p[1] for p in clear]
        self.assertAlmostEqual((min(xs) + max(xs)) / 2, AP["cx"], delta=1.5)
        self.assertAlmostEqual((min(ys) + max(ys)) / 2, AP["cy"], delta=1.5)
        visible_r = (max(xs) - min(xs)) / 2
        self.assertLessEqual(visible_r, AP["r"] + 1.5,
                             "the opening is larger than the declared "
                             "aperture — coverage maths would be optimistic")
        self.assertGreaterEqual(visible_r, AP["r"] - 4,
                                f"the chamfer has eaten the aperture: "
                                f"visible r={visible_r}, declared {AP['r']}")
        self.assertIn("chamfer", IMPORT["design_contract"]["aperture_note"])


class TestRenderedFromXml(unittest.TestCase):
    """Checks against the shipped artefacts — the committed XML and the
    drawables that go into the APK — not against the design generator."""

    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("Pillow not available")
        sys.path.insert(0, str(FACE / "tools"))
        import render_from_xml
        cls.R = render_from_xml
        cls.root = ET.fromstring(XML.read_text())
        cls.font = render_from_xml.Font(cls.root)

    def _render(self, ambient=False, **env):
        return self.R.compose(self.root, self.font,
                              dict(self.R.FIXTURE_ENV, **env), ambient)

    def test_the_face_composes_from_the_committed_xml(self):
        img = self._render()
        self.assertEqual(img.size, (480, 480))
        self.assertGreater(len(img.getcolors(maxcolors=1 << 20) or []), 500,
                           "the composed face is nearly featureless")

    def test_nothing_escapes_the_case_at_any_motion_extreme(self):
        """The regression that mattered: at pitch extremes the oversized
        horizon field once escaped past the case into the canvas corners."""
        corner = 26
        for rx in (-45.0, 0.0, 45.0):
            for ry in (-40.0, 0.0, 40.0):
                img = self._render(ACCELEROMETER_ANGLE_X=rx,
                                   ACCELEROMETER_ANGLE_Y=ry)
                px = img.load()
                for cx, cy in ((0, 0), (479, 0), (0, 479), (479, 479)):
                    for dx in range(corner):
                        for dy in range(corner):
                            x = cx + (dx if cx == 0 else -dx)
                            y = cy + (dy if cy == 0 else -dy)
                            self.assertEqual(
                                px[x, y], (0, 0, 0),
                                f"content at ({x},{y}) with wrist "
                                f"({rx},{ry}) — the horizon field has "
                                "escaped the case")

    def test_the_aperture_is_never_uncovered_at_any_supported_extreme(self):
        """Compose the moving field ALONE and require that it fills the
        aperture at every supported wrist extreme.

        Everything else is skipped deliberately. The plate cannot stand in
        for the field — it draws the fixed aircraft datum inside the
        aperture, in black, so a composition including it would mask a real
        coverage hole behind legitimate black pixels."""
        others = {p.get("name") for p in self.root.find("Scene")
                  if p.get("name") != "z00_horizon"}
        prof = PROFILES[DEFAULT_PROFILE]
        r = AP["r"] - 2
        for rx in (-45.0, -22.5, 0.0, 22.5, 45.0):
            for ry in (-40.0, -20.0, 0.0, 20.0, 40.0):
                img = self.R.compose(
                    self.root, self.font,
                    dict(self.R.FIXTURE_ENV, ACCELEROMETER_ANGLE_X=rx,
                         ACCELEROMETER_ANGLE_Y=ry), False, skip=others).load()
                bare = [(x, y)
                        for y in range(AP["cy"] - r, AP["cy"] + r + 1)
                        for x in range(AP["cx"] - r, AP["cx"] + r + 1)
                        if math.hypot(x - AP["cx"], y - AP["cy"]) <= r
                        and img[x, y] == (0, 0, 0)]
                self.assertEqual(
                    bare, [],
                    f"{len(bare)} uncovered aperture pixels at wrist "
                    f"({rx},{ry}) — profile {DEFAULT_PROFILE} "
                    f"(±{prof['roll_deg']}°, ±{prof['pitch_px']}px)")

    def test_ambient_render_is_identical_at_every_wrist_angle(self):
        neutral = self._render(ambient=True).tobytes()
        for rx, ry in ((-45.0, -40.0), (45.0, 40.0), (30.0, -25.0)):
            moved = self._render(ambient=True, ACCELEROMETER_ANGLE_X=rx,
                                 ACCELEROMETER_ANGLE_Y=ry).tobytes()
            self.assertEqual(neutral, moved,
                             f"ambient render changed at wrist ({rx},{ry})")

    def test_live_values_actually_reach_the_dial(self):
        """Change every data source and require the pixels to change, so a
        readout silently bound to nothing cannot pass."""
        base = self._render().tobytes()
        for source, value in (("DAY", 8), ("BATTERY_PERCENT", 12),
                              ("STEP_COUNT", 33), ("HEART_RATE", 155)):
            other = self._render(**{source: value}).tobytes()
            self.assertNotEqual(base, other,
                                f"changing [{source}] changed no pixel")

    def test_review_images_match_their_recorded_hashes(self):
        r = subprocess.run([sys.executable,
                            str(FACE / "tools/render_from_xml.py"), "--check"],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestHandCollisions(unittest.TestCase):
    """Reviewed hand positions: no readout may be buried by the hands."""

    TIMES = [(10, 9, 30), (12, 0, 0), (3, 15, 15), (6, 30, 45), (8, 40, 20)]
    MAX_COVERED = 0.75

    @classmethod
    def setUpClass(cls):
        studio = Path.home() / "AGENOR-Horology" / "scripts"
        if not (studio / "meridian_v1.py").exists():
            raise unittest.SkipTest("studio repository not available")
        sys.path.insert(0, str(studio))
        try:
            import meridian_v1
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("studio generator not importable")
        cls.M = meridian_v1
        cls.base = meridian_v1.compose(0, 0, 0, seconds=False)

    def test_no_readout_is_buried_at_any_reviewed_position(self):
        M = self.M
        regions = {"date": (M.DATE_C, 20),
                   "steps": (M.SUB_STEPS, M.SUB_R - 8),
                   "heart rate": (M.SUB_HR, M.SUB_R - 8)}
        for hh, mm, ss in self.TIMES:
            img = M.compose(hh, mm, ss)
            for label, (c, r) in regions.items():
                box = (c[0] - r, c[1] - r, c[0] + r, c[1] + r)
                a, b = img.crop(box), self.base.crop(box)
                diff = sum(1 for p, q in zip(a.getdata(), b.getdata())
                           if p != q)
                frac = diff / (a.width * a.height)
                self.assertLess(
                    frac, self.MAX_COVERED,
                    f"{label} is {frac:.0%} covered at {hh:02d}:{mm:02d}")


class TestBuildConfiguration(unittest.TestCase):
    def setUp(self):
        self.gradle = (FACE / "app/build.gradle.kts").read_text()
        self.root_gradle = (FACE / "build.gradle.kts").read_text()

    def test_no_release_signing_configuration(self):
        for token in ("signingConfig", "signingConfigs", "storeFile",
                      "storePassword", "keyAlias", "keyPassword"):
            self.assertNotIn(token, self.gradle, f"{token} present")

    def test_no_bundle_or_store_configuration(self):
        for token in ("bundle {", "android.bundle", "playConsole",
                      "publishing {", "com.google.gms"):
            self.assertNotIn(token, self.gradle + self.root_gradle, token)

    def test_no_release_artifacts_are_produced_or_committed(self):
        out = FACE / "app/build/outputs"
        if out.exists():
            self.assertEqual(list(out.rglob("*.aab")), [])
            self.assertEqual(list(out.rglob("*-release*.apk")), [])
        self.assertEqual(list(FACE.rglob("*.jks")), [])
        self.assertEqual(list(FACE.rglob("*.keystore")), [])

    def test_the_face_is_not_registered_as_a_release_candidate(self):
        releases = REPO / "releases"
        if releases.exists():
            hits = [p for p in releases.rglob("*") if SLUG in p.name
                    or "meridian" in p.name.lower()]
            self.assertEqual(hits, [], f"release entries exist: {hits}")

    def test_the_apk_carries_the_android_debug_certificate(self):
        """Modern v2/v3 signing puts nothing in META-INF, so ask apksigner
        who signed it rather than guessing from the zip listing."""
        apk = FACE / "app/build/outputs/apk/debug/app-debug.apk"
        if not apk.exists():
            self.skipTest("APK not built in this working tree")
        sdk = Path.home() / "Android/Sdk/build-tools"
        tools = sorted(sdk.glob("*/apksigner")) if sdk.exists() else []
        jbr = Path.home() / "Android/android-studio/jbr"
        if not tools or not jbr.exists():
            self.skipTest("apksigner not available")
        import os
        env = dict(os.environ, JAVA_HOME=str(jbr),
                   PATH=f"{jbr / 'bin'}:{os.environ.get('PATH', '')}")
        r = subprocess.run([str(tools[-1]), "verify", "--print-certs",
                            str(apk)], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("CN=Android Debug", r.stdout)
        self.assertNotIn("O=xsytrance", r.stdout,
                         "the APK is signed with a production key")


class TestNoCollateralChange(unittest.TestCase):
    """This branch must not disturb Aurelius or the accepted spike."""

    def _changed_files(self):
        r = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only",
                            "main...HEAD"], capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("cannot diff against main")
        return [f for f in r.stdout.splitlines() if f]

    def test_no_aurelius_change(self):
        touched = [f for f in self._changed_files()
                   if f.startswith("watchfaces/aurelius/")
                   or "/aurelius/" in f]
        self.assertEqual(touched, [], f"Aurelius touched: {touched}")

    def test_no_spike_or_preview_change(self):
        touched = [f for f in self._changed_files()
                   if f.startswith(("spikes/", "previews/"))]
        self.assertEqual(touched, [], f"spike/preview touched: {touched}")


class TestGeneratedXmlIsCurrent(unittest.TestCase):
    def test_committed_xml_matches_the_spec(self):
        r = subprocess.run([sys.executable, "tools/generate_face.py", SLUG,
                            "--check"], cwd=REPO, capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_generation_is_deterministic(self):
        spec = load_spec(SPEC)
        self.assertEqual(render_face(spec), render_face(load_spec(SPEC)))

    def test_the_studio_import_record_still_matches_the_studio(self):
        tool = FACE / "tools/import_studio_export.py"
        r = subprocess.run([sys.executable, str(tool), "--check"], cwd=REPO,
                           capture_output=True, text=True)
        if "studio export not found" in r.stderr:
            self.skipTest("studio repository not available")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
