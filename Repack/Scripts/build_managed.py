"""Build the independent Unity-compatible helper and patch the original managed assembly."""
import json
import csv
import re
import hashlib
import shutil
import subprocess
import xml.etree.ElementTree as ET
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'Repack/Build'
DATA = ROOT / 'Game/Expeditions Conquistador_Data/Managed'

def main():
    assets=json.loads((ROOT/'Repack/reports/assets_build.json').read_text('utf-8'))
    assert hashlib.sha256((ROOT/'expeditions-conquistador_text_translated.csv').read_bytes()).hexdigest()==assets['translation_sha256'], 'Formal translation changed; revalidate before building'
    records = json.loads((BUILD / 'managed_map.json').read_text('utf-8'))
    mapping = {}
    for r in records:
        assert r['text'] not in mapping or mapping[r['text']] == r['translation']
        mapping[r['text']] = r['translation']
    content = 'using System.Collections.Generic;\nnamespace Zfy.Localization { public static partial class ChineseLayout {\n'
    content += 'static readonly Dictionary<string,string> DisplayMap = new Dictionary<string,string> {\n'
    content += ''.join('{'+json.dumps(k)+','+json.dumps(v)+'},\n' for k,v in sorted(mapping.items()))
    content += '};\npublic static string Localize(string text) { string value; return text != null && DisplayMap.TryGetValue(text,out value) ? value : text; }\n}}\n'
    generated = BUILD / 'ChineseDisplayMap.cs'
    generated.write_text(content, encoding='utf-8')
    source_records = json.loads((ROOT/'Analysis/text_mapping.json').read_text('utf-8'))
    with (ROOT/'expeditions-conquistador_text_translated.csv').open(encoding='utf-8-sig',newline='') as f:
        translations = [r[0] for r in csv.reader(f)]
    tables = {'SavedTitles':{}, 'SavedDescriptions':{}, 'SavedBios':{}, 'SavedFragments':{}}
    provenance = []
    for r,translation in zip(source_records,translations):
        xpath = r.get('xpath','')
        table = None
        if re.search(r'/Goal\[\d+\]/Title\[\d+\]$',xpath): table='SavedTitles'
        elif re.search(r'/Goal\[\d+\]/Description\[\d+\]$',xpath): table='SavedDescriptions'
        elif r.get('field')=='Bio': table='SavedBios'
        elif r.get('asset_name')=='GUI-en': table='SavedFragments'
        if table and r['text'] not in tables[table]:
            tables[table][r['text']] = translation
            provenance.append({'table':table,'row':r['row'],'source':r['text'],'translation':translation})
    # Old saves may serialize a different official language into the generic Bio field.
    # Match exact foreign strings by the original character identity, never by position.
    def identity(node):
        name='|'.join((node.findtext(tag) or '').strip() for tag in ('GivenName','FamilyName'))
        return ''.join(c for c in unicodedata.normalize('NFD',name).casefold() if not unicodedata.combining(c))
    english_bios={}
    for filename in ('772_Level0.txt','793_Level1.txt','781_RandomEvents.txt'):
        root=ET.fromstring((ROOT/'Analysis/textassets/sharedassets1.assets'/filename).read_bytes().decode('utf-8-sig'))
        for node in root.iter('FollowerAdd'):
            bio=node.findtext('Bio')
            if bio in tables['SavedBios']:
                english_bios.setdefault(identity(node),set()).add(bio)
    inventory=json.loads((ROOT/'Analysis/textasset_inventory.json').read_text('utf-8'))
    alias_report=[]
    for entry in inventory:
        if entry['asset_file']!='sharedassets1.assets' or not entry['name'].startswith(('Level0','Level1','RandomEvents')): continue
        path=ROOT/entry['export']
        raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==entry['sha256'], 'Original XML export changed'
        root=ET.fromstring(raw.decode('utf-8-sig'))
        for node in root.iter('FollowerAdd'):
            bio=node.findtext('Bio'); candidates=english_bios.get(identity(node),set())
            if not bio or bio in tables['SavedBios'] or len(candidates)!=1: continue
            english=next(iter(candidates)); translated=tables['SavedBios'][english]
            tables['SavedBios'][bio]=translated
            alias_report.append({'source_export':entry['export'],'identity':identity(node),'source':bio,'english_source':english,'translation':translated})
    (ROOT/'Repack/reports/multilingual_bio_aliases.json').write_text(json.dumps({'aliases':alias_report,'count':len(alias_report),'policy':'Exact official localized Bio matched by unambiguous GivenName/FamilyName to an already reviewed English Bio; no new translation.'},ensure_ascii=False,indent=2),encoding='utf-8')
    saved = 'using System.Collections.Generic;\nnamespace Zfy.Localization { public static partial class SavedDisplay {\n'
    for table,values in tables.items():
        saved += 'static readonly Dictionary<string,string> '+table+' = new Dictionary<string,string> {\n'
        saved += ''.join('{'+json.dumps(k)+','+json.dumps(v)+'},\n' for k,v in sorted(values.items()))
        saved += '};\n'
    saved += '}}\n'
    saved_map = BUILD/'ChineseSavedMap.cs'
    saved_map.write_text(saved,encoding='utf-8')
    tutorial_root=ROOT/'TranslateFiles/tutorial_supplement'
    assert (tutorial_root/'acceptance.json').exists(), 'New tutorial captions require independent acceptance'
    accepted=json.loads((tutorial_root/'acceptance.json').read_text('utf-8'))
    assert accepted['status']=='passed' and accepted['new_records']==48
    captions=json.loads((tutorial_root/'tutorial_captions_reviewed.json').read_text('utf-8'))
    assert len(captions)==48
    caption_hash=hashlib.sha256(json.dumps(captions,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    assert caption_hash==accepted['output_hash'], 'Supplemental caption acceptance is stale'
    tutorial_map=BUILD/'ChineseTutorialMap.cs'
    tutorial_code='using System.Collections.Generic;\nnamespace Zfy.Localization { public static partial class ChineseLayout {\n'
    tutorial_code+='static readonly Dictionary<string,string> TutorialCaptions=new Dictionary<string,string> {\n'
    tutorial_code+=''.join('{'+json.dumps(r['name'])+','+json.dumps(r['translation'])+'},\n' for r in captions)
    tutorial_map.write_text(tutorial_code+'};\n}}\n',encoding='utf-8')
    (ROOT/'Repack/reports/saved_display_map.json').write_text(json.dumps({'duplicate_policy':'First previously reviewed CSV row for identical source within the same display field; no CSV translations modified.','entries':provenance},ensure_ascii=False,indent=2),encoding='utf-8')
    helper = BUILD / 'ConquistadorChinese.dll'
    csc = Path(r'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe')
    subprocess.run([str(csc), '/noconfig', '/nologo', '/utf8output', '/target:library', '/nostdlib',
        '/out:'+str(helper), '/reference:'+str(DATA/'mscorlib.dll'), '/reference:'+str(DATA/'System.dll'), '/reference:'+str(DATA/'UnityEngine.dll'),
        str(ROOT/'Repack/Scripts/ChineseLayout.cs'), str(ROOT/'Repack/Scripts/ChineseSavedText.cs'),
        str(ROOT/'Repack/Scripts/ChineseTutorials.cs'),str(tutorial_map),str(generated),str(saved_map)], check=True)
    subprocess.run(['dotnet','build', str(ROOT/'Repack/Scripts/Patcher/Patcher.csproj'), '-c','Release','-o',str(BUILD/'Patcher'),'--nologo'],check=True)
    original = ROOT/'Repack/Backup/SteamBuild1752467/Expeditions Conquistador_Data/Managed/Assembly-CSharp.dll'
    if not original.exists(): original = DATA/'Assembly-CSharp.dll'
    target = BUILD/'Game/Expeditions Conquistador_Data/Managed'
    target.mkdir(parents=True,exist_ok=True)
    subprocess.run(['dotnet',str(BUILD/'Patcher/Patcher.dll'),str(original),str(helper),str(BUILD/'managed_map.json'),
        str(target/'Assembly-CSharp.dll'),str(ROOT/'Repack/reports/managed_build.json')],check=True)
    shutil.copy2(helper,target/helper.name)

if __name__ == '__main__': main()
