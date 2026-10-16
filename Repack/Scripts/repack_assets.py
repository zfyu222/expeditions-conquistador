"""Rebuild five Unity files using the extraction map; verify untouched objects."""
import collections
import copy
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.Tpk import get_typetree_node

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Game/Expeditions Conquistador_Data'
BUILD = ROOT / 'Repack/Build/Game/Expeditions Conquistador_Data'
EXPECTED_SOURCE = '8ba04dc104e24e2b6c7a10a33f323a501524b4ceba7d7b5f4a9d9e72dcc9c96e'
EXPECTED_TRANSLATION = 'eaad404d187d8ff9ce67ec722bd4d9ead82f81c679f4998d1482bbabd5ca4b48'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def walk(node, path):
    yield path, node
    counts = collections.Counter()
    for child in node:
        counts[child.tag] += 1
        yield from walk(child, f'{path}/{child.tag}[{counts[child.tag]}]')

def xml_index(raw):
    root = ET.fromstring(raw)
    return root, dict(walk(root, '/' + root.tag))

def node_for(obj, generator):
    script = obj.parse_monobehaviour_head().m_Script.deref().read()
    fullname = (script.m_Namespace + '.' if script.m_Namespace else '') + script.m_ClassName
    node = generator.get_nodes_up(script.m_AssemblyName, fullname)
    node.m_Children = list(get_typetree_node(obj.type, obj.version).m_Children) + list(node.m_Children[4:])
    return node

def get_field(tree, path):
    for key in path:
        tree = tree[key]
    return tree

def set_field(tree, path, value):
    for key in path[:-1]:
        tree = tree[key]
    tree[path[-1]] = value

def main():
    source_path = ROOT / 'expeditions-conquistador_text.csv'
    translation_path = ROOT / 'expeditions-conquistador_text_translated.csv'
    assert sha(source_path.read_bytes()) == EXPECTED_SOURCE
    assert sha(translation_path.read_bytes()) == EXPECTED_TRANSLATION
    with source_path.open(encoding='utf-8-sig', newline='') as f:
        source = [r[0] for r in csv.reader(f)]
    with translation_path.open(encoding='utf-8-sig', newline='') as f:
        translations = [r[0] for r in csv.reader(f)]
    records = json.loads((ROOT / 'Analysis/text_mapping.json').read_text('utf-8'))
    assert len(source) == len(translations) == len(records) == 14691
    for rec, original, translated in zip(records, source, translations):
        assert rec['text'] == original and translated.strip()
        rec['translation'] = translated
    baseline = {x['file']: x['sha256'] for x in json.loads((ROOT / 'Analysis/source_hashes.json').read_text('utf-8'))}
    groups = collections.defaultdict(list)
    for rec in records:
        if rec['kind'] != 'managed':
            groups[rec['asset_file']].append(rec)
    managed = [r for r in records if r['kind'] == 'managed']
    (ROOT / 'Repack/Build/managed_map.json').write_text(json.dumps(managed, ensure_ascii=False, indent=2), encoding='utf-8')
    generator = TypeTreeGenerator('4.3.2f1')
    generator.load_local_dll_folder(str(DATA / 'Managed'))
    report = {'source_sha256': EXPECTED_SOURCE, 'translation_sha256': EXPECTED_TRANSLATION,
              'unitypy': UnityPy.__version__, 'records': len(records), 'files': []}
    BUILD.mkdir(parents=True, exist_ok=True)
    for filename, assigned in groups.items():
        backup = ROOT / 'Repack/Backup/SteamBuild1752467/Expeditions Conquistador_Data' / filename
        path = backup if backup.exists() else DATA / filename
        assert sha(path.read_bytes()) == baseline[filename], f'Unsupported source: {filename}'
        print('repack', filename, len(assigned), 'records', flush=True)
        env = UnityPy.load(str(path))
        env.typetree_generator = generator
        assets = env.file
        before = {pid: sha(obj.get_raw_data()) for pid, obj in assets.objects.items()}
        by_object = collections.defaultdict(list)
        for rec in assigned:
            by_object[rec['path_id']].append(rec)
        changed = set()
        for path_id, items in by_object.items():
            obj = assets.objects[path_id]
            if items[0]['kind'] == 'xml':
                textasset = obj.read()
                root, index = xml_index(textasset.m_Script)
                old = {p: (n.tag, n.attrib.copy(), n.text, n.tail) for p, n in index.items()}
                targets = {r['xpath'] for r in items}
                for rec in items:
                    assert index[rec['xpath']].text == rec['text']
                    index[rec['xpath']].text = rec['translation']
                for p, n in index.items():
                    assert (n.tag, n.attrib, n.tail) == (old[p][0], old[p][1], old[p][3])
                    if p not in targets:
                        assert n.text == old[p][2]
                textasset.m_Script = ET.tostring(root, encoding='unicode', short_empty_elements=True)
                textasset.save()
            else:
                node = node_for(obj, generator)
                tree = obj.read_typetree(nodes=node)
                expected = copy.deepcopy(tree)
                for rec in items:
                    assert get_field(tree, rec['field_path']) == rec['text']
                    set_field(tree, rec['field_path'], rec['translation'])
                    set_field(expected, rec['field_path'], rec['translation'])
                assert tree == expected
                obj.save_typetree(tree, nodes=node)
            changed.add(path_id)
        fonts = []
        if filename == 'sharedassets1.assets':
            for obj in assets.objects.values():
                if obj.type.name != 'Font':
                    continue
                tree = obj.read_typetree()
                serif = not tree['m_Name'].startswith('persan')
                bold = tree['m_Name'].endswith(('RB', 'RBI', 'RZ', 'RZI', 'sansb', 'sanbi'))
                family = 'NotoSerifSC' if serif else 'NotoSansSC'
                style = 'Bold' if bold else 'Regular'
                font_path = ROOT / f'Repack/Build/fonts/ZFY{family}-{style}.ttf'
                tree['m_FontData'] = list(font_path.read_bytes())
                tree['m_FontNames'] = ['ZFY Conquistador ' + ('Serif' if serif else 'Sans')]
                tree['m_FallbackFonts'] = []
                tree['m_LineSpacing'] = 19.2
                tree['m_Ascent'] = 14.08
                obj.save_typetree(tree)
                changed.add(obj.path_id)
                fonts.append({'path_id': obj.path_id, 'font': font_path.name, 'sha256': sha(font_path.read_bytes())})
        out = BUILD / filename
        out.write_bytes(assets.save())
        check = UnityPy.load(str(out))
        check.typetree_generator = generator
        assert set(check.file.objects) == set(before)
        for pid, obj in check.file.objects.items():
            if pid not in changed:
                assert sha(obj.get_raw_data()) == before[pid], f'Unrelated object changed: {filename}/{pid}'
        for path_id, items in by_object.items():
            obj = check.file.objects[path_id]
            if items[0]['kind'] == 'xml':
                _, index = xml_index(obj.read().m_Script)
                for rec in items:
                    assert index[rec['xpath']].text == rec['translation']
            else:
                node = node_for(obj, generator)
                tree = obj.read_typetree(nodes=node)
                for rec in items:
                    assert get_field(tree, rec['field_path']) == rec['translation']
        report['files'].append({'game_path': 'Expeditions Conquistador_Data/' + filename,
            'source_sha256': baseline[filename], 'sha256': sha(out.read_bytes()), 'size': out.stat().st_size,
            'text_records': len(assigned), 'changed_objects': sorted(changed), 'fonts': fonts,
            'unchanged_objects_verified': len(before) - len(changed)})
        print('verified', filename, len(before)-len(changed), 'untouched objects', flush=True)
        del env, check
    report['resource_records'] = sum(x['text_records'] for x in report['files'])
    assert report['resource_records'] == 14657 and len(managed) == 34
    (ROOT / 'Repack/reports/assets_build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('resource build passed', report['resource_records'], flush=True)

if __name__ == '__main__':
    main()
