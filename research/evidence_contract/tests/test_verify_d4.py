import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from research.evidence_contract.oracle_reliability.verify_d4 import verify


EC = Path(__file__).resolve().parents[1]
CONTROLS = EC / 'execution/master_01/d4_development_20261117/controls_01'


def test_published_d4_controls_verify():
    result = verify(CONTROLS)
    assert result['paired_tier_evaluations'] == 144
    assert result['divergence_tier_pairs'] == 16


@pytest.mark.parametrize('field', ('shared_input_sha256', 'endpoints', 'checked_reasons', 'asserted_reasons'))
def test_divergence_must_match_paired_results(tmp_path, field):
    folder = tmp_path / 'controls'
    shutil.copytree(CONTROLS, folder)
    path = folder / 'divergences.json'
    rows = json.loads(path.read_bytes())
    row = rows[0]
    if field.endswith('_reasons'):
        row[field]['pointwise'] = 'different_reason'
    elif field == 'endpoints':
        row[field] = ['structure']
    else:
        row[field] = '0' * 64
    path.write_text(json.dumps(rows), encoding='utf-8')
    manifest = folder / 'manifest.json'
    inventory = json.loads(manifest.read_bytes())
    inventory['files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(inventory), encoding='utf-8')
    with pytest.raises(ValueError, match='Divergence details'):
        verify(folder)


def test_optimized_cli_rejects_incomplete_inventory(tmp_path):
    folder = tmp_path / 'controls'
    shutil.copytree(CONTROLS, folder)
    manifest = folder / 'manifest.json'
    inventory = json.loads(manifest.read_bytes())
    del inventory['files']['guard_matrix.json']
    manifest.write_text(json.dumps(inventory), encoding='utf-8')
    result = subprocess.run(
        [sys.executable, '-B', '-O', '-m', 'research.evidence_contract.oracle_reliability.verify_d4', str(folder)],
        cwd=EC.parents[1], capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert 'D4 artifact inventory' in result.stderr
