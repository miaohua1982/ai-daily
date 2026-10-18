# ======================================================================
# 【修复回归标识｜2026-10-18｜新增】
# 文件：test/test_weekly_window.py
# 修改原因：周报不能用“含当天的抓取天数”直接计算周一起点，需按北京时间精确过滤。
# 覆盖全周运行日、跨时区边界及双源编排；不联网、不生成推送文件。
# ======================================================================
"""周报自然周边界契约：周一 00:00（含）到目标日次日 00:00（不含）。"""
from datetime import datetime, timedelta
import importlib
from unittest.mock import Mock
import pytest

weekly = importlib.import_module('src.wechat.weekly_fetcher')

@pytest.mark.parametrize('weekday', range(7))
def test_all_weekdays_have_same_monday_start(weekday):
    target = datetime(2026, 10, 12) + timedelta(days=weekday)
    following = target + timedelta(days=1)
    entries = [
        {'id':'previous-sunday', 'publishedAt':'2026-10-11T23:59:59.999999+08:00'},
        {'id':'monday', 'publishedAt':'2026-10-12T00:00:00+08:00'},
        {'id':'target-last', 'publishedAt':target.strftime('%Y-%m-%d')+'T23:59:59.999999+08:00'},
        {'id':'following-day', 'publishedAt':following.strftime('%Y-%m-%d')+'T00:00:00+08:00'},
    ]
    result = weekly._filter_natural_week(entries, target.strftime('%Y-%m-%d'))
    assert [item['id'] for item in result] == ['monday','target-last']
    assert weekly.natural_week_days_back(target.strftime('%Y-%m-%d')) == weekday + 1

@pytest.mark.parametrize('published,keep', [
    ('2026-10-11T15:59:59Z', False),
    ('2026-10-11T16:00:00Z', True),
    ('2026-10-11T16:00:00+00:00', True),
    ('2026-10-12T00:00:00+09:00', False),
    ('2026-10-11T11:00:00-05:00', True),
    ('2026-10-11T16:00:00', True),
    ('2026-10-18T15:59:59Z', True),
    ('2026-10-18T16:00:00Z', False),
    ('2026-10-19T12:00:00Z', False),
    ('', False), (None, False), ('invalid', False), (123, False),
])
def test_timezone_and_invalid_publication_dates(published, keep):
    item = {'publishedAt':published}
    assert weekly._filter_natural_week([item], '2026-10-18') == ([item] if keep else [])


def test_missing_timestamp_and_invalid_target():
    assert weekly._filter_natural_week([{}], '2026-10-18') == []
    with pytest.raises(ValueError):
        weekly._filter_natural_week([], 'invalid')

@pytest.mark.parametrize('target,days', [('2026-10-12',1),('2026-10-14',3),('2026-10-18',7)])
def test_week_filter_before_dedup_and_translation(monkeypatch, item, target, days):
    old = dict(item, id='old', publishedAt='2026-10-11T12:00:00Z')
    # 周一北京时间零点仍是 UTC 周日，必须保留，不能仅按 UTC 日期截取。
    current = dict(item, id='current', publishedAt='2026-10-11T16:00:00Z')
    future = dict(item, id='future', publishedAt='2026-10-19T00:00:00+08:00')
    hf = Mock(return_value=[old,current]); arxiv = Mock(return_value=[future])
    monkeypatch.setattr(weekly, 'fetch_hf_daily_papers', hf)
    monkeypatch.setattr(weekly, 'fetch_arxiv_papers', arxiv)
    dedup = Mock(side_effect=lambda items,config:items)
    translate = Mock(side_effect=lambda items,config:items)
    monkeypatch.setattr(weekly, 'dedup_data', dedup)
    monkeypatch.setattr(weekly, 'translate_papers', translate)
    config = {'fetch':{'target_date':target},'filter':{'min_summary_len':0}}
    result = weekly.fetch_weekly_papers(config)
    assert [row['id'] for row in result] == ['current']
    assert config['fetch']['days_back'] == days
    hf.assert_called_once_with(config, target)
    arxiv.assert_called_once_with(config, target)
    assert [row['id'] for row in dedup.call_args.args[0]] == ['current']
    assert [row['id'] for row in translate.call_args.args[0]] == ['current']
    assert old['publishedAt'] == '2026-10-11T12:00:00Z'


def test_all_outside_week_stops_before_translation(monkeypatch,item):
    monkeypatch.setattr(weekly,'fetch_hf_daily_papers',lambda *args:[dict(item,publishedAt='2026-10-11T00:00:00Z')])
    monkeypatch.setattr(weekly,'fetch_arxiv_papers',lambda *args:[])
    dedup=Mock();translate=Mock()
    monkeypatch.setattr(weekly,'dedup_data',dedup)
    monkeypatch.setattr(weekly,'translate_papers',translate)
    assert weekly.fetch_weekly_papers({'fetch':{'target_date':'2026-10-18'}})==[]
    dedup.assert_not_called();translate.assert_not_called()
