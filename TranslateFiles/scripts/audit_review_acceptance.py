"""Read-only audit of archived review rounds; never updates workflow state."""
import collections
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
db = sqlite3.connect((ROOT / 'state/workflow.sqlite3').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
db.execute('BEGIN')
tasks = {}
for row in db.execute('SELECT id,payload,result FROM tasks WHERE stage="review" AND result IS NOT NULL'):
    payload, result = json.loads(row['payload']), json.loads(row['result'])
    tasks[row['id']] = (payload, {r['id']: r for r in result.get('records', [])})


def category(error):
    if 'terminology mismatch' in error:
        return 'terminology_gate'
    if 'structural mismatch' in error:
        return 'structure_gate'
    if 'Unresolved blocking semantic issue' in error:
        return 'reported_blocking_semantic_issue'
    return 'review_record_contract'


rounds = []
previous_meaning = set()
examples = []
for path in sorted((ROOT / 'reports/review_rounds').glob('review_*.json')):
    report = json.loads(path.read_text(encoding='utf-8'))
    counts, diagnostics, na, changes = (collections.Counter() for _ in range(4))
    meaning_ids = set()
    meaning_unchanged = 0
    input_files = set()
    for check in report['checks']:
        if check['result'] != 'failed':
            continue
        error = check['diagnostic']
        counts[category(error)] += 1
        diagnostics[error.split('; Regression:')[0]] += 1
        counts['regression_overlap'] += bool(check.get('regressed_terms'))
        payload, items = tasks[check['task_id']]
        item = items[check['id']]
        original = next(r for r in payload['records'] if r['id'] == check['id'])
        if error.startswith('Meaning/completeness/logic'):
            meaning_ids.add(check['id'])
            for name in ('accuracy', 'completeness', 'logic'):
                if item.get('checks', {}).get(name, {}).get('status') == 'not_applicable':
                    na[name] += 1
            meaning_unchanged += item.get('translation') == original['translation']
            if len(examples) < 3:
                examples.append({'round': path.name, 'id': check['id'], 'source': original['source'],
                                 'translation': item.get('translation'), 'checks': item.get('checks')})
        if error.startswith('Invalid review change evidence'):
            for change in item.get('changes', []):
                if not isinstance(change, dict):
                    changes['not_object'] += 1
                    continue
                for label, valid in {
                    'before_not_task_translation': change.get('before') == original['translation'],
                    'after_not_full_translation': change.get('after') == item.get('translation'),
                    'invalid_category': change.get('category') in ('accuracy','completeness','terminology','tone','logic','placeholders'),
                    'invalid_severity': change.get('severity') in ('minor','major','critical'),
                    'missing_reason': isinstance(change.get('reason'), str) and bool(change['reason'].strip()),
                    'excerpt_not_record_excerpt': change.get('source_excerpt') == item.get('source_excerpt'),
                    'unchanged_translation': original['translation'] != item.get('translation'),
                }.items():
                    if not valid:
                        changes[label] += 1
        run = db.execute('SELECT input_file FROM batch_runs WHERE task_id=? AND status="submitted" LIMIT 1',
                         (check['task_id'],)).fetchone()
        if run:
            input_files.add(run['input_file'])
    conflicts = 0
    for filename in input_files:
        text = Path(filename).read_text(encoding='utf-8')
        conflicts += '无相关内容时写 not_applicable' in text
    rounds.append({'archive': path.name, 'checked': report['checked_records'], 'passed': len(report['passed_ids']),
                   'failed': report['failed_records'], 'first_failure_categories': dict(counts),
                   'diagnostics': dict(diagnostics), 'forbidden_not_applicable_dimensions': dict(na),
                   'meaning_failure_records': len(meaning_ids), 'meaning_failure_translation_unchanged': meaning_unchanged,
                   'repeated_meaning_failure_from_previous_round': len(meaning_ids & previous_meaning),
                   'invalid_change_fields_occurrences': dict(changes),
                   'failed_task_input_files': len(input_files), 'input_files_with_conflicting_instruction': conflicts})
    previous_meaning = meaning_ids
db.rollback()
db.close()
out = {'method': 'Read-only SQLite snapshot + immutable round reports and submitted handoff inputs. '
                  'Categories use first failing gate only; regression_overlap is non-exclusive. '
                  'Meaning counts include regression suffixes. No semantic correctness verdict is inferred. '
                  'Change field counts are occurrences, not unique records.',
       'rounds': rounds, 'examples': examples}
target = ROOT / 'reports/review_acceptance_audit_20261016.json'
target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for row in rounds:
    print(json.dumps(row, ensure_ascii=True))
