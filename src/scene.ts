import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import campus from '../public/data/campus.json' with {type:'json'};
import { findBuildingId } from './picking';
import { sampleWorld,vehicleRoutes,ACTOR_CAR_COUNT } from './simulation';
import { applySceneCorrections } from './scene-corrections';
export type Building=typeof campus.buildings[number];
export type Layer='trees'|'people'|'cars'|'labels'|'routes'|'osm';
export function createScene(host:HTMLElement,onSelect:(id:string)=>void,onStats:(fps:number)=>void,onError:(message:string)=>void){
  const scene=new THREE.Scene();
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
  renderer.domElement.setAttribute('aria-label','可旋转、缩放和点击楼宇的三维园区');renderer.domElement.tabIndex=0;host.appendChild(renderer.domElement);
  const pmrem=new THREE.PMREMGenerator(renderer);const room=new RoomEnvironment();const env=pmrem.fromScene(room,.04);scene.environment=env.texture;room.dispose();pmrem.dispose();
  const camera=new THREE.PerspectiveCamera(40,1,1,4000);camera.position.set(480,570,740);
  const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,0,0);controls.enableDamping=true;controls.dampingFactor=.07;controls.maxPolarAngle=Math.PI/2-.08;controls.minDistance=30;controls.maxDistance=1600;
  const hemi=new THREE.HemisphereLight(0xddeaff,0x5e624c,2.1);scene.add(hemi);
  const sun=new THREE.DirectionalLight(0xffe5be,3.5);sun.position.set(-240,400,230);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-440,right:440,top:440,bottom:-440,near:1,far:1100});sun.shadow.bias=-.0005;sun.shadow.normalBias=.7;scene.add(sun);
  const base=new THREE.Mesh(new THREE.PlaneGeometry(8000,8000),new THREE.MeshStandardMaterial({color:0xc3cbbf,roughness:1}));base.rotation.x=-Math.PI/2;base.position.y=-5.1;base.receiveShadow=true;scene.add(base);
  const cars=new THREE.Group(),people=new THREE.Group(),routes=new THREE.Group(),osm=new THREE.Group();scene.add(cars,people,routes,osm);
  let model:THREE.Group|undefined;let disposed=false;let night=false;let labelsVisible=true;
  const labels=new Map<string,HTMLButtonElement>();const roadLabels:HTMLDivElement[]=[];
  const labelLayer=document.createElement('div');labelLayer.className='scene-label-layer';host.appendChild(labelLayer);
  campus.buildings.filter(b=>b.type==='office').forEach(b=>{const el=document.createElement('button');el.className='building-label';el.textContent=b.name;el.onclick=()=>onSelect(b.id);el.setAttribute('aria-label',`定位${b.name}`);labelLayer.appendChild(el);labels.set(b.id,el);});
  const roads=[['范阳中路',-40,240],['朝阳路',-40,-269],['亨通大街',-318,90],['火炬街',324,90]] as const;
  roads.forEach(([name])=>{const el=document.createElement('div');el.className='road-label';el.textContent=name;labelLayer.appendChild(el);roadLabels.push(el);});
  const selectLine=new THREE.LineLoop(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:0x35d6b4,depthTest:false}));selectLine.renderOrder=10;scene.add(selectLine);
  const alarmRing=new THREE.Mesh(new THREE.RingGeometry(7,10,48),new THREE.MeshBasicMaterial({color:0xf6a64b,transparent:true,opacity:.8,side:THREE.DoubleSide,depthWrite:false}));alarmRing.rotation.x=-Math.PI/2;alarmRing.visible=false;scene.add(alarmRing);
  vehicleRoutes.forEach((pts,i)=>{const geometry=new THREE.BufferGeometry().setFromPoints(pts.map(([x,z])=>new THREE.Vector3(x,.7,z)));routes.add(new THREE.Line(geometry,new THREE.LineDashedMaterial({color:i%2?0xffc568:0x3ec9c7,dashSize:4,gapSize:3,transparent:true,opacity:.7})));});routes.children.forEach(x=>(x as THREE.Line).computeLineDistances());routes.visible=false;
  campus.buildings.filter(b=>b.osmId).forEach(b=>{const pts=b.polygon.map(p=>new THREE.Vector3(p[0],.6,p[1]));const line=new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0x36b9da,depthTest:false}));line.renderOrder=20;osm.add(line);});osm.visible=false;
  const loader=new GLTFLoader();let carObjects:THREE.Object3D[]=[];let personObjects:THREE.Object3D[]=[];
  const trackedMaterials=new Set<THREE.Material>();const trackedGeometries=new Set<THREE.BufferGeometry>();
  function track(root:THREE.Object3D){root.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;o.receiveShadow=true;trackedGeometries.add(o.geometry);const ms=Array.isArray(o.material)?o.material:[o.material];ms.forEach(m=>trackedMaterials.add(m));}});}
  function makeCycle(kind:'bike'|'ebike',rider:THREE.Object3D){
    const root=new THREE.Group();
    const frameMat=new THREE.MeshStandardMaterial({color:kind==='ebike'?0x2f6f9f:0x2c3438,roughness:.45,metalness:.35,name:kind==='ebike'?'Ebike frame':'Bike frame'});
    const tireMat=new THREE.MeshStandardMaterial({color:0x111314,roughness:.9,name:'Cycle tire'});
    const accent=new THREE.MeshStandardMaterial({color:kind==='ebike'?0xd4a017:0xb8bec2,roughness:.4,metalness:.2,name:'Cycle accent'});
    trackedMaterials.add(frameMat);trackedMaterials.add(tireMat);trackedMaterials.add(accent);
    const wheelR=kind==='ebike'?.28:.32;
    for(const z of [-.55,.55]){
      const tire=new THREE.Mesh(new THREE.TorusGeometry(wheelR,.045,8,16),tireMat);
      tire.rotation.y=Math.PI/2;tire.position.set(0,wheelR,z);root.add(tire);trackedGeometries.add(tire.geometry);
    }
    const beam=new THREE.Mesh(new THREE.BoxGeometry(.08,.06,1.05),frameMat);beam.position.set(0,wheelR+.12,0);root.add(beam);trackedGeometries.add(beam.geometry);
    const stem=new THREE.Mesh(new THREE.BoxGeometry(.06,.35,.06),frameMat);stem.position.set(0,wheelR+.32,.35);root.add(stem);trackedGeometries.add(stem.geometry);
    const bar=new THREE.Mesh(new THREE.BoxGeometry(.55,.04,.04),accent);bar.position.set(0,wheelR+.5,.35);root.add(bar);trackedGeometries.add(bar.geometry);
    if(kind==='ebike'){
      const deck=new THREE.Mesh(new THREE.BoxGeometry(.22,.05,.9),frameMat);deck.position.set(0,wheelR+.05,0);root.add(deck);trackedGeometries.add(deck.geometry);
      const panel=new THREE.Mesh(new THREE.BoxGeometry(.18,.22,.08),accent);panel.position.set(0,wheelR+.28,.2);root.add(panel);trackedGeometries.add(panel.geometry);
    }else{
      const seat=new THREE.Mesh(new THREE.BoxGeometry(.16,.05,.28),accent);seat.position.set(0,wheelR+.38,-.15);root.add(seat);trackedGeometries.add(seat.geometry);
    }
    const person=rider.clone(true);
    person.scale.setScalar(kind==='ebike'?.85:.9);
    person.position.set(0,kind==='ebike'?wheelR+.15:wheelR+.22,kind==='ebike'?.05:-.05);
    person.traverse(o=>{if(o instanceof THREE.Mesh){o.castShadow=true;}});
    root.add(person);
    root.userData.kind=kind;
    return root;
  }
  const ready=Promise.allSettled([loader.loadAsync('/models/campus.glb'),loader.loadAsync('/models/vehicle.glb'),loader.loadAsync('/models/pedestrian.glb')]).then(results=>{
    const failed=results.find(r=>r.status==='rejected');
    if(failed){results.forEach(r=>{if(r.status==='fulfilled')r.value.scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}});});throw failed.reason;}
    const [g,c,p]=results.map(r=>(r as PromiseFulfilledResult<Awaited<ReturnType<typeof loader.loadAsync>>>).value);
    if(disposed){[g,c,p].forEach(a=>a.scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}}));return;}
    model=g.scene;applySceneCorrections(model);track(model);scene.add(model);track(c.scene);track(p.scene);
    carObjects=Array.from({length:ACTOR_CAR_COUNT},(_,i)=>{const o=c.scene.clone(true);o.traverse(m=>{if(m instanceof THREE.Mesh&&i%4!==0){const mats=Array.isArray(m.material)?m.material:[m.material];const copies=mats.map(material=>{const v=material.clone();if(v.name==='White paint'&&v instanceof THREE.MeshStandardMaterial)v.color.set([0xe9edef,0x416071,0x993b2e,0x414851][i%4]);trackedMaterials.add(v);return v;});m.material=Array.isArray(m.material)?copies:copies[0];}});cars.add(o);return o;});
    const world0=sampleWorld(0);
    personObjects=world0.people.map((a)=>{
      const o=a.mode==='bike'||a.mode==='ebike'?makeCycle(a.mode,p.scene):p.scene.clone(true);
      people.add(o);return o;
    });
    update(0);
  }).catch(e=>{if(!disposed)onError('三维资产加载失败。请检查 public/models 中的 GLB 文件后重试。'+String(e));throw e;});
  let time=0;let alarmId:string|undefined;let chosen:string|undefined;let tween:{from:THREE.Vector3;to:THREE.Vector3;targetFrom:THREE.Vector3;targetTo:THREE.Vector3;start:number}|undefined;
  function update(t:number){time=t;const world=sampleWorld(t);world.cars.forEach((a,i)=>{const o=carObjects[i];if(o){o.position.set(a.x,.33,a.z);o.rotation.y=a.angle;}});world.people.forEach((a,i)=>{const o=personObjects[i];if(!o)return;const bike=a.mode==='bike'||a.mode==='ebike';o.position.set(a.x,bike?.02:.28,a.z);o.rotation.y=a.angle;if(bike)return;const phase=Math.sin(a.phase*6)*.08;o.position.y+=Math.abs(phase)*.25;for(const name of ['LeftLeg','RightLeg','LeftArm','RightArm']){const limb=o.getObjectByName(name);if(limb)limb.rotation.x=phase*5*((name==='LeftLeg'||name==='RightArm')?1:-1);}});}
  function move(to:THREE.Vector3,target:THREE.Vector3){tween={from:camera.position.clone(),to,targetFrom:controls.target.clone(),targetTo:target,start:performance.now()};}
  function select(id:string){const b=campus.buildings.find(x=>x.id===id);if(!b)return;chosen=id;selectLine.geometry.dispose();selectLine.geometry=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(b.x-b.w/2-3,.7,b.z-b.d/2-3),new THREE.Vector3(b.x+b.w/2+3,.7,b.z-b.d/2-3),new THREE.Vector3(b.x+b.w/2+3,.7,b.z+b.d/2+3),new THREE.Vector3(b.x-b.w/2-3,.7,b.z+b.d/2+3)]);move(new THREE.Vector3(b.x+120,145,b.z+185),new THREE.Vector3(b.x,b.height*.35,b.z));labels.forEach((el,key)=>el.classList.toggle('selected',key===id));}
  function setNight(value:boolean){night=value;scene.background=new THREE.Color(value?0x142735:0xcdd6d0);scene.fog=new THREE.Fog(value?0x142735:0xcdd6d0,1200,3300);hemi.intensity=value?.38:1;sun.intensity=value?.18:2.5;renderer.toneMappingExposure=value?1.1:1;scene.environmentIntensity=value?.25:.4;(base.material as THREE.MeshStandardMaterial).color.set(value?0x1b3035:0xc3cbbf);trackedMaterials.forEach(m=>{if(m instanceof THREE.MeshStandardMaterial){if(m.name.includes('glazing')){m.emissive.set(value?0xcaa45f:0x000000);m.emissiveIntensity=value?.55:0;}if(m.name.includes('diffuser'))m.emissiveIntensity=value?4:.3;}});}
  setNight(false);
  function setLayer(name:Layer,visible:boolean){if(name==='trees')model?.getObjectByName('Trees')?.traverse(o=>{o.visible=visible;});if(name==='cars')cars.visible=visible;if(name==='people')people.visible=visible;if(name==='routes')routes.visible=visible;if(name==='osm')osm.visible=visible;if(name==='labels')labelsVisible=visible;}
  function view(type:string){chosen=undefined;selectLine.geometry.dispose();selectLine.geometry=new THREE.BufferGeometry();labels.forEach(e=>e.classList.remove('selected'));if(type==='top')move(new THREE.Vector3(0,920,1),new THREE.Vector3());else if(type==='south')move(new THREE.Vector3(30,100,420),new THREE.Vector3(30,12,100));else move(new THREE.Vector3(480,570,740),new THREE.Vector3());}
  const ray=new THREE.Raycaster();const pointer=new THREE.Vector2();let down:[number,number]=[0,0];
  const onDown=(e:PointerEvent)=>{down=[e.clientX,e.clientY];tween=undefined;};
  const validBuildingIds=new Set(campus.buildings.map(b=>b.id));
  const onUp=(e:PointerEvent)=>{if(Math.hypot(e.clientX-down[0],e.clientY-down[1])>5||!model)return;const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);for(const hit of ray.intersectObject(model,true)){const id=findBuildingId(hit.object,validBuildingIds);if(id){onSelect(id);break;}}};
  renderer.domElement.addEventListener('pointerdown',onDown);renderer.domElement.addEventListener('pointerup',onUp);
  const onContextLost=(e:Event)=>{e.preventDefault();onError('WebGL 上下文已丢失，请点击重新加载。');};renderer.domElement.addEventListener('webglcontextlost',onContextLost);
  const resize=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(w&&h){renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}});resize.observe(host);
  function place(el:HTMLElement,x:number,y:number,z:number){const p=new THREE.Vector3(x,y,z).project(camera);el.style.display=labelsVisible&&p.z<1&&p.z>-1?'':'none';el.style.left=`${(p.x*.5+.5)*host.clientWidth}px`;el.style.top=`${(-p.y*.5+.5)*host.clientHeight}px`;}
  let last=performance.now(),frames=0;let anim=0;
  function frameLoop(now:number){if(disposed)return;anim=requestAnimationFrame(frameLoop);if(tween){const k=Math.min(1,(now-tween.start)/1050),ease=1-Math.pow(1-k,3);camera.position.lerpVectors(tween.from,tween.to,ease);controls.target.lerpVectors(tween.targetFrom,tween.targetTo,ease);if(k===1)tween=undefined;}controls.update();campus.buildings.filter(b=>labels.has(b.id)).forEach(b=>place(labels.get(b.id)!,b.x,b.height+8,b.z));roads.forEach((r,i)=>place(roadLabels[i],r[1],1,r[2]));alarmRing.visible=!!alarmId;if(alarmId){const b=campus.buildings.find(x=>x.id===alarmId);if(b){alarmRing.position.set(b.x,b.height+2,b.z);alarmRing.scale.setScalar(1+(time%2)*.3);}}
    renderer.render(scene,camera);frames++;if(now-last>1000){onStats(Math.round(frames*1000/(now-last)));last=now;frames=0;}}
  anim=requestAnimationFrame(frameLoop);
  return {ready,update,select,setNight,setLayer,view,setAlert:(id?:string)=>{alarmId=id;},get selected(){return chosen;},get night(){return night;},destroy(){disposed=true;cancelAnimationFrame(anim);resize.disconnect();controls.dispose();renderer.domElement.removeEventListener('pointerdown',onDown);renderer.domElement.removeEventListener('pointerup',onUp);renderer.domElement.removeEventListener('webglcontextlost',onContextLost);scene.traverse(o=>{if(o instanceof THREE.Mesh||o instanceof THREE.Line){o.geometry.dispose();(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose());}});trackedGeometries.forEach(g=>g.dispose());trackedMaterials.forEach(m=>m.dispose());env.dispose();renderer.dispose();host.replaceChildren();}};
}


