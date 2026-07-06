#!/usr/bin/env python3
"""
Utils — 公共工具函数

包含:
  - load_dot_env:      简易 .env 解析（无外部依赖）
  - load_config:       YAML 配置加载（PyYAML 优先，fallback 纯标准库）
  - api_get:           HTTP GET + 指数退避重试（共用）
  - get_embeddings:    批量获取文本 embedding（OpenAI 兼容接口，支持分批）
  - cosine_similarity: 余弦相似度计算
  - dedup_data:        URL 去重 + 语义去重（papers / news 共用）
  - write_files:       写入主页面和归档文件（共用）
  - git_commit:        git add/commit/push（共用）
"""

import os
import sys
import json
import subprocess
import time
import random
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── .env 解析 ──────────────────────────────────────────────────

def load_dot_env(path: Path) -> Dict[str, str]:
    """
    简易 .env 文件解析器，无需外部依赖。

    支持:
    - 注释（以 # 开头的行）
    - 引号值（单引号或双引号会被去除）
    - 空行（自动忽略）

    Args:
        path: .env 文件路径

    Returns:
        键值对字典
    """
    result: Dict[str, str] = {}

    if not path.is_file():
        return result

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value

    return result


# ── YAML 配置加载 ───────────────────────────────────────────────

def load_config(path: Path) -> Dict[str, any]:
    """
    加载 YAML 配置文件。优先使用 PyYAML，未安装时回退到纯标准库解析器。

    Args:
        path: YAML 文件路径

    Returns:
        配置字典；文件不存在或解析失败时返回空字典
    """
    if not path.is_file():
        return {}

    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass
    except Exception as e:
        print(f"[WARN] Failed to load YAML config {path}: {e}, using fallback parser", file=sys.stderr)
        return {}

    return _load_yaml_minimal(path)


def _is_quoted(s: str) -> bool:
    return (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'"))


def _split_key_value(s: str):
    """拆分 key: value，忽略引号内的冒号。"""
    in_quote = None
    for idx, ch in enumerate(s):
        if ch in ('"', "'"):
            if in_quote is None:
                in_quote = ch
            elif in_quote == ch:
                in_quote = None
        elif ch == ":" and in_quote is None:
            key = s[:idx].strip()
            val = s[idx + 1:].strip()
            return key, val
    return s, ""


def _parse_scalar(s: str):
    """解析 YAML 标量。"""
    s = s.strip()
    if not s:
        return None
    if _is_quoted(s):
        return s[1:-1]
    if s in ("true", "True", "yes", "on"):
        return True
    if s in ("false", "False", "no", "off"):
        return False
    if s in ("null", "None", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _load_yaml_minimal(path: Path) -> Dict[str, any]:
    """纯标准库 YAML 子集解析器，支持字典、列表、多行字符串。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    tokens = []
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        tokens.append((indent, line.strip()))

    def parse_block(i: int, base_indent: int):
        if i >= len(tokens):
            return None, i
        first_indent = tokens[i][0]
        if first_indent < base_indent:
            return None, i

        if tokens[i][1].startswith("- "):
            # 列表
            result = []
            while i < len(tokens):
                indent, content = tokens[i]
                if indent < first_indent:
                    break
                if indent > first_indent:
                    i += 1
                    continue
                if not content.startswith("- "):
                    break
                value_text = content[2:].strip()
                if value_text == "":
                    child, i = parse_block(i + 1, first_indent)
                    result.append(child if child is not None else None)
                elif ":" in value_text and not _is_quoted(value_text):
                    key, val = _split_key_value(value_text)
                    child_dict = {key: _parse_scalar(val)}
                    i += 1
                    # 解析同列表项下的 key-value 字段
                    while i < len(tokens):
                        ni, nc = tokens[i]
                        if ni <= first_indent:
                            break
                        if nc.startswith("- "):
                            break
                        if ":" in nc:
                            k, v = _split_key_value(nc)
                            if v == "|":
                                block_lines = []
                                i += 1
                                while i < len(tokens) and tokens[i][0] > ni:
                                    block_lines.append(tokens[i][1])
                                    i += 1
                                child_dict[k] = "\n".join(block_lines)
                            elif v == "":
                                child, i = parse_block(i + 1, ni)
                                child_dict[k] = child if child is not None else _parse_scalar(v)
                            else:
                                child_dict[k] = _parse_scalar(v)
                                i += 1
                        else:
                            i += 1
                    result.append(child_dict)
                else:
                    result.append(_parse_scalar(value_text))
                    i += 1
            return result, i
        else:
            # 字典
            result = {}
            while i < len(tokens):
                indent, content = tokens[i]
                if indent < first_indent:
                    break
                if indent > first_indent:
                    i += 1
                    continue
                if ":" not in content:
                    i += 1
                    continue
                key, val = _split_key_value(content)
                if val == "|":
                    block_lines = []
                    i += 1
                    while i < len(tokens) and tokens[i][0] > first_indent:
                        block_lines.append(tokens[i][1])
                        i += 1
                    result[key] = "\n".join(block_lines)
                    continue
                if val == "":
                    child, i = parse_block(i + 1, first_indent)
                    result[key] = child if child is not None else _parse_scalar(val)
                else:
                    result[key] = _parse_scalar(val)
                    i += 1
            return result, i

    if not tokens:
        return {}
    result, _ = parse_block(0, -1)
    return result if result is not None else {}


# ── Embedding 相似度工具 ───────────────────────────────────────

def get_embeddings(
    texts: List[str],
    api_key: str,
    base_url: str,
    model: str,
    batch_size: int = 10,
) -> Optional[List[List[float]]]:
    """
    批量获取文本 embedding，使用 OpenAI 兼容接口。

    部分模型（如阿里 Qwen）单次请求最多支持 batch_size 条文本，
    因此分批发送请求，结果按顺序拼接后返回。

    Args:
        texts:      待向量化的文本列表
        api_key:    API Key
        base_url:   OpenAI 兼容接口地址（如 https://api.openai.com/v1）
        model:      embedding 模型名
        batch_size: 单次请求最大文本数（默认 10）

    Returns:
        向量列表 list[list[float]]，与输入文本一一对应；
        失败时返回 None。
    """
    if not texts:
        return []

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{base_url.rstrip('/')}/embeddings"
    all_embeddings: List[List[float]] = []
    total = len(texts)

    # 显式禁用代理，与 api_get 保持一致
    embed_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    for start in range(0, total, batch_size):
        batch = list(texts[start:start + batch_size])
        payload = {"model": model, "input": batch}
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        try:
            with embed_opener.open(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            batch_emb = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(batch_emb)
        except Exception as e:
            print(
                f"[WARN] get_embeddings batch {start}-{start + len(batch)} failed: {e}",
                file=sys.stderr,
            )
            return None

    return all_embeddings


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_dedup(
    items: List[dict],
    threshold: float,
    api_key: str,
    base_url: str,
    model: str,
    batch_size: int = 10,
    title_key: str = "title",
) -> List[dict]:
    """
    对条目列表做语义去重。

    计算所有条目标题的 embedding，两两比较余弦相似度，
    相似度 >= threshold 时移除后者（保留第一个）。

    Args:
        items:      待去重的条目列表（每个条目为 dict，需包含 title_key 字段）
        threshold:  余弦相似度阈值（0.0-1.0），>= 此值视为重复
        api_key:    embedding API Key
        base_url:   OpenAI 兼容接口地址
        model:      embedding 模型名
        batch_size: 单次请求最大文本数
        title_key:  条目中标题对应的字段名（默认 "title"）

    Returns:
        去重后的条目列表；如果 embedding API 不可用则返回原始列表。
    """
    if len(items) <= 1:
        return items

    titles = [it.get(title_key, "") for it in items]
    embeddings = get_embeddings(titles, api_key, base_url, model, batch_size)

    if embeddings is None:
        print("[WARN] Semantic dedup skipped: embedding API unavailable", file=sys.stderr)
        return items

    if len(embeddings) != len(items):
        print(
            f"[WARN] Semantic dedup skipped: embedding count mismatch "
            f"({len(embeddings)} vs {len(items)})",
            file=sys.stderr,
        )
        return items

    keep = [True] * len(items)
    removed = 0
    for i in range(len(items)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(items)):
            if not keep[j]:
                continue
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                keep[j] = False
                removed += 1
                print(
                    f"[INFO] Semantic dedup: drop '{titles[j][:50]}...' "
                    f"(sim={sim:.3f} with '{titles[i][:50]}...')",
                    file=sys.stderr,
                )

    result = [items[i] for i in range(len(items)) if keep[i]]
    if removed > 0:
        print(f"[INFO] Semantic dedup: removed {removed} duplicate(s)", file=sys.stderr)
    return result


def dedup_data(
    items: List[dict],
    config: Optional[Dict] = None,
    dot_env: Optional[Dict[str, str]] = None,
) -> List[dict]:
    """URL 去重 + 语义去重（papers / news 共用）。

    1. URL 去重：按 ``sourceUrl``（优先）→ ``url`` 去重，去掉 URL fragment
    2. 语义去重：若 ``config.semantic_dedup.enabled``，调用 embedding API 做语义去重

    Args:
        items:   待去重的条目列表（每条需含 ``sourceUrl`` 或 ``url``）
        config:  配置字典（可选，含 ``semantic_dedup`` 段）
        dot_env: .env 解析结果（可选，用于注入 embedding API Key）

    Returns:
        去重后的条目列表
    """
    # 1. URL 去重
    seen = set()
    url_deduped = []
    for p in items:
        url = p.get("sourceUrl") or p.get("url") or ""
        key = urllib.parse.urldefrag(url)[0]
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        url_deduped.append(p)

    # 2. 语义去重
    sem_cfg = (config or {}).get("semantic_dedup", {})
    if sem_cfg.get("enabled", False):
        api_key_env = sem_cfg.get("api_key_env", "EMBEDDING_API_KEY")
        api_key = os.environ.get(api_key_env) or (dot_env or {}).get(api_key_env, "")
        base_url = sem_cfg.get("base_url", "")
        model = sem_cfg.get("model", "text-embedding-3-small")
        threshold = float(sem_cfg.get("threshold", 0.85))
        batch_size = int(sem_cfg.get("batch_size", 10))

        if api_key and base_url:
            before = len(url_deduped)
            url_deduped = semantic_dedup(url_deduped, threshold, api_key, base_url, model, batch_size)
            if len(url_deduped) != before:
                print(f"[INFO] Semantic dedup: {before} -> {len(url_deduped)}", file=sys.stderr)
        else:
            print("[WARN] Semantic dedup enabled but API key or base_url not configured", file=sys.stderr)

    return url_deduped


# ── HTML 转义（共用）───────────────────────────────────────────

def esc_html(s):
    """转义 HTML 文本中的 &, <, >。"""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(s):
    """转义 HTML 属性中的 &, "。"""
    return str(s).replace("&", "&amp;").replace('"', "&quot;")


# ── HTTP GET + 指数退避重试（共用）───────────────────────────

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def api_get(path, base_url, max_retries=3):
    """
    从指定 API 获取数据，失败时进行指数退避 + jitter 重试。

    Args:
        path:        API 路径（如 "/daily/2025-01-01"）
        base_url:    API 基地址（如 "https://aihot.virxact.com/api/public"）
        max_retries: 最大重试次数

    Returns:
        解析后的 JSON dict；失败时返回 None。
    """
    url = f"{base_url}{path}"

    # 使用 ProxyHandler({}) 显式禁用代理，避免 urllib 自动读取系统代理配置
    # （某些环境（如 CI runner、公司网络）的系统代理可能指向不可达地址，
    #   导致所有 HTTPS 请求都变成 "Connection refused"）
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with opener.open(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"[WARN] HTTP {e.code} for {path} (attempt {attempt+1}/{max_retries})", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Failed to fetch {path} (attempt {attempt+1}/{max_retries}): {e}", file=sys.stderr)

        if attempt < max_retries - 1:
            base_backoff = 2 ** attempt
            backoff = random.uniform(0, base_backoff)
            print(f"[INFO] Retrying {path} after {backoff:.1f}s (jitter)...", file=sys.stderr)
            time.sleep(backoff)

    return None


# ── 日期过滤（共用）─────────────────────────────────────────

def filter_by_date(
    items: List[Dict[str, Any]],
    target_date: str,
    days_back: int,
) -> List[Dict[str, Any]]:
    """按 publishedAt 过滤，只保留 days_back 范围内的数据。

    解析 ``publishedAt`` 中的 ISO 8601 时间戳（取前 19 位），
    与 cutoff 日期比较，过期的不入列。
    无日期或解析失败的条目统一丢弃。

    Args:
        items:       待过滤的条目列表
        target_date: 目标日期（格式 ``YYYY-MM-DD``）
        days_back:   截止天数，0 表示不过滤

    Returns:
        过滤后的条目列表
    """
    if not days_back:
        return items

    cutoff_dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=days_back)
    filtered: List[Dict[str, Any]] = []
    for item in items:
        pub_str = item.get("publishedAt", "")
        if not pub_str:
            continue
        try:
            pub_dt = datetime.strptime(pub_str[:19], "%Y-%m-%dT%H:%M:%S")
            if pub_dt >= cutoff_dt:
                filtered.append(item)
        except ValueError:
            continue
    return filtered


# ── 文件写入 & Git 提交（共用）───────────────────────────────

def write_files(html: str, date_str: str, index_file: Path, archive_dir: Path):
    """
    写入主页面和归档文件。

    Args:
        html:        生成的 HTML 内容
        date_str:    日期字符串（用于归档文件名）
        index_file:  主页面路径（如 Path("daily_news.html")）
        archive_dir: 归档目录路径（如 Path("news-archive")）
    """
    archive_dir.mkdir(parents=True, exist_ok=True)

    index_file.write_text(html, encoding="utf-8")
    print(f"[INFO] Written {index_file.name} ({len(html)} bytes)")

    archive_file = archive_dir / f"{date_str}.html"
    archive_file.write_text(html, encoding="utf-8")
    print(f"[INFO] Archived to {archive_file}")


def git_commit(date_str: str, add_files: List[str], commit_label: str, output_dir: Path):
    """
    git add / commit / push。

    Args:
        date_str:      日期字符串
        add_files:     git add 的文件路径列表（相对 output_dir）
        commit_label:  commit message 中的描述词（如 "daily dashboard"）
        output_dir:    git 操作的工作目录
    """
    cwd = str(output_dir)
    subprocess.run(["git", "add"] + add_files, cwd=cwd, check=False)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd, capture_output=True)
    if result.returncode != 0:
        msg = f"chore: update {commit_label} {date_str}"
        subprocess.run(["git", "commit", "-m", msg], cwd=cwd, check=False)
        push_result = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
        if push_result.returncode == 0:
            print(f"[INFO] Committed and pushed: {msg}")
        else:
            print(f"[WARN] Commit done, but push failed: {push_result.stderr}")
    else:
        print("[INFO] No changes to commit")
