#!/usr/bin/env python3
"""
WeChat「一周论文回顾」周报草稿发布入口。

与日报 generate_wechat.py 的差异：
  - 纯论文（news 恒为空列表），数据源直接 arXiv + HuggingFace，跳过 aihot
  - 时间窗口为自然周（本周一 ~ 运行日），每周日 17:00 北京时间由
    .github/workflows/wechat_papers_weekly.yml 触发（cron '0 9 * * 0'）
  - 排序精选：HF upvotes 降序为主力、arXiv 时间倒序补位，取 top_n（默认 30）
  - 产物：wechat_papers_weekly.html / .md + archive/wechat_papers_weekly/{date}.*

流程：fetch weekly papers → 渲染(HTML+MD) → 归档 → 封面 → 上传 → 创建草稿。
去重（URL + 语义）已在 fetch_weekly_papers 内部完成（utils.dedup_data），
无需 cross_dedup（周报只有 papers 单一集合）。

辅助模块：
  - src/wechat/weekly_fetcher.py  周报内容获取（自然周窗口 + 排序精选）
  - src/wechat/cover.py           封面图（generate_weekly_cover 单卡版）
  - src/wechat/api.py             微信 API 客户端（与日报共用）
  - src/wechat/renderer.py        渲染（与日报共用，传周报标题参数）
"""

import os
import sys
from pathlib import Path

from utils import get_dot_env, load_config, get_now_date_str
from src.wechat.renderer import render_wechat_html, render_wechat_md, wrap_wechat_html_doc
from src.wechat.weekly_fetcher import fetch_weekly_papers
from src.wechat.cover import generate_weekly_cover
from src.wechat.api import get_access_token, upload_image, create_draft

# -- Configuration ---------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = OUTPUT_DIR / "config" / "weekly_config.yaml"

# 周报渲染文案（renderer 的可选参数；不传则是日报文案）
WEEKLY_MAIN_TITLE = "📚 AI 一周论文回顾"
WEEKLY_PAPERS_LABEL = "📄 本周精选论文"
WEEKLY_DOC_TITLE = "AI 一周论文回顾"

# -- Load config & secrets -------------------------------------------------
_env = get_dot_env()
_config = load_config(CONFIG_FILE)

WECHAT_BASE = _config["wechat_base"]
REPO_URL = _config["repo_url"]
TITLE_TEMPLATE = _config["title_template"]
DIGEST_TEMPLATE = _config["digest_template"]
DIGEST_FALLBACK = _config["digest_fallback"]
AUTHOR = _config["author"]

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

    # 2. Fetch weekly papers（内部完成：自然周窗口 + 双源抓取 + 过滤 +
    #    去重(URL+语义) + 排序(HF upvotes 前/arXiv 时间后) + top_n 截断 + 翻译）
    print("[INFO] Fetching weekly papers (HF + arXiv, natural week)...")
    papers = fetch_weekly_papers(_config)

    if not papers:
        print("[SKIP] No papers fetched - nothing to publish")
        return 0

    date_str = get_now_date_str()
    print(f"[INFO] Target date: {date_str}, Papers: {len(papers)}")

    # 3. Get WeChat access token
    print("[INFO] Getting WeChat access token...")
    token = get_access_token(WECHAT_BASE, APPID, APPSECRET)
    if not token:
        return 1

    # 4. Generate weekly cover image（单卡：本周精选论文 N 篇）
    print("[INFO] Generating weekly cover image...")
    cover_bytes = generate_weekly_cover(date_str, len(papers))

    # 5. Upload cover image
    print("[INFO] Uploading cover image to WeChat...")
    thumb_media_id = upload_image(WECHAT_BASE, token, cover_bytes)
    if not thumb_media_id:
        print("[ERROR] Cover upload failed, cannot create draft", file=sys.stderr)
        return 1

    # 6. Build WeChat-compatible HTML + local Markdown（news 恒为空 ⇒ 纯论文块）
    content_html = render_wechat_html(
        [], papers, date_str, REPO_URL,
        main_title=WEEKLY_MAIN_TITLE, papers_label=WEEKLY_PAPERS_LABEL,
        show_paper_source=False, paper_link_button=True,
    )
    content_md = render_wechat_md(
        [], papers, date_str, REPO_URL,
        main_title=WEEKLY_MAIN_TITLE, papers_label=WEEKLY_PAPERS_LABEL,
        show_paper_source=False, paper_link_button=True,
    )

    # Write MD to local file (for preview / GitHub display)
    md_path = OUTPUT_DIR / "wechat_papers_weekly.md"
    md_path.write_text(content_md, encoding="utf-8")
    print(f"[INFO] Markdown saved: {md_path} ({len(content_md)} chars)")

    # Write HTML to local file (wrap fragment into complete doc for browsers)
    html_path = OUTPUT_DIR / "wechat_papers_weekly.html"
    html_doc = wrap_wechat_html_doc(content_html, date_str, doc_title=WEEKLY_DOC_TITLE)
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"[INFO] HTML saved: {html_path} ({len(content_html)} chars)")

    # Archive both artifacts by run date（与 archive/wechat_draft 同一约定：
    # {archive_dir}/{date_str}.<ext>，目录缺失时自动创建）
    archive_dir = OUTPUT_DIR / "archive" / "wechat_papers_weekly"
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
    digest = DIGEST_TEMPLATE.format(papers_count=len(papers)) if papers else DIGEST_FALLBACK

    print("[INFO] Creating WeChat draft...")
    print(f"  Title: {title}")
    print(f"  Digest: {digest}")
    print(f"  Content: {len(content_html)} chars")

    ok = create_draft(WECHAT_BASE, token, thumb_media_id, title, content_html, digest, REPO_URL, AUTHOR)
    if ok:
        print("[INFO] WeChat weekly draft published successfully!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
