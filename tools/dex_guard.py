#!/usr/bin/env python3
"""Fail-closed dex gate for the Aurelius release bundle.

Play rejects a Watch Face Format bundle containing dex, and Aurelius is a
resource-only face: AndroidManifest declares android:hasCode="false" and
the project contains no .java or .kt source. AGP nevertheless emits a
small dex holding the generated resource R class, so the build removes it
before packaging.

Removing dex is only safe if we KNOW what is being removed. The first
implementation deleted every .dex it found and merely asserted in a
comment that the content was the R class. That is fail-open: if a real
class or a runtime dependency ever entered the release graph, it would be
silently deleted and the resulting bundle would still pass a final
"contains no dex" check.

This gate inverts that. It enumerates every dex, records its SHA-256 and
size, parses out every class descriptor it DEFINES, and permits deletion
only when the complete set is within the allowlist:

    Lcom/xsytrance/aurelius/R;
    Lcom/xsytrance/aurelius/R$<anything>;

Anything else fails the build before packaging.

    python3 tools/dex_guard.py --dex-dir DIR --package com.xsytrance.aurelius \
        [--delete] [--report OUT.json]

Exit codes: 0 allowlist satisfied, 1 a disallowed class was found, 2 bad
invocation.

Class descriptors are read with a self-contained DEX parser rather than an
external tool, so the gate cannot be skipped by a missing SDK. When
`dexdump` from the pinned build-tools is available it is run as an
independent cross-check and a disagreement is itself a failure — two
parsers agreeing is worth more than one parser trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

DEX_MAGIC = b"dex\n"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _uleb128(buf: bytes, off: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        b = buf[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, off
        shift += 7


def dex_class_descriptors(path: Path) -> list[str]:
    """Every class descriptor DEFINED in a .dex file.

    Deterministic parse of the DEX container: class_defs -> type_ids ->
    string_ids -> string_data. Only classes the file defines are returned;
    referenced-but-not-defined types are deliberately excluded, because
    what matters is what deletion would remove.
    """
    buf = path.read_bytes()
    if buf[:4] != DEX_MAGIC:
        raise ValueError(f"{path.name}: not a DEX file")
    if len(buf) < 112:
        raise ValueError(f"{path.name}: truncated DEX header")

    # Header offsets are fixed by the DEX format.
    (string_ids_size, string_ids_off) = struct.unpack_from("<II", buf, 56)
    (type_ids_size, type_ids_off) = struct.unpack_from("<II", buf, 64)
    (class_defs_size, class_defs_off) = struct.unpack_from("<II", buf, 96)

    def string_at(idx: int) -> str:
        if idx >= string_ids_size:
            raise ValueError(f"{path.name}: string index {idx} out of range")
        off = struct.unpack_from("<I", buf, string_ids_off + 4 * idx)[0]
        _size, data_off = _uleb128(buf, off)
        end = buf.index(b"\x00", data_off)
        return buf[data_off:end].decode("utf-8", errors="replace")

    def type_at(idx: int) -> str:
        if idx >= type_ids_size:
            raise ValueError(f"{path.name}: type index {idx} out of range")
        sidx = struct.unpack_from("<I", buf, type_ids_off + 4 * idx)[0]
        return string_at(sidx)

    out = []
    for i in range(class_defs_size):
        class_idx = struct.unpack_from("<I", buf, class_defs_off + 32 * i)[0]
        out.append(type_at(class_idx))
    return sorted(set(out))


def dexdump_class_descriptors(path: Path) -> list[str] | None:
    """Independent cross-check via the pinned build-tools dexdump."""
    home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not home:
        return None
    cands = sorted((Path(home) / "build-tools").glob("*/dexdump"),
                   reverse=True)
    if not cands:
        return None
    r = subprocess.run([str(cands[0]), "-f", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    found = re.findall(r"Class descriptor\s*:\s*'([^']+)'", r.stdout)
    return sorted(set(found)) if found else []


def allowed(descriptor: str, package: str) -> bool:
    base = "L" + package.replace(".", "/") + "/R"
    return descriptor == base + ";" or descriptor.startswith(base + "$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dex-dir", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--delete", action="store_true",
                    help="delete the dex files after the allowlist passes")
    ap.add_argument("--report")
    args = ap.parse_args()

    root = Path(args.dex_dir)
    inventory = []
    violations = []

    dex_files = sorted(p for p in root.rglob("*.dex")) if root.exists() else []

    for p in dex_files:
        entry = {
            "path": str(p.relative_to(root)),
            "sha256": sha256(p),
            "size_bytes": p.stat().st_size,
        }
        try:
            classes = dex_class_descriptors(p)
        except ValueError as e:
            violations.append(f"{p.name}: could not be parsed ({e}) — "
                              f"refusing to delete a dex we cannot read")
            entry["classes"] = None
            entry["parse_error"] = str(e)
            inventory.append(entry)
            continue

        entry["classes"] = classes
        entry["class_count"] = len(classes)

        cross = dexdump_class_descriptors(p)
        if cross is not None:
            entry["dexdump_agrees"] = (cross == classes)
            entry["dexdump_classes"] = cross
            if cross != classes:
                violations.append(
                    f"{p.name}: the built-in parser and dexdump disagree on "
                    f"the class set ({classes} vs {cross}) — refusing to "
                    f"delete on an ambiguous read")
        else:
            entry["dexdump_agrees"] = None

        bad = [c for c in classes if not allowed(c, args.package)]
        entry["disallowed"] = bad
        if bad:
            violations.append(
                f"{p.name}: contains {len(bad)} class(es) outside the "
                f"generated-R allowlist: {bad}. A resource-only watch face "
                f"must not ship code; this dex would have been silently "
                f"deleted by a fail-open strip.")
        inventory.append(entry)

    result = {
        "gate": "dex-allowlist",
        "package": args.package,
        "dex_dir": str(root),
        "allowlist": [f"L{args.package.replace('.', '/')}/R;",
                      f"L{args.package.replace('.', '/')}/R$*;"],
        "dex_files_found": len(dex_files),
        "pre_strip_inventory": inventory,
        "violations": violations,
        "passed": not violations,
        "deleted": [],
    }

    for v in violations:
        print(f"ERROR {v}", file=sys.stderr)

    if violations:
        print(f"dex gate FAILED — {len(violations)} violation(s); "
              f"nothing deleted", file=sys.stderr)
    else:
        for e in inventory:
            print(f"ok    {e['path']} {e['size_bytes']}B "
                  f"{e['sha256'][:12]}… classes={e['classes']}")
        if args.delete:
            for p in dex_files:
                p.unlink()
                result["deleted"].append(str(p.relative_to(root)))
            print(f"dex gate PASSED — deleted {len(result['deleted'])} "
                  f"file(s) after allowlist verification")
        else:
            print(f"dex gate PASSED — {len(dex_files)} file(s) inspected, "
                  f"none deleted (--delete not given)")

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
