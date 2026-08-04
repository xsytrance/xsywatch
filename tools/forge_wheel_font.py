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

    # ---- numerals: engraved clean through the band surface ----
    cutters = []
    font = bpy.data.fonts.load(str(FONT_TTF))
    for i, ch in enumerate("0123456789"):
        a = 2 * math.pi * i / 10
        bpy.ops.object.text_add()
        txt = bpy.context.object
        txt.data.body = ch
        txt.data.font = font
        txt.data.size = 0.84
        # NO outline offset: fattening the text curves makes them
        # self-intersect, and the exact boolean then flips inside out and
        # skins the whole band instead of cutting ten numerals. Stroke
        # weight for the shipping size comes from the ink stamp, not the
        # cutter.
        txt.data.extrude = 0.025      # shallow: engraved-and-inked, not milled
        txt.data.align_x = "CENTER"
        txt.data.align_y = "CENTER"
        bpy.ops.object.convert(target="MESH")
        # face outward at angle phi: text starts facing +Z, upright in
        # XY; phi=pi/2 puts digit 0 on the -Y face, dead in front of the
        # camera, and location must use the SAME angle as the facing
        phi = a + math.pi / 2
        txt.rotation_euler = (phi, 0, 0)
        txt.location = (0, -math.sin(phi) * 1.0, math.cos(phi) * 1.0)
        cutters.append(txt)

    for c in cutters[1:]:
        c.select_set(True)
    bpy.context.view_layer.objects.active = cutters[0]
    cutters[0].select_set(True)
    bpy.ops.object.join()
    cutter = bpy.context.object

    mod = drum.modifiers.new("engrave", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    bpy.context.view_layer.objects.active = drum
    bpy.ops.object.modifier_apply(modifier="engrave")
    cutter.hide_render = True
    cutter.hide_viewport = True

    # ink the engraving: every face of the band that sits below the turned
    # surface (recess floors and walls) takes the second material slot,
    # the way a real counter drum is engraved and then paint-filled —
    # otherwise the flat recess floor faces the camera square-on, catches
    # the key light, and the digit reads embossed instead of cut
    # NB mesh data is LOCAL: the 90-degree turn that lays the drum on its
    # side is an object transform, so in these coordinates the spindle is
    # the Z axis — axis distance is sqrt(x^2+y^2) and |z| walks the band,
    # with the end caps excluded by the z bound
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(drum.data)
    for f in bm.faces:
        c = f.calc_center_median()
        if (c.x ** 2 + c.y ** 2) ** 0.5 < 0.9925 and abs(c.z) < 0.329:
            f.material_index = 1
    bm.to_mesh(drum.data)
    bm.free()

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
    ink = bpy.data.materials.new("ink")
    ink.use_nodes = True
    ink_bsdf = ink.node_tree.nodes["Principled BSDF"]
    import os
    _dbg = os.environ.get("FORGE_DEBUG")
    ink_bsdf.inputs["Base Color"].default_value = (
        (1.0, 0.0, 0.0, 1) if _dbg else (0.01, 0.01, 0.011, 1))
    ink_bsdf.inputs["Metallic"].default_value = 0.0
    ink_bsdf.inputs["Roughness"].default_value = 0.9
    drum.data.materials.append(band_mat)
    drum.data.materials.append(ink)
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
    cam.data.ortho_scale = 1.28
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
    import os
    count = 1 if os.environ.get("FORGE_DEBUG") else 10
    for i in range(count):
        spindle.rotation_euler = (-2 * math.pi * i / 10, 0, 0)
        scene.render.filepath = str(RENDER_DIR / f"digit_{i}.png")
        bpy.ops.render.render(write_still=True)
        print(f"forged digit {i}")


# ======================================================================
# DRIVER SIDE
# ======================================================================
def digit_mask(ch: str) -> "Image":
    """The numeral, drawn at 4x in exact registration with the render.

    Blender centres the glyph bbox on the drum's front meridian; this
    centres the same glyph's bbox on the cell. The em size falls out of the
    camera maths — text_size * (CELL_H / ortho_scale) px per em — so the
    stamp lands on the engraving without measured constants. The engraving
    was cut with a fattened outline (+0.012 em per side), deliberately: the
    render's dark recess pokes out around this crisp core as a shadow ring,
    which is what sells the depth after the ink goes in.
    """
    from PIL import Image, ImageDraw, ImageFont
    ss = 4
    em = round(ss * 0.84 * (CELL_H / 1.28))
    fnt = ImageFont.truetype(str(FONT_TTF), em)
    m = Image.new("L", (CELL_W * ss, CELL_H * ss), 0)
    d = ImageDraw.Draw(m)
    bbox = d.textbbox((0, 0), ch, font=fnt)
    d.text((CELL_W * ss / 2 - (bbox[0] + bbox[2]) / 2,
            CELL_H * ss / 2 - (bbox[1] + bbox[3]) / 2), ch,
           font=fnt, fill=255)
    return m.resize((CELL_W, CELL_H), Image.LANCZOS)


def install_glyphs(write: bool) -> None:
    """Hybrid finish: Blender makes the metal, the stamp makes it legible.

    A pure render dies at 16px — denoise softness, neighbour slivers and
    specular noise eat the numeral. So the render supplies everything that
    should be physical (knurl, drum falloff, engraving shadow) and the ink
    is re-applied here at full contrast, in registration, with a lit lower
    lip — engraved-and-paint-filled, finished for the size it ships at.
    """
    import math as _m
    from PIL import Image, ImageChops, ImageFilter
    for i in range(10):
        src = RENDER_DIR / f"digit_{i}.png"
        img = Image.open(src).convert("L").resize(
            (CELL_W, CELL_H), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=110,
                                                 threshold=2))
        lum = img.point(lambda v: min(255, int((v / 255) ** 0.9 * 430)))
        # ink the numeral: multiply the steel down to paint-black
        mask = digit_mask("0123456789"[i])
        ink = mask.point(lambda v: 255 - (v * 235) // 255)
        lum = ImageChops.multiply(lum, ink)
        # lit lower lip under the cut
        lip = ImageChops.subtract(
            mask.transform(mask.size, Image.AFFINE, (1, 0, 0, 0, 1, -1)),
            mask)
        lum = ImageChops.add(lum, lip.point(lambda v: (v * 70) // 255))
        # aperture shading toward the slot edges: neighbours stay slivers
        px = lum.load()
        for y in range(CELL_H):
            t = abs(y - (CELL_H - 1) / 2) / (CELL_H / 2)
            k = 0.30 + 0.70 * max(0.0, _m.cos(min(1.0, t) * 1.15))
            for x in range(CELL_W):
                px[x, y] = int(px[x, y] * k)
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
    missing = [i for i in range(10)
               if not (RENDER_DIR / f"digit_{i}.png").exists()]
    if missing:
        sys.stderr.write(f"blender produced no renders for {missing}\n")
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
