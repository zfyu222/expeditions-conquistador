"""Prepare reviewed protection configuration and test actual corpus boundaries."""
import csv
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import read_json, write_json
root = Path(__file__).resolve().parents[2]
tf = root / 'TranslateFiles'
config = read_json(tf / 'config/workflow.json')
exclusions = config['exclusions']
old = exclusions[1]['regex']
new = old.replace('(?![A-Za-z])', '(?![A-Za-z0-9_])') + r'|(?<![A-Za-z])(?:[PF]HimHer)\d*(?=self\b)'
pattern = re.compile(new)
assert re.findall(old, 'FHimHer1self') == ['FHimHer']
assert pattern.findall('FHimHer1self') == ['FHimHer1']
assert pattern.findall('FHimHer12self') == ['FHimHer12']
assert pattern.findall('FHimHer1本人') == ['FHimHer1']
assert pattern.findall('FNameFirst1 and PHimHer') == ['FNameFirst1', 'PHimHer']
assert not pattern.findall('FNameFirst1suffix AFNameFirst1 FNameFirst1_extra')
exclusions[1]['regex'] = new
style = config['style'] + ' 冻结术语若对应技能名但本条是普通词义，须按原句含义处理并逐项说明语境例外；不能添加技能施放。主人公及动态角色未确定性别时，不增加固定性别设定。'
write_json(tf / 'config/variable_boundary_v2.json', {'exclusions': exclusions, 'style': style})
rows = list(csv.reader((root / 'expeditions-conquistador_text.csv').open(encoding='utf-8-sig', newline='')))
affected = []
for ordinal, row in enumerate(rows, 1):
    suffixes = re.findall(r'[PF]HimHer\d*self', row[0])
    if suffixes:
        for token in suffixes:
            assert pattern.findall(token) == [token[:-4]]
        affected.append({'ordinal': ordinal, 'templates': suffixes})
assert len(affected) == 6
write_json(tf / 'reports/variable_boundary_validation.json', {
    'source_records': len(rows), 'old_regex': old, 'new_regex': new,
    'affected': affected, 'boundary_examples': 6, 'result': 'passed',
    'reason': 'Prevent numeric-index backtracking; preserve HimHer index before translatable reflexive suffix self',
    'formal_export_exists': (root / 'expeditions-conquistador_text_translated.csv').exists()
})
print(json.dumps({'affected_records': len(affected), 'boundary_examples': 6, 'result': 'passed'}))
