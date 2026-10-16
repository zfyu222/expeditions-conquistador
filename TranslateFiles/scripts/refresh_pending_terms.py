"""Public repair of unleased input packages, preserving IDs, attempts and drafts."""
import json
import sys
from pathlib import Path
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, bridge, encoded, fingerprint, write_json

class RefreshPendingTerms(Workflow):
    def refresh(self):
        with self.db() as db:
            config=self.config(db)
            if not self.meta(db,'paused') or db.execute('SELECT 1 FROM tasks WHERE status="running"').fetchone():
                raise ValueError('Pause and finish/fail all live tasks before refreshing unleased packages')
            glossary=self.glossary(db)
            changed=[]
            tasks=db.execute('SELECT * FROM tasks WHERE stage="translate" AND revision=? AND status="pending"',
                             (self.meta(db,'revision'),)).fetchall()
            for task in tasks:
                payload=json.loads(task['payload'])
                texts=[]
                for item in payload['records']:
                    row=db.execute('SELECT source FROM records WHERE id=?',(item['id'],)).fetchone()
                    texts.extend([row['source'],item['metadata'].get('speaker','')])
                terms=bridge.matched_terms(glossary,texts,config)
                if terms==payload['terms']:
                    continue
                old=payload['input_hash']
                payload['terms']=terms
                payload.pop('input_hash',None)
                signature=fingerprint(payload)
                payload['input_hash']=signature
                db.execute('UPDATE tasks SET payload=?,input_hash=?,lease_token=NULL,lease_until=NULL WHERE id=?',
                           (encoded(payload),signature,task['id']))
                changed.append({'task_id':task['id'],'attempts_preserved':task['attempt'],'old_input_hash':old,'new_input_hash':signature})
            report={'reason':'冻结表的每条译名保持权威，禁止AINiee自动词族合并覆盖；只刷新未领取任务包',
                    'revision':self.meta(db,'revision'),'changed_tasks':changed,'source_sha256':self.meta(db,'source_hash'),
                    'glossary':self.meta(db,'glossary'),'saved_records_unchanged':True,
                    'attempts_not_reset':True,'pilot_not_reopened':True}
            self.event(db,'refresh_unleased_frozen_terms',report)
            write_json(self.root/'reports/frozen_matcher_refresh.json',report)
            return {'changed_pending_tasks':len(changed),'attempts_reset':False,'records_reset':False}

if __name__=='__main__':
    f=RefreshPendingTerms(Path(__file__).resolve().parents[2])
    print(json.dumps(f.refresh(),ensure_ascii=False))
