import bpy,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
campus=json.loads((root/'public/data/campus.json').read_text(encoding='utf8'))
assert all(bpy.data.objects.get(b['id']) for b in campus['buildings'])
scene=bpy.context.scene
assert scene.camera.data.clip_end>=4000
assert scene.frame_end==21601 and scene.render.fps==24
animated=[o.name for o in scene.objects if o.animation_data]
assert len(animated)>=20
print(json.dumps({'buildings':len(campus['buildings']),'objects':len(scene.objects),'animatedObjects':len(animated),'cameraFar':scene.camera.data.clip_end,'frames':scene.frame_end,'fps':scene.render.fps,'renderEngine':scene.render.engine}))
