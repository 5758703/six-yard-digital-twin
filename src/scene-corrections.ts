import type * as THREE from 'three';

/** Reserved for residual runtime patches. Rebuilt campus.glb already matches campus.json. */
export function applySceneCorrections(_model:THREE.Group){
  // no-op: layout, roads, lawns and factories are baked by blender/build_campus.py
}
