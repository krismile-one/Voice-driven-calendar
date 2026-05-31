"""
一键环境配置脚本

检查并安装所有依赖：
    python setup.py          仅检查
    python setup.py --fix    自动修复可自动处理的问题
"""

import io
import os
import sys
import shutil
import subprocess
import platform

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


# ══════════════════════════════════════════════════════
# 检查项
# ══════════════════════════════════════════════════════

def check_python() -> tuple[bool, str]:
    """检查 Python 版本 >= 3.11"""
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 11
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def check_ffmpeg() -> tuple[bool, str]:
    """检查 ffmpeg 是否可用（Web 录音转码必需）"""
    path = shutil.which("ffmpeg")
    if path:
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
            ver = r.stdout.splitlines()[0].split("version")[-1].strip().split()[0] if r.stdout else "?"
            return True, f"{path}  (v{ver})"
        except Exception:
            return True, path
    return False, "未找到"


def check_uv() -> tuple[bool, str]:
    """检查 uv 包管理器"""
    path = shutil.which("uv")
    if path:
        try:
            r = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=10)
            ver = r.stdout.strip().split()[1] if r.stdout else "?"
            return True, ver
        except Exception:
            return True, path
    return False, "未找到"


def check_env_file() -> tuple[bool, str]:
    """检查 .env 配置文件"""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        # 快速检查关键 key 是否已填写
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        missing = []
        for key in ["ASR_API_KEY", "LLM_API_KEY"]:
            for line in content.splitlines():
                if line.startswith(f"{key}=") and line.strip() == f"{key}=":
                    missing.append(key)
                    break
        if missing:
            return True, f"存在，但缺少: {', '.join(missing)}"
        return True, "已配置"
    return False, "不存在"


def check_python_deps() -> tuple[bool, str]:
    """检查 Python 依赖是否已安装"""
    try:
        import fastapi, uvicorn, sqlalchemy
        return True, "核心依赖已安装"
    except ImportError as e:
        return False, f"缺少依赖: {e.name if hasattr(e, 'name') else e}"


# ══════════════════════════════════════════════════════
# 自动修复
# ══════════════════════════════════════════════════════

def fix_env_file():
    """从 .env.example 复制 .env"""
    src = os.path.join(PROJECT_ROOT, ".env.example")
    dst = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(dst):
        shutil.copy(src, dst)
        print(f"     ✅ 已创建 .env（从 .env.example 复制）")
        print(f"     ⚠️  请编辑 .env 填入 ASR_API_KEY 和 LLM_API_KEY")
    else:
        print(f"     ·  .env 已存在，跳过")


def fix_python_deps():
    """运行 uv sync 安装 Python 依赖"""
    print(f"     ⏳ 运行 uv sync ...")
    try:
        subprocess.run(["uv", "sync"], cwd=PROJECT_ROOT, check=True)
        print(f"     ✅ Python 依赖安装完成")
    except subprocess.CalledProcessError:
        print(f"     ❌ uv sync 失败，请手动运行")
    except FileNotFoundError:
        print(f"     ❌ 未找到 uv，请先安装: pip install uv")


# ══════════════════════════════════════════════════════
# 安装指引
# ══════════════════════════════════════════════════════

FFMPEG_INSTALL_GUIDE = {
    "Windows": '    winget install ffmpeg\n    或下载: https://ffmpeg.org/download.html',
    "Darwin":  '    brew install ffmpeg',
    "Linux":   '    sudo apt install ffmpeg        (Debian/Ubuntu)\n    sudo dnf install ffmpeg-free   (Fedora)',
}

UV_INSTALL_GUIDE = {
    "Windows": '    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
    "Darwin":  '    curl -LsSf https://astral.sh/uv/install.sh | sh',
    "Linux":   '    curl -LsSf https://astral.sh/uv/install.sh | sh',
}


# ══════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════

def main():
    do_fix = "--fix" in sys.argv

    print("═" * 55)
    print("  语音日历助手 · 环境检查")
    print("═" * 55)
    print(f"  系统: {platform.system()} {platform.machine()}")
    print(f"  目录: {PROJECT_ROOT}")
    if do_fix:
        print(f"  模式: --fix（自动修复）")

    checks = [
        ("Python 3.11+",      check_python,      "必须", None),
        ("ffmpeg (音频转码)",  check_ffmpeg,      "Web 录音", FFMPEG_INSTALL_GUIDE.get(platform.system(), "")),
        ("uv (包管理器)",      check_uv,          "安装依赖", UV_INSTALL_GUIDE.get(platform.system(), "")),
        (".env 配置",          check_env_file,    "API 密钥", fix_env_file),
        ("Python 依赖",        check_python_deps, "项目运行", fix_python_deps),
    ]

    all_ok = True
    for name, fn, tag, fix_fn in checks:
        ok, detail = fn()
        status = "✅" if ok else "❌"
        print(f"\n  [{tag}] {name}")
        print(f"     {status}  {detail}")
        if not ok:
            all_ok = False
            if do_fix and fix_fn:
                if callable(fix_fn):
                    fix_fn()
                else:
                    print(f"     安装指引:\n{fix_fn}")

    print(f"\n{'═' * 55}")
    if all_ok:
        print("  ✅ 所有依赖已就绪，可以启动项目")
        print(f"     uv run python main.py --api")
    elif do_fix:
        print("  🔧 已尝试自动修复，请检查上方输出")
    else:
        print("  ❌ 部分依赖缺失，运行以下命令自动修复:")
        print(f"     python setup.py --fix")
    print(f"{'═' * 55}")


if __name__ == "__main__":
    main()
