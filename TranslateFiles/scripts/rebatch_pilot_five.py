"""Scheduling-only pilot replan; prove accepted records/authors remain unchanged."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, prompt, read_json, write_json

project = Path(__file__).resolve().parents[2]
flow = Workflow(project)
guide = (flow.root / 'TranslateDoc.md').read_text(encoding='utf-8-sig')
def accepted():
    with flow.db() as db:
        records = [dict(r) for r in db.execute('SELECT id,ordinal,stage,translation,exceptions FROM records WHERE stage IN (?,?) ORDER BY ordinal', ('pilot_translate', 'pilot_review'))]
        authors = [dict(r) for r in db.execute('SELECT * FROM quality_authors ORDER BY record_id,stage,instance,task_id')]
    return {'records': records, 'authors': authors}

before = accepted()
flow.pause(True)
change = flow.configure(read_json(flow.root / 'config/pilot_five_batches.json'),
                        '用户要求150条试译固定5组，保留已完成成果，取消场景碎片分批以降低消耗')
assert not change['semantic_reset']
after = accepted()
assert after == before, 'Accepted work or actual authorship changed'
prepared = flow.prepare('pilot_translate')
with flow.db() as db:
    tasks = [dict(r) for r in db.execute('SELECT id,payload FROM tasks WHERE stage=? AND revision=? AND status=?',
                                       ('pilot_translate', change['revision'], 'pending'))]
    config = flow.config(db)
rows = []
for task in tasks:
    payload = json.loads(task['payload'])
    payload.update(worker='/root/pilot_bulk/worker01', lease_token='0' * 32, attempt=1)
    system, user = prompt(payload)
    size = len(system) + len(user)
    assert size <= config['task_input_chars']
    assert not payload['context']
    rows.append({'task_id': task['id'], 'records': len(payload['records']), 'input_chars': size,
                 'ordinals': [r['ordinal'] for r in payload['records']]})
assert len(rows) <= 5
report = {**change, 'accepted_preserved': len(before['records']), 'authorship_unchanged': True,
          'pilot_total': 150, 'planned_groups': 5, 'records_per_group': 30,
          'remaining_records': sum(r['records'] for r in rows), 'new_tasks': rows,
          'input_limit_chars': config['task_input_chars'], 'no_adjacent_context': True}
write_json(flow.root / 'reports/pilot_five_batches.json', report)
(flow.root / 'TranslateDoc.md').write_text(guide + '\n\n## 用户要求的试译成本控制\n\n'
    + f"调度修订r{change['revision']}：150条固定5组，每组30条；"
    + f"保留{len(before['records'])}条已验收译文及全部真实作者身份。剩余"
    + f"{report['remaining_records']}条生成{len(rows)}个任务，独立审校同样最多5批。"
    + '场景元数据逐条保留，不附带相邻CSV。仅修订具体有问题的任务，不整体重跑试译。\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
