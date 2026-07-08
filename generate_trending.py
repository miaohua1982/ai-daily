#!/usr/bin/env python3
"""
Trending Radar Generator
直接调用 NewsNow API，按关键词 / AI 过滤生成趋势雷达静态页面。
用法：python generate_trending.py [YYYY-MM-DD]

辅助函数已拆分至 src/trending/ 目录：
  - src/trending/fetcher.py   数据获取（NewsNow 多源抓取）
  - src/trending/dedup.py     去重（URL + 语义）
  - src/trending/filter.py    关键词 / AI 过滤 + 分组
  - src/trending/renderer.py  HTML 渲染
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from utils import load_dot_env, load_config, write_files, git_commit
from src.trending.fetcher import fetch_data as _fetch_data_impl
from src.trending.dedup import dedup_data as _dedup_data_impl
from src.trending.filter import filter_data as _filter_data_impl
from src.trending.renderer import generate_html

# ── 路径常量 ─────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent
CONFIG_FILE = OUTPUT_DIR / "config" / "trending_config.yaml"
ARCHIVE_DIR = OUTPUT_DIR / "trending-archive"
INDEX_FILE = OUTPUT_DIR / "trending.html"

# Load secrets (env > .env file)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")


# ── 向后兼容包装 ─────────────────────────────────────────────────
# test/test.py 通过 gt.fetch_data / gt.filter_data 等调用，
# dedup_data 和 filter_data 需要 _dot_env 注入 API Key，因此保留薄包装层。

def fetch_data(config):
    """Step 1: 获取所有 NewsNow 数据源。返回 items。"""
    return _fetch_data_impl(config)


def dedup_data(items, config):
    """Step 2: URL 去重 + 语义去重。返回去重后的 items。"""
    return _dedup_data_impl(items, config, _dot_env)


def filter_data(items, config):
    """Step 3: 关键词 / AI 过滤 + 分组。返回 grouped_items。"""
    return _filter_data_impl(items, config, _dot_env)


# ── Main ─────────────────────────────────────────────────────────

def main():
    if not CONFIG_FILE.exists():
        print(f"[ERROR] Config file not found: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据
    items = fetch_data(config)

    # Step 2: 去重
    items = dedup_data(items, config)

    # Step 3: 过滤
    grouped_items = filter_data(items, config)

    # Step 4: 生成 HTML
    html = generate_html(grouped_items)

    # Step 5: 写入文件
    date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d-%H")
    write_files(html, date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 6: Git 提交
    git_commit(date_str, ["trending.html", f"trending-archive/{date_str}.html"], "trending radar", OUTPUT_DIR)


if __name__ == "__main__":
    main()
