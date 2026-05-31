"""入口点 — 委托给根目录 main.py"""

import sys, os

# 将项目根目录加入 sys.path
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _root not in sys.path:
    sys.path.insert(0, _root)

from main import main

if __name__ == "__main__":
    main()
