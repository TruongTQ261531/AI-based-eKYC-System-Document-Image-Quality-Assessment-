"""Ephemeral localhost source-reference OCR workbench; no dataset lookup in predict."""
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
from research.v3_common import ROOT,CACHE,R2CACHE,OUT,read,sha,signature,preserve_v1

WEB=ROOT/'research/v3_web'
app=FastAPI(title='Source-aware OCR Research',docs_url=None,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','[::1]'])
app.add_middleware(BodyLimit);app.middleware('http')(privacy)
request_lock=threading.Lock()

def deployment():
    lock=read(OUT/'test_lock.json');audit=read(OUT/'audit.json');pub=read(OUT/'lock_publication.json')
    if lock['signature']!=signature() or audit['signature']!=lock['signature'] or audit['status']!='passed':raise ValueError('Source study audit/source mismatch')
    if pub['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('Source seal changed')
    record=lock['models'][lock['selected_model']]
    path=(ROOT/record['path']).resolve() if record['path'] else None
    if path:
        allowed=(CACHE.resolve(),R2CACHE.resolve(),(ROOT/'research/cache/vlm_lora_v1').resolve())
        if not any(path.is_relative_to(folder) for folder in allowed) or sha(path/'adapter_model.safetensors')!=record['sha256']:raise ValueError('Adapter mismatch')
    return lock,path

@lru_cache(1)
def engine():
    from research.v2_runtime import VLM
    lock,path=deployment();preserve_v1();model=VLM(42,lock['profile'])
    if path:
        from peft import PeftModel
        model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    model.model.eval()
    return model,sha(OUT/'test_lock.json')

def predict(image):
    from research.vlm_train import process_lock
    from research.vlm_analysis import tolerant
    from research.v3_metrics import date_value
    with process_lock():
        lock,_=deployment();model,loaded=engine()
        if loaded!=sha(OUT/'test_lock.json'):raise ValueError('Restart after changing selected adapter')
        result=model.fresh(Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB)))
        fields,parser=tolerant(result['text'])
        warnings=['Đối chiếu từng trường với giấy tờ. Trường thêm hoặc sửa được đánh dấu do bạn nhập.']
        if any((date_value(v) or ('',))[0]=='year2' for k,v in fields.items() if k in ('dob','expiry_date','issue_date')):
            warnings.append('Có ngày chỉ đọc được năm hai chữ số. Hệ thống giữ nguyên, không tự suy đoán thế kỷ.')
        if not lock['deployment_approved']:warnings.append('Chưa vượt cổng đánh giá trên tập phát triển; chỉ dùng khảo sát.')
        return dict(fields=fields,model=lock['selected_model'],profile=lock['profile'],
            recommended_on_development=lock['deployment_approved'],valid_extraction_format=parser['syntax_object_success'],
            inference_seconds=result['wall_seconds'],generated_tokens=result['generated_tokens'],
            view_mode=result['view_mode'],preprocessing_seconds=result['preprocessing_seconds'],
            source_dimensions=[image.shape[1],image.shape[0]],identity_approved=False,liveness_evaluated=False,warnings=warnings)

@app.get('/')
def index():return FileResponse(WEB/'index.html')

@app.get('/assets/{name}')
def asset(name:str):
    paths={'app.js':WEB/'app.js','style.css':ROOT/'research/v2_web/style.css','base.css':ROOT/'research/web/style.css'}
    if name not in paths:raise HTTPException(404)
    return FileResponse(paths[name])

@app.get('/api/health')
def health():
    try:
        lock,_=deployment()
        return dict(app_id='source_visibility_v3',ready=True,recommended=lock['deployment_approved'],model=lock['selected_model'],profile=lock['profile'],
            message='Đã huấn luyện và kiểm tra. Vẫn cần đối chiếu chữ với giấy tờ.' if lock['deployment_approved'] else
            'Đã kiểm tra nhưng chưa vượt cổng tập phát triển. Chỉ thử khi chủ động chọn chế độ nghiên cứu.')
    except (OSError,ValueError,KeyError):
        state=read(CACHE/'workflow.json') if (CACHE/'workflow.json').exists() else {}
        return dict(app_id='source_visibility_v3',ready=False,recommended=False,stage=state.get('stage','preparing'),
            message='Đang huấn luyện hoặc kiểm tra kết quả; chưa mở model cho camera.')

@app.get('/api/specimen/{kind}')
def specimen(kind:str):
    # Training SPECIMENs only; shared endpoint never returns reference fields.
    from research.v2_web import specimen as training_specimen
    return training_specimen(kind)

@app.post('/api/scan')
async def scan(request:Request):
    if request.headers.get('content-type','').split(';')[0] not in ('image/png','image/jpeg'):raise HTTPException(415,'Chỉ hỗ trợ PNG/JPEG.')
    try:lock,_=deployment()
    except (OSError,ValueError,KeyError):raise HTTPException(503,'Chưa hoàn tất kiểm tra model hoặc bằng chứng đã thay đổi.')
    if not lock['deployment_approved'] and request.headers.get('x-research-opt-in')!='yes':raise HTTPException(409,'Cần chủ động chọn chế độ nghiên cứu.')
    image=decode_image(await request.body());start=time.perf_counter()
    if not request_lock.acquire(blocking=False):raise HTTPException(429,'Đang xử lý ảnh trước. Vui lòng đợi.')
    try:
        result=await run_in_threadpool(predict,image);result['request_processing_wall_seconds']=time.perf_counter()-start
        return result
    except Exception:raise HTTPException(503,'Chưa chạy được model. Kiểm tra GPU và tiến trình, rồi thử lại.')
    finally:request_lock.release()
