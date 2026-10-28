import argparse
import csv
import json
from pathlib import Path
from .config import ROOT, Settings
from .io import write_json


def main():
    parser = argparse.ArgumentParser(description='Five-module local eKYC')
    sub = parser.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--workers', type=int, default=8)
    for command in ('verify', 'batch'):
        p = sub.add_parser(command)
        p.add_argument('--output', type=Path, default=ROOT/'outputs')
        p.add_argument('--checkpoint', type=Path, default=Settings().quality_model)
        p.add_argument('--languages', nargs='+', default=['vi'], choices=['vi'], help='ScanOCR/VietOCR Vietnamese recognition')
        if command == 'verify':
            p.add_argument('--card', type=Path, required=True)
            p.add_argument('--selfie', type=Path)
            p.add_argument('--corners', type=Path, help='JSON array of four [x,y] source-image corners')
        else:
            p.add_argument('--manifest', type=Path, default=ROOT/'data/manifest.csv')
            p.add_argument('--limit', type=int, default=None)
            p.add_argument('--split', choices=['train','val','test'])
    args = parser.parse_args()
    if args.command == 'prepare':
        from .dataset import prepare
        prepare(workers=args.workers)
        return
    from .pipeline import EKYCPipeline
    pipeline = EKYCPipeline(Settings(quality_model=args.checkpoint, output_dir=args.output, ocr_languages=tuple(args.languages)))
    if args.command == 'verify':
        corners = json.loads(args.corners.read_text()) if args.corners else None
        result = pipeline.run(args.card, args.selfie, corners)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result['decision'] == 'error':
            raise SystemExit(1)
    else:
        rows = list(csv.DictReader(args.manifest.open(encoding='utf-8-sig')))
        if args.split:
            rows = [r for r in rows if r['split'] == args.split]
        if args.limit is not None:
            if args.limit <= 0:
                parser.error('--limit must be positive')
            rows = rows[:args.limit]
        summary = []
        for index, row in enumerate(rows, 1):
            result = pipeline.run(ROOT/row['relative_path'])
            summary.append(dict(image=row['image_name'], label=row['label'], run_id=result['run_id'],
                                decision=result['decision'], reason=result.get('reason')))
            print(f"[{index}/{len(rows)}] {row['image_name']}: {result['decision']}", flush=True)
            write_json(args.output/'batch_summary.json', summary)


if __name__ == '__main__':
    main()
