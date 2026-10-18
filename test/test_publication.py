# ======================================================================
# 【白盒测试修改标识｜2026-10-18｜新增】
# 文件：test/test_publication.py
# 修改内容及原因：模拟微信/视频请求与发布编排，验证成功和失败路径，绝不真实发布。
# 范围：仅测试/测试配置；不修改生产逻辑，不执行真实外部发布。
# ======================================================================
"""微信/视频 API 与发布编排；只断言构造的请求，永不真实发送。"""
import importlib
import io
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError
import pytest
api=importlib.import_module('src.wechat.api')

@pytest.mark.parametrize('method,payload',[('get',None),('post',{'中文':'内容'}),('post',b'raw'),('post','text')])
@pytest.mark.parametrize('status',['ok','http','timeout'])
def test_wechat_http(monkeypatch,response,method,payload,status):
    error=HTTPError('https://example.org',500,'bad',{},io.BytesIO(b'error')) if status=='http' else TimeoutError('x')
    request=Mock(return_value=response({'ok':True}),side_effect=error if status!='ok' else None)
    monkeypatch.setattr(api.urllib.request,'urlopen',request)
    value=api.wechat_get('https://example.org','/p') if method=='get' else api.wechat_post('https://example.org','/p',payload)
    assert value==({'ok':True} if status=='ok' else None)
    if method=='post':
        sent=request.call_args.args[0].data
        assert isinstance(sent,bytes)
        if isinstance(payload,dict):assert json.loads(sent)==payload

@pytest.mark.parametrize('data,expected',[(None,None),({'errmsg':'denied'},None),({},None),({'access_token':'fake','expires_in':7200},'fake')])
def test_token(monkeypatch,data,expected):
    monkeypatch.setattr(api,'wechat_get',Mock(return_value=data))
    assert api.get_access_token('https://x','fake-id','fake-secret')==expected

@pytest.mark.parametrize('mode',['ok','error','missing'])
def test_upload_image(monkeypatch,response,mode):
    request=Mock(return_value=response({'media_id':'image'} if mode=='ok' else {'errcode':1}),side_effect=TimeoutError('x') if mode=='error' else None)
    monkeypatch.setattr(api.urllib.request,'urlopen',request)
    assert api.upload_image('https://x','fake',b'image')==('image' if mode=='ok' else None)
    assert b'filename="cover.png"' in request.call_args.args[0].data

@pytest.mark.parametrize('success',[True,False])
def test_create_draft(monkeypatch,success):
    post=Mock(return_value={'media_id':'draft'} if success else None);monkeypatch.setattr(api,'wechat_post',post)
    assert api.create_draft('https://x','fake','image','title','<p>body</p>','digest','https://source','author')==success
    article=post.call_args.args[2]['articles'][0]
    assert article['content']=='<p>body</p>' and article['thumb_media_id']=='image'

@pytest.fixture(params=['generate_wechat','generate_wechat_papers_weekly'])
def publisher(request):return importlib.import_module(request.param)

@pytest.mark.parametrize('env,args,expected',[('1',[],True),('true',[],True),('yes',[],True),('',[],False),('', ['--local-only'],True),('false',[],False)])
def test_local_switch(monkeypatch,publisher,env,args,expected):
    monkeypatch.setenv('WECHAT_LOCAL_ONLY',env);monkeypatch.setattr(sys,'argv',['script',*args])
    assert publisher.is_local_only()==expected

@pytest.mark.parametrize('empty',[True,False])
def test_local_artifacts(monkeypatch,publisher,tmp_path,item,empty):
    monkeypatch.setattr(publisher,'OUTPUT_DIR',tmp_path)
    monkeypatch.setattr(publisher,'get_now_date_str',lambda:'2026-10-18')
    weekly=publisher.__name__.endswith('weekly')
    if weekly:monkeypatch.setattr(publisher,'fetch_weekly_papers',Mock(return_value=[] if empty else [item]))
    else:
        monkeypatch.setattr(publisher,'fetch_news',Mock(return_value=[] if empty else [item]))
        monkeypatch.setattr(publisher,'fetch_papers',Mock(return_value=[] if empty else [item]))
        monkeypatch.setattr(publisher,'cross_dedup_news_papers',lambda n,p,c:(n,p))
    result=publisher.build_local_artifacts()
    if empty:
        assert result is None and list(tmp_path.iterdir())==[]
    else:
        stem='wechat_papers_weekly' if weekly else 'wechat'
        archive='wechat_papers_weekly' if weekly else 'wechat_draft'
        for ext in ('html','md'):
            assert (tmp_path/f'{stem}.{ext}').read_bytes()==(tmp_path/f'archive/{archive}/2026-10-18.{ext}').read_bytes()
            assert item['title'] in (tmp_path/f'{stem}.{ext}').read_text()

@pytest.mark.parametrize('stage',['credentials','token','image','draft','ok','papers_only','empty'])
def test_publish_stages(monkeypatch,publisher,item,stage):
    weekly=publisher.__name__.endswith('weekly')
    monkeypatch.setattr(publisher,'APPID','' if stage=='credentials' else 'fake')
    monkeypatch.setattr(publisher,'APPSECRET','fake')
    token=Mock(return_value=None if stage=='token' else 'token');monkeypatch.setattr(publisher,'get_access_token',token)
    monkeypatch.setattr(publisher,'generate_weekly_cover' if weekly else 'generate_cover',Mock(return_value=b'cover'))
    image=Mock(return_value=None if stage=='image' else 'image');monkeypatch.setattr(publisher,'upload_image',image)
    draft=Mock(return_value=stage!='draft');monkeypatch.setattr(publisher,'create_draft',draft)
    papers=[] if stage=='empty' else [item]
    args=(papers,'2026-10-18','html') if weekly else ([] if stage in ('papers_only','empty') else [item],papers,'2026-10-18','html')
    assert publisher.publish_to_wechat(*args)==(1 if stage in ('token','image','draft') else 0)
    if stage=='credentials':token.assert_not_called()
    if stage in ('credentials','token'):image.assert_not_called()
    if stage in ('credentials','token','image'):draft.assert_not_called()

@pytest.mark.parametrize('local,empty',[(False,False),(True,False),(False,True),(True,True)])
def test_publisher_main(monkeypatch,publisher,local,empty):
    weekly=publisher.__name__.endswith('weekly')
    monkeypatch.setattr(publisher,'is_local_only',lambda:local)
    artifact=([{}],'2026-10-18','html') if weekly else ([{}],[{}],'2026-10-18','html')
    monkeypatch.setattr(publisher,'build_local_artifacts',Mock(return_value=None if empty else artifact))
    publish=Mock(return_value=1);monkeypatch.setattr(publisher,'publish_to_wechat',publish)
    assert publisher.main()==(1 if not local and not empty else 0)
    assert publish.call_count==int(not local and not empty)

@pytest.mark.parametrize('mode',['missing','http','timeout','bad_response','ok','ok_url'])
def test_video_upload(monkeypatch,tmp_path,response,mode):
    video=importlib.import_module('generate_wechat_video')
    path=tmp_path/'clip.mp4'
    if mode!='missing':path.write_bytes(b'video')
    error=HTTPError('https://x',500,'bad',{},io.BytesIO(b'error')) if mode=='http' else TimeoutError('x')
    data={'media_id':'video'} if mode.startswith('ok') else {'errcode':1}
    if mode=='ok_url':data['url']='https://x/video'
    send=Mock(return_value=response(data),side_effect=error if mode in ('http','timeout') else None)
    monkeypatch.setattr(video.urllib.request,'urlopen',send)
    assert video.upload_video_material('https://x','fake',path,'Title','Description')==('video' if mode.startswith('ok') else None)
    if mode!='missing':
        body=send.call_args.args[0].data
        assert b'video' in body and b'Description' in body

@pytest.mark.parametrize('stage',['no_file','credentials','token','upload','ok','custom'])
def test_video_main(monkeypatch,tmp_path,stage):
    video=importlib.import_module('generate_wechat_video')
    monkeypatch.setattr(video,'DEFAULT_VIDEO','')
    monkeypatch.setattr(sys,'argv',['video'] if stage=='no_file' else ['video','--video','clip.mp4',*(['--title','custom','--introduction','intro'] if stage=='custom' else [])])
    monkeypatch.setattr(video,'APPID','' if stage=='credentials' else 'fake');monkeypatch.setattr(video,'APPSECRET','fake')
    monkeypatch.setattr(video,'get_access_token',Mock(return_value=None if stage=='token' else 'token'))
    upload=Mock(return_value=None if stage=='upload' else 'media');monkeypatch.setattr(video,'upload_video_material',upload)
    save=Mock();monkeypatch.setattr(video,'save_media_cache',save)
    assert video.main()==(2 if stage=='no_file' else 1 if stage in ('credentials','token','upload') else 0)
    assert save.call_count==int(stage in ('ok','custom'))
    if stage=='custom':assert upload.call_args.args[-2:]==('custom','intro')

def test_video_cache(monkeypatch,tmp_path):
    video=importlib.import_module('generate_wechat_video')
    monkeypatch.setattr(video,'OUTPUT_DIR',tmp_path);monkeypatch.setattr(video,'get_now_date_str',lambda:'2026-10-18')
    video.save_media_cache('media','clip.mp4','title','intro')
    assert json.loads((tmp_path/'archive/wechat_video/2026-10-18.json').read_text())['media_id']=='media'
