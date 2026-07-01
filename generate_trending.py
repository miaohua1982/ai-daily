#!/usr/bin/env python3
"""
Trending Radar Generator
直接调用 NewsNow API，按关键词 / AI 过滤生成趋势雷达静态页面。
用法：python generate_trending.py [YYYY-MM-DD]
"""

import os
import sys
import json
import re
import time
import random
from collections import defaultdict
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from utils import load_dot_env, semantic_dedup, load_config, write_files, git_commit, UA, esc_html, esc_attr
from utils.html_template import (
    render_trending_html,
    TRENDING_CARD_TEMPLATE,
    TRENDING_SECTION_TEMPLATE,
)

# ── 配置 ──
OUTPUT_DIR = Path(__file__).parent
CONFIG_FILE = OUTPUT_DIR / "config" / "trending_config.yaml"
ARCHIVE_DIR = OUTPUT_DIR / "trending-archive"
INDEX_FILE = OUTPUT_DIR / "trending.html"

# ── Load secrets ───────────────────────────────────────────────
# Priority: environment variables (GitHub Actions) > .env file (local dev)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")


# ─── Step 1: 获取数据 ───

def fetch_source(api_url, source_id, max_retries=3):
    """从 NewsNow 获取单个数据源，失败时进行指数退避重试。"""
    startup_jitter = random.uniform(0, 1.5)
    if startup_jitter > 0.05:
        time.sleep(startup_jitter)

    url = f"{api_url}?id={source_id}&latest"

    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            items = data.get("items", [])
            for it in items:
                it["source_id"] = source_id
            print(f"[INFO] {source_id}: {len(items)} items")
            return items
        except urllib.error.HTTPError as e:
            print(f"[WARN] HTTP {e.code} for {source_id} (attempt {attempt+1}/{max_retries}): {url}", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Failed to fetch {source_id} (attempt {attempt+1}/{max_retries}): {e}", file=sys.stderr)

        if attempt < max_retries - 1:
            base_backoff = 2 ** attempt
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] Retrying {source_id} after {backoff:.1f}s (jitter)...", file=sys.stderr)
            time.sleep(backoff)

    return []


def fetch_data(config):
    """Step 1: 获取所有 NewsNow 数据源。返回 items。"""
    api_url = config["newsnow"]["api_url"]
    sources = config["newsnow"]["sources"]
    group_map = {s["id"]: s.get("group", "") for s in sources}
    max_retries = config.get("newsnow", {}).get("max_retries", 3)

    items = []
    for idx, s in enumerate(sources):
        if idx > 0:
            base_backoff = 2 ** (idx - 1)
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] Waiting {backoff:.1f}s before fetching {s['id']}...", file=sys.stderr)
            time.sleep(backoff)

        src_items = fetch_source(api_url, s["id"], max_retries=max_retries)
        src_group = group_map.get(s["id"], "")
        for it in src_items:
            it["source_group"] = src_group
        items.extend(src_items)

    print(f"[INFO] Total raw items: {len(items)}")
    return items


# ─── Step 2: 去重 ───

def dedup_data(items, config):
    """Step 2: URL 去重 + 语义去重。返回去重后的 items。"""
    # ── 1. URL 去重 ──
    seen = set()
    out = []
    for it in items:
        url = it.get("url") or it.get("mobileUrl") or ""
        key = urllib.parse.urldefrag(url)[0]
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(it)

    # ── 2. 语义去重（按 source_group 分组）──
    sem_cfg = config.get("filter", {}).get("semantic_dedup", {})
    if sem_cfg.get("enabled", False):
        api_key_env = sem_cfg.get("api_key_env", "DEEPSEEK_API_KEY")
        api_key = os.environ.get(api_key_env) or _dot_env.get(api_key_env, "")
        base_url = sem_cfg.get("base_url", "")
        model = sem_cfg.get("model", "text-embedding-3-small")
        threshold = float(sem_cfg.get("threshold", 0.85))
        batch_size = int(sem_cfg.get("batch_size", 10))

        if api_key and base_url:
            groups = defaultdict(list)
            no_group = []
            for it in out:
                sg = it.get("source_group", "")
                if sg:
                    groups[sg].append(it)
                else:
                    no_group.append(it)

            result = list(no_group)
            for group_name, group_items in groups.items():
                if len(group_items) <= 1:
                    result.extend(group_items)
                    continue
                before = len(group_items)
                deduped = semantic_dedup(group_items, threshold, api_key, base_url, model, batch_size)
                if len(deduped) != before:
                    print(f"[INFO] Semantic dedup ({group_name}): {before} -> {len(deduped)}", file=sys.stderr)
                result.extend(deduped)
            out = result
        else:
            print("[WARN] Semantic dedup enabled but embedding API key or base_url not configured", file=sys.stderr)

    print(f"[INFO] After dedup: {len(out)}")
    return out


# ─── Step 3: 过滤 ───

def assign_group_names(items, config):
    """给每个 item 标注最匹配的 group_name。"""
    groups = config.get("keywords", {}).get("groups", [])
    result = []
    for item in items:
        title = (item.get("title") or "").lower()
        assigned_group = None
        for g in groups:
            terms = [str(t).lower() for t in g.get("terms", [])]
            excludes = [str(e).lower() for e in g.get("exclude", [])]
            if any(e in title for e in excludes):
                continue
            if any(t in title for t in terms):
                assigned_group = g["name"]
                break
        if assigned_group:
            item = item.copy()
            item["group_name"] = assigned_group
        result.append(item)
    return result


def keyword_filter(items, config):
    """按关键词组匹配，返回命中列表和未命中列表。"""
    result = []
    unmatched = []
    for item in assign_group_names(items, config):
        if "group_name" in item:
            result.append(item)
        else:
            unmatched.append(item)
    return result, unmatched


def ai_score_batch(batch, interests, group_names, api_key, base_url, model):
    """把一批标题发给 LLM，返回 idx -> {"score": float, "group": str} 字典。"""
    lines = "\n".join(f"{i+1}. {it['title']}" for i, it in enumerate(batch))
    group_list = "\n".join(f"- {g}" for g in group_names)
    prompt = f"""你是一位信息筛选与分类助手。请判断以下新闻标题与用户兴趣的相关程度，并从给定的分组中挑选最匹配的一个。

用户兴趣：
{interests}

可选分组（必须从中选择；如果与所有分组都不匹配，分组名称留空）：
{group_list}

新闻标题（每行一个编号）：
{lines}

请按以下格式返回每行的相关性评分（0-1，1 表示高度相关）和分组名称：
1: 0.9 | AI 大模型
2: 0.3 |
3: 0.8 | 财经资讯
...

只返回编号、分数和分组，不要解释。"""

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "disabled"},
        "stream": False,
        "max_tokens": 4096,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{base_url.rstrip('/')}/chat/completions"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"]
        results = {}
        valid_groups = set(group_names)
        for line in content.splitlines():
            m = re.match(r"\s*(\d+)\s*[:：]\s*([0-9.]+)\s*(?:\|\s*(.*?))?\s*$", line)
            if m:
                idx = int(m.group(1)) - 1
                score = max(0.0, min(1.0, float(m.group(2))))
                group = m.group(3).strip() if m.group(3) else ""
                if group not in valid_groups:
                    group = ""
                if 0 <= idx < len(batch):
                    results[idx] = {"score": score, "group": group}
        return results
    except Exception as e:
        print(f"[WARN] AI scoring batch failed: {e}", file=sys.stderr)
        return {}


def ai_filter(items, config, assign_groups=True):
    """对 items 进行 AI 打分过滤；若 assign_groups=True 则同时由 AI 分组。"""
    ai_cfg = config.get("ai", {})
    api_key_env = ai_cfg.get("api_key_env", "DEEPSEEK_API_KEY")
    api_key = os.environ.get(api_key_env) or _dot_env.get(api_key_env, "")
    if not api_key:
        print("[WARN] AI enabled but API key not found, skipping AI filter", file=sys.stderr)
        return items

    base_url = ai_cfg.get("base_url", "https://api.deepseek.com")
    model = ai_cfg.get("model", "deepseek-chat")
    min_score = float(ai_cfg.get("min_score", 0.7))
    batch_size = int(ai_cfg.get("batch_size", 30))
    interests = ai_cfg.get("interests", "")
    group_names = [g["name"] for g in config.get("keywords", {}).get("groups", [])]

    retained = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        results = ai_score_batch(batch, interests, group_names, api_key, base_url, model)
        for idx, it in enumerate(batch):
            res = results.get(idx, {"score": 0.0, "group": ""})
            it["ai_score"] = res["score"]
            if res["score"] >= min_score:
                if assign_groups and res["group"]:
                    it["group_name"] = res["group"]
                retained.append(it)
        kept = sum(1 for r in results.values() if r.get("score", 0) >= min_score)
        print(f"[INFO] AI batch {i//batch_size+1}: kept {kept}/{len(batch)}")
    return retained


def filter_data(items, config):
    """Step 3: 关键词 / AI 过滤 + 分组。返回 grouped_items。"""
    method = config.get("filter", {}).get("method", "keyword")

    if method == "ai":
        matched = ai_filter(items, config, assign_groups=True)
    else:
        matched, unmatched = keyword_filter(items, config)
        if method == "both":
            matched = ai_filter(matched, config, assign_groups=False)

    grouped_items = {}
    for it in matched:
        gname = it.get("group_name", "其他")
        grouped_items.setdefault(gname, []).append(it)

    return grouped_items


# ─── Step 4: 生成 HTML ───

def source_meta(item, config):
    """返回 (来源名称, 图标, 热度文本)。"""
    sid = item.get("source_id", "")
    for s in config["newsnow"]["sources"]:
        if s["id"] == sid:
            return s["name"], s.get("icon", "•"), ""
    return sid, "•", ""


def format_updated(ts):
    if not ts:
        return ""
    try:
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def generate_html(grouped_items, config, build_time):
    """Step 4: 纯 HTML 渲染，不含去重或过滤逻辑。"""
    # 强制按固定顺序展示分组
    desired_order = ["国际局势", "财经资讯", "AI大模型", "智能汽车", "机器人与具身智能", "其他"]
    ordered = {}
    for name in desired_order:
        if name in grouped_items:
            ordered[name] = grouped_items[name]
    for name, items in grouped_items.items():
        if name not in ordered:
            ordered[name] = items
    grouped_items = ordered

    total = sum(len(v) for v in grouped_items.values())

    # 为每个分组分配颜色
    group_colors = [
        "#6366f1", "#0891b2", "#d97706", "#7c3aed", "#059669",
        "#dc2626", "#2563eb", "#ea580c", "#0891b2", "#be185d"
    ]
    color_map = {}
    for i, group_name in enumerate(grouped_items.keys()):
        color_map[group_name] = group_colors[i % len(group_colors)]

    # 构建导航链接
    nav_links_parts = []
    for group_name, items in grouped_items.items():
        if not items:
            continue
        anchor = group_name.replace(" ", "-").lower()
        color = color_map[group_name]
        count = len(items)
        nav_links_parts.append(
            f'    <a href="#sec-{anchor}" class="nav-link">\n'
            f'      <span class="nav-dot" style="background:{color}"></span>{esc_html(group_name)}\n'
            f'      <span class="nav-cnt">{count}</span>\n'
            f'    </a>'
        )
    nav_links = "\n".join(nav_links_parts)

    # 构建分组 sections
    sections_parts = []
    item_counter = 0
    for group_name, items in grouped_items.items():
        if not items:
            continue
        anchor = group_name.replace(" ", "-").lower()
        color = color_map[group_name]
        count = len(items)

        cards_parts = []
        for it in items:
            item_counter += 1
            idx = item_counter
            title = esc_html(it.get("title", "无标题"))
            url = it.get("url") or it.get("mobileUrl") or "#"
            url_attr = esc_attr(url)
            src_name, _, _ = source_meta(it, config)

            source_class = "source-x"
            if "wechat" in src_name.lower() or "微信" in src_name:
                source_class = "source-wechat"
            elif "blog" in src_name.lower() or "博客" in src_name:
                source_class = "source-blog"
            elif "hacker" in src_name.lower() or "hn" in src_name.lower():
                source_class = "source-hn"
            elif "github" in src_name.lower() or "gh" in src_name.lower():
                source_class = "source-gh"

            score_badge = ""
            if "ai_score" in it:
                score = it["ai_score"]
                if score >= 0.8:
                    score_badge = f'<span class="score-badge score-high">关联度：{score:.2f}</span>'
                elif score >= 0.6:
                    score_badge = f'<span class="score-badge score-mid">关联度：{score:.2f}</span>'
                else:
                    score_badge = f'<span class="score-badge score-low">关联度：{score:.2f}</span>'

            updated = format_updated(it.get("updatedTime"))
            time_str = f"{updated}" if updated else ""

            cards_parts.append(
                TRENDING_CARD_TEMPLATE.format(
                    idx=idx,
                    title=title,
                    source_class=source_class,
                    source_name=esc_html(src_name),
                    time_str=time_str,
                    score_badge=score_badge,
                    url=url_attr,
                )
            )

        cards_html = "\n".join(cards_parts)
        sections_parts.append(
            TRENDING_SECTION_TEMPLATE.format(
                anchor=anchor,
                color=color,
                group_name=esc_html(group_name),
                count=count,
                cards_html=cards_html,
            )
        )

    sections_html = "\n".join(sections_parts)

    display_date = build_time.strftime("%Y-%m-%d %H:%M")
    wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][build_time.weekday()]

    return render_trending_html(
        total=total,
        group_count=len(grouped_items),
        display_date=display_date,
        weekday=wd,
        nav_links=nav_links,
        sections_html=sections_html,
    )


# ─── Main ───

def main():
    if not CONFIG_FILE.exists():
        print(f"[ERROR] Config file not found: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    config = load_config(CONFIG_FILE)

    # Step 1: 获取数据
    items = fetch_data(config)

    # Step 2: 去重
    items = dedup_data(items, config)

    # Step 3: 过滤
    grouped_items = filter_data(items, config)

    # 构建时间戳
    now = datetime.now(timezone(timedelta(hours=8)))
    if len(sys.argv) > 1:
        try:
            now = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=8)))
        except Exception:
            pass

    # Step 4: 生成 HTML
    html = generate_html(grouped_items, config, now)

    # Step 5: 写入文件
    date_str = now.strftime("%Y-%m-%d-%H")
    write_files(html, date_str, INDEX_FILE, ARCHIVE_DIR)

    # Step 6: Git 提交
    git_commit(date_str, ["trending.html", f"trending-archive/{date_str}.html"], "trending radar", OUTPUT_DIR)


if __name__ == "__main__":
    main()
