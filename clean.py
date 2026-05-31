"""
清理工具

用法：
    python clean.py          清理端口 8000 占用进程
    python clean.py --reset  清理端口 + 重置数据库（删除 data/calendar.db）
"""

import io
import os
import sys
import socket
import subprocess
import platform

# Windows 下强制 UTF-8 输出，避免 GBK 编码报错
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "calendar.db")
PORT = 8000


def find_pid_by_port(port: int) -> list[int]:
    """查找占用指定端口的 PID 列表"""
    system = platform.system()

    if system == "Windows":
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=10,
            )
            pids = set()
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pids.add(int(parts[-1]))
            return list(pids)
        except Exception as e:
            print(f"[错误] 查找端口占用失败: {e}")
            return []

    else:  # Linux / macOS
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout.strip():
                return [int(p) for p in result.stdout.strip().splitlines()]
            return []
        except FileNotFoundError:
            # 退而求其次用 ss
            try:
                result = subprocess.run(
                    ["ss", "-tlnp"],
                    capture_output=True, text=True, timeout=10,
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line:
                        # 尝试提取 pid
                        import re
                        match = re.search(r"pid=(\d+)", line)
                        if match:
                            return [int(match.group(1))]
            except Exception:
                pass
            return []


def kill_process(pid: int) -> bool:
    """终止指定 PID 进程"""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, timeout=10)
        else:
            os.kill(pid, 9)
        return True
    except Exception as e:
        print(f"[警告] 终止 PID {pid} 失败: {e}")
        return False


def clean_port(port: int = PORT) -> int:
    """清理端口占用，返回清理的进程数"""
    pids = find_pid_by_port(port)
    if not pids:
        print(f"[信息] 端口 {port} 未被占用")
        return 0

    count = 0
    for pid in pids:
        print(f"[清理] 端口 {port} 被 PID {pid} 占用，正在终止...")
        if kill_process(pid):
            print(f"  ✓ PID {pid} 已终止")
            count += 1
    return count


def reset_database(db_path: str = DB_PATH) -> bool:
    """删除数据库文件"""
    if not os.path.exists(db_path):
        print(f"[信息] 数据库文件不存在: {db_path}")
        return True
    try:
        os.remove(db_path)
        print(f"[重置] 数据库已删除: {db_path}")
        return True
    except Exception as e:
        print(f"[错误] 删除数据库失败: {e}")
        return False


def main():
    do_reset = "--reset" in sys.argv

    print("=" * 50)
    print("  语音日历助手 - 清理工具")
    print("=" * 50)

    # 1. 清理端口
    print("\n[1/2] 清理端口占用...")
    cleaned = clean_port(PORT)
    if cleaned == 0 and do_reset:
        pass  # 端口本来就没占用，继续

    # 2. 重置数据库（仅在 --reset 时）
    if do_reset:
        print("\n[2/2] 重置数据库...")
        reset_database()
        print("\n[完成] 端口已释放，数据库已重置。")
    else:
        print("\n[完成] 端口已释放。")
        print("[提示] 如需同时重置数据库，请使用: python clean.py --reset")


if __name__ == "__main__":
    main()
