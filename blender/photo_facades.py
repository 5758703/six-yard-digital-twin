"""Photo-guided facades. Unseen rear elevations and dimensions remain estimates."""
def build_photo_office(b, ns):
    import bpy, math
    Mesh=ns['Mesh']; material=ns['material']; mats=ns['MAT']
    x,z,w,d,h=(b[k] for k in ['x','z','w','d','height'])
    stone=material('Photo white stone',(.82,.83,.80),.58)
    glazing=material('Photo jade curtain glass',(.27,.49,.47),.19,.48)
    seam=material('Photo silver mullions',(.40,.47,.46),.35,.65)
    dark=material('Photo dark lettering',(.09,.15,.21),.38,.2)
    silver=material('Photo brushed aluminium',(.67,.71,.72),.35,.65)
    lettering=material('Equipment blue signage',(.32,.53,.82),.34,.2)
    concrete=ns['concrete']; steel=ns['steel'];glass=ns['glass']
    m=Mesh();south=z+d/2
    m.box(x,z,.22,w+4,d+4,.44,concrete)
    # Full street-facing slab replaces the former unverified U-shaped front.
    m.box(x,z,h/2,w,d,h,stone)
    texts=[]
    def text(body,xx,zz,yy,size,mat,width):
        curve=bpy.data.curves.new(body,'FONT');curve.body=body;curve.align_x='CENTER';curve.size=size;curve.extrude=.035;curve.bevel_depth=.008
        if any(ord(c)>127 for c in body):
            try:curve.font=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttf')
            except RuntimeError:pass
        ob=bpy.data.objects.new(body,curve);bpy.context.collection.objects.link(ob);ob.location=(xx,-zz,yy);ob.rotation_euler=(math.pi/2,0,0);curve.materials.append(mats[mat]);bpy.context.view_layer.update()
        if ob.dimensions.x>width:ob.scale.x*=width/ob.dimensions.x
        texts.append(ob)
    if b['id']=='international':
        # Photograph: continuous narrow jade bays, broad pale piers, sparse cross bands.
        bays=19;pitch=w/bays
        for side in [-1,1]:
            zz=z+side*(d/2+.10)
            for i in range(bays):
                xx=x-w/2+(i+.5)*pitch
                m.box(xx,zz,h*.48,pitch*.64,.18,h*.88,glazing)
                for level in range(1,b['floors']):m.box(xx,zz+side*.11,level*h/b['floors'],pitch*.64,.05,.065,seam)
                m.box(xx,zz+side*.12,h*.48,.045,.05,h*.88,seam)
                if i%4==1:m.box(xx+.4,zz+side*.15,h*(.28+(i%5)*.12),.8,.06,.6,silver)
            for yy in [h*.20,h*.67,h*.92]:m.box(x,zz+side*.14,yy,w,.18,.85,stone)
        for side in [-1,1]:
            for j in range(12):
                m.box(x+side*(w/2+.1),z-d/2+(j+.5)*d/12,h*.48,.15,d/12*.65,h*.88,glazing)
                for level in range(1,b['floors']):m.box(x+side*(w/2+.20),z-d/2+(j+.5)*d/12,level*h/b['floors'],.05,d/12*.65,.065,seam)
        # Stone panel joint grid, kept subtle and geometric.
        for i in range(bays+1):m.box(x-w/2+i*pitch,south+.23,h/2,.025,.03,h, silver)
        for j in range(1,24):m.box(x,south+.24,j*h/24,w,.025,.025,silver)
        m.box(x,south+.3,3.1,20,.3,5.7,glass)
        for xx in [-8,-4,0,4,8]:m.box(x+xx,south+.55,3.1,.15,.2,5.8,silver)
        m.box(x,south+2.0,6.5,26,4.2,.35,silver)
        for xx in [-11,0,11]:m.box(x+xx,south+1.8,6.8,.2,4.3,.32,steel)
        # Shallow segmented overhanging roof and elevated company sign.
        for i in range(20):
            xx=x-w/2+(i+.5)*w/20;yy=h+.8+1.1*((xx-x)/(w/2))**2
            m.box(xx,z,yy,w/20+.03,d+1.8,.42,concrete)
            if i%3==0:m.box(xx,south-.7,h+.45,.18,.18,1.1,steel)
        text('BGP INTERNATIONAL, CNPC',x,south+.46,h*.945,1.32,dark,w*.70)
        text('中国石油集团东方地球物理公司',x+2,south-1,h+3.0,2.25,dark,w*.82)
        # Stylized photo-reference corporate sun emblem, not a pasted photograph.
        emblem=material('CNPC emblem gold',(.88,.64,.12),.4)
        red=material('CNPC emblem red',(.67,.10,.12),.4)
        m.sphere(x-w*.44,south-1,h+3.8,1.75,.2,1.35,emblem);m.box(x-w*.44,south-.77,h+3.2,2.8,.08,.55,red)
        for dx in [-6,0,6]:m.pole(x+dx,south+4,7,.06,14,silver)
    else:
        # Photo 2 shows only the entrance; upper and rear grids are extrapolated.
        for sign in [-1,1]:
            zz=z+sign*(d/2+.12)
            m.box(x,zz,h/2,w-.4,.18,h-.5,glazing)
            for i in range(41):m.box(x-w/2+i*w/40,zz+sign*.12,h/2,.055,.10,h,seam)
            for j in range(13):m.box(x,zz+sign*.12,j*h/12,w,.10,.055,seam)
            for i in range(9):
                xx=x-w/2+(i+.5)*w/9;m.box(xx,zz+sign*.20,h/2,1.1,.32,h,silver)
                for yy in range(1,int(h)):
                    m.box(xx,zz+sign*.38,yy,.84,.04,.045,dark)
                    for dx in [-.28,0,.28]:m.box(xx+dx,zz+sign*.40,yy+.4,.10,.025,.10,dark)
            for yy in [1.2,8.5,16.5,h]:m.box(x,zz+sign*.24,yy,w,.32,.6,silver)
        for sign in [-1,1]:
            m.box(x+sign*(w/2+.12),z,h/2,.18,d,h-.5,glazing)
            for j in range(19):m.box(x+sign*(w/2+.24),z-d/2+j*d/18,h/2,.10,.055,h,seam)
            for yy in range(2,int(h),2):m.box(x+sign*(w/2+.24),z,yy,.10,d,.055,seam)
        m.box(x,south+.45,3.0,17,.55,5.5,steel)
        m.box(x,south+.78,3.0,14,.10,5.1,glass)
        for dx in [-8,8]:m.box(x+dx,south+1.0,3.0,.65,1.3,6,silver)
        m.box(x,south+1.0,5.9,17,1.3,.65,silver)
        m.box(x,south+3.0,7.0,27,6,.13,glazing)
        for dx in range(-12,13,3):m.box(x+dx,south+3,6.87,.13,6,.19,silver)
        for dz in [0,2,4,6]:m.box(x,south+dz,6.87,27,.13,.19,silver)
        for dx in [-11,11]:
            # Sloped canopy suspension rods.
            m.shape([(x+dx-.07,10,south+.2),(x+dx+.07,10,south+.2),(x+dx+.07,7,south+5.6),(x+dx-.07,7,south+5.6)],[(0,1,2,3)],steel)
        text('物探装备专业化服务中心',x,south+1.0,8.0,1.7,lettering,29)
        m.box(x,z,h+.25,w+1,d+1,.5,silver)
    for j in range(4):m.box(x,south+1+j*.8,.65-j*.15,22+j*1.2,.9,.3,concrete)
    ob=m.finish(b['id']);ob['buildingId']=b['id'];ob['floors']=b['floors'];ob['floorsConfirmed']=True;ob['estimatedHeightMeters']=h;ob['facadeSource']='User facade photographs and confirmed floor counts; unseen elevations and height estimated'
    # Merge text meshes into the building so selection/export remains self-contained.
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
    for label in texts:
        bpy.context.view_layer.objects.active=label;label.select_set(True);ob.select_set(False);bpy.ops.object.convert(target='MESH');label.select_set(False);ob.select_set(True)
    for label in texts:label.select_set(True)
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.join()
    return ob
