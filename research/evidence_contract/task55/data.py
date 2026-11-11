"""Read-only cache/evidence access with completed-event payload binding.

Inference, model loading and historical log writes are deliberately absent.
The output normalizer is frozen and explicitly NOT an independent truth oracle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..normalized_output import NativeOutput, ReaderSpec, normalize
from ..runner import InputRequest
from ..source_graph import EvidenceGraph
from ..smoke_task4 import _report_from_dict

EC=Path(__file__).resolve().parents[1]
ROOT=EC.parents[1]
OUT=EC/'execution/task55_audit'
PILOT=EC/'local/task5_pilot_01'
PUBLIC=EC/'execution/task5_pilot/pilot_01'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')


def log_events(path):
    """Independent stdlib reimplementation of event-chain verification."""
    payload=Path(path).read_bytes()
    if payload and not payload.endswith(b'\n'):raise ValueError('Truncated historical event log')
    rows=[];previous='0'*64
    for line in payload.splitlines():
        row=json.loads(line);copy=dict(row);actual=copy.pop('event_sha256')
        if copy['previous_sha256']!=previous or digest(copy)!=actual:raise ValueError('Event chain mismatch')
        previous=actual;rows.append(row)
    return rows


class FrozenPilot:
    def __init__(self):
        lock=read(PUBLIC/'pilot_lock.json')
        for name,expected in lock['manifests'].items():
            if sha(PILOT/name)!=expected:raise ValueError('Changed TASK5 input/scoring manifest')
        for name,expected in lock['code_sha256'].items():
            if sha(ROOT/name)!=expected:raise ValueError('Changed TASK5 method code')
        self.packs=read(PILOT/'scoring.json')['packs']
        self.rows=read(PUBLIC/'evaluation_01.checks.json')['rows']
        if read(PUBLIC/'evaluation_replayed.checks.json')['rows']!=self.rows:raise ValueError('TASK5 replay differs')
        self.requests={r['pixel_sha256']:InputRequest(**r) for r in read(PILOT/'inputs.json')['inputs']}
        for request in self.requests.values():request.load()
        self.outputs={};self.raw={};self.logs={};self.log_hashes={}
        self.loaders_constructed=0;self.model_calls=0
        self.evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in PUBLIC.glob('*') if p.is_file()}
        for reader in ('rapid_v4','rapid_latin_v5','partial_42'):
            spec=ReaderSpec(**read(PILOT/reader/(reader+'.spec.json')))
            stores=[PILOT/reader,EC/'local/smoke_02'/reader]
            event_maps={}
            for store in stores:
                if read(store/(reader+'.spec.json'))!=spec.to_dict():raise ValueError('Reader/runtime mismatch')
                log=store/'events.jsonl';events=log_events(log)
                self.logs[str(log)]=events;self.log_hashes[str(log)]=sha(log)
                event_maps[store]=events
            for pixel,request in self.requests.items():
                key=digest(dict(schema='raw-reader-cache/1',reader=spec.fingerprint,
                    input_file_sha256=request.file_sha256,input_pixel_sha256=request.pixel_sha256))
                found=False
                for store in stores:
                    path=store/'raw'/(key+'.json')
                    if not path.exists():continue
                    envelope=read(path);p=envelope['payload'];events=event_maps[store]
                    if (digest(p)!=envelope['payload_sha256'] or p['reader_spec']!=spec.to_dict()
                            or p['cache_key']!=key or p['input_file_sha256']!=request.file_sha256
                            or p['input_pixel_sha256']!=pixel):raise ValueError('Raw cache binding mismatch')
                    starts=[e for e in events if e['event']=='inference_begin' and e.get('call_id')==p['call_id']]
                    completed=[e for e in events if e['event'] in ('inference_completed','inference_recovered')
                               and e.get('call_id')==p['call_id']]
                    if (len(starts)!=1 or starts[0]['cache_key']!=key or len(completed)!=1
                            or completed[0]['payload_sha256']!=envelope['payload_sha256']):
                        raise ValueError('Output not bound to its completed actual inference')
                    native=NativeOutput.from_dict(p['native'])
                    output=normalize(spec,native,input_file_sha256=request.file_sha256,input_pixel_sha256=pixel,
                        cache_key=key,call_id=p['call_id'],access_mode='replay')
                    if output.output_origin!='actual_model':raise ValueError('Injected output in real pilot')
                    self.outputs[(reader,pixel)]=output;self.raw[(reader,pixel)]=p
                    self.evidence_hashes[str(path.relative_to(ROOT))]=sha(path)
                    found=True;break
                if not found:raise ValueError('Missing raw output; audit cannot call a model')

    def instances(self):
        for raw in self.packs:
            graph=EvidenceGraph.from_dict(raw['graph'])
            report=_report_from_dict(raw['pair']['validation'])
            for reader in ('rapid_v4','rapid_latin_v5','partial_42'):
                yield raw,graph,report,self.outputs[(reader,report.before_pixel_sha256)],self.outputs[(reader,report.after_pixel_sha256)]

    def assert_read_only(self):
        for path,expected in self.log_hashes.items():
            if sha(path)!=expected:raise ValueError('Audit changed an inference event log')
        for relative,expected in self.evidence_hashes.items():
            if sha(ROOT/relative)!=expected:raise ValueError('Audit changed TASK5 evidence')
