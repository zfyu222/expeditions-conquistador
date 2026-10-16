"""Read-only compact report view; preserve all source and review evidence."""
import json
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'reports/pilot_quality_review.json'
d = json.loads(p.read_text(encoding='utf-8-sig'))
for r in d['records_to_check'][int(sys.argv[1]):int(sys.argv[2])]:
    v = r['review']
    # Exact duplicate evidence is shown once with every associated dimension/status.
    evidence = {}
    for dimension, check in v.get('checks', {}).items():
        evidence.setdefault(check['evidence'], []).append([dimension, check['status']])
    print(json.dumps({'id': r['id'], 'ordinal': r['ordinal'], 'source': r['source'],
                     'translation': r['translation'],
                     'metadata': {k: r['metadata'].get(k) for k in ('speaker', 'scene', 'text_type')},
                     'review': {k: v.get(k) for k in ('instance', 'reviewed', 'verdict', 'reason', 'source_excerpt', 'exceptions', 'issues')},
                     'checks': [{'dimensions': names, 'evidence': text} for text, names in evidence.items()],
                     'changes': [{k: c.get(k) for k in ('category', 'severity', 'reason', 'source_excerpt')} for c in v.get('changes', [])]}, ensure_ascii=False))
