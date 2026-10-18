# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_boundaries.py
# 修改内容及原因：补充脚本入口、分页上限、缺失字体、异常日期等可达边界分支。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""补齐入口、分页上限、字体缺失和异常解析的可达分支。"""
import copy
import importlib
import runpy
import sys
from unittest.mock import Mock
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('name',['generate_daily','generate_papers','generate_trending','generate_wechat','generate_wechat_papers_weekly','generate_wechat_video'])
def test_script_main_guards(monkeypatch,name):
    monkeypatch.setattr(sys,'argv',[name])
    if name in ('generate_daily','generate_papers','generate_trending'):
        module=importlib.import_module({'generate_daily':'src.news.pipeline','generate_papers':'src.papers.pipeline','generate_trending':'src.trending.pipeline'}[name])
        cls=getattr(module,{'generate_daily':'NewsPipeline','generate_papers':'PapersPipeline','generate_trending':'TrendingPipeline'}[name])
        run=Mock();monkeypatch.setattr(cls,'run',run)
        runpy.run_path(str(ROOT/f'{name}.py'),run_name='__main__')
        run.assert_called_once()
    else:
        if name=='generate_wechat':
            fetch=importlib.import_module('src.wechat.fetcher')
            monkeypatch.setattr(fetch,'fetch_news',lambda:[]);monkeypatch.setattr(fetch,'fetch_papers',lambda:[])
        elif name=='generate_wechat_papers_weekly':
            fetch=importlib.import_module('src.wechat.weekly_fetcher')
            monkeypatch.setattr(fetch,'fetch_weekly_papers',lambda cfg:[])
        with pytest.raises(SystemExit) as error:
            runpy.run_path(str(ROOT/f'{name}.py'),run_name='__main__')
        assert error.value.code==(2 if name=='generate_wechat_video' else 0)

def test_no_startup_sleep(monkeypatch,config,response):
    n=importlib.import_module('src.news.fetcher');p=importlib.import_module('src.papers.fetcher');t=importlib.import_module('src.trending.fetcher')
    monkeypatch.setattr(n.random,'uniform',lambda *args:0)
    monkeypatch.setattr(n,'api_get',Mock(return_value={'report':{'sections':[]}}))
    n.fetch_data({'fetch':{'api_base':'https://x','max_retries':1,'target_date':'2026-10-18'}})
    monkeypatch.setattr(p,'api_get',Mock(return_value={'items':[],'page':{'hasMore':False}}))
    assert p.fetch_aihot_papers(config,'2026-10-18')==[]
    monkeypatch.setattr(t.urllib.request,'urlopen',Mock(return_value=response({'items':[]})))
    assert t.fetch_source('https://x','x')==[]

def test_pagination_exhaustion_and_duplicate_id(monkeypatch,config,item):
    p=importlib.import_module('src.papers.fetcher')
    config['aihot'].update(take=100,page_size=1)
    raw=dict(item,links={'aihot':'https://aihot.news/items/p1'},source={})
    monkeypatch.setattr(p,'api_get',Mock(return_value={'items':[raw],'page':{'hasMore':True,'nextCursor':'cursor'}}))
    assert len(p.fetch_aihot_papers(config,'2026-10-18'))==3
    assert len(p.merge_papers([item],[dict(item)]))==1

def test_renderer_date_boundaries(monkeypatch,item):
    n=importlib.import_module('src.news.renderer');p=importlib.import_module('src.papers.renderer')
    monkeypatch.setattr(n,'get_now_date_str',lambda:'bad date')
    assert 'bad date' in n.generate_html([item])
    groups,dates=p.group_by_date([item,dict(item)])
    assert len(groups[dates[0]])==2

def test_font_scan_absent_and_broken(monkeypatch,tmp_path):
    import subprocess
    c=importlib.import_module('src.wechat.cover')
    from PIL import ImageFont,ImageDraw,Image
    marker=ImageFont.load_default()
    monkeypatch.setattr(c.ImageFont,'load_default',lambda:marker)
    monkeypatch.setattr(c,'CHINESE_FONT_CANDIDATES',[])
    monkeypatch.setattr(subprocess,'check_output',Mock(return_value='\n/missing/font\n'))
    monkeypatch.setattr(c,'WIN_FONTS_DIR',str(tmp_path))
    assert c._find_chinese_font(12) is marker
    (tmp_path/'cjk.ttf').write_bytes(b'invalid')
    monkeypatch.setattr(c,'WIN_FONT_KEYWORDS',['cjk'])
    monkeypatch.setattr(c.ImageFont,'truetype',Mock(side_effect=OSError('broken font')))
    assert c._find_chinese_font(12) is marker
    monkeypatch.setattr(c,'WARM_WASH_RADIUS',1)
    image=Image.new('RGB',(c.COVER_W,c.COVER_H),'white')
    c._draw_background(image,ImageDraw.Draw(image),c.COVER_W,c.COVER_H)
    assert image.getpixel((0,0))==c.ACCENT_BAR_COLOR

def test_weekly_missing_id(monkeypatch,item):
    m=importlib.import_module('src.wechat.weekly_fetcher')
    monkeypatch.setattr(m,'fetch_hf_daily_papers',lambda *args:[dict(item,id='',source_api='huggingface')])
    monkeypatch.setattr(m,'fetch_arxiv_papers',lambda *args:[])
    monkeypatch.setattr(m,'dedup_data',lambda items,cfg:items)
    monkeypatch.setattr(m,'translate_papers',lambda items,cfg:items)
    result=m.fetch_weekly_papers({'fetch':{'target_date':'2026-10-18'}})
    assert result[0]['url']==item['url']

def test_yaml_quote_and_skip_branches(tmp_path):
    u=importlib.import_module('utils.utils')
    assert u._split_key_value('"a\'b": value')==('"a\'b"','value')
    p=tmp_path/'input.yaml'
    p.write_text('items:\n  - one\n    ignored\n  - name: two\n    ignored\n    - nested\nend: true\n')
    result=u._load_yaml_minimal(p)
    assert result['items'][0]=='one'

def test_semantic_already_removed_inner(monkeypatch):
    u=importlib.import_module('utils.utils')
    # A 与 C 相似，B 与二者不相似；B 的比较循环必须跳过已删除的 C。
    monkeypatch.setattr(u,'get_embeddings',Mock(return_value=[[1,0],[0,1],[1,0]]))
    items=[{'title':'A'},{'title':'B'},{'title':'C'}]
    assert u.semantic_dedup(items,.75,'fake','https://x','m')==items[:2]
