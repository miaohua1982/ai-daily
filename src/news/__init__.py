"""
news — 新闻管线辅助模块。

  - constants:  共享常量（分类、颜色、图标）
  - fetcher:    数据获取（aihot 主源 + newsnow 备用源）
  - dedup:      去重（URL 去重 + 语义去重）— 已提取至 utils.dedup_data
  - renderer:   HTML 渲染
"""

from .constants import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    CATEGORY_COLORS,
    EMPTY_ICONS,
)
from .fetcher import fetch_data
from utils import dedup_data
from .renderer import generate_html, fmt_time, source_class, short_source, summarize

__all__ = [
    # constants
    "CATEGORY_LABELS", "CATEGORY_ORDER",
    "CATEGORY_COLORS", "EMPTY_ICONS",
    # fetcher
    "fetch_data",
    # dedup
    "dedup_data",
    # renderer
    "generate_html", "fmt_time", "source_class", "short_source", "summarize",
]
