"""news — 新闻管线共享常量（分类、颜色、图标等）。"""

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

# newsnow 返回的 extra.info 中包含英文 category slug
SLUG_TO_LABEL = CATEGORY_LABELS
