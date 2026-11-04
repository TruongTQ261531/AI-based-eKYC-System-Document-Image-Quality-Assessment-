"""Loopback annotation catalog and blinded tasks in the existing FastAPI stack."""
from functools import lru_cache
import io
from urllib.parse import urlparse
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,Response,JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from PIL import Image,ImageOps
from research.labels_common import *
from research import labels_review

def evaluation():
    return sample_rows() if (OUT/'evaluation_card.json').exists() else []

def get_sample(key):
    if len(key)!=64 or any(c not in '0123456789abcdef' for c in key):raise KeyError(key)
    if DB.exists():
        with connect() as conn:
            row=conn.execute('SELECT * FROM images WHERE uid=?',(key,)).fetchone()
            if row:
                result=dict(row);result['input_sha256']=result.pop('sha256');result['uid']=result.pop('native_uid')
                result['annotation_uid']=key;result['metadata']=json.loads(result['metadata'])
                result['fields']=[json.loads(f[0]) for f in conn.execute('SELECT annotation FROM fields WHERE image_uid=? ORDER BY field_id',(key,))]
                return result
    found=next((r for r in evaluation() if r['annotation_uid']==key),None)
    if found is None:raise KeyError(key)
    return found

def list_samples(cohort,source,quality,offset,limit):
    if cohort=='evaluation':
        rows=[r for r in evaluation() if not source or r['source']==source]
        return len(rows),[dict(id=r['annotation_uid'],name=r['uid'],source=r['source'],quality=None,
                        role=r['role'],fields=len(r['fields'])) for r in rows[offset:offset+limit]]
    if not DB.exists():return 0,[]
    clauses=[];args=[]
    if source:clauses.append('source=?');args.append(source)
    if quality:clauses.append('quality=?');args.append(quality)
    where=' WHERE '+' AND '.join(clauses) if clauses else ''
    with connect() as conn:
        count=conn.execute('SELECT COUNT(*) FROM images'+where,args).fetchone()[0]
        rows=conn.execute('SELECT uid,native_uid,source,quality,role FROM images'+where+' ORDER BY native_uid LIMIT ? OFFSET ?',args+[limit,offset]).fetchall()
    return count,[dict(id=r['uid'],name=r['native_uid'],source=r['source'],quality=r['quality'],role=r['role']) for r in rows]

def review_tasks():
    if (OUT/'human_review_plan.json').exists():
        plan=read(OUT/'human_review_plan.json')
        if plan['evaluation_sha256']!=sha(DATA/'evaluation.json'):raise ValueError('Registered human panel differs')
        return plan['task_ids']
    rows=evaluation();chosen=[]
    for source in ('authored','midv2020'):
        ids=sorted({r['physical_id'] for r in rows if r['source']==source and r['physical_id']!='ocr-labels-v1-fictional-000'},key=lambda p:uid('label-review-20261104/'+p))[:24]
        for index,pid in enumerate(ids):
            candidates=[r for r in rows if r['physical_id']==pid and r['capture']==('full' if index%2==0 else 'value_mask')]
            selected=min(candidates,key=lambda r:uid('blind-condition/'+r['uid']))
            chosen.append(selected['annotation_uid'])
    return chosen

def create_app(sample_lookup=get_sample,listing=list_samples,tasks=review_tasks,review_path=REVIEW_DB):
    app=FastAPI(title='OCR annotation review',docs_url=None,redoc_url=None)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])
    @app.middleware('http')
    async def privacy(request,call_next):
        if request.method=='POST':
            origin=request.headers.get('origin')
            if origin:
                try:parsed=urlparse(origin);port=parsed.port or (443 if parsed.scheme=='https' else 80)
                except ValueError:return JSONResponse({'detail':'Nguồn gửi không hợp lệ.'},status_code=403)
                expected=request.url.port or (443 if request.url.scheme=='https' else 80)
                if parsed.scheme not in ('http','https') or parsed.hostname not in ('127.0.0.1','localhost','testserver') or port!=expected:
                    return JSONResponse({'detail':'Chỉ gửi đánh giá từ trang localhost này.'},status_code=403)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
            'Content-Security-Policy':"default-src 'self'; img-src 'self' blob:; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"})
        return response
    def sample(key):
        try:return sample_lookup(key)
        except KeyError:raise HTTPException(404,'Không có mẫu ảnh này.')
    @app.get('/')
    async def page():return FileResponse(ROOT/'web/labels_review.html')
    @app.get('/labels_review.js')
    async def js():return FileResponse(ROOT/'web/labels_review.js',media_type='application/javascript')
    @app.get('/labels_review.css')
    async def css():return FileResponse(ROOT/'web/labels_review.css',media_type='text/css')
    @app.get('/api/health')
    async def health():
        ready=(OUT/'corpus_release.json').exists()
        return dict(app_id='ocr_labels_v1',ready=ready,corpus_images=read(OUT/'corpus_release.json')['images'] if ready else 0,
            evaluation_images=len(evaluation()),review=labels_review.status(review_path),new_camera_collection=False)
    @app.get('/api/samples')
    async def catalog(cohort:str='legacy',source:str='',quality:str='',offset:int=0,limit:int=20):
        if cohort not in ('legacy','evaluation') or not 0<=offset<=100000 or not 1<=limit<=100:raise HTTPException(422,'Bộ lọc không hợp lệ.')
        total,items=listing(cohort,source,quality,offset,limit)
        return dict(total=total,offset=offset,items=items)
    @app.get('/api/sample/{key}')
    async def annotation(key:str):
        row=sample(key)
        return dict(id=key,width=row['width'],height=row['height'],source=row['source'],name=row['uid'],
            fields=row['fields'],quality=row.get('quality'),role=row['role'],answer_source='Tác giả/bộ dựng; chưa xác minh khả năng đọc của người')
    @app.get('/api/blind/tasks')
    async def blind_manifest():return dict(ids=tasks(),answers_included=False,independence='Tự khai; chưa được hệ thống xác minh')
    @app.get('/api/blind/{key}')
    async def blind(key:str):
        if key not in tasks():raise HTTPException(404,'Không thuộc bộ đánh giá độc lập.')
        row=sample(key)
        # Do not send reference values, character labels, OCR predictions or another view of this ID.
        return dict(id=key,width=row['width'],height=row['height'],name='Mẫu đánh giá độc lập',fields=[
            dict(field_id=f['field_id'],raw_key=f['raw_key'],semantic_key=f.get('semantic_key'),polygon=f['polygon']) for f in row['fields']],answers_included=False)
    @app.get('/api/image/{key}')
    async def image(key:str):
        row=sample(key);path=ROOT/row['path']
        if sha(path)!=row['input_sha256']:raise HTTPException(409,'Ảnh gốc đã thay đổi, cần kiểm tra lại nhãn.')
        with Image.open(path) as opened:
            im=ImageOps.exif_transpose(opened) if row['coordinate_mode']=='exif_display' else opened
            im=im.convert('RGB');buf=io.BytesIO();im.save(buf,format='PNG')
        return Response(buf.getvalue(),media_type='image/png')
    @app.post('/api/reviews/{key}')
    async def submit(key:str,request:Request):
        raw=await request.body()
        if len(raw)>262144:raise HTTPException(413,'Bản đánh giá quá lớn.')
        try:
            payload=json.loads(raw);event=labels_review.store(sample(key),payload,review_path)
        except (ValueError,TypeError,KeyError):raise HTTPException(422,'Kiểm tra trạng thái, phần chữ quan sát được và vùng đề xuất của từng trường.')
        return dict(saved=True,event_id=event['event_id'],released_reference_changed=False,independence_verified=False)
    @app.get('/api/reviews/export')
    async def export():
        value=dict(version='ocr_labels_v1_proposals',released_reference_changed=False,events=labels_review.events(review_path))
        return Response(canonical(value),media_type='application/json',headers={'Content-Disposition':'attachment; filename="ocr-label-review-proposals.json"'})
    @app.get('/api/reviews/verified')
    async def verified():
        registry=read(DATA/'reviewer_registry.json') if (DATA/'reviewer_registry.json').exists() else {}
        return dict(fields=labels_review.export_verified(review_path,registry),basis='Chỉ reviewer đã được người quản lý xác nhận độc lập; không dùng OCR làm nhãn người')
    @app.get('/api/reviews/single')
    async def single():
        registry=read(DATA/'reviewer_registry.json') if (DATA/'reviewer_registry.json').exists() else {}
        value=dict(version='ocr_labels_v1_single_review',consensus_verified=False,assessments=labels_review.export_single(review_path,registry))
        return Response(canonical(value),media_type='application/json',headers={'Content-Disposition':'attachment; filename="ocr-label-single-review.json"'})
    return app

app=create_app()
