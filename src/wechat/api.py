"""
wechat/api - 微信公众号 API 客户端（HTTP 底层 + access_token + 上传图片 + 创建草稿）。

所有函数接收所需参数，不依赖全局变量，由 generate_wechat.py 编排层传入。
"""

import json
import sys
import urllib.error
import urllib.request
import uuid
from typing import Optional, Union

from utils import UA


def wechat_get(base_url: str, path: str) -> Optional[dict]:
    """微信 API GET 请求。"""
    url = f"{base_url}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[WARN] WeChat API GET failed: {path} - {e}", file=sys.stderr)
        return None


def wechat_post(base_url: str, path: str, payload, content_type: str = "application/json") -> Optional[dict]:
    """微信 API POST 请求，支持 dict / bytes / str。"""
    url = f"{base_url}{path}"
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


def get_access_token(base_url: str, appid: str, appsecret: str) -> Optional[str]:
    """获取微信 access_token。"""
    resp = wechat_get(
        base_url,
        f"/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    )
    if not resp or "access_token" not in resp:
        print("[ERROR] Failed to get WeChat access_token", file=sys.stderr)
        return None
    token = resp["access_token"]
    print(f"[INFO] Got access_token (expires in {resp.get('expires_in', '?')}s)")
    return token


def upload_image(base_url: str, token: str, image_bytes: bytes) -> Optional[str]:
    """上传图片为永久素材，返回 media_id。"""
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

    url = f"{base_url}/cgi-bin/material/add_material?access_token={token}&type=image"
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
            print(f"[INFO] Cover image uploaded - media_id: {data['media_id']}")
            return data["media_id"]
        print(f"[WARN] Image upload failed: {data}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] Image upload error: {e}", file=sys.stderr)
        return None


def create_draft(
    base_url: str,
    token: str,
    thumb_media_id: str,
    title: str,
    content: str,
    digest: str,
    source_url: str,
    author: str,
) -> bool:
    """创建微信公众号草稿。"""
    payload = {
        "articles": [
            {
                "title": title,
                "thumb_media_id": thumb_media_id,
                "author": author,
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
        base_url,
        f"/cgi-bin/draft/add?access_token={token}",
        payload,
    )
    if resp and "media_id" in resp:
        print(f"[INFO] Draft created - media_id: {resp['media_id']}")
        return True
    print(f"[ERROR] Draft creation failed: {resp}", file=sys.stderr)
    return False
