# ======================================================================
# 【修复回归标识｜2026-10-18｜新增】
# 文件：test/test_translation_alignment.py
# 修改原因：防止模型漏译、乱序、重复/非法 ID 或错误字段造成论文译文错配。
# 覆盖真实解析与关联链路，只模拟 HTTP 响应；不访问网络或写入推送文件。
# ======================================================================
"""按批次内整数 ID 关联译文的契约回归。"""
import importlib
import json
from unittest.mock import Mock
import pytest

p = importlib.import_module('src.papers.fetcher')

@pytest.mark.parametrize('entries,expected', [
    ([{'id':0,'title_zh':'第一篇'},{'id':1,'title_zh':'第二篇'}], {0:{'title_zh':'第一篇'},1:{'title_zh':'第二篇'}}),
    ([{'id':1,'title_zh':'第二篇'},{'id':0,'title_zh':'第一篇'}], {0:{'title_zh':'第一篇'},1:{'title_zh':'第二篇'}}),
    ([{'id':1,'title_zh':'第二篇'}], {1:{'title_zh':'第二篇'}}),
    ([{'id':0,'summary_zh':'第一篇摘要'}], {0:{'summary_zh':'第一篇摘要'}}),
    ([], {}),
    ([{'title_zh':'无 ID'},{'id':1,'title_zh':'第二篇'}], {1:{'title_zh':'第二篇'}}),
    ([{'id':'0','title_zh':'字符串 ID'}], {}),
    ([{'id':0.0,'title_zh':'浮点 ID'}], {}),
    ([{'id':True,'title_zh':'布尔 ID'},{'id':False,'title_zh':'布尔 ID'}], {}),
    ([{'id':-1,'title_zh':'负数 ID'},{'id':2,'title_zh':'越界 ID'}], {}),
    ([None, 'bad', 2, [], {'id':1,'title_zh':'第二篇'}], {1:{'title_zh':'第二篇'}}),
    ([{'id':0,'title_zh':'首次'},{'id':0,'title_zh':'重复覆盖'},{'id':1,'title_zh':'第二篇'}], {0:{'title_zh':'首次'},1:{'title_zh':'第二篇'}}),
    ([{'id':0,'title_zh':None,'summary_zh':'有效摘要'},{'id':1,'title_zh':'第二篇'}], {0:{'summary_zh':'有效摘要'},1:{'title_zh':'第二篇'}}),
    ([{'id':0,'title_zh':'有效标题','summary_zh':[]},{'id':1,'title_zh':'第二篇'}], {0:{'title_zh':'有效标题'},1:{'title_zh':'第二篇'}}),
    ([{'id':0,'title_zh':1,'summary_zh':{}},{'id':1,'title_zh':'第二篇'}], {1:{'title_zh':'第二篇'}}),
    ([{'id':0,'title_zh':'  ','summary_zh':'\n'}], {}),
    ([{'id':0,'title_zh':'  中文  ','summary_zh':' 摘要 '}], {0:{'title_zh':'中文','summary_zh':'摘要'}}),
    ([{'id':0,'title_zh':None},{'id':0,'title_zh':'重复结果'}], {}),
])
def test_translation_matches_id_not_position(monkeypatch, response, config, item, entries, expected):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake')
    config['translation']['batch_size'] = 2
    originals = [dict(item, id=f'original-{i}', title=f'English {i}', summary=f'Original summary {i}') for i in range(2)]
    before = [dict(it) for it in originals]
    opener = Mock()
    opener.open.return_value = response({'choices':[{'message':{'content':json.dumps({'translations':entries})}}]})
    monkeypatch.setattr(p.urllib.request, 'build_opener', Mock(return_value=opener))
    result = p.translate_papers(originals, config)
    assert result is originals
    for idx, paper in enumerate(result):
        assert {field:paper[field] for field in before[idx]} == before[idx]
        actual = {field:paper[field] for field in ('title_zh','summary_zh') if field in paper}
        assert actual == expected.get(idx, {})
    payload = json.loads(opener.open.call_args.args[0].data)
    assert '"id": 0' in payload['messages'][1]['content']
    assert '"id": 1' in payload['messages'][1]['content']

@pytest.mark.parametrize('entries,warning', [
    ([{'title_zh':'无编号'}], 'Invalid translation id'),
    ([{'id':'0'}], 'Invalid translation id'),
    ([{'id':0},{'id':0}], 'Duplicate translation id'),
    ([None], 'not an object'),
    ([{'id':0,'summary_zh':None}], 'invalid summary_zh'),
])
def test_invalid_entries_emit_warning(capsys, entries, warning):
    p._parse_translation_response(json.dumps(entries), 2)
    assert warning in capsys.readouterr().err


def test_batch_local_ids_and_failure_isolation(monkeypatch, response, config, item, capsys):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake')
    config['translation']['batch_size'] = 2
    items = [dict(item, id=str(i), title=f'Original {i}') for i in range(5)]
    # 第一批只返回编号 1，第二批异常，第三批编号重新从 0 开始。
    opener = Mock()
    opener.open.side_effect = [
        response({'choices':[{'message':{'content':'[{"id":1,"title_zh":"论文一"}]'}}]}),
        TimeoutError('second batch failed'),
        response({'choices':[{'message':{'content':'[{"id":0,"title_zh":"论文四"}]'}}]}),
    ]
    monkeypatch.setattr(p.urllib.request, 'build_opener', Mock(return_value=opener))
    result = p.translate_papers(items, config)
    assert [it.get('title_zh') for it in result] == [None,'论文一',None,None,'论文四']
    assert [it['title'] for it in result] == [f'Original {i}' for i in range(5)]
    output = capsys.readouterr()
    assert 'missing id 0' in output.err
    assert 'Translated 2/5 papers' in output.err


def test_empty_translation_does_not_count_as_success(monkeypatch, response, config, item, capsys):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'fake')
    opener = Mock()
    opener.open.return_value = response({'choices':[{'message':{'content':'[{"id":0,"title_zh":"  "}]'}}]})
    monkeypatch.setattr(p.urllib.request, 'build_opener', Mock(return_value=opener))
    result = p.translate_papers([dict(item)], config)
    assert 'title_zh' not in result[0]
    assert 'Translated 0/1 papers' in capsys.readouterr().err
