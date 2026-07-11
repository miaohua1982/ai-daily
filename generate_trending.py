#!/usr/bin/env python3
"""
Trending Radar Generator
直接调用 NewsNow API，按关键词 / AI 过滤生成趋势雷达静态页面。
用法：python generate_trending.py [YYYY-MM-DD]

管线由 TrendingPipeline（继承 GeneratorPipeline）编排：
  - src/trending/fetcher.py   数据获取（NewsNow 多源抓取）
  - src/trending/filter.py    关键词 / AI 过滤 + 分组
  - src/trending/renderer.py  HTML 渲染
  - 去重逻辑（URL + 语义）由基类 GeneratorPipeline.dedup_data 统一调用 utils.dedup_data
  - generate_trending.py     薄入口 + 模块级 wrapper（向后兼容 test）
"""

from pathlib import Path

from utils import load_config
from src.trending.pipeline import TrendingPipeline
from src.trending.filter import filter_data  # re-export for test.py
from src.trending.renderer import generate_html  # re-export for test.py

# ── 管线实例 ─────────────────────────────────────────────────────

_pipeline = TrendingPipeline()

# ── 路径常量（引用类属性）────────────────────────────────────────

INDEX_FILE  = TrendingPipeline.INDEX_FILE
ARCHIVE_DIR = TrendingPipeline.ARCHIVE_DIR
CONFIG_FILE = TrendingPipeline.CONFIG_FILE
OUTPUT_DIR  = TrendingPipeline.OUTPUT_DIR

# ── 向后兼容包装 ─────────────────────────────────────────────────
# test/test.py 通过 gt.fetch_data / gt.dedup_data / gt.filter_data / gt.INDEX_FILE 等调用。

def fetch_data(config):
    """Step 1: 获取所有 NewsNow 数据源。返回 items。"""
    return _pipeline.fetch_data(config)


def dedup_data(items, config):
    """Step 2: URL 去重 + 语义去重。返回去重后的 items。"""
    return _pipeline.dedup_data(items, config)


# ── Main ─────────────────────────────────────────────────────────

def main():
    config = load_config(CONFIG_FILE)
    _pipeline.run(config, INDEX_FILE, ARCHIVE_DIR, "trending radar", OUTPUT_DIR)


if __name__ == "__main__":
    main()
