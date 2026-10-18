# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_filters_renderers.py
# 修改内容及原因：覆盖关键词/AI 过滤、网页/微信渲染、字段回退与内容转义。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""过滤边界、HTML 内容断言、中文回退与模板安全回归。"""
import importlib
import itertools
from datetime import datetime,timedelta,timezone
from unittest.mock import Mock
import pytest
f=importlib.import_module('src.trending.filter')
n=importlib.import_module('src.news.renderer')
p=importlib.import_module('src.papers.renderer')
t=importlib.import_module('src.trending.renderer')
w=importlib.import_module('src.wechat.renderer')

def keyword_config():
    return {'keywords':{'groups':[{'name':'AI大模型','terms':['AI'],'exclude':['skip']},{'name':'汽车','terms':['car']}]}}

@pytest.mark.parametrize('method',['keyword','both','ai'])
def test_filter_modes(monkeypatch,method):
    config=keyword_config();config['filter']={'method':method}
    items=[{'title':'AI launch'},{'title':'skip AI'},{'title':'CAR'},{'title':None}]
    if method=='ai':
        ai=Mock(return_value=items[:1]);monkeypatch.setattr(f,'ai_filter',ai)
        assert f.filter_data(items,config)==items[:1]
    else:
        if method=='both':monkeypatch.setattr(f,'ai_filter',lambda values,*a,**kw:values)
        result=f.filter_data(items,config)
        assert [i['group_name'] for i in result]==['AI大模型','汽车']
    assert 'group_name' not in items[0]

@pytest.mark.parametrize('content',['1: 0.9 | AI大模型\n2: 0.1 | unknown\n3: 2\n99: 0.8\nnonsense','1: ... | AI大模型'])
def test_ai_response(monkeypatch,response,content):
    monkeypatch.setattr(f.urllib.request,'urlopen',Mock(return_value=response({'choices':[{'message':{'content':content}}]})))
    result=f.ai_score_batch([{'title':'a'},{'title':'b'},{'title':'c'}],'interest',['AI大模型'],'fake','https://x','m')
    if '...' in content:assert result=={}
    else:
        assert result[0]=={'score':0.9,'group':'AI大模型'}
        assert result[1]['group']=='' and result[2]['score']==1

def test_ai_network_error(monkeypatch):
    monkeypatch.setattr(f.urllib.request,'urlopen',Mock(side_effect=TimeoutError('x')))
    assert f.ai_score_batch([], '', [],'k','https://x','m')=={}

@pytest.mark.parametrize('key,assign',[(False,True),(True,True),(True,False)])
def test_ai_filter(monkeypatch,key,assign):
    items=[{'title':'a'},{'title':'b'},{'title':'c'}]
    if key:monkeypatch.setenv('DEEPSEEK_API_KEY','fake')
    monkeypatch.setattr(f,'ai_score_batch',Mock(return_value={0:{'score':0.9,'group':'AI大模型'},1:{'score':0.1,'group':''}}))
    result=f.ai_filter(items,keyword_config(),assign)
    if key:
        assert result==items[:1]
        assert ('group_name' in result[0])==assign
    else:assert result is items

@pytest.mark.parametrize('source,cls,label',[
    ('X：a','source-x','X'),('Twitter','source-x','Twitte'),('公众号：abc','source-wechat','公众号'),('wechat','source-wechat','wechat'),
    ('GitHub','source-gh','GitHub'),('MarkTechPost','source-blog','博客'),('RSS','source-blog','RSS'),('arxiv','source-media','arXiv'),
    ('Hacker News','source-hn','HN'),('buzzing','source-hn','HN'),('TechCrunch Media','source-media','TechCr'),('','source-media','来源')])
def test_news_sources(source,cls,label):
    assert n.source_class(source)==cls
    assert n.short_source(source)==label

@pytest.mark.parametrize('seconds', [30,3700,90000])
def test_relative_time(seconds):
    iso=(datetime.now(timezone.utc)-timedelta(seconds=seconds)).isoformat()
    value=n.fmt_time(iso)
    assert ('分钟前' in value if seconds<3600 else '小时前' in value if seconds<86400 else '今天' in value)
    assert n.fmt_time('bad')=='bad'
    assert n.fmt_time('')==''

def test_news_content(item):
    assert n.summarize('')=='暂无摘要'
    assert n.summarize('abc')=='abc'
    assert n.summarize('x'*70).endswith('…')
    html=n.generate_html([dict(item,title='<script>alert(1)</script>')])
    assert '&lt;script&gt;' in html and '<script>alert(1)</script>' not in html
    assert 'https://example.org/p1' in html
    assert '暂无' in n.generate_html([]) or '今日' in n.generate_html([])

def test_paper_content(item):
    assert p.sanitize(1)==1
    assert '\ud800' not in p.sanitize('\ud800')
    assert p.get_badge_color('arxiv')!=p.get_badge_color('unknown')
    assert p.get_badge_label('site：author (RSS)')=='site'
    assert p.get_badge_label('x'*30).endswith('…')
    assert p.get_badge_label('site (RSS)')=='site'
    data=[dict(item,title_zh='中文标题',summary_zh='中'*250),dict(item,id='empty',publishedAt='',summary=''),dict(item,id='bad',publishedAt='invalid-date')]
    html=p.generate_html(data)
    assert '中文标题' in html and '中'*201 not in html
    assert 'window.PAPERS' in html and 'invalid-date' in html
    assert '暂无摘要' in p.generate_html([dict(item,summary='')])
    assert 'window.PAPERS' in p.generate_html([])

@pytest.mark.parametrize('stamp',[0,1700000000000,1700000000,'bad'])
def test_trending_time(stamp): assert bool(t.format_updated(stamp))==isinstance(stamp,int) and stamp!=0 if stamp else t.format_updated(stamp)==''

def test_trending_metadata_and_content(monkeypatch):
    cfg={'newsnow':{'sources':[{'id':'x','name':'X'}]}}
    assert t.source_meta({'source_id':'x'},cfg)==('X','•','')
    assert t.source_meta({'source_id':'y'},cfg)==('y','•','')
    for source in ('wechat','blog','hacker news','github','other'):
        monkeypatch.setitem(t.SOURCES,source,{'name':source})
    items=[{'title':f'title {i}','url':'https://example.org','group_name':'AI大模型' if i%2 else 'unknown','source_id':src,'ai_score':score,'updatedTime':1700000000}
           for i,(src,score) in enumerate(zip(('wechat','blog','hacker news','github','other'),(.9,.7,.4,.9,.7)))]
    html=t.generate_html(items+[{'title':'no score','mobileUrl':'https://example.org/mobile'}])
    assert all(f'title {i}' in html for i in range(5))
    assert all(x in html for x in ('score-high','score-mid','score-low','https://example.org/mobile'))
    assert '雷达' in t.generate_html([])

@pytest.mark.parametrize('url',['','example.org/p','https://example.org/p'])
@pytest.mark.parametrize('summary',['','Useful summary'])
@pytest.mark.parametrize('show,button',[(False,False),(False,True),(True,False),(True,True)])
def test_wechat_item_variants(item,url,summary,show,button):
    value=dict(item,url=url,sourceUrl=url,summary=summary,category='')
    for fn in (w._wechat_build_news_item,w._wechat_md_news_item):
        text=fn(1,value)
        assert item['title'] in text
        if url:assert 'https://example.org/p' in text
    for fn in (w._wechat_build_paper_item,w._wechat_md_paper_item):
        text=fn(1,value,show,button)
        assert ('🔗 arXiv:' in text)==bool(button and url)
        assert item['title'] in text

@pytest.mark.parametrize('news,papers',[(False,False),(True,False),(False,True),(True,True)])
def test_wechat_document(item,news,papers):
    for fn in (w.render_wechat_html,w.render_wechat_md):
        text=fn([item] if news else [],[item] if papers else [],'2026-10-18','https://example.org')
        assert (item['title'] in text)==(news or papers)
    assert '2026年10月18日' in w._wechat_format_date_cn('2026-10-18')
    assert w._wechat_format_date_cn('bad')=='bad'
    assert '<!DOCTYPE html>' in w.wrap_wechat_html_doc('<p>hello</p>','2026-10-18')
