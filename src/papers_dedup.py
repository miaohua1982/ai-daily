#!/usr/bin/env python3
"""
Papers deduplication layer.
URL dedup + semantic dedup + top-N selection.
"""

import os
import sys
import urllib.parse

from utils import semantic_dedup


# ── Step 2: 去重 ─────────────────────────────────────────────────

def dedup_data(items, config=None, dot_env=None):
    """Step 2: URL 去重 + 语义去重 + 选出 top papers。返回 papers。

    Args:
        items:    原始论文列表
        config:   配置字典（需包含 semantic_dedup 段）
        dot_env:  .env 解析结果字典（用于获取 API Key）
    """
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
    sem_cfg = config["semantic_dedup"]
    if sem_cfg["enabled"]:
        api_key_env = sem_cfg["api_key_env"]
        api_key = os.environ.get(api_key_env) or (dot_env or {}).get(api_key_env, "")
        base_url = sem_cfg["base_url"]
        model = sem_cfg["model"]
        threshold = float(sem_cfg["threshold"])
        batch_size = int(sem_cfg["batch_size"])

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
    """按 score 排序选出 top papers，未启用语义去重时用标题前缀兜底去重。"""
    selected = [i for i in items if i.get("selected")]
    not_selected = [i for i in items if not i.get("selected")]
    selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    not_selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    result = selected[:limit]
    if len(result) < limit:
        result += not_selected[:limit - len(result)]

    # 如果未启用语义去重，使用标题前缀作为兜底去重
    sem_enabled = config["semantic_dedup"]["enabled"]
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
