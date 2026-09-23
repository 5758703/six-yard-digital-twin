import bpy,pathlib,json
r=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(r/'blender/campus.blend'))
for bid in ['international','equipment']:
    bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects[bid];o.select_set(True)
    assert o.get('buildingId')==bid and o.get('facadeSource')
    bpy.ops.export_scene.gltf(filepath=str(r/'public/models'/(bid+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_extras=True)
p=r/'public/models/manifest.json';data=json.loads(p.read_text());data['note']='Two office facades updated from user photographs; unseen elevations and dimensions estimated';data['facadeReferences']=['references/international-facade.jpg','references/equipment-facade.jpg'];p.write_text(json.dumps(data,indent=2))
print('PHOTO OFFICE EXPORTS VERIFIED')
