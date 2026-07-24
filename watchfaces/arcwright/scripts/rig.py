"""ARCWRIGHT shared Blender rig — ONE light world for every rendered asset.

Import from every render script so all layers composite under identical
lighting: HDRI environment (real reflections in the metal) + a single cool
key light, ortho top-down camera, transparent film.

Run inside Blender's python (bpy).
"""
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HDRI = os.path.join(ROOT, 'assets-source', 'hdri', 'studio_small_08_1k.hdr')

# ---------- palette (material story: oil-blued steel / worn brass / gunmetal) ----------
PALETTE = {
    'blued_steel':  {'base': (0.020, 0.028, 0.055), 'rough': 0.35},
    'worn_brass':   {'base': (0.190, 0.115, 0.038), 'rough': 0.32},
    'gunmetal':     {'base': (0.045, 0.048, 0.055), 'rough': 0.40},
    'dark_fill':    {'base': (0.004, 0.005, 0.007), 'rough': 0.85},
    'polished':     {'base': (0.560, 0.570, 0.600), 'rough': 0.28},
}


def enable_gpu(sc):
    """OptiX on the RTX 5060 Ti; fall back to CPU if unavailable.
    Set ARCWRIGHT_CPU=1 to force CPU (e.g. when ollama/ComfyUI hold VRAM)."""
    if os.environ.get('ARCWRIGHT_CPU'):
        sc.cycles.device = 'CPU'
        print('CYCLES DEVICE: CPU (forced)')
        return False
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == 'OPTIX']
        if gpus:
            for d in prefs.devices:
                d.use = d.type == 'OPTIX'
            sc.cycles.device = 'GPU'
            print('CYCLES DEVICE: OptiX GPU (' + gpus[0].name + ')')
            return True
    except Exception as e:  # noqa: BLE001
        print('GPU setup failed, CPU fallback:', e)
    sc.cycles.device = 'CPU'
    return False


def reset_scene(samples=192):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    enable_gpu(sc)
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    # AgX: photographic highlight response (Filmic reads flat/CG)
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = 0.5

    # world: studio HDRI for reflections, kept dim so the key light dominates
    world = bpy.data.worlds.new('world')
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(HDRI)
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.06
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

    # dominant cool key (small = crisp speculars), cool fill, rim — the
    # Chronova-proven trio, plus the dim HDRI above for polished glints.
    def light(name, loc, energy, size, color):
        li = bpy.data.lights.new(name, type='AREA')
        li.energy = energy
        li.size = size
        li.color = color
        lo = bpy.data.objects.new(name, li)
        bpy.context.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return lo

    light('key', (-4, 4, 8), 700, 2.0, (0.90, 0.95, 1.05))
    light('fill', (5, -2, 6), 180, 8, (0.75, 0.85, 1.0))
    light('rim', (0, -6, 3), 350, 3, (0.9, 0.95, 1.0))

    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    co = bpy.data.objects.new('cam', cam)
    bpy.context.collection.objects.link(co)
    co.location = (0, 0, 10)
    sc.camera = co
    return sc


def metal(name, key, aniso=0.0):
    """Principled metal from the PALETTE."""
    p = PALETTE[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*p['base'], 1)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = p['rough']
    if aniso:
        bsdf.inputs['Anisotropic'].default_value = aniso
    return m


def render(path, world_radius, px, scene=None):
    sc = scene or bpy.context.scene
    sc.camera.data.ortho_scale = world_radius * 2
    sc.render.resolution_x = px
    sc.render.resolution_y = px
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
