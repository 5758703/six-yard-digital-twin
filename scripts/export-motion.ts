import { writeFileSync } from 'node:fs';
import { sampleWorld, PARKED_COUNT } from '../src/simulation.ts';
const samples=Array.from({length:181},(_,i)=>{const t=i*5,s=sampleWorld(t);return {t,cars:s.cars.slice(PARKED_COUNT,PARKED_COUNT+8),people:s.people.slice(0,12)};});
writeFileSync('blender/motion.json',JSON.stringify(samples));
console.log('Exported 900-second Blender motion samples.');
