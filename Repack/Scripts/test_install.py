"""Exercise the exact player installer on the supported installation, then verify hashes."""
import hashlib
import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = (ROOT / 'Game').resolve()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def under(root, rel):
    path = (root / rel).resolve()
    assert path.is_relative_to(root.resolve()), rel
    return path

def test_isolated_upgrade(legacy_zip):
    report = json.loads((ROOT / 'Repack/reports/candidate_patchkit_build.json').read_text('utf-8'))
    files = report['installed_outputs']
    executable = 'Expeditions Conquistador.exe'
    installer = '安装汉化.exe'
    tests = []
    with tempfile.TemporaryDirectory(dir=ROOT / 'Repack/Build', prefix='安装与升级-') as directory:
        game = Path(directory)
        shutil.copy2(GAME / executable, game / executable)
        marker = game / 'player-settings.keep'
        marker.write_bytes(b'settings to preserve')
        with zipfile.ZipFile(legacy_zip) as package:
            previous = json.loads(package.read('ChinesePatch/patch_manifest.json'))
            legacy_files = {item['game_path']: item['sha256'] for item in previous['files']}
            for name in [installer, 'ChinesePatch/patch_manifest.json', previous['decoder_path'],
                         *(item['patch_path'] for item in previous['files'])]:
                dest = under(game, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(package.read(name))
        originals = {item['game_path']: item['source_sha256'] for item in files}
        current = {item['game_path']: item['sha256'] for item in files}
        for name, original in originals.items():
            if original:
                source = under(ROOT / 'Repack/Backup/SteamBuild1752467', name)
                assert sha(source) == original
                dest = under(game, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)

        def exercise(label, operation, expected, returncode=0):
            run = subprocess.run([str(game / installer), operation, '--game-root', str(game)],
                                 capture_output=True, encoding='utf-8', errors='replace', timeout=180)
            assert run.returncode == returncode, run.stdout + run.stderr
            for name, digest in expected.items():
                target = under(game, name)
                assert sha(target) == digest if digest else not target.exists(), name
            assert marker.read_bytes() == b'settings to preserve'
            tests.append({'case': label, 'status': 'pass', 'outputs_verified': len(expected)})
            print(label, 'passed', flush=True)

        exercise('install v1.0', '--install', legacy_files)
        for item in report['files']:
            source = under(ROOT, item['path'])
            assert sha(source) == item['sha256']
            dest = under(game, item['game_path'])
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        exercise('upgrade v1.0 to v1.1', '--install', current)
        exercise('repeat v1.1 installation', '--install', current)
        exercise('uninstall v1.1', '--uninstall', originals)
        exercise('clean v1.1 installation', '--install', current)
        exercise('restore clean baseline', '--uninstall', originals)
        corrupt = under(game, previous['files'][0]['patch_path'])
        corrupt.write_bytes(b'damaged patch data')
        exercise('reject damaged payload and preserve originals', '--install', originals, returncode=1)
    result = {'status': 'pass', 'tests': tests, 'kit_files': report['files'], 'installed_outputs': files}
    (ROOT / 'Repack/reports/installer_v1.1_test.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--isolated-upgrade-from', type=Path)
    args = parser.parse_args()
    if args.isolated_upgrade_from:
        test_isolated_upgrade(args.isolated_upgrade_from)
        return
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
