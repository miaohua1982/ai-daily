#!/usr/bin/env python3
"""
WeChat Official Account - Video Channel (Stage 1: upload)

公众号「第二渠道 · 视频」上传脚本，与现有图文草稿逻辑完全独立：
  - 不走草稿箱（draft/add），直接以「永久素材」上传视频
  - 对应官方接口（用户从官网查到的 curl）：
      curl ".../material/add_material?access_token=TOKEN&type=video" \
        -F media=@file -F description='{"title":T,"introduction":I}'
  - 复用 src/wechat/api.get_access_token 取 token

本步只做：取 token → 上传视频永久素材 → 打印 media_id（并缓存到
archive/wechat_video/<date>.json，供后续审阅/发布阶段复用）。

审阅（preview，推给自己）与发布（sendall，群发）为后续阶段，本文件暂不包含。

运行（需配置 WECHAT_APPID / WECHAT_APPSECRET）：
  python generate_wechat_video.py --video path/to/video.mp4
  # 可选：--title "标题" --introduction "简介"
  # 或用环境变量 WECHAT_VIDEO_FILE 指定视频路径
"""

import os
import sys
import json
import uuid
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from utils import get_dot_env, load_config, get_now_date_str, UA
from src.wechat.api import get_access_token

# -- Configuration ---------------------------------------------------------
OUTPUT_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = OUTPUT_DIR / "config" / "wechat_config.yaml"

_env = get_dot_env()
_config = load_config(CONFIG_FILE)

WECHAT_BASE = _config["wechat_base"]
appid_env = _config["appid_env"]
appsecret_env = _config["appsecret_env"]
APPID = (os.environ.get(appid_env) or _env.get(appid_env, "")).strip()
APPSECRET = (os.environ.get(appsecret_env) or _env.get(appsecret_env, "")).strip()

# 默认视频路径（可被 --video 或环境变量 WECHAT_VIDEO_FILE 覆盖；留空则必须显式传 --video）
DEFAULT_VIDEO = os.environ.get("WECHAT_VIDEO_FILE", "")


def upload_video_material(base_url, token, video_path, title, introduction):
    """上传视频为永久素材，返回 media_id。

    对应官方接口（用户从官网查到的 curl）：
      curl ".../material/add_material?access_token=TOKEN&type=video" \
        -F media=@file -F description='{"title":T,"introduction":I}'
    """
    p = Path(video_path)
    if not p.is_file():
        print(f"[ERROR] Video file not found: {video_path}", file=sys.stderr)
        return None
    video_bytes = p.read_bytes()
    print(f"[INFO] Read video: {p.name} ({len(video_bytes) / 1024 / 1024:.1f} MB)")

    boundary = uuid.uuid4().hex
    desc = json.dumps({"title": title, "introduction": introduction}, ensure_ascii=False)

    # 第一段：media 文件
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{p.name}"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode("utf-8") + video_bytes + b"\r\n"
    # 第二段：description（JSON 字符串）
    body += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="description"\r\n'
        f"Content-Type: application/json\r\n\r\n"
        f"{desc}\r\n"
    ).encode("utf-8")
    body += f"--{boundary}--\r\n".encode("utf-8")

    url = f"{base_url}/cgi-bin/material/add_material?access_token={token}&type=video"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": UA,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Video upload HTTP {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERROR] Video upload error: {e}", file=sys.stderr)
        return None

    if "media_id" in data:
        print(f"[INFO] Video uploaded - media_id: {data['media_id']}")
        if data.get("url"):
            print(f"[INFO] Video URL: {data['url']}")
        return data["media_id"]
    print(f"[ERROR] Video upload failed: {data}", file=sys.stderr)
    return None


def save_media_cache(media_id, video_path, title, introduction):
    """把上传结果缓存到 archive/wechat_video/<date>.json，供审阅/发布阶段复用。"""
    date_str = get_now_date_str()
    cache_dir = OUTPUT_DIR / "archive" / "wechat_video"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{date_str}.json"
    payload = {
        "media_id": media_id,
        "video_path": str(video_path),
        "title": title,
        "introduction": introduction,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] media_id cached: {cache_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="WeChat video channel - upload stage")
    parser.add_argument("--video", help="path to the video file to upload")
    parser.add_argument("--title", help="video title (default: filename without extension)")
    parser.add_argument("--introduction", help="video introduction (default: 'ai-daily 视频渠道')")
    args = parser.parse_args()

    # 视频路径：--video > 环境变量 WECHAT_VIDEO_FILE > 默认
    video_path = args.video or DEFAULT_VIDEO
    if not video_path:
        print("usage: python generate_wechat_video.py --video <path> [--title T] [--introduction I]")
        return 2

    # 凭据检查（发布阶段必须有凭据）
    if not APPID or not APPSECRET:
        print("[SKIP] WECHAT_APPID or WECHAT_APPSECRET not set - cannot upload")
        return 1

    # 标题/简介默认值
    stem = Path(video_path).stem
    title = args.title or stem
    introduction = args.introduction or "ai-daily 视频渠道"

    # 阶段一·取 token（复用现有 get_access_token）
    print("[INFO] Getting WeChat access token...")
    token = get_access_token(WECHAT_BASE, APPID, APPSECRET)
    if not token:
        return 1

    # 阶段一·上传视频永久素材（material/add_material?type=video）
    print(f"[INFO] Uploading video: {video_path}")
    media_id = upload_video_material(WECHAT_BASE, token, video_path, title, introduction)
    if not media_id:
        return 1

    # 缓存 media_id，供后续 审阅(preview) / 发布(sendall) 阶段直接复用，不必重复上传
    save_media_cache(media_id, video_path, title, introduction)

    print("[INFO] Stage 1 (upload) done. media_id above - next: review(preview) / publish(sendall).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
