"""
HTML/CSS/JS templates for ai-daily generators.

This module keeps the large template strings out of generator scripts
so the generator logic stays readable.
"""

from datetime import datetime


WEEKDAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


PAPERS_CSS = """\
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


PAPERS_SEARCH_SVG = (
    '<svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"'
    ' fill="currentColor" viewBox="0 0 16 16">'
    '<path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.099zm-5.242 1.656a5.5 5.5 0 1 1 0-11 5.5 5.5 0 0 1 0 11z"/>'
    '</svg>'
)


PAPERS_EXT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor">'
    '<path d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>'
    '<path d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>'
    '</svg>'
)


PAPERS_JS_TEMPLATE = """\
(function(){
  var WEEKDAYS = ['星期日','星期一','星期二','星期三','星期四','星期五','星期六'];

  function relativeTime(isoStr){
    var now = Date.now();
    var t = new Date(isoStr).getTime();
    var diff = Math.floor((now - t) / 1000);
    if(diff < 60) return '刚刚';
    if(diff < 3600) return Math.floor(diff/60) + ' 分钟前';
    if(diff < 86400) return Math.floor(diff/3600) + ' 小时前';
    if(diff < 604800) return Math.floor(diff/86400) + ' 天前';
    return new Date(isoStr).toLocaleDateString('zh-CN',{month:'numeric',day:'numeric'});
  }

  function escHtml(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function escAttr(s){ return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;'); }

  function buildTimeline(){
    var list = document.getElementById('timelineList');
    if(!list) return;
    list.innerHTML = '';
    window.TIMELINE_DATA.forEach(function(g){
      var li = document.createElement('li');
      li.className = 'timeline-item';
      li.dataset.date = g.date;
      li.innerHTML = '<div class="timeline-date">' + g.date.slice(5) + '</div>'
        + '<div class="timeline-count">' + g.wd + ' · ' + g.count + ' 篇</div>';
      li.addEventListener('click', function(){
        var el = document.getElementById('anchor-' + g.date);
        if(el) el.scrollIntoView({behavior:'smooth', block:'start'});
      });
      list.appendChild(li);
    });
  }

  function buildCards(filtered){
    var section = document.getElementById('papersSection');
    if(!section) return;
    section.innerHTML = '';

    var groups = {};
    filtered.forEach(function(p){
      if(!groups[p.dateStr]) groups[p.dateStr] = [];
      groups[p.dateStr].push(p);
    });
    var sortedDates = Object.keys(groups).sort(function(a,b){ return b.localeCompare(a); });

    var timelineGroups = sortedDates.map(function(d){
      return {date:d, wd:WEEKDAYS[new Date(d+'T00:00:00+08:00').getDay()], count:groups[d].length};
    });
    window.TIMELINE_DATA = timelineGroups;
    buildTimeline();

    sortedDates.forEach(function(date){
      var grp = groups[date];
      var d = new Date(date + 'T00:00:00+08:00');
      var wd = WEEKDAYS[d.getDay()];
      var groupEl = document.createElement('div');
      groupEl.className = 'date-group';
      var anchor = document.createElement('div');
      anchor.className = 'date-anchor';
      anchor.id = 'anchor-' + date;
      groupEl.appendChild(anchor);
      var header = document.createElement('div');
      header.className = 'date-header';
      header.innerHTML = '<span class="date-pill">' + date + '</span>'
        + '<span class="date-weekday">' + wd + '</span>'
        + '<span class="date-count">' + grp.length + ' 篇</span>';
      groupEl.appendChild(header);
      var stack = document.createElement('div');
      stack.className = 'papers-stack';

      grp.forEach(function(p){
        var card = document.createElement('div');
        card.className = 'paper-card' + (p.selected ? ' selected-card' : '');
        card.dataset.id = p.idx;
        var shtml = '';
        if(p.summary && p.summary !== '暂无摘要'){
          shtml = '<div class="card-summary">' + escHtml(p.summary) + '</div>';
        }
        card.innerHTML =
          '<div class="card-header">' +
            '<div class="card-num">' + p.idx + '</div>' +
            '<div class="card-title-wrap">' +
              '<a class="card-title" href="' + escAttr(p.url) + '" target="_blank" rel="noopener">' + escHtml(p.title) + '</a>' +
              '<div class="card-meta">' +
                '<span class="badge" style="background:' + escAttr(p.badgeBg) + ';color:' + escAttr(p.badgeColor) + '" title="' + escAttr(p.source) + '">' + escHtml(p.badgeLabel) + '</span>' +
                '<span class="rel-time">' + relativeTime(p.publishedAt) + '</span>' +
                '<span class="score-dot"><span class="score-star">\\u2605</span>' + p.score + '</span>' +
              '</div>' +
            '</div>' +
          '</div>' +
          shtml +
          '<div class="card-footer">' +
            '<a class="read-link" href="' + escAttr(p.url) + '" target="_blank" rel="noopener">' +
              '__PAPERS_EXT_SVG__' + ' 阅读原文</a>' +
          '</div>';
        stack.appendChild(card);
      });
      groupEl.appendChild(stack);
      section.appendChild(groupEl);
    });

    document.getElementById('filtered-count').textContent = filtered.length;

    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(e.isIntersecting){ e.target.classList.add('visible'); observer.unobserve(e.target); }
      });
    }, {threshold:0.08, rootMargin:'0px 0px -40px 0px'});
    document.querySelectorAll('.paper-card').forEach(function(el){ observer.observe(el); });

    highlightTimeline();
  }

  function highlightTimeline(){
    var groups = document.querySelectorAll('.date-group');
    var tItems = document.querySelectorAll('.timeline-item');
    var scrollY = window.scrollY + 160;
    var activeDate = null;
    groups.forEach(function(g){
      var anchor = g.querySelector('.date-anchor');
      if(anchor && anchor.getBoundingClientRect().top + window.scrollY <= scrollY){
        activeDate = g.querySelector('.date-anchor').id.replace('anchor-','');
      }
    });
    tItems.forEach(function(item){
      item.classList.toggle('active', item.dataset.date === activeDate);
    });
  }

  window.addEventListener('scroll', highlightTimeline, {passive:true});

  var searchInput = document.getElementById('searchInput');
  var searchCount = document.getElementById('searchCount');
  var debounceTimer;
  if(searchInput){
    searchInput.addEventListener('input', function(){
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function(){
        var q = searchInput.value.trim().toLowerCase();
        var filtered;
        if(!q){ filtered = window.PAPERS; }
        else { filtered = window.PAPERS.filter(function(p){
          return (p.title && p.title.toLowerCase().indexOf(q)!==-1)
              || (p.summary && p.summary.toLowerCase().indexOf(q)!==-1)
              || (p.source && p.source.toLowerCase().indexOf(q)!==-1)
              || (p.badgeLabel && p.badgeLabel.toLowerCase().indexOf(q)!==-1);
        }); }
        searchCount.textContent = filtered.length + ' 篇';
        buildCards(filtered);
      }, 250);
    });
  }

  buildCards(window.PAPERS);
  buildTimeline();

  /* ---- back to top ---- */
  var qtop = document.getElementById('quickTop');
  window.addEventListener('scroll', function(){
    qtop.classList.toggle('visible', window.scrollY > 400);
  });
})();
"""


PAPERS_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 学术档案库 · 近日论文精选</title>
<style>
__PAPERS_CSS__
</style>
</head>
<body>

<header class="header">
  <div class="header-inner">
    <div class="header-badge">📄 AI 学术档案库</div>
    <h1 class="header-title">近日 AI 论文精选</h1>
    <p class="header-sub">数据来源 AI HOT · 过去 7 天精选 __PAPERS_TOTAL__ 篇</p>
    <div class="header-stats">
      <div class="stat-card">
        <span class="stat-num" id="total-count">__PAPERS_TOTAL__</span>
        <span class="stat-label">论文总数</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">__PAPERS_NUM_DATES__</span>
        <span class="stat-label">覆盖天数</span>
      </div>
      <div class="stat-card">
        <span class="stat-num" id="filtered-count">__PAPERS_TOTAL__</span>
        <span class="stat-label">当前显示</span>
      </div>
    </div>
  </div>
</header>

<main class="main">
  <div class="search-bar">
    __PAPERS_SEARCH_SVG__
    <input class="search-input" id="searchInput" type="text"
     placeholder="搜索论文标题、摘要或来源…" autocomplete="off">
    <span class="search-count" id="searchCount">__PAPERS_TOTAL__ 篇</span>
  </div>

  <nav class="timeline">
    <div class="timeline-title">时间轴</div>
    <ul class="timeline-list" id="timelineList"></ul>
  </nav>

  <section class="papers-section" id="papersSection">
__PAPERS_DATE_GROUPS_HTML__
  </section>
</main>

<footer class="footer">
  数据来源：<a href="https://aihot.virxact.com" target="_blank" rel="noopener">AI HOT</a> · 精选论文 · 仅供学术参考
</footer>

<script>
window.PAPERS = __PAPERS_DATA_JSON__;
window.TIMELINE_DATA = __PAPERS_TIMELINE_JSON__;
</script>

<script>
__PAPERS_JS__
</script>

<div class="quick-top" id="quickTop" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</div>

</body>
</html>
"""


def _build_paper_date_groups(groups, sorted_dates):
    """Build the initial date-group HTML shells (cards are rendered by JS)."""
    paper_date_groups_html = ""
    for d in sorted_dates:
        try:
            wd = WEEKDAY_NAMES[datetime.strptime(d, "%Y-%m-%d").weekday()]
        except Exception:
            wd = ""
        paper_date_groups_html += (
            '  <div class="date-group">\n'
            '    <div class="date-anchor" id="anchor-' + d + '"></div>\n'
            '    <div class="date-header">\n'
            '      <span class="date-pill">' + d + '</span>\n'
            '      <span class="date-weekday">' + wd + '</span>\n'
            '      <span class="date-count">' + str(len(groups[d])) + ' 篇</span>\n'
            '    </div>\n'
            '    <div class="papers-stack" id="stack-' + d + '"></div>\n'
            '  </div>\n'
        )
    return paper_date_groups_html


def _render_papers_js():
    """Return the papers JS block with the external-link SVG injected."""
    escaped_svg = PAPERS_EXT_SVG.replace('"', '\\"')
    return PAPERS_JS_TEMPLATE.replace("__PAPERS_EXT_SVG__", escaped_svg)


def render_papers_html(total, num_dates, papers_json, timeline_json, groups, sorted_dates):
    """Render the complete papers HTML page."""
    paper_date_groups_html = _build_paper_date_groups(groups, sorted_dates)
    papers_js = _render_papers_js()

    papers_html = PAPERS_PAGE_TEMPLATE
    papers_html = papers_html.replace("__PAPERS_CSS__", PAPERS_CSS)
    papers_html = papers_html.replace("__PAPERS_SEARCH_SVG__", PAPERS_SEARCH_SVG)
    papers_html = papers_html.replace("__PAPERS_DATE_GROUPS_HTML__", paper_date_groups_html)
    papers_html = papers_html.replace("__PAPERS_JS__", papers_js)
    papers_html = papers_html.replace("__PAPERS_TOTAL__", str(total))
    papers_html = papers_html.replace("__PAPERS_NUM_DATES__", str(num_dates))
    papers_html = papers_html.replace("__PAPERS_DATA_JSON__", papers_json)
    papers_html = papers_html.replace("__PAPERS_TIMELINE_JSON__", timeline_json)

    # Final cleanup: remove any remaining surrogate characters
    return papers_html.encode("utf-8", errors="replace").decode("utf-8")


# ═══════════════════════════════════════════════════════════════
# Trending templates
# ═══════════════════════════════════════════════════════════════

TRENDING_CSS = """    :root {
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
    .score-badge {
      font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 100px;
    }
    .score-high { background: #e8f8e8; color: #2e7d32; }
    .score-mid { background: #fff3e0; color: #e65100; }
    .score-low { background: #fce4ec; color: #c62828; }
    .card-footer { display: flex; align-items: center; gap: 12px; margin-top: auto; flex-wrap: wrap; }
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

TRENDING_JS = """    // 滚动揭示动画
    const cards = document.querySelectorAll('[data-reveal]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add('revealed'), i * 60);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    cards.forEach(c => observer.observe(c));

    // 回到顶部
    const quickTop = document.getElementById('quickTop');
    window.addEventListener('scroll', () => {
      quickTop.classList.toggle('visible', window.scrollY > 400);
    });
    quickTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // 导航高亮
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-link');
    window.addEventListener('scroll', () => {
      let current = '';
      sections.forEach(sec => {
        if (window.scrollY >= sec.offsetTop - 100) {
          current = sec.id;
        }
      });
      navLinks.forEach(a => {
        const isActive = a.getAttribute('href') === '#' + current;
        a.style.background = isActive ? 'rgba(255,107,53,.1)' : '';
        a.style.color = isActive ? 'var(--accent-dark)' : '';
      });
    });"""

TRENDING_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>当日热点 — __TRENDING_DATE_STR__</title>
<style>
__TRENDING_CSS__
</style>
</head>
<body>

<header class="hero">
  <div class="hero-content">
    <div class="hero-badge">🔥 当日热点</div>
    <h1>__TRENDING_TOTAL__ 条热点资讯</h1>
    <p class="hero-sub">全网热点雷达 · 关键词过滤 · 智能聚合</p>
    <div class="hero-stats">
      <div class="hero-stat">
        <span class="hero-stat-num">__TRENDING_TOTAL__</span>
        <span class="hero-stat-lbl">命中条数</span>
      </div>
      <div class="hero-stat">
        <span class="hero-stat-num">__TRENDING_GROUP_COUNT__</span>
        <span class="hero-stat-lbl">分组数</span>
      </div>
      <div class="hero-stat">
        <span class="hero-stat-num">__TRENDING_WEEKDAY__</span>
        <span class="hero-stat-lbl">__TRENDING_DISPLAY_DATE__</span>
      </div>
    </div>
  </div>
</header>

<nav class="nav-wrap" id="nav">
  <div class="nav-inner">
__TRENDING_NAV_LINKS__
  </div>
</nav>

<main class="main" id="main">
__TRENDING_SECTIONS__
</main>

<footer class="footer">
  <p>数据来源 <strong>NewsNow</strong> · 最后生成 <time>__TRENDING_DISPLAY_DATE__</time> · <a href="../index.html">返回首页</a></p>
</footer>

<button class="quick-top" id="quickTop" aria-label="回到顶部">↑</button>

<script>
__TRENDING_JS__
</script>

</body>
</html>"""

TRENDING_CARD_TEMPLATE = """        <article class="card" data-reveal>
          <span class="card-num">{idx}</span>
          <div class="card-top">
            <h3 class="card-title">{title}</h3>
            <span class="card-source {source_class}">{source_name}</span>
          </div>
          <div class="card-footer">
            <span class="card-time">{time_str}</span>
            {score_badge}
            <a class="card-link" href="{url}" target="_blank" rel="noopener noreferrer">
              阅读原文
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
            </a>
          </div>
        </article>"""

TRENDING_SECTION_TEMPLATE = """    <section class="section" id="sec-{anchor}">
      <div class="section-header">
        <div class="section-dot" style="background:{color}"></div>
        <h2>{group_name}</h2>
        <span class="section-count">{count} 条</span>
      </div>
      <div class="card-grid">
{cards_html}
      </div>
    </section>"""


def render_trending_html(total, group_count, display_date, weekday, nav_links, sections_html):
    """Render the complete trending HTML page."""
    date_str = f"{display_date} · {weekday}"
    html = TRENDING_PAGE_TEMPLATE
    html = html.replace("__TRENDING_CSS__", TRENDING_CSS)
    html = html.replace("__TRENDING_TOTAL__", str(total))
    html = html.replace("__TRENDING_GROUP_COUNT__", str(group_count))
    html = html.replace("__TRENDING_WEEKDAY__", weekday)
    html = html.replace("__TRENDING_DISPLAY_DATE__", display_date)
    html = html.replace("__TRENDING_DATE_STR__", date_str)
    html = html.replace("__TRENDING_NAV_LINKS__", nav_links)
    html = html.replace("__TRENDING_SECTIONS__", sections_html)
    html = html.replace("__TRENDING_JS__", TRENDING_JS)
    return html.encode("utf-8", errors="replace").decode("utf-8")


# ═══════════════════════════════════════════════════════════════
# News templates
# ═══════════════════════════════════════════════════════════════

NEWS_CSS = """    :root {
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

NEWS_JS = """    (function(){
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

NEWS_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI HOT 晨报 — __NEWS_DISPLAY_DATE__</title>
<style>
__NEWS_CSS__
</style>
</head>
<body>

<header class="hero">
  <div class="hero-content">
    <div class="hero-badge">☀️ AI HOT 晨报</div>
    <h1>__NEWS_DISPLAY_DATE__</h1>
    <p class="hero-sub">共 __NEWS_TOTAL__ 条资讯</p>
    <div class="hero-stats">
      <div class="hero-stat">
        <span class="hero-stat-num">__NEWS_TOTAL__</span>
        <span class="hero-stat-lbl">今日总条数</span>
      </div>
    </div>
  </div>
</header>

<nav class="nav-wrap" id="nav">
  <div class="nav-inner">
__NEWS_NAV_ITEMS__
  </div>
</nav>

<main class="main" id="main">
__NEWS_SECTIONS__
</main>

<footer class="footer">
  <p>共 <strong>__NEWS_TOTAL__</strong> 条资讯 · 数据来源：<a href="https://aihot.virxact.com" target="_blank" rel="noopener noreferrer">AI HOT</a></p>
</footer>

<button class="quick-top" id="quickTop" title="回到顶部">↑</button>

<script>__NEWS_JS__</script>

</body>
</html>"""

NEWS_CARD_TEMPLATE = """<article class="card" data-reveal>
  <span class="card-num">{idx}</span>
  <div class="card-top">
    <h3 class="card-title">{title}</h3>
    <span class="card-source {source_class}">{source_short}</span>
  </div>
  <p class="card-summary">{summary}</p>
  <div class="card-footer">
    <span class="card-time">{time_str}</span>
    <a class="card-link" href="{url}" target="_blank" rel="noopener noreferrer">
      阅读原文
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
    </a>
  </div>
</article>
"""

NEWS_SECTION_TEMPLATE = """<section class="section" id="sec-{cat}">
  <div class="section-header">
    <div class="section-dot" style="background:{color}"></div>
    <h2>{label}</h2>
    <span class="section-count">{count} 条</span>
  </div>
  <div class="card-grid">
{cards_html}
  </div>
</section>
"""

NEWS_EMPTY_SECTION_TEMPLATE = """<section class="section" id="sec-{cat}">
  <div class="section-header">
    <div class="section-dot" style="background:{color}"></div>
    <h2>{label}</h2>
    <span class="section-count">0 条</span>
  </div>
  <div class="section-empty">
    <div class="section-empty-icon">{icon}</div>
    <p>今日无{label}相关资讯</p>
  </div>
</section>
"""


def render_news_html(display_date, total, nav_items, sections_html):
    """Render the complete news HTML page."""
    html = NEWS_PAGE_TEMPLATE
    html = html.replace("__NEWS_CSS__", NEWS_CSS)
    html = html.replace("__NEWS_DISPLAY_DATE__", display_date)
    html = html.replace("__NEWS_TOTAL__", str(total))
    html = html.replace("__NEWS_NAV_ITEMS__", nav_items)
    html = html.replace("__NEWS_SECTIONS__", sections_html)
    html = html.replace("__NEWS_JS__", NEWS_JS)
    return html.encode("utf-8", errors="replace").decode("utf-8")


# ═══════════════════════════════════════════════════════════════
# WeChat templates (inline-styled, no <style>/<script> tags)
# ═══════════════════════════════════════════════════════════════



WECHAT_HEAD_SECTION = """\
<section style="padding:12px 15px 0;text-align:center">
  <p style="color:#6b7280;font-size:13px;margin:0 0 6px;letter-spacing:2px">📰 每日 AI 情报</p>
  <p style="color:#111827;font-size:24px;font-weight:800;margin:0;letter-spacing:-0.5px">{display_date}</p>
</section>
<section style="margin:16px 15px 12px;height:1px;background:#e5e7eb"></section>"""

WECHAT_NEWS_HEADER = """\
<section style="padding:4px 15px">
  <h2 style="font-size:16px;color:#111827;margin:14px 0 10px;font-weight:700;line-height:1.4">
    <span style="display:inline-block;width:4px;height:16px;background:#10b981;vertical-align:middle;margin-right:8px;border-radius:2px"></span>🔥 AI 热点资讯（{count}条）
  </h2>
</section>"""

WECHAT_ITEM_TEMPLATE = """\
{{link_open}}<section class="ai-card" style="margin:0 15px 10px;padding:12px 14px 10px;background:{bg_color};border-radius:8px;border-left:3px solid {accent_color};transition:transform .2s ease,box-shadow .2s ease,border-left-width .2s ease">
  <p style="margin:0;line-height:1.45;text-align:left">
    <strong style="color:{accent_color};font-size:14px;font-weight:700">{num}.</strong><strong style="color:#111827;font-size:15px;font-weight:700">{title}</strong>
  </p>
  <p style="margin:4px 0 6px;font-size:13px;color:#4b5563;line-height:1.65;text-align:justify;text-justify:inter-ideograph">{summary}</p>
  <p style="margin:0;font-size:11px;color:#9ca3af;line-height:1.5">{{section_badge}}<span style="margin-left:8px">来源：{source}</span></p>
</section>{{link_close}}"""

WECHAT_PAPERS_HEADER = """\
<section style="padding:4px 15px">
  <h2 style="font-size:16px;color:#111827;margin:18px 0 10px;font-weight:700;line-height:1.4">
    <span style="display:inline-block;width:4px;height:16px;background:#ec4899;vertical-align:middle;margin-right:8px;border-radius:2px"></span>📄 AI 论文精选（{count}篇）
  </h2>
</section>"""

WECHAT_PAPER_TEMPLATE = """\
{{link_open}}<section class="ai-card" style="margin:0 15px 10px;padding:12px 14px 10px;background:{bg_color};border-radius:8px;border-left:3px solid {accent_color};transition:transform .2s ease,box-shadow .2s ease,border-left-width .2s ease">
  <p style="margin:0;line-height:1.45;text-align:left">
    <strong style="color:{accent_color};font-size:14px;font-weight:700">{num}.</strong><strong style="color:#111827;font-size:15px;font-weight:700">{title}</strong>
  </p>
  <p style="margin:4px 0 6px;font-size:13px;color:#4b5563;line-height:1.65;text-align:justify;text-justify:inter-ideograph">{summary}</p>
  <p style="margin:0;font-size:11px;color:#9ca3af;line-height:1.5">{{source_badge}}</p>
</section>{{link_close}}"""

# ── 4-color pastel palette for alternating card styles ──
# Each entry: (accent, background)
WECHAT_COLOR_PALETTE = [
    ("#10b981", "#ecfdf5"),  # 薄荷绿
    ("#ec4899", "#fdf2f8"),  # 樱花粉
    ("#8b5cf6", "#f5f3ff"),  # 柔紫
    ("#3b82f6", "#eff6ff"),  # 天空蓝
]

WECHAT_FOOT_SECTION = """\
<section style="margin:20px 15px 16px;height:1px;background:#e5e7eb"></section>
<section style="padding:0 15px 30px">
  <p style="text-align:center;font-size:12px;color:#9ca3af;line-height:1.8">
    由 <a href="{repo_url}" style="color:#10b981;text-decoration:none">ai-daily</a> 自动生成 · 仅供学习参考
  </p>
</section>"""
