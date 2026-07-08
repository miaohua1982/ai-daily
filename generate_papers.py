#!/usr/bin/env python3
"""
AI HOT Academic Papers Archive Generator
Fetches recent AI papers from aihot / arXiv / HuggingFace and generates a static HTML archive.
Usage: python generate_papers.py [YYYY-MM-DD]

辅助函数已拆分至 src/papers/ 目录：
  - src/papers/fetcher.py   数据获取（aihot + arXiv + HuggingFace 三源合并）
  - src/papers/renderer.py  HTML 渲染
  - 去重逻辑（URL + 语义）已提取至 utils.dedup_data — papers / news 共用
  - generate_papers.py     编排（含 Top-N 选择）
"""

import sys
from pathlib import Path

from utils import load_dot_env, load_config, write_files, git_commit, dedup_data as _dedup_data_impl
from src.papers.fetcher import fetch_data as _fetch_data_impl
from src.papers.renderer import generate_html

# ── 路径常量 ─────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "papers-archive"
INDEX_FILE = OUTPUT_DIR / "papers.html"
CONFIG_FILE = OUTPUT_DIR / "config" / "papers_config.yaml"

# Load secrets (env > .env file)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")


# ── 向后兼容包装 ─────────────────────────────────────────────────
# generate_wechat.py 通过 gp.fetch_data / gp.dedup_data 调用，
# dedup_data 需要 _dot_env 注入 API Key，因此保留薄包装层。

def fetch_data(target_date=None, config=None):
    """Step 1: 多源获取论文原始数据 + 英文翻译。返回 (items, date_str)。"""
    return _fetch_data_impl(target_date, config, _dot_env)


def _select_top_papers(items, limit=50, config=None):
    """按 score 排序选出 top papers，未启用语义去重时用标题前缀兜底去重。"""
    selected = [i for i in items if i.get("selected")]
    not_selected = [i for i in items if not i.get("selected")]
    selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    not_selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    result = selected[:limit]
    if len(result) < limit:
        result += not_selected[:limit - len(result)]

    result.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return result[:limit]


def dedup_data(items, config=None):
    """Step 2: URL 去重 + 语义去重 + Top-N 选择。返回 papers。"""
    deduped = _dedup_data_impl(items, config, _dot_env)
    return _select_top_papers(deduped, limit=50, config=config)


# ── Main ─────────────────────────────────────────────────────────

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据（aihot + arXiv + HuggingFace 三源合并）
    papers, fetched_date_str = fetch_data(target_date, config)

    # Step 2: 去重（URL 去重 + 语义去重 + Top-N 选择）
    papers = dedup_data(papers, config)

    # Step 3: 生成 HTML
    html = generate_html(papers)

    # Step 4: 写入文件
    write_files(html, fetched_date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 5: Git 提交
    git_commit(fetched_date_str, ["papers.html", f"papers-archive/{fetched_date_str}.html"], "papers archive", OUTPUT_DIR)


if __name__ == "__main__":
    main()
