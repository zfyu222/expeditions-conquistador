"""Update only the execution-status paragraph from the factual saved report."""
import json
import re
from pathlib import Path

project = Path(__file__).resolve().parents[2]
report = json.loads((project / 'TranslateFiles/reports/body_execution_progress.json').read_text(encoding='utf-8-sig'))
counts = report['records']
drafts = counts.get('translate',0)
remaining = counts.get('source',0)
reviews = counts.get('review',0) + counts.get('final_review',0)
done = sum(t['n'] for t in report['production_tasks'] if t['stage']=='translate' and t['status']=='done')
line = (f'- 当前状态：冻结表含 162 条人物、951 条术语（共 1,113 条）。150 条试译已完成独立审校及 Sol 验收并复用于正文，不重跑试译。'
        f'正文翻译已启动，当前保存 {drafts:,} 条正文草稿，剩余 {remaining:,} 条待翻译；已完成 {done} 个正文翻译任务。'
        f'全文独立审校完成 {reviews:,} 条；草稿数不代表语义验收。正式译文CSV尚未导出。'
        '试译批准哈希 `ce4c4bbec230762af6f16decb9a469bd61453eb72450a9b098bd44a1b7268a6e`；'
        '最新执行状态见 `TranslateFiles/reports/body_execution_progress.json`，试译复用来源见 `pilot_production_reuse.json`。')
path = project / 'README.md'
text = path.read_text(encoding='utf-8-sig')
text = re.sub(r'^> 项目状态：.*$', '> 项目状态：文本提取完成（14,691 条），150 条试译已批准并复用，正在执行正文翻译。以用户清理后的纯净 Steam 安装目录为基准。', text, count=1, flags=re.MULTILINE)
text, n = re.subn(r'^- 当前状态：.*$', lambda _: line, text, count=1, flags=re.MULTILINE)
assert n == 1
text = text.replace('- 当前仅试译，尚未完成全文翻译或回填，不代表汉化已生效。',
                    '- 已进入正文翻译；全量独立审校、正式译文导出及回填尚未完成，不代表汉化已生效。')
path.write_text(text, encoding='utf-8')
print(f'Updated README: {drafts} drafts, {remaining} source records, {reviews} fully reviewed.')
