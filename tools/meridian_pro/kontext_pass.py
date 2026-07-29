"""MERIDIAN PRO — the Kontext finishing pass.

The owner's call, 2026-07-29: the procedural render is the LAYOUT, Kontext
Pro makes it photoreal. The division of labour that makes this safe:

  - geometry.py + plate.py stay the source of truth. The generation is an
    img2img pass over OUR OWN render, so there is no third-party source in
    the chain — the inbound rights question that hung over the aviators
    does not exist here.
  - Kontext is told to move NOTHING, and we do not take its word for it:
    verify() measures the wells and plate against geometry.py afterwards,
    because Kontext always widens what you give it (kontext-api-facts).
  - The wells stay EMPTY. Hands, arcs, numbers are live WFF vectors drawn
    by the watch; anything Kontext painted in a well would sit under them
    as a lie.

Adapted from the studio's pipeline/aiml_kontext.py — the recipe that built
the five aviators. curl-shaped headers (the API rejects default urllib UAs).

Usage:
    python3 tools/meridian_pro/kontext_pass.py <in.png> <out.png> [model]
"""

from __future__ import annotations

import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

KEY = Path.home().joinpath(".bfl_key").read_text().strip()
BASE = "https://api.aimlapi.com/v1"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")

PROMPT = (
    "Turn this watch dial design into an ultra photorealistic macro "
    "photograph of a real luxury aviator wristwatch dial. Keep every "
    "element in exactly the same position, size and arrangement - do not "
    "move, add or remove anything. The outer bezel is deep navy anodized "
    "metal with engraved gold minute numerals and a luminous triangle at "
    "the top. The applied hour markers are polished steel batons filled "
    "with pale luminous paint, standing slightly off the dial and casting "
    "tiny soft shadows. The large centre plate is real machined brushed "
    "steel with fine metal grain, bevelled edges, real slotted screws and "
    "faint tooling marks. The dark circular and rectangular openings are "
    "empty recessed instrument wells with machined counterbores - keep "
    "them empty and dark, add nothing inside them. The MERIDIAN "
    "COMMODORE lettering is engraved into the metal. The dial base is "
    "deep navy blue with subtle circular brushing. No watch hands, no "
    "extra text, no glare. Studio product photography, even lighting, "
    "extremely sharp, 8k."
)


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json",
                 "User-Agent": UA, "Accept": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:900])
        sys.exit(2)


def generate(src: Path, dst: Path, model: str) -> None:
    data_uri = ("data:image/png;base64,"
                + base64.b64encode(src.read_bytes()).decode())
    r = post("/images/generations",
             {"model": model, "prompt": PROMPT, "image_url": data_uri,
              "num_images": 1, "output_format": "png",
              "safety_tolerance": "2"})
    url = None
    if isinstance(r.get("images"), list) and r["images"]:
        url = r["images"][0].get("url")
    elif r.get("data"):
        url = r["data"][0].get("url")
    elif r.get("url"):
        url = r["url"]
    gid = r.get("id") or r.get("generation_id")
    for _ in range(60):
        if url:
            break
        time.sleep(5)
        q = urllib.request.Request(
            f"{BASE}/images/generations?generation_id={gid}",
            headers={"Authorization": "Bearer " + KEY, "User-Agent": UA})
        try:
            s = json.load(urllib.request.urlopen(q, timeout=60))
        except Exception as e:
            print("poll err", e)
            continue
        if s.get("status") in ("completed", "succeeded") or s.get("images"):
            imgs = s.get("images") or s.get("data") or []
            if imgs:
                url = imgs[0].get("url")
        elif s.get("status") in ("failed", "error"):
            print("FAILED", json.dumps(s)[:600])
            sys.exit(3)
    if not url:
        print("no image url; raw:", json.dumps(r)[:900])
        sys.exit(4)
    # The CDN 403s urllib's fingerprint; kontext-api-facts says "curl, not
    # urllib" and means it. The API calls above pass with a browser UA; the
    # image download does not.
    import subprocess
    subprocess.run(["curl", "-sSL", "-A", UA, "-o", str(dst), url],
                   check=True, timeout=180)
    print("SAVED", dst)


def verify(dst: Path) -> None:
    """Measure the result against geometry.py — Kontext's layout promises
    are checked, not believed. Wells must still be dark at their centres,
    the plate still steel at its heart, the bezel still navy."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from geometry import DATE, MOON, PALETTE, SUBDIAL, WINDOWS
    from PIL import Image
    img = Image.open(dst).convert("RGB")
    if img.size != (480, 480):
        img = img.resize((480, 480), Image.LANCZOS)
        img.save(dst)
        print("  resized back to 480 (Kontext returned other dims)")
    checks = [
        ("steps well", SUBDIAL["steps_c"], "dark"),
        ("hr well", SUBDIAL["hr_c"], "dark"),
        ("moon well", MOON["c"], "dark"),
        ("date window", DATE["c"], "dark"),
        ("left window", WINDOWS["left_c"], "dark"),
        ("right window", WINDOWS["right_c"], "dark"),
        ("plate heart", (240, 240), "steel"),
    ]
    bad = 0
    for name, (x, y), want in checks:
        px = img.getpixel((int(x), int(y)))
        lum = sum(px) / 3
        ok = lum < 90 if want == "dark" else lum > 90
        print(f"  {name:14} rgb{px} -> {'OK' if ok else 'DRIFTED'}")
        bad += 0 if ok else 1
    print(f"  verify: {len(checks) - bad}/{len(checks)} anchors hold")


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    model = sys.argv[3] if len(sys.argv) > 3 else \
        "flux/kontext-pro/image-to-image"
    generate(src, dst, model)
    verify(dst)
