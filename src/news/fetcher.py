"""
news/fetcher — 新闻数据获取（aihot 主源 + newsnow 备用源）。
"""

import sys
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

from utils import api_get
from src.news.constants import CATEGORY_ORDER, CATEGORY_LABELS


def fetch_data(
    target_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], str]:
    """Step1: 获取每日新闻原始数据（aihot 主源 → newsnow 备用源）。返回 (data, date_str)。"""
    if config is None:
        # caller should pass config
        print(f"[INFO] Caller do not pass config, just return empty data for test purpose.")
        return {}, ""

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

    # ── 第一级回退：主源最新日期 ──
    print(f"[WARN] Daily {date_str} not available on primary, falling back to latest...")
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

    # ── 第二级回退：备用数据源 newsnow ──
    print(f"[WARN] Primary source unavailable, falling back to newsnow secondary source...")
    data = _fetch_from_newsnow(config)
    if data and data.get("sections"):
        sections = data["sections"]
        total = sum(len(s.get("items", [])) for s in sections)
        print(f"[INFO] Got from newsnow: {len(sections)} sections, {total} items")
        return data, date_str

    raise RuntimeError("Failed to fetch any daily report from both primary and secondary sources")


def _fetch_from_newsnow(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    从 newsnow.busiyi.world 备用源获取数据，并转换为与 aihot 主源兼容的格式。

    newsnow 原始格式:
      {"items": [{"id":"..","title":"..","url":"..",
                   "extra":{"hover":"摘要","info":"来源名 · category_slug"}}]}

    转换为 aihot 格式:
      {"sections": [{"label":"技巧与观点","items":[{...}]}], "date":"2026-07-05"}
    """
    fallback_base = config["fetch"]["fallback_base"]
    fallback_path = config["fetch"]["fallback_path"]
    max_retries = config["fetch"]["max_retries"]

    data = api_get(fallback_path, base_url=fallback_base, max_retries=max_retries)
    if not data or not data.get("items"):
        return None

    # 按 category slug 分组
    sections = [ {"label": CATEGORY_LABELS.get(slug, slug), "items": []} for slug in CATEGORY_ORDER ]
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
            slug = "tip"  # 无法解析时归入"技巧与观点"

        transformed = {
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "sourceUrl": item.get("url", ""),
            "sourceName": source_name,
            "summary": extra.get("hover", ""),
        }
        for section in sections:
            if section["label"] == CATEGORY_LABELS.get(slug, slug):
                section["items"].append(transformed)
                break

    # 从 updatedTime（Unix 毫秒时间戳）提取日期
    date_str = None
    updated = data.get("updatedTime")
    if updated:
        try:
            from datetime import timezone as tz
            dt = datetime.fromtimestamp(updated / 1000, tz=tz.utc)
            dt_bj = dt.astimezone(timezone(timedelta(hours=8)))
            date_str = dt_bj.strftime("%Y-%m-%d")
        except Exception:
            pass
    if not date_str:
        date_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")

    return {"sections": sections, "date": date_str}
