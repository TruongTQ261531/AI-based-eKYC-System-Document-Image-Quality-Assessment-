"""Export a source/model seal; deployed prediction does not need annotations."""
import json
from pathlib import Path

from research.benchmark import save,digest
from research.layout_kie_study import signature
from research.recovery_study import OUT


def main():
    lock=json.loads((OUT/'layout_kie_lock.json').read_text(encoding='utf-8'))
    if lock['signature']!=signature():raise ValueError('Offline study signature changed')
    names=['research/layout_kie.py','research/recovery_runtime.py','research/recovery_selection.py',
        'research/recovery_upstream.py','research/e2e_pipeline.py','research/partial_support.py',
        'ekyc/document_fields.py','ekyc/module2_homography.py','ekyc/io.py']
    save(OUT/'kie_deployment.json',dict(source_lock_sha256=digest(OUT/'layout_kie_lock.json'),
        study_signature=lock['signature'],model_sha256=digest(OUT/'selector_models.json'),
        deployment_approved_on_development=lock['deployment_approved_on_development'],
        code_sha256={name:digest(name) for name in names},training_annotations_required_at_inference=False,
        code_sha256_exporter=digest(__file__)))
    print('DATA_INDEPENDENT_DEPLOYMENT_SEAL_WRITTEN',flush=True)


if __name__=='__main__':main()
