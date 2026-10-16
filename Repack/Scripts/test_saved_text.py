"""Run the actual saved-text lookup implementation against screenshot regressions."""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'Repack/Build'
def main():
    entries=json.loads((ROOT/'Repack/reports/saved_display_map.json').read_text('utf-8'))['entries']
    maps={}
    for r in entries: maps.setdefault(r['table'],{})[r['source']]=r['translation']
    cases=[]
    for title in ('Return to Spain','The Feast','Conspiracy','Kill Moctezuma',"Take Moctezuma's Palace",'Clear the Causeway','Fortify','Stable Finished'):
        cases.append(('SavedTitle',title,maps['SavedTitles'][title]))
    bio=next(x for x in maps['SavedBios'] if x.startswith('Proud, fierce, and gorgeous'))
    cases.append(('SavedBio',bio,maps['SavedBios'][bio]))
    description=next(x for x in maps['SavedDescriptions'] if x.startswith('When you are ready to go home'))
    cases.append(('SavedDescription',description,maps['SavedDescriptions'][description]))
    for region in ('Mountains','Volcano'):
        cases.append(('SavedTitle','Chart the '+region,maps['SavedFragments']['Chart the ']+maps['SavedFragments'][region]))
    for count,total in ((9,10),(0,10),(10,10),(123,456)):
        original='Discovered %d out of %d cairns'%(count,total)
        expected=maps['SavedFragments']['Discovered ']+str(count)+maps['SavedFragments'][' out of ']+str(total)+maps['SavedFragments'][' cairns']
        cases.append(('SavedDescription',original,expected))
    for method in ('SavedTitle','SavedDescription','SavedBio'):
        cases.append((method,'Unknown user-created text','Unknown user-created text'))
    alias_path=ROOT/'Repack/reports/multilingual_bio_aliases.json'
    if alias_path.exists():
        aliases=json.loads(alias_path.read_text('utf-8'))['aliases']
        assert any(r['source'].startswith('Die schöne Bonita') for r in aliases), 'Screenshot regression must be covered'
        for r in aliases: cases.append(('SavedBio',r['source'],r['translation']))
    source='using System; using Zfy.Localization; class SavedTextSmoke { static void Main() { int n=0;\n'
    for method,original,expected in cases:
        source+='if(SavedDisplay.'+method+'('+json.dumps(original)+')!='+json.dumps(expected)+') throw new Exception("Case '+str(len(source))+' failed"); n++;\n'
    source+='Console.WriteLine("Saved text regressions: "+n+" passed"); }}'
    cs=BUILD/'SavedTextSmoke.cs';cs.write_text(source,encoding='utf-8')
    exe=BUILD/'SavedTextSmoke.exe'
    subprocess.run([r'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe','/noconfig','/nologo','/reference:System.dll','/out:'+str(exe),str(cs),str(ROOT/'Repack/Scripts/ChineseSavedText.cs'),str(BUILD/'ChineseSavedMap.cs')],check=True)
    run=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
    print(run.stdout,flush=True)
    (ROOT/'Repack/reports/saved_text_tests.json').write_text(json.dumps({'status':'passed','cases':len(cases),'scope':'Actual shared lookup source compiled for standalone CLR; target Mono game still needs runtime verification.','output':run.stdout},indent=2),encoding='utf-8')

if __name__=='__main__': main()
