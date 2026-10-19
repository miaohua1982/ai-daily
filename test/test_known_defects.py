# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_known_defects.py
# 修改内容及原因：用 strict xfail 明确保留两项未修复缺陷及三项已修复回归；不把预期失败当成测试通过。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""已确认的缺陷回归：strict xfail 明确保留失败证据，修复后必须移除 xfail。
不为提高覆盖率改变生产行为；这些问题不在本次测试代码改造中顺带修复。
"""
import importlib
from unittest.mock import Mock
import pytest

@pytest.mark.xfail(strict=True,reason='YAML fallback strips a bare dash before recognizing an empty list item')
def test_yaml_nested_list_contract(tmp_path):
    u=importlib.import_module('utils.utils');p=tmp_path/'nested.yaml'
    p.write_text('items:\n  -\n    nested: 1\n')
    assert u._load_yaml_minimal(p)=={'items':[{'nested':1}]}

# 【修复回归标识｜2026-10-18】周报自然周边界已修复，移除 xfail，必须通过。
def test_natural_week_excludes_previous_sunday():
    w=importlib.import_module('src.wechat.weekly_fetcher')
    previous={'publishedAt':'2026-10-11T12:00:00Z'};monday={'publishedAt':'2026-10-12T12:00:00Z'}
    assert w._filter_natural_week([previous,monday],'2026-10-18')==[monday]

# 【修复回归标识｜2026-10-18】译文缺项已修复，移除 xfail，必须正常通过。
def test_translation_missing_id_preserves_alignment(monkeypatch,config,item):
    p=importlib.import_module('src.papers.fetcher')
    monkeypatch.setenv('DEEPSEEK_API_KEY','fake')
    monkeypatch.setattr(p,'_translate_batch',Mock(return_value=[{'id':1,'title_zh':'第二篇'}]))
    result=p.translate_papers([dict(item),dict(item,id='second')],config)
    assert 'title_zh' not in result[0] and result[1]['title_zh']=='第二篇'

# 【修复回归标识｜2026-10-19】归档 Git 路径已修复，移除 xfail。
# 三条管线均断言：主页面名称保持不变，归档保留 archive/，自动提交仍会调用。
@pytest.mark.parametrize('index_name,section,date_str', [
    ('daily_news.html', 'news', '2026-10-19'),
    ('papers.html', 'papers', '2026-10-19'),
    ('trending.html', 'trending', '2026-10-19-13'),
])
def test_pipeline_stages_real_archive_path(monkeypatch,tmp_path,index_name,section,date_str):
    import utils
    from src.pipeline import GeneratorPipeline
    class Pipeline(GeneratorPipeline):
        def fetch_data(self,config):return []
        def generate_html(self,items):return 'html'
    staged=Mock();monkeypatch.setattr(utils,'git_commit',staged)
    root=tmp_path;archive=root/'archive'/section
    Pipeline().run({'fetch':{'target_date':date_str}},root/index_name,archive,section,root)
    staged.assert_called_once_with(date_str,[index_name,f'archive/{section}/{date_str}.html'],section,root)
    assert (archive/f'{date_str}.html').read_text()=='html'

@pytest.mark.xfail(strict=True,reason='Embedded JSON does not escape closing script tags in external text')
def test_paper_json_cannot_break_script_context(item):
    p=importlib.import_module('src.papers.renderer')
    html=p.generate_html([dict(item,title='</script><script>untrusted()</script>')])
    assert '</script><script>untrusted()' not in html
