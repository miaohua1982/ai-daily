# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜重写】
# 文件：test/test_cover.py
# 修改内容及原因：用 PNG 格式、尺寸及字体回退断言替代导入即写文件的封面脚本。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""封面测试改为内存断言，避免导入测试模块就写 craft/cover.png。"""
import importlib
import io
from unittest.mock import Mock
from PIL import Image,ImageFont
import pytest
c=importlib.import_module('src.wechat.cover')

@pytest.mark.parametrize('weekly',[False,True])
def test_cover_png(weekly):
    content=c.generate_weekly_cover('2026-10-18',10) if weekly else c.generate_cover('2026-10-18',1,10)
    with Image.open(io.BytesIO(content)) as image:
        assert image.format=='PNG' and image.size==(c.COVER_W,c.COVER_H)
        image.verify()

def test_font_fallbacks(monkeypatch,tmp_path):
    marker=ImageFont.load_default()
    font=tmp_path/'font.ttf';font.write_bytes(b'fake')
    monkeypatch.setattr(c.ImageFont,'truetype',Mock(return_value=marker))
    monkeypatch.setattr(c,'CHINESE_FONT_CANDIDATES',[str(font)])
    assert c._find_chinese_font(12) is marker
    monkeypatch.setattr(c,'CHINESE_FONT_CANDIDATES',[])
    import subprocess
    monkeypatch.setattr(subprocess,'check_output',Mock(return_value=f'\n{font}\n'))
    assert c._find_chinese_font(12) is marker
    monkeypatch.setattr(subprocess,'check_output',Mock(side_effect=OSError('no fontconfig')))
    monkeypatch.setattr(c,'WIN_FONTS_DIR',str(tmp_path))
    monkeypatch.setattr(c,'WIN_FONT_KEYWORDS',['cjk'])
    (tmp_path/'plain.ttf').write_bytes(b'fake');(tmp_path/'cjk.ttf').write_bytes(b'fake')
    assert c._find_chinese_font(12) is marker
    monkeypatch.setattr(c,'WIN_FONTS_DIR',str(tmp_path/'missing'))
    monkeypatch.setattr(c.ImageFont,'load_default',Mock(return_value=marker))
    assert c._find_chinese_font(12) is marker
    monkeypatch.setattr(c,'_find_chinese_font',Mock(side_effect=OSError('no font')))
    assert c._load_fonts()==(marker,)*6
