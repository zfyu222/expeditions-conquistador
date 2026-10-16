# 静态回填与修复候选

目标为 Steam Windows x86，Build 1752467 / 游戏 1.6.6.1。游戏语言保持 English，无需 BepInEx 或 XUnity。

截至 2026-10-16：初版已实测首章对白、选项、任务目标及安装/还原。用户后续截图证实旧存档保存的英文 Bio/Goal 不会随资源回填更新，教程内容是图片。本目录的新候选在显示层复用已审校译文，并保留教程原图、增加中文说明。候选现已按用户授权部署并通过安装文件哈希核对；实机复测尚未完成，不能发布。

## 构建

在项目目录使用已安装 UnityPy、FontTools 的 Python 3.12：

```powershell
python Repack/Scripts/prepare_fonts.py
python Repack/Scripts/repack_assets.py
python Repack/Scripts/build_managed.py
python Repack/Scripts/test_saved_text.py
python Repack/Scripts/prepare_candidate.py
python Repack/Scripts/build_patchkit.py --candidate
python Repack/Scripts/verify_candidate.py
```

字体来自固定官方提交及本地缓存。托管构建使用 Windows 自带 .NET Framework 编译器和 .NET 10 SDK，dnlib 引用工作区已有 dnSpy 副本。差分工具固定为 xdelta 3.2.2；载荷中名为 `xdelta3decode.exe` 的程序实际使用完整 xdelta 可执行文件，以支持 LZMA 二次压缩。

资源输入优先使用项目中的六个原版备份；无备份时仅接受原始游戏哈希。五个资源保存后重新加载，逐条校验译文并验证全部未修改对象。所有新增组件不得引用游戏内部类型，`WordChunk` 转换仅在原游戏程序集内完成。

`CandidatePatchKit/` 是离线候选，`PatchKit/` 保留此前测试的初版。原版游戏备份、完整游戏资源、生成的二进制及解码验证副本均在忽略目录中，不入库。

## 新增教程说明

`inspect_tutorial_images.py` 导出引用纹理供分析；`ocr_tutorials.py` 用 AINiee 环境内 RapidOCR 本地识别透明字形，无外部 API。只提取英语教程页的说明区域，任务保留图片来源和 OCR 坐标，独立审校处理英文粘连与左右栏交错。

新增说明及标题共 48 条，由 `TranslateFiles/scripts/tutorial_supplement.py` 独立管理文件任务与校验。未修改主源 CSV、正式译文、已批准试译或数据库。正式补充成果和逐项审校证据在 `TranslateFiles/tutorial_supplement/`；可阅读其中的 `中文说明预览.md`。

游戏中的原图按比例缩放至说明区域上方，中文说明位于下方并支持滚动；未改写原始教程纹理文件。该布局目前仅完成编译，须实机检查，不视为已经显示正常。

## 退出游戏后的必要检查

1. 已运行 `deploy_candidate.py`：部署七个游戏文件，并同步匹配的十三个安装/还原载荷文件；原版备份保留，存档未改。该脚本拒绝覆盖运行中的游戏。
2. 加载用户旧存档，检查 Citlalli 传记、返航等静态任务、测绘任务标题和 9/10 石冢进度；确认选择/任务进展仍正常，存档内部键未被替换。
3. 检查右侧“教程”标题、营地制作第 1/3 页及数种长说明，检查切页、滚动、字体、按钮和截图比例。
4. 重建正式安装载荷，重新执行玩家安装、还原、再次安装及重复安装的哈希测试。
5. 记录绑定新载荷哈希的实机验收，`release-check` 通过后才能重新生成 ZIP。

当前没有对外上传或发布。此前按用户要求仅做离线工作；收到“部署吧”后确认进程退出并完成部署，尚未重新操作游戏 UI。

## 后续德语传记修复候选

用户截图显示旧存档通用 Bio 字段中保存了 Bonita 的德语原文。已依据官方语言 XML 的 GivenName/FamilyName 唯一身份加入188条多语言原文别名，对应已审校的英语传记中文；来源文件逐个校验提取哈希，不按数组位置猜测，不新增翻译。207项共享代码回归通过。代码、候选及差分已重建；随后按用户授权确认游戏退出并完成本轮部署，七个游戏输出和十三个安装/还原文件哈希通过。`candidate_deployment.json` 现对应本轮多语言传记修复，实机显示仍待复测。

## 最终验收与发布

用户已明确确认传记、任务和教程说明均正常，最终安装四轮测试通过；已重新record-game-check并通过release-check。正式v1.0 ZIP已生成，档案见release_archive_validation.json。历史待测记录已被最终验收覆盖。公开仓库按已提交文件快照同步，用户提供的四张反馈截图保留本地，主项目历史不改写。
