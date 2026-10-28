"""Pinned ScanOCR field detector + local VietOCR Vietnamese text recognition.

No Ultralytics runtime, network calls or images written to disk. The ONNX
contract is YOLO11 raw xywh + 11 class probabilities (not end-to-end NMS).
"""
import ast

import cv2
import numpy as np
from PIL import Image

from .io import StageError

FIELD_LABELS = {'ID_Number': 'id_number', 'Full_Name': 'full_name', 'DOB': 'dob',
                'Gender': 'gender', 'Address': 'address', 'Nationality':'nationality', 'Hometown':'hometown'}
EXPECTED_LABELS = ['ID_Number', 'Full_Name', 'DOB', 'Gender', 'Nationality', 'Hometown',
                   'Address', 'CCCD_Chip', 'CCCD_NoChip', 'GPLX', 'Passport']


def cpu_session(path):
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    return ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])


def letterbox(image, size=640):
    h, w = image.shape[:2]
    ratio = min(size/w, size/h)
    nw, nh = round(w*ratio), round(h*ratio)
    left, top = (size-nw)//2, (size-nh)//2
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[top:top+nh, left:left+nw] = cv2.resize(image, (nw, nh))
    tensor = np.ascontiguousarray(canvas[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32)/255.
    return tensor, ratio, left, top


def decode_regions(output, shape, ratio, left, top, threshold=.35):
    raw = np.asarray(output)
    if raw.ndim != 3 or raw.shape[0:2] != (1, 15) or not np.isfinite(raw).all():
        raise StageError('Invalid ScanOCR output contract')
    rows = raw[0].T
    labels = rows[:, 4:].argmax(axis=1)
    scores = rows[np.arange(len(rows)), labels+4]
    regions = []
    h, w = shape[:2]
    for cls, label in enumerate(EXPECTED_LABELS):
        if label not in FIELD_LABELS:
            continue  # Never send whole-card/type boxes to a line recognizer.
        indices = np.where((labels == cls) & (scores >= threshold))[0]
        indices = indices[np.argsort(scores[indices])[::-1]][:100]
        boxes = [[float(rows[i, 0]-rows[i, 2]/2), float(rows[i, 1]-rows[i, 3]/2),
                  float(rows[i, 2]), float(rows[i, 3])] for i in indices]
        if not boxes:
            continue
        keep = cv2.dnn.NMSBoxes(boxes, scores[indices].tolist(), threshold, .45)
        for j in np.asarray(keep).reshape(-1):
            x, y, bw, bh = boxes[j]
            x1, y1 = max(0, (x-left)/ratio), max(0, (y-top)/ratio)
            x2, y2 = min(w, (x+bw-left)/ratio), min(h, (y+bh-top)/ratio)
            if x2-x1 < 4 or y2-y1 < 4:
                continue
            regions.append(dict(label=label, field=FIELD_LABELS[label],
                                xyxy=[x1, y1, x2, y2], detection_confidence=float(scores[indices[j]])))
    return sorted(regions, key=lambda r: (r['xyxy'][1], r['xyxy'][0]))[:30]


class VietnameseRecognizer:
    def __init__(self, directory):
        import torch
        import yaml
        from vietocr.tool.translate import build_model
        with (directory/'base.yml').open(encoding='utf-8') as source:
            config = yaml.safe_load(source)
        with (directory/'vgg-transformer.yml').open(encoding='utf-8') as source:
            config.update(yaml.safe_load(source))
        config['device'] = 'cpu'
        config['cnn']['pretrained'] = False  # Complete checkpoint; never download a backbone.
        self.model, self.vocab = build_model(config)
        self.model.load_state_dict(torch.load(directory/'vgg_transformer.pth', map_location='cpu', weights_only=True))
        self.model.eval()
        self.config = config

    def predict(self, crop):
        import torch
        from vietocr.tool.translate import process_input, translate
        data = self.config['dataset']
        tensor = process_input(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)),
                               data['image_height'], data['image_min_width'], data['image_max_width'])
        with torch.inference_mode():
            tokens, probabilities = translate(tensor, self.model, max_seq_length=128)
        text = self.vocab.decode(tokens[0].tolist()).strip()
        confidence = float(probabilities[0])
        return text, confidence if np.isfinite(confidence) else 0.


class ScanOCRReader:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        directory = models_dir/'scanocr'
        self.session = cpu_session(directory/'yolo_v11_best.onnx')
        names = ast.literal_eval(self.session.get_modelmeta().custom_metadata_map['names'])
        if names != dict(enumerate(EXPECTED_LABELS)) or self.session.get_inputs()[0].shape != [1, 3, 640, 640]:
            raise StageError('Unsupported ScanOCR model contract')
        self.input_name = self.session.get_inputs()[0].name
        self.recognizer = VietnameseRecognizer(directory)
        self._text_detector = None

    def locate_documents(self, image):
        """Card classes are localization hints, never fields or identity evidence."""
        tensor, ratio, left, top = letterbox(image)
        rows = self.session.run(None, {self.input_name:tensor})[0][0].T
        cls = rows[:,4:].argmax(axis=1)
        scores = rows[np.arange(len(rows)),cls+4]
        indices = np.where((cls>=7)&(scores>=.65))[0]
        boxes=[]; found=[]
        h,w=image.shape[:2]
        for i in indices[np.argsort(scores[indices])[::-1]][:100]:
            cx,cy,bw,bh=rows[i,:4]
            x1,y1=max(0.,float((cx-bw/2-left)/ratio)),max(0.,float((cy-bh/2-top)/ratio))
            x2,y2=min(float(w-1),float((cx+bw/2-left)/ratio)),min(float(h-1),float((cy+bh/2-top)/ratio))
            if min(x2-x1,y2-y1)<80 or (x2-x1)*(y2-y1)<h*w*.025: continue
            boxes.append([x1,y1,x2-x1,y2-y1])
            found.append(dict(box=[x1,y1,x2,y2],confidence=float(scores[i]),label=EXPECTED_LABELS[cls[i]]))
        if not found: return []
        keep=cv2.dnn.NMSBoxes(boxes,[r['confidence'] for r in found],.65,.45)
        return [found[int(i)] for i in np.asarray(keep).reshape(-1)][:3]

    def generic_regions(self, card):
        """CRAFT detects arbitrary text; VietOCR, rather than English OCR, reads it."""
        if self._text_detector is None:
            import easyocr
            self._text_detector=easyocr.Reader(['en'],gpu=False,recognizer=False,
                model_storage_directory=str(self.models_dir/'easyocr'),download_enabled=False,verbose=False)
        horizontal,free=self._text_detector.detect(card,canvas_size=1600,mag_ratio=1.5,
            text_threshold=.55,low_text=.3,link_threshold=.3,min_size=6,
            width_ths=.35,add_margin=.06)
        boxes=[]
        for x1,x2,y1,y2 in horizontal[0]:
            if x2>x1 and y2>y1:
                boxes.append(np.float32([[x1,y1],[x2,y1],[x2,y2],[x1,y2]]))
        boxes.extend(np.asarray(box,np.float32) for box in free[0])
        return sorted(boxes,key=lambda box:(float(box[:,1].min()),float(box[:,0].min())))[:60]

    def read(self, card):
        tensor, ratio, left, top = letterbox(card)
        output = self.session.run(None, {self.input_name: tensor})[0]
        regions = decode_regions(output, card.shape, ratio, left, top)
        lines = []
        h, w = card.shape[:2]
        for region in regions:
            x1, y1, x2, y2 = region.pop('xyxy')
            # Small crop margin retains accents at the top and bottom of text.
            px, py = max(2, (x2-x1)*.015), max(2, (y2-y1)*.10)
            crop = card[max(0,int(y1-py)):min(h,int(np.ceil(y2+py))),
                        max(0,int(x1-px)):min(w,int(np.ceil(x2+px)))]
            text, confidence = self.recognizer.predict(crop)
            lines.append(dict(region, text=text, confidence=confidence,
                              source='scanocr_field',box=[[x1,y1],[x2,y1],[x2,y2],[x1,y2]]))
        for box in self.generic_regions(card):
            x1,y1=np.maximum(0,np.floor(box.min(axis=0))).astype(int)
            x2,y2=np.minimum([w,h],np.ceil(box.max(axis=0))).astype(int)
            if x2-x1<4 or y2-y1<4: continue
            text,confidence=self.recognizer.predict(card[y1:y2,x1:x2])
            if text:
                lines.append(dict(text=text,confidence=confidence,source='generic_text',
                                  box=[[float(x),float(y)] for x,y in box]))
        return lines
