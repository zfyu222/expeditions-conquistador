"""Decode the offline candidate against project backups; never install into Game."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=json.loads((ROOT/'Repack/reports/candidate_payload_manifest.json').read_text('utf-8'))
    kit=ROOT/'Repack/Build/CandidatePatchKit'
    patch=json.loads((kit/'ChinesePatch/patch_manifest.json').read_text('utf-8'))
    decoder=kit/patch['decoder_path']
    assert sha(decoder)==patch['decoder_sha256']
    outputs=[]
    for f in patch['files']:
        payload=kit/f['patch_path']; assert sha(payload)==f['patch_sha256']
        output=(ROOT/'Repack/Build/CandidateDecoded'/f['game_path']).resolve()
        assert output.is_relative_to((ROOT/'Repack/Build/CandidateDecoded').resolve())
        output.parent.mkdir(parents=True,exist_ok=True)
        if f['added']: shutil.copy2(payload,output)
        else:
            original=ROOT/'Repack/Backup/SteamBuild1752467'/f['game_path']
            assert sha(original)==f['source_sha256']
            subprocess.run([str(decoder),'-f','-d','-s',str(original),str(payload),str(output)],check=True)
        assert sha(output)==f['sha256']
        outputs.append({'game_path':f['game_path'],'sha256':sha(output),'status':'passed'})
        print('offline decode verified:',f['game_path'],flush=True)
    # Capture current installed hashes read-only, proving this candidate was not deployed.
    installed=json.loads((ROOT/'Repack/reports/payload_manifest.json').read_text('utf-8'))
    game=(ROOT/'Game').resolve()
    unchanged=all(sha(game/f['game_path'])==f['sha256'] for f in installed['files'])
    result={'status':'offline_checks_passed_runtime_pending','decode_outputs':outputs,
        'previous_installation_unchanged':unchanged,'candidate_installed':False,
        'required_next':['User exits game','Deploy candidate and preserve original backup','Retest old-save Citlalli biography and screenshot quest list','Check Chinese caption and scrolling in representative tutorial pages','Repeat player installer roundtrip for final kit','Record new in-game check before packaging or publication']}
    (ROOT/'Repack/reports/candidate_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('7 candidate outputs verified; installed game unchanged:',unchanged,flush=True)

if __name__=='__main__': main()
