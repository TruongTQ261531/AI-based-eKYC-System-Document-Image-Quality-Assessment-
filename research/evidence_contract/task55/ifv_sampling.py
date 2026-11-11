"""Freeze a development-only case sample from the saved audit, without reading OCR outputs."""
from collections import defaultdict
import random

from .data import EC, OUT, digest, read, save_new, sha

RECOVERY = EC / 'execution/task55_recovery'
SAMPLE = EC / 'local/task55_analyst/ifv_sample.json'
IDENTITY = ('physical_id_sha256', 'original_pixel_sha256', 'followup_pixel_sha256',
            'contract_id', 'field_key', 'reader', 'graph_sha256')
SEED = 550055
NO_ALERT_BUDGET = 28


def select(rows, *, seed=SEED, no_alert_budget=NO_ALERT_BUDGET):
    clusters = defaultdict(list)
    for row in rows:
        identity = [row[key] for key in IDENTITY]
        clusters[digest(identity)].append(row)

    strata = defaultdict(list)
    for identity, aliases in sorted(clusters.items()):
        first = aliases[0]
        if len({digest([r['stratum'], r['validity'], r['checks']]) for r in aliases}) != 1:
            raise ValueError('Same comparison has conflicting annotations or decisions')
        if first['stratum'] != 'primary':
            stratum = 'diagnostic/' + first['stratum']
        elif first['checks']['A']['alarm']:
            stratum = 'primary/A_alert'
        else:
            b3 = 'B3_alert' if first['checks']['B3']['alarm'] else 'B3_no_alert'
            stratum = 'primary/A_no_alert/' + b3 + '/' + first['contract_id']
        strata[stratum].append(dict(identity_sha256=identity, stratum=stratum, row=first,
                                   alias_evaluations=sorted(r['evaluation_id'] for r in aliases)))

    quota = {}
    remaining = no_alert_budget
    no_alert = [key for key in sorted(strata) if key.startswith('primary/A_no_alert/')]
    while remaining and any(quota.get(key, 0) < len(strata[key]) for key in no_alert):
        for key in no_alert:
            if remaining and quota.get(key, 0) < len(strata[key]):
                quota[key] = quota.get(key, 0) + 1
                remaining -= 1

    groups = []
    frame = []
    for stratum, cases in sorted(strata.items()):
        if stratum == 'primary/A_alert':
            count, reason = len(cases), 'all_unique_A_alerts'
        elif stratum.startswith('diagnostic/'):
            count, reason = 1, 'one_reader_per_diagnostic_family'
        else:
            count, reason = quota.get(stratum, 0), 'stratified_uniform_A_no_alert'
        rng = random.Random(int(digest([seed, stratum]), 16))
        chosen = {r['identity_sha256'] for r in rng.sample(cases, count)}
        groups.append(dict(stratum=stratum, unique_comparisons=len(cases), selected=count,
                           probability_numerator=count, probability_denominator=len(cases)))
        frame.extend(dict(**case, selected=case['identity_sha256'] in chosen,
                          selection_reason=reason, inclusion_probability=count / len(cases))
                     for case in cases)
    return frame, groups


def freeze_sample():
    audit_path = OUT / 'audit_run_01.json'
    audit = read(audit_path)
    frame, groups = select(audit['rows'])
    source = dict(seed=SEED, no_alert_budget=NO_ALERT_BUDGET, audit_sha256=sha(audit_path),
                  selection_code_sha256=sha(__file__), identity_fields=IDENTITY,
                  scheduled=len(audit['rows']), unique=len(frame), strata=groups)
    sample = dict(**source, frame=frame, schema='ifv-development-sample/1')
    sample['sample_id'] = digest(sample)
    save_new(SAMPLE, sample)
    selected = [c for c in frame if c['selected']]
    summary = dict(**source, sample_id=sample['sample_id'], sample_file_sha256=sha(SAMPLE),
                   selected=len(selected), selected_primary=sum(c['row']['stratum'] == 'primary' for c in selected),
                   physical_ids_selected=len({c['row']['physical_id_sha256'] for c in selected}),
                   confirmatory=False, independent_labels_available=0, model_calls=0)
    save_new(RECOVERY / 'ifv_sampling_summary.json', summary)
    return summary
