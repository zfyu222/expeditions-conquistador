"""Exercise the exact player installer on the supported installation, then verify hashes."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = (ROOT / 'Game').resolve()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def under(root, rel):
    path = (root / rel).resolve()
    assert path.is_relative_to(root.resolve()), rel
    return path

def main():
    check = subprocess.run(['powershell', '-NoProfile', '-Command',
        "if (Get-Process 'Expeditions Conquistador' -ErrorAction SilentlyContinue) { exit 1 }"], check=False)
    assert check.returncode == 0, 'Exit the game before testing'
    report = json.loads((ROOT / 'Repack/reports/patchkit_build.json').read_text('utf-8'))
    files = report['installed_outputs']
    # Verify every installed file and every original backup before restoring.
    for f in files:
        current = under(GAME, f['game_path'])
        assert (sha(current) in (f['sha256'], f['source_sha256'])) if current.exists() else f['source_sha256'] is None
        if f['source_sha256']:
            assert sha(under(ROOT / 'Repack/Backup/SteamBuild1752467', f['game_path'])) == f['source_sha256']
    for f in files:
        dest = under(GAME, f['game_path'])
        if f['source_sha256']:
            shutil.copy2(ROOT / 'Repack/Backup/SteamBuild1752467' / f['game_path'], dest)
        else:
            if dest.exists(): dest.unlink()
    for f in report['files']:
        src, dst = ROOT / f['path'], under(GAME, f['game_path'])
        assert sha(src) == f['sha256']
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    results = []
    for action, installed in [('--install', True), ('--uninstall', False), ('--install', True), ('--install', True)]:
        run = subprocess.run([str(GAME / '安装汉化.exe'), action, '--game-root', str(GAME)],
                             capture_output=True, encoding='utf-8', errors='replace')
        assert run.returncode == 0, run.stdout + run.stderr
        for f in files:
            dest = under(GAME, f['game_path'])
            expected = f['sha256'] if installed else f['source_sha256']
            assert sha(dest) == expected if expected else not dest.exists(), f['game_path']
        results.append({'action': action, 'status': 'pass', 'outputs_verified': len(files), 'output': run.stdout})
        print(action, 'passed:', len(files), 'file hashes', flush=True)
    result = {'status': 'pass', 'tests': results, 'kit_files': report['files'], 'installed_outputs': files}
    (ROOT / 'Repack/reports/installer_test.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
