"""ARCWRIGHT assembly renderer — the WHOLE watch in ONE Cycles scene.

Kills the sticker-sheet look of per-part renders: the static base is one
integrated render with full GI (contact shadows, inter-reflections), and
every moving part is rendered IN PLACE — neighbors set visible_camera=False
so the sprite carries its true neighborhood lighting without baking neighbor
pixels. Moving parts stay invisible-to-camera in the base render but keep
shadowing it, so each sprite lands on its own pre-baked contact shadow.

Run AFTER gen_masks.py:
    blender -b -noaudio --python scripts/assembly.py [-- --only base,nw_gear_a]
"""
import math
import os
import shutil
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_layers as RL  # noqa: E402
from rig import reset_scene  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets-source')
RES = os.path.join(ROOT, 'app/src/main/res/drawable-nodpi')

S = 0.01  # 1 screen px = 0.01 world units


def W(sx, sy, z=0.0):
    """Screen (x down-right) -> world (y up)."""
    return ((sx - 240) * S, (240 - sy) * S, z)


# neutralize the standalone-mode scene calls inside RL builders
RL.reset_scene = lambda **k: bpy.context.scene
RL.render = lambda *a, **k: None

PARTS = {}          # name -> list of objects (subtree)


class part:
    def __init__(self, name, scale, at, rz=0.0):
        self.name, self.scale, self.at, self.rz = name, scale, at, rz

    def __enter__(self):
        self.before = set(bpy.data.objects)
        return self

    def __exit__(self, *exc):
        new = [o for o in bpy.data.objects if o not in self.before]
        root = bpy.data.objects.new(f'{self.name}_root', None)
        bpy.context.scene.collection.objects.link(root)
        for o in new:
            if o.parent is None:
                o.parent = root
        root.scale = (self.scale,) * 3
        root.location = self.at
        root.rotation_euler = (0, 0, self.rz)
        PARTS[self.name] = [o for o in new if o.type == 'MESH']


def sprite_scale(final_px, local_radius):
    return (final_px / 2) * S / local_radius


def build_world():
    reset_scene(samples=256)

    # ---- static deck ----
    with part('plate', 2.4, W(240, 240, 0.0)):
        RL.build_plate()
    with part('chassis', 4.8, W(240, 240, 0.20)):
        RL.build_chassis()
    with part('bezel', 2.4, W(240, 240, 0.21)):
        RL.build_bezel()
    with part('turbine_housing', sprite_scale(130, 1.03), W(240, 88, 0.27)):
        RL.build_ring('rotors', 'x', 0, 0.30, 'gunmetal', bolts=4)
    with part('chamber', sprite_scale(210, 1.03), W(240, 240, 0.26)):
        RL.build_ring('chamber', 'x', 0, 0.16, 'gunmetal', bolts=8)
    for nm, sx, sy, ang in [('cond_nw', 112, 112, 45), ('cond_ne', 368, 112, -45),
                            ('cond_sw', 112, 368, -45), ('cond_se', 368, 368, 45)]:
        with part(nm, sprite_scale(130, 0.75), W(sx, sy, 0.24), math.radians(ang)):
            RL.build_conduit()
    with part('disp_hrs', 1.0, W(88, 240, 0.30)):
        RL.build_display_bezel('x', 'label_hrs', 1.36, 0.96, 0, 0)
    with part('disp_min', 1.0, W(392, 240, 0.30)):
        RL.build_display_bezel('x', 'label_min', 1.36, 0.96, 0, 0)
    with part('disp_sec', 1.0, W(240, 404, 0.30)):
        RL.build_display_bezel('x', 'label_sec', 1.04, 0.76, 0, 0)
    for i, sx in enumerate((206, 274)):
        with part(f'sleeve_{i}', sprite_scale(36, 0.28), W(sx, 345, 0.24)):
            # sleeve: local cylinder r0.28, side-on; len 1.09 -> 70px on screen
            m = RL.metal_v3('m', 'blued_steel', ring_scale=30, grime=0.3)
            sl = RL.cylinder('sleeve', 0.28, 1.09)
            RL.assign(sl, m)
            for zz in (-0.35, 0, 0.35):
                band = RL.torus(f'band{zz}', 0.285, 0.02, zz)
                RL.assign(band, RL.metal_v3(f'bd{zz}', 'gunmetal', rough=0.45))
                band.rotation_euler = (math.pi / 2, 0, 0)
            sl.rotation_euler = (math.pi / 2, 0, 0)

    # ---- moving parts (each becomes an in-place sprite) ----
    MOV = [
        ('gear_rear_l', 166, 306, 260, lambda: RL.build_gear('x', 0, 36, 'dark', 6, seed=1.1), 1.02, 0.06),
        ('gear_rear_m', 330, 176, 150, lambda: RL.build_gear('x', 0, 24, 'dark', 5, seed=2.2), 1.02, 0.06),
        ('ring_hour', 240, 240, 252, lambda: RL.build_index_ring('x', 0, 12), 1.02, 0.23),
        ('ring_min', 240, 240, 286, lambda: RL.build_index_ring('x', 0, 60), 1.02, 0.22),
        ('nw_gear_a', 138, 148, 110, lambda: RL.build_gear('x', 0, 22, 'brass', 5, seed=3.3), 1.02, 0.26),
        ('nw_gear_c', 204, 196, 60, lambda: RL.build_gear('x', 0, 12, 'brass', 3, seed=5.5), 1.02, 0.27),
        ('ne_gear_a', 342, 148, 110, lambda: RL.build_gear('x', 0, 22, 'brass', 5, seed=3.7), 1.02, 0.26),
        ('ne_gear_c', 276, 196, 60, lambda: RL.build_gear('x', 0, 12, 'brass', 3, seed=5.9), 1.02, 0.27),
        ('ratchet', 135, 332, 90, RL.build_ratchet, 1.0, 0.26),
        ('sw_gear_d', 192, 368, 44, lambda: RL.build_gear('x', 0, 10, 'brass', 0, seed=6.6), 1.02, 0.27),
        ('se_gear_b', 342, 332, 84, lambda: RL.build_gear('x', 0, 16, 'steel', 4, seed=4.4), 1.02, 0.26),
        ('cam', 286, 368, 72, RL.build_cam, 1.05, 0.27),
        ('fan', 240, 88, 84, RL.build_fan, 0.92, 0.25),
        ('ring_outer', 240, 240, 168, lambda: RL.build_ring('chamber', 'x', 0, 0.13, 'blued_steel', segments=8), 1.03, 0.30),
        ('ring_inner', 240, 240, 132, lambda: RL.build_ring('chamber', 'x', 0, 0.15, 'gunmetal', segments=6), 1.03, 0.34),
        ('rod_0', 206, 330, 60, None, 1.0, 0.25),
        ('rod_1', 274, 330, 60, None, 1.0, 0.25),
    ]
    moving = {}
    for name, sx, sy, px, fn, local_r, z in MOV:
        if fn is None:      # piston rod, built inline
            with part(name, sprite_scale(px, 0.9), W(sx, sy, z)):
                rod = RL.cylinder('rod', 0.10, 1.6)
                RL.assign(rod, RL.metal_v3('rm', 'polished', rough=0.22, aniso=0.95))
                crown = RL.cylinder('crown', 0.22, 0.28, 0.8)
                RL.assign(crown, RL.metal_v3('brass', 'worn_brass', wear=0.5))
                rod.rotation_euler = (math.pi / 2, 0, 0)
                crown.rotation_euler = (math.pi / 2, 0, 0)
                crown.location = (0, 0.8, 0)
        else:
            with part(name, sprite_scale(px, local_r), W(sx, sy, z)):
                fn()
        moving[name] = (sx, sy, px)
    return moving


def set_camera(cx, cy, half_px):
    sc = bpy.context.scene
    sc.camera.location = (*W(cx, cy)[:2], 10)
    sc.camera.data.ortho_scale = half_px * 2 * S


def save(file, px_w, px_h=None):
    sc = bpy.context.scene
    sc.render.resolution_x = px_w
    sc.render.resolution_y = px_h or px_w
    out = os.path.join(SRC, 'assembly', file)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    shutil.copy(out, os.path.join(RES, file))
    print(f'RENDERED assembly/{file}', flush=True)


def main():
    only = None
    if '--only' in sys.argv:
        only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
    moving = build_world()
    all_meshes = [o for objs in PARTS.values() for o in objs]

    # TWO static slabs so under-chassis sprites keep correct occlusion:
    #   base_lower = plate only (carries everyone's contact shadows)
    #   base_upper = chassis and everything above it (alpha where plate shows)
    # Moving parts stay shadow-only in both.
    lower_statics = {'plate'}
    if not only or 'base_lower' in only:
        for o in all_meshes:
            o.visible_camera = False
        for nm in lower_statics:
            for o in PARTS[nm]:
                o.visible_camera = True
        set_camera(240, 240, 240)
        save('base_lower.png', 960)
    if not only or 'base_upper' in only:
        for o in all_meshes:
            o.visible_camera = True
        for nm in list(moving) + list(lower_statics):
            for o in PARTS[nm]:
                o.visible_camera = False
        set_camera(240, 240, 240)
        save('base_upper.png', 960)

    # each moving part in place: only its own subtree camera-visible
    for name, (sx, sy, px) in moving.items():
        if only and name not in only:
            continue
        for o in all_meshes:
            o.visible_camera = False
        for o in PARTS[name]:
            o.visible_camera = True
        set_camera(sx, sy, px / 2)
        save(f'{name}.png', px * 2)
    print('ASSEMBLY RENDER COMPLETE')


if __name__ == '__main__':
    main()
