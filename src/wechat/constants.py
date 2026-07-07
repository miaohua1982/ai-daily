"""wechat — 微信公众号封面图生成常量（尺寸、配色、字体路径）。"""

# ── 封面图尺寸 ───────────────────────────────────────────────────
COVER_W = 900
COVER_H = 380

# ── 封面图配色 ───────────────────────────────────────────────────
# 背景渐变（上→下）
BG_TOP = (244, 246, 250)
BG_BOTTOM = (250, 250, 242)

# 暖色光晕（右上角）
WARM_WASH_CENTER = (0 - 0, 20)  # 相对右上角
WARM_WASH_RADIUS = 520
WARM_WASH_COLOR_DELTA = (11, -10, -35)

# 点阵纹理
DOT_GRID_SPACING = 28
DOT_GRID_COLOR = (228, 232, 238)

# 装饰圆 — 右上大圆（暖橙）
DECO_CIRCLE_1 = {"cx": COVER_W + 150, "cy": -100, "r": 360, "delta": (6, 2, -2)}

# 装饰圆 — 左下小圆
DECO_CIRCLE_2 = {"cx": -60, "cy": COVER_H - 100, "r": 110, "delta": (4, 1, -3)}

# 顶部/底部装饰条
ACCENT_BAR_COLOR = (255, 107, 53)

# ── 文字配色 ─────────────────────────────────────────────────────
TEXT_TITLE_COLOR = (30, 30, 40)
TEXT_DATE_COLOR = (150, 140, 130)
TEXT_DIVIDER_COLOR = (240, 200, 170)
TEXT_FOOTER_COLOR = (175, 170, 165)

# ── 统计卡片配色 ─────────────────────────────────────────────────
# NEWS 卡片
CARD_NEWS_BG = (255, 252, 248)
CARD_NEWS_OUTLINE = (255, 220, 180)
CARD_NEWS_ACCENT = (255, 107, 53)
CARD_NEWS_LABEL = (180, 130, 100)
CARD_NEWS_UNIT = (160, 130, 110)

# PAPERS 卡片
CARD_PAPERS_BG = (255, 250, 250)
CARD_PAPERS_OUTLINE = (255, 200, 200)
CARD_PAPERS_ACCENT = (224, 82, 82)
CARD_PAPERS_LABEL = (180, 100, 100)
CARD_PAPERS_UNIT = (160, 100, 100)

# 卡片尺寸
CARD_Y = 175
CARD_W = 375
CARD_H = 145
CARD_GAP = 24
CARD_SHADOW_COLOR = (200, 200, 210)
CARD_SHADOW_OFFSET = 3
CARD_RADIUS = 14

# ── 字体大小 ─────────────────────────────────────────────────────
FONT_SIZE_TITLE = 54
FONT_SIZE_DATE = 26
FONT_SIZE_LABEL = 24
FONT_SIZE_NUM = 68
FONT_SIZE_UNIT = 22
FONT_SIZE_FOOT = 18

# ── 中文字体候选路径（macOS / Windows / Linux）─────────────────
CHINESE_FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    # Windows - 微软雅黑（Win7+ 默认中文字体）
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    # Windows - 黑体（兼容老系统）
    "C:/Windows/Fonts/simhei.ttf",
    # Windows - 等线（Win10+ 默认）
    "C:/Windows/Fonts/Deng.ttf",
    # Windows - 宋体
    "C:/Windows/Fonts/simsun.ttc",
    # Ubuntu 24.04 - noto-cjk (opentype or truetype)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Medium.ttc",
    # Ubuntu older - noto-cjk package
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

# Windows 字体目录（用于扫描兜底）
WIN_FONTS_DIR = "C:/Windows/Fonts"
WIN_FONT_KEYWORDS = ("msyh", "simhei", "simsun", "deng", "yahei", "song",
                     "hei", "kai", "ming", "fang")
