"""Apply user-confirmed floor counts; metric height remains an estimate."""
import pathlib,json
r=pathlib.Path(__file__).resolve().parents[1]
p=r/'public/data/campus.json';c=json.loads(p.read_text(encoding='utf8'))
for b in c['buildings']:
    b['floorsConfirmed']=b['id'] in ['international','equipment']
    if b['floorsConfirmed']:
        b['floors']=20 if b['id']=='international' else 6
        b['height']=72 if b['id']=='international' else 25
        b['source']='用户确认 '+str(b['floors'])+' 层；位置与可见立面依据用户图片；高度、尺寸和未见立面近似'
c['modelLimitations']='两栋重点楼层数经用户确认（国际部20层、装备楼6层）；高度仍为估算，国际部按平均层高3.6米估为72米；非测绘成果。'
p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
p=r/'src/App.vue';s=p.read_text(encoding='utf8').replace('{{b.floors}} 层（估）',"{{b.floors}} 层{{b.floorsConfirmed?'（已确认）':'（估）'}}").replace('<span>高度约 {{building.height}} m</span>',"<span>{{building.floors}} 层{{building.floorsConfirmed?'（已确认）':'（估）'}}</span><span>高度约 {{building.height}} m</span>").replace('轮廓、层数、未见立面及绿化仍为近似。','国际部 20 层、装备专业化大楼 6 层已由用户确认；高度、轮廓、未见立面及绿化仍为近似。');p.write_text(s,encoding='utf8')
# Both regeneration entrypoints must preserve the confirmed information.
for name in ['scripts/prepare-campus.py','scripts/update-photo-provenance.py']:
    p=r/name;s=p.read_text(encoding='utf8')
    hook="\n# Preserve user-confirmed floor counts after regeneration.\nexec((pathlib.Path(__file__).resolve().parent/'confirm-floors.py').read_text(encoding='utf8'))\n"
    if 'confirm-floors.py' not in s:
        if name.endswith('prepare-campus.py'):hook='\nimport pathlib\n'+hook
        p.write_text(s+hook,encoding='utf8')
