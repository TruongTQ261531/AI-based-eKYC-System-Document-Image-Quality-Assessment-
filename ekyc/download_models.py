"""Explicit model setup. Runtime inference never downloads assets implicitly."""
import argparse
import hashlib
import urllib.request
from .config import ROOT
from .io import write_json

ASSETS = {
    'face_detection_yunet_2023mar.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
    'face_recognition_sface_2021dec.onnx': 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx',
    'face_landmarker.task': 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--languages', nargs='+', default=['en'])
    args = parser.parse_args()
    directory = ROOT/'models'
    directory.mkdir(exist_ok=True)
    records = []
    for filename, url in ASSETS.items():
        destination = directory/filename
        if not destination.exists():
            print(f'Downloading {filename}', flush=True)
            temporary = destination.with_suffix('.download')
            urllib.request.urlretrieve(url, temporary)
            if temporary.stat().st_size < 100000:
                raise ValueError(f'Invalid model download: {filename}')
            temporary.replace(destination)
        records.append(dict(file=filename, url=url, sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    import easyocr
    easyocr.Reader(args.languages, gpu=False, model_storage_directory=str(directory/'easyocr'), verbose=False)
    write_json(directory/'model_sources.json', records)
    print('Models ready')


if __name__ == '__main__':
    main()
