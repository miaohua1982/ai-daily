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
  - generate_wechat.py      编排（配置加载 + 两阶段：本地产出 → 微信发布）

本地预览模式：设置环境变量 WECHAT_LOCAL_ONLY=1 或加命令行参数 --local-only，
只生成 wechat.md / wechat.html 及归档，不调用微信 API、不生成封面、不建草稿。
本地模式不要求 WECHAT_APPID / WECHAT_APPSECRET，便于无密钥调试。
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from utils import get_dot_env, load_config, get_now_date_str
from src.wechat.renderer import render_wechat_html, render_wechat_md, wrap_wechat_html_doc
from src.wechat.fetcher import fetch_news, fetch_papers, cross_dedup_news_papers
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


# -- Local-only mode -------------------------------------------------------
def is_local_only() -> bool:
    """本地预览模式开关：只生成本地文件，不调用微信 API。

    触发方式（任一即可）：
      - 环境变量 WECHAT_LOCAL_ONLY=1（或 true/yes）
      - 命令行参数 --local-only
    """
    env_val = os.environ.get("WECHAT_LOCAL_ONLY", "").strip().lower()
    if env_val in ("1", "true", "yes"):
        return True
    return "--local-only" in sys.argv


# -- Phase 1: build & write local artifacts --------------------------------
def build_local_artifacts():
    """抓取 + 去重 + 截断 + 渲染 + 写入本地 wechat.md / wechat.html + 归档。

    Returns:
        (news, papers, date_str, content_html) 元组；无内容时返回 None。
    """
    print("[INFO] Fetching news...")
    news = fetch_news()
    print("[INFO] Fetching papers...")
    papers = fetch_papers()

    # 统一去重（URL 精确 + 全量语义；冲突时保留 news）
    news, papers = cross_dedup_news_papers(news, papers, _config)

    # 去重后再截断，确保每个区块都达到上限
    news = news[:MAX_NEWS]
    papers = papers[:MAX_PAPERS]

    if not news and not papers:
        print("[SKIP] No content fetched - nothing to publish")
        return None

    date_str = get_now_date_str()
    print(f"[INFO] Target date: {date_str}, News: {len(news)}, Papers: {len(papers)}")

    # 渲染微信 HTML + 本地 Markdown
    content_html = render_wechat_html(news, papers, date_str, REPO_URL)
    content_md = render_wechat_md(news, papers, date_str, REPO_URL)

    # 写 MD 到本地
    md_path = OUTPUT_DIR / "wechat.md"
    md_path.write_text(content_md, encoding="utf-8")
    print(f"[INFO] Markdown saved: {md_path} ({len(content_md)} chars)")

    # 写 HTML 到本地（content_html 是微信风格片段，包成完整文档便于浏览器预览）
    html_doc = wrap_wechat_html_doc(content_html, date_str)
    html_path = OUTPUT_DIR / "wechat.html"
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"[INFO] HTML saved: {html_path} ({len(content_html)} chars)")

    # 按日期归档（与 archive/news、archive/papers 约定一致：{archive_dir}/{date_str}.<ext>）
    archive_dir = OUTPUT_DIR / "archive" / "wechat_draft"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_html = archive_dir / f"{date_str}.html"
    archive_html.write_text(html_doc, encoding="utf-8")
    print(f"[INFO] HTML archived: {archive_html}")
    archive_md = archive_dir / f"{date_str}.md"
    archive_md.write_text(content_md, encoding="utf-8")
    print(f"[INFO] MD archived: {archive_md}")

    return news, papers, date_str, content_html


# -- Phase 2: publish to WeChat --------------------------------------------
def publish_to_wechat(news, papers, date_str, content_html) -> int:
    """取 access token → 生成封面 → 上传封面 → 建草稿。需要 WECHAT_APPID/APPSECRET。"""
    # Gate: 发布阶段必须有凭据
    if not APPID or not APPSECRET:
        print("[SKIP] WECHAT_APPID or WECHAT_APPSECRET not set - skip publishing")
        return 0

    print("[INFO] Getting WeChat access token...")
    token = get_access_token(WECHAT_BASE, APPID, APPSECRET)
    if not token:
        return 1

    print("[INFO] Generating cover image...")
    cover_bytes = generate_cover(date_str, len(news), len(papers))

    print("[INFO] Uploading cover image to WeChat...")
    thumb_media_id = upload_image(WECHAT_BASE, token, cover_bytes)
    if not thumb_media_id:
        print("[ERROR] Cover upload failed, cannot create draft", file=sys.stderr)
        return 1

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
    return 1


# -- Main ------------------------------------------------------------------
def main() -> int:
    # 判断是否本地预览模式（WECHAT_LOCAL_ONLY=1 或 --local-only）
    local = is_local_only()
    if local:
        print("[INFO] Local-only mode: building wechat.md / wechat.html, skip WeChat API")

    # 阶段一：抓取 → 去重 → 截断 → 渲染 → 写入本地 wechat.md/wechat.html → 归档
    result = build_local_artifacts()
    # 无内容可发布，直接结束
    if result is None:
        return 0

    # 本地模式：阶段一（本地产出）已完成即返回，不调用微信 API / 不生成封面 / 不建草稿
    if local:
        print("[INFO] Local-only mode done. Skipped WeChat publish (token/cover/draft).")
        return 0

    # 解包阶段一产物，供发布阶段复用
    news, papers, date_str, content_html = result
    # 阶段二：发布到微信（取 token → 生成封面 → 上传封面 → 创建草稿）
    return publish_to_wechat(news, papers, date_str, content_html)


if __name__ == "__main__":
    sys.exit(main())
