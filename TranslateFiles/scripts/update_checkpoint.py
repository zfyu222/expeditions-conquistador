"""Record current workflow provenance and documentation; no translation mutation."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, r'D:\StaticHanHua\Tools\localization')
from translation_workflow import Workflow, write_json, read_json
root = Path(__file__).resolve().parents[2]
tf = root / 'TranslateFiles'
flow = Workflow(root)
status = flow.status()
with flow.db() as db:
    config = flow.config(db)
    glossary = flow.meta(db, 'glossary')
    tasks = list(db.execute('SELECT id,payload FROM tasks WHERE revision=? AND stage=?', (status['revision'], 'pilot_translate')))
from translation_workflow import prompt
sizes = [(r['id'], sum(map(len, prompt(json.loads(r['payload']))))) for r in tasks]
write_json(tf / 'reports/context_lifecycle_checkpoint.json', {
    'status': status, 'glossary': glossary,
    'policy': {k: config[k] for k in ('agent_task_limit','agent_attempt_limit','task_input_chars','review_batch_records','batch_records','context_records')},
    'prepared_pilot_tasks': len(sizes), 'max_prelease_input_chars': max((n for _, n in sizes), default=0),
    'over_budget_tasks': [task for task,n in sizes if n > config['task_input_chars']],
    'legacy_dispatcher': 'codex_dispatch.py is historical only; single_task.py leases one task per actual fresh instance',
    'formal_translation_exported': (root / 'expeditions-conquistador_text_translated.csv').exists()
})
runtime = read_json(tf / 'reports/runtime_versions.json')
runtime['latest_run_files'] = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in runtime['files']}
runtime['current_update'] = 'Fresh instance per batch, no CSV neighbours; fix numeric backtracking before HimHer reflexive suffix self; historical pilot work retained as history but not approved under new protection/style.'
runtime['latest_regression'] = {'tests': 66, 'result': 'passed', 'seconds': 167.522,
    'includes': '3 pilot scheduling/semantic/sample migration regressions',
    'base_commit': '2b9d0ef', 'files': runtime['latest_run_files']}
write_json(tf / 'reports/runtime_versions.json', runtime)
path = root / 'README.md'
text = path.read_text(encoding='utf-8')
text = text.replace('当前进行全文术语整理', '术语已冻结，正在进行代表性试译')
start = text.index('- 当前状态：', text.index('## 翻译'))
end = text.index('\n- 工作流：', start)
text = text[:start] + '- 当前状态：已按最新技能恢复，冻结表含 162 条人物、951 条术语（共 1,113 条），有独立实例逐项审校证据。150 条代表性试译正在执行，尚未进行全文正文或导出正式译文。' + text[end:]
text = text.replace('当前在 `glossary/r4/` 分 25 批独立语义审校', '已在 `glossary/r4/` 完成 25 批独立语义审校，正式冻结版位于 `glossary/r4/freeze_5acab910/built/glossary_reviewed.json`')
text = text.replace('每批至多 60 条、10,000 原文字符', '每批至多 20 条、10,000 原文字符，1 条局部邻近上下文')
text = text.replace('，1 条局部邻近上下文', '；不附带 CSV 相邻记录')
text = text.replace('术语冻结后先做 150 条代表性试译', '先做 150 条代表性试译')
needle = '- 配置与记录：'
text = '\n'.join(line for line in text.split('\n') if not line.startswith('- 最新调度：'))
pos = text.index(needle, text.index('## 翻译'))
text = text[:pos] + '- 最新调度：每批新建 `fork_turns=none` 的 Luna 实例，一个实际实例最多一个不同任务，最多两次领取；同一租约最多一次局部修复。完整提示词与任务输入限制 48,000 字符，三个子代理并行；保留已完成术语成果。原长期轮询脚本只供历史追踪，当前由 `single_task.py` 单批调度。\n' + text[pos:]
text = text.replace('- 尚未翻译或回填，不代表汉化已生效。', '- 当前仅试译，尚未完成全文翻译或回填，不代表汉化已生效。')
text = '\n'.join(line for line in text.split('\n') if not line.startswith('- 变量保护修复：'))
pos = text.index('- 输出约定：', text.index('## 翻译'))
text = text[:pos] + '- 变量保护修复：`FHimHer1self` 的旧正则会回溯漏掉编号，已改为禁止数字回溯并允许完整 HimHer 编号后接 self。6 条原文共 7 次出现，通过实际模板及边界检查；第 7,372 条新任务已确认完整保护 `FHimHer1`。因保护/文体变化，r7/r8 的 95 条试译仅保留历史，新版 r9 重新进行 150 条试译，不能沿用旧批准。全文正文未启动。\n' + text[pos:]
text = '\n'.join(line for line in text.split('\n') if not line.startswith('- 最新迁移验证：'))
pos = text.index('- 输出约定：', text.index('## 翻译'))
text = text[:pos] + '- 最新迁移验证：取消 CSV 相邻文本，保留已验收 61 条试译及实例来源；仅重建剩余 89 条任务。补充调度改动保留进度、文体改动重置和样本改动重置的回归测试，完整 66 项检查通过（167.522 秒）。原文 SHA-256 与提取时一致。\n' + text[pos:]
path.write_text(text, encoding='utf-8')
(tf / 'TranslateDoc.md').write_text('''# Expeditions: Conquistador 翻译执行记录

用户已选择自定义 Codex 子代理路线，目标简体中文，默认 gpt-6-luna。主代理 Sol 调度、审查和验收，子代理生成术语、译文及语义审校结果。纯静态汉化，不涉及 BepInEx 或 XUnity。

原文 14,691 个 CSV 逻辑记录，正式源文件在项目根目录；正式译文仅由 workflow export 在全部质量门槛通过后生成。Game/ 永不写入或提交。

## 当前成果
全文术语提取 441 批完成，25 批独立审校有逐项证据。冻结表 162 人物、951 术语，共 1,113 条；版本 `r4/freeze_5acab910`，哈希 `e9f83f14f476e243b37f516128d0aaceeec549a70b4dc4b1ccf242d5c804bd2d`。旧版历史不用于绕过 quality_version=2。

当前进行 150 条代表性试译，覆盖报告见 reports/pilot_selection_plan.json。最初分为93个任务，最新修订保留已验收记录，仅准备未完成部分，数量见当前 checkpoint。任务保留场景边界，不宣称覆盖每个分支、角色或图片正文。试译完成后由不同新实例逐条六维审校，再由 Sol 阅读全部试译及证据验收，才开放全文。

## 最新生命周期
每批一个新实例（fork_turns=none），agent_task_limit=1，agent_attempt_limit=2，task_input_chars=48000。每批最多20条、10000原文字符，context_records=0；审校最多20条。不附带CSV相邻记录，提取顺序不推断剧情延续，依据已确认元数据和冻结术语。术语审校仍保留条目明确出处。程序拒绝超预算任务，不截断正文或证据。已准备试译全量预算检查见 reports/context_lifecycle_checkpoint.json。

调度迁移曾保留已验收61条试译，只重建剩余89条任务；随后发现HimHer数字在self后缀前被旧正则回溯丢失。已修复并验证全文6条/7次实际模板、6组边界样例，r9的第7372条任务完整保护FHimHer1。因保护与文体变化，旧95条试译只作历史，不沿用为新版验收；新版重新进行150条试译。普通词不得机械套技能、动态人物不得增加未确定性别，规则已加入style。

仅调度变更保留进度的修复完整66项回归通过（167.522秒），根工作区改动快照见 scripts/pilot_migration.patch。文体、样本或保护规则改变仍重置试译，未绕过独立审校或Sol验收。

single_task.py 仅由主代理 claim/submit；check 生成只读结构和术语诊断，子代理可对本批执行。不自动转交下一批，不通过别名规避身份限制。子代理只读自己的任务、生成提示词和局部筛选术语，写指定结果文件；最多一次同批局部修复，仍失败则 fail --retry 后换新实例。

## 保护与语境
按 workflow.json 保护实际变量、样式 / * $、换行与字面转义；[Check ...] 玩家提示可译。GivenName/FamilyName 等身份键不在源文本内，回填时保留。多义普通词、语言/民族形容词等必须按记录语境处理，并为命中术语的合理例外逐项说明，不强制堆字。真实错误退回子代理修订，不能用无依据的例外掩盖。

## 后续门槛
试译验收后重新执行全文 translate → 独立 review（逐条六维证据）；未开启 polish。Sol 最终阅读高风险、普通抽样、审校变动、同源多译及角色口吻组，经 approve-quality 后 export。实机状态保持 pending_repack，字体、排版、UI、对白、任务留待回填验证，不宣称游戏内已通过。

配置、术语证据与交付报告入库；state/tasks/results/source/cache/backups/logs 和凭据不入库。
''', encoding='utf-8')
print(json.dumps({'revision': status['revision'], 'pilot_tasks':len(sizes),'max_input':max((n for _,n in sizes),default=0)}, ensure_ascii=False))
