"""File-driven supplemental captions; preserves the completed 14,691-row workflow.

Only new image captions are processed. The approved main pilot is not repeated.
Separate authors/reviewers and hash-bound per-record six-dimension evidence are required.
"""
import argparse
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
ROOT=PROJECT/'TranslateFiles/tutorial_supplement'
DIMS={'accuracy','completeness','terminology','tone','logic','placeholders'}
def read(p): return json.loads(p.read_text('utf-8-sig'))
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def prepare():
    assert not (ROOT/'source.json').exists(), 'Existing supplement must be resumed, not reset'
    ocr=read(PROJECT/'Repack/reports/tutorial_ocr.json')
    entries=[]
    for r in ocr:
        lines=[x for x in r['lines'] if x['y']>=420]
        assert lines,r['name']
        entries.append({'id':'T%03d'%(len(entries)+1),'name':r['name'],'source':'\n'.join(x['text'] for x in lines),
                        'image':r['image'],'ocr_lines':lines})
    entries.append({'id':'T048','name':'Tutorials','source':'Tutorials','image':'Right-hand tutorial header texture'})
    assert len(entries)==48
    glossary=read(PROJECT/'TranslateFiles/glossary/mechanics_revision/built/glossary_reviewed.json')
    write(ROOT/'source.json',entries)
    with (ROOT/'tutorial_captions_text.csv').open('w',encoding='utf-8-sig',newline='') as f:
        csv.writer(f).writerows([[r['source']] for r in entries])
    for batch in range(2):
        records=entries[batch*24:(batch+1)*24]
        joined=re.sub(r'\s+','', ' '.join(r['source'] for r in records)).lower()
        selected=[t for t in glossary['terms'] if re.sub(r'\s+','',str(t.get('src',t.get('source','')))).lower() in joined]
        data={'task':'tutorial_caption_translate','batch':batch+1,'records':records,'terms':selected,
            'instructions':'翻译新增教程图片说明为简体中文。OCR常把英文单词粘在一起，按图片语境分词；同一行或相邻行可能来自左右两栏，须保留各自指代。可必要时查看指定PNG（透明PNG的RGB背景可能误显，实际字形在alpha中）；遇不清楚处写issues，不编造。只翻译底部说明，保留Arabic数字/快捷键/原意，段落可以为中文排版自然合并。不改原有CSV、术语及游戏文件。输出JSON {author:实际代理ID, records:[{id,translation,issues:[]}]}，不自审、不运行检查；中文需直接可作游戏教程说明。标题Tutorials译为简短中文。'}
        data['input_hash']=digest(data)
        write(ROOT/('tasks/translate_%02d.json'%(batch+1)),data)
    print('prepared 48 new captions in 2 batches; main workflow unchanged')

def prepare_review():
    source=read(ROOT/'source.json'); translations={}; authors={}
    for batch in (1,2):
        task=read(ROOT/('tasks/translate_%02d.json'%batch)); result=read(ROOT/('results/translate_%02d.json'%batch))
        assert result.get('author') and {r['id'] for r in result['records']}=={r['id'] for r in task['records']}
        assert len(result['records'])==24
        for r in result['records']:
            assert isinstance(r.get('translation'),str) and r['translation'].strip()
            assert not r.get('issues'),r
            translations[r['id']]=r['translation'];authors[r['id']]=result['author']
    for batch in (1,2):
        task=read(ROOT/('tasks/translate_%02d.json'%batch))
        records=[{**{k:v for k,v in r.items() if k!='ocr_lines'},'translation':translations[r['id']],'author':authors[r['id']]} for r in task['records']]
        terms=[{'source':t['source'],'translation':t['recommended_translation']} for t in task['terms']]
        data={'task':'independent_tutorial_review','batch':batch,'records':records,'terms':terms,
              'instructions':'独立逐条审校新增图片说明，不接触14,691条主译文。核对含义/完整性/术语/文体/逻辑/数字快捷键。OCR英文粘连和左右栏应按语义正确读；疑难查看图片或报issues。输出 {reviewer:实际代理ID,records:[{id,translation,source_excerpt,reason,checks:{accuracy:{status:pass/corrected,evidence:具体依据},completeness:{...},terminology:{...},tone:{...},logic:{...},placeholders:{...}},issues:[]}]}，可必要修正，准确自然即通过，不因同义偏好返工。不得自审（reviewer不能等于任一author）。所有数字保留阿拉伯数字；标题不添加新内容。'}
        data['input_hash']=digest(data)
        write(ROOT/('tasks/review_%02d.json'%batch),data)
    print('prepared 2 independent review batches')

def finish():
    source=read(ROOT/'source.json'); byid={r['id']:r for r in source}; accepted={}; provenance=[]
    for batch in (1,2):
        task=read(ROOT/('tasks/review_%02d.json'%batch)); result=read(ROOT/('results/review_%02d.json'%batch))
        assert result.get('reviewer') and result['reviewer'] not in {r['author'] for r in task['records']}
        assert len(result['records'])==24 and {r['id'] for r in result['records']}=={r['id'] for r in task['records']}
        for r in result['records']:
            original=byid[r['id']]['source']; translated=r.get('translation')
            assert isinstance(translated,str) and translated.strip() and not r.get('issues'),r['id']
            assert r.get('source_excerpt') and r['source_excerpt'] in original
            assert r.get('reason') and set(r['checks'])==DIMS
            for dim,c in r['checks'].items():
                assert c.get('status') in ('pass','corrected','not_applicable') and c.get('evidence'),(r['id'],dim)
                if dim in ('accuracy','completeness','logic'): assert c['status']!='not_applicable'
            numeric_source=re.sub(r'\bthree\b','3',original,flags=re.I)
            numeric_source=re.sub(r'one(?=point|unit)','1',numeric_source,flags=re.I)
            assert collections.Counter(re.findall(r'\d+',numeric_source))==collections.Counter(re.findall(r'\d+',translated)),r['id']+' numeric mismatch'
            for key in ('Alt','BEGIN BATTLE'):
                if key=='Alt' and key in original: assert key in translated,r['id']
            accepted[r['id']]=translated
            author=next(x['author'] for x in task['records'] if x['id']==r['id'])
            provenance.append({'id':r['id'],'author':author,'reviewer':result['reviewer'],'review_hash':digest(r),
                'source_excerpt':r['source_excerpt'],'reason':r['reason'],'checks':r['checks'],
                'translation_sha256':hashlib.sha256(translated.encode()).hexdigest()})
    output=[{**r,'translation':accepted[r['id']]} for r in source]
    write(ROOT/'tutorial_captions_reviewed.json',output)
    with (ROOT/'tutorial_captions_translated.csv').open('w',encoding='utf-8-sig',newline='') as f:
        csv.writer(f).writerows([[r['translation']] for r in output])
    write(ROOT/'acceptance.json',{'status':'passed','new_records':48,'source_hash':digest(source),'output_hash':digest(output),'provenance':provenance,'scope':'New tutorial captions only; original approved pilot and all 14691 translations preserved.'})
    print('48 supplemental captions independently reviewed and exported')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','prepare-review','finish']);a=p.parse_args()
    {'prepare':prepare,'prepare-review':prepare_review,'finish':finish}[a.command]()
