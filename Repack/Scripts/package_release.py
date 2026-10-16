"""Package exactly the tested installation kit through the release skill."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    kit=json.loads((ROOT/'Repack/reports/patchkit_build.json').read_text('utf-8'))
    args=[sys.executable,str(ROOT.parents[1]/'.agents/skills/game-release-patch/scripts/create_release_patch.py'),
        '--project',str(ROOT),'--version','1.0','--game-name','expeditions-conquistador',
        '--introduction','为《Expeditions: Conquistador（远征：征服者）》Steam Windows 版制作的简体中文静态汉化补丁。无需额外汉化框架，运行时无需联网翻译。',
        '--coverage','已提取的14,691条剧情、对话、任务、人物传记、界面及场景文字；兼容旧存档中的英文任务和官方多语言人物传记。47页教程保留原图，另加中文说明。',
        '--game-version','Steam 1752467 / game 1.6.6.1','--platform','Steam Windows x86',
        '--install','先备份存档并完全退出游戏。将压缩包全部内容解压到游戏根目录（Expeditions Conquistador.exe 所在目录），保留 ChinesePatch 目录结构；运行“安装汉化.exe”，输入1并回车，等待显示“汉化安装完成”。游戏语言选择 English。安装器只接受对应原版文件哈希，自动把原文件备份到 ChinesePatch/Backup；请勿删除该备份。',
        '--uninstall','完全退出游戏后，运行同一“安装汉化.exe”，输入2并回车，等待显示“原版已还原”。确认恢复后，可移走“安装汉化.exe”和 ChinesePatch 目录。若备份丢失，可用 Steam 验证游戏文件恢复原版。',
        '--verification','已验证主菜单、首章多轮对话及分支推进；用户加载旧存档确认人物传记、任务和教程中文说明正常。最终载荷已通过纯净基线安装、还原、再次安装和重复安装四轮哈希测试。未进行全流程通关验证。',
        '--known-issues','原教程截图内的英文保留，中文说明位于图下方；过场视频文字未汉化。日期和程序身份姓名保留原文。固定尺寸界面在高分辨率下可能较小。未测试其他商店版本、其他系统、全部剧情分支、多人联机或 Steam 成就实际解锁；更新游戏后请先确认补丁兼容。']
    for f in kit['files']:args+=['--include',str(ROOT/f['path'])+'='+f['game_path']]
    if a.dry_run:args+=['--dry-run']
    subprocess.run(args,check=True)

if __name__=='__main__':main()
