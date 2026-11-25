"""Package the verified Conquistador difference installer and its exact payload."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release-date', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    kit = json.loads((ROOT / 'Repack/reports/candidate_patchkit_build.json').read_text('utf-8'))
    manifest = json.loads((ROOT / 'Repack/Build/CandidatePatchKit/ChinesePatch/patch_manifest.json').read_text('utf-8'))
    command = [
        sys.executable, str(ROOT.parents[1] / '.agents/skills/game-release-patch/scripts/create_release_patch.py'),
        '--project', str(ROOT), '--version', manifest['patch_version'],
        '--release-date', args.release_date,
        '--chinese-name', '远征：征服者', '--english-name', 'Expeditions: Conquistador',
        '--steam-url', 'https://store.steampowered.com/app/237430/',
        '--download-url', 'https://github.com/zfyu222/expeditions-conquistador/releases/',
        '--mirror-url', 'https://pan.baidu.com/s/5a1u7wfYfZ30XA-OZ6oU8cA', '--share-name', '百度网盘',
        '--introduction', '这是一款以十六世纪西班牙远征美洲为背景的回合制策略角色扮演游戏。玩家招募并培养队员、安排营地工作和补给，在岛屿与丛林中探索，通过外交选择和战术战斗推动两段战役。',
        '--coverage', '剧情、对话、任务、人物传记、界面及场景文字，教程附中文说明。',
        '--game-version', manifest['game_version'], '--platform', manifest['platform'],
        '--install', '解压到 Expeditions Conquistador.exe 所在目录，运行“安装汉化.exe”并输入 1，游戏语言选择 English。',
        '--upgrade', '将新版补丁覆盖解压到游戏目录，运行“安装汉化.exe”并输入 1。',
        '--uninstall', '运行“安装汉化.exe”并输入 2。',
        '--changes', '全文润色，增量复审后更新 1,246 条译文，支持从 v1.0 直接升级。',
    ]
    for item in kit['files']:
        command.extend(['--include', str(ROOT / item['path']) + '=' + item['game_path']])
    if args.dry_run:
        command.append('--dry-run')
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
