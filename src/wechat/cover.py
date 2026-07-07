"""
wechat/cover - 微信公众号封面图生成（Pillow 绘图 + 字体查找）。

generate_cover(today, news_count, papers_count) -> bytes (PNG)
"""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.wechat.constants import (
    COVER_W, COVER_H,
    BG_TOP,
    WARM_WASH_RADIUS, WARM_WASH_COLOR_DELTA,
    DOT_GRID_SPACING, DOT_GRID_COLOR,
    DECO_CIRCLE_1, DECO_CIRCLE_2,
    ACCENT_BAR_COLOR,
    TEXT_TITLE_COLOR, TEXT_DATE_COLOR, TEXT_DIVIDER_COLOR, TEXT_FOOTER_COLOR,
    CARD_NEWS_BG, CARD_NEWS_OUTLINE, CARD_NEWS_ACCENT, CARD_NEWS_LABEL, CARD_NEWS_UNIT,
    CARD_PAPERS_BG, CARD_PAPERS_OUTLINE, CARD_PAPERS_ACCENT, CARD_PAPERS_LABEL, CARD_PAPERS_UNIT,
    CARD_Y, CARD_W, CARD_H, CARD_GAP, CARD_SHADOW_COLOR, CARD_SHADOW_OFFSET, CARD_RADIUS,
    FONT_SIZE_TITLE, FONT_SIZE_DATE, FONT_SIZE_LABEL, FONT_SIZE_NUM, FONT_SIZE_UNIT, FONT_SIZE_FOOT,
    CHINESE_FONT_CANDIDATES, WIN_FONTS_DIR, WIN_FONT_KEYWORDS,
)


def generate_cover(today: str, news_count: int, papers_count: int) -> bytes:
    """生成封面图 PNG bytes - 先绘制背景再叠加文字。"""
    W, H = COVER_W, COVER_H

    img = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)

    # 1a. 垂直渐变 - 白色到暖米色（上->下）
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + t * 6)
        g = int(BG_TOP[1] + t * 4)
        b = int(BG_TOP[2] - t * 8)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 1b. 右上角暖色光晕
    for y in range(0, 170):
        for x in range(W // 2, W):
            dist = ((x - W) ** 2 + (y - 20) ** 2) ** 0.5
            alpha = max(0, 1 - dist / WARM_WASH_RADIUS)
            if alpha > 0.02:
                dr, dg, db = WARM_WASH_COLOR_DELTA
                r2 = int(BG_TOP[0] + alpha * dr)
                g2 = int(BG_TOP[1] + alpha * dg)
                b2 = int(BG_TOP[2] + alpha * db)
                img.putpixel((x, y), (r2, g2, b2))

    # 1c. 点阵纹理
    spacing = DOT_GRID_SPACING
    for gx in range(spacing, W, spacing):
        for gy in range(spacing, H, spacing):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=DOT_GRID_COLOR)

    # 1d. 大装饰圆 - 暖橙色，低透明度
    _draw_deco_circle(img, draw, DECO_CIRCLE_1, W, H)

    # 1e. 小装饰圆 - 左下角
    _draw_deco_circle(img, draw, DECO_CIRCLE_2, W, H)

    # 1f. 顶部装饰条
    draw.rectangle([0, 0, W, 5], fill=ACCENT_BAR_COLOR)

    # 1g. 底部装饰条
    draw.rectangle([0, H - 5, W, H], fill=ACCENT_BAR_COLOR)

    # ── STEP 2 - 文字叠加 ──
    try:
        font_title = _find_chinese_font(FONT_SIZE_TITLE)
        font_date = _find_chinese_font(FONT_SIZE_DATE)
        font_label = _find_chinese_font(FONT_SIZE_LABEL)
        font_num = _find_chinese_font(FONT_SIZE_NUM)
        font_unit = _find_chinese_font(FONT_SIZE_UNIT)
        font_foot = _find_chinese_font(FONT_SIZE_FOOT)
    except Exception:
        font_title = font_date = font_label = font_num = font_unit = font_foot = ImageFont.load_default()

    # ── Header ──
    draw.text((55, 45), "AI 情报", fill=TEXT_TITLE_COLOR, font=font_title)
    draw.text((55, 112), today, fill=TEXT_DATE_COLOR, font=font_date)
    draw.line([(55, 150), (440, 150)], fill=TEXT_DIVIDER_COLOR, width=2)

    # ── 统计卡片 ──
    nx1 = 50
    px1 = nx1 + CARD_W + CARD_GAP

    _draw_stats_card(draw, nx1, CARD_Y, "热点资讯", str(news_count), "则",
                     CARD_NEWS_BG, CARD_NEWS_OUTLINE, CARD_NEWS_ACCENT,
                     CARD_NEWS_LABEL, CARD_NEWS_UNIT,
                     font_label, font_num, font_unit)

    _draw_stats_card(draw, px1, CARD_Y, "精选论文", str(papers_count), "篇",
                     CARD_PAPERS_BG, CARD_PAPERS_OUTLINE, CARD_PAPERS_ACCENT,
                     CARD_PAPERS_LABEL, CARD_PAPERS_UNIT,
                     font_label, font_num, font_unit)

    # ── Footer ──
    draw.text((55, 345), "由 ai-daily 自动生成 · 仅供学习参考", fill=TEXT_FOOTER_COLOR, font=font_foot)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _draw_deco_circle(img, draw, circle: dict, W: int, H: int):
    """绘制半透明装饰圆。"""
    cx, cy, r = circle["cx"], circle["cy"], circle["r"]
    dr, dg, db = circle["delta"]
    for x in range(max(0, cx - r), min(W, cx + r)):
        for y in range(max(0, cy - r), min(H, cy + r)):
            if (x - cx) ** 2 + (y - cy) ** 2 < r ** 2:
                orig = img.getpixel((x, y))
                r0, g0, b0 = orig
                img.putpixel((x, y), (
                    min(255, r0 + dr), min(255, g0 + dg), max(0, b0 + db)
                ))


def _draw_stats_card(draw, x1, y1, label, num_text, unit,
                     bg, outline, accent, label_color, unit_color,
                     font_label, font_num, font_unit):
    """绘制一个统计卡片（阴影 + 圆角矩形 + 左侧色条 + 数字居中）。"""
    x2 = x1 + CARD_W
    y2 = y1 + CARD_H

    # 阴影
    sx1 = x1 + CARD_SHADOW_OFFSET
    sy1 = y1 + CARD_SHADOW_OFFSET
    sx2 = x2 + CARD_SHADOW_OFFSET
    sy2 = y2 + CARD_SHADOW_OFFSET
    draw.rounded_rectangle(
        [(sx1, sy1), (sx2, sy2)], radius=CARD_RADIUS,
        fill=CARD_SHADOW_COLOR
    )

    # 卡片主体
    draw.rounded_rectangle(
        [(x1, y1), (x2, y2)], radius=CARD_RADIUS,
        fill=bg, outline=outline, width=2
    )

    # 左侧色条
    draw.rectangle([x1 + 1, y1 + 14, x1 + 6, y2 - 14], fill=accent)

    # 标签
    draw.text((x1 + 28, y1 + 20), label, fill=label_color, font=font_label)

    # 数字 - 测量宽度并居中
    nbox = draw.textbbox((0, 0), num_text, font=font_num)
    ntw = nbox[2] - nbox[0]
    draw.text((x1 + (CARD_W - ntw) // 2 - 30, y1 + 48), num_text, fill=accent, font=font_num)
    draw.text((x1 + CARD_W // 2 + 20, y1 + 82), unit, fill=unit_color, font=font_unit)


def _find_chinese_font(size: int):
    """跨平台查找中文字体，返回 ImageFont 对象。"""
    from PIL import ImageFont

    # 1. 按候选路径列表查找
    for path in CHINESE_FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    # 2. Fallback: 用 fc-list 扫描系统（Linux/macOS with fontconfig）
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

    # 3. Fallback: Windows - 扫描字体目录查找任何 CJK ttc/ttf
    try:
        win_fonts_dir = Path(WIN_FONTS_DIR)
        if win_fonts_dir.is_dir():
            for ext in ("*.ttc", "*.ttf"):
                for fp in win_fonts_dir.glob(ext):
                    name = fp.name.lower()
                    if any(k in name for k in WIN_FONT_KEYWORDS):
                        return ImageFont.truetype(str(fp), size)
    except Exception:
        pass

    return ImageFont.load_default()
