"""Real-weight document regression. Reports contain keys/counts, never OCR PII.

Synthetic examples exercise text extraction; they are not real issued cards.
Optional --image/--camera-rect reads a supplied screenshot in RAM only.
"""
import argparse
import json
import time

import cv2
import numpy as np
import torch
from PIL import Image,ImageDraw,ImageFont

from ekyc.config import ROOT
from ekyc.io import read_image,write_json
from ekyc.pipeline import EKYCPipeline


def synthetic_card(title,rows):
    image=Image.new('RGB',(1200,800),'#424b52')
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((95,70,1105,725),radius=25,fill='#f1f5ef',outline='#a3c3bb',width=4)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',36)
    heading=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',42)
    draw.text((145,110),title,font=heading,fill='#164046')
    for i,row in enumerate(rows): draw.text((145,205+i*70),row,font=font,fill='#142b3f')
    draw.text((145,650),'DỮ LIỆU KIỂM THỬ TỔNG HỢP',font=font,fill='#575e63')
    return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)


def summarize(result,embedding,elapsed):
    fields={key:value for key,value in result.get('fields',{}).items() if value}
    fields.update(result.get('additional_fields',{}))
    return dict(status=result['status'],reason=result.get('reason'),
        rectification_method=result.get('rectification_method'),
        document_type=result.get('document_type',{}).get('key'),
        field_keys=list(fields),field_lengths={k:len(v) for k,v in fields.items()},
        ocr_text_rows=len(result.get('ocr_text',[])),portrait_available=embedding is not None,
        elapsed_seconds=round(elapsed,2))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image')
    parser.add_argument('--camera-rect',type=int,nargs=4,metavar=('X1','Y1','X2','Y2'))
    parser.add_argument('--output',default=str(ROOT/'outputs/document_regression.json'))
    args=parser.parse_args()
    torch.set_num_threads(4);cv2.setNumThreads(2)
    pipeline=EKYCPipeline();report={'real_weights':True,'cases':[]}
    examples=[('synthetic_student','THẺ HỌC SINH',[
        'Họ và tên: NGUYỄN VĂN AN','Mã học sinh: HS20260042','Lớp: 12A3','Niên khóa: 2024 - 2027']),
        ('synthetic_driver','GIẤY PHÉP LÁI XE',[
        'Họ và tên: TRẦN THỊ LAN','License number: A1234567','Hạng: B2','Ngày cấp: 02/03/2024','Có giá trị đến: 02/03/2034'])]
    for name,title,rows in examples:
        image=synthetic_card(title,rows);started=time.monotonic()
        result,embedding=pipeline.process_document(image)
        record=dict(case=name,**summarize(result,embedding,time.monotonic()-started))
        record['source']='synthetic text card; no real identity or portrait'
        report['cases'].append(record)
    if args.image:
        image=read_image(args.image)
        if args.camera_rect:
            x1,y1,x2,y2=args.camera_rect
            if not (0<=x1<x2<=image.shape[1] and 0<=y1<y2<=image.shape[0]): raise ValueError('Invalid screenshot camera rectangle')
            image=image[y1:y2,x1:x2].copy()
        started=time.monotonic();result,embedding=pipeline.process_document(image)
        report['cases'].append(dict(case='provided_camera_preview',source='user-provided image, processed in RAM',
                                   **summarize(result,embedding,time.monotonic()-started)))
    report['limitations']=['Synthetic cards do not establish real student/license OCR accuracy.',
        'Screenshot camera preview differs from original sensor image.',
        'Counts are not a claim that all OCR characters are correct. No OCR values/images saved.']
    write_json(args.output,report)
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__=='__main__': main()
