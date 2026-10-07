"""Regenerate residential meshes in the shipped GLB without requiring Blender.

Blender's full scene generator uses the same build_residential function. This
patcher is useful when the original Blender executable is unavailable.
"""
import array
import copy
import json
import math
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
from residential_facades import build_residential, make_textures

PATH = ROOT / 'public/models/campus.glb'
DATA = json.loads((ROOT / 'public/data/campus.json').read_text(encoding='utf8'))


class Geometry:
    def __init__(self):
        self.parts = {}

    def shape(self, vertices, faces, material):
        part = self.parts.setdefault(material, {'position': [], 'normal': [], 'uv': [], 'indices': []})
        for face in faces:
            p = [vertices[i] for i in face]
            a, b, c = p[:3]
            ab = [b[i] - a[i] for i in range(3)]
            ac = [c[i] - a[i] for i in range(3)]
            normal = [ab[1] * ac[2] - ab[2] * ac[1],
                      ab[2] * ac[0] - ab[0] * ac[2],
                      ab[0] * ac[1] - ab[1] * ac[0]]
            size = math.sqrt(sum(v * v for v in normal)) or 1
            normal = [v / size for v in normal]
            start = len(part['position']) // 3
            for x, y, z in p:
                part['position'].extend((x, y, z))
                part['normal'].extend(normal)
                part['uv'].extend((x / 4 if abs(normal[2]) > abs(normal[0]) else z / 4,
                                   y / 3 if abs(normal[1]) < .8 else z / 3))
            for i in range(1, len(face) - 1):
                part['indices'].extend((start, start + i, start + i + 1))

    def box(self, x, z, y, w, d, h, material):
        verts = [(x + a * w / 2, y + b * h / 2, z + c * d / 2)
                 for a, b, c in [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1),
                                 (-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)]]
        self.shape(verts, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                           (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material)

    def polygon(self, points, h, material):
        n = len(points)
        verts = [(x, y, z) for y in (.15, h) for x, z in points]
        self.shape(verts, [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
                   + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)], material)


def linear(value):
    value /= 255
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def main():
    raw = PATH.read_bytes()
    if raw[:4] != b'glTF':
        raise ValueError('Expected a binary glTF campus model')
    json_length, json_kind = struct.unpack_from('<II', raw, 12)
    if json_kind != 0x4e4f534a:
        raise ValueError('Missing glTF JSON chunk')
    gltf = json.loads(raw[20:20 + json_length])
    bin_start = 20 + json_length
    bin_length, bin_kind = struct.unpack_from('<II', raw, bin_start)
    if bin_kind != 0x004e4942:
        raise ValueError('Missing glTF binary chunk')
    binary = bytearray(raw[bin_start + 8:bin_start + 8 + bin_length])

    def append_view(payload, target=None):
        while len(binary) % 4:
            binary.append(0)
        view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(payload)}
        if target:
            view['target'] = target
        gltf['bufferViews'].append(view)
        binary.extend(payload)
        return len(gltf['bufferViews']) - 1

    texture_paths = make_textures(ROOT / 'public/models')
    image_indices = {}
    for kind, path in texture_paths.items():
        name = f'residential-{kind}'
        view = append_view(path.read_bytes())
        image = {'name': name, 'mimeType': 'image/png', 'bufferView': view}
        existing = next((i for i, entry in enumerate(gltf.get('images', [])) if entry.get('name') == name), None)
        if existing is None:
            gltf.setdefault('images', []).append(image)
            existing = len(gltf['images']) - 1
        else:
            gltf['images'][existing] = image
        image_indices[kind] = existing
    sampler_spec = {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}
    sampler = next((i for i, entry in enumerate(gltf.get('samplers', [])) if entry == sampler_spec), None)
    if sampler is None:
        gltf.setdefault('samplers', []).append(sampler_spec)
        sampler = len(gltf['samplers']) - 1
    texture_indices = {}
    for kind, image in image_indices.items():
        texture = {'source': image, 'sampler': sampler}
        existing = next((i for i, entry in enumerate(gltf.get('textures', [])) if entry == texture), None)
        if existing is None:
            gltf.setdefault('textures', []).append(texture)
            existing = len(gltf['textures']) - 1
        texture_indices[kind] = existing

    colors = {
        'coping': (79, 69, 64), 'joint': (133, 125, 110),
        'frame': (186, 184, 171), 'glass': (26, 43, 46),
        'curtain': (94, 99, 87), 'mullion': (128, 133, 122),
        'sill': (161, 156, 140), 'bay_edge': (217, 212, 196),
        'grille': (51, 61, 59), 'ac': (176, 176, 163),
        'ac_vent': (71, 79, 77), 'door': (69, 89, 97),
        'entry_shadow': (84, 77, 69), 'canopy': (145, 99, 87),
        'sign': (31, 79, 128), 'pipe': (173, 171, 153),
    }
    names = {'wall': 'Residential weathered ivory plaster',
             'wall-aged': 'Residential aged cream plaster',
             'plinth': 'Residential ochre plinth', 'roof': 'Residential dark clay roof'}
    mats = {}
    for kind in ('wall', 'wall-aged', 'plinth', 'roof', *colors):
        color = colors.get(kind, (255, 255, 255))
        pbr = {'baseColorFactor': [*(linear(c) for c in color), 1],
               'metallicFactor': .05, 'roughnessFactor': .82}
        if kind in texture_indices:
            pbr['baseColorTexture'] = {'index': texture_indices[kind]}
        material = {'name': names.get(kind, 'Residential ' + kind.replace('_', ' ')),
                    'pbrMetallicRoughness': pbr, 'doubleSided': True}
        existing = next((i for i, entry in enumerate(gltf['materials']) if entry.get('name') == material['name']), None)
        if existing is None:
            gltf['materials'].append(material)
            existing = len(gltf['materials']) - 1
        else:
            gltf['materials'][existing] = material
        mats[kind] = existing

    def accessor(values, components, component_type, target):
        fmt = 'f' if component_type == 5126 else 'I'
        payload = array.array(fmt, values).tobytes()
        view = append_view(payload, target)
        result = {'bufferView': view, 'componentType': component_type,
                  'count': len(values) // components,
                  'type': {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3'}[components]}
        if target == 34962 and components == 3 and values is not None:
            result['min'] = [min(values[i::3]) for i in range(3)]
            result['max'] = [max(values[i::3]) for i in range(3)]
        gltf['accessors'].append(result)
        return len(gltf['accessors']) - 1

    residential = {b['id']: b for b in DATA['buildings'] if b['type'] == 'residential'}
    updated = set()
    for node in gltf['nodes']:
        building = residential.get(node.get('name'))
        if not building:
            continue
        mesh = Geometry()
        palette = mats.copy()
        if int(building['id'].split('-')[-1]) % 3 == 0:
            palette['wall'] = mats['wall-aged']
        build_residential(mesh, building, palette)
        primitives = []
        for material, part in mesh.parts.items():
            primitives.append({'attributes': {
                'POSITION': accessor(part['position'], 3, 5126, 34962),
                'NORMAL': accessor(part['normal'], 3, 5126, 34962),
                'TEXCOORD_0': accessor(part['uv'], 2, 5126, 34962)},
                'indices': accessor(part['indices'], 1, 5125, 34963),
                'material': material})
        gltf['meshes'].append({'name': building['id'], 'primitives': primitives})
        node['mesh'] = len(gltf['meshes']) - 1
        node.setdefault('extras', {})['facadeSource'] = 'Four user supplied residential photographs; unobserved dimensions estimated'
        updated.add(building['id'])
    if updated != set(residential):
        raise ValueError(f'Missing residential nodes: {set(residential) - updated}')

    # Drop unused geometry from the original residential meshes and prior runs.
    mesh_ids = sorted({n['mesh'] for n in gltf['nodes'] if 'mesh' in n})
    mesh_remap = {old: new for new, old in enumerate(mesh_ids)}
    gltf['meshes'] = [gltf['meshes'][i] for i in mesh_ids]
    for node in gltf['nodes']:
        if 'mesh' in node:
            node['mesh'] = mesh_remap[node['mesh']]
    accessor_ids = sorted({index for mesh in gltf['meshes'] for primitive in mesh['primitives']
                           for index in [primitive['indices'], *primitive['attributes'].values()]})
    accessor_remap = {old: new for new, old in enumerate(accessor_ids)}
    gltf['accessors'] = [gltf['accessors'][i] for i in accessor_ids]
    for mesh in gltf['meshes']:
        for primitive in mesh['primitives']:
            primitive['indices'] = accessor_remap[primitive['indices']]
            primitive['attributes'] = {key: accessor_remap[value]
                                       for key, value in primitive['attributes'].items()}
    view_ids = sorted({a['bufferView'] for a in gltf['accessors']} |
                      {im['bufferView'] for im in gltf.get('images', []) if 'bufferView' in im})
    new_binary = bytearray()
    view_remap = {}
    new_views = []
    for old in view_ids:
        view = copy.deepcopy(gltf['bufferViews'][old])
        while len(new_binary) % 4:
            new_binary.append(0)
        start = view.get('byteOffset', 0)
        payload = binary[start:start + view['byteLength']]
        view['byteOffset'] = len(new_binary)
        new_binary.extend(payload)
        view_remap[old] = len(new_views)
        new_views.append(view)
    gltf['bufferViews'] = new_views
    for a in gltf['accessors']:
        a['bufferView'] = view_remap[a['bufferView']]
    for im in gltf.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = view_remap[im['bufferView']]
    gltf['buffers'][0]['byteLength'] = len(new_binary)
    gltf.setdefault('asset', {}).setdefault('extras', {})['residentialFacades'] = 'photo-guided 2026-09-29'

    encoded = json.dumps(gltf, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    encoded += b' ' * (-len(encoded) % 4)
    new_binary += b'\0' * (-len(new_binary) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(new_binary)
    output = (struct.pack('<4sII', b'glTF', 2, total)
              + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
              + struct.pack('<II', len(new_binary), 0x004e4942) + new_binary)
    temporary = PATH.with_suffix('.glb.tmp')
    temporary.write_bytes(output)
    temporary.replace(PATH)
    print(f'Updated {len(updated)} residential buildings in {PATH.name}: {len(output):,} bytes')


if __name__ == '__main__':
    main()
