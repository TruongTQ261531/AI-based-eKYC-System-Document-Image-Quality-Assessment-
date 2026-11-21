"""Render P5B tables and the two sensitivity figures from public counters."""
import argparse
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest

NAMES = {'v3':'v3 percentile', 'cluster_t':'Cluster t', 'bounded':'Hoeffding'}
COLORS = ['#236a99','#bf5913','#297649']


def percentage(k,n):
    return f'{100*k/n:.1f}' if n else 'NA'


def interval(k,n):
    if not n:
        return 'NA'
    ci=binomtest(k,n).proportion_ci(method='wilson')
    return f'{100*k/n:.1f} [{max(0,100*ci.low):.1f}, {min(100,100*ci.high):.1f}]'


def render(folder):
    reports={k:json.loads((folder/(k+'.json')).read_bytes()) for k in ('calibration','held_out')}
    lines=['# P5B · Ma trận theo giả định', '',
           'Đơn vị là %. Khoảng trong ngoặc là Wilson 95% theo từng điểm. P(đạt) và P(thiếu) dùng mọi cohort làm mẫu số. '
           'Độ phủ chỉ tính trên cohort xuất cả ba cận. C/S/Δ là coverage quyết định, độ nhạy trên lỗi có nhãn và giảm FAR. '
           'P(đạt) là power khi cả ba estimand đạt ngưỡng, là sai số loại I khi có null đúng, và không xác định về hiệu quả khi thiếu toàn bộ truth.', '']
    for stage,report in reports.items():
        n=report['n']
        lines+=['## '+stage,'',f'{n} cohort cho mỗi hàng và phương pháp, cùng đầu vào theo cặp.','',
                '| Scenario | Phương pháp | P(đạt cả ba) [95% MC] | P(thiếu) | Xuất cận | Độ phủ C / S / Δ | Độ phủ đồng thời |',
                '|---|---|---:|---:|---:|---:|---:|']
        for key,row in report['points'].items():
            if 'methods' not in row:
                lines.append(f'| {key} | Loại trước mô phỏng | — | — | — | — | — |')
                continue
            for method,s in row['methods'].items():
                issued=s['issued']
                coverage=' / '.join(percentage(k,issued) for k in s['covers'])
                lines.append(f"| {key} | {NAMES[method]} | {interval(s['joint'],n)} | {percentage(s['insufficient'],n)} | {issued}/{n} | {coverage} | {percentage(s['joint_covers'],issued)} |")
        lines += ['', '### Báo đạt sai ở các biên', '',
                  '| Null | Phương pháp | Sai số biên [95% MC] | Sai số đồng thời [95% MC] |',
                  '|---|---|---:|---:|']
        for i,scenario in enumerate(('null_coverage','null_sensitivity','null_far','null_joint','stress_template_null')):
            for m,s in report['points'][scenario]['methods'].items():
                indices=[0,1,2] if scenario=='null_joint' else [1 if scenario=='stress_template_null' else i]
                marginal=' / '.join(interval(s['passes'][j],n) for j in indices)
                lines.append(f"| {scenario} | {NAMES[m]} | {marginal} | {interval(s['joint'],n)} |")
        lines+=['']
    (folder/'MATRIX.md').write_bytes(('\n'.join(lines).rstrip()+'\n').encode())
    report=reports['held_out']
    n=report['n']
    fig,axs=plt.subplots(1,2,figsize=(10,4.7),layout='constrained')
    ids=[50,100,150,200]
    for m,col in zip(NAMES,COLORS):
        rows=[report['points']['mixed_'+str(k)]['methods'][m] for k in ids]
        for ax,field in zip(axs,('joint','insufficient')):
            ax.plot(ids,[100*r[field]/n for r in rows],marker='o',color=col,label=NAMES[m])
    axs[0].axhline(80,color='.4',linestyle=':',label='Power target')
    for ax,title in zip(axs,['All three criteria pass','Insufficient information']):
        ax.set(title=title,xlabel='Physical IDs',ylabel='Cohorts (%)',xticks=ids,ylim=(-4,105))
        ax.grid(axis='y',alpha=.25)
    axs[0].legend(fontsize=9)
    fig.suptitle('D4 mixed panel · held-out simulation')
    fig.savefig(folder/'size.png',dpi=150)
    plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4.8),layout='constrained')
    for idx,(m,col) in enumerate(zip(NAMES,COLORS)):
        offset=(idx-1)*.23
        points=report['points']
        rates=[100*points[k]['methods'][m]['joint']/n for k in ('null_coverage','null_sensitivity','null_far','stress_template_null')]
        axs[0].bar(np.arange(4)+offset,rates,.22,color=col,label=NAMES[m])
        rows=[points[k]['methods'][m] for k in ('mixed_200','stress_near','stress_full')]
        axs[1].bar(np.arange(3)+offset,[100*r['issued']/n for r in rows],.22,color=col)
    axs[0].axhline(5,color='.35',linestyle=':')
    axs[0].set(title='False joint success',xticks=range(4),xticklabels=['Coverage','Sensitivity','FAR','Template\n+ sens.'],ylabel='Cohorts (%)',xlabel='True null')
    axs[1].set(title='All intervals issued',xticks=range(3),xticklabels=['D4 mixed','Stress\n99.9%','Stress\n100%'],ylabel='Cohorts (%)',ylim=(0,105))
    axs[0].legend(fontsize=9)
    fig.suptitle('Calibration and boundary behaviour · held-out simulation')
    fig.savefig(folder/'calibration.png',dpi=150)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    render(parser.parse_args().folder)
