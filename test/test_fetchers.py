# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_fetchers.py
# 【修复回归补充｜2026-10-18】翻译样本显式携带批次 ID，新增异常响应及对齐用例。
# 修改内容及原因：覆盖 AIHOT v1 契约、分页、arXiv/HF 抓取、翻译及双源异常隔离。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""新接口契约、回退、重试、分页、翻译与双来源异常隔离。"""
import copy
import importlib
import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError
from urllib.parse import parse_qs,urlsplit
import pytest
n=importlib.import_module('src.news.fetcher')
p=importlib.import_module('src.papers.fetcher')
t=importlib.import_module('src.trending.fetcher')

@pytest.mark.parametrize('module',[n,p,t])
def test_missing_config(module):
    with pytest.raises(ValueError): module.fetch_data(None)

@pytest.mark.parametrize('responses,expected_calls',[(1,1),(2,2),(3,3),(0,3)])
def test_news_routes(monkeypatch,item,responses,expected_calls):
    raw=dict(item,source={'name':'source'},links={'original':'https://example.org'})
    report={'date':'2026-10-18','windowEnd':'2026-10-18T00:00:00Z','sections':[{'label':'ai-models','items':[raw]}],'flashes':[{'title':'excluded'}]}
    result={'report':report}
    data=[result] if responses==1 else [None,result] if responses==2 else [None,None,{'items':[{'title':'backup','url':'https://backup','extra':{'info':'RSS · industry','hover':'summary'}}],'updatedTime':1} if responses==3 else None]
    api=Mock(side_effect=data);monkeypatch.setattr(n,'api_get',api)
    cfg={'fetch':{'api_base':'https://aihot.news/api/v1','max_retries':1,'target_date':'2026-10-18','fallback_base':'https://backup','fallback_path':'/api'}}
    if responses:
        items=n.fetch_data(cfg)
        assert items[0]['title']==(item['title'] if responses<3 else 'backup')
        if responses<3:
            assert items[0]['sourceName']=='source' and items[0]['category']=='模型发布/更新'
            assert items[0]['sourceUrl']=='https://example.org'
            assert 'sourceUrl' not in raw['links']
    else:
        with pytest.raises(RuntimeError): n.fetch_data(cfg)
    assert api.call_count==expected_calls
    assert api.call_args_list[0].args[0]=='/dailies/2026-10-18'
    if expected_calls>1: assert api.call_args_list[1].args[0]=='/dailies/latest'

@pytest.mark.parametrize('updated,info',[(None,'plain source'),('bad','RSS · unknown'),(1750000000000,'RSS · paper')])
def test_newsnow_fields(monkeypatch,updated,info):
    monkeypatch.setattr(n,'api_get',Mock(return_value={'updatedTime':updated,'items':[{'extra':{'info':info},'url':'https://x'}]}))
    cfg={'fetch':{'fallback_base':'https://x','fallback_path':'/p','max_retries':1}}
    items=n._fetch_from_newsnow(cfg)
    assert items[0]['category']==('论文研究' if 'paper' in info else '技巧与观点')
    assert bool(items[0]['publishTime'])==isinstance(updated,int)

@pytest.mark.parametrize('endpoint', ['aihot','arxiv','huggingface'])
def test_disabled_sources(config,endpoint):
    config[endpoint]['enabled']=False
    fn={'aihot':p.fetch_aihot_papers,'arxiv':p.fetch_arxiv_papers,'huggingface':p.fetch_hf_daily_papers}[endpoint]
    assert fn(config,'2026-10-18')==[]

@pytest.mark.parametrize('ending',['done','missing_cursor','missing_items','empty','limit'])
def test_aihot_pagination(monkeypatch,config,item,ending):
    config['aihot'].update(take=3,page_size=2)
    raw=dict(item,source={'name':'Source'},links={'original':'https://x/p'})
    old=dict(raw,id='old',publishedAt='2025-01-01T00:00:00Z')
    first={'items':[raw,old],'page':{'hasMore':True,'nextCursor':'opaque+/=&'}}
    second={'items':[dict(raw,id='second')],'page':{'hasMore':False}}
    if ending=='missing_cursor': first['page'].pop('nextCursor')
    if ending=='missing_items': first={}
    if ending=='empty': first={'items':[],'page':{'hasMore':False}}
    if ending=='limit': first={'items':[raw,raw,raw],'page':{'hasMore':True,'nextCursor':'unused'}}
    api=Mock(side_effect=[first,second]);monkeypatch.setattr(p,'api_get',api)
    result=p.fetch_aihot_papers(config,'2026-10-18')
    if ending=='done':
        assert [x['id'] for x in result]==['p1','second']
        q=parse_qs(urlsplit(api.call_args_list[1].args[0]).query)
        assert q['cursor']==['opaque+/=&'] and q['limit']==['1']
    elif ending in ('missing_items','empty'): assert result==[]
    else: assert len(result)==(3 if ending=='limit' else 1)
    if result: assert result[0]['source']=='Source' and result[0]['url']=='https://x/p'
    q=parse_qs(urlsplit(api.call_args_list[0].args[0]).query)
    assert q['window']==['7d'] and 'cursor' not in q and 'since' not in q and 'take' not in q

@pytest.mark.parametrize('mode',['success','retry','fail','zero'])
def test_http_retries(monkeypatch,response,config,mode):
    config['fetch']['max_retries']=0 if mode=='zero' else 2
    fn=Mock(side_effect=[response(b'raw')] if mode=='success' else [TimeoutError('x'),response(b'raw')] if mode=='retry' else TimeoutError('x'))
    monkeypatch.setattr(p.urllib.request,'urlopen',fn)
    if mode in ('fail','zero'):
        with pytest.raises((RuntimeError,TimeoutError)): p._http_get('https://x',config)
    else: assert p._http_get('https://x',config)==b'raw'

@pytest.mark.parametrize('days,cats',[(0,['cs.AI']),(5,['cs.AI','cs.CL'])])
def test_arxiv_xml(monkeypatch,config,days,cats):
    config['fetch']['days_back']=days;config['arxiv']['categories']=cats
    xml=b'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom"><entry><id>https://arxiv.org/abs/1</id><title>Title</title><summary>Summary</summary><author><name>Author</name></author><published>2026-10-17T00:00:00Z</published><arxiv:primary_category term="cs.AI"/></entry><entry><id>broken</id></entry></feed>'''
    http=Mock(return_value=xml);monkeypatch.setattr(p,'_http_get',http)
    result=p.fetch_arxiv_papers(config,'2026-10-18')
    assert result[0]['id']=='1' and result[0]['authors']==['Author']
    assert result[0]['pdf_url']=='https://arxiv.org/pdf/1'

@pytest.mark.parametrize('days',[0,3])
def test_hf_daily(monkeypatch,config,days):
    config['fetch']['days_back']=days
    paper={'id':'1','title':'Title','summary':' Summary ','publishedAt':'2026-10-17T00:00:00Z','upvotes':60}
    monkeypatch.setattr(p,'_http_get',Mock(side_effect=[TimeoutError('x'),b'[]',json.dumps([{'paper':paper}]).encode()]))
    result=p.fetch_hf_daily_papers(config,'2026-10-18')
    assert len(result)==(1 if days else 0)
    if result: assert result[0]['selected'] and result[0]['summary']=='Summary'

@pytest.mark.parametrize('fail_arxiv,fail_hf',[(False,False),(True,False),(False,True),(True,True)])
def test_backup_source_isolation(monkeypatch,config,item,fail_arxiv,fail_hf):
    monkeypatch.setattr(p,'fetch_aihot_papers',Mock(return_value=[]))
    arxiv=Mock(side_effect=TimeoutError('arxiv') if fail_arxiv else None,return_value=[item])
    hf_item=dict(item,id='hf',source_api='huggingface')
    hf=Mock(side_effect=ValueError('hf') if fail_hf else None,return_value=[hf_item])
    monkeypatch.setattr(p,'fetch_arxiv_papers',arxiv);monkeypatch.setattr(p,'fetch_hf_daily_papers',hf)
    monkeypatch.setattr(p,'translate_papers',lambda items,cfg:items)
    assert p.fetch_data(config)==([] if fail_arxiv else [item])+([] if fail_hf else [hf_item])
    arxiv.assert_called_once();hf.assert_called_once()

def test_aihot_primary_and_merge(monkeypatch,config,item):
    monkeypatch.setattr(p,'fetch_aihot_papers',Mock(return_value=[item]))
    fallback=Mock();monkeypatch.setattr(p,'fetch_arxiv_papers',fallback)
    assert p.fetch_data(config)==[item];fallback.assert_not_called()
    original=dict(item)
    hf=dict(item,source_api='huggingface',score=100,upvotes=100)
    merged=p.merge_papers([original,{}],[hf])
    assert len(merged)==1 and merged[0]['upvotes']==100

@pytest.mark.parametrize('text,expected', [('[]',[]),('{"translations":[{"id":1},{"id":0}]}',[{'id':0},{'id':1}]),('```json\n[{"id":0}]\n```',[{'id':0}])])
def test_translation_parser(text,expected): assert p._parse_translation_response(text,2)==expected

@pytest.mark.parametrize('text',['{}','null','bad'])
def test_invalid_translation(text):
    with pytest.raises((ValueError,TypeError)):p._parse_translation_response(text,1)

@pytest.mark.parametrize('mode',['disabled','not_needed','missing_key','success','failure'])
def test_translation_batches(monkeypatch,config,item,mode):
    config['translation']['enabled']=mode!='disabled';config['translation']['batch_size']=1
    items=[dict(item,source_api='aihot' if mode=='not_needed' else 'arxiv'),dict(item,id='2')]
    if mode=='not_needed':items=items[:1]
    if mode not in ('missing_key','disabled','not_needed'):monkeypatch.setenv('DEEPSEEK_API_KEY','fake')
    translate=Mock(side_effect=RuntimeError('bad') if mode=='failure' else [[{'id':0,'title_zh':'中文','summary_zh':''}],[{'id':0,'title_zh':'','summary_zh':'摘要'}]])
    monkeypatch.setattr(p,'_translate_batch',translate)
    result=p.translate_papers(items,config)
    if mode=='success':assert result[0]['title_zh']=='中文' and result[1]['summary_zh']=='摘要'
    else:assert 'title_zh' not in result[0]

def test_translate_request(monkeypatch,response,item):
    opener=Mock();opener.open.return_value=response({'choices':[{'message':{'content':'{"translations":[{"id":0,"title_zh":"中"}]}'}}]})
    monkeypatch.setattr(p.urllib.request,'build_opener',Mock(return_value=opener))
    assert p._translate_batch([item],'fake','https://x','m',5)[0]['title_zh']=='中'
    assert opener.open.call_args.args[0].full_url=='https://x/chat/completions'

@pytest.mark.parametrize('mode',['ok','http','timeout','retry'])
def test_trending_fetch(monkeypatch,response,mode):
    err=HTTPError('https://x',500,'bad',{},io.BytesIO()) if mode=='http' else TimeoutError('x')
    fn=Mock(side_effect=[response({'items':[{'title':'x'}]})] if mode=='ok' else [err,response({'items':[{'title':'x'}]})] if mode=='retry' else [err,err])
    monkeypatch.setattr(t.urllib.request,'urlopen',fn)
    result=t.fetch_source('https://x','weibo',2)
    assert bool(result)==(mode in ('ok','retry'))
    if result:assert result[0]['source_id']=='weibo'

def test_trending_aggregation(monkeypatch):
    monkeypatch.setattr(t,'fetch_source',Mock(side_effect=[[{'title':'a'}],[{'title':'b'}]]))
    result=t.fetch_data({'newsnow':{'api_url':'https://x','sources':[{'id':'a','group':'A'},{'id':'b'}]}})
    assert [i['source_group'] for i in result]==['A','']
