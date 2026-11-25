"""Publish a committed project snapshot while keeping user-provided screenshots local.

The original project history and working tree are preserved. The public repository
gets an independent snapshot history, avoiding disclosure through older commits.
"""
import argparse
import io
import subprocess
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'Repack/Build/PublicRepository'
PRIVATE={
    'Repack/Evidence/14-user-biography.jpg','Repack/Evidence/15-user-tutorial.jpg',
    'Repack/Evidence/16-user-quests.jpg','Repack/Evidence/17-user-german-biography.jpg'}
COVER={'Dispatch/Artwork/title.jpg','Dispatch/Artwork/source.json'}
def run(args,cwd=ROOT):return subprocess.run(args,cwd=cwd,check=True,capture_output=True,text=True,encoding='utf-8',errors='replace').stdout.strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--remote',required=True);p.add_argument('--message',required=True);p.add_argument('--push',action='store_true');a=p.parse_args()
    assert a.remote=='https://github.com/zfyu222/expeditions-conquistador.git'
    assert not run(['git','ls-files','Game']) and run(['git','check-ignore','Game'])=='Game'
    PUBLIC.mkdir(parents=True,exist_ok=True)
    archive=subprocess.run(['git','archive','--format=tar','HEAD'],cwd=ROOT,check=True,capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        cover_files=[]
        for item in tar:
            if not item.isfile() or item.name in PRIVATE:continue
            if item.name.startswith('Dispatch/'):
                if item.name not in COVER:continue
                cover_files.append(item.name)
            dest=(PUBLIC/item.name).resolve()
            assert dest.is_relative_to(PUBLIC.resolve()) and item.size<50_000_000
            assert not item.name.startswith(('Game/','Repack/Build/','Repack/Backup/'))
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(tar.extractfile(item).read())
    if not (PUBLIC/'.git').exists():
        run(['git','init','-b','main'],PUBLIC)
        for key in ('user.name','user.email'):run(['git','config',key,run(['git','config',key])],PUBLIC)
        run(['git','remote','add','origin',a.remote],PUBLIC)
    assert run(['git','remote','get-url','origin'],PUBLIC)==a.remote
    run(['git','add','--all'],PUBLIC)
    if cover_files:run(['git','add','-f','--',*cover_files],PUBLIC)
    if run(['git','status','--porcelain'],PUBLIC):print(run(['git','commit','-m',a.message],PUBLIC).splitlines()[0])
    if a.push:print(run(['git','push','origin','main'],PUBLIC))
    print('Public snapshot:',run(['git','rev-parse','HEAD'],PUBLIC),flush=True)

if __name__=='__main__':main()
