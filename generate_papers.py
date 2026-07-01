#!/usr/bin/env python3
"""
AI HOT Academic Papers Archive Generator
Fetches recent AI papers from aihot.virxact.com and generates a static HTML archive.
Usage: python generate_papers.py [YYYY-MM-DD]
"""

import sys
import os
import json
import time
import random
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from utils import load_dot_env, semantic_dedup, load_config, write_files, git_commit, api_get
from utils.html_template import render_papers_html, WEEKDAY_NAMES

OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "papers-archive"
INDEX_FILE = OUTPUT_DIR / "papers.html"
CONFIG_FILE = OUTPUT_DIR / "config" / "papers_config.yaml"

# Load secrets (env > .env file)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")

SOURCE_COLORS = {
    "arxiv": ("#fce4ec", "#c0392b"),
    "hugging face": ("#fff3e0", "#e65100"),
    "openai": ("#e8f5e9", "#2e7d32"),
    "anthropic": ("#f3e5f5", "#7b1fa2"),
    "google": ("#e3f2fd", "#1565c0"),
    "nvidia": ("#e8f5e9", "#2e7d32"),
    "nature": ("#fbe9e7", "#d84315"),
    "mit": ("#fce4ec", "#c0392b"),
    "stanford": ("#fbe9e7", "#bf360c"),
    "berkeley": ("#e8eaf6", "#283593"),
    "microsoft": ("#e3f2fd", "#1565c0"),
    "deepmind": ("#e8eaf6", "#283593"),
}


# ─── Step 1: 获取数据 ───

def fetch_data(target_date=None, config=None):
    """Step 1: 获取论文原始数据。返回 (items, date_str)。"""
    if config is None:
        config = load_config(CONFIG_FILE)
    api_base = config["fetch"]["api_base"]
    max_retries = config["fetch"]["max_retries"]

    # 随机启动抖动：避免多实例同时请求
    startup_jitter = random.uniform(0, 1.5)
    if startup_jitter > 0.05:
        time.sleep(startup_jitter)

    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        since_dt = dt - timedelta(days=7)
    else:
        now_bj = datetime.now(timezone(timedelta(hours=8)))
        if now_bj.hour < 9:
            now_bj = now_bj - timedelta(days=1)
        since_dt = now_bj - timedelta(days=7)
        target_date = now_bj.strftime("%Y-%m-%d")

    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    all_items = []
    cursor = ""
    remaining = 150

    for page_idx in range(3):
        # 分页之间添加退避与抖动（第一页不等待）
        if page_idx > 0:
            base_backoff = 2 ** (page_idx - 1)
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] Waiting {backoff:.1f}s before next page...", file=sys.stderr)
            time.sleep(backoff)

        url = ("/items?mode=all&category=paper&since=" + since_iso +
               "&take=" + str(min(remaining, 100)))
        if cursor:
            url += "&cursor=" + cursor
        data = api_get(url, base_url=api_base, max_retries=max_retries)
        if not data or "items" not in data:
            break
        items = data.get("items", [])
        all_items.extend(items)
        remaining -= len(items)
        if not data.get("hasNext") or remaining <= 0:
            break
        cursor = data.get("nextCursor", "")
        if not cursor:
            break

    print("[INFO] Fetched", len(all_items), "papers total", file=sys.stderr)
    return all_items, target_date


# ─── Step 2: 去重 ───

def dedup_data(items, config=None):
    """Step 2: URL 去重 + 语义去重 + 选出 top papers。返回 papers。"""
    # 1. URL 去重
    seen = set()
    url_deduped = []
    for p in items:
        url = p.get("url") or ""
        key = urllib.parse.urldefrag(url)[0]
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        url_deduped.append(p)

    # 2. 语义去重
    sem_cfg = (config or {}).get("semantic_dedup", {})
    if sem_cfg.get("enabled", False):
        api_key_env = sem_cfg.get("api_key_env", "EMBEDDING_API_KEY")
        api_key = os.environ.get(api_key_env) or _dot_env.get(api_key_env, "")
        base_url = sem_cfg.get("base_url", "")
        model = sem_cfg.get("model", "text-embedding-3-small")
        threshold = float(sem_cfg.get("threshold", 0.85))
        batch_size = int(sem_cfg.get("batch_size", 10))

        if api_key and base_url:
            before = len(url_deduped)
            url_deduped = semantic_dedup(url_deduped, threshold, api_key, base_url, model, batch_size)
            if len(url_deduped) != before:
                print(f"[INFO] Semantic dedup: {before} -> {len(url_deduped)}", file=sys.stderr)
        else:
            print("[WARN] Semantic dedup enabled but API key or base_url not configured", file=sys.stderr)

    # 3. 选出 top papers
    papers = select_top_papers(url_deduped, limit=50, config=config)

    return papers


def select_top_papers(items, limit=50, config=None):
    selected = [i for i in items if i.get("selected")]
    not_selected = [i for i in items if not i.get("selected")]
    selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    not_selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    result = selected[:limit]
    if len(result) < limit:
        result += not_selected[:limit - len(result)]

    # 如果未启用语义去重，使用标题前缀作为兜底去重
    sem_enabled = (config or {}).get("semantic_dedup", {}).get("enabled", False)
    if not sem_enabled:
        seen = set()
        unique = []
        for p in result:
            key = p.get("title", "")[:30]
            if key not in seen:
                seen.add(key)
                unique.append(p)
        result = unique

    result.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return result[:limit]


# ─── Step 3: 生成 HTML ───

def sanitize(s):
    """Remove lone surrogates and other invalid Unicode from a string."""
    if not isinstance(s, str):
        return s
    return s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def get_badge_color(source):
    sl = (source or "").lower()
    for key, (bg, text) in SOURCE_COLORS.items():
        if key in sl:
            return (bg, text)
    return ("#f0f0f0", "#555555")


def get_badge_label(source):
    s = source or ""
    for sep in ["\uff1a", ":"]:
        if sep in s:
            s = s.split(sep)[0].strip()
    if "(" in s:
        s = s.split("(")[0].strip()
    if len(s) > 20:
        s = s[:20] + "\u2026"
    return s


def group_by_date(papers):
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


def generate_html(papers, date_str):
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
            title = sanitize(p.get("title", "") or "")
            source = sanitize(p.get("source", "") or "")
            summary = sanitize(p.get("summary", "") or "") or "\u6682\u65e0\u6458\u8981"
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


# ─── Main ───

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据
    items, date_str = fetch_data(target_date, config)

    # Step 2: 去重
    papers = dedup_data(items, config)

    # Step 3: 生成 HTML
    html = generate_html(papers, date_str)

    # Step 4: 写入文件
    write_files(html, date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 5: Git 提交
    git_commit(date_str, ["papers.html", f"papers-archive/{date_str}.html"], "papers archive", OUTPUT_DIR)


if __name__ == "__main__":
    main()
