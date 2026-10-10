# Prepares a tree made with meshy.ai (free plan, CC BY 4.0: credit Meshy) for the game, with headless Blender:
#   PYTHONPATH=<bpy dir> python3 tools/meshy_tree.py <meshy download.glb> <out.glb> <faces>
# Options (environment): CUT_BASE=1 removes a round snow base and loose stones, LUM=0.45 brightness above which the
# model's own texture counts as snow, CLEAN=1 snow by face direction when there is no texture, VOX=0.008 voxel remesh
# first (even surface, no long spiky triangles). Result: 6.5 m high, game colours, baked AO, flat faces, no texture.
# Used: meshy-tree-1 (CLEAN=1 VOX=0.008, 2600), meshy-tree-2 and -3 (CUT_BASE=1 LUM=0.45, 3000) -> tools/src/.
import bpy, sys, os, math
src, out, faces = sys.argv[-3], sys.argv[-2], int(sys.argv[-1])
CUT_BASE = os.environ.get('CUT_BASE') == '1'; LUM = float(os.environ.get('LUM', 0.35)); CLEAN = os.environ.get('CLEAN') == '1'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
import bmesh, numpy as np
from mathutils import Vector
# texture (if any) for snow/needle decisions, read before the mesh changes
img = None
for mt in o.data.materials:
    for nd in (mt.node_tree.nodes if mt and mt.node_tree else []):
        if nd.type == 'TEX_IMAGE' and nd.image: img = nd.image
PX = None
if img:
    w, h = img.size; PX = np.array(img.pixels[:]).reshape(h, w, 4)
# cut away a ground disc (some generations stand on a round snow base)
vs = [v.co for v in o.data.vertices]; z0 = min(v.z for v in vs); H0 = max(v.z for v in vs) - z0
bm = bmesh.new(); bm.from_mesh(o.data)
trunk_r = 0.09 * H0
cut = [f for f in bm.faces if f.calc_center_median().z < z0 + 0.1 * H0 and Vector((f.calc_center_median().x, f.calc_center_median().y)).length > trunk_r]
if CUT_BASE:
    bmesh.ops.delete(bm, geom=cut, context='FACES')
    # drop small loose bits left on the ground (stones, snow lumps): islands low down with few faces
    bm.faces.ensure_lookup_table(); seen = set(); drop = []
    for f0 in bm.faces:
        if f0.index in seen: continue
        isl, stack = [], [f0]; seen.add(f0.index)
        while stack:
            f = stack.pop(); isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        top = max(f.calc_center_median().z for f in isl)
        if top < z0 + 0.2 * H0: drop += isl
    bmesh.ops.delete(bm, geom=drop, context='FACES')
bm.to_mesh(o.data); bm.free(); o.data.update()
VOX = float(os.environ.get('VOX', 0))
if VOX:   # even, closed surface before reducing: no long spiky triangles afterwards
    r = o.modifiers.new('r', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOX * H0; bpy.ops.object.modifier_apply(modifier='r')
n = len(o.data.polygons)
m = o.modifiers.new('d', 'DECIMATE'); m.ratio = faces / n; bpy.ops.object.modifier_apply(modifier='d')
me = o.data; vs = [v.co for v in me.vertices]
zmin = min(v.z for v in vs); zmax = max(v.z for v in vs); H = zmax - zmin
s = 6.5 / H
me.transform(__import__('mathutils').Matrix.Diagonal((s, s, s, 1)) @ __import__('mathutils').Matrix.Translation((0, 0, -zmin)))
me.update()
def hx(h): return [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
G1, G2, SN, WD = hx('#2c5a45'), hx('#1f4335'), hx('#e6edf6'), hx('#5b3f2c')
col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
import random; random.seed(3)
for p in me.polygons:
    c = p.center; r = math.hypot(c.x, c.y)
    if c.z < 1.3 and r < 0.35: rgb = WD
    elif PX is not None and me.uv_layers:
        uv = me.uv_layers.active.data
        u = sum(uv[l].uv.x for l in p.loop_indices) / p.loop_total; v = sum(uv[l].uv.y for l in p.loop_indices) / p.loop_total
        t = PX[min(PX.shape[0] - 1, max(0, int(v * PX.shape[0]))), min(PX.shape[1] - 1, max(0, int(u * PX.shape[1])))]
        lum = 0.3 * t[0] + 0.6 * t[1] + 0.1 * t[2]
        rgb = SN if lum > LUM else (G1 if random.random() < 0.6 else G2)
    elif CLEAN:   # snow only on what faces up, needles two-tone by height bands (no random speckles)
        rgb = SN if p.normal.z > 0.62 else (G1 if (math.sin(c.z * 9.0) > -0.2) else G2)
    elif p.normal.z > 0.55 and random.random() < 0.75: rgb = SN
    else: rgb = G1 if random.random() < 0.6 else G2
    for li in p.loop_indices: col.data[li].color = (*rgb, 1)
me.color_attributes.active_color = col
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48
bpy.ops.mesh.primitive_plane_add(size=40); pl = bpy.context.object
o.data.materials.clear(); o.data.materials.append(bpy.data.materials.new('m'))
ao = me.color_attributes.new('AO', 'FLOAT_COLOR', 'CORNER'); me.color_attributes.active_color = ao
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
sc.render.bake.target = 'VERTEX_COLORS'; bpy.ops.object.bake(type='AO')
for i, d in enumerate(col.data):
    k = 1 - 0.55 * (1 - ao.data[i].color[0]); c = d.color; d.color = (c[0]*k, c[1]*k, c[2]*k, 1)
me.color_attributes.remove(me.color_attributes['AO']); me.color_attributes.active_color = me.color_attributes['Col']
bpy.data.objects.remove(pl); o.data.materials.clear(); o.name = 'meshy_tree'
for p in me.polygons: p.use_smooth = False
print('faces', len(me.polygons), 'dims', [round(x, 2) for x in o.dimensions])
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_materials='NONE', export_vertex_color='ACTIVE', export_normals=False, export_texcoords=False)
