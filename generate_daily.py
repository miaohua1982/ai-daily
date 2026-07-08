#!/usr/bin/env python3
"""
AI HOT Daily Dashboard Generator
Fetches daily AI news from aihot.virxact.com and generates a static HTML dashboard.
Usage: python generate_daily.py [YYYY-MM-DD]

辅助函数已拆分至 src/news/ 目录：
  - src/news/fetcher.py   数据获取（aihot 主源 + newsnow 备用源）
  - src/news/renderer.py  HTML 渲染
  - 去重逻辑（URL + 语义）已提取至 utils.dedup_data — papers / news 共用
"""

import sys
from pathlib import Path

from utils import load_dot_env, load_config, write_files, git_commit, get_now_date_str, dedup_data as _dedup_data_impl
from src.news.fetcher import fetch_data as _fetch_data_impl
from src.news.renderer import generate_html
from src.news.constants import CATEGORY_LABELS, CATEGORY_ORDER  # re-export

# ── 路径常量 ─────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "news-archive"
INDEX_FILE = OUTPUT_DIR / "daily_news.html"
CONFIG_FILE = OUTPUT_DIR / "config" / "news_config.yaml"

# Load secrets (env > .env file)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")


# ── 向后兼容包装 ─────────────────────────────────────────────────
# generate_wechat.py 通过 gd.fetch_data / gd.dedup_data 调用，
# dedup_data 需要 _dot_env 注入 API Key，因此保留薄包装层。

def fetch_data(target_date=None, config=None):
    """Step 1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 (items, ts)。"""
    return _fetch_data_impl(target_date, config)


def dedup_data(items, config=None):
    """Step 2: URL 去重 + 语义去重。返回去重后的 item 列表。"""
    return _dedup_data_impl(items, config, _dot_env)


# ── Main ─────────────────────────────────────────────────────────

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据，返回 (items, ts)
    news, fetched_date_str = fetch_data(target_date, config)

    # Step 2: 去重
    news = dedup_data(news, config)

    # Step 3: 生成 HTML
    html = generate_html(news, fetched_date_str)

    # Step 4: 写入文件
    gen_date_str = get_now_date_str(target_date) # 可能与数据获取时间不一致！
    write_files(html, gen_date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 5: Git 提交
    git_commit(gen_date_str, ["daily_news.html", f"news-archive/{gen_date_str}.html"], "daily news dashboard", OUTPUT_DIR)


if __name__ == "__main__":
    main()
