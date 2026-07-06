"""
trending — 趋势雷达管线辅助模块。

  - fetcher:   数据获取（NewsNow 多源抓取）
  - dedup:     去重（URL + 语义）
  - filter:    关键词 / AI 过滤 + 分组
  - renderer:  HTML 渲染
"""

from .fetcher import fetch_data
from .dedup import dedup_data
from .filter import filter_data, keyword_filter, ai_filter, ai_score_batch, assign_group_names
from .renderer import generate_html, source_meta, format_updated

__all__ = [
    "fetch_data",
    "dedup_data",
    "filter_data",
    "keyword_filter",
    "ai_filter",
    "ai_score_batch",
    "assign_group_names",
    "generate_html",
    "source_meta",
    "format_updated",
]
