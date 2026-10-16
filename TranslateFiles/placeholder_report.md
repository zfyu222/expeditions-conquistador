# 占位符分析报告

- 文件：`expeditions-conquistador_text.csv`
- 逻辑行：14691，物理行：15077

## square_bracket — 189 次出现
- 方括号标记（变量占位符/BBCode/富文本标签，如 [Player:Name] [i] [color="red"]）
- 建议禁翻正则：`\[[^\[\]\n]{1,60}\]`
- 高频样本：
  - `[HOTKEY]` ×52
  - `[Check Diplomacy Medium]` ×28
  - `[Check Diplomacy Hard]` ×17
  - `[Check Tactics Medium]` ×16
  - `[Check Diplomacy Easy]` ×11
  - `[Stack]` ×9
  - `[s]` ×8
  - `[Check Scouting Medium]` ×8
  - `[Check Tactics Hard]` ×8
  - `[Check Scouting Hard]` ×5
  - `[Check Tactics Easy]` ×4
  - `[Check Scouting Easy]` ×3
