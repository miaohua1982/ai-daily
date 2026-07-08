#!/usr/bin/env python3
"""
Papers data fetching layer.
Multi-source: aihot + arXiv + HuggingFace Daily Papers.
"""

import sys
import os
import re
import json
import time
import random
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from utils import api_get, filter_by_date, get_now_date_str


# ── 通用 HTTP GET（带重试 + 指数退避 + 抖动）────────────────────

def _http_get(url: str, config: Dict[str, Any], timeout: int = 30) -> bytes:
    """带重试 + 指数退避 + 抖动的 HTTP GET，返回原始 bytes。"""
    max_retries = config["fetch"]["max_retries"]
    ua = config["fetch"]["user_agent"]
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                backoff = (2 ** attempt) + random.uniform(0, 1)
                print(f"[INFO] Retry {attempt+1}/{max_retries}: {e}, waiting {backoff:.1f}s", file=sys.stderr)
                time.sleep(backoff)
    if last_err is not None:
        raise last_err
    raise RuntimeError(f"HTTP GET failed for {url}: max_retries={max_retries}")


# ── 数据源 1: AI HOT ─────────────────────────────────────────────

def fetch_aihot_papers(config: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
    """数据源 1: AI HOT API（category=paper 过滤论文）。"""
    cfg = config["aihot"]
    if not cfg["enabled"]:
        return []

    api_base = cfg["api_base"]
    max_retries = config["fetch"]["max_retries"]
    days_back = config["fetch"]["days_back"]
    take = cfg["take"]
    page_size = cfg["page_size"]

    # 随机启动抖动：避免多实例同时请求
    startup_jitter = random.uniform(0, 1.5)
    if startup_jitter > 0.05:
        time.sleep(startup_jitter)

    dt = datetime.strptime(target_date, "%Y-%m-%d")
    since_dt = dt - timedelta(days=days_back)
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    all_items = []
    cursor = ""
    remaining = take

    for page_idx in range(3):
        # 分页之间添加退避与抖动（第一页不等待）
        if page_idx > 0:
            base_backoff = 2 ** (page_idx - 1)
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] aihot waiting {backoff:.1f}s before next page...", file=sys.stderr)
            time.sleep(backoff)

        url = ("/items?mode=all&category=paper&since=" + since_iso +
               "&take=" + str(min(remaining, page_size)))
        if cursor:
            url += "&cursor=" + cursor
        data = api_get(url, base_url=api_base, max_retries=max_retries)
        if not data or "items" not in data:
            break
        items = data.get("items", [])
        all_items.extend(items)
        remaining -= len(items)
        if not data.get("hasNext") or remaining <= 0:
            break
        cursor = data.get("nextCursor", "")
        if not cursor:
            break

    for item in all_items:
        item.setdefault("source_api", "aihot")

    print(f"[INFO] aihot fetched {len(all_items)} papers", file=sys.stderr)
    return all_items


# ── 数据源 2: arXiv ──────────────────────────────────────────────

def fetch_arxiv_papers(config: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
    """数据源 2: arXiv API（按分类检索，本地按日期过滤）。

    arXiv API 不支持 submittedDate 搜索前缀，无法在 API 层按日期过滤。
    改为：按 submittedDate 降序拉取 max_results 条，然后在本地根据
    publishedAt 字段过滤 days_back 范围内的论文。
    """
    cfg = config["arxiv"]
    if not cfg["enabled"]:
        return []

    days_back = config["fetch"]["days_back"]
    categories = cfg["categories"]
    max_results = cfg["max_results"]
    timeout = cfg["timeout_seconds"]

    # 构造 search_query: (cat:cs.AI+OR+cat:cs.CL+OR+...)
    # 注意：使用 + 而非 %20 表示空格，arXiv API 要求这种格式
    cat_query = "+OR+".join(f"cat:{c}" for c in categories)
    if len(categories) > 1:
        cat_query = f"%28{cat_query}%29"
    search_query = cat_query

    params = {
        "search_query": search_query,
        "start": "0",
        "max_results": str(max_results),
        "sortBy": cfg["sort_by"],
        "sortOrder": cfg["sort_order"],
    }
    url = f"{cfg['endpoint']}?{urllib.parse.urlencode(params, safe=':+%')}"
    print(f"[INFO] arXiv request: {url}", file=sys.stderr)

    raw = _http_get(url, config, timeout=timeout)
    xml_data = raw.decode("utf-8")

    # 解析 Atom XML
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_data)
    papers = []
    for entry in root.findall("atom:entry", ns):
        try:
            arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = (entry.find("atom:summary", ns).text or "").strip().replace("\n", " ")
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
            published = entry.find("atom:published", ns).text
            primary_cat = entry.find("arxiv:primary_category", ns).attrib.get("term", "")
        except (AttributeError, TypeError):
            continue

        papers.append({
            "id": arxiv_id,
            "title": title,
            "summary": summary,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "source": "arxiv",
            "source_api": "arxiv",
            "publishedAt": published,
            "score": 0,
            "selected": False,
            # 额外字段（不影响下游）
            "authors": authors,
            "primary_category": primary_cat,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
        })

    # 本地日期过滤（arXiv API 不支持 submittedDate 搜索前缀）
    if days_back > 0:
        papers = filter_by_date(papers, target_date, days_back)
        print(f"[INFO] arXiv after date filter: {len(papers)} papers", file=sys.stderr)
    else:
        print(f"[INFO] arXiv fetched {len(papers)} papers", file=sys.stderr)

    return papers


# ── 数据源 3: HuggingFace Daily Papers ───────────────────────────

def fetch_hf_daily_papers(config: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
    """数据源 3: HuggingFace Daily Papers（逐天遍历最近 N 天）。"""
    cfg = config["huggingface"]
    if not cfg["enabled"]:
        return []

    days_back = config["fetch"]["days_back"]
    rate_limit = cfg["rate_limit_seconds"]
    page_limit = cfg["page_limit"]
    timeout = cfg["timeout_seconds"]

    today = datetime.strptime(target_date, "%Y-%m-%d").date()

    all_items = []

    for i in range(days_back):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        
        url = f"{cfg['endpoint_daily']}?date={date_str}&page=1&limit={page_limit}"
        try:
            raw = _http_get(url, config, timeout=timeout)
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            print(f"[WARN] HF {date_str} failed: {e}", file=sys.stderr)
            continue

        if not data:
            print(f"[INFO] HF {date_str} returned empty data", file=sys.stderr)
            continue

        for item in data:
            paper = item.get("paper", {})
            all_items.append({
                "id": paper.get("id", ""),
                "title": paper.get("title", ""),
                "summary": (paper.get("ai_summary") or paper.get("summary") or "").strip(),
                "url": f"https://huggingface.co/papers/{paper.get('id', '')}",
                "source": "hugging face",
                "source_api": "huggingface",
                "publishedAt": paper.get("publishedAt", ""),
                "score": paper.get("upvotes", 0),
                "selected": paper.get("upvotes", 0) >= 50,
                # 额外字段
                "upvotes": paper.get("upvotes", 0),
                "ai_summary": paper.get("ai_summary"),
                "ai_keywords": paper.get("ai_keywords", []),
                "githubRepo": paper.get("githubRepo"),
                "organization": (paper.get("organization") or {}).get("fullname", ""),
                "numComments": item.get("numComments", 0),
            })

        time.sleep(rate_limit)

    # 本地日期过滤：HF 的 daily_papers 返回的是推荐列表，不是严格按 publishedAt 筛选
    if days_back > 0:
        all_items = filter_by_date(all_items, target_date, days_back)
        print(f"[INFO] HuggingFace after date filter: {len(all_items)} papers", file=sys.stderr)
    else:
        print(f"[INFO] HuggingFace fetched {len(all_items)} papers", file=sys.stderr)

    return all_items


# ── 多源合并去重 ─────────────────────────────────────────────────

def merge_papers(*sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """多源合并去重：以 id 或 url 为 key，HF 数据优先补充热度字段。"""
    merged = {}
    for source in sources:
        for p in source:
            key = p.get("id") or p.get("url", "")
            if not key:
                continue
            if key not in merged:
                merged[key] = p
            elif p.get("source_api") == "huggingface":
                # HF 补充热度字段到已有记录
                merged[key].update({
                    "upvotes": p.get("upvotes", 0),
                    "ai_summary": p.get("ai_summary"),
                    "ai_keywords": p.get("ai_keywords"),
                    "githubRepo": p.get("githubRepo"),
                    "score": p.get("score", merged[key].get("score", 0)),
                    "selected": p.get("selected") or merged[key].get("selected", False),
                })
    return list(merged.values())


# ── Step 1 入口：三源拉取 + 合并 ─────────────────────────────────

def fetch_data(
    target_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    dot_env: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """Step 1: 多源获取论文原始数据。返回 (items, date_str)。"""
    if config is None:
        raise ValueError("config is required — pass load_config(CONFIG_FILE) result")

    # 确定 target_date（北京时间 8 点前用前一天）
    target_date = get_now_date_str(target_date)

    # 优先拉取 aihot，成功则直接使用，不再请求 arXiv / HuggingFace
    aihot_items = fetch_aihot_papers(config, target_date)

    if len(aihot_items) > 0:
        all_items = aihot_items
        print(f"[INFO] aihot 获取成功，共 {len(all_items)} 篇论文，跳过 arXiv / HuggingFace", file=sys.stderr)
    else:
        # aihot 失败或无数据，回退到 arXiv + HuggingFace 双源合并
        print("[INFO] aihot 无数据，回退到 arXiv + HuggingFace", file=sys.stderr)
        arxiv_items = fetch_arxiv_papers(config, target_date)
        hf_items = fetch_hf_daily_papers(config, target_date)
        all_items = merge_papers(arxiv_items, hf_items)
        print(f"[INFO] Fetched {len(all_items)} papers total "
              f"(arxiv:{len(arxiv_items)} hf:{len(hf_items)})", file=sys.stderr)

        # 翻译英文论文（arxiv / huggingface 来源）
        all_items = translate_papers(all_items, config, dot_env)

    return all_items, target_date


# ── 翻译（arXiv / HuggingFace 英文论文 → 中文）─────────────────

def translate_papers(
    papers: List[Dict[str, Any]],
    config: Dict[str, Any],
    dot_env: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """将 arXiv / HuggingFace 来源的英文论文标题和摘要翻译为中文。

    翻译后在 paper dict 中新增 title_zh / summary_zh 字段。
    aihot 来源已是中文，跳过。

    Args:
        papers:   论文列表
        config:   配置字典（需包含 translation 段）
        dot_env:  .env 解析结果字典（用于获取 API Key）
    """
    cfg = config["translation"]
    if not cfg["enabled"]:
        return papers

    # 筛选需要翻译的论文（仅 arxiv / huggingface 来源）
    need = [p for p in papers if p.get("source_api") in ("arxiv", "huggingface")]
    if not need:
        return papers

    api_key_env = cfg["api_key_env"]
    api_key = os.environ.get(api_key_env) or (dot_env or {}).get(api_key_env, "")
    if not api_key:
        print(f"[WARN] Translation enabled but {api_key_env} not set, skipping", file=sys.stderr)
        return papers

    base_url = cfg["base_url"]
    model = cfg["model"]
    batch_size = cfg["batch_size"]
    rate_limit = cfg["rate_limit_seconds"]
    timeout = cfg["timeout_seconds"]

    success_count = 0
    for i in range(0, len(need), batch_size):
        batch = need[i:i + batch_size]
        try:
            translations = _translate_batch(batch, api_key, base_url, model, timeout)
            for paper, trans in zip(batch, translations):
                t_zh = trans.get("title_zh", "").strip()
                s_zh = trans.get("summary_zh", "").strip()
                if t_zh:
                    paper["title_zh"] = t_zh
                if s_zh:
                    paper["summary_zh"] = s_zh
                success_count += 1
        except Exception as e:
            print(f"[WARN] Translation batch {i // batch_size + 1} failed: {e}", file=sys.stderr)

        if i + batch_size < len(need):
            time.sleep(rate_limit)

    print(f"[INFO] Translated {success_count}/{len(need)} papers", file=sys.stderr)
    return papers


def _translate_batch(
    papers: List[Dict[str, Any]],
    api_key: str,
    base_url: str,
    model: str,
    timeout: int,
) -> List[Dict[str, Any]]:
    """调用大模型批量翻译论文标题和摘要，返回翻译结果列表。

    Returns:
        list[dict]，每项含 id / title_zh / summary_zh
    """
    items = []
    for idx, p in enumerate(papers):
        items.append({
            "id": idx,
            "title": p.get("title", ""),
            "summary": (p.get("summary") or "")[:500],
        })

    prompt = (
        "请将以下论文的标题和摘要翻译为中文。\n"
        "要求：保持学术术语准确，翻译简洁流畅，不要添加额外解释。\n"
        "以JSON格式返回，格式为：\n"
        '{"translations": [{"id": 0, "title_zh": "中文标题", "summary_zh": "中文摘要"}, ...]}\n\n'
        f"论文列表：\n{json.dumps(items, ensure_ascii=False, indent=2)}"
    )

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的学术翻译助手，擅长将AI领域的英文论文标题和摘要翻译为中文。始终以JSON格式返回结果。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    content = data["choices"][0]["message"]["content"]

    # 解析 JSON — 兼容 markdown 代码块包裹和裸 JSON
    return _parse_translation_response(content, len(papers))


def _parse_translation_response(content: str, expected_count: int) -> List[Dict[str, Any]]:
    """从 LLM 响应中解析翻译结果，返回 list[dict]。"""
    # 尝试直接解析
    text = content.strip()

    # 去除 markdown 代码块包裹
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    result = json.loads(text)

    # 兼容 {"translations": [...]} 或直接 [...]
    if isinstance(result, dict) and "translations" in result:
        result = result["translations"]
    if not isinstance(result, list):
        raise ValueError(f"Unexpected translation response: {type(result)}")

    # 按 id 排序，确保与输入顺序一致
    result.sort(key=lambda x: x.get("id", 0))
    return result
