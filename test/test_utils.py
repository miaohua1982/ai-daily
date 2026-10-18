# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_utils.py
# 修改内容及原因：覆盖配置解析、Embedding、语义去重、HTTP 重试、日期与模拟 Git 分支。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""配置、HTTP 重试、语义去重、日期及 Git 分支；所有外部结果显式模拟。"""
import builtins
import importlib
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError
import pytest
u = importlib.import_module('utils.utils')

def test_dotenv(tmp_path, monkeypatch):
    p=tmp_path/'env'
    assert u.load_dot_env(p)=={}
    p.write_text('# comment\n\n KEY = "value"\nS=\'quoted\'\nbadline\n')
    assert u.load_dot_env(p)=={'KEY':'value','S':'quoted'}
    monkeypatch.setattr(u,'_dot_env_cache',None)
    loader=Mock(return_value={'ONLY':'fake'})
    monkeypatch.setattr(u,'load_dot_env',loader)
    assert u.get_dot_env()==u.get_dot_env()=={'ONLY':'fake'}
    loader.assert_called_once()

@pytest.mark.parametrize('text,value',[('',None),('"a:b"','a:b'),("'x'",'x'),('true',True),('False',False),('null',None),('12',12),('1.25',1.25),('word','word')])
def test_scalars(text,value): assert u._parse_scalar(text)==value

@pytest.mark.parametrize('text,value', [('"a:b": value',('"a:b"','value')),('key: "a:b"',('key','"a:b"')),('bare',('bare',''))])
def test_split(text,value): assert u._split_key_value(text)==value

def test_config_loaders(tmp_path,monkeypatch):
    p=tmp_path/'c.yaml'
    assert u.load_config(p)=={}
    p.write_text('a: 1\n')
    assert u.load_config(p)=={'a':1}
    p.write_text('')
    assert u.load_config(p)=={}
    p.write_text('a: [\n')
    assert u.load_config(p)=={}
    p.write_text('a: true\n')
    original=builtins.__import__
    def missing(name,*a,**kw):
        if name=='yaml': raise ImportError('simulate no PyYAML')
        return original(name,*a,**kw)
    monkeypatch.setattr(builtins,'__import__',missing)
    assert u.load_config(p)=={'a':True}

@pytest.mark.parametrize('text,expected',[
    ('# comment\n\n',{}),
    ('root:\n  list:\n    - a\n    - b\nflag: false\n',{'root':{'list':['a','b']},'flag':False}),
    ('items:\n  - name: one\n    count: 2\n    child:\n      flag: true\n  - name: two\n    body: |\n      hello\n      world\n',{'items':[{'name':'one','count':2,'child':{'flag':True}},{'name':'two','body':'hello\nworld'}]}),
    ('message: |\n  first\n  second\nempty:\n',{'message':'first\nsecond','empty':None}),
])
def test_minimal_yaml(tmp_path,text,expected):
    p=tmp_path/'minimal.yaml';p.write_text(text)
    assert u._load_yaml_minimal(p)==expected

@pytest.mark.parametrize('errors',[False,True])
def test_embeddings(monkeypatch,response,errors):
    assert u.get_embeddings([],'k','https://example.org','m')==[]
    opener=Mock()
    opener.open.side_effect=RuntimeError('offline') if errors else [response({'data':[{'embedding':[1,0]}]}),response({'data':[{'embedding':[0,1]}]})]
    monkeypatch.setattr(u.urllib.request,'build_opener',Mock(return_value=opener))
    result=u.get_embeddings(['a','b'],'fake','https://example.org','m',1)
    assert result is None if errors else result==[[1,0],[0,1]]
    assert json.loads(opener.open.call_args_list[0].args[0].data)['input']==['a']

def test_similarity_and_semantic(monkeypatch):
    assert u.cosine_similarity([1,0],[1,0])==1
    assert u.cosine_similarity([0,0],[1,0])==0
    assert u.semantic_dedup([],0.75,'k','u','m')==[]
    items=[{'title':str(i)} for i in range(4)]
    for embeddings,expected in [(None,items),([[1,0]],items),([[1,0],[1,0],[1,0],[0,1]],[items[0],items[3]]),([[1,0],[0,1],[-1,0],[0,-1]],items)]:
        monkeypatch.setattr(u,'get_embeddings',Mock(return_value=embeddings))
        assert u.semantic_dedup(items,0.75,'k','u','m')==expected

@pytest.mark.parametrize('enabled,key,shrink',[(False,False,False),(True,False,False),(True,True,False),(True,True,True)])
def test_dedup(monkeypatch,enabled,key,shrink):
    a={'title':'a','url':'https://x/a#one'}; b={'title':'b','sourceUrl':'https://x/a#two'}; c={'title':'c','mobileUrl':'https://x/c'}
    items=[a,b,c,{}]
    if key: monkeypatch.setenv('EMBEDDING_API_KEY','fake')
    sem=Mock(side_effect=lambda values,*args: values[:1] if shrink else values)
    monkeypatch.setattr(u,'semantic_dedup',sem)
    result=u.dedup_data(items,{'semantic_dedup':{'enabled':enabled,'base_url':'https://example.org'}})
    assert result==([a] if shrink else [a,c,{}])
    assert sem.call_count==int(enabled and key)

def test_dates_escape_write(tmp_path):
    assert u.get_now_date_str('2026-10-18')=='2026-10-18'
    assert len(u.get_now_date_str())==10
    recent={'publishedAt':'2026-10-17T00:00:00Z'}
    data=[recent,{'publishedAt':'2025-01-01T00:00:00Z'},{},{'publishedAt':'bad'}]
    assert u.filter_by_date(data,'2026-10-18',5)==[recent]
    assert u.filter_by_date(data,'2026-10-18',0) is data
    assert u.esc_html('<a&>')=='&lt;a&amp;&gt;'
    assert u.esc_attr('"&')=='&quot;&amp;'
    u.write_files('content','2026-10-18',tmp_path/'index.html',tmp_path/'archive')
    assert (tmp_path/'index.html').read_text()==(tmp_path/'archive/2026-10-18.html').read_text()=='content'

@pytest.mark.parametrize('mode',['success','http','error','retry'])
def test_api_get(monkeypatch,response,mode):
    error=HTTPError('https://example.org',503,'unavailable',{},io.BytesIO(b'failed')) if mode=='http' else TimeoutError('timeout')
    opener=Mock();opener.open.side_effect=[response({'ok':True})] if mode=='success' else [error,response({'ok':True})] if mode=='retry' else [error,error]
    monkeypatch.setattr(u.urllib.request,'build_opener',Mock(return_value=opener))
    assert u.api_get('/path','https://example.org',2)==({'ok':True} if mode in ('success','retry') else None)

@pytest.mark.parametrize('changed,push_ok',[(False,True),(True,True),(True,False)])
def test_git_operations_only_mocked(monkeypatch,tmp_path,changed,push_ok):
    run=Mock(side_effect=[SimpleNamespace(returncode=0),SimpleNamespace(returncode=int(changed)),SimpleNamespace(returncode=0),SimpleNamespace(returncode=0 if push_ok else 1,stderr='rejected')])
    monkeypatch.setattr(u.subprocess,'run',run)
    u.git_commit('2026-10-18',['one.html'],'test',tmp_path)
    assert run.call_count==(4 if changed else 2)
    assert run.call_args_list[0].args[0]==['git','add','one.html']

def test_minimal_yaml_empty_nested_mapping(tmp_path):
    p=tmp_path/'empty-child.yaml'
    p.write_text('outer:\n  empty:\nend: value\n')
    assert u._load_yaml_minimal(p)=={'outer':{'empty':None},'end':'value'}
