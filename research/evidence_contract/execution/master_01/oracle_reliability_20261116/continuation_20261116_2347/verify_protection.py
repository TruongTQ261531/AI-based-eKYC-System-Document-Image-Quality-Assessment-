"""Check the intake's private immutable-file inventory; emit only aggregates."""
import hashlib
import json
from pathlib import Path

from research.evidence_contract.task55.data import EC


def run():
    path=EC/'local/master_01/oracle_reliability_20261116/continuation_20261116_2347/protected_before.json'
    raw=path.read_bytes();inventory=json.loads(raw)
    missing=changed=0
    for name,expected in inventory.items():
        file=EC/name
        if not file.is_file():missing+=1
        elif hashlib.sha256(file.read_bytes()).hexdigest()!=expected:changed+=1
    result=dict(status='PASS' if missing==changed==0 else 'FAIL',protected_files=len(inventory),
        missing=missing,changed=changed,inventory_sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(result,indent=2))
    if missing or changed:raise SystemExit(1)


if __name__=='__main__':run()
