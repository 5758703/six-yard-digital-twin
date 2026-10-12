import test from 'node:test';
import assert from 'node:assert/strict';
import {sampleTour,TOUR_DURATION,TOUR_LEAD_IN,TOUR_SHOTS} from '../src/tour.ts';

test('camera tour covers distinct campus scenes and ends at the final overview',()=>{
  assert.ok(TOUR_SHOTS.length>=7);
  assert.ok(TOUR_SHOTS.some(shot=>shot.title.includes('厂房')));
  assert.ok(TOUR_SHOTS.some(shot=>shot.title.includes('住宅')));
  const end=sampleTour(TOUR_DURATION-TOUR_LEAD_IN);
  assert.deepEqual(end.position,[...TOUR_SHOTS.at(-1)!.position]);
  assert.deepEqual(end.target,[...TOUR_SHOTS.at(-1)!.target]);
});

test('tour path is continuous at every camera transition',()=>{
  let boundary=0;
  for(const shot of TOUR_SHOTS.slice(0,-2)){
    boundary+=shot.seconds;
    const before=sampleTour(boundary-.001);
    const after=sampleTour(boundary+.001);
    const gap=Math.hypot(...before.position.map((value,i)=>value-after.position[i]));
    assert.ok(gap<.1,`camera jumps ${gap} m at ${shot.title}`);
  }
  for(let seconds=0;seconds<=TOUR_DURATION;seconds+=.25){
    const shot=sampleTour(seconds);
    assert.ok([...shot.position,...shot.target].every(Number.isFinite));
    assert.ok(shot.position[1]>10);
  }
});
