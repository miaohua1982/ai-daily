#!/usr/bin/env python3
"""
Test script for generate_wechat.py
Tests two capabilities locally:
  1. Cover image generation  → craft/cover.png
  2. WeChat-compatible HTML  → craft/wechat_preview.html

All output goes to the craft/ folder (excluded from git).
No WeChat API calls are made; no real credentials are needed.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Setup paths ─────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()
CRAFT_DIR = ROOT / "craft"
CRAFT_DIR.mkdir(exist_ok=True)

# Add project root to import path
sys.path.insert(0, str(ROOT))

# ── Import from generate_wechat ──────────────────────────────────
from generate_wechat import (
    generate_cover,
    build_wechat_html,
    fetch_news,
    fetch_papers,
    _format_date_cn,
)

# ── Helpers ─────────────────────────────────────────────────────
def header(title: str) -> None:
    print(f"\n{'='*56}")
    print(f"  {title}")
    print(f"{'='*56}")


def ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def fail(msg: str) -> None:
    print(f"  ✗  {msg}", file=sys.stderr)


# ── Test 1: Cover image generation ──────────────────────────────
def test_cover_image() -> bool:
    header("TEST 1 — Cover image generation")

    bj = datetime.now(timezone(timedelta(hours=8)))
    date_str = bj.strftime("%Y-%m-%d")
    news_count = 10
    papers_count = 10

    try:
        cover_bytes = generate_cover(date_str, news_count, papers_count)
    except Exception as e:
        fail(f"generate_cover() raised: {e}")
        return False

    if not cover_bytes:
        fail("generate_cover() returned empty bytes")
        return False

    out_path = CRAFT_DIR / "cover.png"
    out_path.write_bytes(cover_bytes)

    ok(f"Cover generated: {len(cover_bytes):,} bytes")
    ok(f"Saved to:        {out_path}")

    # Basic PNG signature check
    if cover_bytes[:4] == b"\x89PNG":
        ok("PNG signature valid ✓")
    else:
        fail("Output is not a valid PNG file")
        return False

    return True


# ── Test 2: WeChat HTML generation ──────────────────────────────
def test_wechat_html() -> bool:
    header("TEST 2 — WeChat-compatible HTML generation")

    bj = datetime.now(timezone(timedelta(hours=8)))
    if bj.hour < 5:
        bj -= timedelta(days=1)
    date_str = bj.strftime("%Y-%m-%d")

    # 2a. Fetch live data from API
    print(f"\n  [*] Fetching news from aihot API...")
    try:
        news = fetch_news()
        ok(f"Fetched {len(news)} news items")
    except Exception as e:
        fail(f"fetch_news() raised: {e}")
        news = []

    print(f"\n  [*] Fetching papers from aihot API...")
    try:
        papers = fetch_papers()
        ok(f"Fetched {len(papers)} papers")
    except Exception as e:
        fail(f"fetch_papers() raised: {e}")
        papers = []

    if len(news) == 0 and len(papers) == 0:
        print("  [!] No content from API (network issue or off-peak hours)")
        print("      Using stub data for HTML generation test...")
        news = _stub_news()
        papers = _stub_papers()

    # 2b. Build WeChat HTML
    repo_url = "https://github.com/miaohua1982/ai-daily"
    try:
        html_content = build_wechat_html(news, papers, date_str, repo_url)
    except Exception as e:
        fail(f"build_wechat_html() raised: {e}")
        return False

    if not html_content or len(html_content) < 200:
        fail(f"HTML too short ({len(html_content)} chars) — likely a build failure")
        return False

    ok(f"HTML content built: {len(html_content):,} chars")

    # 2c. Wrap in a viewable full HTML page (for browser preview)
    display_date = _format_date_cn(date_str)
    preview_html = _wrap_preview(html_content, display_date)

    out_path = CRAFT_DIR / "wechat_preview.html"
    out_path.write_text(preview_html, encoding="utf-8")
    ok(f"Saved to:          {out_path}")

    # 2d. Sanity checks
    checks = [
        ("headline section", "每日 AI 情报" in html_content),
        ("news section header", "AI 热点资讯" in html_content or len(news) == 0),
        ("papers section header", "AI 论文精选" in html_content or len(papers) == 0),
        ("no <script> tags", "<script" not in html_content),
        ("no external CSS", "<link" not in html_content),
        ("inline styles present", "style=" in html_content),
        ("footer/credit present", "ai-daily" in html_content),
    ]

    all_ok = True
    for label, passed in checks:
        if passed:
            ok(f"Check [{label}]")
        else:
            fail(f"Check [{label}] FAILED")
            all_ok = False

    return all_ok


# ── Stub data (used when API is unreachable) ─────────────────────
def _stub_news() -> list[dict]:
    return [
        {
            "title": "OpenAI 发布 GPT-5 Turbo，推理速度提升 3 倍",
            "summary": "OpenAI 最新发布的 GPT-5 Turbo 在保持高质量输出的同时，推理延迟大幅下降。",
            "sourceName": "TechCrunch",
            "_section": "大模型",
            "url": "https://example.com/1",
        },
        {
            "title": "Google DeepMind 在蛋白质折叠领域再突破",
            "summary": "AlphaFold 3 新版本已能预测 RNA 与蛋白质复合物的结构。",
            "sourceName": "Nature",
            "_section": "科学研究",
            "url": "https://example.com/2",
        },
        {
            "title": "Anthropic Claude 4 开放 API 公测",
            "summary": "Claude 4 上下文窗口扩展至 200K tokens，编程任务得分超越同期竞品。",
            "sourceName": "Anthropic Blog",
            "_section": "产品发布",
            "url": "https://example.com/3",
        },
    ]


def _stub_papers() -> list[dict]:
    return [
        {
            "title": "Scaling Laws for Neural Language Models",
            "summary": "本文系统研究了语言模型性能随参数量、数据量、计算量变化的规律，提出了可指导大规模训练的缩放定律。",
            "source": "arXiv",
            "url": "https://arxiv.org/abs/2001.08361",
            "publishedAt": "2024-06-20T00:00:00Z",
        },
        {
            "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
            "summary": "通过在少样本示例中加入思维链，可以显著提升大型语言模型在算术、符号推理等复杂任务上的表现。",
            "source": "arXiv",
            "url": "https://arxiv.org/abs/2201.11903",
            "publishedAt": "2024-06-19T00:00:00Z",
        },
    ]


# ── Preview wrapper ──────────────────────────────────────────────
def _wrap_preview(wechat_html: str, display_date: str) -> str:
    """Wrap WeChat content in a full HTML page for local browser preview."""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>微信草稿预览 — {display_date}</title>
  <style>
    body {{
      background: #f5f5f5;
      margin: 0;
      padding: 20px;
      font-family: -apple-system, "Helvetica Neue", sans-serif;
    }}
    .device {{
      max-width: 390px;
      margin: 0 auto;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 4px 24px rgba(0,0,0,.12);
      overflow: hidden;
    }}
    .status-bar {{
      height: 44px;
      background: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      font-size: 13px;
      color: #333;
      border-bottom: 1px solid #eee;
    }}
    .wechat-content {{
      padding: 0;
      font-size: 15px;
      color: #333;
      line-height: 1.6;
    }}
    .preview-note {{
      text-align: center;
      padding: 10px;
      font-size: 11px;
      color: #bbb;
      background: #fafafa;
      border-top: 1px solid #eee;
    }}
  </style>
</head>
<body>
  <div style="text-align:center;margin-bottom:16px;font-size:13px;color:#888">
    ⬇️ 微信公众号文章预览（craft 本地预览，不会提交到 git）
  </div>
  <div class="device">
    <div class="status-bar">
      <span>9:41</span>
      <span>📶 🔋</span>
    </div>
    <div class="wechat-content">
{wechat_html}
    </div>
    <div class="preview-note">本文件由 test.py 生成 · 仅供本地预览</div>
  </div>
</body>
</html>"""


# ── Runner ───────────────────────────────────────────────────────
def main() -> int:
    print(f"\nai-daily / generate_wechat.py — local test suite")
    print(f"Output directory: {CRAFT_DIR}\n")

    results = {}

    results["cover"] = test_cover_image()
    results["html"] = test_wechat_html()

    # Summary
    header("SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    for name, ok_flag in results.items():
        status = "PASS ✓" if ok_flag else "FAIL ✗"
        print(f"  {status}  {name}")

    print(f"\n  {passed}/{total} tests passed")
    print(f"\n  Open craft/wechat_preview.html in a browser to inspect the WeChat layout.")
    print(f"  Open craft/cover.png to inspect the cover image.\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
