#!/usr/bin/env python3
"""CHRONOVA photoreal layer renderer — Blender 4.5 LTS, Cycles CPU, headless.

Run:
    ~/Android/blender/blender-4.5.11-linux-x64/blender -b -noaudio \
        --python scripts/render_blender_layers.py

Re-renders the METAL components (gears, rings, ratchet, cam, fan, chassis,
plate, pistons, turbine/reactor housings) as physically-lit 3D renders with
transparent backgrounds, overwriting the PIL baseline in assets-source/<cat>/
AND app/src/main/res/drawable-nodpi/. Emissive sprites (blooms, packets, arcs,
conduits) and text panels stay procedural PIL — glow is cheap, metal is not.

Deterministic: fixed seeds, fixed camera/light rig. Every component renders at
2x final size, then Blender's film downsamples via render resolution.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets-source')
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')

# ---------------- scene rig ----------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.cycles.device = 'CPU'
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look = 'Medium High Contrast'

    # world: very dim so metal reads dark like the reference
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.022, 0.028, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.25

    # orthographic top-down camera
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    co.location = (0, 0, 10)
    sc.camera = co

    def light(name, loc, energy, size=6, color=(1, 1, 1)):
        li = bpy.data.lights.new(name, 'AREA')
        li.energy = energy
        li.size = size
        li.color = color
        lo = bpy.data.objects.new(name, li)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return lo

    # key top-left (matches PIL shading), cool fill right, rim
    light('key', (-4, 4, 8), 520, 7, (1.0, 1.0, 1.05))
    light('fill', (5, -2, 6), 250, 8, (0.75, 0.85, 1.0))
    light('rim', (0, -6, 3), 350, 3, (0.9, 0.95, 1.0))
    return sc


def render(name_cat, name_file, world_radius, px):
    """Render current scene: ortho scale fits world_radius, output px^2."""
    sc = bpy.context.scene
    sc.camera.data.ortho_scale = world_radius * 2.0
    sc.render.resolution_x = px
    sc.render.resolution_y = px
    out = os.path.join(SRC, name_cat, name_file)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    # copy into app resources
    import shutil
    shutil.copy(out, os.path.join(RES, name_file))
    print(f'RENDERED {name_cat}/{name_file} @ {px}px')


# ---------------- materials ----------------

def metal(name, base, rough=0.38, aniso=0.7, ring_bump=0.08, ring_scale=160):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough
    b.inputs['Anisotropic'].default_value = aniso
    # radial machining marks: wave rings -> bump
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'RINGS'
    wave.rings_direction = 'SPHERICAL'
    wave.inputs['Scale'].default_value = ring_scale
    wave.inputs['Distortion'].default_value = 9.0
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 300
    mixn = nt.nodes.new('ShaderNodeMix')
    mixn.data_type = 'FLOAT'
    mixn.inputs['Factor'].default_value = 0.5
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = ring_bump
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    nt.links.new(wave.outputs['Fac'], mixn.inputs['A'])
    nt.links.new(noise.outputs['Fac'], mixn.inputs['B'])
    nt.links.new(mixn.outputs['Result'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


STEEL = (0.048, 0.055, 0.068)
STEEL_D = (0.020, 0.023, 0.028)
BRASS = (0.45, 0.26, 0.07)


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------- geometry builders ----------------

def gear_outline(teeth, r_out, tooth_depth=0.13, points_per=6):
    """2D gear outline as list of (x, y) — same profile family as the PIL pass."""
    r_root = r_out * (1 - tooth_depth)
    pts = []
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        half = math.pi / teeth
        # root arc -> flank -> tip arc -> flank
        seq = [(a0 - half * 0.98, r_root), (a0 - half * 0.52, r_root),
               (a0 - half * 0.30, r_out), (a0 + half * 0.30, r_out),
               (a0 + half * 0.52, r_root), (a0 + half * 0.98, r_root)]
        for a, r in seq:
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def mesh_from_outline(name, pts, thickness=0.24, bevel=0.02):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, 0)) for x, y in pts]
    face = bm.faces.new(verts)
    bmesh.ops.triangulate(bm, faces=[face])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    sol = ob.modifiers.new('sol', 'SOLIDIFY')
    sol.thickness = thickness
    bev = ob.modifiers.new('bev', 'BEVEL')
    bev.width = bevel
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    return ob


def cylinder(name, r, depth, z=0, verts=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=(0, 0, z))
    ob = bpy.context.active_object
    ob.name = name
    bev = ob.modifiers.new('bev', 'BEVEL')
    bev.width = min(0.03, depth * 0.2)
    bev.segments = 2
    return ob


def torus(name, r_major, r_minor, z=0):
    bpy.ops.mesh.primitive_torus_add(major_radius=r_major, minor_radius=r_minor,
                                     location=(0, 0, z), major_segments=96,
                                     minor_segments=24)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def boolean_cut(target, cutter):
    mod = target.modifiers.new('cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    cutter.hide_render = True


def screws_ring(parent_r, count, r=0.05, z=0.14, mat=None):
    for i in range(count):
        a = 2 * math.pi * i / count + 0.4
        ob = cylinder(f'screw{i}', r, 0.06, z)
        ob.location = (parent_r * math.cos(a), parent_r * math.sin(a), z)
        slot = cylinder(f'slot{i}', r * 0.9, 0.02, z + 0.035)
        slot.scale = (1, 0.18, 1)
        slot.rotation_euler = (0, 0, a)
        assign(ob, mat)
        assign(slot, bpy.data.materials.get('void') or mat)


def make_void():
    m = bpy.data.materials.new('void')
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.005, 0.005, 0.007, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
    return m


# ---------------- component: gear ----------------

def build_gear(file_cat, file_name, px, teeth, style='steel', spokes=5,
               hub=0.22, unit=1.0):
    reset_scene()
    void = make_void()
    msteel = metal('steel', STEEL if style == 'steel' else STEEL_D,
                   rough=0.30 if style == 'steel' else 0.42, ring_scale=70)
    mbrass = metal('brass', BRASS, rough=0.28, ring_scale=110)
    body_m = mbrass if style == 'brass' else msteel

    r_out = unit
    ob = mesh_from_outline('gear', gear_outline(teeth, r_out), thickness=0.22)
    assign(ob, body_m)

    r_root = r_out * 0.87
    # spoke cutouts
    if spokes:
        r_hub = r_root * (hub + 0.16)
        r_rim = r_root * 0.8
        for i in range(spokes):
            a0 = 2 * math.pi * (i + 0.5) / spokes
            cut = cylinder(f'cut{i}', (r_rim - r_hub) * 0.42, 1.2)
            mid = (r_rim + r_hub) / 2
            cut.location = (mid * math.cos(a0), mid * math.sin(a0), 0)
            cut.scale = (1.5, 0.9, 1)
            cut.rotation_euler = (0, 0, a0)
            boolean_cut(ob, cut)

    # hub stack: plate, bearing, center pin
    hubp = cylinder('hub', r_root * hub, 0.30, 0.02)
    assign(hubp, msteel if style == 'brass' else metal('hub2', STEEL_D, 0.4))
    bear = torus('bearing', r_root * hub * 0.55, 0.035, 0.17)
    assign(bear, mbrass if style != 'brass' else msteel)
    pin = cylinder('pin', r_root * hub * 0.30, 0.36, 0.04)
    assign(pin, void)
    screws_ring(r_root * hub * 0.72, min(6, teeth // 3), z=0.17,
                mat=msteel if style == 'brass' else mbrass)
    render(file_cat, file_name, r_out * 1.02, px)


# ---------------- component: ring / housing ----------------

def build_ring(file_cat, file_name, px, width_frac=0.16, style='steel',
               bolts=0, segments=0, unit=1.0):
    reset_scene()
    void = make_void()
    m = metal('m', STEEL if style == 'steel' else STEEL_D,
              rough=0.33 if style == 'steel' else 0.45, ring_scale=60)
    mb = metal('brass', BRASS, rough=0.3)
    r1, r0 = unit, unit * (1 - width_frac)
    ring = cylinder('ring', r1, 0.26)
    hole = cylinder('hole', r0, 1.5)
    boolean_cut(ring, hole)
    assign(ring, m)
    if segments:
        for i in range(segments):
            a = 2 * math.pi * i / segments
            cut = cylinder(f'seg{i}', width_frac * unit * 0.35, 1.2)
            rm = (r0 + r1) / 2
            cut.location = (rm * math.cos(a), rm * math.sin(a), 0)
            boolean_cut(ring, cut)
    if bolts:
        screws_ring((r0 + r1) / 2, bolts, r=0.045 * unit, z=0.13, mat=mb)
    render(file_cat, file_name, unit * 1.03, px)


# ---------------- component: plate & chassis ----------------

def build_plate(px=960):
    reset_scene()
    m = metal('plate', (0.008, 0.009, 0.012), rough=0.55, ring_bump=0.05,
              ring_scale=40)
    disc = cylinder('disc', 1.0, 0.1, verts=128)
    assign(disc, m)
    # concentric cavity steps for depth
    for rr, dz in [(0.47, 0.05), (0.30, 0.09)]:
        cav = cylinder(f'cav{rr}', rr, 0.2, 0.05 - dz, verts=128)
        boolean_cut(disc, cav)
    render('chassis', 'plate_back.png', 1.0, px)


def build_chassis(px=960):
    reset_scene()
    void = make_void()
    m = metal('chassis', STEEL, rough=0.33, ring_scale=45)
    mb = metal('brass', BRASS, rough=0.3)

    objs = []
    # 8 radial bridges
    for k, ang in enumerate((0, 90, 180, 270, 45, 135, 225, 315)):
        a = math.radians(ang)
        wfrac = 0.13 if ang % 90 == 0 else 0.10
        bpy.ops.mesh.primitive_cube_add(size=1)
        br = bpy.context.active_object
        br.name = f'br{k}'
        bev = br.modifiers.new('bev', 'BEVEL'); bev.width = 0.012; bev.segments = 2
        br.scale = ((0.44 - 0.17), wfrac, 0.22)
        mid = (0.44 + 0.17) / 2
        br.location = (mid * math.cos(a), mid * math.sin(a), 0)
        br.rotation_euler = (0, 0, a)
        assign(br, m)
        objs.append(br)
    # central mount ring
    ring = cylinder('mount', 0.235, 0.24, verts=128)
    hole = cylinder('mhole', 0.155, 1.4, verts=128)
    boolean_cut(ring, hole)
    assign(ring, m)
    # outer rim
    rim = cylinder('rim', 0.478, 0.22, verts=160)
    rimh = cylinder('rimh', 0.448, 1.4, verts=160)
    boolean_cut(rim, rimh)
    assign(rim, m)
    # screws at bridge joints
    for ang in (0, 90, 180, 270, 45, 135, 225, 315):
        a = math.radians(ang)
        for rr in (0.20, 0.30, 0.40):
            s = cylinder(f's{ang}{rr}', 0.014, 0.05, 0.13)
            s.location = (rr * math.cos(a), rr * math.sin(a), 0.13)
            assign(s, mb)
    render('chassis', 'chassis.png', 0.5, px)


# ---------------- component: ratchet / cam / fan / pistons ----------------

def build_ratchet(px=180):
    reset_scene()
    m = metal('m', STEEL, rough=0.3, ring_scale=80)
    mb = metal('brass', BRASS)
    pts = []
    for i in range(20):
        a0 = 2 * math.pi * i / 20
        a1 = 2 * math.pi * (i + 1) / 20
        pts.append((0.96 * math.cos(a0), 0.96 * math.sin(a0)))
        pts.append((0.80 * math.cos(a1), 0.80 * math.sin(a1)))
    ob = mesh_from_outline('ratchet', pts, 0.2)
    assign(ob, m)
    hub = cylinder('hub', 0.40, 0.26, 0.02)
    assign(hub, metal('hd', STEEL_D, 0.45))
    pin = torus('ring', 0.40, 0.03, 0.15)
    assign(pin, mb)
    render('gears', 'ratchet.png', 1.0, px)


def build_cam(px=144):
    reset_scene()
    m = metal('m', STEEL, rough=0.3)
    ob = mesh_from_outline('cam', gear_outline(14, 1.0, 0.10), 0.2)
    assign(ob, m)
    off = cylinder('offb', 0.16, 0.3, 0.05)
    off.location = (0.42, 0, 0.05)
    assign(off, metal('bd', (0.01, 0.011, 0.013), 0.5))
    ring = torus('offr', 0.16, 0.025, 0.18)
    ring.location = (0.42, 0, 0.18)
    assign(ring, metal('brass', BRASS))
    render('gears', 'cam.png', 1.05, px)


def build_fan(px=168):
    reset_scene()
    m = metal('blade', (0.10, 0.11, 0.13), rough=0.25, aniso=0.9, ring_bump=0.15)
    for i in range(7):
        a = 2 * math.pi * i / 7
        bpy.ops.mesh.primitive_plane_add(size=1)
        b = bpy.context.active_object
        b.scale = (0.44, 0.14, 1)
        b.location = (0.40 * math.cos(a), 0.40 * math.sin(a), 0)
        b.rotation_euler = (0.45, 0, a)  # blade pitch
        sol = b.modifiers.new('s', 'SOLIDIFY')
        sol.thickness = 0.02
        assign(b, m)
    hub = cylinder('hub', 0.17, 0.16)
    assign(hub, metal('hub', STEEL_D, 0.4))
    cap = torus('cap', 0.17, 0.02, 0.08)
    assign(cap, metal('brass', BRASS))
    render('rotors', 'fan.png', 0.92, px)


def build_pistons():
    # sleeve
    reset_scene()
    m = metal('m', STEEL, 0.35, ring_scale=30)
    sl = cylinder('sleeve', 0.28, 1.5)
    sl.scale = (1, 1, 1)
    assign(sl, m)
    for zz in (-0.35, 0, 0.35):
        band = torus(f'b{zz}', 0.285, 0.02, zz)
        assign(band, metal('bd', STEEL_D, 0.45))
    bpy.context.scene.camera.data.type = 'ORTHO'
    # camera from side for the sleeve: rotate object instead
    sl.rotation_euler = (math.pi / 2, 0, 0)
    for o in bpy.context.scene.objects:
        if o.name.startswith('b'):
            o.rotation_euler = (math.pi / 2, 0, 0)
    render('pistons', 'piston_sleeve.png', 0.85, 72)
    # rod
    reset_scene()
    rod = cylinder('rod', 0.10, 1.6)
    assign(rod, metal('rm', (0.28, 0.30, 0.34), 0.2, aniso=0.95))
    crown = cylinder('crown', 0.22, 0.28, 0.8)
    assign(crown, metal('brass', BRASS, 0.3))
    rod.rotation_euler = (math.pi / 2, 0, 0)
    crown.rotation_euler = (math.pi / 2, 0, 0)
    crown.location = (0, 0.8, 0)
    render('pistons', 'piston_rod.png', 0.9, 32)


# ---------------- run all ----------------

def main():
    px2 = lambda final: final * 2
    build_plate(960)
    build_chassis(960)
    build_gear('gears', 'gear_rear_l.png', px2(260), 36, 'dark', 6)
    build_gear('gears', 'gear_rear_m.png', px2(150), 24, 'dark', 5)
    build_gear('gears', 'gear_a.png', px2(110), 22, 'steel', 5)
    build_gear('gears', 'gear_b.png', px2(84), 16, 'steel', 4)
    build_gear('gears', 'gear_c.png', px2(60), 12, 'brass', 3)
    build_gear('gears', 'gear_d.png', px2(44), 10, 'brass', 0)
    build_ratchet(180)
    build_cam(144)
    build_fan(168)
    build_ring('rotors', 'turbine_housing.png', px2(130), 0.30, 'steel', bolts=4)
    build_ring('reactor', 'reactor_housing.png', px2(210), 0.16, 'steel', bolts=8)
    build_ring('reactor', 'ring_outer_rot.png', px2(168), 0.13, 'dark', segments=8)
    build_ring('reactor', 'ring_inner_rot.png', px2(132), 0.15, 'steel', segments=6)
    build_pistons()
    print('ALL BLENDER LAYERS RENDERED')


main()
