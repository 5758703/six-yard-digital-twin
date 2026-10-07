"""Update factory east doors and the two precincts in campus.glb without Blender."""
import array
import copy
import json
import pathlib
import runpy
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
from campus_compounds import (build_factory, build_factory_courtyard, build_independent_boundary, build_service_lane,
                              build_factory_wire_fence, build_yard_connector, build_north_walkway,
                              cover_old_yard_overlap)

Geometry = runpy.run_path(str(ROOT / 'scripts/update-residential-glb.py'))['Geometry']
PATH = ROOT / 'public/models/campus.glb'
DATA = json.loads((ROOT / 'public/data/campus.json').read_text(encoding='utf8'))


def linear(value):
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def main():
    raw = PATH.read_bytes()
    if raw[:4] != b'glTF':
        raise ValueError('Expected a binary glTF campus model')
    json_length = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + json_length])
    bin_start = 20 + json_length
    bin_length = struct.unpack_from('<I', raw, bin_start)[0]
    binary = bytearray(raw[bin_start + 8:bin_start + 8 + bin_length])

    def append_view(values, fmt, target):
        payload = array.array(fmt, values).tobytes()
        while len(binary) % 4:
            binary.append(0)
        gltf['bufferViews'].append(dict(buffer=0, byteOffset=len(binary),
                                        byteLength=len(payload), target=target))
        binary.extend(payload)
        return len(gltf['bufferViews']) - 1

    def accessor(values, components, component_type, target):
        view = append_view(values, 'f' if component_type == 5126 else 'I', target)
        result = dict(bufferView=view, componentType=component_type,
                      count=len(values) // components,
                      type={1: 'SCALAR', 3: 'VEC3'}[components])
        if components == 3:
            result['min'] = [min(values[i::3]) for i in range(3)]
            result['max'] = [max(values[i::3]) for i in range(3)]
        gltf['accessors'].append(result)
        return len(gltf['accessors']) - 1

    material = {entry['name']: index for index, entry in enumerate(gltf['materials'])}
    def colored(name, rgb, roughness=.75, metallic=0):
        if name in material:
            entry = gltf['materials'][material[name]]
            entry['pbrMetallicRoughness']['baseColorFactor'] = [*(linear(c) for c in rgb), 1]
            entry['pbrMetallicRoughness']['roughnessFactor'] = roughness
            entry['pbrMetallicRoughness']['metallicFactor'] = metallic
            return material[name]
        gltf['materials'].append(dict(name=name, doubleSided=True,
                                      pbrMetallicRoughness=dict(baseColorFactor=[*(linear(c) for c in rgb), 1],
                                                                metallicFactor=metallic,
                                                                roughnessFactor=roughness)))
        material[name] = len(gltf['materials']) - 1
        return material[name]
    mats = dict(concrete=material['Concrete paving'], brick=material['Weathered brick'],
                frame=material['Window frames'], glass=material['Blue grey glazing'],
                ivory=material['Office limestone'], plaster=material['Warm limestone plaster'],
                blue=material['Standing seam blue metal'], steel=material['Street furniture'],
                asphalt=material['Asphalt'], line=material['Road marking'],
                grass=material['Grass'])
    mats.update(factory_wall=colored('Factory aged white panels', (.73,.74,.70)),
                factory_joint=colored('Factory panel seams', (.40,.43,.42)),
                factory_stain=colored('Factory weather stains', (.57,.56,.51)),
                factory_trim=colored('Factory burgundy eave and frames', (.30,.13,.15)),
                factory_roof=colored('Factory blue barrel roof', (.025,.12,.31), .57, .12),
                factory_roof_rib=colored('Factory blue corrugation ribs', (.045,.20,.40), .5, .16),
                factory_door=colored('Factory worn beige doors', (.65,.62,.53)),
                factory_sign=colored('Factory blue safety boards', (.16,.42,.59)),
                court_line=colored('Courtyard faded yellow markings', (.67,.59,.28)),
                cabin_white=colored('Portable cabin pale walls', (.82,.84,.81)),
                cabin_roof=colored('Portable cabin grey roof', (.50,.55,.54)),
                canopy_green=colored('Portable cabin green awning', (.12,.34,.28)),
                crate_blue=colored('Stacked blue plastic crates', (.035,.20,.47)),
                crate_rim=colored('Blue crate top rims', (.08,.29,.57)),
                crate_shadow=colored('Blue crate vent shadows', (.02,.08,.22)),
                wire=colored('Factory chain-link wire', (.33,.37,.36), .56, .55))

    def replace_mesh(name, geometry, extras):
        primitives = []
        for material_id, part in geometry.parts.items():
            primitives.append(dict(attributes=dict(
                POSITION=accessor(part['position'], 3, 5126, 34962),
                NORMAL=accessor(part['normal'], 3, 5126, 34962)),
                indices=accessor(part['indices'], 1, 5125, 34963),
                material=material_id))
        gltf['meshes'].append(dict(name=name, primitives=primitives))
        matches = [node for node in gltf['nodes'] if node.get('name') == name]
        if len(matches) > 1:
            raise ValueError(f'Multiple {name} nodes')
        if matches:
            node = matches[0]
        else:
            node = dict(name=name)
            gltf['nodes'].append(node)
            gltf['scenes'][gltf.get('scene', 0)]['nodes'].append(len(gltf['nodes']) - 1)
        node['mesh'] = len(gltf['meshes']) - 1
        node.setdefault('extras', {}).update(extras)

    factory = next(b for b in DATA['buildings'] if b['id'] == 'factory-1')
    factory_mesh = Geometry()
    build_factory(factory_mesh, factory, mats)
    replace_mesh('factory-1', factory_mesh,
                 dict(buildingId='factory-1', areaId='shared-yard', eastDoors=factory['eastDoors'],
                      photoGuided='blue barrel roof, white panel facade, east doors'))

    courtyard_mesh = Geometry()
    build_factory_courtyard(courtyard_mesh, DATA['factoryCourtyard'], mats)
    replace_mesh('Factory_courtyard', courtyard_mesh,
                 dict(areaId='shared-yard', source=DATA['factoryCourtyard']['source'],
                      badmintonCourts=len(DATA['factoryCourtyard']['badmintonCourtCenters']),
                      portableCabins=len(DATA['factoryCourtyard']['cabinCenters'])))

    office_area = next(a for a in DATA['areas'] if a['id'] == 'international-office')
    boundary_mesh = Geometry()
    build_independent_boundary(boundary_mesh, office_area['boundary'], mats)
    replace_mesh('International_boundary', boundary_mesh,
                 dict(areaId='international-office', source='User-confirmed separate office precinct; fence alignment estimated'))

    shared_area = next(a for a in DATA['areas'] if a['id'] == 'shared-yard')
    for node in gltf['nodes']:
        if node.get('name') == 'Factory_yard_south_gate':
            node['name'] = 'Factory_wire_fence'
    factory_fence_mesh = Geometry()
    build_factory_wire_fence(factory_fence_mesh, shared_area['factoryFence'],
                             shared_area['factoryYardGate'], mats)
    replace_mesh('Factory_wire_fence', factory_fence_mesh,
                 dict(areaId='shared-yard', connectsTo='equipment',
                      source=shared_area['factoryFence']['source'],
                      pedestrianGate=shared_area['factoryFence']['pedestrianGate'],
                      fenceSegments=len(shared_area['factoryFence']['segments'])))

    road = next(r for r in DATA['roads'] if r['id'] == 'shared-yard-service')
    lane_mesh = Geometry()
    build_service_lane(lane_mesh, road, mats)
    replace_mesh('Shared_yard_service_lane', lane_mesh,
                 dict(areaId='shared-yard', roadId=road['id']))

    connector = next(r for r in DATA['roads'] if r['id'] == 'factory-yard-connector')
    connector_mesh = Geometry()
    build_yard_connector(connector_mesh, connector, mats)
    replace_mesh('Factory_yard_connector', connector_mesh,
                 dict(areaId='shared-yard', roadId=connector['id']))

    north_link = next(r for r in DATA['roads'] if r['id'] == 'international-north-link')
    north_walkway = Geometry()
    build_north_walkway(north_walkway, north_link, mats)
    replace_mesh('International_north_walkway', north_walkway,
                 dict(areaId='international-office', connectsTo='residential', roadId=north_link['id']))

    yard_cover = Geometry()
    cover_old_yard_overlap(yard_cover, mats)
    replace_mesh('Yard_ground_correction', yard_cover, dict(areaId='international-office'))

    # Compact orphaned meshes and buffers so rerunning this patch is stable.
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
    views = []
    view_remap = {}
    for old in view_ids:
        view = copy.deepcopy(gltf['bufferViews'][old])
        while len(packed) % 4:
            packed.append(0)
        start = view.get('byteOffset', 0)
        packed.extend(binary[start:start + view['byteLength']])
        view['byteOffset'] = len(packed) - view['byteLength']
        view_remap[old] = len(views)
        views.append(view)
    gltf['bufferViews'] = views
    for accessor in gltf['accessors']:
        accessor['bufferView'] = view_remap[accessor['bufferView']]
    for image in gltf.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] = view_remap[image['bufferView']]
    gltf['buffers'][0]['byteLength'] = len(packed)
    gltf['asset'].setdefault('extras', {})['compoundLayout'] = 'photo-guided factory courtyard; no through road to residential buildings'

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
    manifest['compoundLayout'] = dict(factoryEastDoors=2,
                                      factorySouthDoors=0,
                                      factoryYardSouthwestGate='connects to equipment building',
                                      factoryWireFenceSegments=len(shared_area['factoryFence']['segments']),
                                      factoryPedestrianGate=shared_area['factoryFence']['pedestrianGate'],
                                      factoryResidentialGap='no through road or simulated people and vehicles',
                                      sharedArea='厂房、装备专业化大楼及住宅区',
                                      separateArea='国际部独立办公区',
                                      internationalNorthGate='connects to residential area',
                                      boundary='示意位置，非测绘边界')
    manifest['factoryPhotoModel'] = dict(roof='蓝色弧形压型钢板',
                                         courtyard='混凝土地坪与羽毛球场线',
                                         portableCabins=len(DATA['factoryCourtyard']['cabinCenters']),
                                         blueCrateGroups=len(DATA['factoryCourtyard']['crateStacks']),
                                         source=DATA['factoryCourtyard']['source'])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'Updated photo-guided factory and courtyard: {len(output):,} bytes')


if __name__ == '__main__':
    main()
