"""Derive authored speaker/text type from mapped XML fields, without touching text."""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / 'TranslateFiles'
mapping = json.loads((ROOT / 'Analysis/text_mapping.json').read_text(encoding='utf-8-sig'))
original = json.loads((TF / 'config/extracted_context.json').read_text(encoding='utf-8-sig'))
normalized = {}
speaker_changes = 0
for item in mapping:
    ordinal = str(item['row'])
    context = dict(original[ordinal])
    field = item.get('field', '')
    category = item['category']
    old_speaker = context.get('speaker', '')
    context['source_field'] = context['text_type']
    if category == 'UI':
        kind = 'UI description' if '\n' in item['text'] or len(item['text']) >= 160 else 'UI label/fragment'
    elif category == 'Codex':
        kind = 'Codex'
    elif category in ('Map/UI', 'Tutorial', 'Hardcoded UI'):
        kind = category
    elif field == 'Bio':
        kind = 'Biography'
    elif field in ('Title', 'Description'):
        kind = 'Quest'
    elif field == 'Name':
        kind = 'Event title'
    elif field == 'ChoiceText':
        kind = 'Player choice'
    elif field == 'Text' and re.search(r'/Dialog\[\d+\]/Text\[\d+\]$', item.get('xpath', '')):
        kind = 'Dialogue'
    else:
        kind = 'Narrative'
    context['text_type'] = kind
    if kind == 'Player choice':
        context['speaker'] = 'Player'
        context['dialogue_partner'] = old_speaker.strip()
        context['note'] += ' ChoiceText 是玩家选项；dialogue_partner 表示对话对象，不是此条作者。'
    elif kind == 'Dialogue':
        context['speaker'] = old_speaker.strip()
    else:
        context['speaker'] = ''
    speaker_changes += context['speaker'] != old_speaker
    normalized[ordinal] = context
assert set(normalized) == set(original)
assert len(normalized) == 14691
(TF / 'config/normalized_context.json').write_text(json.dumps(normalized, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
report = {'records': len(normalized), 'speaker_metadata_changes': speaker_changes,
          'text_types': dict(Counter(r['text_type'] for r in normalized.values())),
          'limitations': ['No speaker invented for unattributed Dialogue.',
                         'Player choice author separated from dialogue recipient.',
                         'Original text, source positions and scene grouping are unchanged.']}
(TF / 'reports/context_normalization.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
