"""
news/fetcher — 新闻数据获取（aihot 主源 + newsnow 备用源）。
"""

import sys
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from utils import api_get, get_now_date_str
from src.news.constants import CATEGORY_LABELS


def fetch_data(
    target_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """Step1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 (items, ts)。

    items: flat list，每个 item 含 category 字段（CATEGORY_ORDER 中的一个 slug）。
    ts:    API 返回的精确时间戳（aihot 用 windowEnd，newsnow 用 updatedTime 转 ISO）。
    """
    if config is None:
        print(f"[INFO] Caller do not pass config, just return empty data for test purpose.")
        return [], ""

    api_base = config["fetch"]["api_base"]
    max_retries = config["fetch"]["max_retries"]

    # 随机启动抖动：避免多实例同时请求
    startup_jitter = random.uniform(0, 1.5)
    if startup_jitter > 0.05:
        time.sleep(startup_jitter)

    date_str = get_now_date_str(target_date)

    print(f"[INFO] Fetching daily for {date_str} ...")
    data = api_get(f"/daily/{date_str}", base_url=api_base, max_retries=max_retries)
    if data and "sections" in data:
        items, ts = _flatten_sections(data)
        print(f"[INFO] Got daily {date_str}: {len(items)} items")
        return items, ts

    # ── 第一级回退：主源最新日期 ──
    print(f"[WARN] Daily {date_str} not available on primary, falling back to latest...")
    dailies = api_get("/dailies?take=5", base_url=api_base, max_retries=max_retries)
    if dailies and dailies.get("items"):
        latest = dailies["items"][0]["date"]
        available = [d["date"] for d in dailies["items"]]
        print(f"[INFO] Fallback to {latest} (available dates: {available})")
        data = api_get(f"/daily/{latest}", base_url=api_base, max_retries=max_retries)
        if data and "sections" in data:
            items, ts = _flatten_sections(data)
            print(f"[INFO] Got daily {latest}: {len(items)} items")
            return items, ts

    # ── 第二级回退：备用数据源 newsnow ──
    print(f"[WARN] Primary source unavailable, falling back to newsnow secondary source...")
    result = _fetch_from_newsnow(config)
    if result:
        items, ts = result
        print(f"[INFO] Got from newsnow: {len(items)} items")
        return items, ts

    raise RuntimeError("Failed to fetch any daily report from both primary and secondary sources")


def _flatten_sections(data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """将 aihot API 的 sections 展平为 item 列表，每个 item 标注 category。返回 (items, ts)。"""
    items = []
    for sec in data.get("sections", []):
        label = sec.get("label", "")
        for item in sec.get("items", []):
            item["category"] = label
            items.append(item)
    ts = data.get("windowEnd", "")
    return items, ts


def _fetch_from_newsnow(config: Dict[str, Any]) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """
    从 newsnow.busiyi.world 备用源获取数据，返回 (items, ts)。

    每个 item 标注 category（CATEGORY_ORDER 中的一个 slug）。
    ts 从 updatedTime（Unix 毫秒时间戳）转换为 ISO 字符串。
    """
    fallback_base = config["fetch"]["fallback_base"]
    fallback_path = config["fetch"]["fallback_path"]
    max_retries = config["fetch"]["max_retries"]

    data = api_get(fallback_path, base_url=fallback_base, max_retries=max_retries)
    if not data or not data.get("items"):
        return None

    items = []
    for item in data["items"]:
        extra = item.get("extra", {})
        info = extra.get("info", "")

        # 解析 "来源描述 · category_slug"（如 "IT之家（RSS） · industry"）
        if " · " in info:
            source_name, slug = info.rsplit(" · ", 1)
            source_name = source_name.strip()
            slug = slug.strip()
        else:
            source_name = info.strip()
            slug = "tip"

        if slug not in CATEGORY_LABELS:
            slug = "tip"

        transformed = {
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "sourceUrl": item.get("url", ""),
            "sourceName": source_name,
            "summary": extra.get("hover", ""),
            "category": CATEGORY_LABELS.get(slug, "技巧与观点"),
        }
        items.append(transformed)

    # 从 updatedTime（Unix 毫秒时间戳）提取精确时间
    ts = ""
    updated = data.get("updatedTime")
    if updated:
        try:
            dt = datetime.fromtimestamp(updated / 1000, tz=timezone.utc)
            dt_bj = dt.astimezone(timezone(timedelta(hours=8)))
            ts = dt_bj.isoformat()
        except Exception:
            pass

    return items, ts
