"""Inventory serialized MonoBehaviour strings using managed type schemas."""
import json
import re
from pathlib import Path
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.Tpk import get_typetree_node

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'Game' / 'Expeditions Conquistador_Data'
generator = TypeTreeGenerator('4.3.2f1')
generator.load_local_dll_folder(str(DATA / 'Managed'))
out = ROOT / 'Analysis' / 'mono'
out.mkdir(exist_ok=True)
inventory, errors, classes = [], [], set()

def strings(value, path=()):
    if isinstance(value, str):
        if value.strip():
            yield list(path), value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(item, (*path, key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from strings(item, (*path, i))

for path in sorted(DATA.iterdir(), key=lambda p: p.name):
    if not (path.suffix == '.assets' or path.name == 'mainData' or re.fullmatch(r'level\d+', path.name)):
        continue
    env = UnityPy.load(str(path))
    env.typetree_generator = generator
    count = 0
    for obj in env.objects:
        if obj.assets_file.name != path.name or obj.type.name != 'MonoBehaviour':
            continue
        script = None
        try:
            script = obj.parse_monobehaviour_head().m_Script.deref().read()
            classes.add(script.m_ClassName)
            fullname = (script.m_Namespace + '.' if script.m_Namespace else '') + script.m_ClassName
            node = generator.get_nodes_up(script.m_AssemblyName, fullname)
            # Use Unity 4's native header, including padding of m_Enabled before m_Script.
            node.m_Children = list(get_typetree_node(obj.type, obj.version).m_Children) + list(node.m_Children[4:])
            tree = obj.read_typetree(nodes=node)
            found = list(strings(tree))
            if not found:
                continue
            dest = out / path.name / f'{obj.path_id}_{script.m_ClassName}.json'
            dest.parent.mkdir(exist_ok=True)
            dest.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding='utf-8')
            inventory.append({'asset_file': path.name, 'path_id': obj.path_id, 'class': script.m_ClassName,
                              'export': dest.relative_to(ROOT).as_posix(), 'strings': found})
            count += 1
        except Exception as exc:
            errors.append({'file': path.name, 'path_id': obj.path_id,
                           'class': script.m_ClassName if script else None, 'error': str(exc)})
    if count:
        print(path.name, count, flush=True)
    del env
(ROOT / 'Analysis' / 'mono_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'Analysis' / 'mono_errors.json').write_text(json.dumps(errors, indent=2), encoding='utf-8')
(ROOT / 'Analysis' / 'mono_classes.json').write_text(json.dumps(sorted(classes), indent=2), encoding='utf-8')
print('Objects with strings', len(inventory), 'errors', len(errors))
