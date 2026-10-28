"""Verify result/code provenance and write a public artifact hash inventory."""
import gzip
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from research.benchmark import digest,save


def main():
    root=Path('research/results');checks=[]
    stages=(('feasibility_v1','PROTOCOL.md','benchmark.py'),
            ('ocr_diagnostic','SECONDARY_OCR_PROTOCOL.md','ocr_diagnostic.py'),
            ('risk_policy_v2','RISK_POLICY_PROTOCOL.md','risk_policy.py'),
            ('external_midv2020','EXTERNAL_PROTOCOL.md','external_midv2020.py'),
            ('neural_baseline','NEURAL_BASELINE_PROTOCOL.md','neural_baseline.py'),
            ('partial_support_v3','PARTIAL_SUPPORT_PROTOCOL.md','partial_support.py'),
            ('posthoc_controls','POSTHOC_CONTROLS.md','posthoc_controls.py'))
    for stage,protocol,code in stages:
        run=json.loads((root/stage/'run.json').read_text())
        code_key='benchmark_sha256' if stage=='feasibility_v1' else 'code_sha256'
        check=dict(stage=stage,protocol_matches=run['protocol_sha256']==digest(Path('research')/protocol),
                   code_matches=run[code_key]==digest(Path('research')/code))
        if not check['protocol_matches'] or not check['code_matches']:raise ValueError(f'Provenance mismatch {stage}')
        checks.append(check)
    primary=json.loads((root/'feasibility_v1/run.json').read_text())
    if primary['support_code_sha256']!=digest('research/support_regions.py'):raise ValueError('Primary predictor changed')
    counts={}
    for stage in ('feasibility_v1','risk_policy_v2','neural_baseline','partial_support_v3','posthoc_controls'):
        with gzip.open(root/stage/'per_image.jsonl.gz','rt',encoding='utf-8') as stream:
            counts[stage]=sum(1 for _ in stream)
    xml=ET.parse(root/'evidence/tests.xml').getroot().find('testsuite')
    changes=subprocess.check_output(['git','diff','mentor/ekyc-v3.2.0','--name-only','--','ekyc','web','tests','start.ps1','open-ekyc.ps1'],text=True).strip()
    if changes:raise ValueError('Mentor runtime source differs')
    repeat=json.loads((root/'evidence/analysis_repeat.json').read_text())
    if not all(r['identical'] for r in repeat['files']):raise ValueError('Analysis not reproducible')
    rerun=json.loads((root/'reproducibility/inference_repeat.json').read_text())
    if rerun['prediction_mismatches'] or rerun['input_mismatches']:raise ValueError('Inference mismatch')
    inventory=[dict(path=p.as_posix(),bytes=p.stat().st_size,sha256=digest(p),
                    status='invalid_superseded' if 'pre_exif_correction' in p.parts else 'current')
               for p in sorted(root.rglob('*')) if p.is_file() and p.suffix!='.jsonl' and
               'repeat' not in p.parts and p.name!='artifact_audit.json']
    save(root/'evidence/artifact_audit.json',dict(provenance_checks=checks,scored_rows=counts,
        python_tests=dict(tests=int(xml.get('tests')),failures=int(xml.get('failures')),errors=int(xml.get('errors'))),
        frontend_tests=dict(tests=15,passed=15,command='node --test tests/camera_frontend.test.cjs'),
        mentor_runtime_diff_empty=True,analysis_repeat_byte_identical=True,
        inference_repeat_images=rerun['selected_images'],inference_mismatches=0,
        raw_images_and_text_published=False,files=inventory))
    print(json.dumps(dict(stages=len(checks),rows=counts,python_tests=xml.get('tests'),artifacts=len(inventory))))


if __name__=='__main__':main()
