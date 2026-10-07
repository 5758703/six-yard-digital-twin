"""Replace the campus Trees mesh using the shared photo-guided generator."""
import array
import copy
import json
import pathlib
import runpy
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
from plane_trees import build_plane_trees

Geometry = runpy.run_path(str(ROOT / 'scripts/update-residential-glb.py'))['Geometry']
PATH = ROOT / 'public/models/campus.glb'
DATA = json.loads((ROOT / 'public/data/campus.json').read_text(encoding='utf8'))


def linear(value):
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def main():
    raw = PATH.read_bytes()
    if raw[:4] != b'glTF':
        raise ValueError('Expected a binary glTF model')
    json_length = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + json_length])
    bin_start = 20 + json_length
    bin_length = struct.unpack_from('<I', raw, bin_start)[0]
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

    palette = {
        'whitewash': ('Plane tree uneven whitewash', (.81, .79, .70)),
        'whitewash_shadow': ('Plane tree weathered whitewash', (.62, .61, .54)),
        'scar': ('Plane tree cut branch ends', (.32, .28, .23)),
        'shade': ('Plane tree canopy shade', (.105, .19, .065)),
    }
    for index, color in enumerate(((.40, .37, .29), (.52, .49, .40),
                                   (.32, .34, .29), (.62, .58, .47))):
        palette[f'bark{index}'] = (f'Plane tree mottled bark {index}', color)
    for index, color in enumerate(((.18, .30, .09), (.27, .38, .12),
                                   (.34, .43, .17), (.23, .34, .11))):
        palette[f'leaf{index}'] = (f'Plane foliage {index}', color)

    material_ids = {}
    for key, (name, color) in palette.items():
        material = {'name': name, 'doubleSided': True,
                    'pbrMetallicRoughness': {
                        'baseColorFactor': [*(linear(v) for v in color), 1],
                        'metallicFactor': 0, 'roughnessFactor': .89}}
        existing = next((i for i, entry in enumerate(gltf['materials']) if entry.get('name') == name), None)
        if existing is None:
            gltf['materials'].append(material)
            existing = len(gltf['materials']) - 1
        else:
            gltf['materials'][existing] = material
        material_ids[key] = existing
    mats = {'whitewash': material_ids['whitewash'],
            'whitewash_shadow': material_ids['whitewash_shadow'],
            'scar': material_ids['scar'], 'shade': material_ids['shade'],
            'bark': [material_ids[f'bark{i}'] for i in range(4)],
            'foliage': [material_ids[f'leaf{i}'] for i in range(4)]}
    geometry = Geometry()
    build_plane_trees(geometry, DATA['trees'], mats)

    def accessor(values, components, component_type, target):
        fmt = 'f' if component_type == 5126 else 'I'
        view = append_view(array.array(fmt, values).tobytes(), target)
        result = {'bufferView': view, 'componentType': component_type,
                  'count': len(values) // components,
                  'type': {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3'}[components]}
        if components == 3 and target == 34962:
            result['min'] = [min(values[i::3]) for i in range(3)]
            result['max'] = [max(values[i::3]) for i in range(3)]
        gltf['accessors'].append(result)
        return len(gltf['accessors']) - 1

    primitives = []
    for material, part in geometry.parts.items():
        primitives.append({'attributes': {
            'POSITION': accessor(part['position'], 3, 5126, 34962),
            'NORMAL': accessor(part['normal'], 3, 5126, 34962)},
            'indices': accessor(part['indices'], 1, 5125, 34963),
            'material': material})
    gltf['meshes'].append({'name': 'Trees', 'primitives': primitives})
    tree_nodes = [node for node in gltf['nodes'] if node.get('name') == 'Trees']
    if len(tree_nodes) != 1:
        raise ValueError(f'Expected one Trees node, found {len(tree_nodes)}')
    tree_nodes[0]['mesh'] = len(gltf['meshes']) - 1
    tree_nodes[0].setdefault('extras', {})['treeSource'] = 'User-supplied photo of pollarded roadside plane trees'

    # Compact orphaned tree buffers so running the updater again is stable.
    mesh_ids = sorted({node['mesh'] for node in gltf['nodes'] if 'mesh' in node})
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
    view_ids = sorted({accessor['bufferView'] for accessor in gltf['accessors']} |
                      {image['bufferView'] for image in gltf.get('images', []) if 'bufferView' in image})
    packed = bytearray()
    new_views = []
    view_remap = {}
    for old in view_ids:
        view = copy.deepcopy(gltf['bufferViews'][old])
        while len(packed) % 4:
            packed.append(0)
        start = view.get('byteOffset', 0)
        packed.extend(binary[start:start + view['byteLength']])
        view['byteOffset'] = len(packed) - view['byteLength']
        view_remap[old] = len(new_views)
        new_views.append(view)
    gltf['bufferViews'] = new_views
    for accessor in gltf['accessors']:
        accessor['bufferView'] = view_remap[accessor['bufferView']]
    for image in gltf.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] = view_remap[image['bufferView']]
    gltf['buffers'][0]['byteLength'] = len(packed)
    gltf['asset'].setdefault('extras', {})['planeTrees'] = 'photo-guided 2026-09-29'

    encoded = json.dumps(gltf, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    encoded += b' ' * (-len(encoded) % 4)
    packed += b'\0' * (-len(packed) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(packed)
    output = (struct.pack('<4sII', b'glTF', 2, total)
              + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
              + struct.pack('<II', len(packed), 0x004e4942) + packed)
    temporary = PATH.with_suffix('.glb.tmp')
    temporary.write_bytes(output)
    temporary.replace(PATH)
    manifest_path = ROOT / 'public/models/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    manifest['note'] = ('OSM outlines + screenshot massing; office and residential facades '
                        'plus pollarded roadside plane trees guided by user photos; '
                        'unseen dimensions estimated; Cycles stills skipped')
    manifest['planeTrees'] = {
        'count': len(DATA['trees']),
        'source': 'User-supplied photograph of roadside plane trees',
        'method': 'Pollarded forks, uneven whitewash, mottled bark, flattened multi-tone crowns and leaf sprays',
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'Updated {len(DATA["trees"])} plane trees: {len(output):,} bytes')


if __name__ == '__main__':
    main()
