"""
trending.renderer — HTML 渲染（含辅助工具函数）。
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple

from utils import esc_html, esc_attr
from utils.html_template import (
    render_trending_html,
    TRENDING_CARD_TEMPLATE,
    TRENDING_SECTION_TEMPLATE,
)


def source_meta(item: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, str, str]:
    """返回 (来源名称, 图标, 热度文本)。"""
    sid = item.get("source_id", "")
    for s in config["newsnow"]["sources"]:
        if s["id"] == sid:
            return s["name"], s.get("icon", "•"), ""
    return sid, "•", ""


def format_updated(ts: Any) -> str:
    """格式化更新时间戳为 HH:MM。"""
    if not ts:
        return ""
    try:
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def generate_html(
    grouped_items: Dict[str, List[Dict[str, Any]]],
    config: Dict[str, Any],
    build_time: datetime,
) -> str:
    """Step 4: 纯 HTML 渲染，不含去重或过滤逻辑。"""
    # 强制按固定顺序展示分组
    desired_order = ["国际局势", "财经资讯", "AI大模型", "智能汽车", "机器人与具身智能", "其他"]
    ordered = {}
    for name in desired_order:
        if name in grouped_items:
            ordered[name] = grouped_items[name]
    for name, items in grouped_items.items():
        if name not in ordered:
            ordered[name] = items
    grouped_items = ordered

    total = sum(len(v) for v in grouped_items.values())

    # 为每个分组分配颜色
    group_colors = [
        "#6366f1", "#0891b2", "#d97706", "#7c3aed", "#059669",
        "#dc2626", "#2563eb", "#ea580c", "#0891b2", "#be185d"
    ]
    color_map = {}
    for i, group_name in enumerate(grouped_items.keys()):
        color_map[group_name] = group_colors[i % len(group_colors)]

    # 构建导航链接
    nav_links_parts = []
    for group_name, items in grouped_items.items():
        if not items:
            continue
        anchor = group_name.replace(" ", "-").lower()
        color = color_map[group_name]
        count = len(items)
        nav_links_parts.append(
            f'    <a href="#sec-{anchor}" class="nav-link">\n'
            f'      <span class="nav-dot" style="background:{color}"></span>{esc_html(group_name)}\n'
            f'      <span class="nav-cnt">{count}</span>\n'
            f'    </a>'
        )
    nav_links = "\n".join(nav_links_parts)

    # 构建分组 sections
    sections_parts = []
    item_counter = 0
    for group_name, items in grouped_items.items():
        if not items:
            continue
        anchor = group_name.replace(" ", "-").lower()
        color = color_map[group_name]
        count = len(items)

        cards_parts = []
        for it in items:
            item_counter += 1
            idx = item_counter
            title = esc_html(it.get("title", "无标题"))
            url = it.get("url") or it.get("mobileUrl") or "#"
            url_attr = esc_attr(url)
            src_name, _, _ = source_meta(it, config)

            source_class = "source-x"
            if "wechat" in src_name.lower() or "微信" in src_name:
                source_class = "source-wechat"
            elif "blog" in src_name.lower() or "博客" in src_name:
                source_class = "source-blog"
            elif "hacker" in src_name.lower() or "hn" in src_name.lower():
                source_class = "source-hn"
            elif "github" in src_name.lower() or "gh" in src_name.lower():
                source_class = "source-gh"

            score_badge = ""
            if "ai_score" in it:
                score = it["ai_score"]
                if score >= 0.8:
                    score_badge = f'<span class="score-badge score-high">关联度：{score:.2f}</span>'
                elif score >= 0.6:
                    score_badge = f'<span class="score-badge score-mid">关联度：{score:.2f}</span>'
                else:
                    score_badge = f'<span class="score-badge score-low">关联度：{score:.2f}</span>'

            updated = format_updated(it.get("updatedTime"))
            time_str = f"{updated}" if updated else ""

            cards_parts.append(
                TRENDING_CARD_TEMPLATE.format(
                    idx=idx,
                    title=title,
                    source_class=source_class,
                    source_name=esc_html(src_name),
                    time_str=time_str,
                    score_badge=score_badge,
                    url=url_attr,
                )
            )

        cards_html = "\n".join(cards_parts)
        sections_parts.append(
            TRENDING_SECTION_TEMPLATE.format(
                anchor=anchor,
                color=color,
                group_name=esc_html(group_name),
                count=count,
                cards_html=cards_html,
            )
        )

    sections_html = "\n".join(sections_parts)

    display_date = build_time.strftime("%Y-%m-%d %H:%M")
    wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][build_time.weekday()]

    return render_trending_html(
        total=total,
        group_count=len(grouped_items),
        display_date=display_date,
        weekday=wd,
        nav_links=nav_links,
        sections_html=sections_html,
    )
