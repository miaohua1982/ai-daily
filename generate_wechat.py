#!/usr/bin/env python3
"""
WeChat Official Account Draft Publisher
- Checks if daily_news.html and papers.html exist (gate condition)
- Fetches content from aihot API and builds WeChat-compatible HTML
- Creates a draft on WeChat Official Account platform
- Uses env vars: WECHAT_APPID, WECHAT_APPSECRET
  
Scheduled after daily (05:00) and papers (06:00) — Beijing time.
"""

import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
AIHOT_BASE = "https://aihot.virxact.com/api/public"
WECHAT_BASE = "https://api.weixin.qq.com"
OUTPUT_DIR = Path(__file__).parent.resolve()

# Gate files — must both exist for the script to run
DAILY_FILE = OUTPUT_DIR / "daily_news.html"
PAPERS_FILE = OUTPUT_DIR / "papers.html"

# Env secrets (set in GitHub Actions)
APPID = os.environ.get("WECHAT_APPID", "").strip()
APPSECRET = os.environ.get("WECHAT_APPSECRET", "").strip()

MAX_NEWS = 10
MAX_PAPERS = 10

# ── Helpers ────────────────────────────────────────────────────

def api_get(path: str) -> dict | None:
    url = f"{AIHOT_BASE}{path}"
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


def wechat_get(path: str) -> dict | None:
    url = f"{WECHAT_BASE}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[WARN] WeChat API GET failed: {path} — {e}", file=sys.stderr)
        return None


def wechat_post(path: str, payload, content_type: str = "application/json"):
    url = f"{WECHAT_BASE}{path}"
    if isinstance(payload, dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    elif isinstance(payload, bytes):
        data = payload
    else:
        data = payload.encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"User-Agent": UA, "Content-Type": content_type}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"[WARN] WeChat POST {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] WeChat POST failed: {e}", file=sys.stderr)
        return None


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Content fetching ───────────────────────────────────────────

def fetch_news() -> list[dict]:
    """Fetch today's AI news via the daily endpoint."""
    bj = datetime.now(timezone(timedelta(hours=8)))
    if bj.hour < 5:
        bj = bj - timedelta(days=1)
    date_str = bj.strftime("%Y-%m-%d")

    data = api_get(f"/daily/{date_str}")
    if not data or "sections" not in data:
        print(f"[WARN] No daily report for {date_str}, trying fallback...")
        dailies = api_get("/dailies?take=3")
        if dailies and dailies.get("items"):
            latest = dailies["items"][0]["date"]
            data = api_get(f"/daily/{latest}")
            date_str = latest
        if not data:
            return []

    items: list[dict] = []
    for sec in data.get("sections", []):
        for it in sec.get("items", []):
            if not it.get("title"):
                continue
            it["_section"] = sec.get("label", "")
            items.append(it)

    # deduplicate by title prefix
    seen = set()
    deduped = []
    for it in items:
        key = it["title"].strip()[:40]
        if key not in seen:
            seen.add(key)
            deduped.append(it)
    return deduped[:MAX_NEWS]


def fetch_papers() -> list[dict]:
    """Fetch recent AI papers via the public items endpoint.

    Mirrors the proven pagination logic from generate_papers.py:
    uses "items" (not "data") as the JSON key, respects hasNext /
    nextCursor, and caps at remaining count.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    items: list[dict] = []
    cursor = ""
    remaining = 30

    for _ in range(3):
        url = f"/items?mode=all&category=paper&since={since}&take={min(remaining, 30)}"
        if cursor:
            url += f"&cursor={cursor}"
        data = api_get(url)
        if not data or "items" not in data:
            break
        batch = data.get("items", [])
        items.extend(batch)
        remaining -= len(batch)
        if not data.get("hasNext") or remaining <= 0:
            break
        cursor = data.get("nextCursor", "")
        if not cursor:
            break

    if not items:
        return []

    # Sort & deduplicate
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    seen = set()
    deduped = []
    for it in items:
        prefix = it.get("title", "").strip()[:40]
        if prefix and prefix not in seen:
            seen.add(prefix)
            deduped.append(it)
    deduped.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    return deduped[:MAX_PAPERS]


# ── WeChat HTML builder ────────────────────────────────────────

def build_wechat_html(
    news: list[dict], papers: list[dict], date_str: str, repo_url: str
) -> str:
    display = _format_date_cn(date_str)

    parts = [_HEAD_SECTION.format(display_date=display)]

    # ── AI News ──
    if news:
        parts.append(_SECTION_NEWS_HEADER.format(count=len(news)))
        for i, it in enumerate(news, 1):
            parts.append(_build_news_item(i, it))

    # ── AI Papers ──
    if papers:
        parts.append(_SECTION_PAPERS_HEADER.format(count=len(papers)))
        for i, it in enumerate(papers, 1):
            parts.append(_build_paper_item(i, it))

    parts.append(_FOOT_SECTION.format(repo_url=repo_url))
    return "\n".join(parts)


def _format_date_cn(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        wd = ["一", "二", "三", "四", "五", "六", "日"][d.weekday()]
        return f"{d.year}年{d.month}月{d.day}日 · 周{wd}"
    except Exception:
        return date_str


def _badge_html(label: str, color: str) -> str:
    return (
        f'<span style="display:inline-block;background:{color}15;'
        f'color:{color};padding:1px 8px;border-radius:2px;'
        f'font-size:11px;line-height:18px">{esc(label)}</span>'
    )


def _build_news_item(i: int, it: dict) -> str:
    title = esc(it.get("title", ""))
    summary = esc((it.get("summary") or it.get("description") or ""))
    source = esc(it.get("sourceName") or it.get("source") or "来源")
    section = esc(it.get("_section", ""))
    url = (it.get("sourceUrl") or it.get("url") or "").strip()
    # Ensure URL has a scheme — WeChat requires absolute URLs
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    html = _ITEM_TEMPLATE.format(
        num=i,
        title=title,
        summary=summary,
        source=source,
    )
    # Prepend section badge if available
    if section and section not in ("未分类", ""):
        badge = _badge_html(section, "#007AAA")
        html = html.replace("{section_badge}", badge)
    else:
        html = html.replace("{section_badge}", "")

    # Wrap in link if URL available
    if url:
        html = html.replace("{link_open}", f'<a href="{url}" style="text-decoration:none;color:inherit">')
        html = html.replace("{link_close}", "</a>")
    else:
        html = html.replace("{link_open}", "").replace("{link_close}", "")
    return html


def _build_paper_item(i: int, it: dict) -> str:
    title = esc(it.get("title", ""))
    summary = esc((it.get("summary") or it.get("description") or ""))
    source = esc(it.get("source") or "arXiv")
    url = (it.get("url") or "").strip()
    # Ensure URL has a scheme — WeChat requires absolute URLs
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    html = _PAPER_TEMPLATE.format(
        num=i, title=title, summary=summary, source=source
    )
    source_color = "#E05252" if "arxiv" in (source or "").lower() else "#007AAA"
    badge = _badge_html(source, source_color)
    html = html.replace("{source_badge}", badge)
    if url:
        html = html.replace("{link_open}", f'<a href="{url}" style="text-decoration:none;color:inherit">')
        html = html.replace("{link_close}", "</a>")
    else:
        html = html.replace("{link_open}", "").replace("{link_close}", "")
    return html


# ── HTML Templates (WeChat-compatible, inline styles only) ─────

_HEAD_SECTION = """\
<section style="padding:8px 15px 0">
  <p style="text-align:center;color:#888;font-size:14px;margin:10px 0 0;letter-spacing:1px">
    📰 每日 AI 情报
  </p>
  <p style="text-align:center;color:#333;font-size:22px;font-weight:bold;margin:6px 0 0">
    {display_date}
  </p>
</section>
<section style="margin:20px 15px 10px;height:1px;background:#eee"></section>"""

_SECTION_NEWS_HEADER = """\
<section style="padding:5px 15px">
  <h2 style="font-size:17px;color:#333;border-left:4px solid #ff6b35;padding-left:10px;margin:18px 0 12px">🔥 AI 热点资讯（{count}条）</h2>
</section>"""

_ITEM_TEMPLATE = """\
{{link_open}}<section style="margin:0 15px 12px;padding:12px 14px;background:#faf8f6;border-radius:4px">
  <p style="margin:0 0 6px;line-height:1.5;text-align:justify;text-justify:inter-ideograph">
    <strong style="color:#ff6b35;font-size:14px">{num}.</strong>
    <strong style="color:#222;font-size:14px">{title}</strong>
  </p>
  <p style="margin:0 0 8px;font-size:13px;color:#666;line-height:1.7;text-align:justify;text-justify:inter-ideograph;text-indent:2em">{summary}</p>
  <p style="margin:0;font-size:12px;color:#999;line-height:1.5">{{section_badge}} <span style="margin-left:6px">来源：{source}</span></p>
</section>{{link_close}}"""

_SECTION_PAPERS_HEADER = """\
<section style="padding:5px 15px">
  <h2 style="font-size:17px;color:#333;border-left:4px solid #E05252;padding-left:10px;margin:22px 0 12px">📄 AI 论文精选（{count}篇）</h2>
</section>"""

_PAPER_TEMPLATE = """\
{{link_open}}<section style="margin:0 15px 12px;padding:12px 14px;background:#faf8f6;border-radius:4px">
  <p style="margin:0 0 6px;line-height:1.5;text-align:justify;text-justify:inter-ideograph">
    <strong style="color:#E05252;font-size:14px">{num}.</strong>
    <strong style="color:#222;font-size:14px">{title}</strong>
  </p>
  <p style="margin:0 0 8px;font-size:13px;color:#666;line-height:1.7;text-align:justify;text-justify:inter-ideograph;text-indent:2em">{summary}</p>
  <p style="margin:0;font-size:12px;color:#999;line-height:1.5">{{source_badge}}</p>
</section>{{link_close}}"""

_FOOT_SECTION = """\
<section style="margin:25px 15px 20px;height:1px;background:#eee"></section>
<section style="padding:0 15px 30px">
  <p style="text-align:center;font-size:12px;color:#bbb;line-height:1.8">
    由 <a href="{repo_url}" style="color:#576b95;text-decoration:none">ai-daily</a> 自动生成 · 仅供学习参考
  </p>
</section>"""


# ── Cover image generation ─────────────────────────────────────

def generate_cover(today: str, news_count: int, papers_count: int) -> bytes:
    """Generate a simple cover image for the WeChat draft. Returns PNG bytes."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[WARN] Pillow not available, using fallback cover", file=sys.stderr)
        return _fallback_cover_bytes()

    w, h = 900, 410
    img = Image.new("RGB", (w, h), (255, 245, 235))
    draw = ImageDraw.Draw(img)

    # Warm gradient background
    for x in range(0, w):
        t = x / w
        r = int(255 - t * 15)
        g = int(245 - t * 20)
        b = int(235 - t * 20)
        draw.line([(x, 0), (x, h)], fill=(r, g, b))

    # Top orange stripe
    draw.rectangle([0, 0, w, 6], fill=(255, 107, 53))
    # Bottom orange stripe
    draw.rectangle([0, h - 6, w, h], fill=(255, 107, 53))

    try:
        font_title = _find_chinese_font(64)
        font_date = _find_chinese_font(28)
        font_label = _find_chinese_font(26)
        font_num = _find_chinese_font(80)
        font_unit = _find_chinese_font(24)
        font_foot = _find_chinese_font(20)
    except Exception:
        font_title = font_date = font_label = font_num = font_unit = font_foot = ImageFont.load_default()

    # ── Header ──
    draw.text((60, 48), "AI 情报日报", fill=(40, 40, 40), font=font_title)
    draw.text((60, 118), today, fill=(160, 130, 110), font=font_date)
    draw.line([(60, 158), (460, 158)], fill=(255, 180, 140), width=2)

    # ── Stats cards: left-right layout ──
    card_y = 195
    card_w = 370
    card_h = 140

    # ---- NEWS card ----
    nx1, ny1 = 60, card_y
    nx2, ny2 = nx1 + card_w, card_y + card_h
    draw.rounded_rectangle(
        [(nx1, ny1), (nx2, ny2)],
        radius=16, fill=(255, 235, 220), outline=(255, 190, 150), width=2
    )
    draw.text((nx1 + 30, ny1 + 18), "NEWS", fill=(200, 130, 100), font=font_label)
    draw.text((nx1 + 30, ny1 + 50), str(news_count), fill=(255, 107, 53), font=font_num)
    draw.text((nx1 + 120, ny1 + 90), "则", fill=(180, 130, 110), font=font_unit)

    # ---- PAPERS card ----
    px1, py1 = nx2 + 40, card_y
    px2, py2 = px1 + card_w, card_y + card_h
    draw.rounded_rectangle(
        [(px1, py1), (px2, py2)],
        radius=16, fill=(255, 228, 228), outline=(255, 175, 175), width=2
    )
    draw.text((px1 + 30, py1 + 18), "PAPERS", fill=(190, 110, 110), font=font_label)
    draw.text((px1 + 30, py1 + 50), str(papers_count), fill=(224, 82, 82), font=font_num)
    draw.text((px1 + 130, py1 + 90), "篇", fill=(170, 110, 100), font=font_unit)

    # ── Footer ──
    draw.text((60, 375), "由 ai-daily 自动生成 · 仅供学习参考", fill=(170, 150, 140), font=font_foot)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _find_chinese_font(size: int):
    from PIL import ImageFont
    candidates = [
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Ubuntu 24.04 — noto-cjk (opentype or truetype)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Medium.ttc",
        # Ubuntu older — noto-cjk package
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansMonoCJK-Regular.ttc",
        # WenQuanYi (lightweight fallback)
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        # DroidSans
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        # Generic Noto fallback
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    # Last resort: scan system with fc-list
    try:
        import subprocess
        out = subprocess.check_output(
            ["fc-list", ":lang=zh", "-f", "%{{file}}\\n"],
            timeout=3, text=True
        )
        for line in out.strip().split("\n"):
            line = line.strip()
            if line and Path(line).exists():
                return ImageFont.truetype(line, size)
    except Exception:
        pass
    return ImageFont.load_default()


def _fallback_cover_bytes() -> bytes:
    """Generate a minimal PNG without Pillow."""
    # 1x1 pixel placeholder — minimal valid PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf"
        b"\xc0\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


# ── WeChat API ─────────────────────────────────────────────────

def get_access_token() -> str | None:
    resp = wechat_get(
        f"/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    )
    if not resp or "access_token" not in resp:
        print("[ERROR] Failed to get WeChat access_token", file=sys.stderr)
        return None
    token = resp["access_token"]
    print(f"[INFO] Got access_token (expires in {resp.get('expires_in', '?')}s)")
    return token


def upload_image(token: str, image_bytes: bytes) -> str | None:
    """Upload image as permanent material. Returns media_id."""
    import uuid

    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

    url = f"{WECHAT_BASE}/cgi-bin/material/add_material?access_token={token}&type=image"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": UA,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if "media_id" in data:
            print(f"[INFO] Cover image uploaded — media_id: {data['media_id']}")
            return data["media_id"]
        print(f"[WARN] Image upload failed: {data}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] Image upload error: {e}", file=sys.stderr)
        return None


def create_draft(
    token: str,
    thumb_media_id: str,
    title: str,
    content: str,
    digest: str,
    source_url: str,
) -> bool:
    payload = {
        "articles": [
            {
                "title": title,
                "thumb_media_id": thumb_media_id,
                "author": "ai-daily",
                "digest": digest,
                "show_cover_pic": 1,
                "content": content,
                "content_source_url": source_url,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }
    resp = wechat_post(
        f"/cgi-bin/draft/add?access_token={token}", payload
    )
    if resp and "media_id" in resp:
        print(f"[INFO] Draft created — media_id: {resp['media_id']}")
        return True
    print(f"[ERROR] Draft creation failed: {resp}", file=sys.stderr)
    return False


# ── Main ───────────────────────────────────────────────────────

def main() -> int:
    # 1. Gate: must have credentials
    if not APPID or not APPSECRET:
        print("[SKIP] WECHAT_APPID or WECHAT_APPSECRET not set in environment")
        return 0

    # 2. Gate: both HTML files must exist (signals daily & papers ran successfully)
    missing = []
    if not DAILY_FILE.exists():
        missing.append("daily_news.html")
    if not PAPERS_FILE.exists():
        missing.append("papers.html")
    if missing:
        print(f"[SKIP] Missing gate files: {', '.join(missing)} — nothing to do")
        return 0

    print("[INFO] Gate files exist ✓ — proceeding to generate WeChat content")

    # 3. Determine date
    bj = datetime.now(timezone(timedelta(hours=8)))
    if bj.hour < 5:
        bj = bj - timedelta(days=1)
    date_str = bj.strftime("%Y-%m-%d")
    print(f"[INFO] Target date: {date_str}")

    # 4. Fetch content
    print("[INFO] Fetching news...")
    news = fetch_news()
    print(f"[INFO] Fetching papers...")
    papers = fetch_papers()

    if not news and not papers:
        print("[SKIP] No content fetched — nothing to publish")
        return 0

    print(f"[INFO]  News items: {len(news)},  Papers: {len(papers)}")

    # 5. Get WeChat access token
    print("[INFO] Getting WeChat access token...")
    token = get_access_token()
    if not token:
        return 1

    # 6. Generate cover image
    print("[INFO] Generating cover image...")
    cover_bytes = generate_cover(date_str, len(news), len(papers))

    # 7. Upload cover image
    print("[INFO] Uploading cover image to WeChat...")
    thumb_media_id = upload_image(token, cover_bytes)
    if not thumb_media_id:
        print("[WARN] Cover upload failed, retrying with fallback...")
        # retry with tiny fallback
        thumb_media_id = upload_image(token, _fallback_cover_bytes())
        if not thumb_media_id:
            print("[ERROR] Cannot create draft without cover image", file=sys.stderr)
            return 1

    # 8. Build WeChat-compatible HTML
    repo_url = f"https://miaohua1982.github.io/ai-daily/"
    content_html = build_wechat_html(news, papers, date_str, repo_url)

    # 9. Create draft
    date_fmt = date_str = bj.strftime("%Y%m%d")
    title = f"AI情报日报 | {date_fmt}"
    digest_parts = []
    if news:
        digest_parts.append(f"今日 {len(news)} 条AI热点")
    if papers:
        digest_parts.append(f"{len(papers)} 篇精选论文")
    digest = " · ".join(digest_parts) if digest_parts else "每日AI情报汇总"

    print(f"[INFO] Creating WeChat draft...")
    print(f"  Title: {title}")
    print(f"  Digest: {digest}")
    print(f"  Content: {len(content_html)} chars")

    ok = create_draft(token, thumb_media_id, title, content_html, digest, repo_url)
    if ok:
        print("[INFO] ✓ WeChat draft published successfully!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
