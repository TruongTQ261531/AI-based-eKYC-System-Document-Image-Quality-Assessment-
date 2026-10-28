"""Fine-tune the supplied classifier on frozen features of all original TIFFs.

This is supervised quality training, not document/person database retrieval.
The existing backbone may have seen the new held-out documents previously;
report this warm-start limitation explicitly instead of claiming an independent test.
"""
import argparse
import csv
import hashlib
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance
import torch
from torch import nn

from .config import ROOT, LABELS
from .io import write_json
from .module1_quality import QualityAssessment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/training_original_transfer')
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.workers) < 1:
        parser.error('epochs/batch-size/workers must be positive')
    random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.set_num_threads(4)
    started = time.monotonic()
    manifest = ROOT/'data/manifest.csv'
    checkpoint = ROOT/'best_mobilenet_diqa_local.pth'
    rows = list(csv.DictReader(manifest.open(encoding='utf-8-sig')))
    splits = {s: {r['document'] for r in rows if r['split']==s} for s in ('train','val','test')}
    if len(rows)!=21050 or any(not v for v in splits.values()) or any(splits[a]&splits[b] for a,b in [('train','val'),('train','test'),('val','test')]):
        raise ValueError('Unexpected manifest or split leakage')
    args.output.mkdir(parents=True, exist_ok=True)
    model = QualityAssessment(checkpoint).model.eval()
    for parameter in model.parameters(): parameter.requires_grad_(False)
    transform = QualityAssessment(checkpoint).transform
    fingerprint = hashlib.sha256(manifest.read_bytes()+checkpoint.read_bytes()).hexdigest()
    cache = args.output/'features.npz'
    labels = np.array([LABELS.index(r['label']) for r in rows],dtype=np.int64)
    train_idx = np.array([i for i,r in enumerate(rows) if r['split']=='train'])
    val_idx = np.array([i for i,r in enumerate(rows) if r['split']=='val'])
    test_idx = np.array([i for i,r in enumerate(rows) if r['split']=='test'])
    refs = np.array([r['is_reference']=='1' for r in rows])
    def features(tensors):
        with torch.inference_mode():
            return model.avgpool(model.features(tensors)).flatten(1).cpu().numpy()
    def load(row):
        with Image.open(ROOT/row['relative_path']) as image:
            return transform(image.convert('RGB'))
    vectors = None
    if cache.exists():
        with np.load(cache) as data:
            if str(data['fingerprint']) == fingerprint:
                vectors = data['features']
    if vectors is None:
        batches=[]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for start in range(0,len(rows),args.batch_size):
                batch = torch.stack(list(pool.map(load, rows[start:start+args.batch_size])))
                batches.append(features(batch))
                completed=min(start+args.batch_size,len(rows))
                if start//args.batch_size % 10==0 or completed==len(rows):
                    status=dict(phase='extracting_original_features',completed=completed,total=len(rows),
                                elapsed_seconds=round(time.monotonic()-started,1))
                    write_json(args.output/'progress.json',status)
                    print(json.dumps(status),flush=True)
        vectors=np.concatenate(batches)
        np.savez_compressed(cache,features=vectors,fingerprint=fingerprint)
    # Mild, label-preserving variation of train references only. Val/test stay untouched.
    augmented=[]
    for i in train_idx[refs[train_idx]]:
        with Image.open(ROOT/rows[i]['relative_path']) as image:
            rgb=image.convert('RGB')
            augmented += [transform(ImageEnhance.Brightness(rgb).enhance(b)) for b in (.9,1.1)]
    extra=features(torch.stack(augmented)) if augmented else np.empty((0,vectors.shape[1]),np.float32)
    classifier=model.classifier
    for parameter in classifier.parameters(): parameter.requires_grad_(True)
    criterion=nn.CrossEntropyLoss(label_smoothing=.05)
    optimizer=torch.optim.AdamW(classifier.parameters(),lr=2e-4,weight_decay=.01)
    def evaluate(indices):
        classifier.eval()
        with torch.inference_mode():
            logits=classifier(torch.from_numpy(vectors[indices]))
            predictions=logits.argmax(1).numpy()
            loss=float(criterion(logits,torch.from_numpy(labels[indices])))
        matrix=np.zeros((5,5),dtype=int)
        np.add.at(matrix,(labels[indices],predictions),1)
        denom=matrix.sum(0)+matrix.sum(1)
        f1=np.divide(2*np.diag(matrix),denom,out=np.zeros(5,dtype=float),where=denom>0)
        localrefs=refs[indices]
        reference_accuracy=float(np.mean(predictions[localrefs]==0)) if localrefs.any() else 0.
        return dict(loss=loss,accuracy=float(np.mean(predictions==labels[indices])),macro_f1=float(f1.mean()),
                    reference_clean_recall=reference_accuracy,reference_count=int(localrefs.sum()),confusion_matrix=matrix.tolist())
    baseline=evaluate(val_idx)
    history=[]
    base_train=torch.from_numpy(vectors[train_idx]); base_labels=torch.from_numpy(labels[train_idx])
    # Each reference carries 20x weight; no val/test examples participate in optimization.
    sample_weights=torch.ones(len(train_idx)); sample_weights[torch.from_numpy(refs[train_idx])]=20
    train_features=torch.cat([base_train,torch.from_numpy(extra)])
    train_labels=torch.cat([base_labels,torch.zeros(len(extra),dtype=torch.int64)])
    sample_weights=torch.cat([sample_weights,torch.full((len(extra),),10.)])
    best=-float('inf'); best_state=None; patience=0
    for epoch in range(1,args.epochs+1):
        classifier.train()
        choices=torch.multinomial(sample_weights,len(train_features),replacement=True)
        total=0.
        for batch in choices.split(256):
            optimizer.zero_grad()
            loss=criterion(classifier(train_features[batch]),train_labels[batch])
            loss.backward(); optimizer.step(); total+=float(loss.detach())*len(batch)
        validation=evaluate(val_idx)
        # Require both overall quality and the previously unsupported clean-reference domain.
        score=.85*validation['macro_f1']+.15*validation['reference_clean_recall']
        history.append(dict(epoch=epoch,train_loss=total/len(choices),validation=validation))
        write_json(args.output/'history.json',history)
        write_json(args.output/'progress.json',dict(phase='training_classifier',epoch=epoch,max_epochs=args.epochs,validation=validation))
        print(f"epoch={epoch} val_f1={validation['macro_f1']:.4f} reference_clean_recall={validation['reference_clean_recall']:.4f}",flush=True)
        if score>best:
            best=score; best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}; patience=0
            torch.save(dict(state_dict=best_state,labels=list(LABELS),training='frozen_backbone_transfer',
                            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest()),args.output/'quality.pth')
        else:
            patience+=1
            if patience>=6: break
    model.load_state_dict(best_state)
    final_validation=evaluate(val_idx)
    test=evaluate(test_idx)
    eligible=(final_validation['macro_f1']>=baseline['macro_f1']-.02 and
              final_validation['reference_clean_recall']>baseline['reference_clean_recall'])
    report=dict(training='frozen_backbone_transfer',optimized_parameters='MobileNet classifier only',
        source='full_dataset_original TIFF images; no lookup at inference',total_originals=len(rows),
        train_count=len(train_idx),validation_count=len(val_idx),test_count=len(test_idx),
        extra_train_reference_variants=len(extra),baseline_validation=baseline,validation=final_validation,test=test,
        eligible_for_activation=eligible,epochs=len(history),elapsed_seconds=round(time.monotonic()-started,1),
        limitation='Warm-start backbone training overlap is unknown; test metrics are NOT an independent generalization claim.',
        checkpoint_sha256=hashlib.sha256((args.output/'quality.pth').read_bytes()).hexdigest())
    write_json(args.output/'training_report.json',report)
    write_json(args.output/'progress.json',dict(phase='complete',eligible_for_activation=eligible))
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__': main()
