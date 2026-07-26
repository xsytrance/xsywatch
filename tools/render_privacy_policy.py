#!/usr/bin/env python3
"""Render the approved privacy-policy text to a hostable page, and pin its bytes.

`policy-ready` wants a privacy policy that is (a) actually hosted and (b)
bound to a content checksum, so the page cannot drift after submission
without anyone noticing. The text itself was approved in the listing copy
long ago; what was missing was a rendered artifact and a hash.

The text is EXTRACTED from the approved draft rather than retyped here, so
there is exactly one authoritative copy. If someone edits the draft, the
rendered page and its checksum change — which is the point.

    python3 tools/render_privacy_policy.py --email rod@x1c7.com --date 2026-07-26
    python3 tools/render_privacy_policy.py --verify path/or/url-dump.html

Writes docs/commercial/aurelius/privacy/privacy_policy.html and
PRIVACY_POLICY.json alongside it.

Refuses to render while a placeholder is unresolved — a policy published
with "<SUPPORT EMAIL — owner to supply>" in it would be worse than none.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRAFT = REPO / "docs/commercial/aurelius/2.0.0-rc2/COPY_DRAFT.md"
OUT_DIR = REPO / "docs/commercial/aurelius/privacy"
MARKER = "AURELIUS privacy policy"

PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AURELIUS — Privacy Policy</title>
<style>
  body {{ font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI",
         Roboto, Helvetica, Arial, sans-serif; max-width: 40rem;
         margin: 3rem auto; padding: 0 1.25rem; color: #1b1b1b; }}
  h1 {{ font-size: 1.5rem; letter-spacing: .01em; }}
  footer {{ margin-top: 2.5rem; color: #666; font-size: .875rem; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #131313; color: #e8e8e8; }}
    footer {{ color: #999; }}
    a {{ color: #9cc3ff; }}
  }}
</style>
<h1>AURELIUS — Privacy Policy</h1>
{body}
<footer>Last updated: {date}</footer>
"""


def extract_policy(draft: Path) -> list[str]:
    """Pull the approved blockquote out of the listing copy."""
    if not draft.exists():
        raise SystemExit(f"ERROR no draft at {draft}")
    lines = draft.read_text(encoding="utf-8").splitlines()
    start = next((i for i, ln in enumerate(lines) if MARKER in ln), None)
    if start is None:
        raise SystemExit(f"ERROR {MARKER!r} not found in {draft.name} — the "
                         f"approved text moved; refusing to guess")
    out: list[str] = []
    for ln in lines[start + 1:]:
        if not ln.startswith(">"):
            break
        out.append(ln.lstrip(">").strip())
    return out


def paragraphs(lines: list[str]) -> list[str]:
    paras, cur = [], []
    for ln in lines:
        if ln:
            cur.append(ln)
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email", help="support address to substitute")
    ap.add_argument("--date", help="last-updated date, e.g. 2026-07-26")
    ap.add_argument("--url", default="https://x1c7.com/privacy/aurelius")
    ap.add_argument("--verify", metavar="FILE",
                    help="check a downloaded copy against the recorded hash")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    page_p = OUT_DIR / "privacy_policy.html"
    rec_p = OUT_DIR / "PRIVACY_POLICY.json"

    if args.verify:
        if not rec_p.exists():
            print("ERROR nothing rendered yet; run without --verify first",
                  file=sys.stderr)
            return 2
        rec = json.loads(rec_p.read_text(encoding="utf-8"))
        got = sha256_text(Path(args.verify).read_text(encoding="utf-8"))
        if got == rec["sha256"]:
            print(f"OK hosted bytes match the recorded policy {got[:12]}…")
            return 0
        print(f"ERROR hosted copy {got[:12]}… != recorded "
              f"{rec['sha256'][:12]}… — the live policy has drifted",
              file=sys.stderr)
        return 1

    if not args.email or not args.date:
        print("ERROR --email and --date are both required to render.\n"
              "      Both are owner inputs; see "
              "docs/commercial/aurelius/LAUNCH_DECISIONS.md §B.",
              file=sys.stderr)
        return 2

    lines = extract_policy(DRAFT)
    text = "\n".join(lines)
    text = re.sub(r"<SUPPORT EMAIL[^>]*>", args.email, text)
    text = re.sub(r"<DATE>", args.date, text)

    leftover = re.findall(r"<[A-Z][^>]*>", text)
    if leftover:
        print(f"ERROR unresolved placeholder(s) still in the text: "
              f"{leftover} — refusing to render a policy with a blank in it",
              file=sys.stderr)
        return 1

    body = "\n".join(
        f"<p>{html.escape(p)}</p>" for p in paragraphs(text.splitlines())
        if not p.lower().startswith("last updated"))
    page = PAGE.format(body=body, date=html.escape(args.date))
    page_p.write_text(page, encoding="utf-8")

    rec = {
        "schema": "agenor.privacy-policy/1",
        "face": "aurelius",
        "source": str(DRAFT.relative_to(REPO)),
        "rendered": str(page_p.relative_to(REPO)),
        "url": args.url,
        "support_email": args.email,
        "last_updated": args.date,
        "sha256": sha256_text(page),
        "hosted": False,
        "note": "hosted=false until the page is live at `url` and verified "
                "with --verify against the downloaded bytes",
    }
    rec_p.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(f"wrote {page_p.relative_to(REPO)}")
    print(f"wrote {rec_p.relative_to(REPO)}")
    print(f"sha256 {rec['sha256']}")
    print(f"\nUpload it to {args.url}, then:\n"
          f"  curl -s {args.url} > /tmp/live.html\n"
          f"  python3 tools/render_privacy_policy.py --verify /tmp/live.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
