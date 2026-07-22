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


def _wechat_build_paper_item(i: int, it: dict) -> str:
    """Build a single WeChat paper item section."""
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

    html = WECHAT_PAPER_TEMPLATE.format(
        num=i, title_block=title_block, summary=summary, source=source,
        accent_color=accent, bg_color=bg,
    )
    badge = _wechat_badge_html(source, accent)
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


def _wechat_md_paper_item(i: int, it: dict) -> str:
    """Build a single paper item in Markdown format."""
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

    lines.append(f"`{source}`")

    return "\n".join(lines)


def render_wechat_md(
    news: list[dict], papers: list[dict], date_str: str, repo_url: str
) -> str:
    """Render Markdown version of the WeChat daily digest (for local preview / GitHub)."""
    display = _wechat_format_date_cn(date_str)

    parts = [
        "# 📰 每日 AI 情报",
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
        parts.append(f"## 📄 AI 前沿技术（{len(papers)}篇）")
        parts.append("")
        for i, it in enumerate(papers, 1):
            parts.append(_wechat_md_paper_item(i, it))
            parts.append("")
            parts.append("---")
            parts.append("")

    # ── Footer ──
    parts.append(f"> 📖 更多内容请访问 [ai-daily]({repo_url})")

    return "\n".join(parts)


def render_wechat_html(
    news: list[dict], papers: list[dict], date_str: str, repo_url: str
) -> str:
    """Render WeChat-compatible HTML (inline styles only, minimal style block for hover)."""
    display = _wechat_format_date_cn(date_str)

    css = (
        '<style>'
        '.ai-card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.08);border-left-width:5px}'
        '.ai-card:active{transform:translateY(0);box-shadow:0 3px 10px rgba(0,0,0,.06)}'
        '</style>'
    )
    parts = [css, WECHAT_HEAD_SECTION.format(display_date=display)]

    # ── AI News ──
    if news:
        parts.append(WECHAT_NEWS_HEADER.format(count=len(news)))
        for i, it in enumerate(news, 1):
            parts.append(_wechat_build_news_item(i, it))

    # ── AI Papers ──
    if papers:
        parts.append(WECHAT_PAPERS_HEADER.format(count=len(papers)))
        for i, it in enumerate(papers, 1):
            parts.append(_wechat_build_paper_item(i, it))

    parts.append(WECHAT_FOOT_SECTION.format(repo_url=repo_url))
    return "\n".join(parts)


def wrap_wechat_html_doc(html_fragment: str, date_str: str) -> str:
    """Wrap a WeChat-style HTML fragment into a complete, locally-viewable document.

    render_wechat_html returns a fragment without <html>/<head>/<body> (what the
    WeChat draft API expects). For local preview we add a minimal complete document
    with charset + title so browsers render Chinese correctly.
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>每日 AI 情报 {date_str}</title>\n"
        "</head>\n"
        "<body>\n"
        f"{html_fragment}\n"
        "</body>\n"
        "</html>\n"
    )
