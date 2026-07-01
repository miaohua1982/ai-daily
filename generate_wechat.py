#!/usr/bin/env python3
"""
WeChat Official Account Draft Publisher
- Fetches + dedup content via generate_daily / generate_papers step functions
- Builds WeChat-compatible HTML and creates a draft on WeChat platform
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
from utils import load_dot_env, load_config, UA
from utils.html_template import render_wechat_html
import generate_daily as gd
import generate_papers as gp

# ── Configuration ──────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = OUTPUT_DIR / "config" / "wechat_config.yaml"

# Gate files — must both exist for the script to run
DAILY_FILE = OUTPUT_DIR / "daily_news.html"
PAPERS_FILE = OUTPUT_DIR / "papers.html"

# ── Load config & secrets ───────────────────────────────────────
_dotenv = load_dot_env(OUTPUT_DIR / ".env")
_config = load_config(CONFIG_FILE)

WECHAT_BASE = _config["wechat_base"]
REPO_URL = _config["repo_url"]
TITLE_TEMPLATE = _config["title_template"]
DIGEST_TEMPLATE = _config["digest_template"]
DIGEST_FALLBACK = _config["digest_fallback"]
AUTHOR = _config["author"]
MAX_NEWS = _config["max_news"]
MAX_PAPERS = _config["max_papers"]

appid_env = _config["appid_env"]
appsecret_env = _config["appsecret_env"]
APPID = (os.environ.get(appid_env) or _dotenv.get(appid_env, "")).strip()
APPSECRET = (os.environ.get(appsecret_env) or _dotenv.get(appsecret_env, "")).strip()

# ── WeChat API helpers ─────────────────────────────────────────

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


# ── Content fetching (reuses generate_daily / generate_papers) ──

def fetch_news() -> tuple[list[dict], str]:
    """Fetch + dedup news via generate_daily step functions. Returns (items, date_str)."""
    try:
        config = load_config(gd.CONFIG_FILE)
        data, date_str = gd.fetch_data(config=config)
    except Exception as e:
        print(f"[WARN] fetch_news failed: {e}", file=sys.stderr)
        return [], ""

    if not data or "sections" not in data:
        return [], date_str

    # Use generate_daily's dedup (URL + semantic)
    items_by_cat = gd.dedup_data(data, config)

    # Flatten items_by_cat → list with _section labels, preserving CATEGORY_ORDER
    news_items = []
    for cat in gd.CATEGORY_ORDER:
        label = gd.CATEGORY_LABELS.get(cat, cat)
        for it in items_by_cat.get(cat, []):
            it["_section"] = label
            news_items.append(it)

    print(f"[INFO] News: {len(news_items)} items after dedup")
    return news_items[:MAX_NEWS], date_str


def fetch_papers() -> tuple[list[dict], str]:
    """Fetch + dedup papers via generate_papers step functions. Returns (papers, date_str)."""
    try:
        config = load_config(gp.CONFIG_FILE)
        items, date_str = gp.fetch_data(config=config)
    except Exception as e:
        print(f"[WARN] fetch_papers failed: {e}", file=sys.stderr)
        return [], ""

    if not items:
        return [], ""

    # Use generate_papers's dedup (URL + semantic + top selection)
    papers = gp.dedup_data(items, config)

    print(f"[INFO] Papers: {len(papers)} items after dedup")
    return papers[:MAX_PAPERS], date_str


# ── Cover image generation ─────────────────────────────────────

def generate_cover(today: str, news_count: int, papers_count: int) -> bytes:
    """Generate a polished cover image — background first, then text overlay."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[WARN] Pillow not available, using fallback cover", file=sys.stderr)
        return _fallback_cover_bytes()

    W, H = 900, 380

    img = Image.new("RGB", (W, H), (244, 246, 250))
    draw = ImageDraw.Draw(img)

    # 1a. Vertical gradient — clean white to warm cream (top→bottom)
    for y in range(H):
        t = y / H
        r = int(244 + t * 6)
        g = int(246 + t * 4)
        b = int(250 - t * 8)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 1b. Top-right warm wash (sunlight feel)
    for y in range(0, 170):
        for x in range(W // 2, W):
            dist = ((x - W) ** 2 + (y - 20) ** 2) ** 0.5
            alpha = max(0, 1 - dist / 520)
            if alpha > 0.02:
                r2 = int(244 + alpha * 11)
                g2 = int(246 - alpha * 10)
                b2 = int(250 - alpha * 35)
                img.putpixel((x, y), (r2, g2, b2))

    # 1c. Subtle dot-grid texture
    spacing = 28
    for gx in range(spacing, W, spacing):
        for gy in range(spacing, H, spacing):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(228, 232, 238))

    # 1d. Large decorative circle — warm orange, low opacity
    cx1, cy1, r1 = W + 150, -100, 360
    for x in range(max(0, cx1 - r1), min(W, cx1 + r1)):
        for y in range(max(0, cy1 - r1), min(H, cy1 + r1)):
            if (x - cx1) ** 2 + (y - cy1) ** 2 < r1 ** 2:
                orig = img.getpixel((x, y))
                r, g, b = orig
                img.putpixel((x, y), (
                    min(255, r + 6), min(255, g + 2), max(0, b - 2)
                ))

    # 1e. Small accent circle — bottom left
    cx2, cy2, r2 = -60, H - 100, 110
    for x in range(max(0, cx2 - r2), min(W, cx2 + r2)):
        for y in range(max(0, cy2 - r2), min(W, cy2 + r2)):
            if (x - cx2) ** 2 + (y - cy2) ** 2 < r2 ** 2:
                orig = img.getpixel((x, y))
                r, g, b = orig
                img.putpixel((x, y), (
                    min(255, r + 4), min(255, g + 1), max(0, b - 3)
                ))

    # 1f. Top accent bar
    draw.rectangle([0, 0, W, 5], fill=(255, 107, 53))

    # 1g. Bottom accent bar
    draw.rectangle([0, H - 5, W, H], fill=(255, 107, 53))

    # STEP 2 — Draw text overlay
    try:
        font_title = _find_chinese_font(54)
        font_date = _find_chinese_font(26)
        font_label = _find_chinese_font(24)
        font_num = _find_chinese_font(68)
        font_unit = _find_chinese_font(22)
        font_foot = _find_chinese_font(18)
    except Exception:
        font_title = font_date = font_label = font_num = font_unit = font_foot = ImageFont.load_default()

    # ── Header ──
    draw.text((55, 45), "AI 情报日报", fill=(30, 30, 40), font=font_title)
    draw.text((55, 112), today, fill=(150, 140, 130), font=font_date)
    draw.line([(55, 150), (440, 150)], fill=(240, 200, 170), width=2)

    # ── Stats cards ──
    card_y = 175
    card_w = 375
    card_h = 145

    # Shared shadow helper
    def _card_shadow(x1, y1, x2, y2, radius=14, offset=3):
        sx1, sy1 = x1 + offset, y1 + offset
        sx2, sy2 = x2 + offset, y2 + offset
        draw.rounded_rectangle(
            [(sx1, sy1), (sx2, sy2)], radius=radius,
            fill=(200, 200, 210)
        )

    # ---- NEWS card ----
    nx1, ny1 = 50, card_y
    nx2, ny2 = nx1 + card_w, card_y + card_h
    _card_shadow(nx1, ny1, nx2, ny2)
    draw.rounded_rectangle(
        [(nx1, ny1), (nx2, ny2)], radius=14,
        fill=(255, 252, 248), outline=(255, 220, 180), width=2
    )
    # Left accent bar on card
    draw.rectangle([nx1 + 1, ny1 + 14, nx1 + 6, ny2 - 14], fill=(255, 107, 53))
    draw.text((nx1 + 28, ny1 + 20), "热点资讯", fill=(180, 130, 100), font=font_label)
    # Number — measure width & center
    ntext = str(news_count)
    nbox = draw.textbbox((0, 0), ntext, font=font_num)
    ntw = nbox[2] - nbox[0]
    draw.text((nx1 + (card_w - ntw) // 2 - 30, ny1 + 48), ntext, fill=(255, 107, 53), font=font_num)
    draw.text((nx1 + card_w // 2 + 20, ny1 + 82), "则", fill=(160, 130, 110), font=font_unit)

    # ---- PAPERS card ----
    px1, py1 = nx2 + 24, card_y
    px2, py2 = px1 + card_w, card_y + card_h
    _card_shadow(px1, py1, px2, py2)
    draw.rounded_rectangle(
        [(px1, py1), (px2, py2)], radius=14,
        fill=(255, 250, 250), outline=(255, 200, 200), width=2
    )
    draw.rectangle([px1 + 1, py1 + 14, px1 + 6, py2 - 14], fill=(224, 82, 82))
    draw.text((px1 + 28, py1 + 20), "精选论文", fill=(180, 100, 100), font=font_label)
    ptext = str(papers_count)
    pbox = draw.textbbox((0, 0), ptext, font=font_num)
    ptw = pbox[2] - pbox[0]
    draw.text((px1 + (card_w - ptw) // 2 - 30, py1 + 48), ptext, fill=(224, 82, 82), font=font_num)
    draw.text((px1 + card_w // 2 + 20, py1 + 82), "篇", fill=(160, 100, 100), font=font_unit)

    # ── Footer ──
    draw.text((55, 345), "由 ai-daily 自动生成 · 仅供学习参考", fill=(175, 170, 165), font=font_foot)

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
                "author": AUTHOR,
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

    # 3. Fetch + dedup content via step functions
    print("[INFO] Fetching news...")
    news, news_date = fetch_news()
    print("[INFO] Fetching papers...")
    papers, papers_date = fetch_papers()

    if not news and not papers:
        print("[SKIP] No content fetched — nothing to publish")
        return 0

    # Use news date as primary; fallback to papers date or local calculation
    date_str = news_date or papers_date
    if not date_str:
        bj = datetime.now(timezone(timedelta(hours=8)))
        if bj.hour < 5:
            bj = bj - timedelta(days=1)
        date_str = bj.strftime("%Y-%m-%d")

    print(f"[INFO] Target date: {date_str}, News: {len(news)}, Papers: {len(papers)}")

    # 4. Get WeChat access token
    print("[INFO] Getting WeChat access token...")
    token = get_access_token()
    if not token:
        return 1

    # 5. Generate cover image
    print("[INFO] Generating cover image...")
    cover_bytes = generate_cover(date_str, len(news), len(papers))

    # 6. Upload cover image
    print("[INFO] Uploading cover image to WeChat...")
    thumb_media_id = upload_image(token, cover_bytes)
    if not thumb_media_id:
        print("[WARN] Cover upload failed, retrying with fallback...")
        thumb_media_id = upload_image(token, _fallback_cover_bytes())
        if not thumb_media_id:
            print("[ERROR] Cannot create draft without cover image", file=sys.stderr)
            return 1

    # 7. Build WeChat-compatible HTML
    content_html = render_wechat_html(news, papers, date_str, REPO_URL)

    # 8. Create draft
    date_fmt = date_str.replace("-", "")
    title = TITLE_TEMPLATE.format(date=date_fmt)
    digest_parts = []
    if news:
        digest_parts.append(DIGEST_TEMPLATE.format(news_count=len(news), papers_count=len(papers)))
    elif papers:
        digest_parts.append(f"{len(papers)} 篇精选论文")
    digest = " · ".join(digest_parts) if digest_parts else DIGEST_FALLBACK

    print(f"[INFO] Creating WeChat draft...")
    print(f"  Title: {title}")
    print(f"  Digest: {digest}")
    print(f"  Content: {len(content_html)} chars")

    ok = create_draft(token, thumb_media_id, title, content_html, digest, REPO_URL)
    if ok:
        print("[INFO] ✓ WeChat draft published successfully!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
