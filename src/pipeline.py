"""
管线抽象接口 — 定义了 fetch → dedup → filter → render → write → git_commit 六个步骤。

子类必须实现: fetch_data / generate_html
子类可选覆盖: dedup_data / filter_data / date_str / write_files / git_commit

此类为抽象基类，不可直接实例化。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class GeneratorPipeline(ABC):
    """AI Daily 生成管线抽象接口。

    Usage::

        class NewsPipeline(GeneratorPipeline):
            def fetch_data(self, config): ...
            def generate_html(self, items): ...
    """

    # ── 抽象方法（子类必须实现）────────────────────────────

    @abstractmethod
    def fetch_data(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 1: 获取原始数据，返回 item 列表。"""
        ...

    @abstractmethod
    def generate_html(self, items: List[Dict[str, Any]]) -> str:
        """Step 4: 将 item 列表渲染为 HTML 字符串。"""
        ...

    # ── 可选覆盖（提供默认实现的步骤）────────────────────────

    def dedup_data(
        self, items: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Step 2: URL 去重 + 语义去重。

        默认复用 utils.dedup_data，三管线共享同一去重逻辑。
        子类可覆盖以使用独立去重策略。
        """
        from utils import dedup_data as _dedup
        return _dedup(items, config)

    def filter_data(
        self, items: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Step 3（可选）: 关键词 / AI 过滤。

        默认透传。trending 管线覆盖此方法实现分组过滤。
        """
        return items

    # ── 日期字符串 — 统一 write / git 的时间来源 ────────────

    def date_str(self, config: Dict[str, Any]) -> str:
        """生成日期字符串（YYYY-MM-DD），用于 write_files / git_commit。

        默认通过 get_now_date_str 计算，受 config.target_date 控制，
        """
        from utils import get_now_date_str
        return get_now_date_str(config["fetch"]["target_date"])

    # ── 固定实现（write / git，默认不覆盖）───────────────────

    def write_files(
        self, html: str, config: Dict[str, Any],
        index_file: Path, archive_dir: Path,
    ) -> None:
        """Step 5: 写入 index.html + archive/{date_str}.html。"""
        from utils import write_files as _write
        _write(html, self.date_str(config), index_file, archive_dir)

    def git_commit(
        self, config: Dict[str, Any], files: List[str],
        label: str, output_dir: Path,
    ) -> None:
        """Step 6: git add + commit + push。"""
        from utils import git_commit as _commit
        _commit(self.date_str(config), files, label, output_dir)

    # ── 管线编排（模板方法）─────────────────────────────────

    def run(self, config: Dict[str, Any], index_file: Path, archive_dir: Path, label: str, output_dir: Path) -> None:
        """标准管线流程，按顺序执行六个步骤。"""
        # Step 1: fetch
        items = self.fetch_data(config)

        # Step 2: dedup
        items = self.dedup_data(items, config)

        # Step 3: filter（trending 在此做 AI 过滤）
        items = self.filter_data(items, config)

        # Step 4: render
        html = self.generate_html(items)

        # Step 5: write
        self.write_files(html, config, index_file, archive_dir)

        # Step 6: git
        files = [index_file.name, f"{archive_dir.name}/{self.date_str(config)}.html"]
        self.git_commit(config, files, label, output_dir)
