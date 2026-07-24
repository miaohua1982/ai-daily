"""
wechat/weekly_fetcher - 「一周论文回顾」周报内容获取。

与日报 fetcher（src/wechat/fetcher.py）的差异：
  - 数据源直接 arXiv + HuggingFace Daily Papers，跳过 aihot
    （复用 src/papers/fetcher.py 的抓取/合并/翻译函数，不碰 gp.fetch_data
    的「优先 aihot」编排逻辑）
  - 时间窗口为「自然周」：本周一 00:00 ~ 运行日（周日运行 = 完整 7 天）
  - 排序精选：HF（带 upvotes 热度）降序在前为主力，arXiv（无热度信号）
    按发布时间倒序在后作补位，截断 top_n

处理顺序（成本最优）：
  抓取 → 合并 → 摘要长度过滤 → 去重(URL+语义) → 排序 → 截断 top_n → 翻译
  翻译放在截断之后，每周只翻译 top_n 篇（而非全池 200+ 篇），节省 LLM 成本；
  语义去重在翻译前用英文原题做 embedding，两源标题同为英文，可直接比对。
"""

import sys
from datetime import datetime
from typing import Any, Dict, List

from utils import get_now_date_str, dedup_data
from src.papers.fetcher import (
    fetch_arxiv_papers,
    fetch_hf_daily_papers,
    merge_papers,
    translate_papers,
)


def natural_week_days_back(target_date: str) -> int:
    """计算自然周窗口天数：本周一 ~ target_date（含当天）共几天。

    weekday(): 周一=0 ... 周日=6，故天数 = weekday + 1：
      - 周日运行 → 7（完整覆盖本周一~周日）
      - 周三手动补跑 → 3（本周一~周三的部分周）

    解析失败时兜底返回 7（一整周），保证抓取不中断。
    """
    try:
        d = datetime.strptime(target_date, "%Y-%m-%d")
        return d.weekday() + 1
    except Exception:
        return 7


def fetch_weekly_papers(config: Dict[str, Any]) -> List[Dict]:
    """获取一周论文精选（周报唯一内容入口）。

    Args:
        config: weekly_config.yaml 加载结果（含 fetch/arxiv/huggingface/
                translation/semantic_dedup/filter/weekly 各段）

    Returns:
        排序精选后的论文列表（HF 高赞在前、arXiv 补位在后，已翻译），
        长度 <= weekly.top_n。
    """
    # ── 1. 确定自然周窗口 ──────────────────────────────────────
    # target_date 取运行日（北京时间）；days_back 按「本周第几天」动态覆盖
    # config 中的兜底值，使底层 fetcher 的滚动窗口恰好等于自然周窗口。
    target_date = get_now_date_str(config["fetch"]["target_date"])
    days_back = natural_week_days_back(target_date)
    config["fetch"]["days_back"] = days_back
    print(
        f"[INFO] Weekly window: {days_back} day(s) back from {target_date} (natural week)",
        file=sys.stderr,
    )

    # ── 2. 双源抓取（跳过 aihot）───────────────────────────────
    # HF 为主力（带 upvotes），arXiv 为补充（分类 + 时间倒序，无热度信号）
    try:
        hf_items = fetch_hf_daily_papers(config, target_date)
    except Exception as e:
        print(f"[WARN] Weekly HF fetch failed: {e}", file=sys.stderr)
        hf_items = []
    try:
        arxiv_items = fetch_arxiv_papers(config, target_date)
    except Exception as e:
        print(f"[WARN] Weekly arXiv fetch failed: {e}", file=sys.stderr)
        arxiv_items = []

    # ── 3. 双源合并 ────────────────────────────────────────────
    # merge_papers 按 id/url 精确合并、先到先得：HF 在前 ⇒ 同一篇论文
    # 两源都有时保留 HF 版（含 upvotes / ai_summary 等热度字段）。
    merged = merge_papers(hf_items, arxiv_items)
    print(
        f"[INFO] Weekly merged: {len(merged)} papers (hf:{len(hf_items)} arxiv:{len(arxiv_items)})",
        file=sys.stderr,
    )
    if not merged:
        return []

    # ── 4. 摘要长度过滤 ────────────────────────────────────────
    # 提前过滤（早于翻译）：无摘要/超短摘要的论文渲染出来没有信息量。
    # 此时尚未翻译，比对英文 summary（arXiv 摘要普遍很长，几乎不误伤）。
    min_len = config.get("filter", {}).get("min_summary_len", 0)
    if min_len > 0:
        before = len(merged)
        merged = [
            p for p in merged
            if len((p.get("summary") or p.get("description") or "").strip()) >= min_len
        ]
        if len(merged) != before:
            print(
                f"[INFO] Weekly summary-length filter: {before} -> {len(merged)}",
                file=sys.stderr,
            )

    # ── 5. 去重（URL 精确 + 语义）──────────────────────────────
    # 复用 utils.dedup_data：URL 去 fragment 精确去重（无条件）+
    # 集合内语义去重（读 config.semantic_dedup，凭证缺失自动跳过）。
    # 语义去重用英文原题 embedding，先于翻译执行。
    merged = dedup_data(merged, config)

    # ── 6. 排序精选 ────────────────────────────────────────────
    # HF 主力：upvotes 降序（社区已投票选优）；
    # arXiv 补位：publishedAt 倒序（无热度信号，最新优先）排在 HF 全部之后。
    hf_pool = [p for p in merged if p.get("source_api") == "huggingface"]
    arxiv_pool = [p for p in merged if p.get("source_api") != "huggingface"]
    hf_pool.sort(key=lambda p: p.get("upvotes", 0) or 0, reverse=True)
    arxiv_pool.sort(key=lambda p: p.get("publishedAt", "") or "", reverse=True)
    ranked = hf_pool + arxiv_pool

    # ── 7. 截断 top_n ─────────────────────────────────────────
    top_n = int(config.get("weekly", {}).get("top_n", 30))
    selected = ranked[:top_n]
    print(
        f"[INFO] Weekly selected: {len(selected)}/{len(ranked)} papers "
        f"(hf:{len(hf_pool)} arxiv:{len(arxiv_pool)}, top_n={top_n})",
        file=sys.stderr,
    )

    # ── 8. 翻译（仅 top_n 篇，控制 LLM 成本）───────────────────
    # translate_papers 就地补充 title_zh / summary_zh 字段，
    # 凭证缺失时自动跳过（渲染层会回退英文原文）。
    selected = translate_papers(selected, config)

    # ── 9. 统一链接：所有周报论文指向 arXiv 摘要页 ────────────────
    # HF 论文的 id 即 arXiv id，可直接拼出 https://arxiv.org/abs/{id}；
    # arXiv 论文 id 本就是 arXiv id，归一化后不变（幂等）。
    # 仅作用于周报管线 —— 不改动 fetch_hf_daily_papers，日报/普通
    # papers 页的 HF 论文仍保留 https://huggingface.co/papers/{id} 链接。
    for p in selected:
        pid = (p.get("id") or "").strip()
        if pid:
            p["url"] = f"https://arxiv.org/abs/{pid}"

    return selected
