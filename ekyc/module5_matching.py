"""Module 5: SFace embedding comparison across selfie samples."""
import numpy as np
from .io import StageError


class FaceMatching:
    def __init__(self, threshold=0.363):
        self.threshold = threshold

    def run(self, id_embedding, selfie_embeddings, min_samples=3):
        if id_embedding is None or len(selfie_embeddings) < min_samples:
            raise StageError(f'ID portrait and at least {min_samples} selfie embeddings required')
        reference = np.asarray(id_embedding).reshape(-1)
        vectors = np.asarray(selfie_embeddings).reshape(len(selfie_embeddings), -1)
        if not np.isfinite(reference).all() or not np.isfinite(vectors).all():
            raise StageError('Non-finite face embeddings')
        norm = np.linalg.norm(reference)
        norms = np.linalg.norm(vectors, axis=1)
        if norm < 1e-8 or (norms < 1e-8).any():
            raise StageError('Zero face embedding')
        scores = np.clip((vectors/norms[:,None])@(reference/norm), -1, 1)
        # All sampled identities must agree, not just the best matching frame.
        return dict(passed=bool(np.min(scores) >= self.threshold), cosine_similarity=float(np.median(scores)),
            minimum_similarity=float(np.min(scores)), threshold=self.threshold, sample_scores=scores.tolist(),
            model='SFace', threshold_note='LFW reference threshold; requires calibration for ID/selfie domain.')
