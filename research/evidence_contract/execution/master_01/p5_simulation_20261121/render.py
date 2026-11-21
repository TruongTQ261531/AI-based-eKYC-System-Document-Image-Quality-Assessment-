"""Render the P5 feasibility matrix and sensitivity figures from aggregate counts only."""
import argparse
import json
from math import comb
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np


def pct(p):
    return 'NA' if p is None else f'{p*100:.1f}'


def interval(p):
    return 'NA' if not p['n'] else f"{pct(p['rate'])} [{pct(p['lo'])}, {pct(p['hi'])}]"


def primary(profile, design):
    return next(p for p in profile['points'] if p['label']=='effect_grid' and p['effect']==design['reference_effect'])


def grid_mde(x):
    return '—' if x is None else f'{100*x:.0f}'


def matrix(results, design):
    lines = ['# P5 · Feasibility matrix', '',
             'At the +10 percentage-point FAR reduction, all probabilities below are percentages of synthetic cohorts unless a different denominator is named. Brackets give pointwise 95% Wilson Monte Carlo intervals. Each scenario/point uses 1,200 cohorts in the recorded run. The nominal tests use the frozen v3 one-sided bootstrap limits.', '',
             '| Profile | P(all three pass) | P(insufficient) | Issued / simulated | MDE point / MC-supported (pp) | Power-only verdict | Statistical verdict |',
             '|---|---:|---:|---:|---:|---|---|']
    for name,r in results.items():
        p=primary(r,design)
        lines.append(f"| {name} | {interval(p['joint_pass'])} | {interval(p['insufficient'])} | {p['issued']}/{p['trials']} | {grid_mde(r['mde_grid_estimate'])} / {grid_mde(r['mde_grid_mc_supported'])} | {r['power_verdict']} | {r['statistical_verdict']} |")
    lines += ['', 'MDE is the first tested alternative whose joint pass estimate (or MC lower bound) reaches 80%. A dash means no such grid point. Inspect the curves before interpreting a crossing. The largest tested effect is 18 pp except for low disagreement (10 pp). Where a population floor fails, these are pass probabilities under a composite null; power and a useful MDE for that combination are inapplicable.', '',
              '## Type I error across three true nulls', '',
              'Numerator is false joint success; denominator includes every attempted cohort, including non-issued results. Each column changes the named population criterion; other assumptions are specified in the JSON. Some stress profiles can fail more than one population criterion.', '',
              '| Profile | FAR difference = 5 pp | Coverage = 79.99% | Labelled sensitivity = 79.99% |',
              '|---|---:|---:|---:|']
    for name,r in results.items():
        nulls={p['label']:p for p in r['points']}
        lines.append('| '+name+' | '+' | '.join(interval(nulls[k]['joint_pass']) for k in ('null_far','null_coverage','null_sensitivity'))+' |')
    lines += ['', '## Interval coverage conditional on issuance at +10 pp', '',
              'Each component reports P(lower limit ≤ true parameter | all three intervals issued). The last column requires simultaneous coverage; it has no separate 95% guarantee. Divide each hit count in the JSON by all trials for the probability of issuing covering bounds. NA means no bounds were issued.', '',
              '| Profile | Decision coverage | All-fault sensitivity | Paired FAR difference | Simultaneous |',
              '|---|---:|---:|---:|---:|']
    for name,r in results.items():
        p=primary(r,design)
        lines.append('| '+name+' | '+' | '.join(interval(v) for v in [*p['coverage_if_issued'].values(),p['simultaneous_coverage_if_issued']])+' |')
    lines += ['', '## Guard accounting at +10 pp', '',
              'The first three counts partition insufficient cohorts. A bootstrap draw is invalid if either truth denominator is zero. Degenerate coverage is counted after the denominator guard and can coincide with another constant metric. Waiver is a counterfactual on identical resamples. It bypasses only the constant-coverage check.', '',
              '| Profile | <30 clusters | Any undefined draw | Any constant metric | Constant coverage | Invalid draws / draws run | Joint pass with waiver (%) | Additional pass probability (%) |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,r in results.items():
        p=primary(r,design)
        lines.append(f"| {name} | {p['short_clusters']} | {p['invalid_bootstrap_cohorts']} | {p['degenerate_any']} | {p['degenerate_by_metric']['decision_coverage']} | {p['invalid_bootstrap_draws']}/{p['bootstrap_draws']} | {pct(p['pass_if_only_coverage_degeneracy_waived']['rate'])} | {interval(p['additional_passes_if_waived'])} |")
    return '\n'.join(lines)+'\n'


def plots(results, design, folder):
    fig, ax = plt.subplots(figsize=(9,5.2), layout='constrained')
    for name in ('reference','strong_dependence','rare_fault','missing_truth','tight_floors','high_disagreement','near_full_coverage'):
        pts = [p for p in results[name]['points'] if p['label']=='effect_grid']
        xx = [100*p['effect'] for p in pts]
        yy = [p['joint_pass'] for p in pts]
        line, = ax.plot(xx, [p['rate'] for p in yy], marker='o', ms=4, label=name.replace('_',' '))
        ax.fill_between(xx,[p['lo'] for p in yy],[p['hi'] for p in yy],color=line.get_color(),alpha=.09)
    ax.axhline(.80,color='0.35',ls='--',lw=1)
    ax.set(xlabel='True paired FAR reduction (percentage points)',ylabel='Probability of passing all three criteria',
           title='Statistical power under the 200-document design',ylim=(-.02,1.02))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc='center left',bbox_to_anchor=(1,.5),frameon=False)
    fig.savefig(folder/'power.png',dpi=155)
    plt.close(fig)

    fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    coverage=np.linspace(.975,1.,251)
    for rho in (0,.2,.6):
        # Fixed cluster size m=4. Constant cluster counts imply constant bootstrap coverage.
        pmf = np.array([(1-rho)*comb(4,j)*coverage**j*(1-coverage)**(4-j) +
                        rho*((1-coverage) if j==0 else coverage if j==4 else 0) for j in range(5)])
        ax.plot(100*coverage, (pmf**200).sum(axis=0),label=f'ICC {rho:g}')
    names=('near_full_coverage','full_coverage')
    for name in names:
        p=primary(results[name],design)
        ax.scatter(100*p['target'][0],p['degenerate_by_metric']['decision_coverage']/p['trials'],
                   color='black',s=25,zorder=4)
    ax.set(title='Constant decision coverage',xlabel='Population decision coverage (%)',ylabel='Probability')
    ax.ticklabel_format(axis='x',useOffset=False)
    ax.legend(frameon=False)
    loc=np.arange(len(names))
    for shift,key,title in ((-.18,'joint_pass','Frozen v3'),(.18,'pass_if_only_coverage_degeneracy_waived','Coverage-only waiver')):
        vals=[primary(results[n],design)[key] for n in names]
        bx.bar(loc+shift,[v['rate'] for v in vals],width=.36,label=title)
        bx.errorbar(loc+shift,[v['rate'] for v in vals],
                    yerr=[[max(0,v['rate']-v['lo']) for v in vals],[max(0,v['hi']-v['rate']) for v in vals]],
                    fmt='none',color='0.2',capsize=3)
    bx.set_xticks(loc,['99.9%','100%'])
    bx.set(title='Joint pass at +10 pp FAR reduction',xlabel='Population decision coverage',ylabel='Probability')
    bx.legend(frameon=False)
    for axis in (ax,bx):
        axis.set_ylim(-.02,1.05)
        axis.yaxis.set_major_formatter(PercentFormatter(1))
    fig.savefig(folder/'coverage_guard.png',dpi=155)
    plt.close(fig)


if __name__ == '__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('folder',type=Path)
    folder=cli.parse_args().folder
    design=json.loads((folder/'design.json').read_bytes())
    results=json.loads((folder/'operating_points.json').read_bytes())['profiles']
    (folder/'MATRIX.md').write_text(matrix(results,design),encoding='utf8',newline='\n')
    plots(results,design,folder)
