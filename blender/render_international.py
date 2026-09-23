import bpy,pathlib,json
from mathutils import Vector
r=pathlib.Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(r/'blender/campus.blend'))
b=next(b for b in json.loads((r/'public/data/campus.json').read_text(encoding='utf8'))['buildings'] if b['id']=='international')
s=bpy.context.scene;cam=s.camera
cam.location=(b['x']+b['w']*.62,-(b['z']+b['d']/2+100),b['height']*.90)
target=Vector((b['x'],-b['z'],b['height']*.46));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(b['w']*1.4,b['height']*2.6)
s.render.resolution_x=1600;s.render.resolution_y=1000;s.render.filepath=str(r/'renders/international-photo-guided.png')
bpy.ops.render.render(write_still=True)
