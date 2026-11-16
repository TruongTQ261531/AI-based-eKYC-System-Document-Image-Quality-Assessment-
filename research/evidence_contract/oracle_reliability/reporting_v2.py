"""Add explicit deferral/invalid/structural rates without altering frozen metrics.

Descriptive accounting only: no inference, relabeling, confidence intervals or GO.
"""
import argparse
import json
from pathlib import Path

from ..reviewer_tools.strict import need, sha_bytes
from ..task55.data import EC, save_new
from . import reporting

STATES={'FAULT','NO_FAULT','UNKNOWN','INVALID_TEST','STRUCTURAL_ERROR'}


def validate_cells(cells):
    for cell in cells:
        need(type(cell['count']) is int and cell['count']>0, 'Positive integer cell weight required')
        need(cell['truth'] is None or type(cell['truth']) is bool, 'Boolean/unknown truth required')
        need(isinstance(cell['state'],str) and cell['state'] in STATES, 'Known decision state required')


def summarize(cells):
    validate_cells(cells);base=reporting.summarize(cells)
    n=base['rows'];counts=base['status_counts'];unknown=counts.get('UNKNOWN',0);invalid=counts.get('INVALID_TEST',0)
    return dict(base=base,unresolved_truth_rows=n-base['labeled_rows'],rates=dict(
        abstention_unknown=reporting.rate(unknown,n),invalid_test=reporting.rate(invalid,n),
        combined_deferral=reporting.rate(unknown+invalid,n),
        structural_error=reporting.rate(counts.get('STRUCTURAL_ERROR',0),n),
        truth_availability=reporting.rate(base['labeled_rows'],n)))


def report(cells):
    validate_cells(cells);groups=[]
    for dataset in sorted({c['dataset'] for c in cells}):
        for partition in sorted({c['partition'] for c in cells if c['dataset']==dataset}):
            panel=[c for c in cells if c['dataset']==dataset and c['partition']==partition]
            views={'all':panel}
            for axis in ('contract','cluster'):
                for key in sorted({c[axis] for c in panel}):views[axis+':'+key]=[c for c in panel if c[axis]==key]
            for view,subset in views.items():
                for method in sorted({c['method'] for c in subset}):
                    for endpoint in sorted({c['endpoint'] for c in subset if c['method']==method}):
                        pool=[c for c in subset if c['method']==method and c['endpoint']==endpoint]
                        groups.append(dict(dataset=dataset,partition=partition,view=view,method=method,
                                           endpoint=endpoint,metrics=summarize(pool)))
    return groups


def run(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    need(output.is_relative_to((EC/'execution').resolve()),'Public execution destination required')
    need(not output.exists(),'Preserve previous report')
    raw=source.read_bytes();cells=json.loads(raw);groups=report(cells)
    value=dict(schema='oracle-accounting-supplement/2',input_sha256=sha_bytes(raw),
        source_cells=len(cells),metric_groups=len(groups),groups=groups,confirmatory=False,
        new_observations=0,model_calls=0,training_runs=0,labels_changed=0,
        scope='Same historical aggregate cells; all zero-denominator rates are null (NA), not zero')
    need(source.read_bytes()==raw,'Source changed during reporting')
    save_new(output/'report.json',value)
    return dict(status='PASS_REPORT_GENERATED',metric_groups=len(groups),source_cells=len(cells),new_observations=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(run(args.input,args.output),indent=2))
