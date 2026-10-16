# 本作术语审校要求

本文件是主代理的审校范围与一致性要求；实际逐项语义判断和任务结果由子代理完成。

- 新版 decisions.entry_reviews 必须逐项覆盖分配 ref；每项含 ref、evidence_rows、source_excerpt、reason 和 checks（source/translation/category/consistency 四维，各有 status 与具体 evidence）。引用 ordinal 既须属于本条 entry.evidence_rows，也须出现在 task.records；source_excerpt 必须是该处原文连续摘录。不得用脚本批量填写同一句认可理由。
- 每个问题对应合理的 edit/quarantine/addition，与本条 entry_review 保持一致。隔离也要说明源文真实含义和为何不宜冻结，不以“隔离了”代替语义审校。

- 对分配的每个条目核对任务中原文证据、译名含义、分类和人名性别；不得仅因自动检查通过而认可。
- 对 `duplicate_source` finding 的同一英文源文，按 `characters`、`terms`、`non_translate` 的表顺序，再按数值 index 升序选择唯一主条目。参考任务中的只读 related_entries，其他分配到本批的重复条目隔离，理由注明主条目 ref。主条目自身仍需语义审校；分类有误时由负责主条目的审校者修正或隔离后添加正确条目。不得修改别批 ref。
- 不把普通叙述词、通用形容词、整个台词或无明确专名用途的短语固化成术语。尤其注意 House、Spring、Market、Hard 等多义普通词。明确的技能、属性、营地工作、物品和角色职业仍可保留，并写明适用语境。
- 译名不得无依据添加“武器：”等标签，也不要把解释性括号放入正文替换译名；解释写在条目说明中。
- 检查相同角色的全名、姓氏、简称之间的译名是否兼容；未获原文证明的性别用“其他”。西班牙称谓、人物职务要根据剧情证据理解，不能单凭现代军衔词典套用。
- 同一地点、武器、技能、资源、阵营的大小写或单复数变体应一致；保留有用变体，不因共用中文译名而全部隔离。
- 军事称谓 Capitán 结合部队与民兵语境，不自动按船长理解；War Chief 不因当前角色恰好为女性而在通用译名额外加入性别。不要删去称谓本身的军事实义。
- 不把 PName/FName/PNAME、HOTKEY、Stack、动态数字键等变量加入普通译名表。它们已有专用保护规则。
- 每个 quarantine/edit/addition 必须解释语义依据并引用本任务提供的真实证据 ordinal。新条目的 source 必须在证据中出现。
- 同一 ref 只能出现在 edits 或 quarantine 中一次；要隔离的重复条目不再编辑。无动作但认可的条目仍需列入 reviewed_refs。所有分配 finding id 都列入 acknowledged_findings，并作语义处理。
- source 指实际术语原文；recommended_translation 指简体中文译名。检查重音符号、全名词间空格和源文拼写，不自行修订英文原文。
- 若同一源文在不同语境确实多义，保留明确玩法概念时说明适用范围，正文遇到其他义项用有依据的单条 exceptions，不通过含糊的全局禁翻绕过审校。
