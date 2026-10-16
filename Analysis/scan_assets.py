"""Read-only Unity TextAsset inventory and lossless export for extraction."""
import hashlib
import json
import re
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'Game' / 'Expeditions Conquistador_Data'
OUT = ROOT / 'Analysis' / 'textassets'
OUT.mkdir(parents=True, exist_ok=True)
inventory = []
files = []
for path in sorted(DATA.iterdir(), key=lambda p: p.name):
    if not (path.suffix == '.assets' or path.name == 'mainData' or re.fullmatch(r'level\d+', path.name)):
        continue
    env = UnityPy.load(str(path))
    found = []
    for obj in env.objects:
        if obj.assets_file.name != path.name or obj.type.name != 'TextAsset':
            continue
        asset = obj.read()
        raw = asset.m_Script.encode('utf-8', errors='surrogateescape')
        dest = OUT / path.name / f'{obj.path_id}_{asset.m_Name}.txt'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        entry = {'asset_file': path.name, 'path_id': obj.path_id, 'name': asset.m_Name,
                 'export': dest.relative_to(ROOT).as_posix(), 'size': len(raw),
                 'sha256': hashlib.sha256(raw).hexdigest()}
        inventory.append(entry)
        found.append(entry['name'])
    files.append({'file': path.name, 'size': path.stat().st_size,
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'textassets': len(found)})
    if found:
        print(path.name, len(found), ', '.join(found), flush=True)
    del env
(ROOT / 'Analysis' / 'textasset_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'Analysis' / 'source_hashes.json').write_text(json.dumps(files, indent=2), encoding='utf-8')
print('TOTAL', len(inventory), 'files scanned', len(files), 'UnityPy', UnityPy.__version__)
