from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ('Clean', 'Blur', 'Cropped', 'Dark', 'Distorted')


@dataclass(frozen=True)
class Settings:
    quality_model: Path = ROOT / 'models' / 'quality_original_transfer.pth'
    models_dir: Path = ROOT / 'models'
    output_dir: Path = ROOT / 'outputs'
    clean_threshold: float = 0.60
    match_threshold: float = 0.363
    ocr_languages: tuple = ('vi',)  # Legacy CLI option; ScanOCR/VietOCR uses Vietnamese weights.
    ocr_min_confidence: float = 0.65
    max_video_seconds: float = 30.0
    min_video_seconds: float = 2.0
    sample_fps: float = 10.0

    def __post_init__(self):
        if not 0 <= self.clean_threshold <= 1:
            raise ValueError('clean_threshold must be between 0 and 1')
        if not -1 <= self.match_threshold <= 1:
            raise ValueError('match_threshold must be between -1 and 1')
