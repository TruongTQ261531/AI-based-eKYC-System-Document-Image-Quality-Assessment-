"""Separate, ephemeral-image localhost V2 workbench; no label lookup at runtime."""
from functools import lru_cache
import threading
import time
import cv2
from PIL import Image
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from research.recovery_web import BodyLimit,privacy,decode_image
from research.v2_common import ROOT,CACHE,DATA,OUT,read,sha,signature,preserve_v1

WEB=ROOT/'research/v2_web'
app=FastAPI(title='V2 OCR Research',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','[::1]'])
app.add_middleware(BodyLimit);app.middleware('http')(privacy)
request_lock=threading.Lock()

def deployment():
    lock=read(OUT/'test_lock.json');audit=read(OUT/'audit.json');publication=read(OUT/'lock_publication.json')
    if lock['signature']!=signature() or audit['signature']!=lock['signature'] or audit['status']!='passed':raise ValueError('V2 audit/source mismatch')
    if publication['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('V2 seal differs from published lock')
    key=lock['selected_model'];record=lock['models'][key];path=(ROOT/record['path']).resolve()
    if not path.is_relative_to(CACHE.resolve()) or sha(path/'adapter_model.safetensors')!=record['sha256']:raise ValueError('V2 adapter mismatch')
    return lock,path

@lru_cache(1)
def engine():
    from peft import PeftModel
    from research.v2_runtime import VLM
    lock,path=deployment();preserve_v1();model=VLM(42,lock['profile'])
    model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    model.model.eval()
    return model,sha(OUT/'test_lock.json')

def predict(image):
    from research.vlm_train import process_lock
    from research.vlm_analysis import tolerant
    with process_lock():
        lock,_=deployment();model,loaded=engine()
        if loaded!=sha(OUT/'test_lock.json'):raise ValueError('Restart the web after changing adapter')
        result=model.fresh(Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB)))
        fields,parser=tolerant(result['text'])
        return dict(fields=fields,model=lock['selected_model'],profile=lock['profile'],
            recommended_on_development=lock['deployment_approved'],valid_extraction_format=parser['syntax_object_success'],
            inference_seconds=result['wall_seconds'],generated_tokens=result['generated_tokens'],
            view_mode=result['view_mode'],preprocessing_seconds=result['preprocessing_seconds'],
            source_dimensions=[image.shape[1],image.shape[0]],identity_approved=False,liveness_evaluated=False,
            warnings=['Đối chiếu từng trường với giấy tờ. Mô hình có thể bỏ sót hoặc đọc sai; trường thêm/sửa là do bạn nhập.']+
                     ([] if lock['deployment_approved'] else ['V2 chưa vượt cổng development; chỉ dùng khảo sát, chưa thay bản OCR hiện tại.']))

@app.get('/')
def index():return FileResponse(WEB/'index.html')

@app.get('/assets/{name}')
def asset(name:str):
    paths={'app.js':WEB/'app.js','style.css':WEB/'style.css','base.css':ROOT/'research/web/style.css'}
    if name not in paths:raise HTTPException(404)
    return FileResponse(paths[name])

@app.get('/api/health')
def health():
    try:
        lock,_=deployment()
        return dict(app_id='vlm_lora_research_v2',ready=True,model=lock['selected_model'],
            recommended=lock['deployment_approved'],profile=lock['profile'],
            message='Đã huấn luyện và audit. V2 dùng ảnh dựng và ảnh chụp giấy tờ mẫu; vẫn cần kiểm tra kết quả.' if lock['deployment_approved'] else
                    'Đã audit, nhưng V2 chưa vượt cổng development. Chỉ mở chế độ nghiên cứu khi bạn chủ động chọn.')
    except (OSError,ValueError,KeyError):
        state=read(CACHE/'workflow.json') if (CACHE/'workflow.json').exists() else {}
        return dict(app_id='vlm_lora_research_v2',ready=False,recommended=False,stage=state.get('stage','preparing'),
                    message='V2 đang được chuẩn bị hoặc chưa hoàn tất audit. Chưa có model được mở cho camera.')

@app.get('/api/specimen/{kind}')
def specimen(kind:str):
    if kind not in ('full','field_clip','value_mask'):raise HTTPException(404)
    # Deliberately no GT response, no private source file/ID endpoint.
    import hashlib
    uid='vlm_v2/train/001/partial/'+str({'full':0,'field_clip':3,'value_mask':4}[kind])
    path=DATA/'images'/(hashlib.sha256(uid.encode()).hexdigest()+'.png')
    if not path.exists():raise HTTPException(404)
    return FileResponse(path,media_type='image/png')

@app.post('/api/scan')
async def scan(request:Request):
    if request.headers.get('content-type','').split(';')[0] not in ('image/png','image/jpeg'):raise HTTPException(415,'Chỉ hỗ trợ PNG/JPEG.')
    try:lock,_=deployment()
    except (OSError,ValueError,KeyError):raise HTTPException(503,'V2 chưa sẵn sàng hoặc bằng chứng kiểm tra đã thay đổi.')
    if not lock['deployment_approved'] and request.headers.get('x-research-opt-in')!='yes':raise HTTPException(409,'V2 chưa vượt cổng development. Cần chủ động chọn chế độ nghiên cứu.')
    image=decode_image(await request.body());start=time.perf_counter()
    if not request_lock.acquire(blocking=False):raise HTTPException(429,'Đang xử lý ảnh trước. Vui lòng đợi.')
    try:
        result=await run_in_threadpool(predict,image);result['request_processing_wall_seconds']=time.perf_counter()-start
        return result
    except Exception:raise HTTPException(503,'Chưa chạy được V2. Kiểm tra GPU/tiến trình và thử lại.')
    finally:request_lock.release()
