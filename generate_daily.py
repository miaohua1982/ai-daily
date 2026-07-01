#!/usr/bin/env python3
"""
AI HOT Daily Dashboard Generator
Fetches daily AI news from aihot.virxact.com and generates a static HTML dashboard.
Usage: python generate_daily.py [YYYY-MM-DD]
"""

import os
import sys
import json
import time
import random
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from utils import load_dot_env, semantic_dedup, load_config, write_files, git_commit, api_get, esc_html, esc_attr
from utils.html_template import (
    render_news_html,
    NEWS_CARD_TEMPLATE,
    NEWS_SECTION_TEMPLATE,
    NEWS_EMPTY_SECTION_TEMPLATE,
)

OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "news-archive"
INDEX_FILE = OUTPUT_DIR / "daily_news.html"
CONFIG_FILE = OUTPUT_DIR / "config" / "news_config.yaml"

# Load secrets (env > .env file)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")

CATEGORY_LABELS = {
    "ai-models": "模型发布/更新",
    "ai-products": "产品发布/更新",
    "industry": "行业动态",
    "paper": "论文研究",
    "tip": "技巧与观点",
}
# Reverse mapping: Chinese label → English slug (API now uses Chinese labels)
LABEL_TO_SLUG = {v: k for k, v in CATEGORY_LABELS.items()}
CATEGORY_ORDER = ["ai-models", "ai-products", "industry", "paper", "tip"]
CATEGORY_COLORS = {
    "ai-models": "#6366f1",
    "ai-products": "#0891b2",
    "industry": "#d97706",
    "paper": "#7c3aed",
    "tip": "#059669",
}

EMPTY_ICONS = {
    "ai-models": "📭",
    "ai-products": "📦",
    "industry": "📰",
    "paper": "📄",
    "tip": "💡",
}


# ─── Step 1: 获取数据 ───

def fetch_data(target_date=None, config=None):
    """Step 1: 获取每日新闻原始数据。返回 (data, date_str)。"""
    if config is None:
        config = load_config(CONFIG_FILE)
    api_base = config["fetch"]["api_base"]
    max_retries = config["fetch"]["max_retries"]

    # 随机启动抖动：避免多实例同时请求
    startup_jitter = random.uniform(0, 1.5)
    if startup_jitter > 0.05:
        time.sleep(startup_jitter)

    if target_date:
        date_str = target_date
    else:
        bj = datetime.now(timezone(timedelta(hours=8)))
        if bj.hour < 8:
            bj = bj - timedelta(days=1)
        date_str = bj.strftime("%Y-%m-%d")

    print(f"[INFO] Fetching daily for {date_str} ...")
    data = api_get(f"/daily/{date_str}", base_url=api_base, max_retries=max_retries)
    if data and "sections" in data:
        sections = data["sections"]
        total = sum(len(s.get("items", [])) for s in sections)
        print(f"[INFO] Got daily {date_str}: {len(sections)} sections, {total} items")
        return data, date_str

    print(f"[WARN] Daily {date_str} not available, falling back to latest...")
    dailies = api_get("/dailies?take=5", base_url=api_base, max_retries=max_retries)
    if dailies and dailies.get("items"):
        latest = dailies["items"][0]["date"]
        available = [d["date"] for d in dailies["items"]]
        print(f"[INFO] Fallback to {latest} (available dates: {available})")
        data = api_get(f"/daily/{latest}", base_url=api_base, max_retries=max_retries)
        if data and "sections" in data:
            sections = data["sections"]
            total = sum(len(s.get("items", [])) for s in sections)
            print(f"[INFO] Got daily {latest}: {len(sections)} sections, {total} items")
        return data, latest

    raise RuntimeError("Failed to fetch any daily report")


# ─── Step 2: 去重 ───

def dedup_data(data, config=None):
    """Step 2: 对原始数据做 URL 去重 + 语义去重，重建分类分组。返回 items_by_cat。"""
    sections = data.get("sections", [])

    # 提取所有 item，记录 item id → category 映射
    all_items = []
    id_to_cat = {}
    for sec in sections:
        label = sec.get("label", "")
        cat = LABEL_TO_SLUG.get(label, "")
        for item in sec.get("items", []):
            all_items.append(item)
            id_to_cat[item.get("id", "")] = cat

    # 1. URL 去重
    seen_urls = set()
    url_deduped = []
    for p in all_items:
        url = p.get("sourceUrl") or p.get("url") or ""
        key = urllib.parse.urldefrag(url)[0]
        if key and key in seen_urls:
            continue
        if key:
            seen_urls.add(key)
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

    # 重建 items_by_cat（去重后）
    items_by_cat = {}
    for it in url_deduped:
        cat = id_to_cat.get(it.get("id", ""), "")
        items_by_cat.setdefault(cat, []).append(it)

    return items_by_cat


# ─── Step 3: 生成 HTML ───

def fmt_time(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        dt = dt.astimezone(timezone(timedelta(hours=8)))
        now = datetime.now(timezone(timedelta(hours=8)))
        diff = now - dt
        s = diff.total_seconds()
        if s < 3600:
            return f"{max(1, int(s // 60))} 分钟前"
        elif s < 86400:
            return f"{int(s // 3600)} 小时前"
        else:
            return dt.strftime("今天 %H:%M")
    except Exception:
        return dt_str or ""


def source_class(source_name):
    s = (source_name or "").lower()
    if "x：" in s or "twitter" in s or s.startswith("x:"):
        return "source-x"
    if "公众号" in s or "wechat" in s or "微信" in s:
        return "source-wechat"
    if "github" in s:
        return "source-gh"
    if any(x in s for x in ["marktechpost", "cloudflare", "dwarkesh", "elastic", "rss"]):
        return "source-blog"
    if any(x in s for x in ["hacker news", "hn ", "buzzing", "eff"]):
        return "source-hn"
    return "source-media"


def short_source(source_name):
    """Extract a 2-4 char label from the full sourceName."""
    s = (source_name or "").lower()
    if "x：" in s or s.startswith("x:"):
        return "X"
    if "公众号" in s:
        return "公众号"
    if "github" in s:
        return "GitHub"
    if "marktechpost" in s:
        return "博客"
    if "rss" in s:
        return "RSS"
    if "arxiv" in s:
        return "arXiv"
    if "hacker news" in s or "buzzing" in s:
        return "HN"
    words = source_name.split()
    if words:
        first = words[0].rstrip("：:")
        return first[:6]
    return "来源"


def summarize(text, max_len=60):
    if not text:
        return "暂无摘要"
    t = text.strip()
    return t if len(t) <= max_len else t[:max_len - 1].rstrip() + "…"



def generate_html(items_by_cat, data, date_str):
    """Step 3: 纯 HTML 渲染，不含去重逻辑。"""
    cat_counts = {cat: len(items_by_cat.get(cat, [])) for cat in CATEGORY_ORDER}
    total = sum(cat_counts.values())

    # Display date
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        wd = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][d.weekday()]
        display_date = f"{d.year}年{d.month}月{d.day}日 · {wd}"
    except Exception:
        display_date = date_str

    # Compute relative time from daily window
    window_relative = ""
    try:
        w_end_str = data.get("windowEnd", "")
        w_end = datetime.fromisoformat(w_end_str.replace("Z", "+00:00"))
        w_end_bj = w_end.astimezone(timezone(timedelta(hours=8)))
        now_bj = datetime.now(timezone(timedelta(hours=8)))
        diff_hours = int((now_bj - w_end_bj).total_seconds() // 3600)
        if diff_hours <= 0:
            window_relative = "今天上午"
        elif diff_hours < 24:
            window_relative = f"{diff_hours} 小时前"
        else:
            days = diff_hours // 24
            window_relative = f"{days} 天前"
    except Exception:
        window_relative = ""

    # ── Build card HTML (global numbering) ──
    cards_parts = {}
    global_idx = 0
    for cat in CATEGORY_ORDER:
        cards_parts[cat] = []
        for item in items_by_cat.get(cat, []):
            global_idx += 1
            title = esc_html(item.get("title", "无标题"))
            summary = esc_html(summarize(item.get("summary", ""), 60))
            url = item.get("sourceUrl") or item.get("url", "#")
            url_attr = esc_attr(url)
            source_name = item.get("sourceName", "")
            source_short = esc_html(short_source(source_name))
            sc = source_class(source_name)
            time_str = window_relative

            cards_parts[cat].append(
                NEWS_CARD_TEMPLATE.format(
                    idx=global_idx,
                    title=title,
                    source_short=source_short,
                    source_class=sc,
                    summary=summary,
                    time_str=time_str,
                    url=url_attr,
                )
            )

    # ── Build sections HTML ──
    sections_parts = []
    for cat in CATEGORY_ORDER:
        label = CATEGORY_LABELS[cat]
        color = CATEGORY_COLORS[cat]
        count = cat_counts[cat]

        if count == 0:
            icon = EMPTY_ICONS.get(cat, "📌")
            sections_parts.append(
                NEWS_EMPTY_SECTION_TEMPLATE.format(
                    cat=cat, color=color, label=label, icon=icon,
                )
            )
        else:
            cards_html = "\n".join(cards_parts[cat])
            sections_parts.append(
                NEWS_SECTION_TEMPLATE.format(
                    cat=cat, color=color, label=label, count=count,
                    cards_html=cards_html,
                )
            )

    sections_html = "\n".join(sections_parts)

    # ── Build nav items ──
    nav_items_parts = []
    for cat in CATEGORY_ORDER:
        lbl = CATEGORY_LABELS[cat]
        cnt = cat_counts[cat]
        nav_items_parts.append(
            f'    <a href="#sec-{cat}" class="nav-link">\n'
            f'      <span class="nav-dot" style="background:{CATEGORY_COLORS[cat]}"></span>{lbl}\n'
            f'      <span class="nav-cnt">{cnt}</span>\n'
            f'    </a>'
        )
    nav_items = "\n".join(nav_items_parts)

    return render_news_html(
        display_date=display_date,
        total=total,
        nav_items=nav_items,
        sections_html=sections_html,
    )


# ─── Main ───

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据
    data, date_str = fetch_data(target_date, config)

    # Step 2: 去重
    items_by_cat = dedup_data(data, config)

    # Step 3: 生成 HTML
    html = generate_html(items_by_cat, data, date_str)

    # Step 4: 写入文件
    write_files(html, date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 5: Git 提交
    git_commit(date_str, ["daily_news.html", f"news-archive/{date_str}.html"], "daily dashboard", OUTPUT_DIR)


if __name__ == "__main__":
    main()
