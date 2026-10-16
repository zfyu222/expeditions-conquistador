import collections
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / 'TranslateFiles'
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
import ainiee_bridge as bridge
from translation_workflow import Workflow

config = {
    'workflow': 'custom', 'backend': 'codex', 'model': 'gpt-6-luna',
    'source_language': '英语', 'target_language': '简体中文',
    'style': '忠实自然的历史冒险与战术RPG文体。叙述清晰流畅，对话保留人物情绪、讽刺、粗口和时代感，避免过度文言或现代网络用语；不增删剧情。UI、技能与任务标题简练明确。保留原文空白、实际换行序列、引号和所有保护标记。斜体/粗体标记仅作为控制符保留，不扩展其作用范围。方括号中的 Check 提示属于玩家可见文字，译为检定提示。',
    'batch_records': 180, 'batch_chars': 22000, 'context_records': 2,
    'polish': False, 'max_attempts': 3, 'lease_seconds': 14400,
    'placeholder_family_overrides': {'square_bracket': r'\[(?:HOTKEY|Stack|s|es|NAME|TASK)\]'},
    'exclusions': [
        {'markers': '', 'regex': r'[/\*$]', 'info': '对话样式控制字符，原样保留次数和作用范围'},
        {'markers': '', 'regex': r'(?<![A-Za-z])(?:[PF](?:Name(?:First|Last)?|HeShe|HimHer|HisHer|SenorSenora|SenorSenorita|ManWoman|BoyGirl|SonDaughter)|F(?:Type|Rank))\d*(?![A-Za-z])|\bPNAME(?:FIRST|LAST)?\b|\b(?:RationsLost|MedicineGathered|Int_[A-Za-z0-9_]+|ManAtArms)\b', 'info': 'NodeText/NodeGoal 动态姓名、代词、数字和等级替换键'},
        {'markers': '', 'regex': r'\bXX\b', 'info': '多人游戏姓名替换键'},
    ],
}
(TF / 'config').mkdir(parents=True, exist_ok=True)
(TF / 'config' / 'init_custom.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
mapping = json.loads((ROOT / 'Analysis' / 'text_mapping.json').read_text('utf-8'))
context = {}
for row in mapping:
    category = row['category']
    event = row.get('context', {}).get('event', '') or ''
    group = category + (':' + event if event else '')
    # Non-narrative resources have stable per-component/group boundaries.
    if row['kind'] == 'mono':
        group += ':' + row['asset_file'] + ':' + row['class_name']
    if row['kind'] == 'managed':
        group += ':' + row['class_name']
    context[str(row['row'])] = {
        'group': group, 'speaker': row.get('context', {}).get('speaker', '') or '',
        'resource': f"{row['asset_file']}:{row.get('path_id', row.get('method_token', ''))}",
        'scene': category + (':' + event if event else ''),
        'text_type': row.get('field', str(row.get('field_path', ['UI'])[-1])),
        'note': ('内部变量不可译；专名按语境统一；此条源位置独立保留。' +
                 ('NodeTag=' + row.get('context', {}).get('node_tag', '') if row.get('context', {}).get('node_tag') else '')),
    }
(TF / 'config' / 'extracted_context.json').write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding='utf-8')
rules = bridge.patterns(True, config['exclusions'], config['placeholder_family_overrides'])
sample = 'PNameLast, /listen/ [HOTKEY] [Check Diplomacy Medium] FNameFirst2 {0} XX'
protected, replacements = bridge.protect(sample, 'check', rules)
assert '[Check Diplomacy Medium]' in protected
assert all(x not in protected for x in ('PNameLast', '[HOTKEY]', 'FNameFirst2', '{0}', 'XX'))
assert bridge.restore(protected, replacements) == sample
assert 'square_bracket' in bridge.structural_issues(sample, sample.replace('[HOTKEY]', ''), rules)
assert not bridge.structural_issues('[Check Diplomacy Medium]', '[交涉检定：中等]', rules)
assert any('Check' in m.group() for name, pattern in bridge.patterns() if name == 'square_bracket' for m in pattern.finditer(sample))
(TF / 'reports').mkdir(exist_ok=True)
(TF / 'reports' / 'protection_setup.json').write_text(json.dumps({'tested': True, 'example': sample, 'protected': protected, 'mapping': replacements, 'notes': 'Default families unchanged without overrides; Check player text remains translatable.'}, ensure_ascii=False, indent=2), encoding='utf-8')
flow = Workflow(ROOT)
print(json.dumps(flow.init(ROOT / 'expeditions-conquistador_text.csv', config, TF / 'config/extracted_context.json'), ensure_ascii=False, indent=2))
tasks = flow.prepare('extract')
print('Prepared extraction tasks:', len(tasks['tasks']))
