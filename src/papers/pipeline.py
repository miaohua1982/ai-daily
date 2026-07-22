"""
论文管线 — PapersPipeline 实现了 GeneratorPipeline 抽象接口。

职责：fetch（aihot + arXiv + HuggingFace 三源）→ dedup（URL + 语义）→ render → write → git
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.pipeline import GeneratorPipeline

# 延迟导入避免顶层循环依赖
from src.papers.fetcher import fetch_data as _fetch_impl
from src.papers.renderer import generate_html as _render_impl


class PapersPipeline(GeneratorPipeline):
    """AI 论文管线。

    Usage::

        pipeline = PapersPipeline()
        pipeline.run(config, index_file, archive_dir, "papers archive", output_dir)
    """

    OUTPUT_DIR  = Path(__file__).parent.parent.parent  # ai-daily 根目录
    ARCHIVE_DIR = OUTPUT_DIR / "archive" / "papers"
    INDEX_FILE  = OUTPUT_DIR / "papers.html"
    CONFIG_FILE = OUTPUT_DIR / "config" / "papers_config.yaml"

    # ── 抽象方法实现 ──────────────────────────────────────

    def fetch_data(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 1: 多源获取论文原始数据 + 英文翻译。返回 papers 列表。"""
        return _fetch_impl(config)

    def generate_html(self, papers: List[Dict[str, Any]]) -> str:
        """Step 4: 将 papers 列表渲染为 HTML 字符串。"""
        return _render_impl(papers)

    def filter_data(self, papers: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 3: 过滤摘要过短的论文（优先 summary_zh 再回退 summary / description，阈值由 config.filter.min_summary_len 控制）。"""
        min_len = config.get("filter", {}).get("min_summary_len", 20)
        kept, dropped = [], 0
        for p in papers:
            s = p.get("summary_zh") or p.get("summary") or p.get("description") or ""
            if len(s.strip()) < min_len:
                dropped += 1
                continue
            kept.append(p)
        if dropped:
            print(f"[INFO] Papers filter_data dropped {dropped} short-summary items (<{min_len} chars)")
        return kept
