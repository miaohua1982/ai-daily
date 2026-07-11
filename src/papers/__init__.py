"""
papers — 论文管线辅助模块。

  - pipeline:  PapersPipeline 继承 GeneratorPipeline，编排 fetch→dedup→render→write→git
  - fetcher:   数据获取（aihot / arXiv / HuggingFace 多源）
  - dedup:     去重（URL 去重 + 语义去重）— 已提取至 utils.dedup_data，基类内部调用
  - renderer:  HTML 渲染
"""

from .pipeline import PapersPipeline
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
    "PapersPipeline",
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
