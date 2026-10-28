import time
import uuid
from .config import Settings
from .io import StageError, read_image, write_image, write_json


class EKYCPipeline:
    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self._quality = self._faces = self._ocr = None

    @property
    def quality(self):
        if self._quality is None:
            from .module1_quality import QualityAssessment
            self._quality = QualityAssessment(self.settings.quality_model, self.settings.clean_threshold)
        return self._quality

    @property
    def faces(self):
        if self._faces is None:
            from .faces import FaceEngine
            self._faces = FaceEngine(self.settings.models_dir)
        return self._faces

    @property
    def ocr(self):
        if self._ocr is None:
            from .module3_ocr import OCRExtraction
            self._ocr = OCRExtraction(self.settings.models_dir, self.settings.ocr_min_confidence)
        return self._ocr

    def process_document(self, image):
        """Camera workflow: process in memory; no files or biometric logs."""
        from .module2_homography import Homography
        from .feedback import retake, issue
        quality = self.quality.run(image)
        if not quality['passed']:
            from .module1_quality import image_metrics
            metrics=quality.get('metrics') or image_metrics(image)
            # A camera background must not veto a recoverable card. Only an
            # effectively empty/black/tiny frame stops before localization.
            if metrics['min_side']<160 or metrics['contrast']<3 or metrics['p90']<10:
                return retake('quality_rejected', quality), None
        reader=getattr(self.ocr,'reader',None)
        hints=reader.locate_documents(image) if hasattr(reader,'locate_documents') else []
        localized=True
        try:
            card, geometry = Homography().run(image,region_hints=hints) if hints else Homography().run(image)
        except StageError:
            if not hasattr(self.ocr,'run_unlocalized'):
                return retake('document_corners_not_found', quality), None
            # Text can still be reviewed; never take the user's face outside an
            # unlocalized card as its printed document portrait.
            localized=False; card=image
            geometry=dict(method='unlocalized_text_only',requires_review=True,
                          warnings=['document_boundary_unverified'])
        document_quality=self.quality.run(card) if localized and card is not image else quality
        ocr, _, embedding = self.ocr.run(card, self.faces) if localized else self.ocr.run_unlocalized(card)
        if ocr.get('accepted_line_count') == 0:
            if not localized:
                return retake('document_corners_not_found',quality),None
            if not document_quality.get('passed',True):
                return retake('quality_rejected',document_quality),None
            return retake('ocr_unreadable', quality), None
        from .module3_ocr import form_fields
        from .document_fields import CORE_KEYS,text_rows
        if not quality['passed']:
            quality=dict(quality,passed=True,frame_assessment_passed=False,
                         frame_issues=quality.get('issues',[]),issues=[],
                         reason='document_text_recovered',policy='document_readability_recovery_v3')
        text_lines=[line for line in ocr.get('raw_lines',[]) if not line.get('field')]
        if not text_lines: text_lines=ocr.get('raw_lines',[])
        portrait_issue = ocr.get('face_error') or 'id_face_unavailable'
        return dict(status='review', fields=form_fields(ocr['fields']), ocr_engine=ocr.get('engine'),
                    additional_fields={k:v for k,v in ocr['fields'].items() if k not in CORE_KEYS and v},
                    document_fields=ocr.get('document_fields'),document_type=ocr.get('document_type'),
                    ocr_text=text_rows(text_lines),rectification_method=geometry['method'] if 'method' in geometry else 'contour_detection',
                    fields_source='ocr', fields_verified=False, quality=quality,document_quality=document_quality,
                    warnings=quality.get('warnings', []),processing_warnings=geometry.get('warnings',[]),
                    portrait_status='available' if embedding is not None else 'unavailable',
                    can_match_selfie=embedding is not None,
                    issues=[] if embedding is not None else [issue(portrait_issue)],
                    rectification_requires_review=geometry['requires_review']), embedding

    def match_selfie(self, image, id_embedding):
        """Single live-camera capture comparison; no claim of liveness."""
        from .module5_matching import FaceMatching
        _, embedding, _ = self.faces.extract(image)
        matching = FaceMatching(self.settings.match_threshold).run(id_embedding, [embedding], min_samples=1)
        from .feedback import issue
        return dict(status='matched' if matching['passed'] else 'not_matched', matching=matching,
                    issues=[] if matching['passed'] else [issue('face_mismatch')],
                    liveness_checked=False, identity_verified=False)

    def match_live_selfie(self, image, id_embedding, live_embeddings):
        """Bind the final high-resolution selfie to the challenge's face samples."""
        import numpy as np
        from .module5_matching import FaceMatching
        from .feedback import issue
        _, embedding, _ = self.faces.extract(image)
        samples = list(live_embeddings) + [embedding]
        matching = FaceMatching(self.settings.match_threshold).run(id_embedding, samples, min_samples=4)
        vectors = np.asarray(samples).reshape(len(samples), -1)
        vectors = vectors / np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-8)
        consistency = float((vectors @ vectors.T).min())
        consistent = consistency >= self.settings.match_threshold
        passed = matching['passed'] and consistent
        return dict(status='matched' if passed else 'not_matched', matching=matching,
                    identity_consistent=bool(consistent), minimum_selfie_consistency=consistency,
                    issues=[] if passed else [issue('face_mismatch' if consistent else 'selfie_identity_changed')], identity_verified=False)

    def run(self, card_path, selfie_path=None, corners=None):
        from .module2_homography import Homography
        from .module4_liveness import LivenessDetection
        from .module5_matching import FaceMatching
        started = time.monotonic()
        run_id = uuid.uuid4().hex
        output = self.settings.output_dir/run_id
        output.mkdir(parents=True)
        result = dict(run_id=run_id, decision='error', stages={}, artifacts={},
            limitations=['Research implementation; MediaPipe motion is not certified presentation attack detection.',
                         'Existing quality checkpoint has unknown cross-dataset training provenance.'])
        stage = 'module1_quality'
        try:
            image = read_image(card_path)
            quality = self.quality.run(image)
            result['stages'][stage] = quality
            if not quality['passed']:
                result.update(decision='rejected', reason='quality_rejected')
                return result
            stage = 'module2_homography'
            card, homography = Homography().run(image, corners)
            result['stages'][stage] = homography
            write_image(output/'rectified_card.jpg', card)
            result['artifacts']['rectified_card'] = 'rectified_card.jpg'
            stage = 'module3_ocr'
            ocr, crop, embedding = self.ocr.run(card, self.faces)
            result['stages'][stage] = ocr
            write_json(output/'id_raw.json', ocr)
            result['artifacts']['id_raw'] = 'id_raw.json'
            if crop is not None:
                write_image(output/'id_face.jpg', crop)
                result['artifacts']['id_face'] = 'id_face.jpg'
            if selfie_path is None:
                result.update(decision='incomplete', reason='selfie_required')
                return result
            if embedding is None:
                result.update(decision='review_required', reason='id_face_unavailable')
                return result
            stage = 'module4_liveness'
            liveness, embeddings, crops = LivenessDetection(self.settings).run(selfie_path, self.faces)
            result['stages'][stage] = liveness
            if not liveness['passed']:
                result.update(decision='rejected', reason='liveness_failed')
                return result
            write_image(output/'selfie_face.jpg', crops[len(crops)//2])
            result['artifacts']['selfie_face'] = 'selfie_face.jpg'
            stage = 'module5_matching'
            matching = FaceMatching(self.settings.match_threshold).run(embedding, embeddings)
            result['stages'][stage] = matching
            if not matching['passed']:
                result.update(decision='rejected', reason='face_mismatch')
            else:
                result.update(decision='review_required', reason='automated_checks_passed_requires_PAD_validation',
                              automated_checks_passed=True)
        except (StageError, FileNotFoundError, ImportError) as error:
            result.update(decision='error', failed_stage=stage, reason=str(error))
        except Exception as error:
            # Persist a failed result rather than leaving an apparently successful partial run.
            result.update(decision='error', failed_stage=stage, reason=f'{type(error).__name__}: {error}')
        finally:
            result['elapsed_seconds'] = round(time.monotonic()-started, 3)
            write_json(output/'result.json', result)
        return result
