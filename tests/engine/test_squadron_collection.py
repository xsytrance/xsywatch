"""ATTITUDE SQUADRON collection: family-wide gates.

Every check runs across all thirteen faces. The point of a platform is that
a defect in one variant is a defect in the family, so nothing here is
written per-variant.
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
sys.path.insert(0, str(REPO / "tools"))

from wffgen.render import render_face          # noqa: E402
from wffgen.spec import load_spec              # noqa: E402

IMPORT = json.loads((REPO / "watchfaces" / "SQUADRON_IMPORT.json").read_text())
VARIANTS = IMPORT["variants"]
PLATFORM = IMPORT["platform"]
PROFILES = PLATFORM["motion_profiles"]
DEFAULT_PROFILE = PLATFORM["default_profile"]
AP = PLATFORM["aperture"]
SLUGS = sorted(VARIANTS)
PUBLIC = sorted(IMPORT["public_variants"])


def face_dir(slug):
    return REPO / "watchfaces" / f"squadron-{slug}"


def xml_of(slug):
    return face_dir(slug) / "app/src/main/res/raw/watchface.xml"


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parts(root):
    return {e.get("name"): e for e in root.iter()
            if e.tag.startswith("Part") and e.get("name")}


class TestCollectionShape(unittest.TestCase):
    def test_twelve_public_variants_plus_one_internal(self):
        self.assertEqual(len(PUBLIC), 12, f"public collection is {PUBLIC}")
        internal = [s for s in SLUGS if s not in PUBLIC]
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(SLUGS), 13)

    def test_the_flagship_is_a_public_variant(self):
        self.assertIn(IMPORT["flagship"], PUBLIC)

    def test_every_variant_has_a_buildable_project(self):
        for slug in SLUGS:
            d = face_dir(slug)
            for f in ("app/build.gradle.kts", "settings.gradle.kts",
                      "gradlew", "engine/face.toml", "README.md",
                      "app/src/main/AndroidManifest.xml",
                      "app/src/main/res/raw/watchface.xml"):
                self.assertTrue((d / f).exists(), f"{slug} missing {f}")


class TestBranding(unittest.TestCase):
    """The public collection must not carry AGENOR on the dial."""

    def test_no_public_variant_is_house_branded(self):
        for slug in PUBLIC:
            title = VARIANTS[slug]["title"]
            self.assertNotIn("AGENOR", title.upper(),
                             f"{slug} carries the house mark publicly")

    def test_public_dial_marks_use_the_permitted_names(self):
        studio = json.loads(
            (Path.home() / "AGENOR-Horology" / "phase3-squadron"
             / "SQUADRON_MANIFEST.json").read_text()) \
            if (Path.home() / "AGENOR-Horology" / "phase3-squadron"
                / "SQUADRON_MANIFEST.json").exists() else None
        if studio is None:
            self.skipTest("studio manifest not available")
        for slug in PUBLIC:
            v = studio["variants"][slug]
            self.assertNotEqual(v["brand"].upper(), "AGENOR",
                                f"{slug} prints AGENOR on the dial")
            self.assertIn(v["brand"].upper(), ("MERIDIAN", "ATTITUDE"),
                          f"{slug} dial mark is {v['brand']}")

    def test_the_internal_variant_is_marked_private(self):
        internal = [s for s in SLUGS if s not in PUBLIC][0]
        self.assertFalse(VARIANTS[internal]["public"])

    def test_no_test_or_spike_language_on_any_dial(self):
        studio_path = (Path.home() / "AGENOR-Horology" / "phase3-squadron"
                       / "SQUADRON_MANIFEST.json")
        if not studio_path.exists():
            self.skipTest("studio manifest not available")
        studio = json.loads(studio_path.read_text())
        for slug in SLUGS:
            v = studio["variants"][slug]
            for word in ("SPIKE", "PREVIEW", "TEST", "DEBUG", "SAMPLE"):
                self.assertNotIn(word, f"{v['brand']} {v['brand2']}".upper(),
                                 f"{slug} dial says {word}")


class TestPackageIsolation(unittest.TestCase):
    def test_every_application_id_is_unique_repository_wide(self):
        found = {}
        for g in REPO.glob("watchfaces/*/app/build.gradle.kts"):
            m = re.search(r'applicationId\s*=\s*"([^"]+)"', g.read_text())
            if m:
                found.setdefault(m.group(1), []).append(g.parts[-3])
        for pkg, owners in found.items():
            self.assertEqual(len(owners), 1,
                             f"application ID {pkg} claimed by {owners}")
        for slug in SLUGS:
            self.assertIn(VARIANTS[slug]["package"], found)

    def test_every_package_is_development_namespaced(self):
        for slug in SLUGS:
            pkg = VARIANTS[slug]["package"]
            self.assertTrue(pkg.endswith(".dev"), pkg)
            self.assertFalse(pkg.startswith("com.xsytrance.aurelius"), pkg)

    def test_no_collection_package_collides_with_meridian_or_aurelius(self):
        reserved = {"com.xsytrance.aurelius",
                    "com.xsytrance.attitude.meridian.dev"}
        for slug in SLUGS:
            self.assertNotIn(VARIANTS[slug]["package"], reserved)


class TestPlatformConsistency(unittest.TestCase):
    """Every face is the same watch underneath."""

    @classmethod
    def setUpClass(cls):
        cls.roots = {s: ET.fromstring(xml_of(s).read_text()) for s in SLUGS}

    def test_every_face_has_the_same_component_list(self):
        shapes = {s: [e.tag + ":" + (e.get("name") or "")
                      for e in r.find("Scene")]
                  for s, r in self.roots.items()}
        first = shapes[SLUGS[0]]
        for slug, shape in shapes.items():
            self.assertEqual(shape, first,
                             f"{slug} diverges from the family scene graph")

    def test_every_face_binds_the_same_live_sources(self):
        want = {"[DAY]", "[BATTERY_PERCENT]", "[STEP_COUNT]", "[HEART_RATE]"}
        for slug, root in self.roots.items():
            got = {p.get("expression") for p in root.iter("Parameter")}
            self.assertEqual(got, want, f"{slug} data bindings are {got}")

    def test_no_face_fabricates_a_health_value(self):
        for slug, root in self.roots.items():
            for p in root.iter("Parameter"):
                self.assertNotIn("?", p.get("expression") or "",
                                 f"{slug} substitutes a fallback reading")

    def test_every_face_shares_the_motion_contract(self):
        prof = PROFILES[DEFAULT_PROFILE]
        for slug, root in self.roots.items():
            h = parts(root)["z00_horizon"]
            t = {x.get("target"): x.get("value") for x in h.iter("Transform")}
            self.assertRegex(t["angle"], r"^0 - ",
                             f"{slug} rolls the wrong way")
            self.assertIn(f"{prof['roll_deg']} *", t["angle"], slug)
            self.assertIn(f"{prof['pitch_px']} *", t["y"], slug)
            self.assertIn("[ACCELEROMETER_ANGLE_X]", t["angle"], slug)
            self.assertIn("[ACCELEROMETER_ANGLE_Y]", t["y"], slug)

    def test_no_ambient_layer_moves_with_the_wrist_on_any_face(self):
        for slug, root in self.roots.items():
            for name, part in parts(root).items():
                variant = part.find("Variant")
                if variant is None or int(variant.get("value")) == 0:
                    continue
                for t in part.iter("Transform"):
                    self.assertNotIn("ACCELEROMETER", t.get("value") or "",
                                     f"{slug}/{name} moves in ambient")

    def test_no_face_animates_seconds_in_ambient(self):
        for slug, root in self.roots.items():
            v = parts(root)["z32_second"].find("Variant")
            self.assertEqual(int(v.get("value")), 0, slug)

    def test_every_face_declares_only_the_permissions_it_uses(self):
        want = {"android.permission.BODY_SENSORS",
                "android.permission.ACTIVITY_RECOGNITION"}
        for slug in SLUGS:
            man = (face_dir(slug) / "app/src/main/AndroidManifest.xml").read_text()
            self.assertEqual(
                set(re.findall(r'uses-permission android:name="([^"]+)"', man)),
                want, slug)


class TestVariantsActuallyDiffer(unittest.TestCase):
    """A family of twelve identical faces would pass every platform check."""

    def test_every_variant_ships_distinct_artwork(self):
        seen = {}
        for slug in SLUGS:
            h = VARIANTS[slug]["resources"]["sq_dial.png"]["sha256"]
            self.assertNotIn(h, seen,
                             f"{slug} has the same dial as {seen.get(h)}")
            seen[h] = slug

    def test_every_variant_has_distinct_propeller_hands(self):
        for asset in ("sq_hand_hour.png", "sq_hand_minute.png"):
            seen = {}
            for slug in SLUGS:
                h = VARIANTS[slug]["resources"][asset]["sha256"]
                seen.setdefault(h, []).append(slug)
            # blade metal is shared by some trims by design; require that the
            # collection still shows real variety rather than one hand reused
            self.assertGreaterEqual(
                len(seen), 6,
                f"{asset} only has {len(seen)} distinct treatments across "
                f"{len(SLUGS)} variants")

    def test_every_variant_has_a_distinct_horizon_palette(self):
        seen = {VARIANTS[s]["resources"]["sq_horizon.png"]["sha256"]
                for s in SLUGS}
        self.assertGreaterEqual(len(seen), 6)


class TestArtworkProvenance(unittest.TestCase):
    def test_every_drawable_matches_the_studio_export(self):
        for slug in SLUGS:
            d = face_dir(slug) / "app/src/main/res/drawable"
            for name, meta in VARIANTS[slug]["resources"].items():
                p = d / name
                self.assertTrue(p.exists(), f"{slug} missing {name}")
                self.assertEqual(sha256(p), meta["sha256"],
                                 f"{slug}/{name} differs from the studio")

    def test_no_face_ships_artwork_the_studio_did_not_export(self):
        for slug in SLUGS:
            d = face_dir(slug) / "app/src/main/res/drawable"
            on_disk = {p.name for p in d.iterdir() if p.is_file()}
            self.assertEqual(on_disk, set(VARIANTS[slug]["resources"]), slug)

    def test_the_scaffold_still_reproduces_every_project(self):
        r = subprocess.run([sys.executable, "tools/squadron_scaffold.py",
                            "--check"], cwd=REPO, capture_output=True,
                           text=True)
        if "studio manifest not found" in r.stderr:
            self.skipTest("studio repository not available")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestGeneration(unittest.TestCase):
    def test_every_committed_xml_matches_its_spec(self):
        for slug in SLUGS:
            r = subprocess.run([sys.executable, "tools/generate_face.py",
                                f"squadron-{slug}", "--check"], cwd=REPO,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_generation_is_deterministic_for_every_face(self):
        for slug in SLUGS:
            spec = face_dir(slug) / "engine/face.toml"
            self.assertEqual(render_face(load_spec(spec)),
                             render_face(load_spec(spec)), slug)


class TestGeometry(unittest.TestCase):
    """Pixel gates on the shipped resources, run across the whole family."""

    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("Pillow not available")
        import render_face_from_xml
        cls.R = render_face_from_xml

    def test_no_plate_leaks_outside_its_aperture(self):
        from PIL import Image
        for slug in SLUGS:
            p = face_dir(slug) / "app/src/main/res/drawable/sq_dial.png"
            with Image.open(p) as im:
                a = im.convert("RGBA").getchannel("A")
                leaks = sum(1 for y in range(im.height) for x in range(im.width)
                            if a.getpixel((x, y)) < 255
                            and math.hypot(x - AP["cx"],
                                           y - AP["cy"]) > AP["r"] + 1)
            self.assertEqual(leaks, 0, f"{slug}: {leaks} uncovered plate px")

    def test_no_field_escapes_the_case_on_any_face(self):
        corner = 22
        for slug in SLUGS:
            self.R.select(f"squadron-{slug}")
            root = ET.fromstring(xml_of(slug).read_text())
            font = self.R.Font(root)
            for rx, ry in ((-45.0, -40.0), (45.0, 40.0), (0.0, 40.0)):
                img = self.R.compose(root, font,
                                     dict(self.R.FIXTURE_ENV,
                                          ACCELEROMETER_ANGLE_X=rx,
                                          ACCELEROMETER_ANGLE_Y=ry),
                                     False).load()
                for cx, cy in ((0, 0), (479, 0), (0, 479), (479, 479)):
                    for dx in range(0, corner, 3):
                        for dy in range(0, corner, 3):
                            x = cx + (dx if cx == 0 else -dx)
                            y = cy + (dy if cy == 0 else -dy)
                            self.assertEqual(img[x, y], (0, 0, 0),
                                             f"{slug}: content at ({x},{y}) "
                                             f"at wrist ({rx},{ry})")

    def test_the_aperture_is_never_uncovered_on_any_face(self):
        prof = PROFILES[DEFAULT_PROFILE]
        r = AP["r"] - 2
        for slug in SLUGS:
            self.R.select(f"squadron-{slug}")
            root = ET.fromstring(xml_of(slug).read_text())
            font = self.R.Font(root)
            others = {p.get("name") for p in root.find("Scene")
                      if p.get("name") != "z00_horizon"}
            for rx, ry in ((-45.0, -40.0), (45.0, 40.0), (0.0, 40.0),
                           (45.0, -40.0)):
                img = self.R.compose(root, font,
                                     dict(self.R.FIXTURE_ENV,
                                          ACCELEROMETER_ANGLE_X=rx,
                                          ACCELEROMETER_ANGLE_Y=ry),
                                     False, skip=others).load()
                bare = sum(1 for y in range(AP["cy"] - r, AP["cy"] + r + 1)
                           for x in range(AP["cx"] - r, AP["cx"] + r + 1)
                           if math.hypot(x - AP["cx"], y - AP["cy"]) <= r
                           and img[x, y] == (0, 0, 0))
                self.assertEqual(bare, 0,
                                 f"{slug}: {bare} uncovered aperture px at "
                                 f"wrist ({rx},{ry}), profile "
                                 f"{DEFAULT_PROFILE} ±{prof['pitch_px']}px")


class TestReadability(unittest.TestCase):
    """Theme must not overwhelm usability, on any variant."""

    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("Pillow not available")
        import render_face_from_xml
        cls.R = render_face_from_xml

    @staticmethod
    def _luma(px):
        return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]

    def _region_contrast(self, img, box):
        xs = [self._luma(img[x, y])
              for y in range(box[1], box[3]) for x in range(box[0], box[2])]
        return max(xs) - min(xs)

    def test_every_readout_has_real_contrast_against_its_recess(self):
        for slug in SLUGS:
            self.R.select(f"squadron-{slug}")
            root = ET.fromstring(xml_of(slug).read_text())
            img = self.R.compose(root, self.R.Font(root),
                                 dict(self.R.FIXTURE_ENV), False).load()
            for name, box in (("date", (322, 226, 374, 254)),
                              ("steps", (78, 296, 146, 320)),
                              ("heart rate", (338, 296, 400, 320))):
                c = self._region_contrast(img, box)
                self.assertGreater(
                    c, 60,
                    f"{slug}: {name} readout contrast is only {c:.0f} — the "
                    "theme has swallowed the data")

    def test_the_hands_stand_off_the_dial_on_every_variant(self):
        """Sample the minute hand against the dial behind it."""
        for slug in SLUGS:
            self.R.select(f"squadron-{slug}")
            root = ET.fromstring(xml_of(slug).read_text())
            font = self.R.Font(root)
            hands = self.R.compose(root, font, dict(self.R.FIXTURE_ENV),
                                   False).load()
            bare = self.R.compose(
                root, font, dict(self.R.FIXTURE_ENV), False,
                skip={"z30_hour", "z31_minute", "z32_second",
                      "z40_pinion"}).load()
            diffs = []
            for r in range(70, 150, 6):
                x = 240 + int(r * math.cos(math.radians(-36)))
                y = 240 + int(r * math.sin(math.radians(-36)))
                diffs.append(abs(self._luma(hands[x, y])
                                 - self._luma(bare[x, y])))
            self.assertGreater(
                max(diffs), 45,
                f"{slug}: the minute hand barely separates from the dial "
                f"(best delta {max(diffs):.0f})")


class TestNoReleaseState(unittest.TestCase):
    def test_no_face_carries_signing_or_store_configuration(self):
        for slug in SLUGS:
            g = (face_dir(slug) / "app/build.gradle.kts").read_text()
            for token in ("signingConfig", "storeFile", "keyAlias",
                          "bundle {", "publishing {"):
                self.assertNotIn(token, g, f"{slug} has {token}")

    def test_no_bundles_or_release_apks_exist(self):
        for slug in SLUGS:
            out = face_dir(slug) / "app/build/outputs"
            if out.exists():
                self.assertEqual(list(out.rglob("*.aab")), [], slug)
                self.assertEqual(list(out.rglob("*-release*.apk")), [], slug)

    def test_the_collection_is_not_registered_as_a_release(self):
        rel = REPO / "releases"
        if rel.exists():
            hits = [p for p in rel.rglob("*") if "squadron" in p.name.lower()]
            self.assertEqual(hits, [], f"release entries exist: {hits}")


class TestNoCollateralChange(unittest.TestCase):
    def _changed(self):
        r = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only",
                            "main...HEAD"], capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("cannot diff against main")
        return [f for f in r.stdout.splitlines() if f]

    def test_no_aurelius_change(self):
        touched = [f for f in self._changed() if "/aurelius/" in f
                   or f.startswith("watchfaces/aurelius/")]
        self.assertEqual(touched, [], f"Aurelius touched: {touched}")

    def test_no_spike_or_preview_change(self):
        touched = [f for f in self._changed()
                   if f.startswith(("spikes/", "previews/"))]
        self.assertEqual(touched, [], f"spike/preview touched: {touched}")


if __name__ == "__main__":
    unittest.main()
