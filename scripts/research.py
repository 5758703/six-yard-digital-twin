import urllib.request, urllib.parse, json, pathlib, datetime, hashlib, concurrent.futures
ROOT = pathlib.Path(__file__).resolve().parents[1]
def fetch(url, path):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'SixYardTwin/1.0 research'})
        with urllib.request.urlopen(req,timeout=60) as r: data=r.read()
        (ROOT/path).write_bytes(data)
        print(str(path),len(data),flush=True)
        return data
    except Exception as e: print(str(path),str(e),flush=True)
query='[out:json][timeout:30];way[highway][name~"亨通|火炬|朝阳|范阳"](39.45,115.90,39.53,116.08);out geom;'
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    jobs=[pool.submit(fetch,'https://overpass-api.de/api/interpreter?data='+urllib.parse.quote(query),pathlib.Path('public/data/osm-road-discovery.json')),pool.submit(fetch,'https://download.blender.org/release/Blender4.5/',pathlib.Path('.tools/blender-index.html'))]
    for job in jobs: job.result()
