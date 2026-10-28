"""Real weights smoke, using synthetic Vietnamese lines and public PAD examples.

No user's card/face is uploaded, saved, or read. Public demo images are NOT a
representative PAD benchmark. Synthetic OCR lines are NOT real CCCD evaluation.
"""
import json
import time
import unicodedata
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

from ekyc.config import ROOT
from ekyc.faces import FaceEngine
from ekyc.scanocr import ScanOCRReader, letterbox, decode_regions
from ekyc.presentation_attack import PresentationAttackDetection
from ekyc.io import read_image, write_json


def api_pad_smoke(faces):
    """Isolated PAD API test: seed a synthetic confirmed session, no ID/OCR claim."""
    from fastapi.testclient import TestClient
    import ekyc.api as api
    results=[]
    with TestClient(api.app,base_url='http://localhost') as client:
        api.get_pipeline()._faces=faces
        token='public-fixture-smoke-only'
        api.sessions[token]=dict(embedding=np.ones((1,128),np.float32),fields={},confirmed=True,
                                 expires=time.monotonic()+600)
        headers={'X-Session-Token':token}
        for name,expected in [('image_T1.jpg','running'),('image_F1.jpg','failed'),('image_F2.jpg','failed')]:
            started=client.post('/api/liveness/start',headers=headers)
            assert started.status_code==200,started.status_code
            packet=started.json()
            raw=(ROOT/'outputs/pad_samples'/name).read_bytes()
            response=client.post('/api/liveness/frame',headers=dict(headers,**{
                'X-Liveness-Id':packet['challenge_id'],'X-Frame-Token':packet['frame_token'],
                'X-Frame-Sequence':'0'}),files={'image':('frame.jpg',raw,'image/jpeg')})
            assert response.status_code==200,response.status_code
            result=response.json()
            assert result['status']==expected,result.get('reason')
            if expected=='failed': assert result['reason']=='spoof_detected',result.get('reason')
            denied=client.post('/api/selfie',headers=headers,files={'image':('selfie.jpg',raw,'image/jpeg')})
            assert denied.status_code==409
            results.append(dict(file=name,status=result['status'],reason=result.get('reason'),
                                completed_actions=result['completed'],final_selfie_http_status=denied.status_code))
        client.delete('/api/session',headers=headers)
        assert not api.sessions
    return results


def synthetic_line(text):
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 38)
    bounds = font.getbbox(text)
    image = Image.new('RGB',(bounds[2]-bounds[0]+12,bounds[3]-bounds[1]+12),'white')
    ImageDraw.Draw(image).text((6-bounds[0],6-bounds[1]),text,font=font,fill='black')
    return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)


def main():
    torch.set_num_threads(4); cv2.setNumThreads(2)
    start=time.monotonic()
    reader=ScanOCRReader(ROOT/'models')
    ocr=[]
    for expected in ['NGUYỄN THỊ ÁNH','001234567890','03/02/1999','Nữ',
                     'Phường Bến Nghé, Thành phố Hồ Chí Minh']:
        predicted,confidence=reader.recognizer.predict(synthetic_line(expected))
        ocr.append(dict(expected=expected,predicted=predicted,confidence=confidence,
                        exact_match=unicodedata.normalize('NFC',predicted)==expected))
    tensor,ratio,left,top=letterbox(np.full((800,1200,3),255,np.uint8))
    output=reader.session.run(None,{reader.input_name:tensor})[0]
    blank_regions=decode_regions(output,(800,1200,3),ratio,left,top)
    faces=FaceEngine(ROOT/'models')
    pad=PresentationAttackDetection(ROOT/'models')
    pad_results=[]
    for name,expected in [('image_T1.jpg','live'),('image_F1.jpg','spoof'),('image_F2.jpg','spoof')]:
        image=read_image(ROOT/'outputs/pad_samples'/name)
        result=pad.check(image,faces)
        pad_results.append(dict(file=name,expected=expected,**result))
        assert result['decision']==expected
    api_results=api_pad_smoke(faces)
    report=dict(real_weights=True,ocr_synthetic_lines=ocr,scanocr_output_shape=list(output.shape),
                blank_card_detected_regions=len(blank_regions),pad_public_examples=pad_results,
                pad_api_public_examples=api_results,api_session_fixture='synthetic confirmed session; OCR/ID stages not exercised',
                elapsed_seconds=round(time.monotonic()-start,2),
                sample_source='https://github.com/yakhyo/face-anti-spoofing/tree/01a38903f4f2680bb59d32a994a6c7b5ae56f49b/assets',
                limitations=['No real Vietnamese CCCD tested.', 'No physical camera or Zalo/Messenger video-call replay tested.',
                             'Three author demo images only; not APCER/BPCER or certification evidence.'])
    write_json(ROOT/'outputs/identity_models_smoke.json',report)
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__=='__main__': main()
