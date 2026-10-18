# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/conftest.py
# 修改内容及原因：隔离 API 凭证，禁止未模拟的 HTTP、socket 和子进程；提供公共样本。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""白盒测试隔离：禁止真实网络、进程和密钥读取；文件仅写入 pytest 临时目录。"""
import importlib
import io
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import Mock
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class Response:
    def __init__(self, data):
        self.data = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.data

@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    attempted = []
    def forbidden(*args, **kwargs):
        attempted.append('network/subprocess')
        raise AssertionError('Test attempted a real network or subprocess operation')
    monkeypatch.setattr(urllib.request, 'urlopen', forbidden)
    monkeypatch.setattr(urllib.request.OpenerDirector, 'open', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    monkeypatch.setattr(subprocess, 'check_output', forbidden)
    monkeypatch.setattr(time, 'sleep', Mock())
    u = importlib.import_module('utils.utils')
    monkeypatch.setattr(u, '_dot_env_cache', {})
    for key in ('EMBEDDING_API_KEY','DEEPSEEK_API_KEY','WECHAT_APPID','WECHAT_APPSECRET','WECHAT_LOCAL_ONLY','WECHAT_VIDEO_FILE'):
        monkeypatch.delenv(key, raising=False)
    yield
    assert not attempted, 'An unstubbed external operation was attempted'

@pytest.fixture
def response(): return Response

@pytest.fixture
def item():
    return {'id':'p1','title':'A meaningful title','summary':'Detailed useful summary ' * 8,
            'source':'arxiv','sourceName':'arxiv','url':'https://example.org/p1',
            'sourceUrl':'https://example.org/p1','category':'模型发布/更新',
            'publishedAt':'2026-10-17T10:00:00Z','publishTime':'2026-10-17T10:00:00Z',
            'source_api':'arxiv','score':80,'selected':True}

@pytest.fixture
def config():
    from utils import load_config
    return load_config(ROOT/'config/papers_config.yaml')
