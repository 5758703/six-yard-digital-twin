import json, math, pathlib
R = pathlib.Path(__file__).resolve().parents[1]
raw = json.loads((R / 'public/data/osm-2026-09-21.json').read_text(encoding='utf8'))
origin = [116.02515, 39.48592]

def project(lon, lat):
    return [
        round((lon - origin[0]) * 111320 * math.cos(math.radians(origin[1])), 2),
        round(-(lat - origin[1]) * 111320, 2),
    ]

def way_by_id(i):
    return next(e for e in raw['elements'] if e.get('id') == i and e.get('type') == 'way')

def footprint(e):
    poly = [project(g['lon'], g['lat']) for g in e['geometry'][:-1]]
    xs = [p[0] for p in poly]; zs = [p[1] for p in poly]
    x = round((min(xs) + max(xs)) / 2, 2)
    z = round((min(zs) + max(zs)) / 2, 2)
    w = round(max(xs) - min(xs), 2)
    d = round(max(zs) - min(zs), 2)
    return x, z, w, d, poly

def union_footprint(ids):
    polys = []
    for i in ids:
        polys.extend(footprint(way_by_id(i))[4])
    xs = [p[0] for p in polys]; zs = [p[1] for p in polys]
    x = round((min(xs) + max(xs)) / 2, 2)
    z = round((min(zs) + max(zs)) / 2, 2)
    w = round(max(xs) - min(xs), 2)
    d = round(max(zs) - min(zs), 2)
    # rectangular stand-in matching union bbox (photo facade builder expects box massing)
    poly = [[x - w / 2, z - d / 2], [x + w / 2, z - d / 2], [x + w / 2, z + d / 2], [x - w / 2, z + d / 2]]
    return x, z, w, d, poly

buildings = []
# OSM residential / service within campus, excluding annotated office/factory complex pieces.
SKIP = {1560982331, 1560982332, 390196010, 390196198, 390195851}
for e in raw['elements']:
    if not e.get('tags', {}).get('building'):
        continue
    b = e['bounds']
    lon = (b['minlon'] + b['maxlon']) / 2
    lat = (b['minlat'] + b['maxlat']) / 2
    if not (116.02165 < lon < 116.02885 and 39.4837 < lat < 39.48813):
        continue
    if e['id'] in SKIP:
        continue
    p = [project(g['lon'], g['lat']) for g in e['geometry']][:-1]
    x, z = project(lon, lat)
    apartment = e['tags']['building'] == 'apartments'
    residential = apartment or e['tags']['building'] in ('detached', 'house', 'bungalow', 'residential')
    buildings.append(dict(
        id=f"osm-{e['id']}",
        name=(f"住宅楼 {sum(x['type']=='residential' for x in buildings)+1:02d}" if residential
              else f"配套建筑 {sum(x['type']=='service' for x in buildings)+1:02d}"),
        type='residential' if residential else 'service',
        x=x, z=z,
        w=round((b['maxlon'] - b['minlon']) * 85900, 2),
        d=round((b['maxlat'] - b['minlat']) * 111320, 2),
        height=18 if apartment else (12 if residential else 9),
        floors=6 if apartment else (4 if residential else 3),
        polygon=p,
        source='OpenStreetMap 2026-09-21 建筑轮廓；高度与立面为近似',
        osmId=e['id'],
    ))

# Real OSM footprints for the annotated south complex (Baidu names kept for UX).
ix, iz, iw, idp, ipoly = footprint(way_by_id(1560982331))
fx, fz, fw, fd, fpoly = footprint(way_by_id(390196198))
ex, ez, ew, ed, epoly = union_footprint([1560982332, 390196010])
# north-office still from older OSM office way if present, else keep prior estimate
try:
    nx, nz, nw, ndp, npoly = footprint(way_by_id(390195851))
    # OSM fragment is too small for the visible north office massing; keep measured center but enlarge.
    if nw < 60 or ndp < 40:
        nx, nz, nw, ndp = 85, -177, 85, 65
        npoly = [[nx - nw / 2, nz - ndp / 2], [nx + nw / 2, nz - ndp / 2], [nx + nw / 2, nz + ndp / 2], [nx - nw / 2, nz + ndp / 2]]
except StopIteration:
    nx, nz, nw, ndp, npoly = 85, -177, 85, 65, [[42.5, -209.5], [127.5, -209.5], [127.5, -144.5], [42.5, -144.5]]

for spec in [
    ('international', '国际部大楼', ix, iz, iw, idp, 72, 20, ipoly, [1560982331], 'OSM way 1560982331（国际部大楼）轮廓；层数用户确认，高度与立面近似'),
    ('equipment', '装备专业化大楼', ex, ez, ew, ed, 25, 6, epoly, [1560982332, 390196010], 'OSM ways 1560982332+390196010（办公厂房等）合并轮廓；层数用户确认，百度地图称装备专业化大楼'),
    ('factory-1', '厂房', fx, fz, fw, fd, 9, 2, fpoly, [390196198], 'OSM way 390196198 轮廓；蓝色弧形压型钢板屋顶与东侧浅色墙面依据用户提供的北向南实拍照片；两个东门依据用户确认'),
    ('north-office', '北侧办公楼', nx, nz, nw, ndp, 21, 5, npoly, [390195851], 'OSM/截图推定；高度与立面近似'),
]:
    bid, name, x, z, w, d, h, floors, poly, osm_ids, source = spec
    buildings.append(dict(
        id=bid, name=name, type='factory' if bid.startswith('factory') else 'office',
        x=x, z=z, w=w, d=d, height=h, floors=floors, polygon=poly,
        source=source, osmIds=osm_ids,
    ))

for building in buildings:
    building['areaId'] = 'international-office' if building['id'] == 'international' else 'shared-yard'
    if building['id'] == 'factory-1':
        building['eastDoors'] = [169, 196]

roads = []
# Skip dual/clipped 范阳中路 centerlines; replace with one continuous carriageway.
SKIP_ROADS = {156261177, 471022676, 1218545434, 1155784875, 1155784876}
for e in raw['elements']:
    if 'highway' not in e.get('tags', {}):
        continue
    if e['id'] in SKIP_ROADS:
        continue
    pts = [project(p['lon'], p['lat']) for p in e['geometry']]
    hw = e['tags']['highway']
    width = 22 if hw in ('primary', 'secondary') else (12 if hw == 'tertiary' else (8 if hw == 'residential' else 6))
    roads.append(dict(
        id=f"osm-{e['id']}",
        name=e['tags'].get('name') or ('园路' if hw in ('residential', 'service') else '道路'),
        points=pts, width=width, source='OSM 2026-09-21',
    ))

# Continuous 范阳中路 across campus (OSM dual ways leave a gap / clip).
# Mean OSM latitude of 范阳中路 ≈ 39.48377 → z ≈ 239 in our frame.
FANYANG_Z = 240
roads.append(dict(id='fanyang-middle', name='范阳中路', points=[[-330, FANYANG_Z], [340, FANYANG_Z]], width=28,
                  source='用户/OSM修正：合并范阳中路双幅并贯通路面'))

intl_south = iz + idp / 2
equip_south = ez + ed / 2
factory_south = fz + fd / 2
row_south = max(intl_south, equip_south, factory_south)
north_road_z = min(iz - idp / 2, ez - ed / 2, fz - fd / 2) - 6
# 国际部楼中轴直连范阳中路（仅楼南至干道，不穿楼体、无丁字展宽）。
GATE_X = round(ix, 1)
roads.append(dict(id='南门引路', name='南门引路', points=[[GATE_X, round(intl_south, 1)], [GATE_X, FANYANG_Z]], width=10,
                  source='用户要求：国际部大楼中间直连范阳中路'))
# The clipped spur would run through the independent office enclosure.
roads = [road for road in roads if road['id'] != 'osm-1560982336']
# Factory east doors open onto the lane shared with the equipment building.
# Its northern end stops short of the residential footprint.
roads.append(dict(id='shared-yard-service', name='共用院区通道',
                  points=[[56.5, round(north_road_z, 1)], [56.5, 220]], width=7,
                  source='用户确认：厂房、装备楼与住宅区同属一个院区；通道为近似布局'))
roads.append(dict(id='factory-yard-connector', name='厂房院子西南联络通道',
                  points=[[34, 225], [34, 219], [56.5, 219], [65, 219], [65, 202]], width=5,
                  source='用户确认：厂房院子西南出入口与装备专业化大楼相连；通道为示意布局'))
roads.append(dict(id='international-north-link', name='国际部北侧出入口',
                  points=[[-82, 147], [-82, 100]], width=4,
                  source='用户确认：国际部北侧出入口连接住宅小区；步行通道为示意布局'))

# 按用户要求：去掉南侧绿化带与楼前分块绿地。
greens = []

parking = []
for row in range(4):
    for col in range(14):
        parking.append(dict(id=f'P{len(parking)+1:03d}', x=-250 + col * 3.3, z=150 + row * 14, angle=0))
# north of office row along clear corridor
park_z = min(iz - idp / 2, ez - ed / 2) - 12
for base in (-70, 140):
    for col in range(18):
        parking.append(dict(id=f'P{len(parking)+1:03d}', x=base + col * 3.3, z=park_z, angle=0))

trees = []

def blocked(x, z):
    # 楼中轴南门引路走廊
    if abs(x - GATE_X) < 6 and intl_south - 2 <= z <= FANYANG_Z + 2:
        return True
    if abs(z - north_road_z) < 5 and -100 <= x <= 180:
        return True
    return False

def clear(x, z):
    if blocked(x, z):
        return False
    return all(abs(x - b['x']) > b['w'] / 2 + 4 or abs(z - b['z']) > b['d'] / 2 + 4 for b in buildings) and \
           all(abs(x - p['x']) > 4 or abs(z - p['z']) > 5 for p in parking)

for rx in [-299, -282, -95, -70, 151, 183, 295, 311]:
    for z in range(-230, 256, 15):
        if clear(rx, z):
            trees.append([rx, z])
for z in [-232, -211, 0, 24, int(north_road_z)]:
    for x in range(-280, 296, 17):
        if clear(x, z):
            trees.append([x, z])

# Fill the two existing plane-tree rows along the straight north-south
# residential avenue. Some original grid positions fall inside building
# setbacks, so move only those missing trees toward the road-side pavement.
main_road = next(road for road in roads if road['id'] == 'osm-1560982335')

def main_road_x(z):
    for (ax, az), (bx, bz) in zip(main_road['points'], main_road['points'][1:]):
        if min(az, bz) <= z <= max(az, bz) and abs(az - bz) > 1:
            return ax + (bx - ax) * (z - az) / (bz - az)
    raise ValueError(f'North-south avenue has no centerline at z={z}')

for row_x, side in [(151, -1), (183, 1)]:
    for z in range(-230, 116, 15):
        if [row_x, z] in trees:
            continue
        center_x = main_road_x(z)
        candidates = sorted(range(row_x - 14, row_x + 15), key=lambda x: abs(x - row_x))
        for x in candidates:
            roadside_offset = side * (x - center_x)
            if not 5.5 <= roadside_offset <= 13:
                continue
            if clear(x, z) and all(math.hypot(x - tx, z - tz) >= 9 for tx, tz in trees):
                trees.append([x, z])
                break

areas = [
    dict(id='shared-yard', name='六号院共用院区',
         buildingIds=[b['id'] for b in buildings if b['areaId'] == 'shared-yard'],
         factoryYardGate=dict(side='southwest', x=34, z=225, width=10, connectsTo='equipment'),
         source='用户确认：厂房、装备专业化大楼和住宅区属于同一院区'),
    dict(id='international-office', name='国际部独立办公区', buildingIds=['international'],
         boundary=dict(west=-102, east=21.5, north=147, south=225,
                       gates=[dict(side='north', x=-82, width=11, connectsTo='residential'),
                              dict(side='south', x=GATE_X, width=12, connectsTo='fanyang-middle')]),
         source='用户确认：国际部大楼为单独隔离的办公大楼；围界位置与门宽为示意'),
]

# Photo taken from a residential building north of the factory, looking south.
# Object positions and dimensions are visual estimates within the OSM building gap.
factory_courtyard = dict(
    west=round(fx + fw / 2 + .08, 2), east=round(ex - ew / 2 - .12, 2),
    north=round(fz - fd / 2 + .25, 2), south=220,
    badmintonCourtX=51.6, badmintonCourtCenters=[170, 186, 202],
    cabinX=61.4, cabinCenters=[159.5, 168.5, 177.5, 186.5, 195.5],
    greenCanopyCount=2,
    crateStacks=[dict(x=47.6, z=179, columns=2, rows=2, height=3),
                 dict(x=47.8, z=207, columns=2, rows=3, height=4),
                 dict(x=53.5, z=158, columns=1, rows=4, height=3)],
    source='用户提供的厂房实拍照片（从北面住宅楼往南拍摄）；数量、尺寸及位置按照片与 OSM 建筑间距近似重建',
)

data = dict(
    name='平安小区 · 六号院',
    origin=origin,
    extent=[-330, -285, 340, 285],
    buildings=buildings,
    roads=roads,
    parking=parking,
    trees=trees,
    greens=greens,
    areas=areas,
    factoryCourtyard=factory_courtyard,
    annotation='建筑与园路底图为 OSM 2026-09-21；厂房弧形蓝色屋顶、浅色墙板、营房车和混凝土院子依据用户实拍照片；厂房仅有两个东门，院子西南出入口连通装备楼；厂房、装备楼及住宅区同属共用院区；国际部大楼独立围合，北侧出入口连接住宅区。',
    modelLimitations='地理底图来源为 OSM 2026-09-21；层数、外立面、绿化树种属于近似重建，不是测绘成果。',
)
(R / 'public/data/campus.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')
# write helper constants for simulation alignment
meta = dict(
    intl={'x': ix, 'z': iz, 'w': iw, 'd': idp, 'south': intl_south, 'north': iz - idp / 2},
    factory={'x': fx, 'z': fz, 'w': fw, 'd': fd, 'south': factory_south, 'north': fz - fd / 2},
    equipment={'x': ex, 'z': ez, 'w': ew, 'd': ed, 'south': equip_south, 'north': ez - ed / 2},
    northRoadZ=north_road_z,
    rowSouth=row_south,
    gateX=GATE_X,
    fanyangZ=FANYANG_Z,
)
(R / 'public/data/campus-layout-meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf8')
print('Prepared', len(buildings), 'buildings,', len(trees), 'trees,', len(parking), 'spaces,', len(roads), 'roads')
print('layout', meta)

# Preserve user-confirmed floor counts after regeneration.
exec((pathlib.Path(__file__).resolve().parent / 'confirm-floors.py').read_text(encoding='utf8'))
