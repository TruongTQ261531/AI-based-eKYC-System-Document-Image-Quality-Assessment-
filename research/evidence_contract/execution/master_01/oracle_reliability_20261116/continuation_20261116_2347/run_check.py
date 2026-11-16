"""Record an explicitly supplied local validation command without hiding failures."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def main():
    name, *command = sys.argv[1:]
    if not re.fullmatch('[a-z0-9_]+', name) or not command:
        raise ValueError('Use a receipt name and an explicit command')
    base=Path(__file__).resolve().parent;log=base/(name+'.log');receipt=base/(name+'.json')
    if log.exists() or receipt.exists():
        raise FileExistsError('Keep previous validation receipts')
    started=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log.write_bytes(result.stdout)
    output=result.stdout.decode('utf-8',errors='replace')
    counts={key:int(match[1]) if (match:=re.search(r'(\d+) '+key+r'\b',output)) else 0
            for key in ('passed','failed','skipped','deselected')}
    subtests=re.search(r'(\d+) subtests passed',output)
    value=dict(command=command,cwd=str(Path.cwd()),python=sys.version,head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        start=started,end=datetime.now(timezone.utc).isoformat(),exit_code=result.returncode,counts=counts,
        subtests_passed=int(subtests[1]) if subtests else 0,stdout_stderr_sha256=hashlib.sha256(result.stdout).hexdigest(),log=log.name,
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    receipt.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    print(output,flush=True)
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
