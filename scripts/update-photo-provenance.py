import pathlib,json
r=pathlib.Path(__file__).resolve().parents[1]
p=r/'public/data/campus.json';c=json.loads(p.read_text(encoding='utf8'))
for b in c['buildings']:
    if b['id'] in ['international','equipment']:
        b['source']='用户标注位置及实景立面照片；未见立面、尺寸与高度近似'
        b['facadeReference']='references/'+b['id']+'-facade.jpg'
c['modelLimitations']='OSM 地理底图；两栋重点楼可见立面依据用户实景照片重建；未见立面、尺寸、高度及绿化近似，非测绘成果。'
p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
p=r/'scripts/prepare-campus.py';s=p.read_text(encoding='utf8').replace('用户标注位置；截图补绘；高度与立面为近似','用户标注位置及实景立面照片；未见立面、尺寸与高度近似');p.write_text(s,encoding='utf8')
p=r/'src/App.vue';s=p.read_text(encoding='utf8').replace('尚未取得能够核实两栋办公楼立面的现场照片，未以其他园区照片冒充。','两栋重点楼的可见立面已依据您补充的实景照片重建。第二张仅展示入口局部，未见部分仍为近似。').replace('办公楼轮廓、层数、外立面及绿化为近似重建。','两栋重点楼可见立面依据您提供的实景照片；轮廓、层数、未见立面及绿化仍为近似。');p.write_text(s,encoding='utf8')
p=r/'README.md';s=p.read_text(encoding='utf8').replace('用户标注截图；形体、高度、楼层及立面为近似重建','用户标注截图与两张实景照片；可见立面按照片重建，未见立面、形体尺寸与高度仍为近似').replace('尚未取得能够可靠匹配两栋办公楼立面的现场照片；不能承诺测绘级或照片级现场一致性。','用户随后提供了两栋重点楼的实景照片，已用于更新可见立面；第二张只展示入口局部，不能推断完整楼高和背面。不能承诺测绘级或照片级现场一致性。');s+='\n## 实景立面修订\n\n两栋重点楼已按用户补充照片更新：国际部采用竖向青绿玻璃、白色石材分格、挑檐及中英文标识；装备楼采用玻璃幕墙、金属装饰立柱、入口雨棚及蓝色中文标识。照片保存在 references，近景渲染在 renders/*-photo-guided.png，建模代码在 blender/photo_facades.py。照片中的临时车辆不属于建筑模型。\n';p.write_text(s,encoding='utf8')
for name in ['docs/research.md','docs/validation.md']:
    p=r/name;s=p.read_text(encoding='utf8');s+='\n## 后续实景照片修订（2026-09-20）\n\n以上未获得立面照片的记录为初版研究状态，现由用户补充的两张照片更新：照片 1 为国际部大楼，照片 2 为装备专业化大楼入口。新增 photo_facades.py 重建可见建筑细节；未见侧后立面与实际尺寸仍为推定，照片没有作为含车辆和遮挡物的平面贴图。\n';p.write_text(s,encoding='utf8')

# Preserve user-confirmed floor counts after regeneration.
exec((pathlib.Path(__file__).resolve().parent/'confirm-floors.py').read_text(encoding='utf8'))
