import urllib.request, pathlib, zipfile, hashlib
root=pathlib.Path(__file__).resolve().parents[1]/'.tools'
version='4.5.3'
name=f'blender-{version}-windows-x64'
url=f'https://mirror.clarkson.edu/blender/release/Blender4.5/{name}.zip'
archive=root/(name+'.zip')
print('Downloading',url,flush=True)
urllib.request.urlretrieve(url,archive)
print('Downloaded',archive.stat().st_size,'sha256',hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
with zipfile.ZipFile(archive) as z: z.extractall(root)
print('Ready',root/name/'blender.exe',flush=True)

