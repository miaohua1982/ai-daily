# ======================================================================
# 【安全修复回归标识｜2026-10-19｜新增】
# 文件：test/test_wechat_log_redaction.py
# 修改原因：请求路径、异常文本、HTTP 响应体及业务 errmsg 均可能回显凭证。
# 使用虚构 AppSecret/token 验证日志不泄露；HTTP 全部模拟，不调用真实微信接口。
# ======================================================================
"""微信客户端日志采用白名单字段，不记录查询参数或任意错误文本。"""
import importlib
import io
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
import pytest

api = importlib.import_module('src.wechat.api')
SECRET = 'FAKE_SECRET_DO_NOT_LOG'
TOKEN = 'FAKE_TOKEN_DO_NOT_LOG'
APPID = 'FAKE_APPID_DO_NOT_LOG'


def assert_no_credentials(capsys):
    captured = capsys.readouterr()
    output = captured.out + captured.err
    for credential in (SECRET, TOKEN, APPID):
        assert credential not in output
    return output


@pytest.mark.parametrize('operation', ['get','post','image'])
@pytest.mark.parametrize('error_kind', ['timeout','url','http'])
def test_transport_errors_do_not_log_credentials(monkeypatch, capsys, operation, error_kind):
    full_url = f'https://example.invalid/cgi-bin/token?appid={APPID}&secret={SECRET}&access_token={TOKEN}'
    message = f'failed request {full_url}'
    if error_kind == 'http':
        error = HTTPError(full_url, 401, message, {}, io.BytesIO(message.encode()))
    elif error_kind == 'url':
        error = URLError(message)
    else:
        error = TimeoutError(message)
    monkeypatch.setattr(api.urllib.request, 'urlopen', Mock(side_effect=error))
    if operation == 'get':
        assert api.get_access_token('https://example.invalid', APPID, SECRET) is None
        endpoint = '/cgi-bin/token'
    elif operation == 'post':
        assert api.wechat_post('https://example.invalid', f'/cgi-bin/draft/add?access_token={TOKEN}#fragment', {'content':SECRET}) is None
        endpoint = '/cgi-bin/draft/add'
    else:
        assert api.upload_image('https://example.invalid', TOKEN, b'fake-image') is None
        endpoint = '/cgi-bin/material/add_material'
    output = assert_no_credentials(capsys)
    assert endpoint in output
    assert f'error={type(error).__name__}' in output
    if error_kind == 'http':
        assert 'http_status=401' in output


@pytest.mark.parametrize('operation', ['token','image','draft'])
@pytest.mark.parametrize('code', [40001, SECRET, None, True])
def test_business_errors_only_log_numeric_code(monkeypatch, response, capsys, operation, code):
    data = {'errcode':code, 'errmsg':f'secret={SECRET} access_token={TOKEN}', 'debug':APPID}
    if operation == 'token':
        monkeypatch.setattr(api,'wechat_get',Mock(return_value=data))
        assert api.get_access_token('https://example.invalid',APPID,SECRET) is None
    elif operation == 'image':
        monkeypatch.setattr(api.urllib.request,'urlopen',Mock(return_value=response(data)))
        assert api.upload_image('https://example.invalid',TOKEN,b'image') is None
    else:
        monkeypatch.setattr(api,'wechat_post',Mock(return_value=data))
        assert api.create_draft('https://example.invalid',TOKEN,'image','title','content','digest','https://source','author') is False
    output = assert_no_credentials(capsys)
    assert ('errcode=' in output) == (type(code) is int)
    if type(code) is int:
        assert f'errcode={code}' in output


@pytest.mark.parametrize('expires', [7200, SECRET, None, True])
def test_success_log_does_not_echo_token_or_arbitrary_fields(monkeypatch,capsys,expires):
    monkeypatch.setattr(api,'wechat_get',Mock(return_value={'access_token':TOKEN,'expires_in':expires,'debug':SECRET}))
    assert api.get_access_token('https://example.invalid',APPID,SECRET) == TOKEN
    output=assert_no_credentials(capsys)
    assert f'expires in {7200 if type(expires) is int else "?"}s' in output


def test_invalid_json_does_not_echo_response(monkeypatch,response,capsys):
    monkeypatch.setattr(api.urllib.request,'urlopen',Mock(return_value=response(f'{SECRET} {TOKEN}'.encode())))
    assert api.wechat_get('https://example.invalid',f'/cgi-bin/token?secret={SECRET}') is None
    output=assert_no_credentials(capsys)
    assert 'error=JSONDecodeError' in output


def test_path_fragment_and_query_are_removed(monkeypatch,capsys):
    monkeypatch.setattr(api.urllib.request,'urlopen',Mock(side_effect=RuntimeError(SECRET)))
    assert api.wechat_get('https://example.invalid',f'/cgi-bin/token#{SECRET}?access_token={TOKEN}') is None
    assert 'GET /cgi-bin/token failed' in assert_no_credentials(capsys)
