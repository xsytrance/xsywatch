"""ARCWRIGHT engraved digit glyphs — displacement-engraved plate TILES.

v2 approach: each glyph is a small blued-steel plate tile with the digit
pressed into it via negative displacement (mask from gen_glyph_masks.py).
A dented, lit plate needs no mesh surgery: normals, chamfer shading and
cavity shadowing all come from the physics. Tiles composite seamlessly
because their margins are flat plate rendered under the shared rig.

Cut anatomy (matches real engraving):
  chamfer band (disp minus fill masks) -> bright freshly-cut steel
  floor (fill mask)                    -> oil-dark fill
  untouched margins                    -> blued plate

Run AFTER gen_glyph_masks.py:
    ~/Android/blender/blender-4.5.11-linux-x64/blender -b -noaudio \
        --python scripts/render_glyphs.py
Then scripts/post_glyphs.py.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import PALETTE, reset_scene  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASKS = os.path.join(ROOT, 'assets-source', 'glyphs', 'masks')
RAW = os.path.join(ROOT, 'assets-source', 'glyphs', 'raw4x')
os.makedirs(RAW, exist_ok=True)

GLYPHS = list('0123456789') + [':']
SETS = [('lg', 52, 68), ('sm', 32, 44)]
SS = 4
DEPTH = 0.045        # engraving depth in tile-width units
GRID = 220           # plane subdivisions across the tile width


def engraved_tile(tag, name):
    """Dense plane + negative displacement from the glyph mask."""
    disp_img = bpy.data.images.load(os.path.join(MASKS, f'disp_{tag}_{name}.png'))
    fill_img = bpy.data.images.load(os.path.join(MASKS, f'fill_{tag}_{name}.png'))

    w, h = 1.0, disp_img.size[1] / disp_img.size[0]
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=GRID, y_subdivisions=int(GRID * h), size=1)
    obj = bpy.context.active_object
    obj.scale = (w, h, 1)

    tex = bpy.data.textures.new('disp', type='IMAGE')
    tex.image = disp_img
    tex.extension = 'EXTEND'
    mod = obj.modifiers.new('engrave', type='DISPLACE')
    mod.texture = tex
    mod.texture_coords = 'UV'
    mod.strength = -DEPTH
    mod.mid_level = 0.0

    # material: blued plate -> bright-cut chamfer -> dark fill floor
    m = bpy.data.materials.new('plate')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Anisotropic'].default_value = 0.4

    tc = nt.nodes.new('ShaderNodeTexCoord')
    t_disp = nt.nodes.new('ShaderNodeTexImage')
    t_disp.image = disp_img
    t_fill = nt.nodes.new('ShaderNodeTexImage')
    t_fill.image = fill_img
    for t in (t_disp, t_fill):
        t.extension = 'EXTEND'
        nt.links.new(tc.outputs['UV'], t.inputs['Vector'])

    def rgb(node_id, vals):
        n = nt.nodes.new('ShaderNodeRGB')
        n.outputs[0].default_value = (*vals, 1)
        n.label = node_id
        return n

    blued = rgb('blued', PALETTE['blued_steel']['base'])
    cut = rgb('cut', PALETTE['polished']['base'])
    dark = rgb('dark', PALETTE['dark_fill']['base'])

    # gate the bright-cut tone to genuine slope: no halo on the flat plate
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[1].position = 0.60
    nt.links.new(t_disp.outputs['Color'], ramp.inputs['Fac'])

    mix1 = nt.nodes.new('ShaderNodeMixRGB')   # plate -> cut where displaced
    nt.links.new(ramp.outputs['Color'], mix1.inputs['Fac'])
    nt.links.new(blued.outputs[0], mix1.inputs['Color1'])
    nt.links.new(cut.outputs[0], mix1.inputs['Color2'])
    mix2 = nt.nodes.new('ShaderNodeMixRGB')   # -> dark fill on the floor
    nt.links.new(t_fill.outputs['Color'], mix2.inputs['Fac'])
    nt.links.new(mix1.outputs['Color'], mix2.inputs['Color1'])
    nt.links.new(dark.outputs[0], mix2.inputs['Color2'])
    nt.links.new(mix2.outputs['Color'], bsdf.inputs['Base Color'])

    rough = nt.nodes.new('ShaderNodeMixRGB')  # fill is matte, metal is not
    nt.links.new(t_fill.outputs['Color'], rough.inputs['Fac'])
    rough.inputs['Color1'].default_value = (PALETTE['blued_steel']['rough'],) * 3 + (1,)
    rough.inputs['Color2'].default_value = (PALETTE['dark_fill']['rough'],) * 3 + (1,)
    nt.links.new(rough.outputs['Color'], bsdf.inputs['Roughness'])

    obj.data.materials.append(m)
    return obj, w, h


def main():
    for tag, wpx, hpx in SETS:
        for ch in GLYPHS:
            name = 'colon' if ch == ':' else ch
            sc = reset_scene(samples=192)
            _, w, h = engraved_tile(tag, name)
            sc.camera.data.ortho_scale = max(w, h)
            sc.render.resolution_x = wpx * SS
            sc.render.resolution_y = hpx * SS
            sc.render.filepath = os.path.join(RAW, f'glyph_{tag}_{name}.png')
            bpy.ops.render.render(write_still=True)
            print(f'RENDERED glyph_{tag}_{name}')
    print('ALL GLYPHS RENDERED')


if __name__ == '__main__':
    main()
