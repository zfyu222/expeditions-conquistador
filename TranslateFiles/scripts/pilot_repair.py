"""Public project repair commands: bounded human grant, ordinary leases/submit/gates.

Does not clear attempts, widen sample, approve quality, or author translations.
"""
import argparse
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, bridge, encoded, fingerprint, read_json, write_json


class ScopedRepair(Workflow):
    def prepare_repair(self, authorization, review=False):
        with self.db() as db:
            config = self.config(db)
            if db.execute('SELECT 1 FROM tasks WHERE status="running"').fetchone():
                raise ValueError('Finish in-flight work before targeted repair')
            if self.pilot_approved(db, config):
                raise ValueError('Approved pilot cannot be repaired')
            current = read_json(self.root / 'reports/pilot_quality_review.json')
            if authorization['report_hash'] != current['report_hash']:
                raise ValueError('Authorization does not bind inspected report')
            ordinals = authorization['ordinals']
            if (authorization['additional_calls'] != 2 or len(ordinals) != len(set(ordinals))
                    or not ordinals or len(ordinals) > 11
                    or authorization['human_answer'] != '允许最多追加 2 次调用：集中修订问题条目，再独立复核；不重跑 150 条'):
                raise ValueError('Invalid human-authorized scope/budget')
            rows = [r for r in self.quality_rows(db) if r['ordinal'] in ordinals]
            pilot = self.pilot_ids(db, self.quality_rows(db), config)
            if len(rows) != len(ordinals) or any(r['id'] not in pilot or r['locked'] for r in rows):
                raise ValueError('Unknown, non-pilot or locked repair record')
            ids = [r['id'] for r in rows]
            grant = self.meta(db, 'pilot_repair_grant')
            if grant is None:
                if review or any(r['stage'] != 'pilot_review' for r in rows):
                    raise ValueError('Repair requires reviewed initial results')
                grant = {'authorization': authorization, 'record_ids': ids,
                         'baseline_spent': self.pilot_spent(db), 'additional_calls': 2, 'task_ids': [],
                         'untouched_hash': fingerprint([r for r in self.quality_rows(db) if r['id'] not in ids])}
                self.put(db, 'pilot_repair_grant', grant)
                self.event(db, 'human_authorized_pilot_repair', grant)
            if grant['authorization'] != authorization or grant['record_ids'] != ids:
                raise ValueError('Cannot change existing grant or refresh budget')
            stage = 'pilot_review' if review else 'pilot_translate'
            existing = [db.execute('SELECT * FROM tasks WHERE id=?', (i,)).fetchone()
                        for i in grant['task_ids']]
            same = next((t for t in existing if t['stage'] == stage), None)
            if same:
                return {'task_id': same['id'], 'existing': True}
            if review and (len(existing) != 1 or existing[0]['status'] != 'done'
                           or any(r['stage'] != 'pilot_translate' for r in rows)):
                raise ValueError('Submit repair producer before independent review')
            if self.pilot_spent(db) + (1 if review else 2) > grant['baseline_spent'] + 2:
                raise ValueError('Two-call repair grant exhausted')
            revision = self.meta(db, 'revision')
            task_id = f'{stage}-r{revision}-repair-{uuid.uuid4().hex[:8]}'
            glossary = self.glossary(db)
            rules = self.rules(db, config)
            payload = {'protocol': 1, 'stage': stage, 'revision': revision, 'task_id': task_id,
                       'source_hash': self.meta(db, 'source_hash'), 'config_hash': fingerprint(config),
                       'language': {'source': config['source_language'], 'target': config['target_language']},
                       'style': config['style'], 'game_background': config.get('game_background', ''),
                       'glossary_version': self.meta(db, 'glossary'), 'context': [], 'records': [],
                       'terms': bridge.matched_terms(glossary, [t for r in rows for t in
                                  (r['source'], r['metadata'].get('speaker', ''))], config),
                       'revision_request': (self.root / 'reports/pilot_sol_audit_20261015.md').read_text(encoding='utf-8-sig'),
                       'human_authorized_repair': authorization}
            for row in rows:
                source, mapping = (row['source'], []) if review else bridge.protect(row['source'], row['id'], rules)
                payload['records'].append({'id': row['id'], 'ordinal': row['ordinal'], 'source': source,
                    'translation': row['translation'], 'locked': bool(row['locked']), 'metadata': row['metadata'],
                    'exceptions': json.loads(row['exceptions']), 'protection': mapping})
            signature = fingerprint(payload)
            payload['input_hash'] = signature
            db.execute('INSERT INTO tasks(id,stage,revision,ids,payload,input_hash,backend,status) VALUES (?,?,?,?,?,?,?,?)',
                       (task_id, stage, revision, encoded(ids), encoded(payload), signature, 'codex', 'pending'))
            grant['task_ids'].append(task_id)
            self.put(db, 'pilot_repair_grant', grant)
            approvals = self.meta(db, 'quality_approvals', {})
            approvals.pop('pilot', None)
            self.put(db, 'quality_approvals', approvals)
            self.event(db, 'prepare_scoped_pilot_repair', {'task': task_id, 'records': ids, 'review': review})
            return {'task_id': task_id, 'records': len(ids), 'additional_call_limit': 2}

    def verify_preservation(self):
        with self.db() as db:
            grant = self.meta(db, 'pilot_repair_grant')
            rows = self.quality_rows(db)
            same = fingerprint([r for r in rows if r['id'] not in grant['record_ids']]) == grant['untouched_hash']
            tasks = [dict(db.execute('SELECT id,stage,status FROM tasks WHERE id=?', (i,)).fetchone())
                     for i in grant['task_ids']]
            if not same:
                raise ValueError('Untouched records changed')
            out = {'untouched_records_unchanged': same, 'repair_record_count': len(grant['record_ids']),
                   'additional_claims_used': self.pilot_spent(db) - grant['baseline_spent'], 'additional_call_limit': 2,
                   'tasks': tasks, 'source_sha256': self.meta(db, 'source_hash')}
            write_json(self.root / 'reports/pilot_repair_preservation.json', out)
            return out

    def adopt_accepted_pilot(self):
        """Reuse accepted text as production draft; full production review stays mandatory."""
        with self.db() as db:
            config = self.config(db)
            if not self.pilot_approved(db, config):
                raise ValueError('Current Sol pilot approval required for reuse')
            if db.execute('SELECT 1 FROM tasks WHERE status="running"').fetchone():
                raise ValueError('Cannot seed production during in-flight work')
            receipt = self.meta(db, 'quality_approvals', {})['pilot']
            folder = self.root / ('reports/accepted/pilot_'+receipt['report_hash'][:16])
            report = read_json(folder / 'report.json')
            if report['source_sha256'] != self.meta(db, 'source_hash') or report['glossary'] != self.meta(db, 'glossary'):
                raise ValueError('Source or glossary changed since pilot acceptance')
            selected = self.pilot_ids(db, self.quality_rows(db), config)
            examples = report['records_to_check']
            if {r['id'] for r in examples} != selected or len(examples) != len(selected):
                raise ValueError('Accepted report does not exactly cover pilot sample')
            for item in examples:
                row = db.execute('SELECT * FROM records WHERE id=?', (item['id'],)).fetchone()
                if row['source'] != item['source'] or row['stage'] not in ('source','translate') or row['locked']:
                    raise ValueError('Cannot overwrite changed, reviewed or locked production text')
                if row['stage'] == 'translate' and row['translation'] != item['translation']:
                    raise ValueError('Cannot replace an existing production draft')
                exceptions = item['review'].get('exceptions')
                if exceptions is None:
                    # Compact pilot pass retained the task's previously accepted exceptions.
                    review_task = db.execute('SELECT payload FROM tasks WHERE id=?', (item['review']['task_id'],)).fetchone()
                    original = next(r for r in json.loads(review_task['payload'])['records'] if r['id']==item['id'])
                    exceptions = original.get('exceptions', [])
                db.execute('UPDATE records SET translation=?,stage="translate",exceptions=? WHERE id=?',
                           (item['translation'], encoded(exceptions), item['id']))
                # Preserve actual producer/corrector origins, not a fictitious Sol writer.
                origins = db.execute('SELECT instance,task_id FROM quality_authors WHERE record_id=? '
                                     'AND stage IN ("pilot_translate","pilot_review")', (item['id'],)).fetchall()
                if not origins:
                    raise ValueError('Missing accepted pilot authorship')
                for origin in origins:
                    db.execute('INSERT OR IGNORE INTO quality_authors VALUES (?,?,?,?)',
                               (item['id'], 'translate', origin['instance'], origin['task_id']))
            result = {'pilot_report_hash': report['report_hash'], 'reused_records': len(examples),
                      'production_stage': 'translate', 'full_production_review_required': True,
                      'additional_model_tasks': 0, 'source_sha256': report['source_sha256']}
            write_json(self.root / 'reports/pilot_production_reuse.json', result)
            self.event(db, 'adopt_accepted_pilot_as_production_draft', result)
            return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['prepare', 'prepare-review', 'verify', 'adopt'])
    a = p.parse_args()
    flow = ScopedRepair(Path(__file__).resolve().parents[2])
    if a.command == 'verify':
        result = flow.verify_preservation()
    elif a.command == 'adopt':
        result = flow.adopt_accepted_pilot()
    else:
        result = flow.prepare_repair(read_json(flow.root / 'config/pilot_repair_authorization.json'), a.command == 'prepare-review')
    print(json.dumps(result, ensure_ascii=False))
