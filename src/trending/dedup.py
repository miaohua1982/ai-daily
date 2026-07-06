"""
trending.dedup — 去重（URL 去重 + 语义去重）。
"""

import os
import sys
import urllib.parse
from collections import defaultdict
from typing import Any, Dict, List, Optional

from utils import semantic_dedup


def dedup_data(
    items: List[Dict[str, Any]],
    config: Dict[str, Any],
    dot_env: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
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
        api_key = os.environ.get(api_key_env) or (dot_env or {}).get(api_key_env, "")
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
