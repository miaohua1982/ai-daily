"""
news — 新闻管线辅助模块。

  - pipeline:   NewsPipeline(GeneratorPipeline) — 管线编排
  - constants:  共享常量（分类、颜色、图标）
  - fetcher:    数据获取（aihot 主源 + newsnow 备用源）
  - renderer:   HTML 渲染
  - dedup:      去重 — 已提取至 utils.dedup_data，NewsPipeline 默认复用
"""

from .constants import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    CATEGORY_LBL,
    CATEGORY_COLORS,
    EMPTY_ICONS,
)
from .pipeline import NewsPipeline
from .fetcher import fetch_data
from utils import dedup_data
from .renderer import generate_html, fmt_time, source_class, short_source, summarize

__all__ = [
    # pipeline
    "NewsPipeline",
    # constants
    "CATEGORY_LABELS", "CATEGORY_ORDER", "CATEGORY_LBL", "CATEGORY_COLORS", "EMPTY_ICONS",
    # fetcher
    "fetch_data",
    # dedup
    "dedup_data",
    # renderer
    "generate_html", "fmt_time", "source_class", "short_source", "summarize",
]
