#!/usr/bin/env python3
"""
AI HOT Daily Dashboard Generator
Fetches daily AI news from aihot.virxact.com and generates a static HTML dashboard.
Usage: python generate_daily.py [YYYY-MM-DD]

管线实现: src/news/pipeline.py — NewsPipeline(GeneratorPipeline)
  fetch → dedup(URL+语义) → filter(透传) → render → write → git_commit
"""
from pathlib import Path

from utils import load_config
from src.news.pipeline import NewsPipeline
from src.news.renderer import generate_html  # re-export for test.py

# ── 管线实例 ─────────────────────────────────────────────────────

_pipeline = NewsPipeline()

# ── 路径常量（引用类属性）────────────────────────────────────────

INDEX_FILE  = NewsPipeline.INDEX_FILE
ARCHIVE_DIR = NewsPipeline.ARCHIVE_DIR
CONFIG_FILE = NewsPipeline.CONFIG_FILE
OUTPUT_DIR  = NewsPipeline.OUTPUT_DIR

# ── 向后兼容包装 ─────────────────────────────────────────────────
# generate_wechat.py / test.py 通过 gd.fetch_data / gd.dedup_data 调用

def fetch_data(config):
    """Step 1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 items 列表，每条含 publishTime。"""
    return _pipeline.fetch_data(config)


def dedup_data(items, config):
    """Step 2: URL 去重 + 语义去重。返回去重后的 item 列表。"""
    return _pipeline.dedup_data(items, config)


def filter_data(items, config):
    """Step 3: 过滤（复用 NewsPipeline.filter_data）。"""
    return _pipeline.filter_data(items, config)


# ── Main ─────────────────────────────────────────────────────────

def main():
    config = load_config(CONFIG_FILE)
    _pipeline.run(config, INDEX_FILE, ARCHIVE_DIR, "daily news dashboard", OUTPUT_DIR)


if __name__ == "__main__":
    main()
