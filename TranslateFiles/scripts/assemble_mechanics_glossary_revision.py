"""Merge independently authored revisions, preserving unchanged reviewed entries."""
import hashlib
import json
from pathlib import Path

project = Path(__file__).resolve().parents[2]
root = project / 'TranslateFiles'
folder = root / 'glossary/mechanics_revision'
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

task = read(folder / 'producer_task.json')
producer = read(folder / 'producer_result.json')
review = read(folder / 'review_result.json')
expected = {e['ref'] for e in task['entries']}
reviewer = '/root/glossary_mechanics_fix_review'
assert producer['producer_instance'] == task['producer_instance'] != reviewer
assert review['reviewer_instance'] == reviewer
assert set(review['reviewed_refs']) == expected
assert set(review['review_instances']) == expected
assert all(v == reviewer for v in review['review_instances'].values())
assert {r['ref'] for r in review['entry_reviews']} == expected
assert {f"{e['table']}:{e['index']}" for e in review['edits']} == expected

snapshot = read(root / 'glossary/r4/glossary_original.json')
decisions = read(root / 'glossary/r4/freeze_5acab910/glossary_decisions.json')
provided = {r['ordinal'] for r in task['records']}
for index, additions in [(284, [1042]), (987, [6468, 6552])]:
    assert set(additions) <= provided
    row = snapshot['terms'][index]
    row['evidence_rows'] = sorted(set(row['evidence_rows']) | set(additions))
snapshot_path = folder / 'glossary_original.json'
save(snapshot_path, snapshot)
decisions['snapshot_sha256'] = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
by_ref = {r['ref']: r for r in decisions['entry_reviews']}
by_ref.update({r['ref']: r for r in review['entry_reviews']})
decisions['entry_reviews'] = [by_ref[r['ref']] for r in decisions['entry_reviews']]
decisions['review_instances'].update(review['review_instances'])
for edit in review['edits']:
    prior = next((e for e in decisions['edits'] if (e['table'], e['index']) == (edit['table'], edit['index'])), None)
    if prior is None:
        decisions['edits'].append(edit)
    else:
        prior['patch'].update(edit['patch'])
        prior['reason'] = edit['reason']
        prior['evidence_rows'] = edit['evidence_rows']
decisions['review_summary'] += '\nMechanics revision: three independently revised refs; unchanged entry reviews and actual identities retained verbatim. Additional cited source records are included in the snapshot.'
save(folder / 'glossary_decisions.json', decisions)
save(folder / 'revision_provenance.json', {
    'producer_instance': producer['producer_instance'],
    'reviewer_instance': reviewer,
    'changed_refs': sorted(expected),
    'retained_review_count': len(decisions['entry_reviews']) - len(expected),
    'source_sha256': decisions['source_sha256'],
    'snapshot_sha256': decisions['snapshot_sha256'],
    'added_evidence_rows': {'terms:284': [1042], 'terms:987': [6468, 6552]},
})
print(json.dumps({'snapshot': str(snapshot_path), 'decisions': str(folder / 'glossary_decisions.json'),
                  'retained_reviews': len(decisions['entry_reviews']) - len(expected), 'new_reviews': len(expected)}))
