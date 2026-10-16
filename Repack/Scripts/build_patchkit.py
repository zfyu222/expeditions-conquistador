"""Generate binary-only differences; never distribute original game resources."""
import hashlib
import json
import shutil
import subprocess
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT.parents[1]/'Tools'
XDELTA=TOOLS/'xdelta3/v3.2.2/xdelta3-3.2.2-windows-x86_64'
KIT=ROOT/'Repack/Build/PatchKit'
BACKUP=ROOT/'Repack/Backup/SteamBuild1752467'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    global KIT
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate',action='store_true',help='Build offline candidate, retaining the previously tested kit')
    args=parser.parse_args()
    if args.candidate: KIT=ROOT/'Repack/Build/CandidatePatchKit'
    name='candidate_payload_manifest.json' if args.candidate else 'payload_manifest.json'
    payload=json.loads((ROOT/'Repack/reports'/name).read_text('utf-8'))
    directory=KIT/'ChinesePatch'
    (directory/'deltas').mkdir(parents=True,exist_ok=True)
    (directory/'files').mkdir(exist_ok=True)
    (directory/'tools').mkdir(exist_ok=True)
    (directory/'Licenses').mkdir(exist_ok=True)
    decoder=directory/'tools/xdelta3decode.exe'
    # Full binary is required: the small decoder omits LZMA secondary compression.
    shutil.copy2(XDELTA/'xdelta3.exe',decoder)
    manifest={'game_version':payload['game_build'],'platform':payload['platform'],
              'translation_sha256':payload['translation_sha256'],
              'decoder_path':'ChinesePatch/tools/xdelta3decode.exe','decoder_sha256':sha(decoder),'files':[]}
    for file in payload['files']:
        source=ROOT/file['path']
        assert sha(source)==file['sha256']
        item={k:file[k] for k in ('game_path','source_sha256','sha256')}
        item['added']=file['source_sha256'] is None
        if item['added']:
            output=directory/'files/ConquistadorChinese.dll'
            shutil.copy2(source,output)
        else:
            original=BACKUP/file['game_path']
            assert sha(original)==file['source_sha256']
            output=directory/'deltas'/(Path(file['game_path']).name+'.vcdiff')
            subprocess.run([str(XDELTA/'xdelta3.exe'),'-f','-e','-9','-A','-s',str(original),str(source),str(output)],check=True)
        item['patch_path']=output.relative_to(KIT).as_posix()
        item['patch_sha256']=sha(output)
        manifest['files'].append(item)
        print('delta ready',output.name,output.stat().st_size,flush=True)
    for file in (ROOT/'Repack/Licenses').glob('*.txt'):
        shutil.copy2(file,directory/'Licenses'/file.name)
    (directory/'patch_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    csc=Path(r'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe')
    subprocess.run([str(csc),'/noconfig','/nologo','/utf8output','/target:exe','/reference:System.dll','/reference:System.Core.dll',
        '/reference:System.Web.Extensions.dll','/out:'+str(KIT/'安装汉化.exe'),str(ROOT/'Repack/Scripts/PatchInstaller.cs')],check=True)
    files=[{'path':p.relative_to(ROOT).as_posix(),'game_path':p.relative_to(KIT).as_posix(),'sha256':sha(p),'size':p.stat().st_size}
           for p in sorted(KIT.rglob('*')) if p.is_file()]
    report={'patch_format':'VCDIFF / xdelta 3.2.2','files':files,'total_bytes':sum(f['size'] for f in files),
            'installed_outputs':payload['files']}
    report['status']='candidate_pending_runtime_validation' if args.candidate else 'built'
    report_name='candidate_patchkit_build.json' if args.candidate else 'patchkit_build.json'
    if args.candidate and (ROOT/'Repack/reports'/report_name).exists():
        previous=ROOT/'Repack/reports/previous_candidate_patchkit_build.json'
        if not previous.exists(): shutil.copy2(ROOT/'Repack/reports'/report_name,previous)
    (ROOT/'Repack/reports'/report_name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('patch kit passed',len(files),'files,',report['total_bytes'],'bytes',flush=True)

if __name__=='__main__': main()
