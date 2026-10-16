"""Prepare an offline payload manifest without touching the running game."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def main():
    assets=json.loads((ROOT/'Repack/reports/assets_build.json').read_text('utf-8'))
    managed=json.loads((ROOT/'Repack/reports/managed_build.json').read_text('utf-8'))
    files=[dict(r) for r in assets['files']]
    files += [{'game_path':'Expeditions Conquistador_Data/Managed/Assembly-CSharp.dll','source_sha256':managed['source_sha256'],'sha256':managed['sha256']},
              {'game_path':'Expeditions Conquistador_Data/Managed/ConquistadorChinese.dll','source_sha256':None,'sha256':managed['helper_sha256']}]
    for f in files:
        path=ROOT/'Repack/Build/Game'/f['game_path']
        assert path.resolve().is_relative_to((ROOT/'Repack/Build/Game').resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']
        f['path']=path.relative_to(ROOT).as_posix()
        f['size']=path.stat().st_size
    report={'status':'candidate_pending_runtime_validation','game_build':'Steam 1752467 / game 1.6.6.1',
            'platform':'Steam Windows x86','translation_sha256':assets['translation_sha256'],'files':files,
            'supplement_acceptance':'TranslateFiles/tutorial_supplement/acceptance.json','installed':False}
    (ROOT/'Repack/reports/candidate_payload_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Offline candidate prepared: 7 files; game installation unchanged',flush=True)

if __name__=='__main__': main()
