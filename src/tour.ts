/** Camera positions use the campus model's X east, Y up, Z south coordinates. */
export const TOUR_SHOTS = [
  {title:'全院区 · 鸟瞰开场',seconds:7,position:[480,570,740],target:[0,0,0]},
  {title:'南侧入口 · 院区全貌',seconds:6,position:[30,175,455],target:[25,18,165]},
  {title:'国际部 · 独立办公区',seconds:7,position:[-200,145,325],target:[-33,34,177]},
  {title:'厂房 · 蓝色拱顶与院落',seconds:7,position:[95,85,265],target:[35,8,183]},
  {title:'装备专业化大楼',seconds:7,position:[230,125,275],target:[109,18,175]},
  {title:'梧桐树 · 南北主路',seconds:7,position:[163,22,95],target:[166,5,-75]},
  {title:'住宅区 · 行道与楼群',seconds:8,position:[350,235,-20],target:[160,8,-45]},
  {title:'北侧办公楼 · 园区纵深',seconds:7,position:[130,175,-375],target:[85,15,-177]},
  {title:'全院区 · 收束全景',seconds:0,position:[-400,480,-560],target:[0,0,0]},
] as const;

export const TOUR_LEAD_IN=2;
export const TOUR_DURATION=TOUR_LEAD_IN+TOUR_SHOTS.reduce((sum,shot)=>sum+shot.seconds,0);

export function sampleTour(seconds:number){
  let elapsed=Math.max(0,Math.min(TOUR_DURATION-TOUR_LEAD_IN,seconds));
  for(let i=0;i<TOUR_SHOTS.length-1;i++){
    const from=TOUR_SHOTS[i],to=TOUR_SHOTS[i+1];
    if(elapsed>from.seconds&&i<TOUR_SHOTS.length-2){elapsed-=from.seconds;continue;}
    const t=Math.min(1,elapsed/from.seconds);
    const eased=t*t*(3-2*t);
    const mix=(a:readonly number[],b:readonly number[])=>a.map((value,axis)=>value+(b[axis]-value)*eased) as [number,number,number];
    return {position:mix(from.position,to.position),target:mix(from.target,to.target),chapter:i,title:from.title};
  }
  throw new Error('Tour has no camera segment');
}
