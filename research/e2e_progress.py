"""One-shot progress without printing source or recognized personal text."""
import json
from pathlib import Path


def main():
    root=Path('research/cache/e2e_ocr_v2');counts={}
    for repeat,expected in ((1,161),(2,32),(3,32)):
        completed=len(list((root/f'pass{repeat}').glob('*.json')))
        counts[f'pass{repeat}']=dict(completed=completed,expected=expected)
    journal=root/'events.jsonl';last=None
    if journal.exists():
        lines=journal.read_text(encoding='utf-8').splitlines()
        if lines:last=json.loads(lines[-1])
    print(json.dumps(dict(progress=counts,total_complete=sum(c['completed'] for c in counts.values()),
        total_expected=225,last_event=last,personal_text_printed=False),indent=2))


if __name__=='__main__':main()
