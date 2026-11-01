"""Opt-in localhost LoRA workbench; camera input stays in memory, no identity approval."""
import json
from functools import lru_cache
from pathlib import Path
import threading
import time

import cv2
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,Response
from PIL import Image
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from research.recovery_web import BodyLimit,privacy,decode_image
from research.vlm_setup import ROOT,OUT,CACHE,sha

WEB=ROOT/'research/vlm_web'
app=FastAPI(title='Local Vintern LoRA Research',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','[::1]'])
app.add_middleware(BodyLimit)
app.middleware('http')(privacy)
request_lock=threading.Lock()


def deployment():
    from research.vlm_runtime import signature
    lock=json.loads((OUT/'test_lock.json').read_text(encoding='utf-8'))
    audit=json.loads((OUT/'audit.json').read_text(encoding='utf-8'))
    provenance=json.loads((OUT/'report_provenance.json').read_text(encoding='utf-8'))
    if lock['signature']!=signature() or audit['signature']!=lock['signature'] or audit['status']!='passed':
        raise ValueError('Study source/audit changed')
    if provenance['model_lock_sha256']!=sha(OUT/'test_lock.json') or provenance['audit_sha256']!=sha(OUT/'audit.json'):
        raise ValueError('Published deployment evidence changed')
    if not lock['deployment_approved']:raise ValueError('Development deployment gate did not pass')
    record=lock['adapters'][lock['selected_model'].split('_')[1]]
    path=(ROOT/record['selected_checkpoint']).resolve()
    if not path.is_relative_to(CACHE.resolve()):raise ValueError('Invalid local checkpoint path')
    if sha(path/'adapter_model.safetensors')!=record['selected_adapter_sha256']:raise ValueError('Selected adapter changed')
    return lock,path


@lru_cache(1)
def engine():
    from peft import PeftModel
    from research.vlm_runtime import VLM
    lock,path=deployment();model=VLM()
    model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    model.model.eval()
    return model,lock,sha(OUT/'test_lock.json')


def predict_image(image):
    import torch
    from research.vlm_runtime import pixels,parsed
    from research.vlm_train import process_lock
    with process_lock():
        model,lock,loaded_seal=engine()
        if loaded_seal!=sha(OUT/'test_lock.json'):raise ValueError('Restart after changing model choice')
        torch.cuda.synchronize();start=time.perf_counter()
        tensor=pixels(Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))).to(device='cuda',dtype=model.dtype)
        with torch.no_grad():features=model.model.extract_feature(tensor)
        text,tokens=model.infer_features(features);torch.cuda.synchronize();fields,valid=parsed(text)
        return dict(fields=fields,model=lock['selected_model'],valid_extraction_format=valid,
                    generated_tokens=tokens,inference_seconds=time.perf_counter()-start,
                    liveness_evaluated=False,identity_approved=False,
                    warnings=['Hãy đối chiếu từng thông tin với ảnh trước khi xác nhận.'] if valid else
                             ['Mô hình chưa trả được thông tin đúng định dạng. Hãy chụp lại hoặc dùng bản OCR hiện tại.'])


@app.get('/')
def index():return FileResponse(WEB/'index.html')


@app.get('/assets/{name}')
def assets(name:str):
    if name=='style.css':return FileResponse(ROOT/'research/web/style.css')
    if name=='app.js':return FileResponse(WEB/'app.js')
    raise HTTPException(404)


@app.get('/api/health')
def health():
    try:
        lock,_=deployment()
        return dict(app_id='vlm_lora_research_v1',ready=True,model=lock['selected_model'],message='LoRA đã qua cổng development và audit. Đây là bản thử nghiệm trên dữ liệu giả lập.')
    except (OSError,ValueError,KeyError):
        state=json.loads((CACHE/'workflow.json').read_text(encoding='utf-8')) if (CACHE/'workflow.json').exists() else {}
        return dict(app_id='vlm_lora_research_v1',ready=False,stage=state.get('stage','not_prepared'),message='Mô hình chưa sẵn sàng hoặc chưa đạt điều kiện triển khai. Bạn có thể mở bản OCR hiện tại.')


@app.get('/api/specimen/{kind}')
def specimen(kind:str):
    # Training-only mock images for UI QA; this endpoint never returns labels.
    if kind not in ('full','field_clip','value_mask'):raise HTTPException(404)
    path=ROOT/f'research/data/vlm_lora_v1/images/vlm_lora_v1_train_001_{kind}.png'
    if not path.exists():raise HTTPException(404)
    return FileResponse(path,media_type='image/png')


@app.post('/api/scan')
async def scan(request:Request):
    started=time.perf_counter()
    if request.headers.get('content-type','').split(';')[0] not in ('image/jpeg','image/png'):raise HTTPException(415,'Chỉ hỗ trợ ảnh JPEG hoặc PNG.')
    try:deployment()
    except (OSError,ValueError,KeyError):raise HTTPException(503,'LoRA chưa sẵn sàng hoặc chưa được duyệt triển khai theo development/audit.')
    image=decode_image(await request.body())
    if not request_lock.acquire(blocking=False):raise HTTPException(429,'Đang xử lý ảnh trước. Hãy đợi rồi thử lại.')
    try:
        result=await run_in_threadpool(predict_image,image)
        result['source_dimensions']=[image.shape[1],image.shape[0]]
        result['request_processing_wall_seconds']=time.perf_counter()-started
        return result
    except HTTPException:raise
    except Exception:raise HTTPException(503,'Chưa chạy được mô hình. Kiểm tra tiến trình huấn luyện/GPU và thử lại.')
    finally:request_lock.release()
