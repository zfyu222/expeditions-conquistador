# 正文批次执行约定

只处理主代理分配的一个任务。Python：`D:/StaticHanHua/Tools/AINiee/venv/Scripts/python.exe -X utf8`。

读取分配JSON中的task_file、prompt_file、result_file。prompt_file只有协议，全部原文、相关冻结术语、元数据、保护映射在task_file。静默加载JSON，分段展示本批所有records的完整原文、保护token、元数据（及审校阶段的现译）。terms只展示src/dst/category_path/info/性别等必要字段，不打印巨大evidence_rows数字数组。不得读取全表、CSV邻行、全库、旧聊天或历史结果；批内记录不是连续剧情。必要的游戏背景和文体已在任务中。

按冻结术语、任务文体和原文忠实自然地处理全部ID，不增加性别、规则、技能施放、结果或剧情。保留首尾空白、换行、引号、数字、否定、条件与样式作用范围。translate输出须用protection中原样token，不能把变量直接译掉或改变次数；审校阶段保留原变量。Check方括号提示是可见文本，应翻译。技能词遇普通词义则按语境处理，并用命中术语精确src和理由记录exceptions，不改表。不要为了同义偏好重写正确译文。

仅写指针指定的result_file，不另起文件替代交付，不修改任务、指针或assignment文件。不得改源文、术语、DB、Game、正式CSV；不得claim/submit或再开代理。顶层task_id/input_hash必须来自本任务，records按ID完整覆盖。translate每项id/translation/issues/exceptions。review按prompt要求逐条返回reviewed、原文连续source_excerpt、reason、六维checks、changes、issues、exceptions；非空文本accuracy/completeness/logic不得not_applicable。修改时before是任务内完整原译文，after是完整新译文，类别为六维之一、严重度minor/major/critical，至少一项checks为corrected。关键未解决疑难写blocking，不能伪造通过。

完成前调用：`D:/StaticHanHua/Projects/expeditions-conquistador/TranslateFiles/scripts/single_task.py check --assignment <本次分配JSON绝对路径>`。此诊断不提交结果；review另外静默逐项用workflow_quality.validate_review核验协议。出现诊断，最多一次集中本地格式/遗漏修正；修正后应再次运行只读诊断，确认结果，而不是跳过复检。复检不算第二次修正，但若仍有错误不要再修改，报告主代理。exceptions的source须使用该记录实际命中的src，不是整批术语的大小写或别条命中；unrelated_exceptions诊断中的case_matches供一次集中修正参考。主代理负责submit及后续恢复。只报告task_id、结果路径、条数、自检状态及简短疑难，不贴整批文本。

检查可能需要十几秒。工具返回session_id表示尚未退出，须用write_stdin等待；functions.exec返回正在运行的cell_id则用functions.wait等待。空输出不代表通过。必须确认进程结束且读取本次生成的diagnostics全部条目，才能做一次集中修正或报告failures=0；不能只修首项或引用旧诊断。

生成时按ID显式绑定译文，不将纯译文列表按位置zip给任务ID。长列表容易漏项，可每组最多20条追加到同一result_file并立即落盘，仍属同一任务；最终按任务ID全覆盖。计数断言失败时保留现有草稿、定位具体缺失ID后补齐，不要丢弃全部草稿或把不齐初稿当成任务结束。
