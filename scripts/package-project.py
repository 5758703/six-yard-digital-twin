"""Validate generated artifacts and package reproducible source (no runtimes/caches)."""
import pathlib,json,hashlib,zipfile,struct
root=pathlib.Path(__file__).resolve().parents[1]
required=['blender/campus.blend','renders/campus-daylight.png','renders/international-photo-guided.png','renders/equipment-photo-guided.png','public/models/campus.glb','public/models/international.glb','public/models/equipment.glb','public/models/vehicle.glb','public/models/pedestrian.glb','dist/index.html']
for item in required:
    path=root/item
    assert path.is_file() and path.stat().st_size>0,f'Missing artifact: {item}'
    if path.suffix=='.glb':
        data=path.read_bytes();assert data[:4]==b'glTF';assert struct.unpack_from('<I',data,8)[0]==len(data)
        length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);assert doc.get('meshes'),f'No meshes: {item}'
        if path.stem in ['campus','international','equipment']:
            for bid,count in [('international',20),('equipment',6)]:
                if path.stem in ['campus',bid]:
                    node=next(n for n in doc['nodes'] if n.get('extras',{}).get('buildingId')==bid)
                    assert node['extras'].get('floors')==count and node['extras'].get('floorsConfirmed'),f'Incorrect confirmed floors: {bid}'
        if path.name=='campus.glb':
            ids={n.get('extras',{}).get('buildingId') for n in doc.get('nodes',[])}
            campus=json.loads((root/'public/data/campus.json').read_text(encoding='utf8'))
            assert all(b['id'] in ids for b in campus['buildings']),'GLB/data building mismatch'
        assert (root/'dist/models'/path.name).read_bytes()==data,'Production model differs from source'
    if path.suffix=='.png':assert path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
    if path.suffix=='.blend':assert path.read_bytes()[:7]==b'BLENDER'
provenance=json.loads((root/'public/data/osm-provenance.json').read_text(encoding='utf8'))
assert hashlib.sha256((root/'public/data/osm-2026-09-20.json').read_bytes()).hexdigest()==provenance['sha256']
out=root/'artifacts';out.mkdir(exist_ok=True)
report={p:{'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in required}
(out/'deliverables.json').write_text(json.dumps(report,indent=2),encoding='utf8')
folders=['src','public','blender','renders','docs','tests','scripts','references']
files=['README.md','package.json','package-lock.json','tsconfig.json','vite.config.ts','index.html','.gitignore']
for folder in folders:
    files.extend(str(p.relative_to(root)) for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.blend1','.pyc','.log'])
with zipfile.ZipFile(out/'six-yard-digital-twin.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for file in files:archive.write(root/file,arcname='six-yard-digital-twin/'+file.replace('\\','/'))
with zipfile.ZipFile(out/'six-yard-digital-twin.zip') as archive:assert archive.testzip() is None
print('Validated artifacts and packaged',len(files),'files;', (out/'six-yard-digital-twin.zip').stat().st_size,'bytes')
