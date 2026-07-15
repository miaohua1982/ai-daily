#!/usr/bin/env python3
"""
AI HOT Academic Papers Archive Generator
Usage: python generate_papers.py [YYYY-MM-DD]

管线由 PapersPipeline（继承 GeneratorPipeline）编排：
  - src/papers/fetcher.py   数据获取（aihot + arXiv + HuggingFace 三源合并）
  - src/papers/renderer.py  HTML 渲染
  - 去重逻辑（URL + 语义）由基类 GeneratorPipeline.dedup_data 统一调用 utils.dedup_data
  - generate_papers.py     薄入口 + 模块级 wrapper（向后兼容 wechat / test）
"""

from pathlib import Path

from utils import load_config
from src.papers.pipeline import PapersPipeline
from src.papers.renderer import generate_html  # re-export for test.py

# ── 管线实例 ─────────────────────────────────────────────────────

_pipeline = PapersPipeline()

# ── 路径常量 ─────────────────────────────────────────────────────

OUTPUT_DIR  = PapersPipeline.OUTPUT_DIR
ARCHIVE_DIR = PapersPipeline.ARCHIVE_DIR
INDEX_FILE  = PapersPipeline.INDEX_FILE
CONFIG_FILE = PapersPipeline.CONFIG_FILE

# ── 向后兼容包装 ─────────────────────────────────────────────────
# generate_wechat.py 通过 gp.fetch_data / gp.dedup_data 调用。

def fetch_data(config):
    """Step 1: 多源获取论文原始数据 + 英文翻译。返回 papers。"""
    return _pipeline.fetch_data(config)

def dedup_data(items, config):
    """Step 2: URL 去重 + 语义去重。返回 papers。"""
    return _pipeline.dedup_data(items, config)


def filter_data(items, config):
    """Step 3: 过滤（复用 PapersPipeline.filter_data）。"""
    return _pipeline.filter_data(items, config)


# ── Main ─────────────────────────────────────────────────────────

def main():
    config = load_config(CONFIG_FILE)
    _pipeline.run(config, INDEX_FILE, ARCHIVE_DIR, "papers archive", OUTPUT_DIR)


if __name__ == "__main__":
    main()
