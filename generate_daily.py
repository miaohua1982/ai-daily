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

from utils import load_dot_env, load_config, write_files, git_commit, dedup_data as _dedup_data_impl
from src.news.fetcher import fetch_data as _fetch_data_impl
from src.news.renderer import generate_html
from src.news.constants import CATEGORY_LABELS, CATEGORY_ORDER, LABEL_TO_SLUG  # re-export

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
    """Step 1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 (data, date_str)。"""
    return _fetch_data_impl(target_date, config)


def dedup_data(data, config=None):
    """Step 2: URL 去重 + 语义去重，重建分类分组。返回 items_by_cat。"""
    # 1. 从 sections 中提取所有 item，标注 category
    sections = data.get("sections", [])
    all_items = []
    for sec in sections:
        label = sec.get("label", "")
        cat = LABEL_TO_SLUG.get(label, "")
        for item in sec.get("items", []):
            item["category"] = cat
            all_items.append(item)

    # 2. 调用底层去重（输入输出均为 item 列表）
    deduped = _dedup_data_impl(all_items, config, _dot_env)

    # 3. 重建 items_by_cat（按 category 分组）
    items_by_cat = {}
    for it in deduped:
        cat = it.get("category", "")
        items_by_cat.setdefault(cat, []).append(it)

    return items_by_cat


# ── Main ─────────────────────────────────────────────────────────

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据，存在无法获取到当前日期，只能获取服务端最新日期的情况，因此返回 (data, date_str)
    data, date_str = fetch_data(target_date, config)

    # Step 2: 去重
    items_by_cat = dedup_data(data, config)

    # Step 3: 生成 HTML
    html = generate_html(items_by_cat, data, date_str)

    # Step 4: 写入文件
    write_files(html, date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 5: Git 提交
    git_commit(date_str, ["daily_news.html", f"news-archive/{date_str}.html"], "daily dashboard", OUTPUT_DIR)


if __name__ == "__main__":
    main()
