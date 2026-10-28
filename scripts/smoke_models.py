"""Exercise real models on local references and a static-photo replay negative control."""
import json
from pathlib import Path
import cv2
import torch
from ekyc.config import ROOT, Settings
from ekyc.faces import FaceEngine
from ekyc.io import read_image, write_json
from ekyc.module1_quality import QualityAssessment
from ekyc.module3_ocr import OCRExtraction
from ekyc.module4_liveness import LivenessDetection
from ekyc.module5_matching import FaceMatching
from ekyc.pipeline import EKYCPipeline


def main():
    torch.set_num_threads(4)
    settings = Settings()
    output = ROOT/'outputs/smoke'
    output.mkdir(parents=True, exist_ok=True)
    faces = FaceEngine(settings.models_dir)
    quality = QualityAssessment(settings.quality_model)
    ocr = OCRExtraction(settings.models_dir)
    reference = ROOT/'full_dataset_original/midv2019_dataset/04_aut_id.tif'
    image = read_image(reference)
    print('Quality', flush=True)
    q = quality.run(image)
    print(q, flush=True)
    print('OCR + face', flush=True)
    raw, crop, feature = ocr.run(image, faces)
    if feature is None:
        raise RuntimeError('Reference portrait not detected')
    same = FaceMatching().run(feature,[feature]*3)
    video = output/'static_photo.avi'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 10, (512,512))
    if not writer.isOpened():
        raise RuntimeError('Video writer unavailable')
    for _ in range(30):
        writer.write(cv2.resize(crop,(512,512)))
    writer.release()
    print('Liveness static replay negative control', flush=True)
    live, _, _ = LivenessDetection(settings).run(video, faces)
    assert not live['passed'], 'Static photo must never pass liveness'
    height,width=image.shape[:2]
    pipeline=EKYCPipeline(settings)
    pipeline._quality, pipeline._faces, pipeline._ocr=quality,faces,ocr
    pipeline_result=pipeline.run(reference,video,[[0,0],[width-1,0],[width-1,height-1],[0,height-1]])
    report=dict(quality=q,ocr=raw,same_face=same,static_replay=live,pipeline=pipeline_result)
    write_json(output/'model_smoke_report.json',report)
    print(json.dumps(report,indent=2,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
