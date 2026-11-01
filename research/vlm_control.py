"""Separate, declared LoRA control reusing the frozen learner in its own process."""
import argparse
import hashlib
import json

from research.vlm_setup import ROOT,CACHE,OUT,save,sha
from research.vlm_runtime import signature as primary_signature
from research.vlm_data import load as primary_load

PUBLIC=OUT/'control'
PRIVATE=CACHE/'control'
CAPTURES=('full','corner_clip','blur_glare')


def signature():
    return hashlib.sha256(json.dumps(dict(primary=primary_signature(),code=sha(__file__),
        protocol=sha(ROOT/'research/VLM_CONTROL_PROTOCOL.md'),captures=CAPTURES),sort_keys=True).encode()).hexdigest()


def load(role=None):
    rows=primary_load(role)
    return [r for r in rows if r['capture'] in CAPTURES] if role=='train' else rows


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','evaluate','seal'])
    p.add_argument('--role',choices=['development','test'],default='development');p.add_argument('--repeat',type=int,default=1)
    args=p.parse_args()
    from research import vlm_train as runner
    # Enter the primary mutex BEFORE redirecting the module's output roots.
    with runner.process_lock():
        PUBLIC.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
        manifest=json.loads((OUT/'assets.json').read_text(encoding='utf-8'));save(PUBLIC/'assets.json',manifest)
        runner.OUT=PUBLIC;runner.CACHE=PRIVATE;runner.signature=signature;runner.load=load
        if args.action=='train':
            save(PUBLIC/'design.json',dict(signature=signature(),primary_signature=primary_signature(),
                training_images=len(load('train')),training_ids=len({r['physical_id'] for r in load('train')}),
                captures=CAPTURES,seed=42,steps=192,microbatches=4,development_motivated=True,
                matched_optimizer_budget=True,matched_unique_raster_count=False))
            runner.train(42)
        elif args.action=='evaluate':runner.evaluate(args.role,'seed_42',args.repeat)
        else:
            result=json.loads((PUBLIC/'train_seed_42.json').read_text(encoding='utf-8'))
            dev=json.loads((PUBLIC/'development_seed_42_1.json').read_text(encoding='utf-8'))
            if result['signature']!=signature() or dev['signature']!=signature():raise ValueError('Control source changed')
            save(PUBLIC/'test_lock.json',dict(signature=signature(),primary_signature=primary_signature(),
                selected_model='seed_42',adapters={'42':{k:result[k] for k in ('selected_checkpoint','selected_adapter_sha256')}},
                development_summary=dev['summary'],test_scored=False,main_choice_unchanged=True,
                source_control_sha256=sha(__file__),protocol_sha256=sha(ROOT/'research/VLM_CONTROL_PROTOCOL.md')))


if __name__=='__main__':main()
