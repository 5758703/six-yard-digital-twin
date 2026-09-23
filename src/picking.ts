type PickNode={name:string;userData:Record<string,unknown>;parent:PickNode|null};
export function findBuildingId(node:PickNode|null,validIds:Set<string>):string|undefined {
  while(node){const id=typeof node.userData.buildingId==='string'?node.userData.buildingId:node.name;if(validIds.has(id))return id;node=node.parent;}return undefined;
}
