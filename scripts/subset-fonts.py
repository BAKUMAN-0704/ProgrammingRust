#!/usr/bin/env python3
r"""按站点实际用到的字符，把 HarmonyOS Sans SC 与 JetBrains Mono 压成 woff2。

为什么需要这个脚本：
  完整的 HarmonyOS Sans SC 每个字重约 7.8 MB，五个字重接近 40 MB，
  放进仓库不现实。这里只保留站点正文 + 界面文案里出现过的字符，
  体积通常能压到原来的 1/10 甚至更小。

什么时候要重跑：
  新增章节、或正文里出现新汉字之后。跑一次即可，产物在
  .vitepress/theme/fonts/ 下，是构建产物的一部分，需要提交进仓库。

依赖：
  py -3 -m pip install fonttools brotli

用法：
  py -3 scripts/subset-fonts.py
  # 字体不在默认位置时用环境变量覆盖
  HARMONY_DIR=D:/fonts JETBRAINS_DIR=D:/fonts py -3 scripts/subset-fonts.py

为什么用 py -3 而不是 python：
  这台机器上 python 可能指向 WorkBuddy 内置的 3.13，pip 却指向 C:\Python314，
  两者不是同一个解释器，会出现“装完却 import 不到”。
  py -3 由 Windows 启动器解析，始终指向默认的 3.x，跨终端稳定。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "site-src"
CONFIG = ROOT / ".vitepress" / "config.mts"
OUT_DIR = ROOT / ".vitepress" / "theme" / "fonts"

HARMONY_DIR = Path(os.environ.get("HARMONY_DIR", r"C:\Users\BAKUMAN\AppData\Local\Microsoft\Windows\Fonts"))
JETBRAINS_DIR = Path(os.environ.get("JETBRAINS_DIR", r"C:\Users\BAKUMAN\AppData\Local\Microsoft\Windows\Fonts"))

# 字重 -> (源文件名, 输出文件名)
HARMONY_WEIGHTS = [
    (400, "HarmonyOS_Sans_SC_Regular.ttf", "harmonyos-sans-sc-400.woff2"),
    (500, "HarmonyOS_Sans_SC_Medium.ttf", "harmonyos-sans-sc-500.woff2"),
    (700, "HarmonyOS_Sans_SC_Bold.ttf", "harmonyos-sans-sc-700.woff2"),
]

JETBRAINS_WEIGHTS = [
    (400, "JetBrainsMonoNerdFontMono-Regular.ttf", "jetbrainsmono-nf-400.woff2"),
    (700, "JetBrainsMonoNerdFontMono-Bold.ttf", "jetbrainsmono-nf-700.woff2"),
]

# 界面文案兜底：VitePress 自带的中文 UI 里可能出现的字
UI_FALLBACK = (
    "目录本页回到顶部上下一最后更新主题搜索菜单外观深色浅色模式切换复制代码已"
    "在GitHub编辑此页跳转到按进行加载中正在失败重试返回关闭展开收起更多显示隐藏"
    "全部文章导航侧边栏外部链接新窗口打开无内容未找到页面"
)

PUNCTUATION = "，。、；：？！“”‘’（）【】《》〈〉—…·　％＃＆＊＋－／＝"


def require_deps() -> None:
    """依赖缺失时，直接告诉用户该给哪个解释器装包。"""
    missing = [m for m in ("fontTools", "brotli") if not _has_module(m)]
    if not missing:
        return
    exe = sys.executable
    sys.exit(
        f"缺少依赖：{', '.join(missing)}\n"
        f"当前解释器：{exe}\n"
        f'安装命令："{exe}" -m pip install fonttools brotli\n'
        f"（用 py -3 启动的话：py -3 -m pip install fonttools brotli）"
    )


def _has_module(name: str) -> bool:
    try:
        __import__(name)
    except ImportError:
        return False
    return True


def collect_text() -> str:
    """收齐所有会被渲染出来的字符。"""
    chars: set[str] = set()

    if not SRC_DIR.is_dir():
        sys.exit(f"找不到 {SRC_DIR}，请先运行 npm run dev 或 npm run build 生成 markdown")

    for md in sorted(SRC_DIR.glob("*.md")):
        chars.update(md.read_text(encoding="utf-8"))

    # 侧边栏、页脚等界面文案写在配置里，不在 markdown 里
    if CONFIG.is_file():
        chars.update(CONFIG.read_text(encoding="utf-8"))

    chars.update(UI_FALLBACK)
    chars.update(PUNCTUATION)
    chars.update(chr(c) for c in range(0x20, 0x7F))

    # 去掉空白、控制字符，以及配置里的代码符号（用不到那么多）
    return "".join(sorted(c for c in chars if ord(c) >= 0x20 and not c.isspace()))


def collect_mono() -> str:
    """等宽字体只需覆盖代码字符：ASCII、制表符、常用符号与箭头。"""
    chars = {chr(c) for c in range(0x20, 0x7F)}
    for lo, hi in ((0x2500, 0x257F), (0x2190, 0x21FF), (0x2502, 0x2502), (0x2026, 0x2026)):
        chars.update(chr(c) for c in range(lo, hi + 1))
    chars.update("→←↑↓✓✗⚠─│┌┐└┘├┤┬┴┼█▌▐░▒▓")
    return "".join(sorted(chars))


def subset(src: Path, dst: Path, text_path: Path, *, keep_ligatures: bool) -> None:
    if not src.is_file():
        sys.exit(f"找不到字体文件：{src}")
    cmd = [
        sys.executable, "-m", "fontTools.subset", str(src),
        f"--text-file={text_path}",
        f"--output-file={dst}",
        "--flavor=woff2",
        "--no-hinting",
        "--desubroutinize",
        "--name-IDs=1,2,3,4,6",
        "--drop-tables+=FFTM,PfEd",
    ]
    if keep_ligatures:
        # 等宽字体保留连字（->、=>、!= 这些在代码里会合并显示）
        cmd.append("--layout-features=*")
    subprocess.run(cmd, check=True)


def main() -> None:
    require_deps()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / ".font-charset.txt"
    tmp_mono = ROOT / ".font-charset-mono.txt"

    text = collect_text()
    tmp.write_text(text, encoding="utf-8")
    print(f"正文用字：{len(text)} 个不同字符")

    mono = collect_mono()
    tmp_mono.write_text(mono, encoding="utf-8")

    for weight, name, out in HARMONY_WEIGHTS:
        subset(HARMONY_DIR / name, OUT_DIR / out, tmp, keep_ligatures=False)
        size = (OUT_DIR / out).stat().st_size / 1024
        print(f"  HarmonyOS Sans SC {weight}  ->  {out}  {size:.0f} KB")

    for weight, name, out in JETBRAINS_WEIGHTS:
        subset(JETBRAINS_DIR / name, OUT_DIR / out, tmp_mono, keep_ligatures=True)
        size = (OUT_DIR / out).stat().st_size / 1024
        print(f"  JetBrains Mono NF {weight}  ->  {out}  {size:.0f} KB")

    tmp.unlink(missing_ok=True)
    tmp_mono.unlink(missing_ok=True)

    total = sum(p.stat().st_size for p in OUT_DIR.glob("*.woff2")) / 1024 / 1024
    print(f"完成，共 {total:.2f} MB，输出目录 {OUT_DIR}")


if __name__ == "__main__":
    main()
