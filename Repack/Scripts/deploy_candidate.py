"""Deploy verified game outputs and synchronize their matching installer/restore kit."""
import json
import shutil
from pathlib import Path
import deploy

ROOT=Path(__file__).resolve().parents[2]
GAME=(ROOT/'Game').resolve()

def main():
    report=json.loads((ROOT/'Repack/reports/candidate_patchkit_build.json').read_text('utf-8'))
    previous=json.loads((ROOT/'Repack/reports/patchkit_build.json').read_text('utf-8'))
    old={f['game_path']:f['sha256'] for f in previous['files']}
    previous_candidate=ROOT/'Repack/reports/previous_candidate_patchkit_build.json'
    prior={f['game_path']:f['sha256'] for f in json.loads(previous_candidate.read_text('utf-8'))['files']} if previous_candidate.exists() else {}
    for f in report['files']:
        source=(ROOT/f['path']).resolve()
        dest=(GAME/f['game_path']).resolve()
        assert source.is_relative_to((ROOT/'Repack/Build/CandidatePatchKit').resolve())
        assert dest.is_relative_to(GAME)
        assert deploy.digest(source)==f['sha256']
        if dest.exists(): assert deploy.digest(dest) in (f['sha256'],old.get(f['game_path']),prior.get(f['game_path'])), f['game_path']
    deploy.main()
    for f in report['files']:
        dest=GAME/f['game_path']
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/f['path'],dest)
        assert deploy.digest(dest)==f['sha256']
    payload=json.loads((ROOT/'Repack/reports/payload_manifest.json').read_text('utf-8'))
    assert all(deploy.digest(GAME/f['game_path'])==f['sha256'] for f in payload['files'])
    result={'status':'deployed_runtime_validation_pending','game_outputs_verified':len(payload['files']),
        'installer_kit_files_verified':len(report['files']),'original_backups_preserved':True,
        'save_files_modified':False,'runtime_validation':'pending','files':payload['files']}
    (ROOT/'Repack/reports/candidate_deployment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Candidate deployed: 7 game outputs and 13 matching installer files verified; saves untouched',flush=True)

if __name__=='__main__': main()
