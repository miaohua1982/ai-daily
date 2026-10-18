#!/usr/bin/env python3
# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜重写】
# 文件：test/test.py
# 修改内容及原因：将原手工测试改为 pytest 统一入口；移除失败后回退假数据的行为。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""离线测试入口。旧脚本的返回值已过时，且 stub 模式仍可能请求真实 API。
改为统一 pytest 测试；异常必须表现为断言失败，不再偷偷回退假数据。
运行：python test/test.py；覆盖率命令见 test/README.md。
"""
from pathlib import Path
import sys
import pytest

if __name__ == '__main__':
    raise SystemExit(pytest.main([str(Path(__file__).parent), '-q', *sys.argv[1:]]))
