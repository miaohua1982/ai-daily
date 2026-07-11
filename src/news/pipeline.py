"""
新闻管线 — NewsPipeline 实现了 GeneratorPipeline 抽象接口。

职责：fetch（aihot + newsnow）→ dedup（URL + 语义）→ render → write → git
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.pipeline import GeneratorPipeline

# 延迟导入避免顶层循环依赖
from src.news.fetcher import fetch_data as _fetch_impl
from src.news.renderer import generate_html as _render_impl


class NewsPipeline(GeneratorPipeline):
    """AI 日报新闻管线。

    Usage::

        pipeline = NewsPipeline()
        pipeline.run(config, index_file, archive_dir, "daily news dashboard", output_dir)
    """

    OUTPUT_DIR  = Path(__file__).parent.parent.parent  # ai-daily 根目录
    ARCHIVE_DIR = OUTPUT_DIR / "news-archive"
    INDEX_FILE  = OUTPUT_DIR / "daily_news.html"
    CONFIG_FILE = OUTPUT_DIR / "config" / "news_config.yaml"

    # ── 抽象方法实现 ──────────────────────────────────────

    def fetch_data(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 items 列表，每条含 publishTime。"""
        return _fetch_impl(config)

    def generate_html(self, items: List[Dict[str, Any]]) -> str:
        """Step 4: 将 item 列表渲染为 HTML 字符串。"""
        return _render_impl(items)
