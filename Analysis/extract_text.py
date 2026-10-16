"""Build the aligned, single-column English corpus and source-location map."""
import collections
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / 'Analysis'
CSV = ROOT / 'expeditions-conquistador_text.csv'
SELECTED = [('sharedassets0.assets', 16, 'UI'), ('sharedassets1.assets', 772, 'Level0'),
            ('sharedassets1.assets', 793, 'Level1'), ('sharedassets1.assets', 781, 'RandomEvents'),
            ('sharedassets1.assets', 796, 'Codex')]
DISPLAY_FIELDS = {('Event', 'Name'), ('FollowerAdd', 'Bio'), ('Text', 'Text'),
                  ('Dialog', 'Text'), ('Choice', 'ChoiceText'), ('Goal', 'Title'),
                  ('Goal', 'Description'), ('Codex', 'Title'), ('Codex', 'Text')}
GUI_CONFIG = {'LanguageCulture', 'CustomCinematicsTutorialLanguage'}
records, trees = [], {}
inventory = json.loads((ANALYSIS / 'textasset_inventory.json').read_text('utf-8'))
index = {(x['asset_file'], x['path_id']): x for x in inventory}

def add(text, **location):
    if not text or not text.strip():
        return
    records.append({'row': len(records) + 1, 'text': text, **location})

def walk(node, path):
    yield node, path
    counters = collections.Counter()
    for child in node:
        counters[child.tag] += 1
        yield from walk(child, f'{path}/{child.tag}[{counters[child.tag]}]')

for filename, path_id, category in SELECTED:
    asset = index[filename, path_id]
    raw = (ROOT / asset['export']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == asset['sha256']
    tree = ET.fromstring(raw)
    if category != 'UI':
        assert tree.findtext('GUILanguageFile') == 'GUI-en'
    parents = {child: parent for parent in tree.iter() for child in parent}
    trees[asset['export']] = dict((path, node) for node, path in walk(tree, '/' + tree.tag))
    for node, xpath in walk(tree, '/' + tree.tag):
        parent = parents.get(node)
        if parent is None or len(node):
            continue
        if category == 'UI':
            selected = parent is tree and node.tag not in GUI_CONFIG
        else:
            selected = (parent.tag, node.tag) in DISPLAY_FIELDS
        if not selected:
            continue
        context = {}
        ancestor = parent
        while ancestor is not None:
            if ancestor.tag == 'Event':
                context['event'] = ancestor.findtext('Tag')
            if ancestor.find('NodeTag') is not None:
                context.setdefault('node_tag', ancestor.findtext('NodeTag'))
            if ancestor.tag == 'Dialog':
                context['speaker'] = ancestor.findtext('Speaker')
            ancestor = parents.get(ancestor)
        add(node.text, kind='xml', category=category, asset_file=filename, path_id=path_id,
            asset_name=asset['name'], export=asset['export'], xpath=xpath, field=node.tag,
            context=context)

mono = json.loads((ANALYSIS / 'mono_inventory.json').read_text('utf-8'))
MONO_FIELDS = {'EventInfo': {'eventMapName', 'goalActiveMarkerName'},
               'EventEnemy': {'eventMapName'}, 'MarkerInfo': {'name'}, 'HostGUI': {'title'}}
for asset in mono:
    cls = asset['class']
    if cls not in MONO_FIELDS and cls != 'TutorialController':
        continue
    data = json.loads((ROOT / asset['export']).read_text('utf-8'))
    for path, value in asset['strings']:
        selected = path[-1] in MONO_FIELDS.get(cls, set())
        if cls == 'TutorialController' and path[-1] in ('sideName', 'headline'):
            selected = data['tutorials']['tutorialSets'][path[2]]['language'] == 0
        if selected:
            add(value, kind='mono', category='Tutorial' if cls == 'TutorialController' else 'Map/UI',
                asset_file=asset['asset_file'], path_id=asset['path_id'], class_name=cls,
                export=asset['export'], field_path=path)

# Direct display strings reviewed in the decompiled application classes.
# Internal keys, debug controls and old unused GUIs are excluded.
CODE_STRINGS = {
    'CampaignSelectionGUI': {'Colombo Easy', 'Cortes Normal', 'Pizarro Difficult', 'Aguirre Insane'},
    'OptionsMenu': {'Colombo Easy', 'Cortes Normal', 'Pizarro Difficult', 'Aguirre Insane',
                    'Full Res', 'Half Res', 'Quarter Res', 'Eighth Res'},
    'HostGUI': {'All Mixed', 'Spanish Only', 'Native Only', 'All non special'},
    'ComboBox': {'Custom'}, 'CampingSystemGUI': {'Rations'}, 'TreatmentGUI': {'Rations'},
    'VersionLabel': {'version '},
}
for cls, wanted in CODE_STRINGS.items():
    file = ANALYSIS / 'decompiled' / 'Assembly-CSharp' / (cls + '.cs')
    method_token = None
    for line_no, line in enumerate(file.read_text('utf-8-sig').splitlines(), 1):
        token = re.search(r'Token: (0x060[0-9A-F]+)', line)
        if token:
            method_token = token.group(1)
        for match in re.finditer(r'"(?:[^"\\]|\\.)*"', line):
            value = json.loads(match.group())
            if value in wanted and ('GUIContent' in line or 'GUI.Button' in line):
                add(value, kind='managed', category='Hardcoded UI',
                    asset_file='Managed/Assembly-CSharp.dll', class_name=cls,
                    method_token=method_token, source=file.relative_to(ROOT).as_posix(), source_line=line_no,
                    source_column=match.start() + 1,
                    note='Patch this display occurrence only; never replace internal keys globally.')

with CSV.open('w', encoding='utf-8-sig', newline='') as f:
    csv.writer(f, lineterminator='\n').writerows([r['text']] for r in records)
(ANALYSIS / 'text_mapping.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')

# Verify every CSV record against the exact mapped XML field, serialized value or C# literal.
rows = list(csv.reader(CSV.open(encoding='utf-8-sig', newline='')))
assert len(rows) == len(records) and all(len(row) == 1 for row in rows)
mono_cache = {}
for row, record in zip(rows, records):
    assert row[0] == record['text'] and row[0].strip()
    if record['kind'] == 'xml':
        assert row[0] == trees[record['export']][record['xpath']].text
    elif record['kind'] == 'mono':
        if record['export'] not in mono_cache:
            mono_cache[record['export']] = json.loads((ROOT / record['export']).read_text('utf-8'))
        value = mono_cache[record['export']]
        for part in record['field_path']:
            value = value[part]
        assert row[0] == value
    else:
        line = (ROOT / record['source']).read_text('utf-8-sig').splitlines()[record['source_line'] - 1]
        assert row[0] in [json.loads(m.group()) for m in re.finditer(r'"(?:[^"\\]|\\.)*"', line)]
locations = [(r['kind'], r['asset_file'], r.get('path_id'), r.get('xpath'),
              str(r.get('field_path')), r.get('source'), r.get('source_line'), r.get('source_column')) for r in records]
assert len(set(locations)) == len(records)
source_hashes = json.loads((ANALYSIS / 'source_hashes.json').read_text('utf-8'))
for source in source_hashes:
    p = ROOT / 'Game' / 'Expeditions Conquistador_Data' / source['file']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == source['sha256'], source['file']
dll = ROOT / 'Game' / 'Expeditions Conquistador_Data' / 'Managed' / 'Assembly-CSharp.dll'
report = {'records': len(records), 'unique_texts': len(set(r['text'] for r in records)),
          'by_category': dict(collections.Counter(r['category'] for r in records)),
          'by_kind': dict(collections.Counter(r['kind'] for r in records)),
          'characters': sum(len(r['text']) for r in records),
          'words_approx': sum(len(re.findall(r"\b[\w'-]+\b", r['text'])) for r in records),
          'multiline_records': sum('\n' in r['text'] for r in records),
          'csv_sha256': hashlib.sha256(CSV.read_bytes()).hexdigest(),
          'managed_dll_sha256': hashlib.sha256(dll.read_bytes()).hexdigest(),
          'selected_textassets': [index[f, i] for f, i, _ in SELECTED],
          'validation': {'single_column': True, 'no_header': True, 'exact_source_roundtrip': True,
                         'unique_locations': True, 'all_171_unity_files_unchanged': True},
          'limitations': ['Tutorial body text and cinematic text baked into images/movies are not extracted.',
                          '462 unrelated or partially decoded MonoBehaviours have schema errors; see mono_errors.json.',
                          'Hardcoded UI list covers reviewed occurrences; runtime residual-English testing is still needed.',
                          'GivenName/FamilyName are excluded because gameplay code also uses these identities.']}
(ANALYSIS / 'extraction_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('selected_textassets', 'limitations')}, indent=2))
