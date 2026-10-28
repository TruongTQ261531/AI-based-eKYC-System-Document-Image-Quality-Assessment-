"""Module 1: MobileNetV3 quality gate using the supplied five-class checkpoint."""
from .config import LABELS
from .io import StageError
from .feedback import issue


def image_metrics(image):
    import cv2
    import numpy as np
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scale = min(1.0, 960 / max(gray.shape))
    resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return dict(min_side=min(gray.shape), brightness=float(resized.mean()),
                p90=float(np.percentile(resized, 90)), contrast=float(resized.std()),
                sharpness=float(cv2.Laplacian(resized, cv2.CV_64F).var()))


def assess_scores(scores, metrics, threshold=.60):
    """Only corroborated severe defects stop the pipeline before localization.

    Softmax is not calibrated for live-camera backgrounds. Cropped/Distorted
    predictions require Module 2 evidence rather than an argmax veto.
    Numeric heuristics are conservative defaults, not universal quality standards.
    """
    label = LABELS[max(range(len(scores)), key=scores.__getitem__)]
    blocking = []
    if metrics['min_side'] < 160:
        blocking.append(issue('low_resolution'))
    if metrics['brightness'] < 25 and metrics['p90'] < 60:
        blocking.append(issue('too_dark'))
    elif label == 'Dark' and scores[3] >= .80 and metrics['brightness'] < 55 and metrics['p90'] < 110:
        blocking.append(issue('too_dark'))
    if metrics['contrast'] < 3 and not blocking:
        blocking.append(issue('no_detail'))
    if label == 'Blur' and scores[1] >= .80 and metrics['sharpness'] < 75 and not blocking:
        blocking.append(issue('blur'))
    warnings = []
    if not blocking and (label != 'Clean' or scores[0] < threshold):
        code = {'Blur':'suspected_blur','Dark':'suspected_dark','Cropped':'suspected_cropped',
                'Distorted':'suspected_distorted'}.get(label, 'quality_uncertain')
        warnings.append(issue(code, suspected=True))
    passed = not blocking
    return dict(passed=passed, label=label, clean_confidence=scores[0], threshold=threshold,
        probabilities=dict(zip(LABELS, scores)), metrics=metrics, issues=blocking, warnings=warnings,
        needs_document_checks=bool(warnings), policy='corroborated_defects_v2',
        reason='quality_rejected' if blocking else ('quality_needs_document_checks' if warnings else 'quality_pass'))


class QualityAssessment:
    def __init__(self, checkpoint, threshold=0.60, device='cpu'):
        import torch
        from torch import nn
        from torchvision import models, transforms
        self.torch, self.device, self.threshold = torch, device, threshold
        if not checkpoint.is_file():
            raise StageError(f'Missing quality checkpoint: {checkpoint}')
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        if 'labels' in state and tuple(state['labels']) != LABELS:
            raise StageError('Checkpoint class order differs from LABELS')
        state = state.get('state_dict', state.get('model_state_dict', state))
        state = {key.removeprefix('module.'): value for key, value in state.items()}
        self.model = models.mobilenet_v3_small(weights=None)
        width = self.model.classifier[3].in_features
        if 'classifier.3.1.weight' in state:
            self.model.classifier[3] = nn.Sequential(nn.Dropout(0.3), nn.Linear(width, len(LABELS)))
        else:
            self.model.classifier[3] = nn.Linear(width, len(LABELS))
        self.model.load_state_dict(state, strict=True)
        self.model.to(device).eval()
        self.transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

    def run(self, image):
        from PIL import Image
        tensor = self.transform(Image.fromarray(image[:, :, ::-1])).unsqueeze(0).to(self.device)
        with self.torch.inference_mode():
            scores = self.model(tensor).softmax(dim=1)[0].cpu().tolist()
        return assess_scores(scores, image_metrics(image), self.threshold)
