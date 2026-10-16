# Expeditions: Conquistador 汉化项目

> 项目状态：14,691条正式翻译、48条新增教程说明、旧存档兼容修复及最终复测均已完成；正式 v1.0 ZIP 已通过校验并发布至GitHub；百度网盘镜像因MCP目录创建错误暂未完成。Steam Windows Build 1752467 / 游戏1.6.6.1。

## 游戏信息
- 原名：Expeditions: Conquistador
- 中文名：远征：征服者（本项目暂译名，非官方中文名）
- 开发商：Logic Artists
- 发行商：THQ Nordic（当前 Steam 商店标示）
- 发行平台：Steam；商店列出 Windows、macOS、Linux，本项目针对 Windows Steam 版
- 发售日期：2013-05-30
- 引擎：Unity 4.3.2f1，Mono / .NET 托管程序集；初始化时本地运行日志记载该引擎版本，目录存在 `Managed/` 和 `Mono/`
- 进程架构：x86（初始化时本地运行日志记载）
- 翻译源语言：英语；Steam 本地安装配置为 `english`
- 官方支持语言：英语、西班牙语（西班牙）、意大利语、德语、俄语；商店未列出中文
- 本地 Steam Build ID：1752467（来自 `steamapps/appmanifest_237430.acf`，不等同于游戏内部版本号）
- 游戏内部版本：1.6.6.1（`level0` 的 `VersionLabel`，pathID 186）；语言 XML 版本：1.6
- 安装目录：`D:\Program Files (x86)\Steam\steamapps\common\Expeditions Conquistador`
- 游戏链接：`Game/` 为指向上述目录的 junction，不复制游戏文件，不纳入 Git
- 网页资料：[Steam 官方商店](https://store.steampowered.com/app/237430/?l=english)（检索日期：2026-10-13）

## 游戏简介

游戏以十六世纪西班牙远征美洲为背景，结合回合制战术战斗、队伍培养、资源管理和剧情选择。玩家招募具有不同性格与立场的队员，在探索中应对生存困难，并通过外交或战斗影响故事走向。资料来源：[Steam 官方商店](https://store.steampowered.com/app/237430/?l=english)。

## 汉化目标
- 范围：以剧情、对话、任务及 UI 等可提取的玩家可见文本为目标，实际覆盖范围在提取后确认
- 目标语言：简体中文

## 技术栈
| 环节 | 工具 | 版本 |
|------|------|------|
| 初始化 | `start-translate` / `init_game_project.py` / Git | 工作区现有脚本 |
| 游戏运行环境 | Unity / Mono | Unity 4.3.2f1；x86 |
| 提取 | UnityPy + TypeTreeGeneratorAPI；dnSpy.Console；Python | UnityPy 1.25.4；TypeTreeGeneratorAPI 0.0.10；dnSpy v6.1.8+2b6dcfaf；Python 3.12 |
| 翻译 | translation_workflow.py 自定义工作流 / Codex 子代理；Sol 最终验收 | revision 13 / quality_version 2；Luna 常规任务；全文独立审校和导出校验通过 |
| 回填 | UnityPy；dnlib 静态 IL 改写；Noto SC 字体子集 | UnityPy 1.25.4；FontTools 4.63；Unity 4.3.2f1 |
| 发布 | `game-release-patch`；xdelta；自包含差分安装器 | xdelta 3.2.2；补丁 v1.0 |

## 文本提取

- 正式原文：`expeditions-conquistador_text.csv`，UTF-8 BOM、单列、无表头；共 **14,691 条**，约 231,318 个英文词（含重复），11,020 条不同文本。
- 每个源位置对应一个 CSV 记录，不去重，保留空白、标点和格式符。194 条原文含换行，使用标准 CSV 引号保存；必须按 CSV 记录读取，不能按物理行切割。
- 来源映射：`Analysis/text_mapping.json`，记录 CSV 行号、资源文件、pathID、XML XPath/字段路径、事件及说话人上下文；DLL 文本记录类型、方法 token 与反编译位置。
- 校验报告：`Analysis/extraction_report.json`；资源清单：`Analysis/textasset_inventory.json`；输入哈希：`Analysis/source_hashes.json`。

| 范围 | 来源（相对游戏 Data 目录） | pathID / 类型 | CSV 记录数 |
|------|------|------|------|
| UI、提示、技能、物品等 | `sharedassets0.assets`，`GUI-en` | 16 | 1,773 |
| 第一章（Hispaniola） | `sharedassets1.assets`，`Level0` | 772 | 2,912 |
| 第二章（Yucatan） | `sharedassets1.assets`，`Level1` | 793 | 6,967 |
| 随机事件 | `sharedassets1.assets`，`RandomEvents` | 781 | 2,502 |
| 百科标题与正文 | `sharedassets1.assets`，`Codex` | 796 | 48 |
| 地图地点、标记、多人地图标题 | 场景与资源中的 MonoBehaviour | EventInfo / EventEnemy / MarkerInfo / HostGUI | 321 |
| 英语教程分类与标题 | `level2` / `level3` 中的 MonoBehaviour | TutorialController | 134 |
| 人工确认的硬编码 UI | `Managed/Assembly-CSharp.dll` | 记录方法 token；仅修改对应显示位置 | 34 |

### 可复现命令与关键步骤

在项目目录执行：

```powershell
python -m pip install UnityPy==1.25.4 TypeTreeGeneratorAPI==0.0.10
& D:\StaticHanHua\Tools\dnSpy-net-win64\bin\dnSpy.Console.exe '.\Game\Expeditions Conquistador_Data\Managed\Assembly-CSharp.dll' -o '.\Analysis\decompiled' --no-resources --no-color
python -X utf8 .\Analysis\scan_assets.py
python -X utf8 .\Analysis\scan_mono.py
python -X utf8 .\Analysis\extract_text.py
```

1. AssetRipper-CLI `inspect` 确认 Unity 4.3.2f1 / Mono。UABEA exe 在管道下无输出；改用 `dotnet UABEAvalonia.dll list` 后报 UTF-8 解码缓冲区错误。AssetRipper 的 `narrative` 配置选择了 0 个导出集合，未取得文本；最终改用 UnityPy 的只读资源解析。
2. 扫描 171 个 Unity 文件，导出 167 个 TextAsset。按实际内容、语言和资源定位选取上述五个正式英语 XML，不混入 Demo、测试地图、其他语言或事件脚本数据。
3. 用 dnSpy 读取 `LanguageHandler`、`EventInfoParser`、`DialogGUI` 等加载/显示逻辑，确认可翻译字段。仅提取事件名、叙述、对话、选项、任务标题/描述、人物 Bio 和百科；条件表达式、事件键、跳转、坐标、枚举、战斗配置不进入原文。
4. 用托管 DLL 生成 MonoBehaviour 类型结构，并用 Unity 4 原生组件头修正 `m_Enabled` 对齐；提取字段采用白名单。462 个组件存在类型结构解码错误，已记录类型及位置于 `Analysis/mono_errors.json`，主要涉及后处理、动画曲线、寻路等；不据此宣称所有组件均完整解析。
5. CSV 全部记录与映射中的源字段逐项一致、无空白记录、源位置唯一；再次核对 171 个输入文件的 SHA-256，确认提取未修改游戏资源。

- CSV SHA-256：`8ba04dc104e24e2b6c7a10a33f323a501524b4ceba7d7b5f4a9d9e72dcc9c96e`
- 原始 `Assembly-CSharp.dll` SHA-256：`1b1dbf3001f5c1fc3909c694e59fc3aa57f39446948e8055319c5cfac02cf8a8`
- 注意：`Codex` 有多个同名语言资源，其中 pathID 763 的德语正文仍标记 `GUI-en`。英语正文为 pathID 796，不能仅按名称或 `GUILanguageFile` 选取。
- 大体积导出、反编译目录和日志已排除 Git；提取脚本、原文、映射、清单及校验报告入库。

## 翻译
- 2026-10-16 翻译阶段完成并复核：150条已批准试译复用于正文，没有重跑；全文14,691条完成独立语义审校及Sol最终质量闭环，最新报告哈希为 `4ab829a90ae0694f5f723122eb088a7650701f65045100a69481532f547e7b0e`，第5轮无待裁决争议并获程序批准；完整验收快照见 `TranslateFiles/reports/accepted/final_4ab829a90ae0694f/`。导出前另核出26条拼接文本的边界空格不一致，均按源文修复并独立复查通过（review round 22 clean）；最终CSV为单列14,691条，与原文逐行对应，无空译文、无边界空格差异。译文SHA-256为 `eaad404d187d8ff9ce67ec722bd4d9ead82f81c679f4998d1482bbabd5ca4b48`，验证见 `TranslateFiles/reports/final_validation.json`。冻结术语表revision 10（162个人物、951条术语），哈希 `0b9e22152b88ca7cf2d4dc242e15c63bc5931dfcb6665c4e0ccf177f051ab649`；变量、样式标记、换行及术语均通过导出校验。实机验证留待回填阶段，当前状态 `pending_repack`。
- 2026-10-16 协议一致性复查：补齐试译与正文的证据限制，统一直接提交/批次交接的试译例外继承和逐 ID 总结保存，修复冻结键大小写误合并、修复背景丢失、纯空白原文摘录及非文本理由误通过。56项流程回归及补充定向回归通过；本轮未操作游戏译文、运行数据库或在途任务。详见 `TranslateFiles/reports/workflow_contract_review_20261016.md`。
- 2026-10-16 Sol 定位修正（用户明确要求）：Sol 只裁决明确遗留争议或处理多轮失败/反复回退的定向难题，不批量复审风险标签、普通样本、历史改动和一般一致性分组。已通过公开 `quality-report --kind final` 将旧6,070项轮归档并迁移为第2轮：24条明确疑点，17条复用已有有效结论，迁移时剩7条待裁决；旧轮已发现的1,452条问题保留为 carried_findings，待争议结论齐备后集中定向修复，不让 Sol 重读或自动放行。后续只读取新 quality-report 返回的 next_input_file，不继续旧输入包；修订复查通过后不因曾改动再交 Sol。规则、保全与验证见 `TranslateFiles/reports/sol_scope_fix_20261016.md`。
- 2026-10-15 多术语修复防回退：修复包列出已满足术语和已有语境例外；例外默认继承，撤销需明确原文理由。整轮复查记录新引入的术语问题，同条目两次回退自动提前转 Sol 子代理；保留整轮调度及严格语义审校。仅更新工具规则，未重置译文或改动在途任务。
- 2026-10-15 流程更新：正文后常规修复按失败条目累计最多 6 轮；仍未通过自动交新 Sol 子代理定向修复，无须申请追加轮次。每轮全部批次完成才统一复查；保留已有译文、历史计数、独立审校证据与通过结论。单任务重试和试译预算保持独立，见 game-translate 整轮验收规则。
- 2026-10-15 独立审校与 Sol 整轮验收：review/final_review 各批先保存候选及真实六维证据，整轮全部结束后通过 review-scan 统一验收，只有通过项才写入正式审校状态；失败 ID 跨批合成下一轮，保留无关译文、审校者与预算。quality-report --kind final 固定 Sol 本轮范围并分包；sol-round-record 分次记录通过或问题，不立即派修；所有检查齐备后 sol-round-finish 才集中派发修订或批准。下一轮只复查变更及受影响一致性，通过项复用。试译和已有严格验收结果沿用；只更新工具与协议，未重置现存译文、证据或在途任务。
- 2026-10-15 整轮修复调度：一轮包含本次复查后生成的全部修复批次。各批次只保存修复稿，等本轮全部批次完成后统一复查本轮所有修复 ID，再将剩余失败项重新合批为下一轮；不得修完一批立即质量验收并插入返修。尚有未完成批次时 draft-scan 返回 awaiting_round、checked_records=0。修复轮编号和任务状态写入报告，跨轮保留未解决问题的尝试数；问题清零后才最终全量验收。旧版最新被拒绝的修复候选可重新 batch-finish 保存，保留任务、草稿、身份与在途交接；不重置或重译已有成果。
- 2026-10-15 验收范围优化：`draft-scan --prepare-repairs` 首次执行全量验收并合批安排问题修复；后续仅复查本轮修复或变化的 ID，保留未变化的通过结论，不每轮重扫全文或重译通过项。所有问题清零后自动最终全量验收，若发现遗漏则继续定向修复。首次全量无问题时直接复用结果。`reports/draft_checks/round_XXXXX.json` 逐轮区分 full 全量验收与 issues 问题条目复查，记录检查 ID、问题、修复状态和结果；最新汇总仍为 `reports/full_draft_scan.json`。独立语义审校、Sol 审查及导出门槛保留。旧工具已有有效全量报告时核对输入版本后直接复用基线，不因升级重扫。此条取代下方旧“修复后再次全量扫描”的调度描述；本次仅更新工具及文档，不操作在途任务或重置译文。
- 2026-10-15 集中验收调整：普通正文批次只检查任务版本、ID、字段类型及锁定约束并保存草稿，不再因术语、变量或空译文当批返工。全部草稿完成且在途任务结束后，通过 `TranslateFiles/scripts/batch_task.py draft-scan --prepare-repairs` 全库严格扫描，将失败 ID 跨原批次集中合批为严格修复任务；其余译文和真实产出者保留。修复完成后再次扫描，clean 才进入全文独立审校，之后保持 Sol 审查及严格导出。试译仍即时严格验收。旧 `single_task.py check` 的普通 translate 分支仅做保存可靠性检查，避免历史控制器继续触发碎片化术语返工。此次只改工具和协议，不重置草稿、不调整在途任务或运行配置；只读保全证据见 `TranslateFiles/reports/deferred_draft_preservation.json`。
- 2026-10-15 批次交接优化：新增 `TranslateFiles/scripts/batch_task.py`，正文后续新批次改用 `batch-open --stage translate --workers <实际实例ID...>` 一次领取并生成单文件输入包；结束通知后 `batch-finish --sessions <session...>` 一次检查、暂存、完整提交和汇总，不再循环调用旧 `single_task.py check`、sleep 或读日志。失败时 `batch-repair` 只交付失败 ID，合格条目持久保留，至多一次自动集中修复；原产出者、修复者与审校者逐条追踪。术语与普通词义由模型说明例外，程序只规范字段和唯一大小写匹配，不关闭术语检查。长结果可 `batch-save` 分段落盘并由程序合并。只读保全核对确认 14,691 条记录的内容/阶段/例外/锁定指纹前后一致，7,558 条草稿保留，未操作现有 1 个在途任务或调整运行配置；证据见 `TranslateFiles/reports/batch_execution_preservation.json`。当前显式批量设置继续沿用，若需更新为翻译/审校均 80 条，按公共配置接口在无在途任务时变更调度，不重置译文。
- 用户成本约束（本次优先执行）：150 条试译固定分为 5 组，每组 30 条；逐条保留场景/角色信息，场景变化不再拆出小批。完整保留已验收 40 条译文及真实作者身份，仅用 4 个新任务（20/30/30/30）补齐剩余 110 条。随后因共享工具总执行预算，独立审校合并为 3 批、每批 50 条，保留全部 150 条而未缩小样本。调度修订 r11/r12 均未重置语义状态，不重跑已完成译文。完整输入预算 96,000 字符，不截断原文或证据。局部问题只修相关结果，不整体重跑试译；计划证据见 `TranslateFiles/reports/pilot_five_batches.json`。
- 当前状态（2026-10-16）：150条试译已批准并复用；14,691条译文、全量独立审校、Sol最终验收和正式CSV导出均已完成。正式输出与质量哈希、零空译及pending_repack状态见本节首条记录与TranslateFiles/reports/final_validation.json。
- 工作流：用户于 2026-10-14 选择自定义工作流、Codex 子代理；使用技能默认模型 `gpt-6-luna`，不调用外部 API。
- 词典：新版全文术语提取已覆盖 14,691 条文本、441 个批次，汇总为 198 条人物候选和 1,254 条术语候选；已在 `glossary/r4/` 完成 25 批独立语义审校，并独立修订三项机制/称号/设施译名。当前正式冻结版位于 `glossary/revision_10_fd73d738/built/glossary_reviewed.json`，与入库的 `glossary/mechanics_revision/built/glossary_reviewed.json` 字节一致，SHA-256 为 `0b9e22152b88ca7cf2d4dc242e15c63bc5931dfcb6665c4e0ccf177f051ab649`。旧版冻结表只供历史追踪。候选数量不是冻结数量。
- 策略：实际子代理 ID 记录产出/审校来源，术语和正文分别由不同实例审校。r13 已通过公开 configure 将全文翻译上限提高到每批 80 条、审校 40 条，字符上限沿用 10,000；跨场景合批、逐条保留元数据，不附带 CSV 相邻记录。该调度变更 semantic_reset=false，保留全部 150 条现有试译及审校。试译经 Sol 核验后开放全文；全文六维审校完成后再检查高风险、普通抽样和跨批一致性，最后由程序导出。
- 调度与验证：沿用自定义Codex子代理工作流，常规模型为gpt-6-luna，最终疑难验收使用Sol；正文批次上限80条、独立审校/修复40条，源文字数上限10,000、完整输入包96,000字符，context_records=0。批次通过batch-open/batch-finish交接，整轮集中复查；不附带CSV邻行，不重跑已批准试译。API请求数为0。
- 配置与记录：`TranslateFiles/config/workflow.json`、`TranslateFiles/config/extracted_context.json`、`TranslateFiles/TranslateDoc.md`；运行状态、任务、结果、缓存不入库。
- 2026-10-15 正文工具修复：标识符紧接中文不再误报丢失；不区分大小写匹配时仅归一化可唯一确定的 ASCII 术语例外键；冻结词表的逐条译名禁止被自动词族合并覆盖（例如 Guard/Guards）。17 项定向回归通过。暂停且无在途任务时刷新了65个未领取任务包，保留任务 ID、尝试次数、草稿及150条试译批准；已保存草稿将在必需的全文独立审校中核对。修复补丁、测试和刷新报告保存在 `TranslateFiles/scripts/` 与 `reports/frozen_matcher_refresh.json`。
- 保护规则：收紧通用方括号规则，仅保护实际变量 `[HOTKEY]`、`[Stack]`、`[s]`、`[es]`、`[NAME]`、`[TASK]`；`[Check ...]` 玩家提示允许翻译。补充 `PName*`、`FName*`、代词/等级替换键、`Int_*`、`RationsLost`、`MedicineGathered`、`XX` 及样式符 `/`、`*`、`$` 的保护。
- 工具适配：共享工作流增加可选 `placeholder_family_overrides`，默认行为不变；项目配置负责本作的窄化规则。另修正稀疏术语证据的上下文范围，并增加 Windows 瞬时文件占用的原子写入重试。保护/还原及玩家提示可译样例通过，工作流和术语工具共 40 项测试通过。
- 新质量版本：流程升级检查为 61 项；本项目补充正文前上下文替换 API 的暂停、任务和数据覆盖约束后，完整工作流/术语/质量回归共 63 项通过。元数据修改通过公开 `replace-context` 命令并保留历史，不直接修改数据库。
- 当前上下文：`config/normalized_context.json`。按 XML 直接父节点与字段区分 Dialogue/Narrative/Player choice/Quest 等；ChoiceText 的作者为 Player，原继承 NPC 改为 dialogue_partner；无明确说话人的正文保持空，不发明角色归属。原文、源位置和场景分组未变。
- 试译计划：`reports/pilot_selection_plan.json`，150 条包含全部八类源资源、12 类文本、91 个场景组，兼顾否定/条件/数字/人物关系/变量与长句。它不代表覆盖每个分支和角色。
- 变量保护修复：`FHimHer1self` 的旧正则会回溯漏掉编号，已改为禁止数字回溯并允许完整 HimHer 编号后接 self。6 条原文共 7 次出现，通过实际模板及边界检查；第 7,372 条新任务已确认完整保护 `FHimHer1`。因保护/文体变化，r7/r8 的 95 条试译仅保留历史，新版 r9 重新进行 150 条试译，不能沿用旧批准。全文正文未启动。
- r8 历史迁移验证（已被 r9 语义重置取代）：取消 CSV 相邻文本时保留了 61 条试译及实例来源，仅重建当时剩余 89 条任务。补充调度改动保留进度、文体改动重置和样本改动重置的回归测试，完整 66 项检查通过（167.522 秒）。原文 SHA-256 与提取时一致。
- 本次 Skill 复读与术语复核：重读当前入口及自定义、质量、术语、占位符参考，沿用每批新 Luna、独立审校及无 CSV 邻行规则。r9 已完成的 125/150 条试译保留历史。三项问题经新产出实例及另一审校实例独立处理，正式 revise-glossary 成功：Walk Your Shots → 逐发校准；The Flayed One → 被剥皮之神；Barracks Rebuilt → 兵营重建完成。保留其余 1,449 项逐项审校及实例来源；全表术语命中比较确认影响 15 条记录。已恢复 r10，重新准备 150 条试译、93 批任务，独立审校及 Sol 验收尚未完成。证据在 `TranslateFiles/glossary/mechanics_revision/`，主审范围在 `reports/glossary_sol_preflight_20261014.md`；本记录不构成试译批准。
- 输出约定：项目根目录 `expeditions-conquistador_text_translated.csv`，与原文逐行对应
- 低成本试译工具：共享流程默认 30 条、翻译和独立审校各一批，合计最多 6 次执行（含重试）；`pilot-plan` 预检，`reduce-pilot` 可优先复用已译样本。项目单批诊断脚本兼容精简 pass 记录和已有术语例外。本次仅接入工具兼容与项目副本模拟，不表示真实在途样本已收缩为 30 条；变更范围前须结束/回收在途任务。
- 禁翻信息：`GivenName` / `FamilyName` 等身份字段未进入原文，因为剧情函数直接比较这些原始姓名。`LanguageCulture` 与 `CustomCinematicsTutorialLanguage` 也为程序配置，不送翻译。人名可在正文中译写，但回填时保留身份键。
- 格式提醒：`DialogGUI.PrepareStringForDisplay` 将 `/`、`*`、`$` 作为斜体/粗体/颜色标记；需保留标记及作用范围。选项正文中的 `[Check ...]` 是显示说明，与独立的条件表达式区分。

## 回填
- 方式：直接重建五个 Unity 文件并静态改写 `Assembly-CSharp.dll`，增加独立的 `ConquistadorChinese.dll` 排版组件。不需要 BepInEx、XUnity 或联网翻译，游戏语言保持 English。
- 文本：五个 XML 共 14,202 条、场景字段 455 条、托管显示文本 34 条，合计 14,691 条，与正式 CSV 逐条对应；姓名身份键、难度及设置内部键保持原值，仅显示时汉化。
- 文件：`Expeditions Conquistador_Data/` 下的 `sharedassets0.assets`、`sharedassets1.assets`、`level0`、`level2`、`level3` 及 `Managed/Assembly-CSharp.dll`；新增 `Managed/ConquistadorChinese.dll`。
- 字体：官方 Noto Serif SC / Noto Sans SC，固定 google/fonts 提交 `1d0e46c7933245c8180fe83e47917961c913bbdb`，实例化常规/粗体并按源文、译文和 ASCII 字符子集化；修复候选覆盖 3,157 个所需字符（补全空格字形），新增教程中文无缺字，附 OFL 许可证。
- 排版：保留 `/`、`*`、`$` 样式标记处理，改用中文分字、标点避头及像素测量换行，保留拉丁姓名和原有空格。游戏内结构转换在游戏程序集完成，独立组件不依赖游戏内部 `WordChunk` 类型。
- 可复现脚本：`Repack/Scripts/prepare_fonts.py` → `repack_assets.py` → `build_managed.py` → `deploy.py` → `build_patchkit.py`。字体脚本需要联网获取固定版本字体，其余步骤本地执行；备份在 `Repack/Backup/SteamBuild1752467/`，构建结果在 `Repack/Build/`，两者不入库。
- 资源校验：保存后重新加载并逐条对照译文；53,437 个未修改对象的原始字节哈希保持一致；托管程序集检查 34 条显示文本、190 处显示调用、5 个换行方法及 79 处测量调用。
- 实机验证：中文主菜单、战役设置、角色指南、队员传记、开局介绍、首章港口“没收”事件的多轮对白和选项跳转、资源扣除及“再次启航”任务目标。长对白滚动、姓名变量和中文标点正常；代表场景截图保存在 `Repack/Evidence/`。这是首章代表场景验证，未逐一游玩全部分支与第二章。
- 安装验证：恢复六个原版文件后，使用玩家安装器依次执行安装、还原、再次安装、重复安装，每次核对七个输出位置及 SHA-256，均通过。测试记录为 `Repack/reports/installer_test.json`。
- 差分发布：仅分发 VCDIFF 差分、独立组件、解码器、安装器和许可证，约 7.5 MB；安装器校验原版哈希、先生成并验证全部目标，再备份和写入；不包含游戏本体或原始资源。首次发现精简解码器不支持 LZMA 后已改为完整 xdelta 解码器并通过整套安装测试。
- 自定义语言模式未使用；未验证 Steam 成就实际解锁，不作成就兼容承诺。
- 用户实测补充（2026-10-16）：旧存档把英文 Bio、Goal Title/Description 独立序列化，替换原始资源不会刷新这些副本。离线修复仅在人物界面与目标界面读值后映射已审校译文，保留存档文件、姓名身份及内部任务键。已覆盖截图中的八个静态任务标题、动态测绘标题/计数、Citlalli 传记和返航说明，19 项共享代码回归通过；已部署，待游戏内复测。
- 图片教程：确认 47 页英语教程为 `resources.assets` 中 800×600 的透明 Texture2D，右侧 Tutorials 标题也是贴图。按用户选择保留原图，在同一窗口增加可滚动的中文说明区域；新说明及标题共 48 条，分两批产出并由不同实例逐条六维审校，文件程序校验及独立导出通过，存于 `TranslateFiles/tutorial_supplement/`。主项目不支持追加源记录，本次为独立文件补充通道，不重跑主项目试译，也不改动 14,691 条正式 CSV。离线组件已构建，不能沿用初版实机通过结论。
- 上一轮已部署候选：13 个安装载荷文件、7,775,495 字节；七个输出文件均完成原版→差分解码→目标哈希验证。此前离线验证记录为 `Repack/reports/candidate_validation.json`。用户授权后已确认游戏退出并部署候选，七个游戏输出及十三个配套安装/还原工具文件的哈希均通过；未改动存档，原版备份保留。部署记录为 `Repack/reports/candidate_deployment.json`，旧存档传记、任务及教程布局仍待实机复测。`release-check` 已按预期拒绝旧证据哈希，正式打包与发布继续暂停。

## 已知问题

- 中文字体和排版已完成上述代表场景验证；游戏原有固定尺寸 UI 在高分辨率下文字偏小，未全面调整所有窗口比例。
- 2026-10-14 用户确认已清理安装目录；复查根目录仅有游戏数据目录、游戏 EXE 及两个 Steam DLL。后续以此版本为基准。
- 教程正文通过 `TutorialSlide.imageName` 对应图片显示；当前只提取分类及标题，图片内正文尚未处理。过场视频内文字也未提取。
- 硬编码 UI 已收录人工确认的显示位置；异常提示、运行时拼接与剩余英文仍需游戏内检查，不宣称全文覆盖已验证。
- 对话原有空格分词问题已通过静态排版补丁处理；尚未逐场景检查的极端长度文本仍可能存在排版问题。
- 原始姓名身份字段及日期仍保留原文。旧存档传记/任务及 Tutorials 的漏译已进入本次修复，尚未实测通过；原教程截图内文字保留，另加中文说明。视频文字暂未处理。
- 回填已在本地安装目录生效；使用其他游戏版本或已有其他补丁时，安装器会因原版哈希不匹配而停止。安装前请备份存档，勿删除 `ChinesePatch/Backup` 原版备份。
- 历史试译曾记录若干非阻断措辞注意项（普通词语境、轻微重复和建筑别名）；这些事项已进入全文独立审校与定向复查，最终验收无未解决争议。

## 对外发布

- 补丁：`Dispatch/expeditions-conquistador_子非鱼汉化1.0.zip`，7,436,931字节。
- SHA-256：`6c87aba83c265c3afc6b30b580c6ecc1c4fd7ae938dfbbc0801ce2bc4437891a`。
- 支持：Steam Windows，Build1752467 / 游戏1.6.6.1；游戏进程为x86，随附差分解码器要求64位Windows。未测试其他商店或系统。
- 载荷：安装器、六个VCDIFF差分、中文显示组件、解码器、安装清单及三份许可证，共13个载荷文件；ZIP另含安装说明、发布清单及SHA256SUMS。
- 安装：备份存档、退出游戏，将ZIP全部解压至游戏根目录，运行“安装汉化.exe”，输入1；游戏内选择English。原文件自动备份至ChinesePatch/Backup。
- 卸载：退出游戏后运行同一安装器，输入2，待确认还原完成后再移走工具。保留原版备份。
- 验证：最终纯净基线安装、还原、再次安装与重复安装四轮哈希测试通过；用户明确确认旧存档传记、任务及中文教程说明均正常；首章代表性对白已有实测。未进行全流程通关验证。
- 已知问题：教程原图英文保留，另加中文说明；视频文字未汉化；日期和程序身份姓名保留；高分辨率下固定尺寸UI可能较小。未测试全部分支、联机及成就实际解锁。
- 正式下载：[GitHub Release v1.0](https://github.com/zfyu222/expeditions-conquistador/releases/tag/v1.0)；独立公开仓库：[zfyu222/expeditions-conquistador](https://github.com/zfyu222/expeditions-conquistador)。已确认公开、非草稿、非预发布，匿名下载HTTP200且SHA-256与本地ZIP一致。GitHub自动规范了资产下载名，页面标签保留完整中文名称；ZIP内容及校验不变。
- 百度网盘镜像：目标 `/Hanhua/expeditions-conquistador/expeditions-conquistador_子非鱼汉化1.0.zip`，尚未上传。MCP ensure_directory返回“创建目录失败 /Hanhua: errno -6”，已停止后续删除与上传，未删除网盘旧文件。需检查或更新网盘授权后重试；以GitHub Release为当前下载入口。
- 后续可能更新，请关注仓库/Releases或收藏网盘发布渠道。
- 公开仓库采用提交快照发布，用户提供的四张反馈截图仅保存在本地历史；用 `Repack/Scripts/publish_snapshot.py` 同步公开源码与交付文档，主项目原始历史不重写。

## 版本记录
- 2026-10-13 - 初始化汉化项目工作区（start-translate skill）
- 2026-10-14 - 补充官方游戏资料、本地技术线索与纯净版本基准，完成初始化档案
- 2026-10-14 - 提取 14,691 条英语文本，保存逐条回填映射并完成源位置与 CSV 校验
- 2026-10-14 - 按用户选择初始化 Codex 子代理翻译流程，开始全文术语整理；正文尚未执行
- 2026-10-16 - 完成14,691条全文独立审校和Sol最终验收，导出正式单列译文CSV；游戏内验证留待回填阶段
- 2026-10-16 - 复核全部26条拼接文本边界空格并通过独立整轮验收，重新完成Sol质量闭环与正式CSV导出；边界空格差异为0
- 2026-10-16 - 完成静态资源、中文字体及托管排版回填；修复剧情窗口类型加载错误；通过首章多轮对话、任务目标及差分安装/还原测试
- 2026-10-16 - 根据用户截图定位旧存档序列化文本及图片教程；按授权保留教程原图、补充中文说明，离线构建新候选，待部署复测后重新验收

- 2026-10-16 - 按用户授权部署旧存档显示修复与中文教程说明候选，同步匹配的安装/还原工具，七个输出及十三个工具载荷哈希验证通过；实机复测待完成

- 2026-10-16 - 用户截图发现 Bonita 的德语传记残留：按原始 GivenName/FamilyName 的唯一身份对应官方多语言 XML，新增188条传记别名，复用既有中文；207项离线回归通过。该轮候选随后已按用户授权部署，待实机复测。

- 最新离线候选：`Repack/Build/CandidatePatchKit/`，13个载荷文件、7,951,623字节，七个输出差分解码哈希通过；加入德语等传记映射后已按用户授权部署，七个游戏输出及十三个安装/还原文件哈希核对通过，存档未改动。

- 2026-10-16 - 按用户授权部署188条多语言传记映射修复；确认游戏退出后覆盖并同步安装/还原载荷，全部文件哈希通过，保留存档及原版备份；Bonita等旧存档传记仍待用户实测确认

- 2026-10-16 - 用户确认传记、任务和教程说明全部正常；最终安装四轮测试及release-check通过，生成并校验v1.0正式ZIP，开始公开发布

- 2026-10-16 - 正式发布v1.0至GitHub Release并完成匿名下载哈希核验；百度网盘MCP创建目录返回errno -6，镜像未完成且未删除任何旧文件
