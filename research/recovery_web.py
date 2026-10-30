"""Local-only research workbench. No camera image or OCR text is persisted."""
import base64
import io
import json
import threading
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import cv2
import numpy as np
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from PIL import Image,ImageOps,UnidentifiedImageError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool

from research.recovery_runtime import RecoveryEngine

ROOT=Path(__file__).resolve().parent
WEB=ROOT/'web'
OUT=ROOT/'results/recovery_v4'
MAX_BODY=30*1024*1024
MAX_PIXELS=32_000_000
inference_lock=threading.Lock()
app=FastAPI(title='Document Recovery Research',version='4.0.0',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','[::1]'])


class BodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method']!='POST':return await self.app(scope,receive,send)
        blocks=[];total=0
        while True:
            event=await receive()
            if event['type']=='http.disconnect':return
            total+=len(event.get('body',b''))
            if total>MAX_BODY:
                return await JSONResponse({'detail':'Ảnh vượt giới hạn30MB.'},status_code=413,headers={'Cache-Control':'no-store'})(scope,receive,send)
            blocks.append(event.get('body',b''))
            if not event.get('more_body',False):break
        sent=False
        async def replay():
            nonlocal sent
            if sent:return await receive()
            sent=True;return {'type':'http.request','body':b''.join(blocks),'more_body':False}
        await self.app(scope,replay,send)


app.add_middleware(BodyLimit)


@app.middleware('http')
async def privacy(request,call_next):
    if request.client and request.client.host not in ('127.0.0.1','::1','localhost','testclient'):
        return JSONResponse({'detail':'Localhost only'},status_code=403)
    if request.method=='POST':
        origin=request.headers.get('origin');actual=urlsplit(str(request.base_url))
        supplied=urlsplit(origin) if origin else None
        if request.headers.get('sec-fetch-site')=='cross-site' or supplied and (supplied.scheme,supplied.netloc)!=(actual.scheme,actual.netloc):
            return JSONResponse({'detail':'Cross-origin request denied'},status_code=403,headers={'Cache-Control':'no-store'})
    response=await call_next(request)
    response.headers.update({'Cache-Control':'no-store','Pragma':'no-cache','Referrer-Policy':'no-referrer',
        'X-Content-Type-Options':'nosniff','Permissions-Policy':'camera=(self), microphone=()',
        'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"})
    return response


@lru_cache(1)
def engine():return RecoveryEngine()


def locked_model():
    from research.recovery_assets import sha
    try:
        lock=json.loads((OUT/'selector_lock.json').read_text());model_path=OUT/'selector_models.json'
        if sha(model_path)!=lock['model_sha256']:raise ValueError('Model lock mismatch')
        model=json.loads(model_path.read_text());manifest=json.loads((OUT/'manifest.json').read_text())
        if model['signature']!=lock['signature'] or lock['signature']!=manifest['signature']:raise ValueError('Experiment signature mismatch')
        if any(sha(ROOT/name)!=value for name,value in manifest['code_sha256'].items()):raise ValueError('Runtime code differs from frozen study')
        return model
    except (OSError,ValueError,KeyError):raise HTTPException(503,'Mô hình chọn view chưa được khóa. Benchmark đang hoàn thiện; chưa có kết quả giả lập thay thế.')


def decode_image(raw):
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('JPEG','PNG'):raise HTTPException(415,'Chỉ hỗ trợ ảnh JPEG hoặc PNG.')
            if image.width*image.height>MAX_PIXELS:raise HTTPException(413,'Ảnh vượt giới hạn32 triệu pixel.')
            if min(image.size)<64:raise HTTPException(400,'Ảnh quá nhỏ để đọc giấy tờ.')
            image=ImageOps.exif_transpose(image).convert('RGB')
            return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
    except HTTPException:raise
    except (OSError,UnidentifiedImageError,Image.DecompressionBombError,ValueError):
        raise HTTPException(400,'Không đọc được ảnh. Hãy chụp lại.')


@app.get('/')
def index():return FileResponse(WEB/'index.html')


@app.get('/assets/{name}')
def asset(name:str):
    if name not in ('app.js','style.css'):raise HTTPException(404)
    return FileResponse(WEB/name)


@app.get('/api/health')
def health():
    counts=[len(list((ROOT/'cache/recovery_v4'/f'pass{i}').glob('*.json'))) for i in (1,2,3)]
    return dict(status='ready',app_id='research_recovery_v4',selector_ready=(OUT/'selector_lock.json').exists(),
                completed=sum(counts),expected=588,mentor_server_unchanged=True)


@app.get('/api/results')
def results():
    if not (OUT/'summary.json').exists() or not (OUT/'independent_audit.json').exists():
        return dict(status='running',rows=[],message='Chờ chấm và audit điểm test sau khi khóa selector.')
    rows=json.loads((OUT/'summary.json').read_text())
    models=json.loads((OUT/'selector_models.json').read_text())
    return dict(status='complete',rows=[r for r in rows if r['role']=='test'],
        primary_methods={key:value['primary_method'] for key,value in models['selectors'].items()},
        dataset=json.loads((OUT/'dataset_card.json').read_text()),
        latency_note='Selector trong bảng dùng chi phí tái dựng trace; thời gian xử lý camera bên dưới được đo thực tế.')


@app.get('/api/specimen/{kind}')
def specimen(kind:str):
    if kind not in ('full','corner_clip','field_clip','blur_glare'):raise HTTPException(404)
    path=ROOT/'data/recovery_v4/synthetic'/f'specimen_L0_00_{kind}.png'
    if not path.exists():raise HTTPException(503,'Chưa tạo ảnh SPECIMEN.')
    return FileResponse(path,media_type='image/png')


@app.post('/api/scan')
async def scan(request:Request):
    request_started=time.perf_counter()
    if request.headers.get('content-type','').split(';')[0] not in ('image/jpeg','image/png'):
        raise HTTPException(415,'Gửi trực tiếp ảnh JPEG hoặc PNG.')
    model=locked_model();raw=await request.body()
    if not raw:raise HTTPException(400,'Chưa có ảnh chụp.')
    if not inference_lock.acquire(blocking=False):raise HTTPException(429,'Đang xử lý một ảnh khác. Hãy thử lại sau.')
    try:
        image=decode_image(raw)
        result=await run_in_threadpool(engine().online,image,model)
        from ekyc.document_fields import observed_information,LABELS
        _,items,_=observed_information(result['predictions'],{})
        result['field_labels']={**LABELS,**{item['key']:item['label'] for item in items}}
        preview=result.pop('_private_preview');scale=min(1.,1280/max(preview.shape[:2]))
        preview=cv2.resize(preview,None,fx=scale,fy=scale)
        ok,encoded=cv2.imencode('.jpg',preview,[cv2.IMWRITE_JPEG_QUALITY,88])
        if not ok:raise RuntimeError('Preview encoding failed')
        result['preview_data_url']='data:image/jpeg;base64,'+base64.b64encode(encoded).decode('ascii')
        result['source_dimensions']=[image.shape[1],image.shape[0]]
        result['privacy']='Ảnh và text không được ghi vào file hoặc phiên máy chủ.'
        result['request_processing_wall_seconds']=time.perf_counter()-request_started
        return result
    except HTTPException:raise
    except Exception:raise HTTPException(500,'Xử lý OCR gặp lỗi. Không lưu ảnh. Hãy thử lại hoặc kiểm tra terminal máy chủ.')
    finally:inference_lock.release()
