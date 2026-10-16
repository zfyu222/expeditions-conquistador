"""Select 150 source-only samples by mapped type, scene, speaker and risk."""
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / 'TranslateFiles'
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from workflow_quality import risk_reasons

rows = json.loads((ROOT / 'Analysis/text_mapping.json').read_text(encoding='utf-8-sig'))
contexts = json.loads((TF / 'config/normalized_context.json').read_text(encoding='utf-8-sig'))
for row in rows:
    row['ordinal'] = row['row']
    row['source'] = row['text']
    row['metadata'] = contexts[str(row['row'])]
    row['risk'] = risk_reasons(row)

quotas = {'UI label/fragment': 16, 'UI description': 8, 'Dialogue': 36,
          'Player choice': 28, 'Narrative': 24, 'Quest': 10, 'Event title': 2,
          'Biography': 6, 'Codex': 8, 'Map/UI': 6, 'Tutorial': 4, 'Hardcoded UI': 2}
assert sum(quotas.values()) == 150
seeds = {3, 4, 771, 773, 2099, 3878, 4725, 4728, 5116, 5121, 11138, 14156}
chosen = []
for kind, count in quotas.items():
    pool = [r for r in rows if r['metadata']['text_type'] == kind]
    picks = [r for r in pool if r['ordinal'] in seeds]
    seen_groups, seen_speakers, seen_categories, seen_risks, seen_lengths = set(), set(), set(), set(), set()

    def mark(row):
        seen_groups.add(row['metadata']['group'])
        seen_speakers.add(row['metadata']['speaker'])
        seen_categories.add(row['category'])
        seen_risks.update(row['risk'])
        seen_lengths.add('long' if len(row['source']) >= 300 else 'short')

    for row in picks:
        mark(row)
    while len(picks) < count:
        used = {r['ordinal'] for r in picks}
        available = [r for r in pool if r['ordinal'] not in used]
        if not available:
            break

        def score(row):
            m = row['metadata']
            return (5 * (m['group'] not in seen_groups)
                    + 5 * (bool(m['speaker']) and m['speaker'] not in seen_speakers)
                    + 4 * (row['category'] not in seen_categories)
                    + 2 * len(set(row['risk']) - seen_risks)
                    + 2 * (('long' if len(row['source']) >= 300 else 'short') not in seen_lengths),
                    len(row['risk']), -row['ordinal'])
        row = max(available, key=score)
        picks.append(row)
        mark(row)
    chosen.extend(picks)

assert len(chosen) == len({r['ordinal'] for r in chosen}) == 150
config = {'pilot_ordinals': sorted(r['ordinal'] for r in chosen)}
(TF / 'config/pilot_selection_v2.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
report = {'records': len(chosen), 'types': dict(Counter(r['metadata']['text_type'] for r in chosen)),
          'source_categories': dict(Counter(r['category'] for r in chosen)),
          'dialogue_speakers': dict(Counter(r['metadata']['speaker'] for r in chosen if r['metadata']['text_type'] == 'Dialogue')),
          'scene_groups': len({r['metadata']['group'] for r in chosen}),
          'risk_flags': dict(Counter(flag for r in chosen for flag in r['risk'])),
          'shortest_chars': min(len(r['source']) for r in chosen),
          'longest_chars': max(len(r['source']) for r in chosen),
          'limitations': ['Representative sample is not every branch/character.',
                         'Unattributed Dialogue remains unattributed.',
                         'Tutorial image bodies/cinematic text are outside extracted CSV.'],
          'samples': [{'ordinal': r['ordinal'], 'category': r['category'], 'metadata': r['metadata'],
                       'source': r['source'], 'risk': r['risk']} for r in sorted(chosen, key=lambda r: r['ordinal'])]}
(TF / 'reports/pilot_selection_plan.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'samples'}, ensure_ascii=False, indent=2))
