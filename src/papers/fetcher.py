#!/usr/bin/env python3
"""
Papers data fetching layer.
Multi-source: aihot + arXiv + HuggingFace Daily Papers.
"""

# AIHOT v1 迁移依据：https://aihot.news/agent?tab=api#legacy-api-migration
# 仅适配 AI HOT 抓取，保留现有备用源编排、翻译与渲染流程。

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

from utils import api_get, filter_by_date, get_now_date_str, get_dot_env


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

    all_items = []
    # v1 cursor 与查询绑定，且不兼容旧版；每次运行从首屏开始。
    cursor = ""
    remaining = take

    for page_idx in range(3):
        # 分页之间添加退避与抖动（第一页不等待）
        if page_idx > 0:
            base_backoff = 2 ** (page_idx - 1)
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] aihot waiting {backoff:.1f}s before next page...", file=sys.stderr)
            time.sleep(backoff)

        # v1 不接受旧 since/take：改用 window/limit，并按 publishedAt 排序。
        # 先取滚动 7 天，再按原 days_back 配置本地过滤；接口无法补取更早历史。
        params = {
            "mode": "all", "category": "paper", "window": "7d",
            "by": "published", "limit": min(remaining, page_size, 100),
        }
        if cursor:
            params["cursor"] = cursor
        # cursor 是不透明字符串，统一编码，避免特殊字符破坏查询参数。
        url = "/items?" + urllib.parse.urlencode(params)
        data = api_get(url, base_url=api_base, max_retries=max_retries)
        if not data or "items" not in data:
            break
        items = data.get("items", [])
        all_items.extend(items)
        remaining -= len(items)
        # v1 分页元数据移到 page，旧顶层 hasNext 改名为 hasMore。
        page = data.get("page", {})
        if not page.get("hasMore") or remaining <= 0:
            break
        cursor = page.get("nextCursor", "")
        if not cursor:
            break

    # v1 的 links.original、source.name 恢复为内部 url、字符串 source。
    # 保留原始其余字段及 source_api 标记，避免改动去重、翻译与渲染接口。
    papers = []
    for raw in all_items:
        item = dict(raw)
        links = raw.get("links") or {}
        source = raw.get("source") or {}
        item["url"] = links.get("original") or links.get("aihot") or ""
        item["source"] = source.get("name", "")
        item["source_api"] = "aihot"
        papers.append(item)

    # 替代旧 since 参数，沿用共享日期过滤的现有边界规则，不在此次迁移中重构。
    papers = filter_by_date(papers, target_date, days_back)
    print(f"[INFO] aihot fetched {len(papers)} papers after date filter", file=sys.stderr)
    return papers


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
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Step 1: 多源获取论文原始数据。返回 items 列表。"""
    if config is None:
        raise ValueError("config is required — pass load_config(CONFIG_FILE) result")

    # 确定 target_date（北京时间 8 点前用前一天）
    target_date = get_now_date_str(config["fetch"]['target_date'])

    # 优先拉取 aihot，成功则直接使用，不再请求 arXiv / HuggingFace
    aihot_items = fetch_aihot_papers(config, target_date)

    if len(aihot_items) > 0:
        all_items = aihot_items
        print(f"[INFO] aihot 获取成功，共 {len(all_items)} 篇论文，跳过 arXiv / HuggingFace", file=sys.stderr)
    else:
        # aihot 失败或无数据，回退到 arXiv + HuggingFace 双源合并
        print("[INFO] aihot 无数据，回退到 arXiv + HuggingFace", file=sys.stderr)
        # 分别捕获来源异常：一个源失败时仍尝试另一个，并保留已成功获取的数据。
        try:
            arxiv_items = fetch_arxiv_papers(config, target_date)
        except Exception as e:
            print(f"[WARN] arXiv fetch failed: {e}", file=sys.stderr)
            arxiv_items = []
        try:
            hf_items = fetch_hf_daily_papers(config, target_date)
        except Exception as e:
            print(f"[WARN] HuggingFace fetch failed: {e}", file=sys.stderr)
            hf_items = []
        all_items = merge_papers(arxiv_items, hf_items)
        print(f"[INFO] Fetched {len(all_items)} papers total "
              f"(arxiv:{len(arxiv_items)} hf:{len(hf_items)})", file=sys.stderr)

        # 翻译英文论文（arxiv / huggingface 来源）
        all_items = translate_papers(all_items, config)

    return all_items


# ── 翻译（arXiv / HuggingFace 英文论文 → 中文）─────────────────

def translate_papers(
    papers: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """将 arXiv / HuggingFace 来源的英文论文标题和摘要翻译为中文。

    翻译后在 paper dict 中新增 title_zh / summary_zh 字段。
    aihot 来源已是中文，跳过。

    Args:
        papers:   论文列表
        config:   配置字典（需包含 translation 段）
    """
    cfg = config["translation"]
    if not cfg["enabled"]:
        return papers

    # 筛选需要翻译的论文（仅 arxiv / huggingface 来源）
    need = [p for p in papers if p.get("source_api") in ("arxiv", "huggingface")]
    if not need:
        return papers

    api_key_env = cfg["api_key_env"]
    api_key = os.environ.get(api_key_env) or get_dot_env().get(api_key_env, "")
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
            # 【修复标识｜2026-10-18｜译文 ID 对齐】不能按位置 zip：漏译会使后续译文错配。
            # ID 是本批次从 0 开始的编号，不是论文自身 ID；每批重新建立映射。
            translations_by_id = {trans["id"]: trans for trans in translations}
            for idx, paper in enumerate(batch):
                trans = translations_by_id.get(idx)
                if trans is None:
                    # 缺少对应 ID 时保留论文原文，不借用其他论文的译文。
                    print(f"[WARN] Translation batch {i // batch_size + 1}: missing id {idx}, keeping original", file=sys.stderr)
                    continue
                t_zh = trans.get("title_zh", "").strip()
                s_zh = trans.get("summary_zh", "").strip()
                if t_zh:
                    paper["title_zh"] = t_zh
                if s_zh:
                    paper["summary_zh"] = s_zh
                # 只有实际写入非空译文才计为成功，避免空结果虚增成功数。
                if t_zh or s_zh:
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
        "每条结果必须保留输入的整数 id，不要重新编号；无法翻译时保留 id 并将译文字段留空。\n"
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

    # 【修复标识｜2026-10-18｜模型响应校验】逐条校验，坏记录不能中断同批其他论文。
    # 不接受无 ID、字符串/浮点/布尔 ID 或越界 ID；不能用列表位置猜测所属论文。
    validated = []
    seen_ids = set()
    for trans in result:
        if not isinstance(trans, dict):
            print("[WARN] Translation entry is not an object, skipped", file=sys.stderr)
            continue
        idx = trans.get("id")
        if type(idx) is not int or not 0 <= idx < expected_count:
            print(f"[WARN] Invalid translation id {idx!r}, skipped", file=sys.stderr)
            continue
        if idx in seen_ids:
            # 同一 ID 只保留首次结果，并记录告警，避免后续重复结果悄悄覆盖。
            print(f"[WARN] Duplicate translation id {idx}, keeping first", file=sys.stderr)
            continue
        seen_ids.add(idx)
        cleaned = dict(trans)
        for field in ("title_zh", "summary_zh"):
            if field in cleaned and not isinstance(cleaned[field], str):
                # 非字符串译文视为缺失；仍允许同条记录的另一个有效字段使用。
                print(f"[WARN] Translation id {idx}: invalid {field}, keeping original field", file=sys.stderr)
                cleaned.pop(field)
        validated.append(cleaned)

    # 排序仅用于稳定输出；真正关联由 translate_papers 按 ID 完成，而非按顺序。
    validated.sort(key=lambda x: x["id"])
    return validated
