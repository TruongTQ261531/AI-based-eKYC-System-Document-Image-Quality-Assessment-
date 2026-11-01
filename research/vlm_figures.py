"""Publication-style plots from completed public numeric outputs only."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from research.vlm_setup import OUT,sha,save


def main():
    def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
    models=['ocr_existing_web','original','control_seed_42','seed_42','seed_31415']
    labels=['V4 research OCR\nCPU','Base VLM\nGPU','Intact-content LoRA\nseed42, GPU','Partial-content LoRA\nseed42, GPU','Partial-content LoRA\nseed31415, GPU']
    tolerant={r['model']:r for r in read('format_analysis.json')['results'] if r['role']=='test'}
    strict={m:tolerant[m]['strict_summary'] for m in models if m!='ocr_existing_web'}
    strict['ocr_existing_web']=read('test_ocr.json')['summaries']['ocr_existing_web']
    alternative={m:tolerant[m]['tolerant_summary'] if m in tolerant else strict[m] for m in models}
    error=read('error_taxonomy.json')
    opportunities=next(r['totals']['opaque_mask_opportunities'] for r in error['results'])
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,1,figsize=(11,8),layout='constrained')
    x=np.arange(len(models));width=.34
    for ax,metric in zip(axes,['f1','masked_field_outputs']):
        for offset,source,label,color in [(-width/2,strict,'Strict extraction contract','#136f7d'),(width/2,alternative,'Whole-fence/null-tolerant parser','#cb7a37')]:
            values=[source[m][metric] for m in models]
            bars=ax.bar(x+offset,values,width,label=label,color=color)
            ax.bar_label(bars,labels=[f'{v:.3f}' if metric=='f1' else str(v) for v in values],padding=3,fontsize=9)
        ax.set_xticks(x,labels);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    axes[0].set_ylim(0,1.16);axes[0].set_ylabel('Exact key-value micro F1')
    axes[0].legend(loc='upper left',ncol=2,frameon=False,fontsize=9)
    axes[1].set_ylabel('Parsed outputs of masked fields')
    axes[1].set_ylim(0,max(1,max(alternative[m]['masked_field_outputs'] for m in models))*1.25)
    axes[1].set_title(f'Opaque-mask opportunities: {opportunities}; zero observed is not a calibrated safety guarantee',fontsize=10)
    fig.suptitle('Identity-disjoint synthetic test: 24 mock IDs, 120 images\nShared generator / layouts / fonts across roles; no independent camera collection',fontsize=13)
    fig.savefig(OUT/'test_metrics.png',dpi=200)
    fig.savefig(OUT/'test_metrics.svg')
    plt.close(fig)
    save(OUT/'figures.json',dict(code_sha256=sha(__file__),public_numeric_inputs_only=True,
        source_sha256={n:sha(OUT/n) for n in ('format_analysis.json','test_ocr.json','error_taxonomy.json')},
        file_sha256={n:sha(OUT/n) for n in ('test_metrics.png','test_metrics.svg')},
        invalid_strict_outputs_can_undercount_masked_field_outputs=True,
        ocr_python_dict_by_construction_not_generative_schema_benchmark=True))
    print('FIGURES_SAVED',flush=True)


if __name__=='__main__':main()
