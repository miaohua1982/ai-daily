"""
papers — 论文管线辅助模块。

  - fetcher:   数据获取（aihot / arXiv / HuggingFace 多源）
  - dedup:     去重（URL 去重 + 语义去重）— 已提取至 utils.dedup_data
  - renderer:  HTML 渲染
"""

from .fetcher import (
    fetch_data,
    fetch_aihot_papers,
    fetch_arxiv_papers,
    fetch_hf_daily_papers,
    merge_papers,
    translate_papers,
)
from utils import dedup_data
from .constants import SOURCE_COLORS
from .renderer import generate_html

__all__ = [
    "fetch_data",
    "fetch_aihot_papers",
    "fetch_arxiv_papers",
    "fetch_hf_daily_papers",
    "merge_papers",
    "translate_papers",
    "dedup_data",
    "generate_html",
    "SOURCE_COLORS",
]
