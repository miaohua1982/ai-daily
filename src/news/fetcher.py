"""
news/fetcher — 新闻数据获取（aihot 主源 + newsnow 备用源）。
"""

import time
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from utils import api_get, get_now_date_str
from src.news.constants import CATEGORY_LABELS


def fetch_data(
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Step1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 items 列表。

    每条 item 含 publishTime 字段（ISO 格式字符串）。
    aiho 主源用 windowEnd，newsnow 备用源从 updatedTime 毫秒时间戳转换。
    """
    if config is None:
        raise ValueError("config is required — pass load_config(CONFIG_FILE) result")

    api_base = config["fetch"]["api_base"]
    max_retries = config["fetch"]["max_retries"]

    # 随机启动抖动：避免多实例同时请求
    startup_jitter = random.uniform(0, 1.5)
    if startup_jitter > 0.05:
        time.sleep(startup_jitter)

    date_str = get_now_date_str(config['target_date'])

    print(f"[INFO] Fetching daily for {date_str} ...")
    data = api_get(f"/daily/{date_str}", base_url=api_base, max_retries=max_retries)
    if data and "sections" in data:
        items = _flatten_sections(data)
        print(f"[INFO] Got daily {date_str}: {len(items)} items")
        return items

    # ── 第一级回退：主源最新日期 ──
    print(f"[WARN] Daily {date_str} not available on primary, falling back to latest...")
    dailies = api_get("/dailies?take=5", base_url=api_base, max_retries=max_retries)
    if dailies and dailies.get("items"):
        latest = dailies["items"][0]["date"]
        available = [d["date"] for d in dailies["items"]]
        print(f"[INFO] Fallback to {latest} (available dates: {available})")
        data = api_get(f"/daily/{latest}", base_url=api_base, max_retries=max_retries)
        if data and "sections" in data:
            items = _flatten_sections(data)
            print(f"[INFO] Got daily {latest}: {len(items)} items")
            return items

    # ── 第二级回退：备用数据源 newsnow ──
    print(f"[WARN] Primary source unavailable, falling back to newsnow secondary source...")
    result = _fetch_from_newsnow(config)
    if result:
        print(f"[INFO] Got from newsnow: {len(result)} items")
        return result

    raise RuntimeError("Failed to fetch any daily report from both primary and secondary sources")


def _flatten_sections(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将 aihot API 的 sections 展平为 item 列表，每个 item 标注 category 和 publishTime。"""
    window_end = data.get("windowEnd", "")
    items = []
    for sec in data.get("sections", []):
        label = sec.get("label", "")
        for item in sec.get("items", []):
            item["category"] = label
            item["publishTime"] = window_end
            items.append(item)
    return items


def _fetch_from_newsnow(config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    从 newsnow.busiyi.world 备用源获取数据，返回 items 列表。

    每个 item 标注 category（CATEGORY_ORDER 中的一个 slug）和 publishTime（从 updatedTime 毫秒转 ISO）。
    """
    fallback_base = config["fetch"]["fallback_base"]
    fallback_path = config["fetch"]["fallback_path"]
    max_retries = config["fetch"]["max_retries"]

    data = api_get(fallback_path, base_url=fallback_base, max_retries=max_retries)
    if not data or not data.get("items"):
        return None

    # 从 updatedTime（Unix 毫秒时间戳）提取精确时间，用于每条 item 的 publishTime
    publish_time = ""
    updated = data.get("updatedTime")
    if updated:
        try:
            dt = datetime.fromtimestamp(updated / 1000, tz=timezone.utc)
            dt_bj = dt.astimezone(timezone(timedelta(hours=8)))
            publish_time = dt_bj.isoformat()
        except Exception:
            pass

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
            "publishTime": item.get("pubDate", publish_time),
        }
        items.append(transformed)

    return items
