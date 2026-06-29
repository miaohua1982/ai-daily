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
from dotenv_helper import load_dot_env

# ── 配置 ──
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
CONFIG_FILE = Path(__file__).parent / "trending_config.yaml"
OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "trending-archive"
INDEX_FILE = OUTPUT_DIR / "trending.html"

# ── Load secrets ───────────────────────────────────────────────
# Priority: environment variables (GitHub Actions) > .env file (local dev)
_dot_env = load_dot_env(OUTPUT_DIR / ".env")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or _dot_env.get("DEEPSEEK_API_KEY", "")
# 把加载的 API Key 设置到环境变量，供 ai_filter 使用
if DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY


def _is_quoted(s):
    return (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'"))


def _split_key_value(s):
    """拆分 key: value，忽略引号内的冒号。"""
    in_quote = None
    for idx, ch in enumerate(s):
        if ch in ('"', "'"):
            if in_quote is None:
                in_quote = ch
            elif in_quote == ch:
                in_quote = None
        elif ch == ":" and in_quote is None:
            key = s[:idx].strip()
            val = s[idx + 1:].strip()
            return key, val
    return s, ""


def _parse_scalar(s):
    """解析 YAML 标量。"""
    s = s.strip()
    if not s:
        return None
    if _is_quoted(s):
        return s[1:-1]
    if s in ("true", "True", "yes", "on"):
        return True
    if s in ("false", "False", "no", "off"):
        return False
    if s in ("null", "None", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _load_yaml_minimal(path):
    """纯标准库 YAML 子集解析器，支持本配置用到的字典、列表、多行字符串。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    tokens = []
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        tokens.append((indent, line.strip()))

    def parse_block(i, base_indent):
        if i >= len(tokens):
            return None, i
        first_indent = tokens[i][0]
        if first_indent < base_indent:
            return None, i

        if tokens[i][1].startswith("- "):
            # 列表
            result = []
            while i < len(tokens):
                indent, content = tokens[i]
                if indent < first_indent:
                    break
                if indent > first_indent:
                    i += 1
                    continue
                if not content.startswith("- "):
                    break
                value_text = content[2:].strip()
                if value_text == "":
                    child, i = parse_block(i + 1, first_indent)
                    result.append(child if child is not None else None)
                elif ":" in value_text and not _is_quoted(value_text):
                    key, val = _split_key_value(value_text)
                    child_dict = {key: _parse_scalar(val)}
                    i += 1
                    # 解析同列表项下的 key-value 字段
                    while i < len(tokens):
                        ni, nc = tokens[i]
                        if ni <= first_indent:
                            break
                        if nc.startswith("- "):
                            break
                        if ":" in nc:
                            k, v = _split_key_value(nc)
                            if v == "|":
                                block_lines = []
                                i += 1
                                while i < len(tokens) and tokens[i][0] > ni:
                                    block_lines.append(tokens[i][1])
                                    i += 1
                                child_dict[k] = "\n".join(block_lines)
                            elif v == "":
                                child, i = parse_block(i + 1, ni)
                                child_dict[k] = child if child is not None else _parse_scalar(v)
                            else:
                                child_dict[k] = _parse_scalar(v)
                                i += 1
                        else:
                            i += 1
                    result.append(child_dict)
                else:
                    result.append(_parse_scalar(value_text))
                    i += 1
            return result, i
        else:
            # 字典
            result = {}
            while i < len(tokens):
                indent, content = tokens[i]
                if indent < first_indent:
                    break
                if indent > first_indent:
                    i += 1
                    continue
                if ":" not in content:
                    i += 1
                    continue
                key, val = _split_key_value(content)
                if val == "|":
                    block_lines = []
                    i += 1
                    while i < len(tokens) and tokens[i][0] > first_indent:
                        block_lines.append(tokens[i][1])
                        i += 1
                    result[key] = "\n".join(block_lines)
                    continue
                if val == "":
                    child, i = parse_block(i + 1, first_indent)
                    result[key] = child if child is not None else _parse_scalar(val)
                else:
                    result[key] = _parse_scalar(val)
                    i += 1
            return result, i

    if not tokens:
        return {}
    result, _ = parse_block(0, -1)
    return result if result is not None else {}


def load_yaml(path):
    """加载 YAML 配置。优先使用 PyYAML，未安装时回退到纯标准库解析器。"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        return _load_yaml_minimal(path)


def fetch_source(api_url, source_id, max_retries=3):
    """从 NewsNow 获取单个数据源，失败时进行指数退避重试。"""
    # 随机启动抖动：避免所有线程同时请求同一 API
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
        
        # 如果不是最后一次尝试，则等待后重试
        if attempt < max_retries - 1:
            base_backoff = 2 ** attempt
            backoff = random.uniform(0, base_backoff)  # 全抖动：0 ~ base_backoff 之间的随机值
            print(f"[INFO] Retrying {source_id} after {backoff:.1f}s (jitter)...", file=sys.stderr)
            time.sleep(backoff)
    
    return []


def fetch_all_sources(config):
    """顺序获取所有数据源，source 之间使用指数退避。
    同时为每条 item 标注 source_group（来自 config 中 source 的 group 字段）。
    """
    api_url = config["newsnow"]["api_url"]
    sources = config["newsnow"]["sources"]
    # 建立 source_id -> group 的映射
    group_map = {s["id"]: s.get("group", "") for s in sources}
    max_retries = config.get("newsnow", {}).get("max_retries", 3)
    items = []

    for idx, s in enumerate(sources):
        # 第一个 source 不等待，后续 source 指数退避
        if idx > 0:
            base_backoff = 2 ** (idx - 1)
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] Waiting {backoff:.1f}s before fetching {s['id']}...", file=sys.stderr)
            time.sleep(backoff)

        src_items = fetch_source(api_url, s["id"], max_retries=max_retries)
        # 为每条 item 标注 source_group
        src_group = group_map.get(s["id"], "")
        for it in src_items:
            it["source_group"] = src_group
        items.extend(src_items)

    return items


def assign_group_names(items, config):
    """给每个 item 标注最匹配的 group_name；命中则返回副本并写入 group_name，未命中返回原 item。"""
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
    """按关键词组匹配，给每个 item 标注 group_name，返回命中列表和未命中列表。"""
    result = []
    unmatched = []

    for item in assign_group_names(items, config):
        if "group_name" in item:
            result.append(item)
        else:
            unmatched.append(item)

    return result, unmatched


def dedup(items, config=None):
    """
    1. 按 url 去重，保留首次出现。
    2. 如果配置了语义去重，在同一 source_group 内部再做 embedding 相似度去重。
    """
    # ── 1. URL 去重 ──────────────────────────────────
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

    # ── 2. 语义去重（按 source_group 分组）────────────
    if config is None:
        return out

    sem_cfg = config.get("filter", {}).get("semantic_dedup", {})
    if not sem_cfg.get("enabled", False):
        return out

    api_key_env = sem_cfg.get("api_key_env", "")
    api_key = os.environ.get(api_key_env) or _dot_env.get(api_key_env, "")
    base_url   = sem_cfg.get("base_url", "")
    model      = sem_cfg.get("model", "text-embedding-3-small")
    threshold   = float(sem_cfg.get("threshold", 0.85))
    batch_size  = int(sem_cfg.get("batch_size", 10))

    if not api_key or not base_url:
        print("[WARN] Semantic dedup enabled but embedding API key or base_url not configured", file=sys.stderr)
        return out

    # 按 source_group 分组（空字符串的 group 单独处理，不做语义去重）
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

        # 调用 embedding API 做语义去重
        titles = [it.get("title", "") for it in group_items]
        embeddings = get_embeddings(titles, api_key, base_url, model, batch_size)
        if embeddings is None or len(embeddings) != len(group_items):
            print(f"[WARN] Semantic dedup skipped for group '{group_name}': embedding API failed", file=sys.stderr)
            result.extend(group_items)
            continue

        keep = [True] * len(group_items)
        removed = 0
        for i in range(len(group_items)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(group_items)):
                if not keep[j]:
                    continue
                sim = cosine_similarity(embeddings[i], embeddings[j])
                if sim >= threshold:
                    keep[j] = False
                    removed += 1
                    print(f"[INFO] Semantic dedup ({group_name}): drop '{titles[j][:40]}...' (sim={sim:.3f})", file=sys.stderr)

        deduped = [group_items[i] for i in range(len(group_items)) if keep[i]]
        if removed > 0:
            print(f"[INFO] Semantic dedup ({group_name}): {len(group_items)} -> {len(deduped)}", file=sys.stderr)
        result.extend(deduped)

    return result


def get_embeddings(texts, api_key, base_url, model, batch_size=10):
    """
    批量获取文本 embedding，使用 OpenAI 兼容接口。
    部分模型（如阿里 Qwen）单次请求最多支持 batch_size 条文本，
    因此分批发送请求，结果按顺序拼接后返回。
    返回 list[list[float]]，失败时返回 None。
    """
    if not texts:
        return []

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    url = f"{base_url.rstrip('/')}/embeddings"
    all_embeddings = []
    total = len(texts)

    for start in range(0, total, batch_size):
        batch = list(texts[start:start + batch_size])
        payload = {
            "model": model,
            "input": batch
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            batch_emb = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(batch_emb)
        except Exception as e:
            print(f"[WARN] get_embeddings batch {start}-{start + len(batch)} failed: {e}", file=sys.stderr)
            return None

    return all_embeddings


def cosine_similarity(a, b):
    """计算两个向量的余弦相似度。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_dedup_items(items, threshold, api_key, base_url, model):
    """
    对同一分组内的条目做语义去重。
    计算所有标题的 embedding，两两比较余弦相似度，
    相似度 >= threshold 时移除后者（保留第一个）。
    """
    if len(items) <= 1:
        return items

    titles = [it.get("title", "") for it in items]
    embeddings = get_embeddings(titles, api_key, base_url, model)

    if embeddings is None:
        print("[WARN] Semantic dedup skipped: embedding API unavailable", file=sys.stderr)
        return items

    if len(embeddings) != len(items):
        print(f"[WARN] Semantic dedup skipped: embedding count mismatch ({len(embeddings)} vs {len(items)})", file=sys.stderr)
        return items

    keep = [True] * len(items)
    removed = 0
    for i in range(len(items)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(items)):
            if not keep[j]:
                continue
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                keep[j] = False
                removed += 1
                print(f"[INFO] Semantic dedup: '{titles[j][:40]}...' (sim={sim:.3f})")

    result = [items[i] for i in range(len(items)) if keep[i]]
    if removed > 0:
        print(f"[INFO] Semantic dedup: removed {removed} duplicate(s) within group")
    return result


# ── AI 过滤 ──
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
        "thinking": {
            "type": "disabled"
        },
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
            # 格式: 1: 0.9 | AI 大模型
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

    api_key = os.environ.get(ai_cfg.get("api_key_env", "DEEPSEEK_API_KEY"))
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


# ── HTML 生成 ──

def esc_html(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;")


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
        # NewsNow 返回的 updatedTime 可能是毫秒时间戳
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def build_html(grouped_items, config, build_time):
    # 强制按固定顺序展示分组：国际局势、财经资讯、AI大模型、智能汽车、机器人与具身智能、其他
    desired_order = ["国际局势", "财经资讯", "AI大模型", "智能汽车", "机器人与具身智能", "其他"]
    ordered = {}
    for name in desired_order:
        if name in grouped_items:
            ordered[name] = grouped_items[name]
    # 保留配置中新增但未在固定顺序中声明的分组
    for name, items in grouped_items.items():
        if name not in ordered:
            ordered[name] = items
    grouped_items = ordered

    source_counts = {}
    for group_name, items in grouped_items.items():
        for it in items:
            sid = it.get("source_id", "")
            source_counts[sid] = source_counts.get(sid, 0) + 1

    total = sum(len(v) for v in grouped_items.values())
    source_summary = " · ".join(
        f"{next((s['name'] for s in config['newsnow']['sources'] if s['id']==sid), sid)} {cnt}"
        for sid, cnt in sorted(source_counts.items(), key=lambda x: -x[1])[:5]
    ) or "暂无"

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

        # 构建卡片
        cards_parts = []
        for it in items:
            item_counter += 1
            idx = item_counter
            title = esc_html(it.get("title", "无标题"))
            url = it.get("url") or it.get("mobileUrl") or "#"
            url_attr = esc_attr(url)
            src_name, icon, _ = source_meta(it, config)

            # 来源样式
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

            card_html = f"""        <article class="card" data-reveal>
          <span class="card-num">{idx}</span>
          <div class="card-top">
            <h3 class="card-title">{title}</h3>
            <span class="card-source {source_class}">{esc_html(src_name)}</span>
          </div>
          <div class="card-footer">
            <span class="card-time">{time_str}</span>
            {score_badge}
            <a class="card-link" href="{url_attr}" target="_blank" rel="noopener noreferrer">
              阅读原文
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
            </a>
          </div>
        </article>"""
            cards_parts.append(card_html)

        cards_html = "\n".join(cards_parts)
        section_html = f"""    <section class="section" id="sec-{anchor}">
      <div class="section-header">
        <div class="section-dot" style="background:{color}"></div>
        <h2>{esc_html(group_name)}</h2>
        <span class="section-count">{count} 条</span>
      </div>
      <div class="card-grid">
{cards_html}
      </div>
    </section>"""
        sections_parts.append(section_html)

    sections_html = "\n".join(sections_parts)

    display_date = build_time.strftime("%Y-%m-%d %H:%M")
    wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][build_time.weekday()]
    date_str = f"{display_date} · {wd}"

    # CSS - 普通字符串，花括号不需要转义
    css = """    :root {
      --hero-from: #ff5e3a;
      --hero-mid: #f73b4a;
      --hero-to: #c0392b;
      --accent: #ff6b35;
      --accent-dark: #e0552b;
      --bg: #faf8f6;
      --card-bg: #ffffff;
      --card-border: #ede8e2;
      --text: #2c2c2c;
      --text-secondary: #6b6b6b;
      --text-muted: #999999;
      --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
      --shadow-md: 0 4px 12px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.04);
      --shadow-lg: 0 12px 32px rgba(0,0,0,.1), 0 4px 8px rgba(0,0,0,.05);
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    .hero {
      position: relative; overflow: hidden;
      background: linear-gradient(135deg, var(--hero-from) 0%, var(--hero-mid) 40%, var(--hero-to) 100%);
      color: #fff; padding: 56px 24px 48px; text-align: center;
    }
    .hero::before {
      content: ''; position: absolute; inset: 0;
      background: radial-gradient(ellipse at 70% 30%, rgba(255,255,255,.15) 0%, transparent 60%),
                  radial-gradient(ellipse at 20% 80%, rgba(255,200,120,.12) 0%, transparent 50%);
    }
    .hero-content { position: relative; z-index: 1; max-width: 720px; margin: 0 auto; }
    .hero-badge {
      display: inline-block; background: rgba(255,255,255,.2);
      backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,.25); border-radius: 100px;
      padding: 4px 16px; font-size: 13px; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 16px;
    }
    .hero h1 { font-size: clamp(28px,5vw,44px); font-weight: 800; letter-spacing: -0.5px; margin-bottom: 8px; }
    .hero-sub { font-size: 16px; opacity: 0.85; margin-bottom: 24px; }
    .hero-stats { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }
    .hero-stat {
      display: flex; flex-direction: column; align-items: center;
      background: rgba(255,255,255,.15); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
      border-radius: 12px; padding: 12px 20px; min-width: 80px;
    }
    .hero-stat-num { font-size: 28px; font-weight: 800; line-height: 1.2; }
    .hero-stat-lbl { font-size: 12px; opacity: 0.8; margin-top: 2px; }
    .nav-wrap {
      position: sticky; top: 0; z-index: 100;
      background: rgba(255,255,255,.92); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border); padding: 0 16px;
    }
    .nav-inner { max-width: 1100px; margin: 0 auto; display: flex; gap: 4px; overflow-x: auto; padding: 10px 0; scrollbar-width: none; }
    .nav-inner::-webkit-scrollbar { display: none; }
    .nav-link {
      flex-shrink: 0; display: flex; align-items: center; gap: 6px;
      padding: 8px 16px; border-radius: 100px; font-size: 13.5px; font-weight: 600;
      color: var(--text-secondary); text-decoration: none; transition: 0.3s; white-space: nowrap; border: 1px solid transparent;
    }
    .nav-link:hover { background: #f5f0eb; color: var(--accent-dark); }
    .nav-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .nav-cnt { font-size: 11px; opacity: 0.6; }
    .main { max-width: 1100px; margin: 0 auto; padding: 32px 16px 48px; }
    .section { margin-bottom: 48px; scroll-margin-top: 72px; }
    .section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--card-border); }
    .section-dot { width: 14px; height: 14px; border-radius: 4px; flex-shrink: 0; transform: rotate(45deg); }
    .section h2 { font-size: 20px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; }
    .section-count { font-size: 14px; color: var(--text-muted); margin-left: auto; }
    .section-empty { text-align: center; padding: 32px 16px; color: var(--text-muted); background: var(--card-bg); border-radius: 16px; border: 1px dashed var(--card-border); }
    .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px,1fr)); gap: 16px; }
    .card {
      position: relative; background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 16px; padding: 20px 20px 16px;
      transition: 0.3s; box-shadow: 0 1px 3px rgba(0,0,0,.06);
      display: flex; flex-direction: column; opacity: 0; transform: translateY(24px);
    }
    .card.revealed { opacity: 1; transform: translateY(0); }
    .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.07); transform: translateY(-2px); }
    .card.revealed:hover { transform: translateY(-2px); }
    .card-num {
      position: absolute; top: -10px; left: 16px; background: var(--accent); color: #fff;
      font-size: 11px; font-weight: 700; width: 24px; height: 24px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 2px 6px rgba(255,107,53,.35);
    }
    .card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 10px; margin-top: 6px; }
    .card-title { font-size: 15px; font-weight: 700; line-height: 1.5; color: var(--text); flex: 1; }
    .card-source { flex-shrink: 0; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 100px; white-space: nowrap; }
    .source-x { background: #f0f0f0; color: #555; }
    .source-blog { background: #e8f4fd; color: #1a73e8; }
    .source-wechat { background: #e8f8e8; color: #2e7d32; }
    .source-media { background: #fff3e0; color: #e65100; }
    .source-hn { background: #fce4ec; color: #c62828; }
    .source-gh { background: #f3e5f5; color: #6a1b9a; }
    .score-badge {
      font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 100px;
    }
    .score-high { background: #e8f8e8; color: #2e7d32; }
    .score-mid { background: #fff3e0; color: #e65100; }
    .score-low { background: #fce4ec; color: #c62828; }
    .card-footer { display: flex; align-items: center; gap: 12px; margin-top: auto; flex-wrap: wrap; }
    .card-time { font-size: 12px; color: var(--text-muted); }
    .card-link {
      display: inline-flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 600;
      color: var(--accent); text-decoration: none; padding: 6px 14px; border-radius: 100px;
      background: rgba(255,107,53,.08); transition: 0.3s;
    }
    .card-link:hover { background: rgba(255,107,53,.16); color: var(--accent-dark); }
    .card-link svg { width: 14px; height: 14px; }
    .footer { text-align: center; padding: 32px 16px 40px; border-top: 1px solid var(--card-border); color: var(--text-muted); font-size: 13px; max-width: 1100px; margin: 0 auto; }
    .footer strong { color: var(--text-secondary); }
    .footer a { color: var(--accent); text-decoration: none; }
    .footer a:hover { text-decoration: underline; }
    .quick-top {
      position: fixed; bottom: 24px; right: 24px; width: 44px; height: 44px; border-radius: 50%;
      background: var(--accent); color: #fff; border: none; cursor: pointer; font-size: 20px;
      box-shadow: 0 12px 32px rgba(0,0,0,.1); opacity: 0; transform: translateY(12px);
      pointer-events: none; transition: 0.3s; z-index: 200;
      display: flex; align-items: center; justify-content: center;
    }
    .quick-top.visible { opacity: 1; transform: translateY(0); pointer-events: auto; }
    .quick-top:hover { background: var(--accent-dark); }
    @media (max-width: 600px) {
      .hero { padding: 40px 16px 36px; }
      .hero-stats { gap: 12px; }
      .hero-stat { padding: 10px 14px; min-width: 64px; }
      .hero-stat-num { font-size: 22px; }
      .card-grid { grid-template-columns: 1fr; }
      .section h2 { font-size: 17px; }
      .nav-link { padding: 6px 12px; font-size: 12px; }
    }"""

    # JavaScript - 需要转义 { 和 } 为 {{ 和 }}
    js = """    // 滚动揭示动画
    const cards = document.querySelectorAll('[data-reveal]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add('revealed'), i * 60);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    cards.forEach(c => observer.observe(c));

    // 回到顶部
    const quickTop = document.getElementById('quickTop');
    window.addEventListener('scroll', () => {
      quickTop.classList.toggle('visible', window.scrollY > 400);
    });
    quickTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // 导航高亮
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-link');
    window.addEventListener('scroll', () => {
      let current = '';
      sections.forEach(sec => {
        if (window.scrollY >= sec.offsetTop - 100) {
          current = sec.id;
        }
      });
      navLinks.forEach(a => {
        const isActive = a.getAttribute('href') === '#' + current;
        a.style.background = isActive ? 'rgba(255,107,53,.1)' : '';
        a.style.color = isActive ? 'var(--accent-dark)' : '';
      });
    });"""

    # 构建完整的 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>当日热点 — {date_str}</title>
<style>
{css}
</style>
</head>
<body>

<header class="hero">
  <div class="hero-content">
    <div class="hero-badge">🔥 当日热点</div>
    <h1>{total} 条热点资讯</h1>
    <p class="hero-sub">全网热点雷达 · 关键词过滤 · 智能聚合</p>
    <div class="hero-stats">
      <div class="hero-stat">
        <span class="hero-stat-num">{total}</span>
        <span class="hero-stat-lbl">命中条数</span>
      </div>
      <div class="hero-stat">
        <span class="hero-stat-num">{len(grouped_items)}</span>
        <span class="hero-stat-lbl">分组数</span>
      </div>
      <div class="hero-stat">
        <span class="hero-stat-num">{wd}</span>
        <span class="hero-stat-lbl">{display_date}</span>
      </div>
    </div>
  </div>
</header>

<nav class="nav-wrap" id="nav">
  <div class="nav-inner">
{nav_links}
  </div>
</nav>

<main class="main" id="main">
{sections_html}
</main>

<footer class="footer">
  <p>数据来源 <strong>NewsNow</strong> · 最后生成 <time>{display_date}</time> · <a href="../index.html">返回首页</a></p>
</footer>

<button class="quick-top" id="quickTop" aria-label="回到顶部">↑</button>

<script>
{js}
</script>

</body>
</html>'''

    return html


def main():
    if not CONFIG_FILE.exists():
        print(f"[ERROR] Config file not found: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    config = load_yaml(CONFIG_FILE)
    print("[INFO] Fetching NewsNow sources...")
    items = fetch_all_sources(config)
    print(f"[INFO] Total raw items: {len(items)}")

    if config.get("filter", {}).get("dedup", True):
        items = dedup(items, config)
        print(f"[INFO] After dedup: {len(items)}")

    method = config.get("filter", {}).get("method", "keyword")

    if method == "ai":
        # AI 模式：由 AI 同时完成打分与分组
        matched = ai_filter(items, config, assign_groups=True)
    else:
        # keyword / both 模式：先关键词匹配
        matched, unmatched = keyword_filter(items, config)
        if method == "both":
            # 关键词命中后再经 AI 打分过滤（分组保留关键词结果）
            matched = ai_filter(matched, config, assign_groups=False)

    grouped_items = {}
    for it in matched:
        gname = it.get("group_name", "其他")
        grouped_items.setdefault(gname, []).append(it)

    now = datetime.now(timezone(timedelta(hours=8)))
    if len(sys.argv) > 1:
        try:
            now = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=8)))
        except Exception:
            pass

    html = build_html(grouped_items, config, now)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(html, encoding="utf-8")
    print(f"[INFO] Written {INDEX_FILE} ({len(html)} bytes)")

    date_str = now.strftime("%Y-%m-%d-%H")
    archive_file = ARCHIVE_DIR / f"{date_str}.html"
    archive_file.write_text(html, encoding="utf-8")
    print(f"[INFO] Archived to {archive_file}")

    # Git 自动提交（与 generate_daily.py 行为一致）
    import subprocess
    cwd = str(OUTPUT_DIR)
    subprocess.run(["git", "add", "trending.html", f"trending-archive/{date_str}.html", "trending_config.yaml"], cwd=cwd, check=False)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd, capture_output=True)
    if result.returncode != 0:
        msg = f"chore: update trending radar {date_str}"
        subprocess.run(["git", "commit", "-m", msg], cwd=cwd, check=False)
        push_result = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
        if push_result.returncode == 0:
            print(f"[INFO] Committed and pushed: {msg}")
        else:
            print(f"[WARN] Commit done, but push failed: {push_result.stderr}")
    else:
        print("[INFO] No changes to commit")


if __name__ == "__main__":
    main()
