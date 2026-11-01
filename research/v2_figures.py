"""Publication-style figures drawn only from audited numeric results."""
import numpy as np
from research.v2_common import *

def make():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from research.v2_runtime import summary
    if read(OUT/'audit.json')['status']!='passed':raise ValueError('Audited results required')
    keys=['original','v1','control_42','partial_42','control_31415','partial_31415','rapid_v4','rapid_latin_v5']
    labels=['Original Vintern','V1 transfer','V2 control /42','V2 partial /42','V2 control /31415','V2 partial /31415','PP-OCRv4 + layout','Latin PP-OCRv5 + layout']
    cpu=read(OUT/'test_cpu.json');rows={k:read(OUT/f'test_{k}.json')['rows'] for k in keys[:6]}
    for k in keys[6:]:rows[k]=[r for r in cpu['rows'] if r['model']==k]
    dest=OUT/'figures';dest.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    fig,ax=plt.subplots(figsize=(10,5.8),layout='constrained');y=np.arange(len(keys));h=.34
    for offset,source,color,title in [(-h/2,'authored','#198882','Authored mock rasters'),(h/2,'midv2020','#304c79','Photographed mock IDs')]:
        values=[summary([r for r in rows[k] if r['source']==source])['f1'] for k in keys]
        bars=ax.barh(y+offset,values,height=h,color=color,label=title)
        ax.bar_label(bars,labels=[f'{v:.3f}' for v in values],padding=3,fontsize=8)
    ax.set(yticks=y,yticklabels=labels,xlim=(0,1.13),xlabel='Key-value micro F1 (17 optional keys)',title='V2 R2: separate synthetic and photographed-source performance')
    ax.invert_yaxis();ax.set_xticks(np.arange(0,1.01,.2));ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.legend(loc='lower right',fontsize=8)
    fig.savefig(dest/'source_f1.png');fig.savefig(dest/'source_f1.svg');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
    for seed0,ax in zip(CONFIG['seeds'],axes):
        for arm,color in [('control','#66758a'),('partial','#198882')]:
            events=read(OUT/f'train_{arm}_{seed0}.json')['events'];x=[r['step'] for r in events];loss=np.array([r['loss'] for r in events])
            smooth=np.convolve(loss,np.ones(16)/16,mode='valid')
            ax.plot(x[15:],smooth,color=color,label=arm)
        ax.set(title=f'Seed {seed0}',xlabel='Optimizer step',ylabel='Training loss (16-step mean)');ax.grid(alpha=.15);ax.legend()
    fig.savefig(dest/'training_curves.png');fig.savefig(dest/'training_curves.svg');plt.close(fig)
    save(OUT/'figure_provenance.json',dict(signature=signature(),source='Audited numeric test/train JSON only; no document images or personal text',
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(dest.glob('*'))]))
    print('V2_FIGURES_READY',flush=True)

if __name__=='__main__':make()
