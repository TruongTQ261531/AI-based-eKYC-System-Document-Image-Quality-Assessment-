"""Real-model negative smoke: a printed/static portrait must not pass liveness.

No genuine person/camera sequence is available to this test. It must never report
a successful live-person verification. All camera API data remains in RAM.
"""
import time

import cv2
import numpy as np
import torch
from fastapi.testclient import TestClient

from ekyc.api import app,get_pipeline,sessions
from ekyc.config import ROOT
from ekyc.io import read_image,write_json
from ekyc.module2_homography import Homography


def payload(image):
    return cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,95])[1].tobytes()


def main():
    cv2.setNumThreads(2); torch.set_num_threads(4)
    source=read_image(ROOT/'full_dataset_original/midv500_dataset/27_hrv_passport/images/KS/KS27_30.tif')
    before=set((ROOT/'outputs').iterdir())
    with TestClient(app,base_url='http://localhost') as client:
        doc=client.post('/api/document',files={'card':('card.jpg',payload(source))})
        assert doc.status_code==200 and doc.json()['status']=='review'
        data=doc.json(); headers={'X-Session-Token':data['session_token']}
        assert client.post('/api/confirm',headers=headers,json=data['fields']).json()['liveness_required']
        rectified,_=Homography().run(source)
        _,crop,_,_=get_pipeline().faces.extract_document(rectified)
        view=cv2.copyMakeBorder(cv2.resize(crop,(240,240)),100,100,160,160,
                               cv2.BORDER_CONSTANT,value=(120,120,120))
        assert client.post('/api/selfie',headers=headers,files={'image':('s.jpg',payload(view))}).status_code==409
        packet=client.post('/api/liveness/start',headers=headers).json()
        assert packet['status']=='running'
        def send(image):
            nonlocal packet
            response=client.post('/api/liveness/frame',headers=dict(headers,**{
                'X-Liveness-Id':packet['challenge_id'],'X-Frame-Token':packet['frame_token'],
                'X-Frame-Sequence':str(packet['next_sequence'])}),files={'image':('f.jpg',payload(image))})
            assert response.status_code==200,response.status_code
            packet=response.json()
            time.sleep(.15)
            return packet
        for _ in range(4): send(view)
        assert packet['status']=='failed' and packet['reason']=='repeated_frame'
        repeat_result=packet['reason']
        packet=client.post('/api/liveness/start',headers=headers).json()
        observations=[]
        for i in range(20):
            varied=view.copy()
            # Change background pixels while retaining exactly the same printed face.
            varied[:8,:8]=i*10
            packet=send(varied)
            observations.append(packet.get('observation') or {})
            assert packet['status']!='passed'
            if packet['status']=='failed': break
        denied=client.post('/api/selfie',headers=headers,files={'image':('s.jpg',payload(view))})
        assert denied.status_code==409
        assert client.delete('/api/session',headers=headers).status_code==200 and not sessions
        assert set((ROOT/'outputs').iterdir())==before
        report=dict(real_models=True,api_version=app.version,printed_portrait='never_passed',
            repeated_frame_rejected=repeat_result,changed_background_frames=len(observations),
            observed_face_frames=sum(o.get('face_count')==1 for o in observations),
            completed_actions=packet['completed'],final_selfie_http_status=denied.status_code,
            session_deleted=True,new_pii_files=0,
            limitation='Static dataset ID portrait only. No physical camera or genuine blink/head/gaze sequence tested; no PAD accuracy claim.')
    write_json(ROOT/'outputs/active_liveness_smoke.json',report)
    print(report)


if __name__=='__main__': main()
