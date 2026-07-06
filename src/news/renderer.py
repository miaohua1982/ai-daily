"""
news/renderer — 新闻 HTML 渲染（含卡片、分类、导航构建）。
"""

from datetime import datetime, timezone, timedelta

from utils import esc_html, esc_attr
from utils.html_template import (
    render_news_html,
    NEWS_CARD_TEMPLATE,
    NEWS_SECTION_TEMPLATE,
    NEWS_EMPTY_SECTION_TEMPLATE,
)
from src.news.constants import CATEGORY_ORDER, CATEGORY_LABELS, CATEGORY_COLORS, EMPTY_ICONS


def fmt_time(dt_str):
    """格式化相对时间（暂未使用，保留以备后续需求）。"""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        dt = dt.astimezone(timezone(timedelta(hours=8)))
        now = datetime.now(timezone(timedelta(hours=8)))
        diff = now - dt
        s = diff.total_seconds()
        if s < 3600:
            return f"{max(1, int(s // 60))} 分钟前"
        elif s < 86400:
            return f"{int(s // 3600)} 小时前"
        else:
            return dt.strftime("今天 %H:%M")
    except Exception:
        return dt_str or ""


def source_class(source_name):
    """根据来源名称返回 CSS class 名。"""
    s = (source_name or "").lower()
    if "x：" in s or "twitter" in s or s.startswith("x:"):
        return "source-x"
    if "公众号" in s or "wechat" in s or "微信" in s:
        return "source-wechat"
    if "github" in s:
        return "source-gh"
    if any(x in s for x in ["marktechpost", "cloudflare", "dwarkesh", "elastic", "rss"]):
        return "source-blog"
    if any(x in s for x in ["hacker news", "hn ", "buzzing", "eff"]):
        return "source-hn"
    return "source-media"


def short_source(source_name):
    """从完整 sourceName 中提取 2-6 字简短标签。"""
    s = (source_name or "").lower()
    if "x：" in s or s.startswith("x:"):
        return "X"
    if "公众号" in s:
        return "公众号"
    if "github" in s:
        return "GitHub"
    if "marktechpost" in s:
        return "博客"
    if "rss" in s:
        return "RSS"
    if "arxiv" in s:
        return "arXiv"
    if "hacker news" in s or "buzzing" in s:
        return "HN"
    words = source_name.split()
    if words:
        first = words[0].rstrip("：:")
        return first[:6]
    return "来源"


def summarize(text, max_len=60):
    """截断摘要文本到指定长度。"""
    if not text:
        return "暂无摘要"
    t = text.strip()
    return t if len(t) <= max_len else t[:max_len - 1].rstrip() + "…"


def generate_html(items_by_cat, data, date_str):
    """Step 3: 纯 HTML 渲染，不含任何数据获取或去重逻辑。"""
    cat_counts = {cat: len(items_by_cat.get(cat, [])) for cat in CATEGORY_ORDER}
    total = sum(cat_counts.values())

    # 展示日期
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        wd = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][d.weekday()]
        display_date = f"{d.year}年{d.month}月{d.day}日 · {wd}"
    except Exception:
        display_date = date_str

    # 计算相对于日报窗口的时间
    window_relative = ""
    try:
        w_end_str = data.get("windowEnd", "")
        w_end = datetime.fromisoformat(w_end_str.replace("Z", "+00:00"))
        w_end_bj = w_end.astimezone(timezone(timedelta(hours=8)))
        now_bj = datetime.now(timezone(timedelta(hours=8)))
        diff_hours = int((now_bj - w_end_bj).total_seconds() // 3600)
        if diff_hours <= 0:
            window_relative = "今天上午"
        elif diff_hours < 24:
            window_relative = f"{diff_hours} 小时前"
        else:
            days = diff_hours // 24
            window_relative = f"{days} 天前"
    except Exception:
        window_relative = ""

    # ── 构建卡片 HTML（全局编号）──
    cards_parts = {}
    global_idx = 0
    for cat in CATEGORY_ORDER:
        cards_parts[cat] = []
        for item in items_by_cat.get(cat, []):
            global_idx += 1
            title = esc_html(item.get("title", "无标题"))
            summary = esc_html(summarize(item.get("summary", ""), 60))
            url = item.get("sourceUrl") or item.get("url", "#")
            url_attr = esc_attr(url)
            source_name = item.get("sourceName", "")
            source_short = esc_html(short_source(source_name))
            sc = source_class(source_name)
            time_str = window_relative

            cards_parts[cat].append(
                NEWS_CARD_TEMPLATE.format(
                    idx=global_idx,
                    title=title,
                    source_short=source_short,
                    source_class=sc,
                    summary=summary,
                    time_str=time_str,
                    url=url_attr,
                )
            )

    # ── 构建分类区块 ──
    sections_parts = []
    for cat in CATEGORY_ORDER:
        label = CATEGORY_LABELS[cat]
        color = CATEGORY_COLORS[cat]
        count = cat_counts[cat]

        if count == 0:
            icon = EMPTY_ICONS.get(cat, "📌")
            sections_parts.append(
                NEWS_EMPTY_SECTION_TEMPLATE.format(
                    cat=cat, color=color, label=label, icon=icon,
                )
            )
        else:
            cards_html = "\n".join(cards_parts[cat])
            sections_parts.append(
                NEWS_SECTION_TEMPLATE.format(
                    cat=cat, color=color, label=label, count=count,
                    cards_html=cards_html,
                )
            )

    sections_html = "\n".join(sections_parts)

    # ── 构建导航 ──
    nav_items_parts = []
    for cat in CATEGORY_ORDER:
        lbl = CATEGORY_LABELS[cat]
        cnt = cat_counts[cat]
        nav_items_parts.append(
            f'    <a href="#sec-{cat}" class="nav-link">\n'
            f'      <span class="nav-dot" style="background:{CATEGORY_COLORS[cat]}"></span>{lbl}\n'
            f'      <span class="nav-cnt">{cnt}</span>\n'
            f'    </a>'
        )
    nav_items = "\n".join(nav_items_parts)

    return render_news_html(
        display_date=display_date,
        total=total,
        nav_items=nav_items,
        sections_html=sections_html,
    )
