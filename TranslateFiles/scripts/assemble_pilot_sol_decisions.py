"""Serialize already-read, explicit Sol observations; no inferred semantic passes."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
notes_path = root / 'reports/pilot_sol_reading_notes.json'
notes = json.loads(notes_path.read_text(encoding='utf-8-sig'))
report = json.loads((root / 'reports/pilot_quality_review.json').read_text(encoding='utf-8-sig'))
repaired_observations = {
2573: ('pass', '实际复读新译，已恢复完整引号；政变控制岛屿不等于获授全新大陆主权的反问关系保留。'),
5121: ('pass', '袋子样式有女性气息而非确定女性所有，不再限定钱袋功能；药草药剂、绣名与三年前远征无人返回保留。'),
7372: ('pass', '新译明确不侍奉羽蛇神的人，不再反转人群；本人或主人自愿献祭、九层米克特兰和四个姓名/代词变量均保留。'),
10052: ('pass', '改为英勇的战斗中，十四岁女孩、围观壮汉、不与部族结仇的条件均保留；courageous按普通形容词使用并有精确src例外。'),
10230: ('contextual', '已去除当年与在这里遗失的增译，寻找村落和数百人的规模正确；lost采用遗失，应在全文同场景复查是否更适合失去，不据该孤句补球赛剧情。'),
10259: ('pass', '新译否定位于斜体外，仅属于加斜体；我们赢球在先、父亲公正取得神像在后，主体与先后关系均恢复。'),
12025: ('pass', '加勒比人是实施献祭者，人物交给他们供他们献祭；西北海岸附近山区和下次满月前期限保留。'),
12434: ('contextual', '所有格用于其自己的意愿，不再成为离开的宾语；条件性自主离队及劝说/留队损士气/惩戒提士气的关系正确。很明显与显然略重复，全文审校可精简，不因此重跑试译。'),
13469: ('contextual', '新译只保留动态PSenorSenora敬称，既不叠加阁下也不加入我的配偶暗示；妻子照顾儿子与不再属于西班牙的否定正确。exceptions旧理由写保留mi而当前已省略，措辞记录需在全文审校清理，语境例外本身有效；不宣称该理由字面准确。'),
14164: ('contextual', '修订将Incarnation作为道成肉身的名称括注，并保留源文英文正式别名；不再译圣母领报或圣母出生。结合梵蒂冈教理461的圣子取人性概念验收；括注属称号而非声称圣母本人道成肉身。中文建筑名称仍可在全文统一，原游戏历史年代未改写。'),
14170: ('pass', '末段改为哥伦布之子迭戈及其妻玛丽亚居住两年，不再把妻子归给父亲或误加母子身份；二层/一层及104公里、18.5米等全段数值保留。'),
}
for ordinal, (disposition, reason) in repaired_observations.items():
    notes['records'][str(ordinal)] = {'disposition': disposition, 'reason': reason}
for item in notes['consistency'].values():
    if item['speaker'] == 'Xolotl':
        item.update(disposition='contextual', reason='本组仅一条例句，不能证明全文口吻；7372否定已修复，回应献祭的惊讶、接受提议与命令语气保留。')
    elif item['disposition'] == 'sample_only_not_full_voice_validation':
        item['disposition'] = 'contextual'
notes['report_hash'] = report['report_hash']
notes['status'] = 'read_and_scoped_repair_accepted_for_pilot_only'
notes['external_evidence']['14164'] = {
    'url': 'https://www.vatican.va/content/catechism/en/part_one/section_two/chapter_two/artcile_3.html',
    'scope': 'Catechism 461 Incarnation概念，未据此改写游戏历史', 'checked': '2026-10-15'}
decisions = []
by_id = {r['id']: r for r in report['records_to_check']}
for record_id in report['required_decisions']:
    if record_id in by_id:
        observation = notes['records'][str(by_id[record_id]['ordinal'])]
    elif record_id in notes['consistency']:
        observation = notes['consistency'][record_id]
    elif record_id == 'G:review_changes':
        observation = notes['glossary']
    else:
        raise ValueError('Requested check has not been read: '+record_id)
    if observation['disposition'] not in ('pass', 'contextual') or not observation['reason']:
        raise ValueError('Unresolved read observation: '+record_id)
    decisions.append({'id': record_id, 'disposition': observation['disposition'], 'reason': observation['reason']})
assert len(notes['records']) == 150
out = {'report_hash': report['report_hash'], 'reviewer': 'sol',
       'summary': '实际阅读150条源译、独立审校证据、32个角色样本组及冻结术语变化。只对11条集中修订并由另一实例复核，其余139条保持原有结果。否定、施受关系、球赛主体、动态变量和百科夫妻关系关键问题已解决。接受该代表样本作为历史冒险战术RPG文体校准，不宣称覆盖全文角色或实机字体排版。角色单例组仅限样本观察；普通词与冻结技能词的语境例外须继续逐条说明。13469例外理由残留、少量措辞和建筑别名统一记为非阻断审校注意项，不把程序通过等同全文质量通过。',
       'decisions': decisions}
notes_path.write_text(json.dumps(notes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(root / 'reports/pilot_sol_decisions.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'decisions': len(decisions), 'report_hash': report['report_hash']}))
