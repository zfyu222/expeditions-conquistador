"""Parent-only single-batch lease and submission helper; never redispatch an instance."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, read_json, write_json, bridge
from diagnostic_restore import diagnostic_restore
root = Path(__file__).resolve().parents[2]
flow = Workflow(root)
p = argparse.ArgumentParser()
p.add_argument('action', choices=['claim', 'submit', 'check'])
p.add_argument('--stage')
p.add_argument('--worker')
p.add_argument('--assignment')
a = p.parse_args()
if a.action == 'claim':
    claim = flow.claim(a.stage, a.worker, 'codex')
    if not claim:
        print('null')
        sys.exit(0)
    prompt = flow.task_prompt(claim['task_file'])
    result = root / 'TranslateFiles/results' / a.stage / claim['task_id'] / (claim['lease_token'] + '.json')
    result.parent.mkdir(parents=True, exist_ok=True)
    assignment = {k: v for k, v in claim.items() if k != 'payload'}
    assignment.update(prompt_file=prompt['prompt_file'], result_file=str(result), worker=a.worker,
                      record_count=len(claim['payload']['records']))
    attention = root / 'TranslateFiles/reports/pilot_review_attention.json'
    if a.stage == 'pilot_review' and attention.exists():
        ordinals = {r['ordinal'] for r in claim['payload']['records']}
        notes = [n for n in read_json(attention)['records'] if ordinals.intersection(n.get('ordinals', [n.get('ordinal')]))]
        if notes:
            note_file = Path(claim['task_file']).with_suffix('.parent_notes.json')
            write_json(note_file, {'scope': 'Sol concerns to independently assess; do not replace source or auto-approve', 'records': notes})
            assignment['parent_notes_file'] = str(note_file)
    out = Path(claim['task_file']).with_suffix('.assignment.json')
    assignment['assignment_file'] = str(out)
    write_json(out, assignment)
    pointer = root / 'TranslateFiles/tasks' / (Path(a.worker).name + '.current.json')
    write_json(pointer, assignment)
    print(json.dumps({'task_id': claim['task_id'], 'assignment_file': str(pointer), 'record_count': assignment['record_count'], 'context_policy': claim['context_policy']}, ensure_ascii=False))
elif a.action == 'check':
    assignment_path = Path(a.assignment) if a.assignment else root / 'TranslateFiles/tasks' / (Path(a.worker).name + '.current.json')
    assignment = read_json(assignment_path)
    task = read_json(assignment['task_file'])
    result = read_json(assignment['result_file'])
    if (task['stage'] in ('review', 'final_review')
            or task['stage'] == 'translate' and (not task.get('strict_translation') or task.get('draft_scan_key'))):
        # Historical controllers may still call check. Keep it a cheap persistence
        # check; quality findings are collected only after all drafts are saved.
        diagnostics = []
        rows = result.get('records')
        expected = {r['id'] for r in task['records']}
        if result.get('task_id') != task['task_id'] or result.get('input_hash') != task['input_hash']:
            diagnostics.append({'scope': 'batch', 'issue': 'task_id/input_hash mismatch'})
        if (not isinstance(rows, list) or any(not isinstance(r, dict) or not isinstance(r.get('id'), str)
                                              or not isinstance(r.get('translation'), str) for r in rows)):
            diagnostics.append({'scope': 'batch', 'issue': 'records require text IDs and translations'})
        elif len(rows) != len(expected) or {r['id'] for r in rows} != expected:
            diagnostics.append({'scope': 'batch', 'issue': 'missing, duplicate or unrelated IDs'})
        path = assignment_path.with_suffix('.diagnostics.json')
        write_json(path, diagnostics)
        print(json.dumps({'diagnostics_file': str(path), 'failures': len(diagnostics),
                          'quality': 'deferred_to_round_check' if task.get('draft_scan_key') or task['stage'] in ('review', 'final_review') else 'deferred_to_full_draft_scan'}, ensure_ascii=False))
        sys.exit(0)
    with flow.db() as db:
        config = flow.config(db)
        analysis = flow.glossary(db)
        rules = flow.rules(db, config)
        sources = {item['id']: db.execute('SELECT source FROM records WHERE id=?', (item['id'],)).fetchone()['source']
                   for item in result['records']}
    # Validation is read-only; release the transaction before expensive term matching.
    diagnostics = []
    for item in result['records']:
        row = {'source': sources[item['id']]}
        protected = next(r for r in task['records'] if r['id'] == item['id'])
        value = item.get('translation', protected.get('translation'))
        if not isinstance(value, str):
            raise ValueError('Missing translation in result and task')
        translation, protection_issues = diagnostic_restore(value, protected['protection']) if task['stage'] in ('translate','pilot_translate') else (value, [])
        terms = bridge.matched_terms(analysis, [row['source']], config)
        exceptions = bridge.normalize_exception_sources(
            item.get('exceptions', protected.get('exceptions', [])), terms, config['case_sensitive'])
        exempt = {e['source'] for e in exceptions}
        allowed_sources = {t['src'] for t in terms}
        unrelated = [{'source': source, 'case_matches': [s for s in allowed_sources if s.casefold() == source.casefold()]}
                     for source in exempt if source not in allowed_sources]
        missing = [t for t in terms if not bridge.helper().is_keep_original_translation(t['dst']) and t['src'] not in exempt and t['dst'] not in translation]
        structure = bridge.structural_issues(row['source'], translation, rules)
        if missing or structure or unrelated or protection_issues:
            diagnostics.append({'id': item['id'], 'missing_terms': missing, 'structural_issues': structure,
                                'unrelated_exceptions': unrelated, 'protection_issues': protection_issues})
    path = assignment_path.with_suffix('.diagnostics.json')
    write_json(path, diagnostics)
    print(json.dumps({'diagnostics_file': str(path), 'failures': len(diagnostics)}, ensure_ascii=False))
else:
    assignment_path = Path(a.assignment) if a.assignment else root / 'TranslateFiles/tasks' / (Path(a.worker).name + '.current.json')
    assignment = read_json(assignment_path)
    print(json.dumps(flow.submit(assignment['task_id'], assignment['lease_token'], read_json(assignment['result_file'])), ensure_ascii=False))
