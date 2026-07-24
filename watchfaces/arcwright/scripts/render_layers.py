"""ARCWRIGHT photoreal layer renderer — every visual layer is a Cycles render.

Evolved from Chronova's render_blender_layers.py with:
  - shared rig.py (HDRI reflections + one cool key) for global light coherence
  - materials v3: Pointiness edge-wear, AO recess grime, fine micro-bump
    mixed with the machining wave BEFORE one Bump node (the moire lesson)
  - displacement engraving (the technique proven on the digit glyphs) for the
    bezel numeral scale, display labels and the plate maker's mark
  - declarative REGISTRY with --only for sane iteration

Run AFTER scripts/gen_masks.py:
    ~/Android/blender/blender-4.5.11-linux-x64/blender -b -noaudio \
        --python scripts/render_layers.py [-- --only name1,name2]
"""
import math
import os
import shutil
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import PALETTE, reset_scene  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets-source')
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')
MASKS = os.path.join(SRC, 'masks')

# ---------------- materials v3 ----------------

def metal_v3(name, key, rough=None, aniso=0.5, ring_scale=90, ring_bump=0.10,
             wear=0.0, grime=0.0, seed=0.0):
    """Palette metal + machining bump + optional edge-wear and recess grime."""
    p = PALETTE[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = p['rough'] if rough is None else rough
    b.inputs['Anisotropic'].default_value = aniso
    # radial brushed tangent: the circular sheen of a machined watch part
    tan = nt_tangent = m.node_tree.nodes.new('ShaderNodeTangent')
    tan.direction_type = 'RADIAL'
    tan.axis = 'Z'
    m.node_tree.links.new(tan.outputs['Tangent'], b.inputs['Tangent'])

    tc = nt.nodes.new('ShaderNodeTexCoord')
    map_ = nt.nodes.new('ShaderNodeMapping')
    map_.inputs['Location'].default_value = (seed, seed * 0.7, 0)
    nt.links.new(tc.outputs['Object'], map_.inputs['Vector'])

    # machining rings + fine noise mixed pre-Bump (single Bump: no moire)
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'RINGS'
    wave.rings_direction = 'SPHERICAL'
    wave.inputs['Scale'].default_value = ring_scale
    wave.inputs['Distortion'].default_value = 9.0
    fine = nt.nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 420
    mixh = nt.nodes.new('ShaderNodeMix')
    mixh.data_type = 'FLOAT'
    mixh.inputs['Factor'].default_value = 0.45
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = ring_bump
    nt.links.new(map_.outputs['Vector'], wave.inputs['Vector'])
    nt.links.new(map_.outputs['Vector'], fine.inputs['Vector'])
    nt.links.new(wave.outputs['Fac'], mixh.inputs['A'])
    nt.links.new(fine.outputs['Fac'], mixh.inputs['B'])
    nt.links.new(mixh.outputs['Result'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])

    base = nt.nodes.new('ShaderNodeRGB')
    base.outputs[0].default_value = (*p['base'], 1)
    color_out = base.outputs[0]

    if wear:
        # convex edges polish bright (Pointiness). Flat faces sit at ~0.5 —
        # the ramp must start ABOVE that or wear smears everywhere.
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.56
        ramp.color_ramp.elements[1].position = 0.70
        scale = nt.nodes.new('ShaderNodeMath')
        scale.operation = 'MULTIPLY'
        scale.inputs[1].default_value = wear
        bright = nt.nodes.new('ShaderNodeRGB')
        bright.outputs[0].default_value = (*PALETTE['polished']['base'], 1)
        mixw = nt.nodes.new('ShaderNodeMixRGB')
        nt.links.new(geo.outputs['Pointiness'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], scale.inputs[0])
        nt.links.new(scale.outputs['Value'], mixw.inputs['Fac'])
        nt.links.new(color_out, mixw.inputs['Color1'])
        nt.links.new(bright.outputs[0], mixw.inputs['Color2'])
        color_out = mixw.outputs['Color']

    if grime:
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.inputs['Distance'].default_value = 0.15
        inv = nt.nodes.new('ShaderNodeInvert')
        dark = nt.nodes.new('ShaderNodeRGB')
        dark.outputs[0].default_value = (*PALETTE['dark_fill']['base'], 1)
        mixg = nt.nodes.new('ShaderNodeMixRGB')
        nt.links.new(ao.outputs['AO'], inv.inputs['Color'])
        nt.links.new(inv.outputs['Color'], mixg.inputs['Fac'])
        mixg.inputs['Fac'].default_value = 0
        nt.links.new(inv.outputs['Color'], mixg.inputs['Fac'])
        nt.links.new(color_out, mixg.inputs['Color1'])
        nt.links.new(dark.outputs[0], mixg.inputs['Color2'])
        color_out = mixg.outputs['Color']

    nt.links.new(color_out, b.inputs['Base Color'])
    return m


def make_void():
    m = bpy.data.materials.new('void')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*PALETTE['dark_fill']['base'], 1)
    b.inputs['Roughness'].default_value = PALETTE['dark_fill']['rough']
    return m


def dark_glass():
    m = bpy.data.materials.new('glass')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.02, 0.022, 0.03, 1)
    b.inputs['Roughness'].default_value = 0.12
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['IOR'].default_value = 1.45
    return m


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ---------------- geometry ----------------

def gear_outline(teeth, r_out, tooth_depth=0.13):
    """Filleted tooth profile: root fillet -> flank -> tip chamfer."""
    r_root = r_out * (1 - tooth_depth)
    r_fil = r_root * 1.015
    r_tip = r_out * 0.995
    pts = []
    for i in range(teeth):
        a0 = 2 * math.pi * i / teeth
        half = math.pi / teeth
        seq = [(a0 - half * 0.98, r_root), (a0 - half * 0.60, r_root),
               (a0 - half * 0.54, r_fil),                       # root fillet
               (a0 - half * 0.30, r_out), (a0 - half * 0.24, r_tip),  # tip chamfer
               (a0 + half * 0.24, r_tip), (a0 + half * 0.30, r_out),
               (a0 + half * 0.54, r_fil),
               (a0 + half * 0.60, r_root), (a0 + half * 0.98, r_root)]
        for a, r in seq:
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def mesh_from_outline(name, pts, thickness=0.22, bevel=0.02):
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
    bev.segments = 4
    bev.limit_method = 'ANGLE'
    return ob


def cylinder(name, r, depth, z=0, verts=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=(0, 0, z))
    ob = bpy.context.active_object
    ob.name = name
    bev = ob.modifiers.new('bev', 'BEVEL')
    bev.width = min(0.03, depth * 0.2)
    bev.segments = 3
    return ob


def torus(name, r_major, r_minor, z=0):
    bpy.ops.mesh.primitive_torus_add(major_radius=r_major, minor_radius=r_minor,
                                     location=(0, 0, z), major_segments=96,
                                     minor_segments=24)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def box(name, sx, sy, sz, loc=(0, 0, 0), rz=0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, sy, sz)
    ob.location = loc
    ob.rotation_euler = (0, 0, rz)
    bev = ob.modifiers.new('bev', 'BEVEL')
    bev.width = 0.012
    bev.segments = 3
    return ob


def boolean_cut(target, cutter):
    mod = target.modifiers.new('cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    cutter.hide_render = True


def screws_ring(parent_r, count, r=0.05, z=0.14, mat=None, void=None, phase=0.4):
    for i in range(count):
        a = 2 * math.pi * i / count + phase
        ob = cylinder(f'screw{i}', r, 0.06, z)
        ob.location = (parent_r * math.cos(a), parent_r * math.sin(a), z)
        slot = cylinder(f'slot{i}', r * 0.9, 0.02, z + 0.035)
        slot.scale = (1, 0.18, 1)
        slot.rotation_euler = (0, 0, a + i * 1.7)   # slots at "worked" angles
        assign(ob, mat)
        assign(slot, void or mat)


def engraving_mix(m, mask_name, uv_from='UV'):
    """Wire disp/fill masks of `mask_name` into material m's base color
    (bright-cut chamfer + dark fill floor), returns the disp image."""
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    prev = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
    tc = nt.nodes.new('ShaderNodeTexCoord')
    t_disp = nt.nodes.new('ShaderNodeTexImage')
    t_disp.image = bpy.data.images.load(os.path.join(MASKS, f'disp_{mask_name}.png'))
    t_fill = nt.nodes.new('ShaderNodeTexImage')
    t_fill.image = bpy.data.images.load(os.path.join(MASKS, f'fill_{mask_name}.png'))
    for t in (t_disp, t_fill):
        t.extension = 'EXTEND'
        nt.links.new(tc.outputs[uv_from], t.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[1].position = 0.60
    nt.links.new(t_disp.outputs['Color'], ramp.inputs['Fac'])
    cut = nt.nodes.new('ShaderNodeRGB')
    cut.outputs[0].default_value = (*PALETTE['polished']['base'], 1)
    dark = nt.nodes.new('ShaderNodeRGB')
    dark.outputs[0].default_value = (*PALETTE['dark_fill']['base'], 1)
    mix1 = nt.nodes.new('ShaderNodeMixRGB')
    nt.links.new(ramp.outputs['Color'], mix1.inputs['Fac'])
    if prev is not None:
        nt.links.new(prev, mix1.inputs['Color1'])
    else:
        mix1.inputs['Color1'].default_value = b.inputs['Base Color'].default_value
    nt.links.new(cut.outputs[0], mix1.inputs['Color2'])
    mix2 = nt.nodes.new('ShaderNodeMixRGB')
    nt.links.new(t_fill.outputs['Color'], mix2.inputs['Fac'])
    nt.links.new(mix1.outputs['Color'], mix2.inputs['Color1'])
    nt.links.new(dark.outputs[0], mix2.inputs['Color2'])
    nt.links.new(mix2.outputs['Color'], b.inputs['Base Color'])
    return t_disp.image


def engrave(obj, image, depth=0.035):
    tex = bpy.data.textures.new('eng', type='IMAGE')
    tex.image = image
    tex.extension = 'EXTEND'
    mod = obj.modifiers.new('engrave', type='DISPLACE')
    mod.texture = tex
    mod.texture_coords = 'UV'
    mod.strength = -depth
    mod.mid_level = 0.0


def dense_disc(name, r, hole_r=0.0, grid=380):
    """UV'd dense square grid trimmed to a disc/annulus (for engraving)."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=grid, y_subdivisions=grid,
                                    size=2 * r)
    ob = bpy.context.active_object
    ob.name = name
    trim = cylinder('trim', r, 2.0, verts=160)
    mod = ob.modifiers.new('keep', 'BOOLEAN')
    mod.operation = 'INTERSECT'
    mod.object = trim
    trim.hide_render = True
    if hole_r:
        hole = cylinder('hole', hole_r, 2.2, verts=160)
        boolean_cut(ob, hole)
    return ob


def render(cat, file, world_w, px_w, world_h=None, px_h=None):
    """world_w/world_h are RADII (half-extents), Chronova convention."""
    sc = bpy.context.scene
    world_h = world_h or world_w
    px_h = px_h or px_w
    sc.camera.data.ortho_scale = max(world_w, world_h) * 2.0
    sc.render.resolution_x = px_w
    sc.render.resolution_y = px_h
    out = os.path.join(SRC, cat, file)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    shutil.copy(out, os.path.join(RES, file))
    print(f'RENDERED {cat}/{file} @ {px_w}x{px_h}', flush=True)


# ---------------- builders ----------------

def build_plate():
    reset_scene(samples=224)
    m = metal_v3('plate', 'blued_steel', ring_scale=42, ring_bump=0.04,
                 aniso=0.6, grime=0.4)
    disc = dense_disc('disc', 1.0, grid=420)
    img = engraving_mix(m, 'makers')
    engrave(disc, img, depth=0.020)
    assign(disc, m)
    # cavity steps for depth (carved as real geometry below the engraved top)
    for rr, dz in [(0.47, 0.06), (0.30, 0.10)]:
        cav = cylinder(f'cav{rr}', rr, 0.2, -0.1 - dz, verts=128)
        boolean_cut(disc, cav)
    render('chassis', 'plate_back.png', 1.0, 960)


def build_bezel():
    reset_scene(samples=224)
    m = metal_v3('bezel', 'gunmetal', ring_scale=55, aniso=0.6,
                 wear=0.35, grime=0.3)
    ring = dense_disc('bezel', 1.0, hole_r=0.795, grid=460)
    img = engraving_mix(m, 'bezel')
    engrave(ring, img, depth=0.030)
    assign(ring, m)
    render('chassis', 'bezel_ring60.png', 1.0, 960)


def build_chassis():
    reset_scene(samples=224)
    void = make_void()
    m = metal_v3('chassis', 'gunmetal', ring_scale=45, wear=0.4, grime=0.45)
    mb = metal_v3('screwm', 'worn_brass', ring_scale=120, wear=0.5)
    for k, ang in enumerate((0, 90, 180, 270, 45, 135, 225, 315)):
        a = math.radians(ang)
        wfrac = 0.13 if ang % 90 == 0 else 0.10
        mid = (0.44 + 0.17) / 2
        br = box(f'br{k}', 0.44 - 0.17, wfrac, 0.22,
                 (mid * math.cos(a), mid * math.sin(a), 0), a)
        assign(br, m)
    ring = cylinder('mount', 0.235, 0.24, verts=128)
    hole = cylinder('mhole', 0.155, 1.4, verts=128)
    boolean_cut(ring, hole)
    assign(ring, m)
    rim = cylinder('rim', 0.478, 0.22, verts=160)
    rimh = cylinder('rimh', 0.448, 1.4, verts=160)
    boolean_cut(rim, rimh)
    assign(rim, m)
    for ang in (0, 90, 180, 270, 45, 135, 225, 315):
        a = math.radians(ang)
        for rr in (0.20, 0.30, 0.40):
            s = cylinder(f's{ang}{rr}', 0.014, 0.05, 0.13)
            s.location = (rr * math.cos(a), rr * math.sin(a), 0.13)
            assign(s, mb)
    render('chassis', 'chassis.png', 0.5, 960)


def build_gear(file, px, teeth, style='brass', spokes=5, hub=0.22, seed=0.0):
    reset_scene(samples=192)
    void = make_void()
    msteel = metal_v3('steel', 'blued_steel', ring_scale=70, wear=0.3,
                      grime=0.3, seed=seed)
    mbrass = metal_v3('brass', 'worn_brass', ring_scale=110, ring_bump=0.16,
                      aniso=0.85, wear=0.55, grime=0.5, seed=seed)
    mdark = metal_v3('darks', 'gunmetal', rough=0.42, ring_scale=70,
                     wear=0.25, grime=0.4, seed=seed)
    body = {'brass': mbrass, 'steel': msteel, 'dark': mdark}[style]

    ob = mesh_from_outline('gear', gear_outline(teeth, 1.0), thickness=0.22)
    assign(ob, body)
    r_root = 0.87
    if spokes:
        r_hub, r_rim = r_root * (hub + 0.16), r_root * 0.8
        for i in range(spokes):
            a0 = 2 * math.pi * (i + 0.5) / spokes
            cut = cylinder(f'cut{i}', (r_rim - r_hub) * 0.42, 1.2)
            mid = (r_rim + r_hub) / 2
            cut.location = (mid * math.cos(a0), mid * math.sin(a0), 0)
            cut.scale = (1.5, 0.9, 1)
            cut.rotation_euler = (0, 0, a0)
            boolean_cut(ob, cut)
    hubp = cylinder('hub', r_root * hub, 0.30, 0.02)
    assign(hubp, msteel if style == 'brass' else mdark)
    bear = torus('bearing', r_root * hub * 0.55, 0.035, 0.17)
    assign(bear, mbrass if style != 'brass' else msteel)
    pin = cylinder('pin', r_root * hub * 0.30, 0.36, 0.04)
    assign(pin, void)
    screws_ring(r_root * hub * 0.72, min(6, teeth // 3), z=0.17,
                mat=msteel if style == 'brass' else mbrass, void=void)
    render('gears', file, 1.02, px)


def build_ring(cat, file, px, width_frac=0.16, style='gunmetal', bolts=0,
               segments=0):
    reset_scene(samples=192)
    void = make_void()
    m = metal_v3('m', style, ring_scale=60, wear=0.35, grime=0.35)
    mb = metal_v3('brass', 'worn_brass', ring_scale=120, wear=0.5)
    r1, r0 = 1.0, 1.0 - width_frac
    ring = cylinder('ring', r1, 0.26)
    hole = cylinder('hole', r0, 1.5)
    boolean_cut(ring, hole)
    assign(ring, m)
    if segments:
        for i in range(segments):
            a = 2 * math.pi * i / segments
            cut = cylinder(f'seg{i}', width_frac * 0.35, 1.2)
            rm = (r0 + r1) / 2
            cut.location = (rm * math.cos(a), rm * math.sin(a), 0)
            boolean_cut(ring, cut)
    if bolts:
        screws_ring((r0 + r1) / 2, bolts, r=0.045, z=0.13, mat=mb, void=void)
    render(cat, file, 1.03, px)


def build_index_ring(file, px, marks, accent_first=False):
    reset_scene(samples=160)
    void = make_void()
    m = metal_v3('m', 'blued_steel', rough=0.4, ring_scale=50, grime=0.3)
    ring = cylinder('ring', 1.0, 0.10)
    hole = cylinder('hole', 0.90, 1.2)
    boolean_cut(ring, hole)
    assign(ring, m)
    for i in range(marks):
        a = 2 * math.pi * i / marks - math.pi / 2
        rm = 0.95
        s = box(f'n{i}', 0.035, 0.008, 0.08,
                (rm * math.cos(a), rm * math.sin(a), 0.06), a)
        assign(s, make_void() if i else metal_v3('acc', 'polished', seed=i))
    render('gears', file, 1.02, px)


def build_ratchet():
    reset_scene(samples=192)
    m = metal_v3('m', 'blued_steel', ring_scale=80, wear=0.35, grime=0.35)
    mb = metal_v3('brass', 'worn_brass', wear=0.5)
    pts = []
    for i in range(20):
        a0 = 2 * math.pi * i / 20
        a1 = 2 * math.pi * (i + 1) / 20
        pts.append((0.96 * math.cos(a0), 0.96 * math.sin(a0)))
        pts.append((0.80 * math.cos(a1), 0.80 * math.sin(a1)))
    ob = mesh_from_outline('ratchet', pts, 0.2)
    assign(ob, m)
    hub = cylinder('hub', 0.40, 0.26, 0.02)
    assign(hub, metal_v3('hd', 'gunmetal', rough=0.45))
    pin = torus('ring', 0.40, 0.03, 0.15)
    assign(pin, mb)
    render('gears', 'ratchet.png', 1.0, 180)


def build_cam():
    reset_scene(samples=192)
    m = metal_v3('m', 'blued_steel', ring_scale=70, wear=0.35, grime=0.3)
    ob = mesh_from_outline('cam', gear_outline(14, 1.0, 0.10), 0.2)
    assign(ob, m)
    off = cylinder('offb', 0.16, 0.3, 0.05)
    off.location = (0.42, 0, 0.05)
    assign(off, make_void())
    ring = torus('offr', 0.16, 0.025, 0.18)
    ring.location = (0.42, 0, 0.18)
    assign(ring, metal_v3('brass', 'worn_brass', wear=0.5))
    render('gears', 'cam.png', 1.05, 144)


def build_fan():
    reset_scene(samples=192)
    m = metal_v3('blade', 'gunmetal', rough=0.25, aniso=0.9, ring_bump=0.10,
                 wear=0.45)
    for i in range(7):
        a = 2 * math.pi * i / 7
        bpy.ops.mesh.primitive_plane_add(size=1)
        b = bpy.context.active_object
        b.scale = (0.44, 0.14, 1)
        b.location = (0.40 * math.cos(a), 0.40 * math.sin(a), 0)
        b.rotation_euler = (0.45, 0, a)
        sol = b.modifiers.new('s', 'SOLIDIFY')
        sol.thickness = 0.02
        assign(b, m)
    hub = cylinder('hub', 0.17, 0.16)
    assign(hub, metal_v3('hub', 'blued_steel', rough=0.4))
    cap = torus('cap', 0.17, 0.02, 0.08)
    assign(cap, metal_v3('brass', 'worn_brass', wear=0.5))
    render('rotors', 'fan.png', 0.92, 168)


def build_pistons():
    reset_scene(samples=192)
    m = metal_v3('m', 'blued_steel', ring_scale=30, grime=0.3)
    sl = cylinder('sleeve', 0.28, 1.5)
    assign(sl, m)
    bands = []
    for zz in (-0.35, 0, 0.35):
        band = torus(f'band{zz}', 0.285, 0.02, zz)
        assign(band, metal_v3(f'bd{zz}', 'gunmetal', rough=0.45))
        bands.append(band)
    sl.rotation_euler = (math.pi / 2, 0, 0)
    for o in bands:
        o.rotation_euler = (math.pi / 2, 0, 0)
    render('pistons', 'piston_sleeve.png', 0.85, 72, 0.85, 140)
    reset_scene(samples=192)
    rod = cylinder('rod', 0.10, 1.6)
    assign(rod, metal_v3('rm', 'polished', rough=0.22, aniso=0.95))
    crown = cylinder('crown', 0.22, 0.28, 0.8)
    assign(crown, metal_v3('brass', 'worn_brass', wear=0.5))
    rod.rotation_euler = (math.pi / 2, 0, 0)
    crown.rotation_euler = (math.pi / 2, 0, 0)
    crown.location = (0, 0.8, 0)
    render('pistons', 'piston_rod.png', 0.9, 32, 0.9, 120)


def build_display_bezel(file, mask, world_w, world_h, px_w, px_h):
    """Gunmetal frame + flush blued digit well + engraved label strip."""
    reset_scene(samples=224)
    void = make_void()
    mf = metal_v3('frame', 'gunmetal', ring_scale=60, wear=0.4, grime=0.4)
    frame = box('frame', world_w, world_h, 0.16)
    well = box('well', world_w * 0.86, world_h * 0.62, 0.4, (0, world_h * 0.06, 0.06))
    boolean_cut(frame, well)
    assign(frame, mf)
    # flush blued floor where the digit tiles composite (matches glyph tiles)
    mw = metal_v3('wellm', 'blued_steel', ring_scale=42, ring_bump=0.04, aniso=0.6)
    floor = box('floor', world_w * 0.86, world_h * 0.62, 0.02,
                (0, world_h * 0.06, -0.06))
    assign(floor, mw)
    # engraved label strip along the bottom edge of the frame
    ml = metal_v3('labelm', 'gunmetal', ring_scale=60)
    strip_h = world_h * 0.16
    strip = dense_disc  # noqa: F841  (grid helper below)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=240, y_subdivisions=48,
                                    size=1)
    lab = bpy.context.active_object
    lab.scale = (world_w * 0.7, strip_h, 1)
    lab.location = (0, -world_h * 0.335, 0.081)
    img = engraving_mix(ml, mask)
    engrave(lab, img, depth=0.012)
    assign(lab, ml)
    # corner screws
    mb = metal_v3('brass', 'worn_brass', wear=0.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s = cylinder(f'cs{sx}{sy}', 0.022, 0.05, 0.09)
            s.location = (sx * (world_w / 2 - 0.045),
                          sy * (world_h / 2 - 0.045), 0.09)
            assign(s, mb)
    render('displays', file, world_w / 2, px_w, world_h / 2, px_h)


def build_conduit():
    """Metal channel + smoked-glass tube, dark at rest (arcs light it later)."""
    reset_scene(samples=224)
    void = make_void()
    m = metal_v3('chan', 'gunmetal', ring_scale=40, wear=0.4, grime=0.4)
    W, H = 1.5, 0.46
    chan = box('chan', W, H, 0.14)
    trough = box('trough', W * 0.94, H * 0.52, 0.4, (0, 0, 0.06))
    boolean_cut(chan, trough)
    assign(chan, m)
    tube = cylinder('tube', H * 0.20, W * 0.92)
    tube.rotation_euler = (0, math.pi / 2, 0)
    assign(tube, dark_glass())
    mb = metal_v3('brass', 'worn_brass', wear=0.5)
    for sx in (-1, 1):
        collar = cylinder(f'col{sx}', H * 0.30, 0.12)
        collar.rotation_euler = (0, math.pi / 2, 0)
        collar.location = (sx * W * 0.40, 0, 0)
        assign(collar, mb)
    render('conduits', 'conduit_housing.png', W / 2, 300, H / 2, 92)


# ---------------- registry ----------------

REGISTRY = [
    ('plate', build_plate),
    ('bezel', build_bezel),
    ('chassis', build_chassis),
    ('gear_rear_l', lambda: build_gear('gear_rear_l.png', 520, 36, 'dark', 6, seed=1.1)),
    ('gear_rear_m', lambda: build_gear('gear_rear_m.png', 300, 24, 'dark', 5, seed=2.2)),
    ('gear_a', lambda: build_gear('gear_a.png', 220, 22, 'brass', 5, seed=3.3)),
    ('gear_b', lambda: build_gear('gear_b.png', 168, 16, 'steel', 4, seed=4.4)),
    ('gear_c', lambda: build_gear('gear_c.png', 120, 12, 'brass', 3, seed=5.5)),
    ('gear_d', lambda: build_gear('gear_d.png', 88, 10, 'brass', 0, seed=6.6)),
    ('ratchet', build_ratchet),
    ('cam', build_cam),
    ('fan', build_fan),
    ('turbine_housing', lambda: build_ring('rotors', 'turbine_housing.png', 260, 0.30, 'gunmetal', bolts=4)),
    ('chamber_housing', lambda: build_ring('chamber', 'chamber_housing.png', 420, 0.16, 'gunmetal', bolts=8)),
    ('ring_outer_rot', lambda: build_ring('chamber', 'ring_outer_rot.png', 336, 0.13, 'blued_steel', segments=8)),
    ('ring_inner_rot', lambda: build_ring('chamber', 'ring_inner_rot.png', 264, 0.15, 'gunmetal', segments=6)),
    ('ring_hour', lambda: build_index_ring('ring_hour.png', 504, 12)),
    ('ring_min', lambda: build_index_ring('ring_min.png', 572, 60)),
    ('pistons', build_pistons),
    ('display_hrs', lambda: build_display_bezel('display_hrs.png', 'label_hrs', 1.36, 0.96, 272, 192)),
    ('display_min', lambda: build_display_bezel('display_min.png', 'label_min', 1.36, 0.96, 272, 192)),
    ('display_sec', lambda: build_display_bezel('display_sec.png', 'label_sec', 1.04, 0.76, 208, 152)),
    ('conduit', build_conduit),
]


def main():
    only = None
    if '--only' in sys.argv:
        only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
    for name, fn in REGISTRY:
        if only and name not in only:
            continue
        fn()
    print('ALL ARCWRIGHT LAYERS RENDERED')


if __name__ == '__main__':
    main()
