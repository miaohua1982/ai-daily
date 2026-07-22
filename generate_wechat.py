#!/usr/bin/env python3
"""
WeChat Official Account Draft Publisher
- Fetches + dedup content via generate_daily / generate_papers step functions
- Builds WeChat-compatible HTML → submits draft via API
- Builds local Markdown → saves wechat.md (for preview / GitHub display)
- Uses env vars: WECHAT_APPID, WECHAT_APPSECRET

Scheduled after daily (05:00) and papers (06:00) - Beijing time.

辅助函数已拆分至 src/wechat/ 目录：
  - src/wechat/fetcher.py   内容获取（复用 generate_daily/papers 的 fetch + dedup）
  - src/wechat/cover.py     封面图生成（Pillow 绘图 + 字体查找）
  - src/wechat/api.py       微信 API 客户端（HTTP + access_token + 上传 + 草稿）
  - src/wechat/renderer.py  微信草稿渲染（HTML + Markdown 双格式，组合 news + papers）
  - generate_wechat.py      编排（配置加载 + gate 检查 + 主流程）
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from utils import get_dot_env, load_config, get_now_date_str
from src.wechat.renderer import render_wechat_html, render_wechat_md, wrap_wechat_html_doc
from src.wechat.fetcher import fetch_news, fetch_papers
from src.wechat.cover import generate_cover
from src.wechat.api import get_access_token, upload_image, create_draft

# -- Configuration ---------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = OUTPUT_DIR / "config" / "wechat_config.yaml"

# -- Load config & secrets -------------------------------------------------
_env = get_dot_env()
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
APPID = (os.environ.get(appid_env) or _env.get(appid_env, "")).strip()
APPSECRET = (os.environ.get(appsecret_env) or _env.get(appsecret_env, "")).strip()


# -- Main ------------------------------------------------------------------

def main() -> int:
    # 1. Gate: must have credentials
    if not APPID or not APPSECRET:
        print("[SKIP] WECHAT_APPID or WECHAT_APPSECRET not set in environment")
        return 0

    # 2. Fetch + dedup content via step functions
    print("[INFO] Fetching news...")
    news = fetch_news(MAX_NEWS)
    print("[INFO] Fetching papers...")
    papers = fetch_papers(MAX_PAPERS)

    if not news and not papers:
        print("[SKIP] No content fetched - nothing to publish")
        return 0

    # Use news date as primary; fallback to papers date or local calculation
    date_str = get_now_date_str()
    print(f"[INFO] Target date: {date_str}, News: {len(news)}, Papers: {len(papers)}")

    # 3. Get WeChat access token
    print("[INFO] Getting WeChat access token...")
    token = get_access_token(WECHAT_BASE, APPID, APPSECRET)
    if not token:
        return 1

    # 4. Generate cover image
    print("[INFO] Generating cover image...")
    cover_bytes = generate_cover(date_str, len(news), len(papers))

    # 5. Upload cover image
    print("[INFO] Uploading cover image to WeChat...")
    thumb_media_id = upload_image(WECHAT_BASE, token, cover_bytes)
    if not thumb_media_id:
        print("[ERROR] Cover upload failed, cannot create draft", file=sys.stderr)
        return 1

    # 6. Build WeChat-compatible HTML + local Markdown
    content_html = render_wechat_html(news, papers, date_str, REPO_URL)
    content_md = render_wechat_md(news, papers, date_str, REPO_URL)

    # Write MD to local file (for preview / GitHub display)
    md_path = OUTPUT_DIR / "wechat.md"
    md_path.write_text(content_md, encoding="utf-8")
    print(f"[INFO] Markdown saved: {md_path} ({len(content_md)} chars)")

    # Write HTML to local file (for preview / GitHub display).
    # content_html is a WeChat-style fragment (no <html>/<head>/<body>); wrap it
    # in a complete document via the renderer for proper local browser rendering.
    html_path = OUTPUT_DIR / "wechat.html"
    html_doc = wrap_wechat_html_doc(content_html, date_str)
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"[INFO] HTML saved: {html_path} ({len(content_html)} chars)")

    # Archive both local artifacts by date (mirrors archive/news, archive/papers
    # convention: {archive_dir}/{date_str}.<ext>), creating the dir if missing.
    archive_dir = OUTPUT_DIR / "archive" / "wechat_draft"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_html = archive_dir / f"{date_str}.html"
    archive_html.write_text(html_doc, encoding="utf-8")
    print(f"[INFO] HTML archived: {archive_html}")
    archive_md = archive_dir / f"{date_str}.md"
    archive_md.write_text(content_md, encoding="utf-8")
    print(f"[INFO] MD archived: {archive_md}")

    # 7. Create draft
    date_fmt = date_str.replace("-", "")
    title = TITLE_TEMPLATE.format(date=date_fmt)
    digest_parts = []
    if news:
        digest_parts.append(DIGEST_TEMPLATE.format(news_count=len(news), papers_count=len(papers)))
    elif papers:
        digest_parts.append(f"{len(papers)} 篇精选论文")
    digest = " · ".join(digest_parts) if digest_parts else DIGEST_FALLBACK

    print("[INFO] Creating WeChat draft...")
    print(f"  Title: {title}")
    print(f"  Digest: {digest}")
    print(f"  Content: {len(content_html)} chars")

    ok = create_draft(WECHAT_BASE, token, thumb_media_id, title, content_html, digest, REPO_URL, AUTHOR)
    if ok:
        print("[INFO] WeChat draft published successfully!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
