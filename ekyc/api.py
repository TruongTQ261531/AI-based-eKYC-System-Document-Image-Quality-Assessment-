"""Camera workflow API: short-lived in-memory sessions, no persistent PII."""
import io
import os
import secrets
import time
from contextlib import asynccontextmanager
from datetime import date
from functools import lru_cache
from threading import Lock, Event, Thread
from urllib.parse import urlsplit

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.formparsers import MultiPartParser
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import ROOT, Settings
from .io import StageError
from .pipeline import EKYCPipeline

MAX_CARD = 30 * 1024 * 1024
MAX_PIXELS = 32_000_000
MAX_BODY = MAX_CARD + 1024 * 1024
MAX_LIVE_FRAME = 750 * 1024
MAX_LIVE_BODY = MAX_LIVE_FRAME + 64 * 1024
# The bounded ASGI reader below guarantees multipart files never reach the
# disk-spooling threshold. UploadFile alone would spool large photos to disk.
MultiPartParser.spool_max_size = MAX_BODY
SESSION_TTL = 600
sessions = {}
session_lock = Lock()
inference_lock = Lock()


def purge_expired():
    now = time.monotonic()
    with session_lock:
        for token in list(sessions):
            if sessions[token]['expires'] <= now:
                sessions.pop(token, None)


@asynccontextmanager
async def lifespan(app):
    stop = Event()
    def cleanup():
        while not stop.wait(15):
            purge_expired()
    thread = Thread(target=cleanup, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=2)
        with session_lock:
            sessions.clear()
        if hasattr(get_observer, 'cache_info') and get_observer.cache_info().currsize:
            get_observer().close()
            get_observer.cache_clear()


app = FastAPI(title='Local eKYC Camera', version='3.2.0', lifespan=lifespan)
allowed_hosts = ['localhost', '127.0.0.1', '[::1]']
allowed_hosts += [h.strip() for h in os.environ.get('EKYC_ALLOWED_HOSTS', '').split(',') if h.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


class BoundedBody:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] not in ('POST', 'PUT', 'PATCH'):
            return await self.app(scope, receive, send)
        limit = (MAX_LIVE_BODY if scope['path']=='/api/liveness/frame' else
                 8192 if scope['path'] in ('/api/confirm','/api/liveness/start') else MAX_BODY)
        chunks, total = [], 0
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return
            block = event.get('body', b'')
            total += len(block)
            if total > limit:
                response = JSONResponse({'detail': 'Yêu cầu quá lớn.'}, status_code=413,
                                        headers={'Cache-Control': 'no-store'})
                return await response(scope, receive, send)
            chunks.append(block)
            if not event.get('more_body', False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}
        await self.app(scope, replay, send)


app.add_middleware(BoundedBody)


@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    # FastAPI's default validation payload can echo submitted personal data.
    return JSONResponse({'detail': 'Thông tin gửi lên không hợp lệ.'}, status_code=422)


@app.middleware('http')
async def privacy_and_origin(request: Request, call_next):
    if request.url.hostname not in ('localhost', '127.0.0.1', '::1') and request.url.scheme != 'https':
        return JSONResponse({'detail': 'HTTPS required'}, status_code=403)
    origin = request.headers.get('origin')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        expected = urlsplit(str(request.base_url))
        supplied = urlsplit(origin) if origin else None
        if request.headers.get('sec-fetch-site') == 'cross-site' or (
            supplied and (supplied.scheme, supplied.netloc) != (expected.scheme, expected.netloc)
        ):
            return JSONResponse({'detail': 'Cross-origin request denied'}, status_code=403)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Permissions-Policy'] = 'camera=(self), microphone=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )
    return response


@lru_cache
def get_pipeline():
    import torch
    torch.set_num_threads(min(4,torch.get_num_threads()))
    return EKYCPipeline()


@lru_cache
def get_observer():
    from .face_observation import FaceObservation
    cv2.setNumThreads(2)
    return FaceObservation(Settings().models_dir)


@lru_cache
def get_pad():
    from .presentation_attack import PresentationAttackDetection
    return PresentationAttackDetection(Settings().models_dir)


def observe_live_capture(image):
    observation = dict(get_observer().observe(image))
    if observation.get('face_count') == 1:
        try:
            result = get_pad().check(image, get_pipeline().faces)
        except Exception:
            # PAD failures are service failures, not a retryable face-crop error.
            # Both calling routes revoke challenge state on this exception.
            raise RuntimeError('PAD inference unavailable') from None
        # Never disclose raw PAD scores or accept measurements from the client.
        observation['pad'] = {key:result[key] for key in ('decision','method')}
    return observation


@app.get('/')
def home():
    return FileResponse(ROOT/'web/index.html')


@app.get('/app.js')
def javascript():
    return FileResponse(ROOT/'web/app.js', media_type='text/javascript')


@app.get('/style.css')
def stylesheet():
    return FileResponse(ROOT/'web/style.css', media_type='text/css')


@app.get('/api/health')
def health():
    from .live_challenge import LiveChallenge
    settings = Settings()
    required = [settings.quality_model] + [settings.models_dir/name for name in (
        'face_detection_yunet_2023mar.onnx', 'face_recognition_sface_2021dec.onnx',
        'face_landmarker.task', 'easyocr/craft_mlt_25k.pth', 'scanocr/yolo_v11_best.onnx', 'scanocr/vgg_transformer.pth',
        'scanocr/base.yml', 'scanocr/vgg-transformer.yml',
        'pad/MiniFASNetV2.onnx', 'pad/MiniFASNetV1SE.onnx')]
    missing = [p.name for p in required if not p.is_file()]
    return dict(status='ready' if not missing else 'setup_required', missing=missing,
                api_version=app.version, quality_checkpoint=settings.quality_model.name,
                document_portrait_method='yunet_rotations_multiview_v1',
                ocr_engine='scanocr_vietocr_generic', ocr_language='vi', document_fields='observed_only',
                liveness_enabled=True, liveness_method='server_random_motion_challenge_v1',
                liveness_action_count=4,liveness_timeout_seconds=LiveChallenge.lifetime,
                presentation_attack_detection='minifasnet_v2_v1se_rgb_v1', pad_certified=False,
                session_ttl_seconds=SESSION_TTL)


def decode_capture(upload, *, live=False):
    try:
        limit = MAX_LIVE_FRAME if live else MAX_CARD
        raw = upload.file.read(limit + 1)
        if live and len(raw)>limit:
            raise HTTPException(413, 'Khung hình kiểm tra quá lớn. Vui lòng mở lại camera.')
        if len(raw) > limit:
            raise HTTPException(413, 'Ảnh vượt quá 30 MB. Vui lòng giảm độ phân giải camera.')
        if not raw:
            raise HTTPException(400, 'Ảnh trống.')
        # Inspect dimensions before native decode to limit decompression allocations.
        with Image.open(io.BytesIO(raw)) as probe:
            if probe.format not in ('JPEG', 'PNG', 'WEBP'):
                raise HTTPException(400, 'Camera cần gửi ảnh JPEG, PNG hoặc WebP.')
            if live and probe.width * probe.height > 1_200_000:
                raise HTTPException(413, 'Khung hình kiểm tra vượt quá độ phân giải cho phép.')
            if probe.width * probe.height > MAX_PIXELS:
                raise HTTPException(413, 'Ảnh vượt quá 32 megapixel.')
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if image is None or min(image.shape[:2]) < 160:
            raise HTTPException(400, 'Không đọc được ảnh hoặc ảnh quá nhỏ.')
        return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, 'Dữ liệu ảnh không hợp lệ.')
    finally:
        upload.file.close()


def get_session(token):
    purge_expired()
    with session_lock:
        state = sessions.get(token or '')
        if state is None:
            raise HTTPException(401, 'Phiên không hợp lệ hoặc đã hết hạn. Vui lòng chụp lại giấy tờ.')
        return state


@app.post('/api/verify')
@app.post('/api/document')
def document(card: UploadFile = File(...), x_session_token: str | None = Header(None)):
    # Existing /api/verify URL now performs only stages 1–3; no video endpoint.
    if not inference_lock.acquire(blocking=False):
        card.file.close()
        raise HTTPException(429, 'Hệ thống đang xử lý. Vui lòng thử lại.')
    try:
        if x_session_token:
            with session_lock:
                sessions.pop(x_session_token, None)
        purge_expired()
        with session_lock:
            if len(sessions) >= 100:
                raise HTTPException(429, 'Đã đạt giới hạn phiên. Vui lòng thử lại sau.')
        image = decode_capture(card)
        result, embedding = get_pipeline().process_document(image)
        if result['status'] != 'review':
            return result
        token = secrets.token_urlsafe(32)
        with session_lock:
            sessions[token] = dict(embedding=embedding, expires=time.monotonic()+SESSION_TTL,
                                   fields=dict(result['fields']), confirmed=False,
                                   additional_field_keys=set(result.get('additional_fields',{})))
        return dict(result, session_token=token, expires_in=SESSION_TTL, liveness_checked=False)
    except HTTPException:
        raise
    except Exception:
        # Do not expose paths, OCR text, image bytes or exception contents.
        raise HTTPException(503, 'Hệ thống tạm thời chưa xử lý được giấy tờ. Vui lòng thử lại sau; lỗi này không có nghĩa ảnh chụp của bạn không đạt.')
    finally:
        card.file.close()
        inference_lock.release()


class ConfirmedFields(BaseModel):
    model_config = ConfigDict(extra='forbid')
    full_name: str = Field(default='', max_length=150)
    id_number: str = Field(default='', max_length=40)
    dob: str = Field(default='', max_length=10)
    gender: str = Field(default='', max_length=30)
    address: str = Field(default='', max_length=500)
    additional_fields: dict[str,str] = Field(default_factory=dict,max_length=30)

    @field_validator('additional_fields')
    @classmethod
    def bounded_additional_fields(cls,value):
        if any(not key or len(key)>80 or len(text)>500 for key,text in value.items()):
            raise ValueError('Invalid additional field')
        return value


@app.post('/api/confirm')
def confirm(fields: ConfirmedFields, x_session_token: str | None = Header(None)):
    state = get_session(x_session_token)
    if state['embedding'] is None:
        raise HTTPException(409, 'Thông tin OCR vẫn xem được, nhưng chưa có chân dung để đối chiếu. Vui lòng chụp lại mặt giấy tờ có ảnh.')
    values = {key: value.strip() for key, value in fields.model_dump(exclude={'additional_fields'}).items()}
    if set(fields.additional_fields)-state.get('additional_field_keys',set()):
        raise HTTPException(422,'Chỉ được sửa các trường đã đọc từ giấy tờ trong phiên hiện tại.')
    if fields.additional_fields:
        values['additional_fields']={key:value.strip() for key,value in fields.additional_fields.items()}
    if values['dob']:
        try:
            parsed = date.fromisoformat(values['dob'])
            if parsed > date.today() or parsed.year < 1850:
                raise ValueError()
        except ValueError:
            raise HTTPException(422, 'Ngày sinh không hợp lệ.')
    with session_lock:
        if sessions.get(x_session_token) is not state:
            raise HTTPException(401, 'Phiên đã hết hạn.')
        state['fields'] = values
        state['confirmed'] = True
        state.pop('liveness', None)
    return dict(status='selfie_required', fields=values, fields_source='user_confirmed',
                fields_verified=False, liveness_checked=False, liveness_required=True)


def checked_selfie_session(token):
    state = get_session(token)
    if state['embedding'] is None:
        raise HTTPException(409, 'Chưa có chân dung giấy tờ để đối chiếu. Vui lòng chụp lại giấy tờ.')
    if not state['confirmed']:
        raise HTTPException(409, 'Vui lòng xác nhận thông tin trước khi chụp selfie.')
    return state


@app.post('/api/liveness/start')
def start_liveness(x_session_token: str | None = Header(None)):
    from .live_challenge import LiveChallenge
    state = checked_selfie_session(x_session_token)
    if not inference_lock.acquire(blocking=False):
        raise HTTPException(429, 'Hệ thống đang xử lý. Vui lòng thử lại.')
    try:
        with session_lock:
            if sessions.get(x_session_token) is not state:
                raise HTTPException(401, 'Phiên đã hết hạn.')
            if state.get('liveness_attempts',0)>=3:
                raise HTTPException(429, 'Đã thử 3 lần. Vui lòng xóa phiên và bắt đầu lại.')
            state.pop('liveness',None)
        get_observer()  # Fail before promising a working challenge if model loading fails.
        get_pad()
        challenge = LiveChallenge(time.monotonic(),Settings().match_threshold)
        with session_lock:
            if sessions.get(x_session_token) is not state or state['expires']<=time.monotonic():
                raise HTTPException(401, 'Phiên đã hết hạn.')
            state['liveness']=challenge
            state['liveness_attempts']=state.get('liveness_attempts',0)+1
        return challenge.report(time.monotonic())
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, 'Không khởi tạo được bộ kiểm tra khuôn mặt. Vui lòng thử lại sau.')
    finally:
        inference_lock.release()


@app.delete('/api/liveness')
def cancel_liveness(x_session_token: str | None = Header(None)):
    state=checked_selfie_session(x_session_token)
    with session_lock:
        state.pop('liveness',None)
    return dict(status='cancelled')


@app.post('/api/liveness/frame')
def liveness_frame(image: UploadFile = File(...), x_session_token: str | None = Header(None),
                   x_liveness_id: str | None = Header(None), x_frame_token: str | None = Header(None),
                   x_frame_sequence: int = Header(-1)):
    from .live_challenge import ChallengeRequestError
    acquired=False
    try:
        state=checked_selfie_session(x_session_token)
        if not inference_lock.acquire(blocking=False):
            raise HTTPException(429, 'Hệ thống đang xử lý. Vui lòng thử lại.')
        acquired=True
        with session_lock:
            challenge=state.get('liveness')
            if challenge is None:
                raise HTTPException(409, 'Vui lòng bắt đầu thử thách camera.')
            received=time.monotonic()
            challenge.validate(x_liveness_id,x_frame_token,x_frame_sequence,received)
        capture=decode_capture(image,live=True)
        observation=observe_live_capture(capture)
        result=challenge.update(observation,capture,received,get_pipeline().faces.extract)
        with session_lock:
            if sessions.get(x_session_token) is not state or state['expires']<=time.monotonic():
                raise HTTPException(401, 'Phiên đã hết hạn.')
            if state.get('liveness') is not challenge:
                raise HTTPException(409, 'Thử thách đã bị hủy. Vui lòng bắt đầu lại.')
        return result
    except ChallengeRequestError as error:
        raise HTTPException(409,str(error))
    except HTTPException:
        raise
    except Exception:
        # A failed inference must invalidate any partially advanced challenge.
        if 'state' in locals():
            with session_lock: state.pop('liveness',None)
        raise HTTPException(503, 'Không phân tích được khung hình camera. Vui lòng bắt đầu lại thử thách.')
    finally:
        image.file.close()
        if acquired: inference_lock.release()


@app.post('/api/selfie')
def selfie(image: UploadFile = File(...), x_session_token: str | None = Header(None)):
    try:
        state = checked_selfie_session(x_session_token)
        if not inference_lock.acquire(blocking=False):
            raise HTTPException(429, 'Hệ thống đang xử lý. Vui lòng thử lại.')
        try:
            challenge=state.get('liveness')
            if challenge is None or not challenge.proof_valid(time.monotonic()):
                raise HTTPException(409, 'Cần hoàn thành thử thách camera trước khi đối chiếu. Kết quả thử thách có hiệu lực 45 giây.')
            capture = decode_capture(image)
            observation=observe_live_capture(capture)
            pad = observation.get('pad') or {}
            if observation.get('face_count') == 1 and pad.get('decision') != 'live':
                from .live_challenge import HINTS
                reason = 'spoof_detected' if pad.get('decision')=='spoof' else 'pad_uncertain'
                challenge.fail(reason)
                return JSONResponse(dict(detail=HINTS[reason], code=reason, liveness_invalidated=True),
                                    status_code=403 if reason=='spoof_detected' else 422)
            if not observation.get('quality_ok') or not challenge.neutral(observation):
                from .live_challenge import HINTS
                problems=observation.get('problems') or []
                hint=HINTS.get(problems[0]) if problems else 'Nhìn thẳng, mở hai mắt và chụp lại ảnh chân dung.'
                return JSONResponse(dict(detail=hint,issues=[]),status_code=422)
            result = get_pipeline().match_live_selfie(capture,state['embedding'],challenge.embeddings)
            if not challenge.proof_valid(time.monotonic()):
                raise HTTPException(409, 'Thử thách camera đã hết hạn. Vui lòng thực hiện lại.')
            result.update(liveness_checked=True,liveness_passed=True,liveness=challenge.summary())
            result['liveness']['pad']['final_selfie_passed'] = True
            with session_lock:
                if (sessions.get(x_session_token) is not state or state.get('liveness') is not challenge or
                        state['expires'] <= time.monotonic()):
                    sessions.pop(x_session_token, None)
                    raise HTTPException(401, 'Phiên đã hết hạn. Vui lòng bắt đầu lại.')
                # Consume the biometric session on a completed comparison, even mismatch.
                sessions.pop(x_session_token, None)
            return dict(result, fields_source='user_confirmed', fields_verified=False)
        except StageError:
            from .feedback import issue
            return JSONResponse(dict(detail='Vui lòng điều chỉnh và chụp lại selfie.',
                                     issues=[issue('selfie_face_unavailable')]), status_code=422)
        except HTTPException:
            raise
        except Exception:
            with session_lock:
                state.pop('liveness',None)
            raise HTTPException(503, 'Không thể đối chiếu khuôn mặt. Vui lòng thử lại.')
        finally:
            inference_lock.release()
    finally:
        image.file.close()


@app.delete('/api/session')
def delete_session(x_session_token: str | None = Header(None)):
    with session_lock:
        sessions.pop(x_session_token or '', None)
    return {'status': 'deleted'}


@app.get('/api/results/{run_id}/{filename}')
def artifact(run_id: str, filename: str):
    # Never expose historical CLI artifacts/PII through the live camera API.
    raise HTTPException(404)
