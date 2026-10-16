"""Back up and deploy only the hash-verified supported-build payload."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = (ROOT / 'Game').resolve()
BACKUP = ROOT / 'Repack/Backup/SteamBuild1752467'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    running = subprocess.run(['powershell','-NoProfile','-Command',"if (Get-Process 'Expeditions Conquistador' -ErrorAction SilentlyContinue) { exit 1 }"],check=False)
    assert running.returncode == 0, 'Exit the game before deploying; no files changed'
    assets = json.loads((ROOT / 'Repack/reports/assets_build.json').read_text('utf-8'))
    managed = json.loads((ROOT / 'Repack/reports/managed_build.json').read_text('utf-8'))
    manifest_path = ROOT / 'Repack/reports/payload_manifest.json'
    previous = {x['game_path']: x['sha256'] for x in json.loads(manifest_path.read_text('utf-8'))['files']} if manifest_path.exists() else {}
    files = [dict(x) for x in assets['files']]
    files += [{'game_path': 'Expeditions Conquistador_Data/Managed/Assembly-CSharp.dll',
               'source_sha256': managed['source_sha256'], 'sha256': managed['sha256']},
              {'game_path': 'Expeditions Conquistador_Data/Managed/ConquistadorChinese.dll',
               'source_sha256': None, 'sha256': managed['helper_sha256']}]
    # Validate the whole transaction before copying any game file.
    for item in files:
        rel = item['game_path']
        src = ROOT / 'Repack/Build/Game' / rel
        dst = GAME / rel
        assert digest(src) == item['sha256'], f'Build hash mismatch: {rel}'
        if dst.exists():
            assert digest(dst) in (item['source_sha256'], item['sha256'], previous.get(rel)), f'Unsupported installed file: {rel}'
        else:
            assert item['source_sha256'] is None
        if item['source_sha256'] is not None:
            backup = BACKUP / rel
            if backup.exists():
                assert digest(backup) == item['source_sha256']
            else:
                assert digest(dst) == item['source_sha256'], f'Original backup missing: {rel}'
    for item in files:
        rel = item['game_path']
        src = ROOT / 'Repack/Build/Game' / rel
        dst = GAME / rel
        if item['source_sha256'] is not None:
            backup = BACKUP / rel
            if not backup.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup)
        shutil.copy2(src, dst)
        assert digest(dst) == item['sha256']
        item['path'] = src.relative_to(ROOT).as_posix()
        print('installed', rel, flush=True)
    report = {'game_build': 'Steam 1752467 / game 1.6.6.1', 'platform': 'Steam Windows x86',
              'translation_sha256': assets['translation_sha256'], 'files': files}
    (ROOT / 'Repack/reports/payload_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
