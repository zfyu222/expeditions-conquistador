import csv
import json
from pathlib import Path

project = Path(__file__).resolve().parents[2]
root = project / 'TranslateFiles'
snapshot = json.loads((root / 'glossary/r4/glossary_original.json').read_text(encoding='utf-8-sig'))
decisions = json.loads((root / 'glossary/r4/freeze_5acab910/glossary_decisions.json').read_text(encoding='utf-8-sig'))
with (project / 'expeditions-conquistador_text.csv').open(encoding='utf-8-sig', newline='') as handle:
    rows = [r[0] for r in csv.reader(handle)]
refs = [284, 739, 987]
evidence = sorted({968, 1004, 1042, 1768, 1769, 6083, 6088, 6090, 14200, 6468, 11656, 6552})
payload = {
    'kind': 'glossary_revision_proposal',
    'producer_instance': '/root/glossary_mechanics_fix_producer',
    'entries': [{'ref': f'terms:{i}', 'row': snapshot['terms'][i],
                 'prior_review': next(r for r in decisions['entry_reviews'] if r['ref'] == f'terms:{i}'),
                 'prior_edits': [e for e in decisions['edits'] if e['table'] == 'terms' and e['index'] == i]}
                for i in refs],
    'related_entries': [{'ref': f'terms:{i}', 'row': snapshot['terms'][i]} for i in [377, 738]],
    'records': [{'ordinal': i, 'source': rows[i - 1]} for i in evidence],
    'questions': {
        'terms:284': '现行译名行进射击的移动含义与1042机制说明冲突。依据正式说明核对技能名，避免增加移动设定。',
        'terms:739': 'The Flayed One 的被动称号含义是否被剥皮者表达为主动剥皮人？按14200百科及对话确认，保持神祇别称一致。',
        'terms:987': '完整标题Barracks Rebuilt与单词barracks现译兵营是否一致？现行营房重建完成需核对，避免同设施产生两种称谓。'
    },
    'output_protocol': '仅本批三ref的edits和entry_reviews，逐项四维checks、真实evidence_rows和source_excerpt、理由。建议修订字段，勿改正式文件；没有修订也须逐项证据。不改related_entries。'
}
folder = root / 'glossary/mechanics_revision'
folder.mkdir(parents=True, exist_ok=True)
output = folder / 'producer_task.json'
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'path': str(output), 'chars': len(output.read_text(encoding='utf-8'))}))
