#!/usr/bin/env python3
"""Forge the HOG-WILD `wheel` font in Blender: real metal, really lit.

make_wheel_font.py PAINTS a lock wheel; this MACHINES one. A single drum is
modelled with all ten numerals engraved around its circumference (boolean
difference, so the digit is a true recess whose walls catch light) and two
knurled rims built from real ridge geometry standing proud of the band —
then the drum is detented 36° at a time and rendered head-on with Cycles.
Because every digit lives on the same physical drum, the neighbouring
numerals curve away at the slot edges in correct perspective, the engraving
self-shadows, and the lathe-turned brushing crosses highlight like metal
instead of like a gradient.

The BitmapFont alpha-mask constraint is unchanged: the pipeline discards
glyph colour, so the render ships as relief — luminance becomes alpha, the
declared colour becomes the steel, and the engraved cut (which Cycles
renders dark) goes transparent for the aperture's darkness to fill.

One file, two roles: run as plain Python it drives everything (invokes
Blender headless on itself, then post-processes); run inside Blender (-P)
it builds and renders.

Determinism: fixed seed, fixed sample count, denoiser on. Cycles output is
stable for a given Blender build (4.5 LTS here) but not warranted across
versions — regenerate and eyeball rather than diff.

Usage:
    python3 tools/forge_wheel_font.py            # report
    python3 tools/forge_wheel_font.py --write    # forge + install glyphs
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DRAWABLE = REPO / "watchfaces/hogwild/app/src/main/res/drawable"
FONT_TTF = Path.home() / ".local/share/fonts/BarlowCondensed-Bold.ttf"
RENDER_DIR = REPO / "build/wheel_forge"
CELL_W, CELL_H = 34, 46
RES_W, RES_H = 340, 460          # 10x, downscaled at install


# ======================================================================
# BLENDER SIDE
# ======================================================================
def blender_main() -> None:
    import bpy

    # ---- clean scene ----
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # ---- the drum: axis along X, digit band radius 1.0 ----
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=256, radius=1.0, depth=0.66,
        rotation=(0, math.pi / 2, 0))
    drum = bpy.context.object
    drum.name = "drum"
    bpy.ops.object.shade_smooth()

    # ---- knurled rims: ridge boxes arrayed around each rim ring ----
    rims = []
    for side in (-1, 1):
        x0 = side * (0.33 + 0.085)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=256, radius=1.04, depth=0.17,
            rotation=(0, math.pi / 2, 0), location=(x0, 0, 0))
        rim = bpy.context.object
        rim.name = f"rim{side}"
        bpy.ops.object.shade_smooth()
        rims.append(rim)
        for i in range(72):                      # the knurl, as geometry
            a = 2 * math.pi * i / 72
            bpy.ops.mesh.primitive_cube_add(size=1, location=(
                x0, -math.sin(a) * 1.045, math.cos(a) * 1.045))
            ridge = bpy.context.object
            ridge.scale = (0.075, 0.012, 0.022)
            ridge.rotation_euler = (a, 0, 0)
            rims.append(ridge)

    # ---- no engraving in the scene ----
    # 1.3.2 cut the numerals into the drum and stamped ink over them; at
    # the 15-20px the face ships at, the stamp/recess misregistration and
    # the neighbouring rows read as damage, not depth. The drum renders
    # CLEAN and rotationally uniform — one render serves all ten digits —
    # and the numeral, its recess shadow and its lit lip are all applied
    # in post at target scale, where their weights can be chosen for
    # legibility instead of physics.
    # ---- materials: lathe-brushed steel band, rougher rims ----
    def steel(name, rough, lathe=False):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.74, 0.75, 0.77, 1)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Specular IOR Level"].default_value = 0.4
        if lathe:
            nt = m.node_tree
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.inputs["Scale"].default_value = 6.0
            tex.noise_dimensions = "3D"
            mapping = nt.nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (60.0, 1.0, 1.0)
            coord = nt.nodes.new("ShaderNodeTexCoord")
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.015
            nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
            nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
            nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        return m

    band_mat = steel("band", 0.30, lathe=True)
    rim_mat = steel("rims", 0.45)
    drum.data.materials.append(band_mat)
    for r in rims:
        r.data.materials.append(rim_mat)

    # ---- parent everything to a spindle for detenting ----
    bpy.ops.object.empty_add(location=(0, 0, 0))
    spindle = bpy.context.object
    spindle.name = "spindle"
    for ob in [drum] + rims:
        ob.parent = spindle

    # ---- camera: orthographic, dead-on ----
    bpy.ops.object.camera_add(location=(0, -4, 0),
                              rotation=(math.pi / 2, 0, 0))
    cam = bpy.context.object
    cam.data.type = "ORTHO"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.ortho_scale = 1.38   # full wheel width — band plus both
    # knurled rims — which the cell aspect turns into a vertical span of
    # +/-0.69: harmless now the drum carries no engraving to leak into
    # the frame, just clean rolled-away metal
    scene.camera = cam

    # ---- studio: key, fill, and a hot equator strip ----
    def area(loc, rot, size, power):
        bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
        li = bpy.context.object
        li.data.size = size
        li.data.energy = power
        return li

    area((1.5, -3.0, 3.0), (math.radians(50), 0, math.radians(20)), 4, 115)
    area((-2.0, -3.0, -1.0), (math.radians(105), 0, math.radians(-30)), 3, 45)
    area((0, -2.6, 0.55), (math.radians(78), 0, 0), 1.2, 55)
    world = bpy.data.worlds.new("w")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[
        "Strength"].default_value = 0.03

    # ---- Cycles ----
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.cycles.seed = 7
    scene.cycles.use_denoising = True
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs:
        cp = prefs.preferences
        for backend in ("OPTIX", "CUDA"):
            try:
                cp.compute_device_type = backend
                cp.get_devices()
                for d in cp.devices:
                    d.use = True
                scene.cycles.device = "GPU"
                break
            except Exception:
                continue
    scene.render.resolution_x = RES_W
    scene.render.resolution_y = RES_H
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "Filmic"

    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(RENDER_DIR / "base.png")
    bpy.ops.render.render(write_still=True)
    print("forged base drum")


# ======================================================================
# DRIVER SIDE
# ======================================================================
def digit_mask(ch: str) -> "Image":
    """The numeral at 4x, sized for legibility at the shipping 15-20px:
    cap height ~55% of the cell, centred on the drum's equator."""
    from PIL import Image, ImageDraw, ImageFont
    ss = 4
    em = round(ss * 35)          # Barlow Condensed cap ~0.72em -> ~25px cap
    fnt = ImageFont.truetype(str(FONT_TTF), em)
    m = Image.new("L", (CELL_W * ss, CELL_H * ss), 0)
    d = ImageDraw.Draw(m)
    bbox = d.textbbox((0, 0), ch, font=fnt)
    d.text((CELL_W * ss / 2 - (bbox[0] + bbox[2]) / 2,
            CELL_H * ss / 2 - (bbox[1] + bbox[3]) / 2), ch,
           font=fnt, fill=255)
    return m.resize((CELL_W, CELL_H), Image.LANCZOS)


def install_glyphs(write: bool) -> None:
    """Finish: Blender supplies the metal, post supplies the numeral.

    The render is a clean lit drum (knurl, cylindrical falloff, brushing) —
    rotationally uniform, so one render serves all ten cells. Each numeral
    is applied here as engraved-and-ink-filled at target scale: a soft
    recess shadow a pixel above the cut, near-black ink in the cut, a lit
    lip a pixel below it. Weights chosen at 15-20px, where this ships.
    """
    import math as _m
    from PIL import Image, ImageChops, ImageFilter
    base = Image.open(RENDER_DIR / "base.png").convert("L").resize(
        (CELL_W, CELL_H), Image.LANCZOS)
    base = base.filter(ImageFilter.UnsharpMask(radius=2, percent=90,
                                               threshold=2))
    lum0 = base.point(lambda v: min(255, int((v / 255) ** 0.95 * 400)))
    # gentle aperture shading only — harsh vignettes turn to speckle
    # when the runtime scales the cell down
    px = lum0.load()
    for y in range(CELL_H):
        t = abs(y - (CELL_H - 1) / 2) / (CELL_H / 2)
        k = 0.55 + 0.45 * max(0.0, _m.cos(min(1.0, t) * 0.95))
        for x in range(CELL_W):
            px[x, y] = int(px[x, y] * k)

    for i in range(10):
        lum = lum0.copy()
        mask = digit_mask(str(i))
        # recess shadow: blurred mask, shifted up, darkens the metal
        shadow = mask.filter(ImageFilter.GaussianBlur(1.2)).transform(
            mask.size, Image.AFFINE, (1, 0, 0, 0, 1, 1))
        lum = ImageChops.multiply(
            lum, shadow.point(lambda v: 255 - (v * 90) // 255))
        # the ink fill
        lum = ImageChops.multiply(
            lum, mask.point(lambda v: 255 - (v * 240) // 255))
        # lit lower lip
        lip = ImageChops.subtract(
            mask.transform(mask.size, Image.AFFINE, (1, 0, 0, 0, 1, -1)),
            mask)
        lum = ImageChops.add(lum, lip.point(lambda v: (v * 80) // 255))
        out = Image.new("RGBA", (CELL_W, CELL_H), (255, 255, 255, 0))
        out.putalpha(lum)
        dest = DRAWABLE / f"w_{i}.png"
        if write:
            out.save(dest)
            print(f"installed {dest.relative_to(REPO)}")
        else:
            print(f"would install {dest.relative_to(REPO)}")


def driver_main() -> int:
    write = "--write" in sys.argv
    blender = subprocess.run(["blender", "-b", "-P", __file__],
                             capture_output=True, text=True)
    if blender.returncode != 0:
        sys.stderr.write(blender.stdout[-2000:] + blender.stderr[-2000:])
        return 1
    if not (RENDER_DIR / "base.png").exists():
        sys.stderr.write("blender produced no base render\n")
        sys.stderr.write(blender.stdout[-2000:])
        return 1
    install_glyphs(write)
    return 0


try:
    import bpy  # noqa: F401  — present only under `blender -P`
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

if IN_BLENDER:
    blender_main()
elif __name__ == "__main__":
    sys.exit(driver_main())
