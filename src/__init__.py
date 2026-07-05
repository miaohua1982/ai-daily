"""
src — 业务逻辑分层模块。

每个 generate_*.py 的辅助函数按职责拆分到独立子模块：
  - papers_fetcher:   数据获取（aihot / arXiv / HuggingFace 多源）
  - papers_dedup:     去重（URL 去重 + 语义去重 + Top-N 选择）
  - papers_renderer:  HTML 渲染
"""

from .papers_fetcher import (
    fetch_data,
    fetch_aihot_papers,
    fetch_arxiv_papers,
    fetch_hf_daily_papers,
    merge_papers,
    translate_papers,
)
from .papers_dedup import dedup_data, select_top_papers
from .papers_renderer import generate_html, SOURCE_COLORS

__all__ = [
    "fetch_data",
    "fetch_aihot_papers",
    "fetch_arxiv_papers",
    "fetch_hf_daily_papers",
    "merge_papers",
    "translate_papers",
    "dedup_data",
    "select_top_papers",
    "generate_html",
    "SOURCE_COLORS",
]
