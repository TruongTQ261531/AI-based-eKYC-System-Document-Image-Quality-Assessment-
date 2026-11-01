"""Recreate the synthetic corpus without installing packages or fetching MIDV."""
import json
from research.vlm_setup import ROOT,OUT,sha
from research.vlm_data import DATA,build


def main():
    from research.recovery_setup import ASSETS,fetch_asset
    for item in ASSETS:
        if item[0].startswith('fonts/'):fetch_asset(*item)
    expected=json.loads((OUT/'dataset_card.json').read_text(encoding='utf-8'))
    if not (DATA/'samples.json').exists():build()
    if sha(DATA/'samples.json')!=expected['data_sha256']:raise ValueError('Recreated references differ from published data')
    samples=json.loads((DATA/'samples.json').read_text(encoding='utf-8'))
    for row in samples:
        if sha(ROOT/row['path'])!=row['input_sha256']:raise ValueError('Recreated raster changed')
    previous=set()
    for name in ('recovery_v4/dataset_manifest.json','recovery_v4/layout_stress.json'):
        path=ROOT/'research/results'/name
        if path.exists():
            value=json.loads(path.read_text(encoding='utf-8'))
            rows=value if isinstance(value,list) else value.get('rows',[])
            previous|={r['input_sha256'] for r in rows if 'input_sha256' in r}
    if previous&{r['input_sha256'] for r in samples}:raise ValueError('Raster overlaps earlier study')
    print('VERIFIED_SYNTHETIC_DATA',len(samples),'no reference/raster changes',flush=True)


if __name__=='__main__':main()
