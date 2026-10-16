"""Parent-owned queue: lease tasks, generate prompts, accept worker result files.

Workers only read their inbox/task/prompt and atomically write independent JSON.
All state changes go through the shared workflow API, never direct SQLite writes.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, write_json, read_json

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / 'TranslateFiles'
parser = argparse.ArgumentParser()
parser.add_argument('stage')
args = parser.parse_args()
flow = Workflow(ROOT)
slots = {}
errors = []

def make_item(worker, claim):
    inbox = TF / 'tasks' / f'{worker}.inbox.json'
    prompt = flow.task_prompt(claim['task_file'])
    result = TF / 'results' / args.stage / claim['task_id'] / f'{worker}.json'
    result.parent.mkdir(parents=True, exist_ok=True)
    slot = {'status': 'work', 'stage': args.stage, 'task_id': claim['task_id'],
            'task_file': claim['task_file'], 'prompt_file': prompt['prompt_file'],
            'result_file': str(result), 'worker': worker, 'validation_error': None}
    print(f"ASSIGN {worker} {claim['task_id']} records={len(claim['payload']['records'])}", flush=True)
    return {'claim': claim, 'result': result, 'inbox': inbox, 'slot': slot, 'rejections': 0,
            'heartbeat_at': time.monotonic()}

def publish(worker, items):
    inbox = TF / 'tasks' / f'{worker}.inbox.json'
    if not items:
        write_json(inbox, {'status': 'done', 'stage': args.stage})
    else:
        write_json(inbox, {'status': 'work', 'stage': args.stage,
                          'task_id': '|'.join(i['claim']['task_id'] for i in items),
                          'tasks': [i['slot'] for i in items]})

def assign(worker, resume=False):
    items = []
    inbox = TF / 'tasks' / f'{worker}.inbox.json'
    if resume and inbox.exists():
        previous = read_json(inbox)
        if previous.get('stage') == args.stage and previous.get('status') == 'work':
            for slot in previous.get('tasks', [previous]):
                task = read_json(slot['task_file'])
                with flow.db() as db:
                    state = db.execute('SELECT status,lease_token FROM tasks WHERE id=?', (task['task_id'],)).fetchone()
                if state and state['status'] == 'done':
                    continue  # Submission may have committed before inbox rename failed.
                if not state or state['status'] != 'running' or state['lease_token'] != task['lease_token']:
                    raise ValueError('Cannot resume an invalid lease: ' + task['task_id'])
                # Accept the parent's existing leases; no recovery or duplicate claims.
                items.append(make_item(worker, {'task_id': task['task_id'], 'lease_token': task['lease_token'],
                                                 'task_file': slot['task_file'], 'payload': task}))
    char_budget = 35000 if args.stage == 'extract' else 18000
    record_budget = 600 if args.stage == 'extract' else 160
    while len(items) < 6:
        chars = sum(len(r['source']) + len(r.get('translation') or '') for i in items for r in i['claim']['payload']['records'])
        count = sum(len(i['claim']['payload']['records']) for i in items)
        if items and (chars >= char_budget or count >= record_budget):
            break
        claim = flow.claim(args.stage, worker, 'codex')
        if not claim:
            break
        items.append(make_item(worker, claim))
    publish(worker, items)
    return items

for worker in ('luna-1', 'luna-2', 'luna-3'):
    slots[worker] = assign(worker, resume=True)
last_status = 0
while any(slots.values()):
    for worker, items in list(slots.items()):
      had_items = bool(items)
      for item in list(items):
        claim = item['claim']
        if time.monotonic() - item['heartbeat_at'] > 300:
            flow.heartbeat(claim['task_id'], claim['lease_token'])
            item['heartbeat_at'] = time.monotonic()
        if not item['result'].exists():
            continue
        try:
            result = read_json(item['result'])
            accepted = flow.submit(claim['task_id'], claim['lease_token'], result)
            print(f"ACCEPT {worker} {claim['task_id']} {accepted}", flush=True)
            items.remove(item)
        except (ValueError, OSError, json.JSONDecodeError) as error:
            item['rejections'] += 1
            err = {'task_id': claim['task_id'], 'worker': worker, 'rejection': item['rejections'], 'error': str(error)}
            errors.append(err)
            rejected = item['result'].with_suffix(f'.rejected{item["rejections"]}.json')
            item['result'].replace(rejected)
            item['slot']['validation_error'] = str(error)
            item['slot']['rejected_result'] = str(rejected)
            if item['rejections'] >= 3:
                item['slot']['status'] = 'attention'
                write_json(item['inbox'], item['slot'])
                write_json(TF / 'reports' / f'dispatch_{args.stage}_errors.json', errors)
                print('ATTENTION ' + json.dumps(err, ensure_ascii=False), flush=True)
                # Leave the valid lease intact for explicit parent repair/recovery.
                raise SystemExit(2)
            publish(worker, items)
            print('REPAIR ' + json.dumps(err, ensure_ascii=False), flush=True)
      if items:
          publish(worker, items)
      elif had_items:
          slots[worker] = assign(worker)
    if time.monotonic() - last_status > 30:
        status = flow.status()
        write_json(TF / 'state' / 'dispatch_status.json', {'stage': args.stage, 'status': status})
        print('STATUS ' + json.dumps({'stage': args.stage, 'tasks': status['tasks'], 'records': status['records']}), flush=True)
        last_status = time.monotonic()
    time.sleep(1)
write_json(TF / 'reports' / f'dispatch_{args.stage}_errors.json', errors)
write_json(TF / 'state' / 'dispatch_status.json', {'stage': args.stage, 'status': flow.status()})
print('STAGE DONE ' + args.stage, flush=True)
