"""Run: blender --background --python blender/build_campus.py
Shared meter coordinates: X east, Z south, Y up; converted to Blender Z-up.
OSM footprints are preserved. Facades, heights, offices and landscaping are approximations.
"""
import bpy, math, json, pathlib, random, bmesh, sys, os
from mathutils import Vector, Matrix
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from photo_facades import build_photo_office
OUT=ROOT/'public/models'; OUT.mkdir(parents=True,exist_ok=True)
RENDERS=ROOT/'renders'; RENDERS.mkdir(exist_ok=True)
C=json.loads((ROOT/'public/data/campus.json').read_text(encoding='utf8'))
random.seed(26)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
MAT=[]
def material(name,color,rough=.7,metal=0):
    color=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in color)
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    MAT.append(m);return len(MAT)-1
plaster=material('Warm limestone plaster',(.69,.64,.52)); ivory=material('Office limestone',(.77,.78,.74));brick=material('Weathered brick',(.49,.39,.29))
glass=material('Blue grey glazing',(.12,.23,.28),.2,.5);frame=material('Window frames',(.58,.61,.59),.38,.25)
roof=material('Terracotta roof tiles',(.30,.23,.18));blue=material('Standing seam blue metal',(.12,.28,.35),.4,.25);concrete=material('Concrete paving',(.46,.48,.44))
asphalt=material('Asphalt',(.13,.16,.17));line=material('Road marking',(.84,.83,.70));grass=material('Grass',(.20,.28,.13));soil=material('Bare ground',(.44,.37,.23))
bark=material('Plane tree bark',(.38,.34,.23));leaves=[material('Plane foliage '+str(i),c) for i,c in enumerate([(.18,.30,.09),(.27,.38,.12),(.34,.43,.17),(.23,.34,.11)])]
steel=material('Street furniture',(.20,.24,.25),.45,.55);white=material('White paint',(.8,.83,.81),.3,.35);tire=material('Rubber',(.022,.028,.031));red=material('Car red',(.40,.09,.06),.3,.4)
lamp=material('Warm lamp diffuser',(.94,.80,.43),.25);p=MAT[lamp].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.68,.27,1);p.inputs['Emission Strength'].default_value=.5
class Mesh:
    def __init__(self):self.v=[];self.f=[];self.m=[]
    def shape(self,v,f,m):
        n=len(self.v);self.v += [(x,-z,y) for x,y,z in v];self.f += [tuple(n+i for i in face) for face in f];self.m += [m]*len(f)
    def box(self,x,z,y,w,d,h,m):
        self.shape([(x+a*w/2,y+b*h/2,z+c*d/2) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
    def sphere(self,x,z,y,rx,rz,ry,m):
        n=10;r=6;v=[];f=[]
        for j in range(r+1):
            a=math.pi*j/r
            for i in range(n):
                b=2*math.pi*i/n;v.append((x+rx*math.sin(a)*math.cos(b),y+ry*math.cos(a),z+rz*math.sin(a)*math.sin(b)))
        for j in range(r):
            for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
        self.shape(v,f,m)
    def pole(self,x,z,y,r,h,m):
        v=[];n=8
        for yy in [y-h/2,y+h/2]:
            for i in range(n):v.append((x+r*math.cos(i*math.tau/n),yy,z+r*math.sin(i*math.tau/n)))
        self.shape(v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
    def polygon(self,pts,h,m):
        n=len(pts);self.shape([(x,y,z) for y in [.15,h] for x,z in pts],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
    def finish(self,name):
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(self.v,[],self.f);mesh.update()
        for m in MAT:mesh.materials.append(m)
        for p,i in zip(mesh.polygons,self.m):
            p.material_index=i
            if i in leaves:p.use_smooth=True
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
        ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);return ob
def gable(mesh,x,z,w,d,h):
    mesh.shape([(x-w/2-.5,h,z-d/2-.5),(x+w/2+.5,h,z-d/2-.5),(x+w/2+.5,h,z+d/2+.5),(x-w/2-.5,h,z+d/2+.5),(x-w/2-.5,h+2.5,z),(x+w/2+.5,h+2.5,z)],[(0,1,5,4),(4,5,2,3),(0,4,3),(1,2,5)],roof)
    for i in range(int(w/1.5)):
        xx=x-w/2+i*1.5
        mesh.shape([(xx-.035,h+.04,z-d/2-.5),(xx+.035,h+.04,z-d/2-.5),(xx+.035,h+2.54,z),(xx-.035,h+2.54,z),(xx-.035,h+.04,z+d/2+.5),(xx+.035,h+.04,z+d/2+.5)],[(0,1,2,3),(3,2,5,4)],roof)
    for i in range(1,int(d/1.2)):
        zz=z-d/2+i*1.2;yy=h+2.5*(1-abs(zz-z)/(d/2+.5))+.04;mesh.box(x,zz,yy,w,.055,.045,roof)
def facade(mesh,x,z,w,d,h,floors,office=False):
    step=3.8 if office else 4.5
    for floor in range(floors):
        yy=2+floor*(h-1)/floors
        for i in range(max(1,int(w/step)-1)):
            xx=x-w/2+(i+1)*step
            for sign in [-1,1]:
                zz=z+sign*(d/2+.06);ww=2.55 if office else 1.55;hh=2.05 if office else 1.65
                mesh.box(xx,zz,yy,ww+.25,.19,hh+.24,frame);mesh.box(xx,zz+sign*.11,yy,ww,.08,hh,glass)
                mesh.box(xx,zz+sign*.16,yy,.075,.1,hh,ivory)
                if not office and floor>0 and i%3==0:
                    mesh.box(xx,zz+sign*.65,yy-.92,2.2,1.3,.16,concrete);mesh.box(xx,zz+sign*1.22,yy-.46,2.2,.13,.8,plaster)
        if office:mesh.box(x,z,h/floors*(floor+1),w+.35,d+.35,.24,ivory)
    for sign in [-1,1]:
        for floor in range(floors):
            for zz in [z-d*.22,z+d*.22]:mesh.box(x+sign*(w/2+.06),zz,2+floor*(h-1)/floors,.12,1.8,1.8,glass)
def building(b):
    if b['id'] in ['international','equipment']:return build_photo_office(b,globals())
    m=Mesh();x,z,w,d,h=b['x'],b['z'],b['w'],b['d'],b['height'];office=b['type']=='office';factory=b['type']=='factory'
    m.box(x,z,.22,w+4,d+4,.44,concrete)
    if office:
        # Courtyard wings match the visible massing only; no claim of measured facade accuracy.
        blocks=[(x,z-d*.24,w,d*.52,h),(x-w*.40,z+d*.18,w*.20,d*.64,h*.82),(x+w*.40,z+d*.18,w*.20,d*.64,h*.82)]
        for xx,zz,ww,dd,hh in blocks:
            m.box(xx,zz,hh/2,ww,dd,hh,ivory);facade(m,xx,zz,ww,dd,hh,b['floors'],True)
            m.box(xx,zz,hh+.16,ww+.6,dd+.6,.32,concrete)
            for dx in [-ww/2,ww/2]:m.box(xx+dx,zz,hh+.65,.3,dd,1.0,ivory)
            for dz in [-dd/2,dd/2]:m.box(xx,zz+dz,hh+.65,ww,.3,1.0,ivory)
            for dx in [-ww*.22,ww*.22]:m.box(xx+dx,zz,hh+1.25,4,3,2.0,steel)
        m.box(x,z+d*.05,4,16,3,8,glass);m.box(x,z+d*.23,6.5,24,12,.5,steel)
        for dx in [-10,10]:m.pole(x+dx,z+d*.3,3.2,.28,6.4,ivory)
        for s in range(4):m.box(x,z+d*.4+s*.8,.2+s*.13,25,1,.3,concrete)
    elif factory:
        # Long industrial shed: brick mass, blue standing-seam roof, loading apron.
        m.box(x,z,h/2,w,d,h,brick);facade(m,x,z,w,d,h,b['floors'])
        m.box(x,z,h+.35,w+1.2,d+1.2,.7,blue)
        for dx in [-w*.28,0,w*.28]:m.box(x+dx,z+d/2+.08,2.4,5.5,.16,4.2,steel)
        m.box(x,z+d/2+6,.18,w*.9,10,.2,concrete)
    else:
        m.polygon(b['polygon'],h,plaster if b['type']=='residential' else brick);facade(m,x,z,w,d,h,b['floors'])
        if b['type']=='residential':gable(m,x,z,w,d,h)
        else:m.box(x,z,h+.15,w+.7,d+.7,.3,blue)
    ob=m.finish(b['id']);ob['buildingId']=b['id'];return ob
print('Building footprints',flush=True)
for b in C['buildings']:building(b)
ground=Mesh();ground.box(0,0,-2.5,680,585,5,concrete);ground.box(0,0,.02,665,570,.12,grass)
ground.box(-187,155,.12,160,157,.16,soil)
# Yard pocket between 国际部 and 厂房 / 装备楼 (not a south E–W road).
ground.box(32,198,.11,48,50,.14,soil)
for g in C.get('greens',[]):
    ground.box(g['x'],g['z'],.22,g['w'],g['d'],.14,grass)
def clip(a,b):
    # Match campus extent [-330,-285,340,285] so southern city roads (范阳中路) stay continuous.
    dx,dz=b[0]-a[0],b[1]-a[1];lo,hi=0.,1.
    for p,q in [(-dx,a[0]+330),(dx,340-a[0]),(-dz,a[1]+285),(dz,285-a[1])]:
        if p==0:
            if q<0:return None
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
    if lo>hi:return None
    return [a[0]+lo*dx,a[1]+lo*dz],[a[0]+hi*dx,a[1]+hi*dz]
def strip(m,a,b,width,y,mat):
    dx,dz=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dz)
    if l<.01:return
    nx,nz=-dz/l*width/2,dx/l*width/2
    m.shape([(a[0]+nx,y,a[1]+nz),(a[0]-nx,y,a[1]-nz),(b[0]-nx,y,b[1]-nz),(b[0]+nx,y,b[1]+nz)],[(3,2,1,0)],mat)
for road_index,road in enumerate(C['roads']):
    for segment_index,(a,b) in enumerate(zip(road['points'],road['points'][1:])):
        pair=clip(a,b)
        if not pair:continue
        y=.19+road_index*.01+segment_index*.0002
        a,b=pair;strip(ground,a,b,road['width']+4,y-.035,concrete);strip(ground,a,b,road['width'],y,asphalt)
        length=math.dist(a,b)
        for s in range(0,int(length),12):
            p=[a[i]+(b[i]-a[i])*s/length for i in [0,1]];q=[a[i]+(b[i]-a[i])*min(s+5,length)/length for i in [0,1]];strip(ground,p,q,.20,y+.01,line)
for p in C['parking']:
    x,z=p['x'],p['z'];ground.box(x,z,.2,3.3,6,.18,asphalt)
    for dx in [-1.6,1.6]:ground.box(x+dx,z,.31,.10,5.8,.035,line)
    ground.box(x,z-2.9,.31,3.3,.12,.035,line);ground.box(x,z-2.15,.42,1.4,.3,.2,concrete)
for x in [-82,165]:
    for i in range(10):ground.box(x-6+i*1.3,253,.5,.68,7,.045,line)
ground.finish('Ground_and_roads')
print('Growing plane trees',flush=True)
tree=Mesh()
for idx,(x,z) in enumerate(C['trees']):
    height=8+random.random()*3;tree.pole(x,z,height*.32,.28,height*.64,bark)
    for j in range(10):
        angle=j*2.4;radius=random.uniform(.5,3.3);tree.sphere(x+math.cos(angle)*radius,z+math.sin(angle)*radius,height+random.uniform(-1.5,1),random.uniform(2.2,3),random.uniform(2,3),random.uniform(1.8,2.7),leaves[j%4])
tree.finish('Trees')
furn=Mesh()
for x in [-89,173]:
    for z in range(-214,252,42):
        furn.pole(x,z,4.3,.10,8.6,steel);furn.box(x+1.1,z,8.5,2.5,.18,.18,steel);furn.box(x+2.2,z,8.45,.85,.45,.18,lamp)
for x in [-74,148]:
    furn.pole(x,251,2.8,.15,5.6,steel);furn.box(x,251,5.45,1.0,.4,.45,white)
furn.finish('Street_furniture')
def export(path,objects=None):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects or [o for o in bpy.context.scene.objects if o.type=='MESH']:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_extras=True)
export(OUT/'campus.glb')
for bid in ['international','equipment']:export(OUT/(bid+'.glb'),[bpy.data.objects[bid]])
if os.environ.get('SKIP_RENDER')=='1':
    (OUT/'manifest.json').write_text(json.dumps({'generator':'Blender '+bpy.app.version_string,'buildings':len(C['buildings']),'trees':len(C['trees']),'note':'OSM outlines + screenshot massing; two office facades based on user photos; unseen elevations and dimensions estimated; Cycles stills skipped'},indent=2),encoding='utf8')
    print('DONE (GLB only)',flush=True);raise SystemExit(0)
static=list(bpy.context.scene.objects)
def car(x=0,z=0,color=white):
    m=Mesh();m.box(x,z,.8,1.8,4.2,.7,color);m.box(x,z-.2,1.35,1.58,2.15,.75,glass);m.box(x,z-.2,1.77,1.58,1.7,.1,color)
    for dx in [-.91,.91]:
        for dz in [-1.35,1.35]:m.sphere(x+dx,z+dz,.48,.17,.40,.40,tire)
    for dx in [-.61,.61]:m.box(x+dx,z+2.12,.88,.43,.08,.20,lamp);m.box(x+dx,z-2.12,.88,.40,.08,.20,red)
    m.box(x,z+2.17,.6,.7,.06,.18,glass);return m.finish('Vehicle')
carOb=car();export(OUT/'vehicle.glb',[carOb]);bpy.data.objects.remove(carOb,do_unlink=True)
person=[]
for name,x,z,y,w,d,h,mat in [('Body',0,0,1.15,.48,.28,.6,blue),('Head',0,0,1.66,.28,.28,.29,plaster),('LeftLeg',-.14,0,.45,.16,.20,.70,steel),('RightLeg',.14,0,.45,.16,.20,.70,steel),('LeftArm',-.32,0,1.05,.14,.19,.58,blue),('RightArm',.32,0,1.05,.14,.19,.58,blue)]:
    m=Mesh();m.box(x,z,y,w,d,h,mat);ob=m.finish(name)
    if name.endswith('Leg') or name.endswith('Arm'):
        pivot=Vector((x,-z,y+h/2));ob.data.transform(Matrix.Translation(-pivot));ob.location=pivot
    person.append(ob)
export(OUT/'pedestrian.glb',person)
# Use the same deterministic motion samples as the browser for editable Blender animation.
motion_path=ROOT/'blender/motion.json'
if motion_path.exists():
    motion=json.loads(motion_path.read_text(encoding='utf8'))
    for idx in range(12):
        root=bpy.data.objects.new(f'Walker_{idx+1:02d}',None);bpy.context.collection.objects.link(root)
        for src in person:
            limb=src.copy();limb.data=src.data;bpy.context.collection.objects.link(limb);limb.parent=root
            if limb.name.startswith(('LeftLeg','RightLeg','LeftArm','RightArm')):
                sign=1 if limb.name.startswith(('LeftLeg','RightArm')) else -1
                for frame,angle in [(1,-.4),(13,.4),(25,-.4)]:limb.rotation_euler.x=angle*sign;limb.keyframe_insert('rotation_euler',frame=frame)
                for fcurve in limb.animation_data.action.fcurves:fcurve.modifiers.new('CYCLES')
        for s in motion:
            p=s['people'][idx];root.location=(p['x'],-p['z'],.3);root.rotation_euler.z=-p['angle'];root.keyframe_insert('location',frame=1+s['t']*24);root.keyframe_insert('rotation_euler',frame=1+s['t']*24)
    for idx in range(8):
        ob=car(color=[white,steel,glass,red][idx%4]);ob.name=f'Animated_vehicle_{idx+1}'
        for s in motion:
            p=s['cars'][idx];ob.location=(p['x'],-p['z'],.33);ob.rotation_euler.z=-p['angle'];ob.keyframe_insert('location',frame=1+s['t']*24);ob.keyframe_insert('rotation_euler',frame=1+s['t']*24)
    for ob in bpy.context.scene.objects:
        if ob.animation_data and ob.animation_data.action:
            for curve in ob.animation_data.action.fcurves:
                for key in curve.keyframe_points:key.interpolation='LINEAR'
for ob in person:bpy.data.objects.remove(ob,do_unlink=True)
# A representative still uses the same simulated parking placements.
for i,p in enumerate(C['parking'][:58]):car(p['x'],p['z'],[white,steel,glass,red][i%4])
backdrop=Mesh();backdrop.box(0,0,-5.2,8000,8000,.15,material('Backdrop',(.24,.29,.27)));backdrop.finish('Render_background');
world=bpy.data.worlds.new('Daylight');bpy.context.scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;sky=nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=math.radians(40);sky.sun_rotation=math.radians(135);sky.altitude=.1
world.node_tree.links.new(sky.outputs['Color'],nodes.get('Background').inputs['Color']);nodes.get('Background').inputs['Strength'].default_value=.15
bpy.ops.object.light_add(type='SUN',location=(100,-100,250));bpy.context.object.rotation_euler=(.45,-.5,-.6);bpy.context.object.data.energy=2.0;bpy.context.object.data.angle=.07
bpy.ops.object.camera_add(location=(580,-740,660));cam=bpy.context.object;direction=Vector((0,0,0))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.clip_end=5000;cam.data.ortho_scale=920;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.frame_end=21601;scene.render.fps=24;scene.frame_set(2881);scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(RENDERS/'campus-daylight.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/campus.blend'))
print('Rendering Cycles overview',flush=True);bpy.ops.render.render(write_still=True)
for bid in ['international','equipment']:
    b=next(b for b in C['buildings'] if b['id']==bid)
    cam.location=(b['x']+b['w']*.62,-(b['z']+b['d']/2+100),b['height']*.90)
    target=Vector((b['x'],-b['z'],b['height']*.46));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(b['w']*1.40,b['height']*2.60)
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.filepath=str(RENDERS/(bid+'-photo-guided.png'))
    bpy.ops.render.render(write_still=True)
(OUT/'manifest.json').write_text(json.dumps({'generator':'Blender '+bpy.app.version_string,'buildings':len(C['buildings']),'trees':len(C['trees']),'note':'OSM outlines + screenshot massing; two office facades based on user photos; unseen elevations and dimensions estimated'},indent=2),encoding='utf8')
print('DONE',flush=True)



