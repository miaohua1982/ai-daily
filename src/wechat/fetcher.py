"""
wechat/fetcher - 内容获取（复用 generate_daily / generate_papers 的 fetch + filter）。

通过 gd.fetch_data / gp.fetch_data 获取原始数据 + 各自 filter_data 过滤，
返回全量原始池（不去重、不截断）。去重统一在 cross_dedup_news_papers 完成：
URL 精确去重（无条件） + 全量语义去重（集合内 + 集合间，同一阈值），news 优先保留。
截断统一在 generate_wechat.main 的 cross dedup 之后、按 MAX_NEWS / MAX_PAPERS 上限做。
"""

import os
import sys
import urllib.parse
from typing import Dict, List, Tuple

from utils import load_config, get_now_date_str, get_dot_env, semantic_dedup
import generate_daily as gd
import generate_papers as gp


def fetch_news() -> List[Dict]:
    """
    通过 generate_daily 的 step 函数获取 + 过滤新闻（不去重）。

    去重统一交给 cross_dedup_news_papers（URL + 语义全量去重）。

    Returns:
        news_items - 全量原始池（已展平并标注 _section），不去重、不截断；
        截断统一在 generate_wechat.main 的 cross dedup 之后按 MAX_NEWS 做。
    """
    try:
        config = load_config(gd.CONFIG_FILE)
        items = gd.fetch_data(config=config)
    except Exception as e:
        print(f"[WARN] fetch_news failed: {e}", file=sys.stderr)
        return []

    if not items:
        return []

    # 去重已移至 cross_dedup_news_papers 统一处理（URL + 语义一次跑全量）
    # 使用 generate_daily 的过滤（摘要长度）
    filtered_news = gd.filter_data(items, config)
    print(f"[INFO] News: {len(filtered_news)} items after filtering")

    return filtered_news


def fetch_papers() -> List[Dict]:
    """
    通过 generate_papers 的 step 函数获取 + 过滤论文（不去重）。

    去重统一交给 cross_dedup_news_papers（URL + 语义全量去重）。

    Returns:
        papers - 全量原始池，不去重、不截断；
        截断统一在 generate_wechat.main 的 cross dedup 之后按 MAX_PAPERS 做。
    """
    try:
        config = load_config(gp.CONFIG_FILE)
        items = gp.fetch_data(config=config)
    except Exception as e:
        print(f"[WARN] fetch_papers failed: {e}", file=sys.stderr)
        return []

    if not items:
        return []

    # 去重已移至 cross_dedup_news_papers 统一处理（URL + 语义一次跑全量）
    # 使用 generate_papers 的过滤（摘要长度）
    filtered_papers = gp.filter_data(items, config)
    print(f"[INFO] Papers: {len(filtered_papers)} items after filtering")

    return filtered_papers


def cross_dedup_news_papers(
    news: List[Dict],
    papers: List[Dict],
    config: Dict,
) -> Tuple[List[Dict], List[Dict]]:
    """
    news + papers 全量统一去重（唯一去重入口，必做无开关）。

    fetch_news / fetch_papers 只抓取 + 过滤、不去重，本函数承担全部去重：
      1. URL 精确去重（无条件执行）：按 sourceUrl → url → mobileUrl 取 key，
         去掉 fragment 后精确比对（逻辑同 utils.dedup_data 的 URL 段）
      2. 语义去重（凭证可用时执行）：集合内 + 集合间一次跑全量，
         统一阈值 threshold（默认 0.75）

    保留优先级说明：URL 去重按顺序保留首次出现；semantic_dedup 贪心保留
    「第一个」条目。merged 按 [*news, *papers] 组装（news 在前），故
    news↔paper 撞车时自动保留 news、删除 paper，对应「重复保留 A」的约定。

    单边为空也照常执行（另一边仍需集合内去重），仅两边全空时早退。
    保持分块渲染，返回 (news, papers) 供 renderer 原样使用。
    """
    if not news and not papers:
        return news, papers

    cross_cfg = config.get("cross_dedup", {})

    # 1. 统一去重文本（中文优先），并打 _kind 标记
    merged = []
    for it in news:
        c = dict(it)
        c["_dedup_title"] = c.get("title", "")
        c["_kind"] = "news"
        merged.append(c)
    for it in papers:
        c = dict(it)
        c["_dedup_title"] = c.get("title_zh") or c.get("title") or ""
        c["_kind"] = "paper"
        merged.append(c)

    # 2. URL 精确去重（无条件执行；news 在前 → URL 撞车保留 news）
    before_url = len(merged)
    seen = set()
    url_deduped = []
    for it in merged:
        url = it.get("sourceUrl") or it.get("url") or it.get("mobileUrl") or ""
        key = urllib.parse.urldefrag(url)[0]
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        url_deduped.append(it)
    if len(url_deduped) != before_url:
        print(
            f"[INFO] Cross dedup URL: {before_url} -> {len(url_deduped)}",
            file=sys.stderr,
        )
    merged = url_deduped

    # 3. 合并跑一次语义去重（news 在前 → 重复时保留 news、删 paper）
    api_key_env = cross_cfg.get("api_key_env", "EMBEDDING_API_KEY")
    api_key = os.environ.get(api_key_env) or get_dot_env().get(api_key_env, "")
    base_url = cross_cfg.get("base_url", "")
    model = cross_cfg.get("model", "text-embedding-3-small")
    threshold = float(cross_cfg.get("threshold", 0.75))
    batch_size = int(cross_cfg.get("batch_size", 10))

    if api_key and base_url:
        before = len(merged)
        merged = semantic_dedup(
            merged, threshold, api_key, base_url, model, batch_size,
            title_key="_dedup_title",
        )
        removed = before - len(merged)
        if removed > 0:
            print(
                f"[INFO] Cross dedup semantic: removed {removed} duplicate(s)",
                file=sys.stderr,
            )
            print(
                f"[INFO] Cross dedup semantic: {before} -> {len(merged)}",
                file=sys.stderr,
            )
    else:
        # 语义段跳过时仍保留上方 URL 去重结果
        print(
            "[WARN] Cross dedup semantic skipped: API key/base_url not configured",
            file=sys.stderr,
        )

    # 4. 按 _kind 拆回，并剥离内部标记字段
    def _clean(lst):
        return [{k: v for k, v in it.items() if not k.startswith("_")} for it in lst]

    new_news = _clean([it for it in merged if it["_kind"] == "news"])
    new_papers = _clean([it for it in merged if it["_kind"] == "paper"])
    return new_news, new_papers
