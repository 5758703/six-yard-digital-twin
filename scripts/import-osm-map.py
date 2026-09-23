"""Convert Downloads/map (OSM XML) to Overpass-style JSON and summarize keyed features."""
import json, math, pathlib, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = pathlib.Path(r'c:\Users\Administrator\Downloads\map')
OUT = ROOT / 'public/data/osm-2026-09-21.json'
root = ET.parse(SRC).read() if False else ET.parse(SRC).getroot()
nodes = {n.get('id'): {'lat': float(n.get('lat')), 'lon': float(n.get('lon'))} for n in root.findall('node')}
meta = root.find('meta')
bounds = root.find('bounds')
elements = []
interesting = []
origin = [116.02515, 39.48592]

def project(lon, lat):
    return [
        round((lon - origin[0]) * 111320 * math.cos(math.radians(origin[1])), 2),
        round(-(lat - origin[1]) * 111320, 2),
    ]

for w in root.findall('way'):
    tags = {t.get('k'): t.get('v') for t in w.findall('tag')}
    nd_refs = [nd.get('ref') for nd in w.findall('nd')]
    geom = []
    for ref in nd_refs:
        if ref not in nodes:
            continue
        p = nodes[ref]
        geom.append({'lat': p['lat'], 'lon': p['lon']})
    if not geom:
        continue
    lats = [g['lat'] for g in geom]
    lons = [g['lon'] for g in geom]
    el = {
        'type': 'way',
        'id': int(w.get('id')),
        'bounds': {
            'minlat': min(lats), 'minlon': min(lons),
            'maxlat': max(lats), 'maxlon': max(lons),
        },
        'nodes': [int(r) for r in nd_refs if r.isdigit()],
        'geometry': geom,
        'tags': tags,
    }
    elements.append(el)
    if tags.get('building') or tags.get('highway') or tags.get('name'):
        lon = (min(lons) + max(lons)) / 2
        lat = (min(lats) + max(lats)) / 2
        x, z = project(lon, lat)
        interesting.append({
            'id': el['id'],
            'building': tags.get('building'),
            'highway': tags.get('highway'),
            'name': tags.get('name'),
            'x': x, 'z': z,
            'w': round((max(lons) - min(lons)) * 85900, 2),
            'd': round((max(lats) - min(lats)) * 111320, 2),
        })

for r in root.findall('relation'):
    tags = {t.get('k'): t.get('v') for t in r.findall('tag')}
    members = [{'type': m.get('type'), 'ref': int(m.get('ref')), 'role': m.get('role')} for m in r.findall('member')]
    elements.append({'type': 'relation', 'id': int(r.get('id')), 'members': members, 'tags': tags})

payload = {
    'version': 0.6,
    'generator': root.get('generator') or 'OSM XML import',
    'osm3s': {
        'timestamp_osm_base': meta.get('osm_base') if meta is not None else '2026-09-21',
        'copyright': 'The data included in this document is from www.openstreetmap.org. The data is made available under ODbL.',
        'bounds': {k: float(bounds.get(k)) for k in ['minlat', 'minlon', 'maxlat', 'maxlon']} if bounds is not None else {},
    },
    'elements': elements,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
# also keep a raw XML copy
(ROOT / 'public/data/osm-2026-09-21.osm.xml').write_bytes(SRC.read_bytes())
summary = {
    'elements': len(elements),
    'buildings': sum(1 for e in elements if e.get('tags', {}).get('building')),
    'highways': sum(1 for e in elements if e.get('tags', {}).get('highway')),
    'named_buildings': [i for i in interesting if i.get('name') and i.get('building')],
    'office_like': [i for i in interesting if i.get('building') in ('office', 'industrial', 'warehouse', 'yes') and (i.get('name') or i['z'] > 140)],
    'named_highways': [i for i in interesting if i.get('name') and i.get('highway')],
}
(ROOT / 'tmp-map-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
print('Wrote', OUT)
print('buildings', summary['buildings'], 'highways', summary['highways'])
print('named buildings:')
for b in summary['named_buildings']:
    print(' ', b)
print('named highways:')
for h in summary['named_highways']:
    print(' ', h['id'], h['highway'], h['name'], 'z', h['z'])
