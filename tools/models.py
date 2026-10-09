# Builds assets/obstacles.glb from CC0 model packs with Blender (headless bpy):
#   pip install --target <dir> bpy   then   PYTHONPATH=<dir> python3 tools/models.py <quaternius-dir> <kenney-holiday-dir>
# Sources (CC0): Quaternius "Ultimate Nature Pack" (.blend files) and Kenney "Holiday Kit" (GLB format).
# Every model is joined into one mesh, recoloured to the game's palette, darkened with baked ambient occlusion
# (Cycles, written into the vertex colours), stood on its base, scaled to the game's sizes and exported
# without materials: the game draws them all with one vertex-colour material.
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix

QN, KH = sys.argv[-2], sys.argv[-1]
TMP = os.environ.get('TMPDIR', '/tmp'); os.makedirs(TMP, exist_ok=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'obstacles.glb')

def srgb(h):   # '#rrggbb' -> linear rgb (the game's hex colours go straight into the shader, so keep them as written)
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]

PAL = {
    'Green': ['#2c5a45', '#335f3f', '#284f45'], 'DarkGreen': ['#1f4335', '#24472f', '#1d3c35'], 'Wood': '#5b3f2c', 'LightWood': '#a8774e', 'Snow': '#f3f7fc', 'TreeSnow': '#e6edf6',
    'Rock': '#7d8796',
}
ICE = {'Rock': '#8fd0f5', 'Snow': '#eef7ff'}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def append_blend(name):
    path = os.path.join(QN, name + '.blend')
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects]
    objs = []
    for o in dst.objects:
        if o and o.type == 'MESH':
            bpy.context.scene.collection.objects.link(o); objs.append(o)
    return join(objs)

def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def colour_by_material(o, pal, v=0):
    """per face corner colour from the face's material name"""
    me = o.data
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for poly in me.polygons:
        mname = me.materials[poly.material_index].name.split('.')[0] if me.materials else 'Rock'
        c = pal.get(mname, pal.get('Rock'))
        if isinstance(c, list): c = c[v % len(c)]
        rgb = srgb(c)
        for li in poly.loop_indices: col.data[li].color = (*rgb, 1)
    return col

def kenney(glb, png):
    """Kenney GLB -> Blender mesh with one colour per face from the colour atlas
    (read directly: Blender's importer trips over the kit's texture-transform extension)"""
    import json, struct
    from PIL import Image
    img = Image.open(png).convert('RGB'); w, h = img.size
    b = open(glb, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n]); binc = b[20 + n + 8:]
    def acc(i):
        a = j['accessors'][i]; v = j['bufferViews'][a['bufferView']]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
        k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride', 0) or np.dtype(dt).itemsize * k
        raw = np.frombuffer(binc, np.uint8, count=stride * (a['count'] - 1) + np.dtype(dt).itemsize * k, offset=off)
        return np.lib.stride_tricks.as_strided(raw.view(dt), (a['count'], k), (stride, np.dtype(dt).itemsize)).copy()
    def mat(nd):
        m = Matrix.Identity(4)
        if 'matrix' in nd: m = Matrix([nd['matrix'][i::4] for i in range(4)])
        else:
            t = nd.get('translation', [0, 0, 0]); r = nd.get('rotation', [0, 0, 0, 1]); sc = nd.get('scale', [1, 1, 1])
            from mathutils import Quaternion
            m = Matrix.Translation(t) @ Quaternion((r[3], r[0], r[1], r[2])).to_matrix().to_4x4() @ Matrix.Diagonal((*sc, 1))
        return m
    verts, faces, cols = [], [], []
    def walk(ni, parent):
        nd = j['nodes'][ni]; m = parent @ mat(nd)
        if 'mesh' in nd:
            for pr in j['meshes'][nd['mesh']]['primitives']:
                P = acc(pr['attributes']['POSITION']); UV = acc(pr['attributes']['TEXCOORD_0']); I = acc(pr['indices']).reshape(-1, 3)
                base = len(verts)
                for p in P:
                    q = m @ Vector(p)
                    verts.append((q.x, -q.z, q.y))   # glTF y-up -> Blender z-up
                for tri in I:
                    faces.append(tuple(base + int(t) for t in tri))
                    u, v = UV[tri].mean(axis=0)
                    cols.append([c / 255 for c in img.getpixel((min(w - 1, max(0, int(u * w))), min(h - 1, max(0, int(v * h)))))])
        for c in nd.get('children', []): walk(c, m)
    for ni in j['scenes'][j.get('scene', 0)]['nodes']: walk(ni, Matrix.Identity(4))
    me = bpy.data.meshes.new('k'); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new('k', me); bpy.context.scene.collection.objects.link(o)
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for poly in me.polygons:
        for li in poly.loop_indices: col.data[li].color = (*cols[poly.index], 1)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0001); bpy.ops.object.mode_set(mode='OBJECT')
    return o

def bake_ao(o, strength=0.5, ground=True):
    """ambient occlusion into a second corner attribute, then multiplied into Col"""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64
    plane = None
    if ground:   # snow under the object darkens its base, like a contact shadow
        bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); plane = bpy.context.object
    if not o.data.materials:
        o.data.materials.append(bpy.data.materials.new('m'))
    ao = o.data.color_attributes.new('AO', 'FLOAT_COLOR', 'CORNER')
    o.data.color_attributes.active_color = ao
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    sc.render.bake.target = 'VERTEX_COLORS'
    bpy.ops.object.bake(type='AO')
    col = o.data.color_attributes['Col']
    vals = [d.color[0] for d in ao.data]; print(o.name, 'ao', round(min(vals), 2), round(sum(vals) / len(vals), 2), round(max(vals), 2))
    for i, d in enumerate(col.data):
        a = ao.data[i].color[0]
        k = 1 - strength * (1 - a)
        c = d.color; d.color = (c[0] * k, c[1] * k, c[2] * k, 1)
    o.data.color_attributes.remove(o.data.color_attributes['AO'])
    o.data.color_attributes.active_color = o.data.color_attributes['Col']
    if plane: bpy.data.objects.remove(plane)

def fit(o, height=None, size=None, rot_z=0):
    """base on z=0, centred in x/y, scaled to a height (uniform) or to exact sizes (x, y, z)"""
    if rot_z:
        o.rotation_euler = (0, 0, rot_z); bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.context.view_layer.objects.active = o; bpy.ops.object.transform_apply(rotation=True)
    vs = [v.co for v in o.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    dim = hi - lo
    s = (height / dim.z,) * 3 if height else (size[0] / dim.x, size[1] / dim.y, size[2] / dim.z)
    off = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    o.data.transform(Matrix.Diagonal((*s, 1)) @ Matrix.Translation(-off))
    o.data.update()

def decimate(o, faces):
    """fewer triangles for the phones: collapse edges down to about this many faces"""
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    n = len(o.data.polygons)
    if n > faces:
        m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = faces / n
        bpy.ops.object.modifier_apply(modifier='dec')

def flat(o):
    for p in o.data.polygons: p.use_smooth = False

built = []   # (name, object) collected into one scene at the end
def keep(o, name):
    o.name = name; o.data.name = name
    o.data.materials.clear()
    built.append(o)

def build(name, fn):
    reset(); o = fn(); keep(o, name)
    # move the finished mesh into a holding blend file in memory
    path = os.path.join(TMP, name + '.blend')
    bpy.data.libraries.write(path, {o})
    return path

def pine(src, v, h, widen=1.0, snow=0.18):
    """a pine with our own snow: the snow-covered versions of the pack are nearly white from above"""
    def f():
        o = append_blend(src); fit(o, height=h)
        if widen != 1: o.data.transform(Matrix.Diagonal((widen, widen, 1, 1)))
        colour_by_material(o, PAL, v)
        # snow on the most upward-looking part of the needles (by area), the same amount on every tree
        col = o.data.color_attributes['Col']; sn = srgb(PAL['TreeSnow'])
        green = sorted((p for p in o.data.polygons if 'Green' in o.data.materials[p.material_index].name and p.normal.z > 0.25),
                       key=lambda p: -p.normal.z)
        total = sum(p.area for p in o.data.polygons if 'Green' in o.data.materials[p.material_index].name)
        acc = 0
        for poly in green:
            if acc > snow * total: break
            acc += poly.area
            for li in poly.loop_indices: col.data[li].color = (*sn, 1)
        decimate(o, TREE_FACES); bake_ao(o, 0.6); flat(o); return o
    return f

def rock(src, h, v):
    def f():
        o = append_blend(src); fit(o, height=h)
        colour_by_material(o, PAL, v); bake_ao(o, 0.45); flat(o); return o
    return f

def ice(v):
    def f():
        parts = []
        for i, (src, h, x, y, rz) in enumerate([('Rock_Snow_1', 5.4, 0, 0, v), ('Rock_Snow_1', 3.4, 0.95, 0.3, v + 2), ('Rock_Snow_5', 2.6, -0.9, -0.2, v + 4)]):
            o = append_blend(src); fit(o, height=h)
            o.data.transform(Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rz, 4, 'Z'))
            parts.append(o)
        o = join(parts); colour_by_material(o, ICE); bake_ao(o, 0.35); flat(o); return o
    return f

def log():
    o = append_blend('WoodLog_Snow'); fit(o, size=(2.75, 0.74, 0.76), rot_z=math.pi / 2)
    colour_by_material(o, PAL); bake_ao(o, 0.5); flat(o); return o

def stump():
    o = append_blend('TreeStump_Snow'); fit(o, height=0.75)
    colour_by_material(o, PAL); bake_ao(o, 0.5); flat(o); return o

def snowman():
    o = kenney(os.path.join(KH, 'snowman-hat.glb'), os.path.join(KH, 'Textures', 'colormap.png'))
    fit(o, height=2.8); o.data.transform(Matrix.Diagonal((0.8, 1, 1, 1)))   # arms a little shorter: the hitbox is narrow
    bake_ao(o, 0.3); flat(o); return o

TREE_FACES = int(os.environ.get('TREE_FACES', 600))

JOBS = [
    ('fir_tall_0', pine('PineTree_1', 0, 6.5)), ('fir_tall_1', pine('PineTree_2', 1, 6.5)), ('fir_tall_2', pine('PineTree_3', 2, 6.5)),
    ('fir_round_0', pine('PineTree_1', 1, 4.9, 1.2)), ('fir_round_1', pine('PineTree_2', 2, 4.9, 1.2)), ('fir_round_2', pine('PineTree_5', 0, 4.9, 1.25)),
    ('rock_0', rock('Rock_Snow_6', 1.2, 0)), ('rock_1', rock('Rock_Snow_7', 1.15, 0)), ('rock_2', rock('Rock_Snow_4', 1.25, 0)),
    ('ice_0', ice(0)), ('ice_1', ice(1.3)), ('ice_2', ice(2.6)),
    ('log', log), ('stump', stump), ('snowman', snowman),
]

only = os.environ.get('ONLY')
paths = [build(n, f) for n, f in JOBS if not only or n in only.split(',')]
reset()
for p in paths:
    with bpy.data.libraries.load(p) as (src, dst): dst.objects = list(src.objects)
    for o in dst.objects: bpy.context.scene.collection.objects.link(o)
for i, o in enumerate(bpy.context.scene.objects): o.location.x = i * 8   # spread out (the game reads the node's mesh only)
for o in bpy.context.scene.objects:
    print(f'{o.name:12s} {len(o.data.polygons):5d} faces  size', ' × '.join(f'{d:.2f}' for d in o.dimensions))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(OUT), export_format='GLB', export_materials='NONE',
                          export_vertex_color='ACTIVE', export_normals=False, export_texcoords=False, export_yup=True)
print('wrote', os.path.abspath(OUT), os.path.getsize(OUT), 'bytes')
