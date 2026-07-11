"""
trending.fetcher — 数据获取（NewsNow API 多源抓取）。
"""

import json
import time
import random
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List

from utils import UA


def fetch_source(api_url: str, source_id: str, max_retries: int = 3) -> List[Dict[str, Any]]:
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


def fetch_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Step 1: 获取所有 NewsNow 数据源。返回 items。"""
    if config is None:
        raise ValueError("config is required — pass load_config(CONFIG_FILE) result")

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
