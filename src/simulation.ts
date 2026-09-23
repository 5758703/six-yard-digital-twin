import campus from '../public/data/campus.json' with { type: 'json' };
export type Point = [number, number];
export type ActorMode = 'walk' | 'bike' | 'ebike';
export type Actor = {id:string;x:number;z:number;angle:number;parked:boolean;slot:number;phase:number;mode?:ActorMode};
export type AlertRecord = {id:string;buildingId:string;at:number;title:string;level:'warning'|'critical';ackAt?:number;resolvedAt?:number};
export const DURATION=900;
export const PARKED_COUNT=54;
/** Fewer circulating cars inside the campus grid. */
export const CAMPUS_MOVING=8;
/** More traffic on 范阳中路. */
export const FANYANG_MOVING=18;
export const MOVING_COUNT=CAMPUS_MOVING+FANYANG_MOVING;
export const WALK_COUNT=180;
export const BIKE_COUNT=48;
export const EBIKE_COUNT=42;
export const PEOPLE_COUNT=WALK_COUNT+BIKE_COUNT+EBIKE_COUNT;
export const ACTOR_CAR_COUNT=PARKED_COUNT+MOVING_COUNT;
const LANE=2.8;
const FANYANG_Z=240;
const NORTH_Z=146;
const EAST_X=166;
const WEST_X=-82;
const SPUR_X=16;
const GATE_X=-32.6;
const INT_SOUTH=200;
export function advanceTime(time:number,dt:number,playing:boolean,speed:number){return Math.min(DURATION,Math.max(0,time+(playing?dt*speed:0)));}
export function pathLength(points:Point[]){return points.slice(1).reduce((s,p,i)=>s+Math.hypot(p[0]-points[i][0],p[1]-points[i][1]),0);}
export function samplePath(points:Point[],distance:number){
  if(!points.length)return {x:0,z:0,angle:0};
  let left=Math.max(0,distance);
  for(let i=1;i<points.length;i++){
    const a=points[i-1],b=points[i],length=Math.hypot(b[0]-a[0],b[1]-a[1]);
    if(left<=length&&length>0){const k=left/length;return {x:a[0]+(b[0]-a[0])*k,z:a[1]+(b[1]-a[1])*k,angle:Math.atan2(b[0]-a[0],b[1]-a[1])};}left-=length;
  }
  const p=points[points.length-1];return{x:p[0],z:p[1],angle:0};
}
export function lanePath(points:Point[],side:1|-1=1,offset=LANE):Point[]{
  if(points.length<2)return points.map(p=>[...p] as Point);
  return points.map((p,i)=>{
    const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)];
    let dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz);
    if(len<.001){const j=Math.min(points.length-2,i);dx=points[j+1][0]-points[j][0];dz=points[j+1][1]-points[j][1];len=Math.hypot(dx,dz)||1;}
    return [p[0]+side*(dz/len)*offset,p[1]+side*(-dx/len)*offset] as Point;
  });
}
const roadLoops:Point[][]=[
  [[EAST_X,NORTH_Z],[EAST_X,-225],[WEST_X,-225],[WEST_X,NORTH_Z],[EAST_X,NORTH_Z]],
  [[WEST_X,NORTH_Z],[WEST_X,-225],[EAST_X,-225],[EAST_X,NORTH_Z],[WEST_X,NORTH_Z]],
  [[EAST_X,NORTH_Z],[EAST_X,27],[WEST_X,27],[WEST_X,NORTH_Z],[EAST_X,NORTH_Z]],
  [[WEST_X,NORTH_Z],[WEST_X,27],[EAST_X,27],[EAST_X,NORTH_Z],[WEST_X,NORTH_Z]],
  // 南门：先沿楼西到楼南，再中轴直连范阳中路（闭合时不出现斜穿楼体的对角线）
  [[WEST_X,NORTH_Z],[WEST_X,INT_SOUTH],[GATE_X,INT_SOUTH],[GATE_X,FANYANG_Z],[GATE_X,INT_SOUTH],[WEST_X,INT_SOUTH],[WEST_X,NORTH_Z]],
  [[WEST_X,27],[WEST_X,INT_SOUTH],[GATE_X,INT_SOUTH],[GATE_X,FANYANG_Z],[GATE_X,INT_SOUTH],[WEST_X,INT_SOUTH],[WEST_X,27]],
];
function campusRoute(i:number):Point[]{
  const slot=PARKED_COUNT+(i%(campus.parking.length-PARKED_COUNT));
  const p=campus.parking[slot];
  const loop=roadLoops[i%roadLoops.length];
  const usesGate=loop.some(([x,z])=>Math.abs(x-GATE_X)<1&&z>=INT_SOUTH-1);
  const gate:Point=usesGate?[WEST_X,NORTH_Z]:loop[0][0]>50?[EAST_X,NORTH_Z]:loop[0][0]>0?[SPUR_X,NORTH_Z]:[WEST_X,NORTH_Z];
  const center:Point[]=[[p.x,p.z],[p.x,NORTH_Z],gate,...loop,gate,[p.x,NORTH_Z],[p.x,p.z]];
  if(!usesGate)return [[p.x,p.z],...lanePath(center.slice(1,-1),1,LANE),[p.x,p.z]];
  return center;
}
const fanyangRoutes:Point[][]=Array.from({length:FANYANG_MOVING},(_,i)=>{
  const span=280+(i%3)*20;
  const off=LANE+0.4+(i%4)*.15;
  const south=lanePath([[-span,FANYANG_Z],[span,FANYANG_Z]],1,off);
  const north=lanePath([[span,FANYANG_Z],[-span,FANYANG_Z]],1,off);
  return i%2===0?[...south,...north,south[0]]:[...north,...south,north[0]];
});
export const vehicleRoutes:Point[][]=[
  ...Array.from({length:CAMPUS_MOVING},(_,i)=>campusRoute(i)),
  ...fanyangRoutes,
];
const vehicleLengths=vehicleRoutes.map(pathLength);
const walkRoutes:Point[][]=[
  [[WEST_X+4,NORTH_Z],[EAST_X-4,NORTH_Z],[EAST_X-4,-225],[WEST_X+4,-225],[WEST_X+4,NORTH_Z]],
  [[WEST_X,27],[EAST_X,27],[EAST_X,20],[WEST_X,20],[WEST_X,27]],
  [[-190,35],[-130,35],[-130,90],[-190,90],[-190,35]],
  [[WEST_X,NORTH_Z],[EAST_X,NORTH_Z],[EAST_X,-225],[WEST_X,-225],[WEST_X,NORTH_Z]],
  [[-185,40],[-125,40],[-125,90],[-185,90],[-185,40]],
  [[SPUR_X,NORTH_Z],[WEST_X,NORTH_Z],[WEST_X,27],[SPUR_X,27],[SPUR_X,NORTH_Z]],
  [[SPUR_X,NORTH_Z],[EAST_X,NORTH_Z],[EAST_X,27],[SPUR_X,27],[SPUR_X,NORTH_Z]],
  // 南门：楼中轴南缘直连范阳中路，经楼西南侧回院（不穿楼）
  [[GATE_X-2.5,FANYANG_Z],[GATE_X-2.5,INT_SOUTH],[WEST_X,INT_SOUTH],[WEST_X,NORTH_Z],[WEST_X,INT_SOUTH],[GATE_X-2.5,INT_SOUTH],[GATE_X-2.5,FANYANG_Z]],
  [[GATE_X+2.5,FANYANG_Z],[GATE_X+2.5,INT_SOUTH],[WEST_X,INT_SOUTH],[WEST_X,27],[WEST_X,INT_SOUTH],[GATE_X+2.5,INT_SOUTH],[GATE_X+2.5,FANYANG_Z]],
];
const walkLengths=walkRoutes.map(pathLength);
const cycleRoutes:Point[][]=[
  ...walkRoutes,
  lanePath([[-280,FANYANG_Z],[300,FANYANG_Z]],1,12),
  lanePath([[300,FANYANG_Z],[-280,FANYANG_Z]],1,12),
  [[GATE_X+2.5,FANYANG_Z],[GATE_X+2.5,INT_SOUTH],[WEST_X,INT_SOUTH],[WEST_X,NORTH_Z],[EAST_X-4,NORTH_Z],[WEST_X,NORTH_Z],[WEST_X,INT_SOUTH],[GATE_X+2.5,INT_SOUTH],[GATE_X+2.5,FANYANG_Z]],
  [[WEST_X+4,NORTH_Z],[EAST_X-4,NORTH_Z],[EAST_X-4,-225],[WEST_X+4,-225],[WEST_X+4,NORTH_Z]],
];
const cycleLengths=cycleRoutes.map(pathLength);
function personActor(id:string,mode:ActorMode,routeIndex:number,speed:number,time:number,seed:number):Actor{
  const routes=mode==='walk'?walkRoutes:cycleRoutes;
  const lengths=mode==='walk'?walkLengths:cycleLengths;
  const n=routeIndex%routes.length;
  const phase=time*speed+seed;
  return {id,...samplePath(routes[n],phase%lengths[n]),parked:false,slot:-1,phase,mode};
}
export function sampleWorld(time:number){
  const t=Math.max(0,Math.min(DURATION,time));
  const cars:Actor[]=campus.parking.slice(0,PARKED_COUNT).map((p,i)=>({id:`V${i+1}`,x:p.x,z:p.z,angle:0,parked:true,slot:i,phase:0}));
  vehicleRoutes.forEach((route,i)=>{
    const onFanyang=i>=CAMPUS_MOVING;
    const dwell=onFanyang?0:8+i*3;
    const speed=onFanyang?12+(i%4)*1.1:i%2===0?8.2:7;
    const period=Math.max(dwell+vehicleLengths[i]/speed,1);
    const phase=(t+i*17)%period;
    const parked=!onFanyang&&phase<dwell;
    const p=samplePath(route,parked?0:(phase-dwell)*speed);
    cars.push({id:`V${PARKED_COUNT+1+i}`,...p,parked,slot:onFanyang?-1:PARKED_COUNT+(i%(campus.parking.length-PARKED_COUNT)),phase});
  });
  const people:Actor[]=[
    ...Array.from({length:WALK_COUNT},(_,i)=>personActor(`P${i+1}`,'walk',i,1.05+(i%5)*.12,t,i*29)),
    ...Array.from({length:BIKE_COUNT},(_,i)=>personActor(`B${i+1}`,'bike',i,3.2+(i%4)*.25,t,i*37+11)),
    ...Array.from({length:EBIKE_COUNT},(_,i)=>personActor(`E${i+1}`,'ebike',i,4.1+(i%5)*.3,t,i*41+23)),
  ];
  return {
    cars,people,
    parked:cars.filter(c=>c.parked).length,
    moving:cars.filter(c=>!c.parked).length,
    walkers:people.filter(p=>p.mode==='walk').length,
    bikes:people.filter(p=>p.mode==='bike').length,
    ebikes:people.filter(p=>p.mode==='ebike').length,
    energy:Math.round(186+17*Math.sin(t/80)+9*Math.cos(t/32)),
    water:Math.round((6.2+.8*Math.sin(t/190))*10)/10,
  };
}
export function createAlert(buildingId:string,at:number,index:number):AlertRecord{return{id:`AL-${index+1}`,buildingId,at,title:['车辆异常停留','楼宇温度偏高','设备离线'][index%3],level:index%3===1?'critical':'warning'};}
export function activeAlerts(alerts:AlertRecord[],time:number){return alerts.filter(a=>a.at<=time).map(a=>({...a,status:a.resolvedAt!==undefined&&time>=a.resolvedAt?'已解除':a.ackAt!==undefined&&time>=a.ackAt?'已确认':'待处理'}));}
export function recordAlertAction(a:AlertRecord,action:'ack'|'resolve',at:number){
  if(at<a.at)return;
  if(action==='ack'&&a.ackAt===undefined)a.ackAt=at;
  if(action==='resolve'&&a.resolvedAt===undefined&&a.ackAt!==undefined&&at>=a.ackAt)a.resolvedAt=at;
}
