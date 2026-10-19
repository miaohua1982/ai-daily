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


# 【安全修复标识｜2026-10-19｜微信日志脱敏】错误只记录接口路径、异常类型及数字错误码。
# 禁止打印查询参数、str(error)、errmsg 或完整响应：其中可能回显 AppSecret/token。
def _log_api_failure(operation: str, *, error=None, response=None, level: str = "WARN") -> None:
    details = []
    if error is not None:
        details.append(f"error={type(error).__name__}")
        if isinstance(error, urllib.error.HTTPError) and type(error.code) is int:
            details.append(f"http_status={error.code}")
    if isinstance(response, dict):
        code = response.get("errcode")
        # 仅允许整数，避免服务端将凭证放入错误码字段后再次写入日志。
        if type(code) is int:
            details.append(f"errcode={code}")
    suffix = " " + " ".join(details) if details else ""
    print(f"[{level}] WeChat {operation} failed{suffix}", file=sys.stderr)


def wechat_get(base_url: str, path: str) -> Optional[dict]:
    """微信 API GET 请求。"""
    url = f"{base_url}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        # 【安全修复】token 请求的查询参数含 AppSecret，异常文本也可能带完整 URL。
        endpoint = path.split("?", 1)[0].split("#", 1)[0]
        _log_api_failure(f"GET {endpoint}", error=e)
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
        # 【安全修复】HTTP 错误响应体可能回显 access_token，不打印原始内容。
        endpoint = path.split("?", 1)[0].split("#", 1)[0]
        _log_api_failure(f"POST {endpoint}", error=e)
        return None
    except Exception as e:
        endpoint = path.split("?", 1)[0].split("#", 1)[0]
        _log_api_failure(f"POST {endpoint}", error=e)
        return None


def get_access_token(base_url: str, appid: str, appsecret: str) -> Optional[str]:
    """获取微信 access_token。"""
    resp = wechat_get(
        base_url,
        f"/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    )
    if not resp or "access_token" not in resp:
        # 【安全修复】业务错误也只记录数字 errcode，不输出 errmsg/完整响应。
        _log_api_failure("GET /cgi-bin/token", response=resp, level="ERROR")
        return None
    token = resp["access_token"]
    # 【安全修复】成功日志仅允许数字有效期，不回显服务端的任意字符串字段。
    expires_in = resp.get("expires_in")
    safe_expiry = expires_in if type(expires_in) is int else "?"
    print(f"[INFO] Got access_token (expires in {safe_expiry}s)")
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
        _log_api_failure("POST /cgi-bin/material/add_material", response=data)
        return None
    except Exception as e:
        _log_api_failure("POST /cgi-bin/material/add_material", error=e)
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
    _log_api_failure("POST /cgi-bin/draft/add", response=resp, level="ERROR")
    return False
