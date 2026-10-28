"""Fine-tune Module 1 on the reconciled originals, splitting by physical document."""
import argparse
import csv
import random
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
from .config import ROOT, LABELS
from .io import write_json


class OriginalDataset(Dataset):
    def __init__(self, rows, training=False):
        self.rows = rows
        operations = [transforms.Resize((224,224))]
        if training:
            # Avoid blur/dark/perspective augmentation, which would alter the target quality label.
            operations.append(transforms.RandomRotation(3))
        operations.extend([transforms.ToTensor(), transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
        self.transform = transforms.Compose(operations)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(ROOT/row['relative_path']) as image:
            tensor = self.transform(image.convert('RGB'))
        return tensor, LABELS.index(row['label'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, default=ROOT/'data/manifest.csv')
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--initialize', type=Path, help='Optional warm-start checkpoint; omit for uncontaminated evaluation')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/training')
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error('--epochs must be positive')
    random.seed(42); np.random.seed(42); torch.manual_seed(42)
    rows = list(csv.DictReader(args.manifest.open(encoding='utf-8-sig')))
    groups = {s:{r['document'] for r in rows if r['split']==s} for s in ('train','val','test')}
    if any(not group for group in groups.values()) or groups['train']&groups['val'] or groups['train']&groups['test'] or groups['val']&groups['test']:
        raise ValueError('Missing split or document leakage across splits')
    loaders = {s:DataLoader(OriginalDataset([r for r in rows if r['split']==s], s=='train'),
                    batch_size=args.batch_size, shuffle=s=='train', num_workers=args.workers) for s in groups}
    model = models.mobilenet_v3_small(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(LABELS))
    if args.initialize:
        checkpoint = torch.load(args.initialize, map_location='cpu', weights_only=True)
        model.load_state_dict(checkpoint.get('state_dict', checkpoint), strict=True)
    model.to(args.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=.01)
    criterion = nn.CrossEntropyLoss(label_smoothing=.1)
    args.output.mkdir(parents=True, exist_ok=True)
    best, patience, history = float('inf'), 0, []
    def evaluate(loader, train=False):
        model.train(train)
        total_loss = correct = count = 0
        matrix = np.zeros((5,5),dtype=int)
        with torch.set_grad_enabled(train):
            for images, labels in loader:
                images, labels = images.to(args.device), labels.to(args.device)
                logits = model(images)
                loss = criterion(logits, labels)
                if train:
                    optimizer.zero_grad(); loss.backward(); optimizer.step()
                predictions = logits.argmax(1)
                total_loss += loss.item()*len(labels)
                count += len(labels)
                correct += int((predictions==labels).sum())
                for actual,predicted in zip(labels.cpu().tolist(),predictions.cpu().tolist()):
                    matrix[actual,predicted] += 1
        return dict(loss=total_loss/count, accuracy=correct/count, count=count, confusion_matrix=matrix.tolist())
    for epoch in range(args.epochs):
        train = evaluate(loaders['train'], True)
        val = evaluate(loaders['val'])
        history.append(dict(epoch=epoch+1,train=train,val=val))
        print(f"Epoch {epoch+1}: train={train['loss']:.4f}, val={val['loss']:.4f}",flush=True)
        write_json(args.output/'history.json',history)
        if val['loss'] < best:
            best, patience = val['loss'], 0
            torch.save(dict(state_dict=model.state_dict(), labels=list(LABELS)), args.output/'quality.pth')
        else:
            patience += 1
            if patience >= 3:
                break
    model.load_state_dict(torch.load(args.output/'quality.pth',map_location=args.device,weights_only=True)['state_dict'])
    test = evaluate(loaders['test'])
    test['labels'] = list(LABELS)
    test['warm_start'] = str(args.initialize) if args.initialize else None
    test['warning'] = 'Warm-start checkpoint may already have seen test documents' if args.initialize else None
    write_json(args.output/'test_metrics.json',test)


if __name__ == '__main__':
    main()
