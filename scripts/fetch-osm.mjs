import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
// The road intersections were verified against osm-road-discovery.json.
const bbox = [39.4831,116.0206,39.4890,116.0298];
const query = `[out:json][timeout:45];(way[highway](${bbox});way[building](${bbox});way[landuse](${bbox});way[amenity=parking](${bbox});node[natural=tree](${bbox}););out geom;`;
const endpoint = 'https://overpass-api.de/api/interpreter';
await mkdir('public/data',{recursive:true});
const response = await fetch(`${endpoint}?data=${encodeURIComponent(query)}`, {headers:{'User-Agent':'SixYardTwin/1.0 research'},signal:AbortSignal.timeout(90000)});
if (!response.ok) throw new Error(`OSM request failed: ${response.status}`);
const raw=await response.text(); const data=JSON.parse(raw);
if (data.remark || !data.elements?.length) throw new Error(data.remark || 'OSM returned no features');
const provenance={downloadedAt:new Date().toISOString(),osmTimestamp:data.osm3s.timestamp_osm_base,endpoint,query,bbox,sha256:createHash('sha256').update(raw).digest('hex'),elementCount:data.elements.length,attribution:'© OpenStreetMap contributors',license:'ODbL 1.0',licenseUrl:'https://www.openstreetmap.org/copyright',limitations:'内部建筑和树木不足时按用户截图补绘；楼高、立面和模拟运行不来自 OSM。'};
await writeFile('public/data/osm-2026-09-20.json',raw);
await writeFile('public/data/osm-provenance.json',JSON.stringify(provenance,null,2));
console.log(JSON.stringify(provenance,null,2));
