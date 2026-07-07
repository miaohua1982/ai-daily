"""
wechat - 微信公众号草稿发布辅助模块。

  - constants:  封面图常量（尺寸、配色、字体路径）
  - fetcher:    内容获取（复用 generate_daily / generate_papers 的 fetch + dedup）
  - cover:      封面图生成（Pillow 绘图 + 字体查找）
  - api:        微信 API 客户端（HTTP + access_token + 上传 + 草稿）
"""

from .fetcher import fetch_news, fetch_papers
from .cover import generate_cover
from .api import (
    wechat_get,
    wechat_post,
    get_access_token,
    upload_image,
    create_draft,
)

__all__ = [
    # fetcher
    "fetch_news", "fetch_papers",
    # cover
    "generate_cover",
    # api
    "wechat_get", "wechat_post",
    "get_access_token", "upload_image", "create_draft",
]
