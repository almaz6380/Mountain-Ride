# Prepares a generated model (TRELLIS on Hugging Face, MIT; or any textured GLB) for the game, with headless Blender:
#   PYTHONPATH=<bpy dir> python3 tools/prepare_model.py <in.glb> <out.glb> <faces> <height> [x,y,z size] [--long-x]
#     [--gain=<brighter>] [--snow=<normal z: snow above>] [--bark=<normal z: bark below>] [--vox=<remesh detail>]
# The texture is baked into one colour per face (the game draws everything with one vertex-colour material), ambient
# occlusion is baked on top, the model stands on z=0 centred, is reduced to about <faces> faces and scaled to <height>
# metres (or to exact x,y,z metres). --long-x turns the longest side along x (logs lie across the lane).
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix

args = sys.argv[1:]
LONG_X = '--long-x' in args
opt = lambda name, d: next((float(a.split('=')[1]) for a in args if a.startswith('--' + name + '=')), d)
GAIN, SNOW, VOX = opt('gain', 1.0), opt('snow', 0), opt('vox', 140)   # brighter colours, snow on faces looking up (normal z > SNOW), remesh detail
BARK = opt('bark', None)   # faces looking sideways/down (normal z < BARK) get bark colour (snow-covered logs come out all white)
args = [a for a in args if not a.startswith('--')]
src, out, faces, height = args[0], args[1], int(args[2]), float(args[3])
size = [float(v) for v in args[4].split(',')] if len(args) > 4 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data

# the texture of the (first) material
img = None
for m in me.materials:
    for n in (m.node_tree.nodes if m and m.node_tree else []):
        if n.type == 'TEX_IMAGE' and n.image and img is None: img = n.image
PX = None
if img:
    w, h = img.size; PX = np.array(img.pixels[:]).reshape(h, w, 4)

# colour per face of the full-detail model, from the texture under the face's UV centre (faces are tiny, so this
# is exact; corners would hit the dark gaps between UV islands)
col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
uv = me.uv_layers.active.data if me.uv_layers else None
for p in me.polygons:
    rgb = (0.8, 0.8, 0.8)
    if PX is not None and uv is not None:
        u = sum(uv[l].uv.x for l in p.loop_indices) / p.loop_total; v = sum(uv[l].uv.y for l in p.loop_indices) / p.loop_total
        t = PX[min(PX.shape[0] - 1, max(0, int(v * PX.shape[0]))), min(PX.shape[1] - 1, max(0, int(u * PX.shape[1])))]
        rgb = tuple(float(c) ** (1 / 2.2) for c in t[:3])   # Blender hands out linear values; the game's colours are sRGB
    for li in p.loop_indices: col.data[li].color = (*rgb, 1)

# a clean low-poly copy: voxel remesh (closed, even surface – generated meshes fall apart when reduced directly),
# reduce, then take the colours over from the detailed model
src_o = o
bpy.ops.object.select_all(action='DESELECT'); src_o.select_set(True); bpy.context.view_layer.objects.active = src_o
bpy.ops.object.duplicate(); o = bpy.context.view_layer.objects.active
vs = [v.co for v in src_o.data.vertices]; H0 = max(max(v.x for v in vs) - min(v.x for v in vs), max(v.y for v in vs) - min(v.y for v in vs), max(v.z for v in vs) - min(v.z for v in vs))
if VOX:   # --vox=0: no remesh (hard-surface models like vehicles keep their edges better)
    r = o.modifiers.new('r', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = H0 / VOX; bpy.ops.object.modifier_apply(modifier='r')
n = len(o.data.polygons)
if n > faces:
    d = o.modifiers.new('d', 'DECIMATE'); d.ratio = faces / n; bpy.ops.object.modifier_apply(modifier='d')
o.data.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
t = o.modifiers.new('t', 'DATA_TRANSFER'); t.object = src_o
t.use_loop_data = True; t.data_types_loops = {'COLOR_CORNER'}; t.loop_mapping = 'POLYINTERP_NEAREST'
t.layers_vcol_loop_select_src = 'ALL'; t.layers_vcol_loop_select_dst = 'NAME'
bpy.ops.object.modifier_apply(modifier='t')
bpy.data.objects.remove(src_o)
me = o.data; col = me.color_attributes['Col']; me.color_attributes.active_color = col
# generated textures come out dark and without snow: brighten, then snow on what faces up
SNOWC = (0.93, 0.95, 0.98)
BARKC = (0.36, 0.25, 0.17)
for p in me.polygons:
    sn = SNOW and p.normal.z > SNOW
    bk = BARK is not None and p.normal.z < BARK
    for li in p.loop_indices:
        c = col.data[li].color
        if bk:   # keep the texture's light and dark as a little variation in the bark
            l = 0.75 + 0.5 * (0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2]); col.data[li].color = (*(min(1, b * l) for b in BARKC), 1)
        else: col.data[li].color = (*SNOWC, 1) if sn else (min(1, c[0] * GAIN), min(1, c[1] * GAIN), min(1, c[2] * GAIN), 1)

# orientation, base on z=0, size
if LONG_X:
    vs = [v.co for v in me.vertices]
    if (max(v.y for v in vs) - min(v.y for v in vs)) > (max(v.x for v in vs) - min(v.x for v in vs)):
        me.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
vs = [v.co for v in me.vertices]
lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
dim = hi - lo
s = (size[0] / dim.x, size[1] / dim.y, size[2] / dim.z) if size else (height / dim.z,) * 3
me.transform(Matrix.Diagonal((*s, 1)) @ Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
me.update()

# ambient occlusion (with a ground plane: darker where the model meets the snow)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48
bpy.ops.mesh.primitive_plane_add(size=40); plane = bpy.context.object
me.materials.clear(); me.materials.append(bpy.data.materials.new('m'))
ao = me.color_attributes.new('AO', 'FLOAT_COLOR', 'CORNER'); me.color_attributes.active_color = ao
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
sc.render.bake.target = 'VERTEX_COLORS'; bpy.ops.object.bake(type='AO')
for i, d in enumerate(col.data):
    k = 1 - 0.4 * (1 - ao.data[i].color[0]); c = d.color; d.color = (c[0] * k, c[1] * k, c[2] * k, 1)
me.color_attributes.remove(me.color_attributes['AO']); me.color_attributes.active_color = me.color_attributes['Col']
bpy.data.objects.remove(plane)
me.materials.clear()
for p in me.polygons: p.use_smooth = False
o.name = 'model'
print('faces', len(me.polygons), 'size', [round(x, 2) for x in o.dimensions])
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_materials='NONE', export_vertex_color='ACTIVE',
                          export_normals=False, export_texcoords=False)
