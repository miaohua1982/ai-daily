#!/usr/bin/env python3
"""
AI HOT Academic Papers Archive Generator
Fetches recent AI papers from aihot.virxact.com and generates a static HTML archive.
Usage: python generate_papers.py [YYYY-MM-DD]
"""

import sys
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
API_BASE = "https://aihot.virxact.com/api/public"
OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "papers-archive"
INDEX_FILE = OUTPUT_DIR / "papers.html"

SOURCE_COLORS = {
    "arxiv": ("#fce4ec", "#c0392b"),
    "hugging face": ("#fff3e0", "#e65100"),
    "openai": ("#e8f5e9", "#2e7d32"),
    "anthropic": ("#f3e5f5", "#7b1fa2"),
    "google": ("#e3f2fd", "#1565c0"),
    "nvidia": ("#e8f5e9", "#2e7d32"),
    "nature": ("#fbe9e7", "#d84315"),
    "mit": ("#fce4ec", "#c0392b"),
    "stanford": ("#fbe9e7", "#bf360c"),
    "berkeley": ("#e8eaf6", "#283593"),
    "microsoft": ("#e3f2fd", "#1565c0"),
    "deepmind": ("#e8eaf6", "#283593"),
}


def api_get(path):
    url = API_BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print("[WARN] HTTP", e.code, "for", path, file=sys.stderr)
        return None
    except Exception as e:
        print("[WARN] Failed to fetch", path, e, file=sys.stderr)
        return None


def sanitize(s):
    """Remove lone surrogates and other invalid Unicode from a string."""
    if not isinstance(s, str):
        return s
    return s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def fetch_papers(since_iso):
    all_items = []
    cursor = ""
    remaining = 150
    for _ in range(3):
        url = ("/items?mode=all&category=paper&since=" + since_iso +
               "&take=" + str(min(remaining, 100)))
        if cursor:
            url += "&cursor=" + cursor
        data = api_get(url)
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
    print("[INFO] Fetched", len(all_items), "papers total", file=sys.stderr)
    return all_items


def select_top_papers(items, limit=50):
    selected = [i for i in items if i.get("selected")]
    not_selected = [i for i in items if not i.get("selected")]
    selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    not_selected.sort(key=lambda x: x.get("score", 0), reverse=True)
    result = selected[:limit]
    if len(result) < limit:
        result += not_selected[:limit - len(result)]
    seen = set()
    unique = []
    for p in result:
        key = p["title"][:30]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    unique.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return unique[:limit]


def get_badge_color(source):
    sl = (source or "").lower()
    for key, (bg, text) in SOURCE_COLORS.items():
        if key in sl:
            return (bg, text)
    return ("#f0f0f0", "#555555")


def get_badge_label(source):
    s = source or ""
    for sep in ["\uff1a", ":"]:
        if sep in s:
            s = s.split(sep)[0].strip()
    if "(" in s:
        s = s.split("(")[0].strip()
    if len(s) > 20:
        s = s[:20] + "\u2026"
    return s


def fetch_daily_papers(target_date=None):
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        since_dt = dt - timedelta(days=7)
    else:
        now_bj = datetime.now(timezone(timedelta(hours=8)))
        if now_bj.hour < 9:
            now_bj = now_bj - timedelta(days=1)
        since_dt = now_bj - timedelta(days=7)
        target_date = now_bj.strftime("%Y-%m-%d")
    since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    items = fetch_papers(since_iso)
    papers = select_top_papers(items, limit=50)
    return papers, target_date


def group_by_date(papers):
    groups = {}
    for p in papers:
        d = (p.get("publishedAt") or "")[:10]
        if not d:
            continue
        if d not in groups:
            groups[d] = []
        groups[d].append(p)
    keys = sorted(groups.keys(), reverse=True)
    return groups, keys


def generate_html(papers, date_str):
    groups, sorted_dates = group_by_date(papers)
    total = len(papers)
    num_dates = len(sorted_dates)
    weekday_names = ["\u661f\u671f\u65e5", "\u661f\u671f\u4e00", "\u661f\u671f\u4e8c",
                     "\u661f\u671f\u4e09", "\u661f\u671f\u56db", "\u661f\u671f\u4e94", "\u661f\u671f\u516d"]

    # ---- Build JS data arrays ----
    papers_js_items = []
    global_idx = 0
    for d in sorted_dates:
        for p in groups[d]:
            global_idx += 1
            title = sanitize(p.get("title", "") or "")
            source = sanitize(p.get("source", "") or "")
            summary = sanitize(p.get("summary", "") or "") or "\u6682\u65e0\u6458\u8981"
            if len(summary) > 200:
                summary = summary[:200] + "\u2026"
            source_color = get_badge_color(source)
            entry = {
                "idx": global_idx,
                "title": title,
                "source": source,
                "badgeLabel": get_badge_label(source),
                "badgeBg": source_color[0],
                "badgeColor": source_color[1],
                "publishedAt": p.get("publishedAt", ""),
                "dateStr": (p.get("publishedAt") or "")[:10],
                "url": sanitize(p.get("url", "#") or "#"),
                "summary": summary,
                "selected": p.get("selected", False),
                "score": p.get("score", 0),
            }
            papers_js_items.append(json.dumps(entry, ensure_ascii=False))

    timeline_js_items = []
    for d in sorted_dates:
        try:
            wd = weekday_names[datetime.strptime(d, "%Y-%m-%d").weekday()]
        except Exception:
            wd = ""
        timeline_js_items.append(json.dumps(
            {"date": d, "wd": wd, "count": len(groups[d])},
            ensure_ascii=False))

    papers_json = "[\n" + ",\n".join(papers_js_items) + "\n]"
    timeline_json = "[\n" + ",\n".join(timeline_js_items) + "\n]"

    # ── CSS (as a regular string, not f-string) ──
    css = """\
    :root {
        --hero-from: #ff5e3a;
        --hero-mid: #f73b4a;
        --hero-to: #c0392b;
        --accent: #ff6b35;
        --accent-dark: #e0552b;
        --accent-light: rgba(255,107,53,.08);
        --bg: #faf8f6;
        --card-bg: #ffffff;
        --card-border: #ede8e2;
        --text: #2c2c2c;
        --text-secondary: #6b6b6b;
        --text-muted: #999999;
        --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
        --shadow-md: 0 4px 12px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.04);
        --shadow-lg: 0 12px 32px rgba(0,0,0,.1), 0 4px 8px rgba(0,0,0,.05);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        --timeline-dot: #ff6b35;
        --timeline-line: #ede8e2;
        --timeline-active-bg: rgba(255,107,53,.06);
      }
    
      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    
      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
        font-size: 14px;
      }
    
      /* ========= HEADER (matching daily hero) ========= */
      .header {
        position: relative; overflow: hidden;
        background: linear-gradient(135deg, var(--hero-from) 0%, var(--hero-mid) 40%, var(--hero-to) 100%);
        color: #fff;
        padding: 40px 24px 36px;
        text-align: center;
        z-index: 100;
        box-shadow: 0 4px 20px rgba(0,0,0,.15);
      }
      .header::before {
        content: '';
        position: absolute; inset: 0;
        background: radial-gradient(ellipse at 70% 30%, rgba(255,255,255,.15) 0%, transparent 60%),
                    radial-gradient(ellipse at 20% 80%, rgba(255,200,120,.12) 0%, transparent 50%);
      }
      .header-inner {
        position: relative; z-index: 1;
        max-width: 720px; margin: 0 auto;
        display: flex; flex-direction: column; align-items: center; gap: 16px;
      }
      .header-badge {
        display: inline-block;
        background: rgba(255,255,255,.2);
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,.25);
        border-radius: 100px;
        padding: 4px 16px;
        font-size: 13px; font-weight: 600; letter-spacing: 0.5px;
      }
      .header-title {
        font-size: clamp(22px, 4vw, 32px);
        font-weight: 800;
        letter-spacing: -0.5px;
      }
      .header-sub {
        font-size: 14px;
        opacity: 0.85;
      }
      .header-stats {
        display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;
      }
      .stat-card {
        display: flex; flex-direction: column; align-items: center;
        background: rgba(255,255,255,.15);
        backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,.2);
        border-radius: var(--radius-md);
        padding: 10px 18px; min-width: 80px;
      }
      .stat-num { font-size: 24px; font-weight: 800; line-height: 1.2; }
      .stat-label { font-size: 11px; opacity: 0.8; margin-top: 2px; }
    
      /* ========= LAYOUT ========= */
      .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 28px 24px 48px;
        display: grid;
        grid-template-columns: 160px 1fr;
        gap: 24px;
        align-items: start;
      }
    
      /* ========= TIMELINE ========= */
      .timeline {
        position: sticky;
        top: 24px;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-lg);
        padding: 16px 12px;
        box-shadow: var(--shadow-sm);
      }
      .timeline-title {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: .8px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--card-border);
      }
      .timeline-list { list-style: none; position: relative; }
      .timeline-list::before {
        content: '';
        position: absolute;
        left: 8px; top: 4px; bottom: 4px;
        width: 2px;
        background: linear-gradient(to bottom, var(--timeline-dot), var(--card-border));
        border-radius: 2px;
      }
      .timeline-item {
        position: relative;
        padding: 5px 0 5px 22px;
        cursor: pointer;
        border-radius: 6px;
        transition: background .15s;
      }
      .timeline-item:hover { background: var(--accent-light); }
      .timeline-item.active { background: var(--accent-light); }
      .timeline-item::before {
        content: '';
        position: absolute;
        left: 4px; top: 50%;
        transform: translateY(-50%);
        width: 10px; height: 10px;
        border-radius: 50%;
        background: var(--card-bg);
        border: 2px solid var(--card-border);
        transition: border-color .15s, background .15s;
      }
      .timeline-item:hover::before,
      .timeline-item.active::before {
        border-color: var(--timeline-dot);
        background: var(--timeline-dot);
      }
      .timeline-date { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
      .timeline-count { font-size: 10px; color: var(--text-muted); margin-top: 1px; }
    
      /* ========= PAPER LIST ========= */
      .papers-section { display: flex; flex-direction: column; gap: 0; }
      .date-group { margin-bottom: 32px; }
      .date-anchor { display: block; height: 1px; margin-top: -90px; padding-top: 90px; pointer-events: none; }
      .date-header {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--card-border);
      }
      .date-pill {
        background: var(--accent);
        color: white;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 12px;
        border-radius: 100px;
      }
      .date-weekday { font-size: 12px; color: var(--text-muted); }
      .date-count { font-size: 12px; color: var(--text-muted); margin-left: auto; }
    
      .papers-stack { display: flex; flex-direction: column; gap: 12px; }
    
      /* ========= PAPER CARD ========= */
      .paper-card {
        position: relative;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-lg);
        padding: 20px 20px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,.06);
        transition: var(--transition);
        display: flex; flex-direction: column;
        opacity: 0;
        transform: translateY(18px);
      }
      .paper-card.visible {
        opacity: 1;
        transform: translateY(0);
      }
      .paper-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,.07);
        transform: translateY(-2px);
      }
      .paper-card.visible:hover {
        transform: translateY(-2px);
      }
      .paper-card.selected-card {
        border-left: 3px solid var(--accent);
      }
    
      .card-header {
        display: flex; align-items: flex-start; gap: 10px;
        margin-bottom: 10px;
      }
      .card-num {
        position: absolute; top: -10px; left: 14px;
        background: var(--accent); color: #fff;
        font-size: 11px; font-weight: 700;
        width: 24px; height: 24px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 6px rgba(255,107,53,.35);
        flex-shrink: 0;
      }
      .selected-card .card-num {
        background: var(--accent-dark);
        box-shadow: 0 2px 8px rgba(255,107,53,.5);
      }
    
      .card-title-wrap { flex: 1; min-width: 0; margin-top: 6px; }
      .card-title {
        font-size: 15px;
        font-weight: 700;
        color: var(--text);
        line-height: 1.5;
        text-decoration: none;
        display: block;
      }
      .card-title:hover { color: var(--accent); }
    
      .card-meta {
        display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
        margin-top: 6px;
      }
      .badge {
        display: inline-block;
        font-size: 11px; font-weight: 600;
        padding: 3px 10px; border-radius: 100px;
        white-space: nowrap;
        max-width: 160px;
        overflow: hidden; text-overflow: ellipsis;
      }
      .rel-time {
        font-size: 11px;
        color: var(--text-muted);
      }
      .score-dot {
        margin-left: auto;
        font-size: 11px;
        color: var(--text-muted);
        display: flex; align-items: center; gap: 3px;
      }
      .score-star { color: #F6C90E; }
    
      .card-summary {
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.65;
        margin-bottom: 14px;
        flex: 1;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
    
      .card-footer {
        display: flex; align-items: center; justify-content: flex-end;
        margin-top: auto;
        padding-top: 10px;
        border-top: 1px solid var(--card-border);
      }
      .read-link {
        display: inline-flex; align-items: center; gap: 5px;
        font-size: 13px; font-weight: 600;
        color: var(--accent);
        text-decoration: none;
        padding: 6px 14px;
        border-radius: 100px;
        background: var(--accent-light);
        transition: var(--transition);
      }
      .read-link:hover {
        background: rgba(255,107,53,.16);
        color: var(--accent-dark);
      }
      .read-link svg { width: 14px; height: 14px; }
    
      /* ========= SEARCH BAR ========= */
      .search-bar {
        grid-column: 1 / -1;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-md);
        padding: 10px 16px;
        box-shadow: var(--shadow-sm);
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 4px;
      }
      .search-input {
        border: none; outline: none;
        width: 100%;
        font-size: 14px;
        color: var(--text);
        background: transparent;
      }
      .search-input::placeholder { color: var(--text-muted); }
      .search-icon { color: var(--text-muted); flex-shrink: 0; }
      .search-count { font-size: 12px; color: var(--text-muted); white-space: nowrap; }
    
      /* ========= FOOTER ========= */
      .footer {
        text-align: center;
        padding: 32px 16px 40px;
        border-top: 1px solid var(--card-border);
        color: var(--text-muted);
        font-size: 13px;
        max-width: 1200px; margin: 0 auto;
      }
      .footer a { color: var(--accent); text-decoration: none; }
      .footer a:hover { text-decoration: underline; }
    
      /* ========= BACK TO TOP ========= */
      .quick-top {
        position: fixed; bottom: 24px; right: 24px;
        width: 44px; height: 44px; border-radius: 50%;
        background: var(--accent); color: #fff;
        border: none; cursor: pointer; font-size: 20px;
        box-shadow: 0 12px 32px rgba(0,0,0,.1);
        opacity: 0; transform: translateY(12px);
        pointer-events: none; transition: var(--transition); z-index: 200;
        display: flex; align-items: center; justify-content: center;
      }
      .quick-top.visible { opacity: 1; transform: translateY(0); pointer-events: auto; }
      .quick-top:hover { background: var(--accent-dark); }
    
      /* ========= RESPONSIVE ========= */
      @media (max-width: 768px) {
        .header { padding: 32px 16px 28px; }
        .header-stats { gap: 10px; }
        .stat-card { padding: 8px 14px; min-width: 64px; }
        .stat-num { font-size: 20px; }
        .main {
          grid-template-columns: 1fr;
          padding: 16px;
        }
        .timeline { position: static; display: none; }
        .search-bar { grid-column: 1; }
        .card-title { font-size: 14px; }
        .paper-card { padding: 16px 16px 14px; }
      }
    """

    # ---- search SVG ----
    search_svg = (
        '<svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"'
        ' fill="currentColor" viewBox="0 0 16 16">'
        '<path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.099zm-5.242 1.656a5.5 5.5 0 1 1 0-11 5.5 5.5 0 0 1 0 11z"/>'
        '</svg>'
    )

    #  ---- ext SVG (read link) ----
    ext_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>'
        '<path d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>'
        '</svg>'
    )

    # ---- Build date-group HTML shells ----
    date_groups_html = ""
    for d in sorted_dates:
        try:
            wd = weekday_names[datetime.strptime(d, "%Y-%m-%d").weekday()]
        except Exception:
            wd = ""
        date_groups_html += (
            '  <div class="date-group">\n'
            '    <div class="date-anchor" id="anchor-' + d + '"></div>\n'
            '    <div class="date-header">\n'
            '      <span class="date-pill">' + d + '</span>\n'
            '      <span class="date-weekday">' + wd + '</span>\n'
            '      <span class="date-count">' + str(len(groups[d])) + ' \u7bc7</span>\n'
            '    </div>\n'
            '    <div class="papers-stack" id="stack-' + d + '"></div>\n'
            '  </div>\n'
        )

    # ---- JS ----
    js = (
        "(function(){\n"
        "  var WEEKDAYS = ['\u661f\u671f\u65e5','\u661f\u671f\u4e00','\u661f\u671f\u4e8c',"
        "'\u661f\u671f\u4e09','\u661f\u671f\u56db','\u661f\u671f\u4e94','\u661f\u671f\u516d'];\n"
        "\n"
        "  function relativeTime(isoStr){\n"
        "    var now = Date.now();\n"
        "    var t = new Date(isoStr).getTime();\n"
        "    var diff = Math.floor((now - t) / 1000);\n"
        "    if(diff < 60) return '\u521a\u521a';\n"
        "    if(diff < 3600) return Math.floor(diff/60) + ' \u5206\u949f\u524d';\n"
        "    if(diff < 86400) return Math.floor(diff/3600) + ' \u5c0f\u65f6\u524d';\n"
        "    if(diff < 604800) return Math.floor(diff/86400) + ' \u5929\u524d';\n"
        "    return new Date(isoStr).toLocaleDateString('zh-CN',{month:'numeric',day:'numeric'});\n"
        "  }\n"
        "\n"
        "  function escHtml(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }\n"
        "  function escAttr(s){ return s.replace(/&/g,'&amp;').replace(/\"/g,'&quot;'); }\n"
        "\n"
        "  function buildTimeline(){\n"
        "    var list = document.getElementById('timelineList');\n"
        "    if(!list) return;\n"
        "    list.innerHTML = '';\n"
        "    window.TIMELINE_DATA.forEach(function(g){\n"
        "      var li = document.createElement('li');\n"
        "      li.className = 'timeline-item';\n"
        "      li.dataset.date = g.date;\n"
        "      li.innerHTML = '<div class=\"timeline-date\">' + g.date.slice(5) + '</div>'\n"
        "        + '<div class=\"timeline-count\">' + g.wd + ' \\u00b7 ' + g.count + ' \u7bc7</div>';\n"
        "      li.addEventListener('click', function(){\n"
        "        var el = document.getElementById('anchor-' + g.date);\n"
        "        if(el) el.scrollIntoView({behavior:'smooth', block:'start'});\n"
        "      });\n"
        "      list.appendChild(li);\n"
        "    });\n"
        "  }\n"
        "\n"
        "  function buildCards(filtered){\n"
        "    var section = document.getElementById('papersSection');\n"
        "    if(!section) return;\n"
        "    section.innerHTML = '';\n"
        "\n"
        "    var groups = {};\n"
        "    filtered.forEach(function(p){\n"
        "      if(!groups[p.dateStr]) groups[p.dateStr] = [];\n"
        "      groups[p.dateStr].push(p);\n"
        "    });\n"
        "    var sortedDates = Object.keys(groups).sort(function(a,b){ return b.localeCompare(a); });\n"
        "\n"
        "    var timelineGroups = sortedDates.map(function(d){\n"
        "      return {date:d, wd:WEEKDAYS[new Date(d+'T00:00:00+08:00').getDay()], count:groups[d].length};\n"
        "    });\n"
        "    window.TIMELINE_DATA = timelineGroups;\n"
        "    buildTimeline();\n"
        "\n"
        "    sortedDates.forEach(function(date){\n"
        "      var grp = groups[date];\n"
        "      var d = new Date(date + 'T00:00:00+08:00');\n"
        "      var wd = WEEKDAYS[d.getDay()];\n"
        "      var groupEl = document.createElement('div');\n"
        "      groupEl.className = 'date-group';\n"
        "      var anchor = document.createElement('div');\n"
        "      anchor.className = 'date-anchor';\n"
        "      anchor.id = 'anchor-' + date;\n"
        "      groupEl.appendChild(anchor);\n"
        "      var header = document.createElement('div');\n"
        "      header.className = 'date-header';\n"
        "      header.innerHTML = '<span class=\"date-pill\">' + date + '</span>'\n"
        "        + '<span class=\"date-weekday\">' + wd + '</span>'\n"
        "        + '<span class=\"date-count\">' + grp.length + ' \u7bc7</span>';\n"
        "      groupEl.appendChild(header);\n"
        "      var stack = document.createElement('div');\n"
        "      stack.className = 'papers-stack';\n"
        "\n"
        "      grp.forEach(function(p){\n"
        "        var card = document.createElement('div');\n"
        "        card.className = 'paper-card' + (p.selected ? ' selected-card' : '');\n"
        "        card.dataset.id = p.idx;\n"
        "        var shtml = '';\n"
        "        if(p.summary && p.summary !== '\u6682\u65e0\u6458\u8981'){\n"
        "          shtml = '<div class=\"card-summary\">' + escHtml(p.summary) + '</div>';\n"
        "        }\n"
        "        card.innerHTML =\n"
        "          '<div class=\"card-header\">' +\n"
        "            '<div class=\"card-num\">' + p.idx + '</div>' +\n"
        "            '<div class=\"card-title-wrap\">' +\n"
        "              '<a class=\"card-title\" href=\"' + escAttr(p.url) + '\" target=\"_blank\" rel=\"noopener\">' + escHtml(p.title) + '</a>' +\n"
        "              '<div class=\"card-meta\">' +\n"
        "                '<span class=\"badge\" style=\"background:' + escAttr(p.badgeBg) + ';color:' + escAttr(p.badgeColor) + '\" title=\"' + escAttr(p.source) + '\">' + escHtml(p.badgeLabel) + '</span>' +\n"
        "                '<span class=\"rel-time\">' + relativeTime(p.publishedAt) + '</span>' +\n"
        "                '<span class=\"score-dot\"><span class=\"score-star\">\\u2605</span>' + p.score + '</span>' +\n"
        "              '</div>' +\n"
        "            '</div>' +\n"
        "          '</div>' +\n"
        "          shtml +\n"
        "          '<div class=\"card-footer\">' +\n"
        "            '<a class=\"read-link\" href=\"' + escAttr(p.url) + '\" target=\"_blank\" rel=\"noopener\">' +\n"
        "              '" + ext_svg.replace('\"', '\\\\\"') + "' + ' \\u9605\\u8bfb\\u539f\\u6587</a>' +\n"
        "          '</div>';\n"
        "        stack.appendChild(card);\n"
        "      });\n"
        "      groupEl.appendChild(stack);\n"
        "      section.appendChild(groupEl);\n"
        "    });\n"
        "\n"
        "    document.getElementById('filtered-count').textContent = filtered.length;\n"
        "\n"
        "    var observer = new IntersectionObserver(function(entries){\n"
        "      entries.forEach(function(e){\n"
        "        if(e.isIntersecting){ e.target.classList.add('visible'); observer.unobserve(e.target); }\n"
        "      });\n"
        "    }, {threshold:0.08, rootMargin:'0px 0px -40px 0px'});\n"
        "    document.querySelectorAll('.paper-card').forEach(function(el){ observer.observe(el); });\n"
        "\n"
        "    highlightTimeline();\n"
        "  }\n"
        "\n"
        "  function highlightTimeline(){\n"
        "    var groups = document.querySelectorAll('.date-group');\n"
        "    var tItems = document.querySelectorAll('.timeline-item');\n"
        "    var scrollY = window.scrollY + 160;\n"
        "    var activeDate = null;\n"
        "    groups.forEach(function(g){\n"
        "      var anchor = g.querySelector('.date-anchor');\n"
        "      if(anchor && anchor.getBoundingClientRect().top + window.scrollY <= scrollY){\n"
        "        activeDate = g.querySelector('.date-anchor').id.replace('anchor-','');\n"
        "      }\n"
        "    });\n"
        "    tItems.forEach(function(item){\n"
        "      item.classList.toggle('active', item.dataset.date === activeDate);\n"
        "    });\n"
        "  }\n"
        "\n"
        "  window.addEventListener('scroll', highlightTimeline, {passive:true});\n"
        "\n"
        "  var searchInput = document.getElementById('searchInput');\n"
        "  var searchCount = document.getElementById('searchCount');\n"
        "  var debounceTimer;\n"
        "  if(searchInput){\n"
        "    searchInput.addEventListener('input', function(){\n"
        "      clearTimeout(debounceTimer);\n"
        "      debounceTimer = setTimeout(function(){\n"
        "        var q = searchInput.value.trim().toLowerCase();\n"
        "        var filtered;\n"
        "        if(!q){ filtered = window.PAPERS; }\n"
        "        else { filtered = window.PAPERS.filter(function(p){\n"
        "          return (p.title && p.title.toLowerCase().indexOf(q)!==-1)\n"
        "              || (p.summary && p.summary.toLowerCase().indexOf(q)!==-1)\n"
        "              || (p.source && p.source.toLowerCase().indexOf(q)!==-1)\n"
        "              || (p.badgeLabel && p.badgeLabel.toLowerCase().indexOf(q)!==-1);\n"
        "        }); }\n"
        "        searchCount.textContent = filtered.length + ' \u7bc7';\n"
        "        buildCards(filtered);\n"
        "      }, 250);\n"
        "    });\n"
        "  }\n"
        "\n"
        "  buildCards(window.PAPERS);\n"
        "  buildTimeline();\n"
        "\n"
        "  /* ---- back to top ---- */\n"
        "  var qtop = document.getElementById('quickTop');\n"
        "  window.addEventListener('scroll', function(){\n"
        "    qtop.classList.toggle('visible', window.scrollY > 400);\n"
        "  });\n"
        "})();\n"
    )

    # ---- Assemble final HTML ----
    html = "<!DOCTYPE html>\n"
    html += '<html lang="zh-CN">\n'
    html += "<head>\n"
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html += "<title>AI \u5b66\u672f\u6863\u6848\u5e93 \u00b7 \u8fd1\u65e5\u8bba\u6587\u7cbe\u9009</title>\n"
    html += "<style>\n" + css + "\n</style>\n"
    html += "</head>\n"
    html += "<body>\n"
    html += "\n"
    html += '<header class="header">\n'
    html += '  <div class="header-inner">\n'
    html += '    <div class="header-badge">\U0001f4c4 AI \u5b66\u672f\u6863\u6848\u5e93</div>\n'
    html += '    <h1 class="header-title">\u8fd1\u65e5 AI \u8bba\u6587\u7cbe\u9009</h1>\n'
    html += '    <p class="header-sub">\u6570\u636e\u6765\u6e90 AI HOT \u00b7 \u8fc7\u53bb 7 \u5929\u7cbe\u9009 ' + str(total) + ' \u7bc7</p>\n'
    html += '    <div class="header-stats">\n'
    html += '      <div class="stat-card">\n'
    html += '        <span class="stat-num" id="total-count">' + str(total) + '</span>\n'
    html += '        <span class="stat-label">\u8bba\u6587\u603b\u6570</span>\n'
    html += '      </div>\n'
    html += '      <div class="stat-card">\n'
    html += '        <span class="stat-num">' + str(num_dates) + '</span>\n'
    html += '        <span class="stat-label">\u8986\u76d6\u5929\u6570</span>\n'
    html += '      </div>\n'
    html += '      <div class="stat-card">\n'
    html += '        <span class="stat-num" id="filtered-count">' + str(total) + '</span>\n'
    html += '        <span class="stat-label">\u5f53\u524d\u663e\u793a</span>\n'
    html += '      </div>\n'
    html += '    </div>\n'
    html += '  </div>\n'
    html += '</header>\n'
    html += "\n"
    html += '<main class="main">\n'
    html += '  <div class="search-bar">\n'
    html += "    " + search_svg + "\n"
    html += '    <input class="search-input" id="searchInput" type="text"'
    html += ' placeholder="\u641c\u7d22\u8bba\u6587\u6807\u9898\u3001\u6458\u8981\u6216\u6765\u6e90\u2026" autocomplete="off">\n'
    html += '    <span class="search-count" id="searchCount">' + str(total) + " \u7bc7</span>\n"
    html += "  </div>\n"
    html += "\n"
    html += '  <nav class="timeline">\n'
    html += '    <div class="timeline-title">\u65f6\u95f4\u8f74</div>\n'
    html += '    <ul class="timeline-list" id="timelineList"></ul>\n'
    html += "  </nav>\n"
    html += "\n"
    html += '  <section class="papers-section" id="papersSection">\n'
    html += date_groups_html
    html += "  </section>\n"
    html += "</main>\n"
    html += "\n"
    html += '<footer class="footer">\n'
    html += '  \u6570\u636e\u6765\u6e90\uff1a<a href="https://aihot.virxact.com" target="_blank" rel="noopener">AI HOT</a>'
    html += " \u00b7 \u7cbe\u9009\u8bba\u6587 \u00b7 \u4ec5\u4f9b\u5b66\u672f\u53c2\u8003\n"
    html += "</footer>\n"
    html += "\n"
    html += '<script>\nwindow.PAPERS = ' + papers_json + ";\n"
    html += 'window.TIMELINE_DATA = ' + timeline_json + ";\n"
    html += "</script>\n"
    html += "\n"
    html += "<script>\n" + js + "</script>\n"
    html += "\n"
    html += '<div class="quick-top" id="quickTop" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">\u2191</div>\n'
    html += "\n"
    html += "</body>\n"
    html += "</html>\n"

    # Final cleanup: remove any remaining surrogate characters
    html = html.encode("utf-8", errors="replace").decode("utf-8")

    return html


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    papers, actual_date = fetch_daily_papers(target_date)

    if not papers:
        print("[WARN] No papers found, skipping.", file=sys.stderr)
        sys.exit(0)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    html = generate_html(papers, actual_date)

    INDEX_FILE.write_text(html, encoding="utf-8")
    print("[INFO] Written", INDEX_FILE.name, "(" + str(len(html)) + " bytes)", file=sys.stderr)

    archive_file = ARCHIVE_DIR / (actual_date + ".html")
    archive_file.write_text(html, encoding="utf-8")
    print("[INFO] Archived to", archive_file, file=sys.stderr)

    cwd = str(OUTPUT_DIR)
    subprocess.run(["git", "add", "papers.html", "papers-archive/" + actual_date + ".html"], cwd=cwd, check=False)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd, capture_output=True)
    if result.returncode != 0:
        msg = "chore: update papers archive " + actual_date
        subprocess.run(["git", "commit", "-m", msg], cwd=cwd, check=False)
        push_result = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
        if push_result.returncode == 0:
            print("[INFO] Committed and pushed:", msg, file=sys.stderr)
        else:
            print("[WARN] Commit done, but push failed:", push_result.stderr, file=sys.stderr)
            print("[WARN] Run 'git push' manually.", file=sys.stderr)
    else:
        print("[INFO] No changes to commit", file=sys.stderr)


if __name__ == "__main__":
    main()
