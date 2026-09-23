import urllib.request, concurrent.futures, pathlib, zipfile, time, hashlib
root=pathlib.Path(__file__).resolve().parents[1]/'.tools';parts=root/'blender-parts';parts.mkdir(exist_ok=True)
size=400100678;chunk=2*1024*1024
url='https://mirrors.ocf.berkeley.edu/blender/release/Blender4.5/blender-4.5.3-windows-x64.zip'
def part(i):
    start=i*chunk;end=min(size-1,start+chunk-1);p=parts/f'{i:04d}.part'
    if p.exists() and p.stat().st_size==end-start+1:return
    for attempt in range(6):
        try:
            endpoint=url.replace('mirrors.ocf.berkeley.edu',['mirror.clarkson.edu','mirrors.aliyun.com','mirrors.ocf.berkeley.edu'][attempt%3])
            req=urllib.request.Request(endpoint,headers={'Range':f'bytes={start}-{end}'})
            started=time.monotonic()
            with urllib.request.urlopen(req,timeout=20) as r:
                if r.status!=206 or r.headers.get('Content-Range','').split('/')[0]!=f'bytes {start}-{end}':raise RuntimeError('Unexpected range '+str(r.headers))
                chunks=[]
                while True:
                    piece=r.read1(65536)
                    if not piece:break
                    chunks.append(piece)
                    if time.monotonic()-started>60:raise TimeoutError('Range exceeded total deadline')
                data=b''.join(chunks)
            if len(data)!=end-start+1:raise RuntimeError('Wrong length')
            p.write_bytes(data);return
        except Exception as e:
            if attempt==5:raise
    
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    for i,_ in enumerate(pool.map(part,range((size+chunk-1)//chunk))):
        if i%10==0:print('Parts ready',i+1,flush=True)
archive=root/'blender-complete.zip'
with archive.open('wb') as out:
    for p in sorted(parts.glob('*.part')):out.write(p.read_bytes())
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='6b657c8bdd3a7b65b07b9e1ae17eb4be7dd4aa23121da7f3d3354fc2551330a7','Blender ZIP checksum mismatch'
with zipfile.ZipFile(archive) as z:z.extractall(root)
print('BLENDER READY',flush=True)


