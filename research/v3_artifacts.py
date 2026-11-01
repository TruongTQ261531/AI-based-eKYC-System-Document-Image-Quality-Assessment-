"""Audited numeric plots and a local-only selected adapter export."""
import shutil
import numpy as np
from research.v3_common import *

def make():
    if read(OUT/'audit.json')['status']!='passed':raise ValueError('Audit required')
    lock=read(OUT/'test_lock.json');key=lock['selected_model'];record=lock['models'][key]
    dest=CACHE/'export'/key;dest.mkdir(parents=True,exist_ok=True);hashes={}
    if record['path']:
        source=ROOT/record['path']
        for name in ('adapter_config.json','adapter_model.safetensors'):
            digest=sha(source/name)
            if (dest/name).exists() and sha(dest/name)!=digest:raise ValueError('Existing export differs')
            shutil.copyfile(source/name,dest/name);hashes[name]=digest
    base=read(ROOT/'research/results/vlm_lora_v1/assets.json')
    manifest=dict(signature=signature(),selected_model=key,profile=lock['profile'],adapter_sha256=hashes,
        base_model=base['model_id'],base_revision=base['revision'],
        base_weights_sha256=next(r['sha256'] for r in base['model'] if r['file']=='model.safetensors'),
        full_Vintern_vision_projector_and_tokenizer_required=True,apply_adapter_to='model.language_model' if hashes else None,
        merged_full_model=False,weights_uploaded=False,private_labels_copied=False)
    save(dest/'model_manifest.json',manifest)
    (dest/'README.txt').write_text('Load the complete pinned Vintern model, vision, projector and tokenizer.\n'
        'If present, apply this LoRA to model.language_model. The PEFT Qwen name alone is not a VLM.\n'
        'Use the sealed rectification profile and V2 prompt, as in research.v3_web.\n'
        'Launch start-source-v3.ps1. Weights stay local; no private examples are exported.\n',encoding='utf-8',newline='\n')
    save(OUT/'export.json',dict(directory=dest.relative_to(ROOT).as_posix(),**manifest))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from research.v3_metrics import summary
    keys=['original','v1','control_42','partial_42','source_42','control_31415','partial_31415','source_31415']
    records={k:read(OUT/f'test_{k}.json')['rows'] for k in keys}
    dest=OUT/'figures';dest.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(9,5.5),layout='constrained');y=np.arange(len(keys));height=.32
    for offset,source,color,label in [(-height/2,'authored','#198882','Authored mock rasters'),(height/2,'midv2020','#304c79','Photographed mock IDs')]:
        values=[summary([r for r in records[k] if r['source']==source])['f1'] for k in keys]
        bars=ax.barh(y+offset,values,height=height,color=color,label=label)
        ax.bar_label(bars,labels=[f'{v:.3f}' for v in values],padding=3,fontsize=8)
    ax.set(yticks=y,yticklabels=keys,xlim=(0,1.1),xlabel='Micro F1 under source-aware references',title='Matched pixels; body-target vs source-target supervision')
    ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.legend(loc='lower right',fontsize=8)
    fig.savefig(dest/'source_f1.png',dpi=160);fig.savefig(dest/'source_f1.svg',metadata={'Date':None});plt.close(fig)
    save(OUT/'figure_provenance.json',dict(signature=signature(),source='Audited numeric result files; no document images',
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(dest.glob('*'))]))

if __name__=='__main__':make()
