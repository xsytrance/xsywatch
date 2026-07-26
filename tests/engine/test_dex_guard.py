"""Deliberate-failure fixtures for the fail-closed dex gate.

Checkpoint B blocker 3: the previous strip deleted every release dex and
merely asserted in a comment that the content was the generated R class.
A real class entering the release graph would have been silently deleted,
and the bundle would still have passed the final "contains no dex" check.

These tests prove the gate now REFUSES to delete anything it cannot
account for. Each fixture builds a real DEX container and runs it through
the same parser and allowlist the build uses.

Run: python3 -m unittest discover -s tests/engine
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import dex_guard as DG                                # noqa: E402

PACKAGE = "com.xsytrance.aurelius"

R_CLASSES = [
    "Lcom/xsytrance/aurelius/R;",
    "Lcom/xsytrance/aurelius/R$drawable;",
    "Lcom/xsytrance/aurelius/R$font;",
    "Lcom/xsytrance/aurelius/R$integer;",
    "Lcom/xsytrance/aurelius/R$raw;",
    "Lcom/xsytrance/aurelius/R$xml;",
]


def _uleb(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def make_dex(descriptors: list[str]) -> bytes:
    """Build a minimal but structurally valid DEX defining `descriptors`.

    Only the parts dex_guard reads are populated — header offsets,
    string_ids, type_ids and class_defs. That is deliberate: the gate must
    work off the container's own tables, and a fixture that faked those
    would test nothing.
    """
    n = len(descriptors)
    header = 112
    string_ids_off = header
    type_ids_off = string_ids_off + 4 * n
    class_defs_off = type_ids_off + 4 * n
    data_off = class_defs_off + 32 * n

    data = bytearray()
    string_offsets = []
    for d in descriptors:
        string_offsets.append(data_off + len(data))
        raw = d.encode("utf-8")
        data += _uleb(len(raw)) + raw + b"\x00"

    buf = bytearray(data_off + len(data))
    buf[0:8] = b"dex\n035\x00"
    struct.pack_into("<II", buf, 56, n, string_ids_off)      # string_ids
    struct.pack_into("<II", buf, 64, n, type_ids_off)        # type_ids
    struct.pack_into("<II", buf, 96, n, class_defs_off)      # class_defs
    for i, off in enumerate(string_offsets):
        struct.pack_into("<I", buf, string_ids_off + 4 * i, off)
        struct.pack_into("<I", buf, type_ids_off + 4 * i, i)   # type -> string
    for i in range(n):
        struct.pack_into("<I", buf, class_defs_off + 32 * i, i)  # class_idx
    buf[data_off:data_off + len(data)] = data
    return bytes(buf)


class DexParserTests(unittest.TestCase):
    """The parser must read exactly the classes a dex DEFINES."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, descriptors, name="classes.dex") -> Path:
        p = self.tmp / name
        p.write_bytes(make_dex(descriptors))
        return p

    def test_reads_the_defined_class_set(self):
        p = self.write(R_CLASSES)
        self.assertEqual(DG.dex_class_descriptors(p), sorted(R_CLASSES))

    def test_rejects_a_non_dex_file(self):
        p = self.tmp / "notadex.dex"
        p.write_bytes(b"this is not a dex file at all")
        with self.assertRaises(ValueError):
            DG.dex_class_descriptors(p)

    def test_rejects_a_truncated_header(self):
        p = self.tmp / "short.dex"
        p.write_bytes(b"dex\n035\x00" + b"\x00" * 8)
        with self.assertRaises(ValueError):
            DG.dex_class_descriptors(p)


class AllowlistTests(unittest.TestCase):

    def test_generated_r_classes_are_allowed(self):
        for d in R_CLASSES:
            self.assertTrue(DG.allowed(d, PACKAGE), d)

    def test_another_packages_r_is_not_allowed(self):
        self.assertFalse(DG.allowed("Lcom/example/other/R;", PACKAGE))

    def test_a_class_merely_starting_with_r_is_not_allowed(self):
        """`Renderer` starts with R but is not the R class."""
        self.assertFalse(
            DG.allowed("Lcom/xsytrance/aurelius/Renderer;", PACKAGE))


class GateRejectionTests(unittest.TestCase):
    """The three injections the review asked for, plus the positive
    control. Each runs the real gate end to end."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.dexdir = self.tmp / "dex"
        self.dexdir.mkdir()

    def run_gate(self, descriptors, delete=True):
        (self.dexdir / "classes.dex").write_bytes(make_dex(descriptors))
        report = self.tmp / "report.json"
        r = subprocess.run(
            [sys.executable, str(REPO / "tools/dex_guard.py"),
             "--dex-dir", str(self.dexdir), "--package", PACKAGE,
             "--report", str(report)] + (["--delete"] if delete else []),
            capture_output=True, text=True)
        data = json.loads(report.read_text()) if report.exists() else {}
        return r.returncode, data

    # -- positive control ------------------------------------------------

    def test_r_only_input_passes_and_is_deleted(self):
        rc, data = self.run_gate(R_CLASSES)
        self.assertEqual(rc, 0, "generated-R-only input must pass")
        self.assertTrue(data["passed"])
        self.assertEqual(data["violations"], [])
        self.assertEqual(data["deleted"], ["classes.dex"])
        self.assertFalse((self.dexdir / "classes.dex").exists())

    # -- 1. an ordinary application class --------------------------------

    def test_ordinary_application_class_fails_before_packaging(self):
        rc, data = self.run_gate(
            R_CLASSES + ["Lcom/xsytrance/aurelius/MainActivity;"])
        self.assertEqual(rc, 1)
        self.assertFalse(data["passed"])
        self.assertIn("Lcom/xsytrance/aurelius/MainActivity;",
                      data["pre_strip_inventory"][0]["disallowed"])
        self.assertTrue((self.dexdir / "classes.dex").exists(),
                        "nothing may be deleted when the gate fails")
        self.assertEqual(data["deleted"], [])

    # -- 2. a runtime / dependency class ---------------------------------

    def test_runtime_dependency_class_fails(self):
        rc, data = self.run_gate(
            R_CLASSES + ["Lkotlin/jvm/internal/Intrinsics;"])
        self.assertEqual(rc, 1)
        self.assertIn("Lkotlin/jvm/internal/Intrinsics;",
                      data["pre_strip_inventory"][0]["disallowed"])
        self.assertTrue((self.dexdir / "classes.dex").exists())

    # -- 3. an unexpected generated / synthetic class --------------------

    def test_unexpected_synthetic_class_fails(self):
        rc, data = self.run_gate(
            R_CLASSES + ["Lcom/xsytrance/aurelius/BuildConfig;",
                         "Lcom/xsytrance/aurelius/R$$ExternalSyntheticLambda0;"])
        self.assertEqual(rc, 1)
        bad = data["pre_strip_inventory"][0]["disallowed"]
        self.assertIn("Lcom/xsytrance/aurelius/BuildConfig;", bad)
        self.assertTrue((self.dexdir / "classes.dex").exists())

    # -- an unreadable dex is not silently deleted -----------------------

    def test_unparseable_dex_is_not_deleted(self):
        (self.dexdir / "classes.dex").write_bytes(b"corrupt not-a-dex")
        report = self.tmp / "r.json"
        r = subprocess.run(
            [sys.executable, str(REPO / "tools/dex_guard.py"),
             "--dex-dir", str(self.dexdir), "--package", PACKAGE,
             "--delete", "--report", str(report)],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertTrue((self.dexdir / "classes.dex").exists(),
                        "a dex we cannot read must never be deleted")

    # -- inventory is recorded for evidence ------------------------------

    def test_pre_strip_inventory_records_hash_and_size(self):
        rc, data = self.run_gate(R_CLASSES)
        self.assertEqual(rc, 0)
        e = data["pre_strip_inventory"][0]
        self.assertRegex(e["sha256"], r"^[0-9a-f]{64}$")
        self.assertGreater(e["size_bytes"], 0)
        self.assertEqual(e["classes"], sorted(R_CLASSES))
        self.assertEqual(e["class_count"], len(R_CLASSES))


class CommittedDexEvidenceTests(unittest.TestCase):
    """The committed candidate evidence must show a gate that actually
    ran and actually inspected an R-only input."""

    def test_candidate_verify_records_the_dex_gate(self):
        import glob
        found = sorted(glob.glob(str(
            REPO / "releases/aurelius/candidates/*/VERIFY.json")))
        if not found:
            self.skipTest("no candidate VERIFY.json yet")
        checked = 0
        for f in found:
            v = json.loads(Path(f).read_text())
            gate = v.get("dex_gate")
            if gate is None:
                continue           # rc1 predates the gate; not a failure
            checked += 1
            self.assertTrue(gate.get("passed"), f)
            for e in gate.get("pre_strip_inventory", []):
                for c in e.get("classes") or []:
                    self.assertTrue(
                        DG.allowed(c, PACKAGE),
                        f"{f}: recorded a non-allowlisted class {c}")
            self.assertFalse(v["artifacts"]["aab"].get("contains_dex"))
        if checked == 0:
            self.skipTest("no candidate carries dex-gate evidence yet")


if __name__ == "__main__":
    unittest.main()
