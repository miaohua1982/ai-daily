#!/usr/bin/env python3
"""
Cover image generator test.
Imports generate_cover from generate_wechat and writes the PNG to craft/.

Usage:
  python test/test_cover.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── Setup paths ─────────────────────────────────────────────────
# 文件位于 test/ 子目录，项目根目录是上两级
ROOT = Path(__file__).parent.parent.resolve()
CRAFT_DIR = ROOT / "craft"
CRAFT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))

# ── Import cover generator from generate_wechat ─────────────────
from generate_wechat import generate_cover

# ── Test data ───────────────────────────────────────────────────
today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
news_count = 15
papers_count = 8

# ── Generate & save ─────────────────────────────────────────────
print(f"[INFO] Generating cover for {today} (news={news_count}, papers={papers_count})...")
cover_bytes = generate_cover(today, news_count, papers_count)

out_path = CRAFT_DIR / "cover.png"
out_path.write_bytes(cover_bytes)

print(f"[OK] Cover saved to {out_path} ({len(cover_bytes):,} bytes)")
