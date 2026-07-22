"""
趋势雷达管线 — TrendingPipeline 实现了 GeneratorPipeline 抽象接口。

职责：fetch（NewsNow 多源）→ dedup（URL + 语义）→ filter（关键词/AI）→ render → write → git
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from src.pipeline import GeneratorPipeline

from src.trending.fetcher import fetch_data as _fetch_impl
from src.trending.filter import filter_data as _filter_impl
from src.trending.renderer import generate_html as _render_impl


class TrendingPipeline(GeneratorPipeline):
    """趋势雷达管线。

    Usage::

        pipeline = TrendingPipeline()
        pipeline.run(config, index_file, archive_dir, "trending radar", output_dir)
    """

    OUTPUT_DIR  = Path(__file__).parent.parent.parent  # ai-daily 根目录
    ARCHIVE_DIR = OUTPUT_DIR / "archive" / "trending"
    INDEX_FILE  = OUTPUT_DIR / "trending.html"
    CONFIG_FILE = OUTPUT_DIR / "config" / "trending_config.yaml"

    # ── 抽象方法实现 ──────────────────────────────────────

    def fetch_data(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 1: 获取所有 NewsNow 数据源。返回 items 列表。"""
        return _fetch_impl(config)

    def generate_html(self, items: List[Dict[str, Any]]) -> str:
        """Step 4: 将 item 列表渲染为 HTML 字符串。"""
        return _render_impl(items)

    # ── 覆盖基类方法 ──────────────────────────────────────

    def filter_data(
        self, items: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Step 3: 关键词 / AI 过滤 + 分组。trending 独有步骤。"""
        return _filter_impl(items, config)

    def date_str(self, config: Dict[str, Any]) -> str:
        """生成日期字符串（YYYY-MM-DD-HH）。trending 保留小时后缀，按北京时间。"""
        return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d-%H")
