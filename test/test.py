#!/usr/bin/env python3
"""
Test script for ai-daily pipelines (news / papers / trending).
Tests all step functions except git_commit, importing from the three generators.
All output goes to the craft/ directory (excluded from git).

Usage:
  python test/test.py          # 默认使用 stub 数据（快速）
  python test/test.py --live   # 尝试真实 API（trending 可能很慢）
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Setup paths ─────────────────────────────────────────────────
# 文件位于 test/ 子目录，项目根目录是上两级
ROOT = Path(__file__).parent.parent.resolve()
CRAFT_DIR = ROOT / "craft"
CRAFT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))

LIVE = "--live" in sys.argv

# ── Import step functions ───────────────────────────────────────
from generate_daily import (
    fetch_data as news_fetch,
    dedup_data as news_dedup,
    generate_html as news_html,
)
import generate_daily as gd

from generate_papers import (
    fetch_data as papers_fetch,
    dedup_data as papers_dedup,
    generate_html as papers_html,
)
import generate_papers as gp

from generate_trending import (
    fetch_data as trending_fetch,
    dedup_data as trending_dedup,
    filter_data as trending_filter,
    generate_html as trending_html,
)
import generate_trending as gt

from utils import load_config, write_files

# ── Config paths ────────────────────────────────────────────────
NEWS_CONFIG = ROOT / "config" / "news_config.yaml"
PAPERS_CONFIG = ROOT / "config" / "papers_config.yaml"
TRENDING_CONFIG = ROOT / "config" / "trending_config.yaml"


# ── Helpers ─────────────────────────────────────────────────────
def header(title: str) -> None:
    print(f"\n{'='*56}")
    print(f"  {title}")
    print(f"{'='*56}")


def ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def fail(msg: str) -> None:
    print(f"  ✗  {msg}", file=sys.stderr)


# ── Monkey-patch helper ─────────────────────────────────────────
class PatchPaths:
    """Temporarily redirect a module's INDEX_FILE and ARCHIVE_DIR to craft/ subdirectory."""

    def __init__(self, module, sub_dir: str):
        self.module = module
        self.dest = CRAFT_DIR / sub_dir
        self.old_index = module.INDEX_FILE
        self.old_archive = module.ARCHIVE_DIR

    def __enter__(self):
        self.dest.mkdir(parents=True, exist_ok=True)
        self.module.INDEX_FILE = self.dest / self.old_index.name
        self.module.ARCHIVE_DIR = self.dest / self.old_archive.name
        return self

    def __exit__(self, *args):
        self.module.INDEX_FILE = self.old_index
        self.module.ARCHIVE_DIR = self.old_archive


# ── Stub data (used when API is unreachable or --live not set) ───
def _stub_news_data():
    """Minimal news data matching aihot API response structure."""
    date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    data = {
        "sections": [
            {
                "label": "模型发布/更新",
                "items": [
                    {"id": "n1", "title": "OpenAI 发布 GPT-5 Turbo，推理速度提升 3 倍",
                     "summary": "推理延迟大幅下降", "sourceName": "TechCrunch",
                     "sourceUrl": "https://example.com/1"},
                    {"id": "n2", "title": "Claude 4 开放 API 公测",
                     "summary": "上下文窗口扩展至 200K tokens", "sourceName": "Anthropic Blog",
                     "sourceUrl": "https://example.com/2"},
                ],
            },
            {
                "label": "行业动态",
                "items": [
                    {"id": "n3", "title": "Google DeepMind 在蛋白质折叠领域再突破",
                     "summary": "AlphaFold 3 新版本", "sourceName": "Nature",
                     "url": "https://example.com/3"},
                ],
            },
        ],
        "windowEnd": datetime.now(timezone(timedelta(hours=8))).isoformat(),
    }
    return data, date_str


def _stub_papers_items():
    """Minimal papers items matching aihot API response structure."""
    date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    return [
        {"title": "Scaling Laws for Neural Language Models",
         "summary": "语言模型缩放定律研究", "source": "arXiv",
         "url": "https://arxiv.org/abs/2001.08361",
         "publishedAt": f"{date_str}T00:00:00Z",
         "selected": True, "score": 9.5},
        {"title": "Chain-of-Thought Prompting Elicits Reasoning",
         "summary": "思维链提示方法", "source": "arXiv",
         "url": "https://arxiv.org/abs/2201.11903",
         "publishedAt": f"{date_str}T00:00:00Z",
         "selected": True, "score": 8.0},
        {"title": "Attention Is All You Need",
         "summary": "Transformer 架构", "source": "arXiv",
         "url": "https://arxiv.org/abs/1706.03762",
         "publishedAt": f"{date_str}T00:00:00Z",
         "selected": False, "score": 7.0},
    ], date_str


def _stub_trending_items():
    """Minimal trending items matching NewsNow API response.
    Titles are crafted to hit keyword groups in trending_config.yaml."""
    return [
        {"title": "OpenAI 发布 GPT-5，推理能力大幅提升",
         "url": "https://example.com/openai-gpt5",
         "source_id": "weibo", "updatedTime": 1750992000000,
         "source_group": "综合热榜"},
        {"title": "特斯拉 FSD 在中国开始推送",
         "url": "https://example.com/tesla-fsd",
         "source_id": "toutiao", "updatedTime": 1750992000000,
         "source_group": "综合热榜"},
        {"title": "比亚迪月销量再创新高",
         "url": "https://example.com/byd-sales",
         "source_id": "jin10", "updatedTime": 1750992000000,
         "source_group": "财经/金融"},
        {"title": "宇树机器人新版本发布",
         "url": "https://example.com/unitree",
         "source_id": "cls", "updatedTime": 1750992000000,
         "source_group": "财经/金融"},
    ]


# ── Test 1: News pipeline (fetch → dedup → html → write) ──────
def test_news_pipeline() -> bool:
    header("TEST 1 — News: fetch → dedup → html → write")

    config = load_config(NEWS_CONFIG)

    # Step 1: Fetch
    data, date_str = None, None
    if LIVE:
        try:
            data, date_str = news_fetch(config=config)
            ok(f"Step 1 Fetch (live): got data for {date_str}")
        except Exception as e:
            fail(f"Step 1 Fetch (live) failed: {e}")
            data, date_str = _stub_news_data()
            ok(f"  Fallback to stub data for {date_str}")
    else:
        data, date_str = _stub_news_data()
        ok(f"Step 1 Fetch (stub): data for {date_str}")

    sections = data.get("sections", [])
    ok(f"  Raw sections: {len(sections)}")

    # Step 2: Dedup
    try:
        items_by_cat = news_dedup(data, config)
        total = sum(len(v) for v in items_by_cat.values())
        ok(f"Step 2 Dedup: {total} items in {len(items_by_cat)} categories")
        for cat, items in items_by_cat.items():
            if items:
                ok(f"    {cat}: {len(items)}")
    except Exception as e:
        fail(f"Step 2 Dedup failed: {e}")
        return False

    # Step 3: Generate HTML
    try:
        html = news_html(items_by_cat, data, date_str)
        ok(f"Step 3 HTML: {len(html):,} chars")
    except Exception as e:
        fail(f"Step 3 HTML failed: {e}")
        return False

    # Step 4: Write files (redirected to craft/)
    with PatchPaths(gd, "news"):
        try:
            write_files(html, date_str, gd.INDEX_FILE, gd.ARCHIVE_DIR)
            ok(f"Step 4 Write: {gd.INDEX_FILE}")
        except Exception as e:
            fail(f"Step 4 Write failed: {e}")
            return False

    # Sanity checks on HTML content
    checks = [
        ("date header", "年" in html or date_str[:4] in html),
        ("section markup", "sec-" in html),
        ("card markup", "card" in html),
        ("nav links", "nav-link" in html),
    ]
    all_ok = True
    for label, passed in checks:
        if passed:
            ok(f"Check [{label}]")
        else:
            fail(f"Check [{label}] FAILED")
            all_ok = False

    # Verify output file
    out_file = CRAFT_DIR / "news" / "daily_news.html"
    if out_file.exists():
        ok(f"File exists: {out_file} ({out_file.stat().st_size:,} bytes)")
    else:
        fail(f"File missing: {out_file}")
        all_ok = False

    return all_ok


# ── Test 2: Papers pipeline (fetch → dedup → html → write) ────
def test_papers_pipeline() -> bool:
    header("TEST 2 — Papers: fetch → dedup → html → write")

    config = load_config(PAPERS_CONFIG)

    # Step 1: Fetch
    items, date_str = None, None
    if LIVE:
        try:
            items, date_str = papers_fetch(config=config)
            ok(f"Step 1 Fetch (live): {len(items)} papers for {date_str}")
        except Exception as e:
            fail(f"Step 1 Fetch (live) failed: {e}")
            items, date_str = _stub_papers_items()
            ok(f"  Fallback to stub data: {len(items)} papers for {date_str}")
    else:
        items, date_str = _stub_papers_items()
        ok(f"Step 1 Fetch (stub): {len(items)} papers for {date_str}")

    if not items:
        fail("No papers fetched")
        return False

    # Step 2: Dedup
    try:
        papers = papers_dedup(items, config)
        ok(f"Step 2 Dedup: {len(papers)} papers after dedup (was {len(items)})")
    except Exception as e:
        fail(f"Step 2 Dedup failed: {e}")
        return False

    if not papers:
        fail("No papers after dedup")
        return False

    # Step 3: Generate HTML
    try:
        html = papers_html(papers, date_str)
        ok(f"Step 3 HTML: {len(html):,} chars")
    except Exception as e:
        fail(f"Step 3 HTML failed: {e}")
        return False

    # Step 4: Write files (redirected to craft/)
    with PatchPaths(gp, "papers"):
        try:
            write_files(html, date_str, gp.INDEX_FILE, gp.ARCHIVE_DIR)
            ok(f"Step 4 Write: {gp.INDEX_FILE}")
        except Exception as e:
            fail(f"Step 4 Write failed: {e}")
            return False

    # Sanity checks
    checks = [
        ("paper content", "论文" in html or "paper" in html.lower()),
        ("timeline or nav", "timeline" in html or "nav" in html),
        ("card or entry", "card" in html or "entry" in html),
    ]
    all_ok = True
    for label, passed in checks:
        if passed:
            ok(f"Check [{label}]")
        else:
            fail(f"Check [{label}] FAILED")
            all_ok = False

    # Verify output file
    out_file = CRAFT_DIR / "papers" / "papers.html"
    if out_file.exists():
        ok(f"File exists: {out_file} ({out_file.stat().st_size:,} bytes)")
    else:
        fail(f"File missing: {out_file}")
        all_ok = False

    return all_ok


# ── Test 3: Trending pipeline (fetch → dedup → filter → html → write)
def test_trending_pipeline() -> bool:
    header("TEST 3 — Trending: fetch → dedup → filter → html → write")

    config = load_config(TRENDING_CONFIG)
    if not config:
        fail("trending_config.yaml not found or empty")
        return False

    # 使用 stub 数据时，将 filter method 临时改为 keyword
    # （避免依赖 DeepSeek API，让 keyword_filter 能匹配 stub 标题）
    test_config = config.copy() if not LIVE else config
    if not LIVE:
        test_config.setdefault("filter", {})["method"] = "keyword"

    # Step 1: Fetch
    items = None
    if LIVE:
        try:
            items = trending_fetch(config)
            ok(f"Step 1 Fetch (live): {len(items)} raw items")
        except Exception as e:
            fail(f"Step 1 Fetch (live) failed: {e}")
            items = _stub_trending_items()
            ok(f"  Fallback to stub data: {len(items)} items")
    else:
        items = _stub_trending_items()
        ok(f"Step 1 Fetch (stub): {len(items)} items")

    if not items:
        fail("No items fetched")
        return False

    # Step 2: Dedup
    try:
        deduped = trending_dedup(items, test_config)
        ok(f"Step 2 Dedup: {len(deduped)} items (was {len(items)})")
    except Exception as e:
        fail(f"Step 2 Dedup failed: {e}")
        return False

    if not deduped:
        fail("No items after dedup")
        return False

    # Step 3: Filter (keyword or AI, per test_config)
    try:
        grouped = trending_filter(deduped, test_config)
        total = sum(len(v) for v in grouped.values())
        ok(f"Step 3 Filter: {total} items in {len(grouped)} groups")
        for gname, gitems in grouped.items():
            ok(f"    {gname}: {len(gitems)}")
    except Exception as e:
        fail(f"Step 3 Filter failed: {e}")
        return False

    if not grouped:
        fail("No groups after filtering")
        return False

    # Step 4: Generate HTML
    build_time = datetime.now(timezone(timedelta(hours=8)))
    try:
        html = trending_html(grouped, test_config, build_time)
        ok(f"Step 4 HTML: {len(html):,} chars")
    except Exception as e:
        fail(f"Step 4 HTML failed: {e}")
        return False

    # Step 5: Write files (redirected to craft/)
    date_str = build_time.strftime("%Y-%m-%d-%H")
    with PatchPaths(gt, "trending"):
        try:
            write_files(html, date_str, gt.INDEX_FILE, gt.ARCHIVE_DIR)
            ok(f"Step 5 Write: {gt.INDEX_FILE}")
        except Exception as e:
            fail(f"Step 5 Write failed: {e}")
            return False

    # Sanity checks
    checks = [
        ("trending/radar title", "trending" in html.lower() or "雷达" in html),
        ("group section", "sec-" in html),
        ("card markup", "card" in html or "link-card" in html),
        ("nav links", "nav-link" in html),
    ]
    all_ok = True
    for label, passed in checks:
        if passed:
            ok(f"Check [{label}]")
        else:
            fail(f"Check [{label}] FAILED")
            all_ok = False

    # Verify output file
    out_file = CRAFT_DIR / "trending" / "trending.html"
    if out_file.exists():
        ok(f"File exists: {out_file} ({out_file.stat().st_size:,} bytes)")
    else:
        fail(f"File missing: {out_file}")
        all_ok = False

    return all_ok


# ── Runner ───────────────────────────────────────────────────────
def main() -> int:
    mode = "LIVE" if LIVE else "STUB"
    print(f"\nai-daily — pipeline test suite (news / papers / trending)")
    print(f"Mode: {mode}  |  Output: {CRAFT_DIR}\n")

    results = {}
    results["news"] = test_news_pipeline()
    results["papers"] = test_papers_pipeline()
    results["trending"] = test_trending_pipeline()

    # Summary
    header("SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok_flag in results.items():
        status = "PASS ✓" if ok_flag else "FAIL ✗"
        print(f"  {status}  {name}")

    print(f"\n  {passed}/{total} tests passed")
    if passed > 0:
        print(f"\n  Open craft/ subfolders in a browser to inspect output pages.\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
