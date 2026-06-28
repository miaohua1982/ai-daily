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
    """顺序获取所有数据源，source 之间使用指数退避。"""
    api_url = config["newsnow"]["api_url"]
    sources = config["newsnow"]["sources"]
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


def dedup(items):
    """按 url 去重，保留首次出现。"""
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
    return out


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

    sections_html = ""
    for group_name, items in grouped_items.items():
        if not items:
            continue
        cards = ""
        for it in items:
            title = esc_html(it.get("title", "无标题"))
            url = it.get("url") or it.get("mobileUrl") or "#"
            url_attr = esc_attr(url)
            src_name, icon, _ = source_meta(it, config)
            score_text = ""
            if "ai_score" in it:
                score_text = f" · AI {it['ai_score']:.2f}"
            updated = format_updated(it.get("updatedTime"))
            meta = f"{src_name}{score_text}"
            cards += (
                f'        <a href="{url_attr}" target="_blank" rel="noopener noreferrer" class="link-card">\n'
                f'          <span class="link-icon">{icon}</span>\n'
                f'          <span class="link-info">\n'
                f'            <div class="link-title">{title}</div>\n'
                f'            <div class="link-desc">{meta}</div>\n'
                f'          </span>\n'
                f'          <span class="link-arrow">→</span>\n'
                f'        </a>\n'
            )
        sections_html += (
            f'      <section class="group">\n'
            f'        <div class="group-header">\n'
            f'          <span class="group-dot"></span>\n'
            f'          <h2 class="group-title">{esc_html(group_name)}</h2>\n'
            f'          <span class="group-count">{len(items)} 条</span>\n'
            f'        </div>\n'
            f'        <div class="group-cards">\n'
            f'{cards}'
            f'        </div>\n'
            f'      </section>\n'
        )

    display_date = build_time.strftime("%Y-%m-%d %H:%M")
    wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][build_time.weekday()]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>~/trending</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}

  :root {{
    --bg: oklch(0.14 0.01 60);
    --surface: oklch(0.18 0.01 60);
    --surface-hover: oklch(0.22 0.01 60);
    --accent: oklch(0.72 0.17 45);
    --accent-dim: oklch(0.55 0.12 45);
    --text-primary: oklch(0.88 0.01 80);
    --text-secondary: oklch(0.55 0.02 80);
    --text-tertiary: oklch(0.38 0.02 80);
    --border: oklch(0.25 0.01 60);
    --mono: "Fira Code", "Cascadia Code", "JetBrains Mono", "SF Mono", "Menlo", "Consolas", monospace;
    --sans: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    --radius: 2px;
    --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
    --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  }}

  html, body {{
    height: 100%;
    background: var(--bg);
    color: var(--text-primary);
    font-family: var(--mono);
    font-weight: 400;
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }}

  body::before {{
    content: "";
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(var(--border) 1px, transparent 1px),
      linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 60px 60px;
    background-position: center center;
    opacity: 0.3;
    pointer-events: none;
    z-index: 0;
  }}

  .terminal {{
    position: relative;
    z-index: 1;
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
  }}

  .viewport {{
    width: 100%;
    max-width: 800px;
    display: flex;
    flex-direction: column;
    gap: 2.5rem;
  }}

  .header {{
    position: relative;
    padding-top: 2rem;
  }}

  .prompt-line {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: clamp(0.8rem, 1.4vw, 0.9rem);
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
  }}

  .prompt-arrow {{ color: var(--accent); font-weight: 600; }}
  .cmd {{ color: var(--accent); font-weight: 500; }}

  .cursor {{
    display: inline-block;
    width: 0.55em;
    height: 1.15em;
    background: var(--accent);
    margin-left: 0.1em;
    vertical-align: text-bottom;
    animation: blink 1s step-end infinite;
  }}

  @keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0; }}
  }}

  .hostname {{
    font-size: clamp(2.4rem, 6vw, 4.5rem);
    font-weight: 300;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    line-height: 1.15;
    margin-bottom: 0.6rem;
  }}

  .hostname .tilde {{ color: var(--accent); font-weight: 400; }}

  .tagline {{
    font-family: var(--sans);
    font-size: clamp(0.85rem, 1.3vw, 0.95rem);
    color: var(--text-tertiary);
    font-weight: 300;
    letter-spacing: 0.01em;
  }}

  .stats {{
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 1.5rem;
  }}

  .stat {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.8rem 1.2rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }}

  .stat strong {{
    color: var(--accent);
    font-weight: 600;
  }}

  .divider {{
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent) 15%, var(--accent) 85%, transparent);
    opacity: 0.3;
  }}

  .section-label {{
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-tertiary);
    margin-bottom: 0.5rem;
  }}

  .groups {{
    display: flex;
    flex-direction: column;
    gap: 2.5rem;
  }}

  .group-header {{
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin-bottom: 1rem;
  }}

  .group-dot {{
    width: 8px;
    height: 8px;
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 6px var(--accent-dim);
  }}

  .group-title {{
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--text-primary);
  }}

  .group-count {{
    margin-left: auto;
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }}

  .group-cards {{
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
  }}

  .link-card {{
    display: flex;
    align-items: center;
    gap: 1.2rem;
    padding: 1.2rem 1.5rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: all 0.3s var(--ease-out-quart);
    position: relative;
    overflow: hidden;
  }}

  .link-card::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent);
    transform: scaleY(0);
    transform-origin: top;
    transition: transform 0.3s var(--ease-out-expo);
  }}

  .link-card:hover {{
    background: var(--surface-hover);
    border-color: oklch(0.35 0.01 60);
    transform: translateX(4px);
  }}

  .link-card:hover::before {{ transform: scaleY(1); }}

  .link-icon {{
    font-size: 1.4rem;
    line-height: 1;
    color: var(--accent);
    flex-shrink: 0;
    width: 2.5rem;
    text-align: center;
  }}

  .link-info {{
    flex: 1;
    min-width: 0;
  }}

  .link-title {{
    font-size: clamp(0.9rem, 1.5vw, 1rem);
    font-weight: 500;
    color: var(--text-primary);
    letter-spacing: 0.01em;
    margin-bottom: 0.15rem;
    transition: color 0.3s;
  }}

  .link-card:hover .link-title {{ color: var(--accent); }}

  .link-desc {{
    font-family: var(--sans);
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 300;
    line-height: 1.4;
  }}

  .link-arrow {{
    font-size: 0.8rem;
    color: var(--text-tertiary);
    transition: all 0.3s var(--ease-out-expo);
    flex-shrink: 0;
  }}

  .link-card:hover .link-arrow {{
    color: var(--accent);
    transform: translateX(4px);
  }}

  .empty {{
    font-size: 0.85rem;
    color: var(--text-tertiary);
    font-style: italic;
    padding: 0.8rem 0;
  }}

  .footer {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
    font-size: 0.72rem;
    color: var(--text-tertiary);
    padding-bottom: 2rem;
  }}

  .footer .dim {{ opacity: 0.5; }}

  .status-dot {{
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    margin-right: 0.35rem;
    box-shadow: 0 0 6px var(--accent-dim);
    animation: pulse 2s ease-in-out infinite;
  }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 0.5; }}
    50% {{ opacity: 1; }}
  }}

  @media (max-width: 480px) {{
    .terminal {{ padding: 1.5rem; }}
    .viewport {{ gap: 2rem; }}
    .link-card {{ padding: 1rem; gap: 0.8rem; }}
    .link-icon {{ width: 2rem; font-size: 1.2rem; }}
  }}
</style>
</head>
<body>

<div class="terminal">
  <div class="viewport">

    <header class="header">
      <div class="prompt-line">
        <span class="prompt-arrow">➜</span>
        <span class="cmd">trending</span>
        <span class="cursor"></span>
      </div>
      <h1 class="hostname"><span class="tilde">~/</span>trending</h1>
      <p class="tagline">全网热点雷达 · 关键词过滤 · 智能聚合</p>
      <div class="stats">
        <div class="stat"><strong>{total}</strong> 条命中</div>
        <div class="stat">{source_summary}</div>
        <div class="stat">{display_date} · {wd}</div>
      </div>
    </header>

    <div class="divider"></div>

    <main class="groups">
      <span class="section-label">// 分组</span>
{sections_html}
    </main>

    <div class="divider"></div>

    <footer class="footer">
      <span><span class="status-dot"></span>在线</span>
      <span class="dim">|</span>
      <span>UTC+8</span>
      <span class="dim">|</span>
      <span>数据来源 NewsNow</span>
      <span class="dim">|</span>
      <span>last build <time>{display_date}</time></span>
    </footer>

  </div>
</div>

</body>
</html>
"""
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
        items = dedup(items)
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
        gname = it.get("group_name", "全部")
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

    date_str = now.strftime("%Y-%m-%d")
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
