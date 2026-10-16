"""Read-only inventory of tutorial texture references and exports for localization."""
import hashlib
import json
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Analysis/tutorial_images'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mono = json.loads((ROOT / 'Analysis/mono/level2/14862_TutorialController.json').read_text('utf-8'))
    names = set()
    def walk(x):
        if isinstance(x,dict):
            if x.get('imageName'): names.add(x['imageName'])
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(mono)
    print('tutorial image references:',len(names),flush=True)
    source = ROOT / 'Game/Expeditions Conquistador_Data/resources.assets'
    env = UnityPy.load(str(source))
    inventory = []
    for obj in env.objects:
        if obj.type.name != 'Texture2D': continue
        texture = obj.read()
        key = texture.m_Name
        if key not in names and 'tutorial' not in key.lower(): continue
        entry = {'container':key,'path_id':obj.path_id,'name':texture.m_Name,
                 'width':texture.m_Width,'height':texture.m_Height}
        if texture.m_Name in names or ('tinker' in key.lower() and '_en' in key.lower()):
            target = OUT / (str(obj.path_id)+'_'+texture.m_Name+'.png')
            texture.image.save(target)
            entry.update(export=target.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        inventory.append(entry)
    report = {'references':sorted(names),'textures':inventory,'tutorial_header_reference':mono.get('tutorialHeadlineEN')}
    (ROOT/'Repack/reports/tutorial_image_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('texture inventory:',len(inventory),'exported:',sum('export' in x for x in inventory),flush=True)
    print(json.dumps([x for x in inventory if 'tinker' in x['name'].lower()],ensure_ascii=True),flush=True)

if __name__ == '__main__': main()
