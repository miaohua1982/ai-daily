#!/usr/bin/env python3
"""
Papers HTML rendering layer.
Pure presentation — no data fetching or dedup logic.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

from utils.html_template import render_papers_html, WEEKDAY_NAMES
from .constants import SOURCE_COLORS


# ── 辅助函数 ─────────────────────────────────────────────────────

def sanitize(s: Any) -> str:
    """Remove lone surrogates and other invalid Unicode from a string."""
    if not isinstance(s, str):
        return s
    return s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def get_badge_color(source: str) -> Tuple[str, str]:
    """根据来源名称返回 (背景色, 文字色)。"""
    sl = (source or "").lower()
    for key, (bg, text) in SOURCE_COLORS.items():
        if key in sl:
            return (bg, text)
    return ("#f0f0f0", "#555555")


def get_badge_label(source: str) -> str:
    """从完整来源名中提取简短标签。"""
    s = source or ""
    for sep in ["\uff1a", ":"]:
        if sep in s:
            s = s.split(sep)[0].strip()
    if "(" in s:
        s = s.split("(")[0].strip()
    if len(s) > 20:
        s = s[:20] + "\u2026"
    return s


def group_by_date(papers: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Dict[str, Any]]], List[str]]:
    """按 publishedAt 日期分组，返回 (groups_dict, sorted_date_keys)。"""
    groups = {}
    for p in papers:
        d = (p.get("publishedAt") or "")[:10]
        if not d:
            continue
        if d not in groups:
            groups[d] = []
        groups[d].append(p)
    keys = sorted(groups.keys(), reverse=True)
    return groups, keys


# ── Step 3: 生成 HTML ────────────────────────────────────────────

def generate_html(papers: List[Dict[str, Any]], date_str: str) -> str:
    """Step 3: 纯 HTML 渲染，不含去重逻辑。"""
    groups, sorted_dates = group_by_date(papers)
    total = len(papers)
    num_dates = len(sorted_dates)

    # ---- Build JS data arrays ----
    papers_js_items = []
    global_idx = 0
    for d in sorted_dates:
        for p in groups[d]:
            global_idx += 1
            # 优先使用中文翻译，回退到原始标题/摘要
            title = sanitize(p.get("title_zh") or p.get("title", "") or "")
            source = sanitize(p.get("source", "") or "")
            summary = sanitize(p.get("summary_zh") or p.get("summary", "") or "") or "\u6682\u65e0\u6458\u8981"
            if len(summary) > 200:
                summary = summary[:200] + "\u2026"
            source_color = get_badge_color(source)
            entry = {
                "idx": global_idx,
                "title": title,
                "source": source,
                "badgeLabel": get_badge_label(source),
                "badgeBg": source_color[0],
                "badgeColor": source_color[1],
                "publishedAt": p.get("publishedAt", ""),
                "dateStr": (p.get("publishedAt") or "")[:10],
                "url": sanitize(p.get("url", "#") or "#"),
                "summary": summary,
                "selected": p.get("selected", False),
                "score": p.get("score", 0),
            }
            papers_js_items.append(json.dumps(entry, ensure_ascii=False))

    timeline_js_items = []
    for d in sorted_dates:
        try:
            wd = WEEKDAY_NAMES[datetime.strptime(d, "%Y-%m-%d").weekday()]
        except Exception:
            wd = ""
        timeline_js_items.append(json.dumps(
            {"date": d, "wd": wd, "count": len(groups[d])},
            ensure_ascii=False))

    papers_json = "[\n" + ",\n".join(papers_js_items) + "\n]"
    timeline_json = "[\n" + ",\n".join(timeline_js_items) + "\n]"

    return render_papers_html(total, num_dates, papers_json, timeline_json, groups, sorted_dates)
