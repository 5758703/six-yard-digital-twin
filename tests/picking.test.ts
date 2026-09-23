import test from 'node:test';
import assert from 'node:assert/strict';
import { findBuildingId } from '../src/picking.ts';
test('a GLB material primitive resolves the building ID on its ancestor group',()=>{const parent={name:'international',userData:{buildingId:'international'},parent:null};const child={name:'international_1',userData:{},parent};assert.equal(findBuildingId(child,new Set(['international'])),'international');assert.equal(findBuildingId(child,new Set(['equipment'])),undefined);});
