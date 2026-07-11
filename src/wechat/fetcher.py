"""
wechat/fetcher - 内容获取（复用 generate_daily / generate_papers 的 fetch + dedup）。

通过 gd.fetch_data / gp.fetch_data 获取原始数据，再用各自的 dedup_data 去重，
最后展平并截断到 max_news / max_papers 上限。
"""

import sys
from typing import Dict, List, Tuple

from utils import load_config, get_now_date_str
import generate_daily as gd
import generate_papers as gp


def fetch_news(max_news: int) -> List[Dict]:
    """
    通过 generate_daily 的 step 函数获取 + 去重新闻。

    Returns:
        (news_items, ) - news_items 已展平并标注 _section，截断到 max_news 条。
    """
    try:
        config = load_config(gd.CONFIG_FILE)
        items = gd.fetch_data(config=config)
    except Exception as e:
        print(f"[WARN] fetch_news failed: {e}", file=sys.stderr)
        return []

    if not items:
        return []

    # 使用 generate_daily 的去重（URL + 语义）
    deduped_news_list = gd.dedup_data(items, config)

    print(f"[INFO] News: {len(deduped_news_list)} items after dedup")
    return deduped_news_list[:max_news]


def fetch_papers(max_papers: int) -> List[Dict]:
    """
    通过 generate_papers 的 step 函数获取 + 去重论文。

    Returns:
        (papers, ) - papers 已截断到 max_papers 条。
    """
    try:
        config = load_config(gp.CONFIG_FILE)
        items = gp.fetch_data(config=config)
    except Exception as e:
        print(f"[WARN] fetch_papers failed: {e}", file=sys.stderr)
        return []

    if not items:
        return []

    # 使用 generate_papers 的去重（URL + 语义 + top 选择）
    papers = gp.dedup_data(items, config)

    print(f"[INFO] Papers: {len(papers)} items after dedup")
    return papers[:max_papers]
