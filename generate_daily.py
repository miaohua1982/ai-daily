#!/usr/bin/env python3
"""
AI HOT Daily Dashboard Generator
Fetches daily AI news from aihot.virxact.com and generates a static HTML dashboard.
Usage: python generate_daily.py [YYYY-MM-DD]
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
API_BASE = "https://aihot.virxact.com/api/public"
OUTPUT_DIR = Path(__file__).parent
ARCHIVE_DIR = OUTPUT_DIR / "news-archive"
INDEX_FILE = OUTPUT_DIR / "daily_news.html"

CATEGORY_LABELS = {
    "ai-models": "模型发布/更新",
    "ai-products": "产品发布/更新",
    "industry": "行业动态",
    "paper": "论文研究",
    "tip": "技巧与观点",
}
# Reverse mapping: Chinese label → English slug (API now uses Chinese labels)
LABEL_TO_SLUG = {v: k for k, v in CATEGORY_LABELS.items()}
CATEGORY_ORDER = ["ai-models", "ai-products", "industry", "paper", "tip"]
CATEGORY_COLORS = {
    "ai-models": "#6366f1",
    "ai-products": "#0891b2",
    "industry": "#d97706",
    "paper": "#7c3aed",
    "tip": "#059669",
}

EMPTY_ICONS = {
    "ai-models": "📭",
    "ai-products": "📦",
    "industry": "📰",
    "paper": "📄",
    "tip": "💡",
}


def api_get(path):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[WARN] HTTP {e.code} for {path}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] Failed to fetch {path}: {e}", file=sys.stderr)
        return None


def fmt_time(dt_str):
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
    """Extract a 2-4 char label from the full sourceName."""
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
    # Fallback: first word up to 4 chars
    words = source_name.split()
    if words:
        first = words[0].rstrip("：:")
        return first[:6]
    return "来源"


def summarize(text, max_len=60):
    if not text:
        return "暂无摘要"
    t = text.strip()
    return t if len(t) <= max_len else t[:max_len - 1].rstrip() + "…"


def fetch_daily(target_date=None):
    if target_date:
        date_str = target_date
    else:
        bj = datetime.now(timezone(timedelta(hours=8)))
        if bj.hour < 8:
            bj = bj - timedelta(days=1)
        date_str = bj.strftime("%Y-%m-%d")

    print(f"[INFO] Fetching daily for {date_str} ...")
    data = api_get(f"/daily/{date_str}")
    if data and "sections" in data:
        print(f"[INFO] Got daily {date_str}")
        return data, date_str

    print(f"[WARN] Daily {date_str} not available, falling back to latest...")
    dailies = api_get("/dailies?take=5")
    if dailies and dailies.get("items"):
        latest = dailies["items"][0]["date"]
        print(f"[INFO] Fallback to {latest}")
        data = api_get(f"/daily/{latest}")
        return data, latest

    raise RuntimeError("Failed to fetch any daily report")


def esc_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def generate_html(data, date_str):
    sections = data.get("sections", [])
    items_by_cat = {}
    for sec in sections:
        label = sec.get("label", "")
        cat = LABEL_TO_SLUG.get(label, "")
        items_by_cat[cat] = sec.get("items", [])

    cat_counts = {cat: len(items_by_cat.get(cat, [])) for cat in CATEGORY_ORDER}
    total = sum(cat_counts.values())

    # Display date
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        wd = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][d.weekday()]
        display_date = f"{d.year}年{d.month}月{d.day}日 · {wd}"
    except Exception:
        display_date = date_str

    # Compute relative time from daily window
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

    # ── Build card HTML (global numbering) ──
    cards_parts = {}  # cat -> list of card html strings
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
            source = esc_html(source_name)
            time_str = window_relative
            sc = source_class(source_name)
            card = (
                f'<article class="card" data-reveal>\n'
                f'  <span class="card-num">{global_idx}</span>\n'
                f'  <div class="card-top">\n'
                f'    <h3 class="card-title">{title}</h3>\n'
                f'    <span class="card-source {sc}">{source_short}</span>\n'
                f'  </div>\n'
                f'  <p class="card-summary">{summary}</p>\n'
                f'  <div class="card-footer">\n'
                f'    <span class="card-time">{time_str}</span>\n'
                f'    <a class="card-link" href="{url_attr}" target="_blank" rel="noopener noreferrer">\n'
                f'      阅读原文\n'
                f'      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>\n'
                f'    </a>\n'
                f'  </div>\n'
                f'</article>\n'
            )
            cards_parts[cat].append(card)

    # ── Build sections HTML ──
    sections_html = ""
    for cat in CATEGORY_ORDER:
        label = CATEGORY_LABELS[cat]
        color = CATEGORY_COLORS[cat]
        count = cat_counts[cat]
        sections_html += (
            f'<section class="section" id="sec-{cat}">\n'
            f'  <div class="section-header">\n'
            f'    <div class="section-dot" style="background:{color}"></div>\n'
            f'    <h2>{label}</h2>\n'
            f'    <span class="section-count">{count} 条</span>\n'
            f'  </div>\n'
        )
        if count == 0:
            icon = EMPTY_ICONS.get(cat, "📌")
            sections_html += (
                f'  <div class="section-empty">\n'
                f'    <div class="section-empty-icon">{icon}</div>\n'
                f'    <p>今日无{label}相关资讯</p>\n'
                f'  </div>\n'
            )
        else:
            sections_html += '  <div class="card-grid">\n'
            for card in cards_parts[cat]:
                sections_html += card
            sections_html += '  </div>\n'
        sections_html += '</section>\n'

    # ── Build nav items ──
    nav_items = ""
    for cat in CATEGORY_ORDER:
        lbl = CATEGORY_LABELS[cat]
        cnt = cat_counts[cat]
        nav_items += (
            f'    <a href="#sec-{cat}" class="nav-link">\n'
            f'      <span class="nav-dot" style="background:{CATEGORY_COLORS[cat]}"></span>{lbl}\n'
            f'      <span class="nav-cnt">{cnt}</span>\n'
            f'    </a>\n'
        )

    # ── CSS (as a regular string, not f-string) ──
    css = """\
    :root {
      --hero-from: #ff5e3a;
      --hero-mid: #f73b4a;
      --hero-to: #c0392b;
      --accent: #ff6b35;
      --accent-dark: #e0552b;
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
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    .hero {
      position: relative; overflow: hidden;
      background: linear-gradient(135deg, var(--hero-from) 0%, var(--hero-mid) 40%, var(--hero-to) 100%);
      color: #fff; padding: 56px 24px 48px; text-align: center;
    }
    .hero::before {
      content: ''; position: absolute; inset: 0;
      background: radial-gradient(ellipse at 70% 30%, rgba(255,255,255,.15) 0%, transparent 60%),
                  radial-gradient(ellipse at 20% 80%, rgba(255,200,120,.12) 0%, transparent 50%);
    }
    .hero-content { position: relative; z-index: 1; max-width: 720px; margin: 0 auto; }
    .hero-badge {
      display: inline-block; background: rgba(255,255,255,.2);
      backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,.25); border-radius: 100px;
      padding: 4px 16px; font-size: 13px; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 16px;
    }
    .hero h1 { font-size: clamp(28px,5vw,44px); font-weight: 800; letter-spacing: -0.5px; margin-bottom: 8px; }
    .hero-sub { font-size: 16px; opacity: 0.85; margin-bottom: 24px; }
    .hero-stats { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }
    .hero-stat {
      display: flex; flex-direction: column; align-items: center;
      background: rgba(255,255,255,.15); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
      border-radius: 12px; padding: 12px 20px; min-width: 80px;
    }
    .hero-stat-num { font-size: 28px; font-weight: 800; line-height: 1.2; }
    .hero-stat-lbl { font-size: 12px; opacity: 0.8; margin-top: 2px; }
    .nav-wrap {
      position: sticky; top: 0; z-index: 100;
      background: rgba(255,255,255,.92); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border); padding: 0 16px;
    }
    .nav-inner { max-width: 1100px; margin: 0 auto; display: flex; gap: 4px; overflow-x: auto; padding: 10px 0; scrollbar-width: none; }
    .nav-inner::-webkit-scrollbar { display: none; }
    .nav-link {
      flex-shrink: 0; display: flex; align-items: center; gap: 6px;
      padding: 8px 16px; border-radius: 100px; font-size: 13.5px; font-weight: 600;
      color: var(--text-secondary); text-decoration: none; transition: 0.3s; white-space: nowrap; border: 1px solid transparent;
    }
    .nav-link:hover { background: #f5f0eb; color: var(--accent-dark); }
    .nav-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .nav-cnt { font-size: 11px; opacity: 0.6; }
    .main { max-width: 1100px; margin: 0 auto; padding: 32px 16px 48px; }
    .section { margin-bottom: 48px; scroll-margin-top: 72px; }
    .section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--card-border); }
    .section-dot { width: 14px; height: 14px; border-radius: 4px; flex-shrink: 0; transform: rotate(45deg); }
    .section h2 { font-size: 20px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; }
    .section-count { font-size: 14px; color: var(--text-muted); margin-left: auto; }
    .section-empty { text-align: center; padding: 32px 16px; color: var(--text-muted); background: var(--card-bg); border-radius: 16px; border: 1px dashed var(--card-border); }
    .section-empty-icon { font-size: 32px; margin-bottom: 8px; }
    .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px,1fr)); gap: 16px; }
    .card {
      position: relative; background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 16px; padding: 20px 20px 16px;
      transition: 0.3s; box-shadow: 0 1px 3px rgba(0,0,0,.06);
      display: flex; flex-direction: column; opacity: 0; transform: translateY(24px);
    }
    .card.revealed { opacity: 1; transform: translateY(0); }
    .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.07); transform: translateY(-2px); }
    .card.revealed:hover { transform: translateY(-2px); }
    .card-num {
      position: absolute; top: -10px; left: 16px; background: var(--accent); color: #fff;
      font-size: 11px; font-weight: 700; width: 24px; height: 24px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 2px 6px rgba(255,107,53,.35);
    }
    .card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; margin-bottom: 10px; margin-top: 6px; }
    .card-title { font-size: 15px; font-weight: 700; line-height: 1.5; color: var(--text); flex: 1; }
    .card-source { flex-shrink: 0; font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 100px; white-space: nowrap; }
    .source-x { background: #f0f0f0; color: #555; }
    .source-blog { background: #e8f4fd; color: #1a73e8; }
    .source-wechat { background: #e8f8e8; color: #2e7d32; }
    .source-media { background: #fff3e0; color: #e65100; }
    .source-hn { background: #fce4ec; color: #c62828; }
    .source-gh { background: #f3e5f5; color: #6a1b9a; }
    .card-summary { font-size: 13px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 14px; flex: 1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
    .card-footer { display: flex; align-items: center; justify-content: space-between; margin-top: auto; }
    .card-time { font-size: 12px; color: var(--text-muted); }
    .card-link {
      display: inline-flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 600;
      color: var(--accent); text-decoration: none; padding: 6px 14px; border-radius: 100px;
      background: rgba(255,107,53,.08); transition: 0.3s;
    }
    .card-link:hover { background: rgba(255,107,53,.16); color: var(--accent-dark); }
    .card-link svg { width: 14px; height: 14px; }
    .footer { text-align: center; padding: 32px 16px 40px; border-top: 1px solid var(--card-border); color: var(--text-muted); font-size: 13px; max-width: 1100px; margin: 0 auto; }
    .footer strong { color: var(--text-secondary); }
    .footer a { color: var(--accent); text-decoration: none; }
    .footer a:hover { text-decoration: underline; }
    .quick-top {
      position: fixed; bottom: 24px; right: 24px; width: 44px; height: 44px; border-radius: 50%;
      background: var(--accent); color: #fff; border: none; cursor: pointer; font-size: 20px;
      box-shadow: 0 12px 32px rgba(0,0,0,.1); opacity: 0; transform: translateY(12px);
      pointer-events: none; transition: 0.3s; z-index: 200;
      display: flex; align-items: center; justify-content: center;
    }
    .quick-top.visible { opacity: 1; transform: translateY(0); pointer-events: auto; }
    .quick-top:hover { background: var(--accent-dark); }
    @media (max-width: 600px) {
      .hero { padding: 40px 16px 36px; }
      .hero-stats { gap: 12px; }
      .hero-stat { padding: 10px 14px; min-width: 64px; }
      .hero-stat-num { font-size: 22px; }
      .card-grid { grid-template-columns: 1fr; }
      .section h2 { font-size: 17px; }
      .nav-link { padding: 6px 12px; font-size: 12px; }
    }"""

    # ── JS ──
    js = """\
    (function(){
      var observer = new IntersectionObserver(function(entries){
        entries.forEach(function(entry){
          if(entry.isIntersecting){ entry.target.classList.add('revealed'); observer.unobserve(entry.target); }
        });
      },{threshold:0.12,rootMargin:'0px 0px -20px 0px'});
      document.querySelectorAll('[data-reveal]').forEach(function(el){ observer.observe(el); });

      var qt = document.getElementById('quickTop'), ticking=false;
      function onScroll(){ if(!ticking){ requestAnimationFrame(function(){ qt.classList.toggle('visible',window.scrollY>400); ticking=false; }); ticking=true; } }
      window.addEventListener('scroll',onScroll,{passive:true});
      qt.addEventListener('click',function(){ window.scrollTo({top:0,behavior:'smooth'}); });

      document.querySelectorAll('.nav-link').forEach(function(link){
        link.addEventListener('click',function(e){ e.preventDefault(); var t=document.querySelector(this.getAttribute('href')); if(t) t.scrollIntoView({behavior:'smooth',block:'start'}); });
      });

      var sections=[],navLinks=document.querySelectorAll('.nav-link');
      document.querySelectorAll('.section').forEach(function(s){ sections.push({id:s.id,el:s}); });
      function highlightNav(){ requestAnimationFrame(function(){ var y=window.scrollY+120,cur=sections[0]&&sections[0].id; for(var i=sections.length-1;i>=0;i--) if(sections[i].el.offsetTop<=y){cur=sections[i].id;break;} navLinks.forEach(function(l){ var a=l.getAttribute('href')==='#'+cur; l.style.color=a?'var(--accent)':''; l.style.background=a?'rgba(255,107,53,.08)':''; }); }); }
      window.addEventListener('scroll',highlightNav,{passive:true});
    })();"""

    # ── Assemble full HTML ──
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI HOT 晨报 — {display_date}</title>
<style>
{css}
</style>
</head>
<body>

<header class="hero">
  <div class="hero-content">
    <div class="hero-badge">☀️ AI HOT 晨报</div>
    <h1>{display_date}</h1>
    <p class="hero-sub">共 {total} 条资讯</p>
    <div class="hero-stats">
      <div class="hero-stat">
        <span class="hero-stat-num">{total}</span>
        <span class="hero-stat-lbl">今日总条数</span>
      </div>
    </div>
  </div>
</header>

<nav class="nav-wrap" id="nav">
  <div class="nav-inner">
{nav_items}
  </div>
</nav>

<main class="main" id="main">
{sections_html}
</main>

<footer class="footer">
  <p>共 <strong>{total}</strong> 条资讯 · 数据来源：<a href="https://aihot.virxact.com" target="_blank" rel="noopener noreferrer">AI HOT</a></p>
</footer>

<button class="quick-top" id="quickTop" title="回到顶部">↑</button>

<script>{js}</script>

</body>
</html>"""

    return html


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    data, actual_date = fetch_daily(target_date)

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    html = generate_html(data, actual_date)

    INDEX_FILE.write_text(html, encoding="utf-8")
    print(f"[INFO] Written daily_news.html ({len(html)} bytes)")

    archive_file = ARCHIVE_DIR / f"{actual_date}.html"
    archive_file.write_text(html, encoding="utf-8")
    print(f"[INFO] Archived to {archive_file}")

    import subprocess
    cwd = str(OUTPUT_DIR)
    subprocess.run(["git", "add", "daily_news.html", f"news-archive/{actual_date}.html"], cwd=cwd, check=False)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd, capture_output=True)
    if result.returncode != 0:
        msg = f"chore: update daily dashboard {actual_date}"
        subprocess.run(["git", "commit", "-m", msg], cwd=cwd, check=False)
        push_result = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
        if push_result.returncode == 0:
            print(f"[INFO] Committed and pushed: {msg}")
        else:
            print(f"[WARN] Commit done, but push failed: {push_result.stderr}")
            print("[WARN] Run 'git push' manually.")
    else:
        print("[INFO] No changes to commit")


if __name__ == "__main__":
    main()
