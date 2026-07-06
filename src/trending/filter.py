"""
trending.filter — 关键词 / AI 过滤 + 分组。
"""

import os
import json
import re
import sys
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def assign_group_names(items: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
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


def keyword_filter(items: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """按关键词组匹配，返回命中列表和未命中列表。"""
    result = []
    unmatched = []
    for item in assign_group_names(items, config):
        if "group_name" in item:
            result.append(item)
        else:
            unmatched.append(item)
    return result, unmatched


def ai_score_batch(
    batch: List[Dict[str, Any]],
    interests: str,
    group_names: List[str],
    api_key: str,
    base_url: str,
    model: str,
) -> Dict[int, Dict[str, Any]]:
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


def ai_filter(
    items: List[Dict[str, Any]],
    config: Dict[str, Any],
    assign_groups: bool = True,
    dot_env: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """对 items 进行 AI 打分过滤；若 assign_groups=True 则同时由 AI 分组。"""
    ai_cfg = config.get("ai", {})
    api_key_env = ai_cfg.get("api_key_env", "DEEPSEEK_API_KEY")
    api_key = os.environ.get(api_key_env) or (dot_env or {}).get(api_key_env, "")
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


def filter_data(
    items: List[Dict[str, Any]],
    config: Dict[str, Any],
    dot_env: Optional[Dict[str, str]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Step 3: 关键词 / AI 过滤 + 分组。返回 grouped_items。"""
    method = config.get("filter", {}).get("method", "keyword")

    if method == "ai":
        matched = ai_filter(items, config, assign_groups=True, dot_env=dot_env)
    else:
        matched, unmatched = keyword_filter(items, config)
        if method == "both":
            matched = ai_filter(matched, config, assign_groups=False, dot_env=dot_env)

    grouped_items = {}
    for it in matched:
        gname = it.get("group_name", "其他")
        grouped_items.setdefault(gname, []).append(it)

    return grouped_items
