"""
wechat/renderer — 微信公众号草稿 HTML 渲染（组合 news + papers）。

具体渲染逻辑放在本包内；纯模板碎片（WECHAT_* 常量）仍由 utils.html_template 提供，
保持与 src/news/renderer.py、src/papers/renderer.py 一致的分层：领域装配在 src/<domain>，
纯模版留在 utils。
"""

from utils import esc_html as _esc_html
from utils.html_template import (
    WECHAT_HEAD_SECTION,
    WECHAT_NEWS_HEADER,
    WECHAT_ITEM_TEMPLATE,
    WECHAT_PAPERS_HEADER,
    WECHAT_PAPER_TEMPLATE,
    WECHAT_COLOR_PALETTE,
    WECHAT_FOOT_SECTION,
)


def _wechat_format_date_cn(date_str: str) -> str:
    """Format date_str (YYYY-MM-DD) to Chinese display format."""
    from datetime import datetime as _dt
    try:
        d = _dt.strptime(date_str, "%Y-%m-%d")
        wd = ["一", "二", "三", "四", "五", "六", "日"][d.weekday()]
        return f"{d.year}年{d.month}月{d.day}日 · 周{wd}"
    except Exception:
        return date_str


def _wechat_badge_html(label: str, color: str) -> str:
    """Build an inline-styled badge span for WeChat HTML."""
    return (
        f'<span style="display:inline-block;background:{color}15;'
        f'color:{color};padding:1px 8px;border-radius:4px;'
        f'font-size:11px;line-height:18px">{_esc_html(label)}</span>'
    )


def _wechat_build_news_item(i: int, it: dict) -> str:
    """Build a single WeChat news item section."""
    title = _esc_html(it.get("title", ""))
    summary = _esc_html(it.get("summary") or it.get("description") or "")
    source = _esc_html(it.get("sourceName") or it.get("source") or "来源")
    section = _esc_html(it.get("category", "tips"))
    url = (it.get("sourceUrl") or it.get("url") or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    # Cycle through 4-color palette
    accent, bg = WECHAT_COLOR_PALETTE[(i - 1) % len(WECHAT_COLOR_PALETTE)]

    # 方案A: 链接只包标题文字, 避免整卡 <a> 包块级 section 在微信内链场景被剥离 background
    title_strong = '<strong style="color:#111827;font-size:15px;font-weight:700">'
    if url:
        title_block = f'{title_strong}<a href="{url}" style="color:inherit;text-decoration:none">{title}</a></strong>'
    else:
        title_block = f'{title_strong}{title}</strong>'

    html = WECHAT_ITEM_TEMPLATE.format(
        num=i, title_block=title_block, summary=summary, source=source,
        accent_color=accent, bg_color=bg,
    )
    if section:
        badge = _wechat_badge_html(section, accent)
        html = html.replace("{section_badge}", badge)
    else:
        html = html.replace("{section_badge}", "")
    return html


def _wechat_build_paper_item(i: int, it: dict, show_source: bool = True, link_button: bool = False) -> str:
    """Build a single WeChat paper item section.

    show_source: 是否渲染来源徽章行（日报默认 True；周报传 False 去掉来源）。
    link_button: 是否在卡片底部显示一行明文 arXiv 链接（仅周报启用；
        微信屏蔽跳转，故直接展示 URL 供复制，而非可点击按钮）。
    """
    title = _esc_html(it.get("title_zh") or it.get("title", ""))
    summary = _esc_html(it.get("summary_zh") or it.get("summary") or it.get("description") or "")
    source = _esc_html(it.get("source") or "arXiv")
    url = (it.get("url") or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    # Cycle through 4-color palette
    accent, bg = WECHAT_COLOR_PALETTE[(i - 1) % len(WECHAT_COLOR_PALETTE)]

    # 方案A: 链接只包标题文字, 避免整卡 <a> 包块级 section 在微信内链场景被剥离 background
    title_strong = '<strong style="color:#111827;font-size:15px;font-weight:700">'
    if url:
        title_block = f'{title_strong}<a href="{url}" style="color:inherit;text-decoration:none">{title}</a></strong>'
    else:
        title_block = f'{title_strong}{title}</strong>'

    # 来源行：日报保留；周报去来源（show_source=False → 空行）
    if show_source:
        badge = _wechat_badge_html(source, accent)
        # 注意用单花括号 {source_badge}，供下方 .replace 注入徽章
        # （模板本身已把来源行抽成 {source_line} 占位，日报回填此处内容）
        source_line = f'<section style="margin:0;font-size:11px;color:#9ca3af;line-height:1.5">{{source_badge}}</section>'
    else:
        source_line = ""
        badge = ""

    # 底部 arXiv 链接行（仅周报）：微信公众号会屏蔽 <a> 跳转，故直接显示明文
    # URL（包一层 <a> 仅供网页预览可点，微信端呈现为可长按复制的网址文字）。
    # <a> 只包行内文字，不包块级 section，不会触发微信 background 剥离。
    if link_button and url:
        url_esc = _esc_html(url)
        link_button_line = (
            f'<section style="margin:8px 0 0;font-size:11px;color:#2563eb;'
            f'line-height:1.5;word-break:break-all">'
            f'🔗 arXiv: <a href="{url}" style="color:#2563eb;'
            f'text-decoration:none;word-break:break-all">{url_esc}</a></section>'
        )
    else:
        link_button_line = ""

    html = WECHAT_PAPER_TEMPLATE.format(
        num=i, title_block=title_block, summary=summary,
        source_line=source_line, link_button_line=link_button_line,
        accent_color=accent, bg_color=bg,
    )
    if show_source:
        html = html.replace("{source_badge}", badge)
    return html


def _wechat_md_news_item(i: int, it: dict) -> str:
    """Build a single news item in Markdown format."""
    title = it.get("title", "")
    summary = it.get("summary") or it.get("description") or ""
    source = it.get("sourceName") or it.get("source") or "来源"
    category = it.get("category", "")
    url = (it.get("sourceUrl") or it.get("url") or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    # Title with optional link
    if url:
        head = f"**{i}. [{title}]({url})**"
    else:
        head = f"**{i}. {title}**"

    # Summary as blockquote with full-width indent
    lines = [head, ""]
    if summary:
        lines.append(f"> 　{summary}")
        lines.append("")

    # Tags: source + category
    tags = []
    if category:
        tags.append(f"`{category}`")
    tags.append(f"`{source}`")
    lines.append(" ".join(tags))

    return "\n".join(lines)


def _wechat_md_paper_item(i: int, it: dict, show_source: bool = True, link_button: bool = False) -> str:
    """Build a single paper item in Markdown format.

    show_source / link_button: 同 _wechat_build_paper_item（日报默认显示来源、
    无按钮；周报去来源 + 末尾加 arXiv 链接行）。
    """
    title = it.get("title_zh") or it.get("title", "")
    summary = it.get("summary_zh") or it.get("summary") or it.get("description") or ""
    source = it.get("source") or "arXiv"
    url = (it.get("url") or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    if url:
        head = f"**{i}. [{title}]({url})**"
    else:
        head = f"**{i}. {title}**"

    lines = [head, ""]
    if summary:
        lines.append(f"> 　{summary}")
        lines.append("")

    # 来源 tag（日报显示；周报去来源）
    if show_source:
        lines.append(f"`{source}`")
        lines.append("")

    # arXiv 链接行（仅周报）：微信屏蔽跳转，直接显示明文 URL 便于复制
    if link_button and url:
        lines.append(f"🔗 arXiv: {url}")

    return "\n".join(lines)


def render_wechat_md(
    news: list[dict], papers: list[dict], date_str: str, repo_url: str,
    main_title: str = "📰 每日 AI 情报",
    papers_label: str = "📄 AI 前沿技术",
    show_paper_source: bool = True,
    paper_link_button: bool = False,
) -> str:
    """Render Markdown version of the WeChat digest (for local preview / GitHub).

    main_title / papers_label 可选：默认沿用日报文案（老调用不传参 ⇒ 行为不变）；
    周报（generate_wechat_papers_weekly）分别传「📚 AI 一周论文回顾」/「📄 本周精选论文」。
    """
    display = _wechat_format_date_cn(date_str)

    parts = [
        f"# {main_title}",
        "",
        f"> {display}",
        "",
        "---",
        "",
    ]

    # ── AI News ──
    if news:
        parts.append(f"## 🔥 AI 热点资讯（{len(news)}条）")
        parts.append("")
        for i, it in enumerate(news, 1):
            parts.append(_wechat_md_news_item(i, it))
            parts.append("")
            parts.append("---")
            parts.append("")

    # ── AI Papers ──
    if papers:
        parts.append(f"## {papers_label}（{len(papers)}篇）")
        parts.append("")
        for i, it in enumerate(papers, 1):
            parts.append(_wechat_md_paper_item(i, it, show_paper_source, paper_link_button))
            parts.append("")
            parts.append("---")
            parts.append("")

    # ── Footer ──
    parts.append(f"> 📖 更多内容请访问 [ai-daily]({repo_url})")

    return "\n".join(parts)


def render_wechat_html(
    news: list[dict], papers: list[dict], date_str: str, repo_url: str,
    main_title: str = "📰 每日 AI 情报",
    papers_label: str = "📄 AI 前沿技术",
    show_paper_source: bool = True,
    paper_link_button: bool = False,
) -> str:
    """Render WeChat-compatible HTML (inline styles only, minimal style block for hover).

    main_title / papers_label 可选：默认沿用日报文案（老调用不传参 ⇒ 行为不变）；
    周报（generate_wechat_papers_weekly）分别传「📚 AI 一周论文回顾」/「📄 本周精选论文」。
    """
    display = _wechat_format_date_cn(date_str)

    css = (
        '<style>'
        '.ai-card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.08);border-left-width:5px}'
        '.ai-card:active{transform:translateY(0);box-shadow:0 3px 10px rgba(0,0,0,.06)}'
        '</style>'
    )
    parts = [css, WECHAT_HEAD_SECTION.format(display_date=display, main_title=main_title)]

    # ── AI News ──
    if news:
        parts.append(WECHAT_NEWS_HEADER.format(count=len(news)))
        for i, it in enumerate(news, 1):
            parts.append(_wechat_build_news_item(i, it))

    # ── AI Papers ──
    if papers:
        parts.append(WECHAT_PAPERS_HEADER.format(count=len(papers), papers_label=papers_label))
        for i, it in enumerate(papers, 1):
            parts.append(_wechat_build_paper_item(i, it, show_paper_source, paper_link_button))

    parts.append(WECHAT_FOOT_SECTION.format(repo_url=repo_url))
    return "\n".join(parts)


def wrap_wechat_html_doc(html_fragment: str, date_str: str, doc_title: str = "每日 AI 情报") -> str:
    """Wrap a WeChat-style HTML fragment into a complete, locally-viewable document.

    render_wechat_html returns a fragment without <html>/<head>/<body> (what the
    WeChat draft API expects). For local preview we add a minimal complete document
    with charset + title so browsers render Chinese correctly.

    doc_title 可选：浏览器标签页标题，默认日报文案；周报传「AI 一周论文回顾」。
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{doc_title} {date_str}</title>\n"
        "</head>\n"
        "<body>\n"
        f"{html_fragment}\n"
        "</body>\n"
        "</html>\n"
    )
