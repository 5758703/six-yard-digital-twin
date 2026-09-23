"""Inspect south-campus OSM footprints and service roads near the office row."""
import json, math, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
raw = json.loads((ROOT / 'public/data/osm-2026-09-21.json').read_text(encoding='utf8'))
origin = [116.02515, 39.48592]

def project(lon, lat):
    return [
        round((lon - origin[0]) * 111320 * math.cos(math.radians(origin[1])), 2),
        round(-(lat - origin[1]) * 111320, 2),
    ]

rows = []
for e in raw['elements']:
    tags = e.get('tags', {})
    if not e.get('geometry'):
        continue
    pts = [project(g['lon'], g['lat']) for g in e['geometry']]
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    if tags.get('building') and -120 < cx < 220 and 130 < cz < 250:
        rows.append({'kind': 'building', 'id': e['id'], 'name': tags.get('name'), 'type': tags.get('building'),
                     'x': round(cx, 1), 'z': round(cz, 1), 'w': round(max(xs) - min(xs), 1), 'd': round(max(zs) - min(zs), 1),
                     'south': round(max(zs), 1), 'north': round(min(zs), 1)})
    if tags.get('highway') and -200 < cx < 250:
        # keep segments that touch south campus band
        if min(zs) < 280 and max(zs) > 100:
            rows.append({'kind': 'road', 'id': e['id'], 'name': tags.get('name'), 'highway': tags.get('highway'),
                         'xmin': round(min(xs), 1), 'xmax': round(max(xs), 1), 'zmin': round(min(zs), 1), 'zmax': round(max(zs), 1),
                         'n': len(pts)})

(ROOT / 'tmp-south-features.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf8')
print('south features', len(rows))
for r in sorted([x for x in rows if x['kind'] == 'building'], key=lambda a: a['x']):
    print('B', r)
print('--- roads ---')
for r in sorted([x for x in rows if x['kind'] == 'road'], key=lambda a: (a['highway'], a['id'])):
    print('R', r)
