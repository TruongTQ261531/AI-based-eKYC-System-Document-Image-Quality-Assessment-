"""Real-model API smoke test; uses a dataset portrait, NOT a real live selfie."""
import argparse
import os
import sys
from pathlib import Path
import cv2
import torch
from fastapi.testclient import TestClient
from ekyc.api import app, get_pipeline, sessions
from ekyc.config import ROOT
from ekyc.io import read_image, write_json
from ekyc.module2_homography import Homography


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--card', type=Path, default=ROOT/'full_dataset_original/midv500_dataset/04_aut_id/images/TS/TS04_20.tif')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/camera_workflow_smoke.json')
    args = parser.parse_args()
    torch.set_num_threads(4)
    cv2.setNumThreads(2)
    path=args.card
    image=read_image(path)
    payload=cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,95])[1].tobytes()
    forbidden = [os.path.normcase(str(ROOT/folder)) + os.sep for folder in ('data', 'full_dataset_original')]
    def guard(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            opened = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
            if any(opened.startswith(folder) for folder in forbidden):
                raise AssertionError('Inference attempted to read a dataset/manifest file')
    # The fixture is already in memory. Monitor Python file I/O for the real API run.
    sys.addaudithook(guard)
    before=set((ROOT/'outputs').iterdir())
    with TestClient(app,base_url='http://localhost') as client:
        result=client.post('/api/document',files={'card':('camera.jpg',payload,'image/jpeg')})
        assert result.status_code==200, result.status_code
        data=result.json()
        if data['status']!='review':
            write_json(args.output, dict(document_status=data['status'],reason=data.get('reason'),
                                         completed=False,fixture=path.name))
        assert data['status']=='review', data.get('reason')
        headers={'X-Session-Token':data['session_token']}
        confirmed=client.post('/api/confirm',headers=headers,json=data['fields'])
        assert confirmed.status_code==200
        rectified,_=Homography().run(image)
        _,crop,_,_=get_pipeline().faces.extract_document(rectified)
        # An enlarged ID crop exercises matching transport only, never liveness.
        selfie=cv2.imencode('.jpg',cv2.resize(crop,(336,336)))[1].tobytes()
        match=client.post('/api/selfie',headers=headers,files={'image':('selfie.jpg',selfie,'image/jpeg')})
        # Since API v3 a single ID crop cannot bypass the active camera challenge.
        assert match.status_code==409, match.status_code
        client.delete('/api/session',headers=headers)
        assert not sessions
        assert set((ROOT/'outputs').iterdir())==before, 'API wrote persistent artifacts'
        report=dict(document_status=data['status'],source_resolution=[image.shape[1],image.shape[0]],
            completed=False,transport_checks_passed=True,fixture=path.name,
            quality_checkpoint=get_pipeline().settings.quality_model.name,
            dataset_file_io_guard='passed_python_open_audit',
            form_status=confirmed.json()['status'],selfie_status='blocked_pending_liveness',
            liveness_checked=False,identity_verified=False,
            session_deleted=True,new_pii_files=0,
            limitation='API v3 correctly blocks photo-only comparison; no genuine live camera sequence tested.')
    write_json(args.output,report)
    print(report)


if __name__=='__main__': main()
