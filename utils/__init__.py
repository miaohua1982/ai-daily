"""
Utils — 公共工具函数包

从子模块中 re-export 所有公共函数和常量，
外部调用方只需 ``from utils import X`` 即可使用。
"""

from .utils import (
    load_dot_env,
    load_config,
    get_embeddings,
    cosine_similarity,
    semantic_dedup,
    dedup_data,
    filter_by_date,
    get_now_date_str,
    esc_html,
    esc_attr,
    api_get,
    write_files,
    git_commit,
    UA,
)

from .html_template import (
    render_news_html,
    render_papers_html,
    render_trending_html,
    render_wechat_html,
    WEEKDAY_NAMES,
)
