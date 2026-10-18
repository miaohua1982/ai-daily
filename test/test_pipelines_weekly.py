# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_pipelines_weekly.py
# 修改内容及原因：验证管线步骤、入口代理、跨区去重、周报时间窗及精选排序。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""管线步骤、微信跨区去重、周报排序和入口代理。"""
import copy
import importlib
from unittest.mock import Mock
import pytest
from src.pipeline import GeneratorPipeline
from src.news.pipeline import NewsPipeline
from src.papers.pipeline import PapersPipeline
from src.trending.pipeline import TrendingPipeline
wf=importlib.import_module('src.wechat.fetcher')
weekly=importlib.import_module('src.wechat.weekly_fetcher')

@pytest.mark.parametrize('cls',[NewsPipeline,PapersPipeline])
def test_summary_filter(cls,item):
    pipeline=cls();short=dict(item,summary='x')
    assert pipeline.filter_data([item,short],{'filter':{'min_summary_len':20}})==[item]
    assert pipeline.filter_data([item],{})==[item]

@pytest.mark.parametrize('name',['generate_daily','generate_papers','generate_trending'])
def test_wrappers(monkeypatch,name,item,tmp_path):
    mod=importlib.import_module(name)
    fetch=Mock(return_value=[item]);dedup=Mock(return_value=[item]);run=Mock()
    monkeypatch.setattr(mod._pipeline,'fetch_data',fetch);monkeypatch.setattr(mod._pipeline,'dedup_data',dedup);monkeypatch.setattr(mod._pipeline,'run',run)
    assert mod.fetch_data({})==[item] and mod.dedup_data([item],{})==[item]
    if name!='generate_trending':
        filt=Mock(return_value=[item]);monkeypatch.setattr(mod._pipeline,'filter_data',filt)
        assert mod.filter_data([item],{})==[item]
    mod.main();run.assert_called_once()

def test_pipeline_sequence(monkeypatch,tmp_path,item):
    class Pipeline(GeneratorPipeline):
        def fetch_data(self,config): return [item]
        def generate_html(self,items): return 'generated'
    pipeline=Pipeline()
    import utils
    git=Mock();monkeypatch.setattr(utils,'git_commit',git)
    cfg={'fetch':{'target_date':'2026-10-18'}}
    pipeline.run(cfg,tmp_path/'index.html',tmp_path/'archive','test',tmp_path)
    assert (tmp_path/'index.html').read_text()=='generated'
    assert (tmp_path/'archive/2026-10-18.html').read_text()=='generated'
    git.assert_called_once()
    assert pipeline.filter_data([item],cfg)==[item]

@pytest.mark.parametrize('cls,module',[ (NewsPipeline,'src.news.pipeline'),(PapersPipeline,'src.papers.pipeline'),(TrendingPipeline,'src.trending.pipeline')])
def test_pipeline_delegation(monkeypatch,cls,module,item):
    m=importlib.import_module(module);fetch=Mock(return_value=[item]);render=Mock(return_value='html')
    monkeypatch.setattr(m,'_fetch_impl',fetch);monkeypatch.setattr(m,'_render_impl',render)
    assert cls().fetch_data({})==[item] and cls().generate_html([item])=='html'
    if cls is TrendingPipeline:
        monkeypatch.setattr(m,'_filter_impl',lambda items,cfg:items)
        assert cls().filter_data([item],{})==[item]
        assert len(cls().date_str({}))==13

@pytest.mark.parametrize('name',['news','papers'])
@pytest.mark.parametrize('mode',['error','empty','ok'])
def test_wechat_fetch_wrappers(monkeypatch,name,mode,item):
    mod=wf.gd if name=='news' else wf.gp
    monkeypatch.setattr(mod,'fetch_data',Mock(return_value=[] if mode=='empty' else [item],side_effect=RuntimeError('fail') if mode=='error' else None))
    result=(wf.fetch_news if name=='news' else wf.fetch_papers)()
    assert result==([item] if mode=='ok' else [])

@pytest.mark.parametrize('key,semantic',[(False,False),(True,False),(True,True)])
def test_cross_dedup(monkeypatch,item,key,semantic):
    if key:monkeypatch.setenv('EMBEDDING_API_KEY','fake')
    news=[item,dict(item)]
    papers=[dict(item,id='p2',url='https://example.org/2',sourceUrl='',title_zh='中文')]
    monkeypatch.setattr(wf,'semantic_dedup',Mock(side_effect=lambda values,*a,**kw:values[:1] if semantic else values))
    a,b=wf.cross_dedup_news_papers(news,papers,{'cross_dedup':{'base_url':'https://x'}})
    assert len(a)==1 and len(b)==(0 if semantic else 1)
    assert all(not k.startswith('_') for it in a+b for k in it)
    assert wf.cross_dedup_news_papers([],[],{})==([],[])
    assert len(wf.cross_dedup_news_papers([{}],[],{})[0])==1

@pytest.mark.parametrize('day,expected',[('2026-10-12',1),('2026-10-18',7),('bad',7)])
def test_week_days(day,expected):assert weekly.natural_week_days_back(day)==expected

@pytest.mark.parametrize('mode',['ok','empty','hf_error','arxiv_error','no_filter'])
def test_weekly_selection(monkeypatch,mode,item):
    cfg={'fetch':{'target_date':'2026-10-18'},'weekly':{'top_n':2},'filter':{'min_summary_len':0 if mode=='no_filter' else 20}}
    hf=[dict(item,id='hf-low',source_api='huggingface',upvotes=1),dict(item,id='hf-high',source_api='huggingface',upvotes=100),dict(item,id='short',summary='x',source_api='huggingface')]
    arxiv=[dict(item,id='arxiv')]
    monkeypatch.setattr(weekly,'fetch_hf_daily_papers',Mock(return_value=[] if mode=='empty' else hf,side_effect=RuntimeError('HF') if mode=='hf_error' else None))
    monkeypatch.setattr(weekly,'fetch_arxiv_papers',Mock(return_value=[] if mode=='empty' else arxiv,side_effect=RuntimeError('arxiv') if mode=='arxiv_error' else None))
    monkeypatch.setattr(weekly,'dedup_data',lambda values,cfg:values)
    translator=Mock(side_effect=lambda values,cfg:values);monkeypatch.setattr(weekly,'translate_papers',translator)
    result=weekly.fetch_weekly_papers(cfg)
    assert cfg['fetch']['days_back']==7
    if mode=='empty':assert result==[];translator.assert_not_called()
    elif mode=='hf_error':assert [it['id'] for it in result]==['arxiv']
    else:assert [it['id'] for it in result]==['hf-high','hf-low']
    assert all(it['url'].startswith('https://arxiv.org/abs/') for it in result)
