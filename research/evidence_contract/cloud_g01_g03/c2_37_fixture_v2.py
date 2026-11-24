"""Synthetic-only C2 accounting v2. Not an authorization or production adapter."""
import hashlib
import json
from collections import Counter
from ..oracle_reliability import reporting

STATES = ('FAULT', 'NO_FAULT', 'UNKNOWN', 'INVALID_TEST')
BINARY = set(STATES[:2])
CONDITIONS = ('backup_supported_after', 'backup_supported_before', 'distinct_sources',
              'primary_removed_after', 'primary_supported_before', 'provenance_verified',
              'reference_approved', 'semantic_equality_approved')
ARMS = ('asserted', 'checked')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def exact(obj, keys):
    need(type(obj) is dict and set(obj) == set(keys), 'Unexpected record schema')


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def seal(obj):
    return dict(obj, record_sha256=digest(obj))


def unseal(obj, keys):
    exact(obj, (*keys, 'record_sha256'))
    body = {k: obj[k] for k in keys}
    need(obj['record_sha256'] == digest(body), 'Record digest mismatch')
    return body


def synthetic_reader():
    return dict(name='SYNTH_READER', profile='SYNTH_RECT2', run='SYNTH_RUN_V2',
                checkpoint=digest('SYNTH_WEIGHTS'), config=digest('SYNTH_CONFIG'),
                runtime=digest('SYNTH_RUNTIME'))


def locked_cases():
    """Deterministic fictitious membership; never a copy of the real private queue."""
    rows = []
    pid = extra = 0
    for template, nids, nc in [('05', 7, 12), ('32', 4, 11), ('41', 7, 14)]:
        pool = list(range(pid + 1, pid + nids + 1))
        pid += nids
        for j in range(nc):
            p = pool[j % nids]
            derived = f'SYNTH_AFTER_{p}'
            if j >= nids and extra < 9:
                extra += 1
                derived = f'SYNTH_EXTRA_{extra}'
            k = len(rows) + 1
            ident = k <= 11
            rows.append(dict(case_id=f'SYNTH_C{k}', physical_id=f'SYNTH_ID{p}',
                             template=template, field='SYNTH_IDENTIFIER' if ident else 'SYNTH_DATE',
                             body_precision='LITERAL_IDENTIFIER' if ident else 'DAY_MONTH_FOUR_DIGIT_YEAR',
                             backup_precision='LITERAL_IDENTIFIER' if ident else 'YYMMDD',
                             primary_region=f'SYNTH_BODY_{k}', backup_region=f'SYNTH_MRZ_{k}',
                             transform=derived, before=digest(f'SYNTH_BEFORE_{p}'), after=digest(derived)))
    return rows


def payload(case, status, reader, before, after):
    return digest(dict(case=case, reference=status['reference'], reader=reader,
                       before=before, after=after, endpoint='pointwise', tier=1,
                       policy='SYNTH_D4_ONLY'))


def counts(rows):
    return dict(candidates=len(rows), physical_ids=len({r['physical_id'] for r in rows}))


def bounds(total, denominator, contributions):
    """Same extrema as v3: all subsets of unknown truths may enter denominator."""
    vals = [total / denominator] if denominator else []
    for reverse in (False, True):
        s, n = total, denominator
        for value in sorted(contributions, reverse=reverse):
            s += value
            n += 1
            vals.append(s / n)
    return dict(minimum=min(vals) if vals else None, maximum=max(vals) if vals else None,
                can_be_undefined=denominator == 0)


def metrics(rows):
    """Only called on a complete named synthetic frame. Reuse frozen reporting."""
    f = [r for r in rows if r['truth'] is True]
    n = [r for r in rows if r['truth'] is False]
    u = [r for r in rows if r['truth'] is None]
    arms = {}
    for arm in ARMS:
        base = reporting.summarize([dict(truth=r['truth'], state=r[arm], count=1,
                                         reason='SYNTH_FIXTURE') for r in rows])
        detected = sum(r[arm] == 'FAULT' for r in f)
        alarms = sum(r[arm] == 'FAULT' for r in n)
        unknown = sum(r[arm] == 'UNKNOWN' for r in rows)
        arms[arm] = dict(base=base, abstention=reporting.rate(unknown, len(rows)),
                         invalid=reporting.rate(sum(r[arm] == 'INVALID_TEST' for r in rows), len(rows)),
                         missed_faults={s: sum(r[arm] == s for r in f) for s in STATES[1:]},
                         sensitivity_bounds=bounds(detected, len(f), [int(r[arm] == 'FAULT') for r in u]),
                         far_bounds=bounds(alarms, len(n), [int(r[arm] == 'FAULT') for r in u]))
    def delta(r):
        return int(r['asserted'] == 'FAULT') - int(r['checked'] == 'FAULT')
    def withdrawn(rs):
        return sum(r['asserted'] == 'FAULT' and r['checked'] == 'UNKNOWN' for r in rs)
    return dict(**counts(rows), known_faults=len(f), known_nonfaults=len(n), missing_truth=len(u),
                truth_availability=reporting.rate(len(f)+len(n), len(rows)), arms=arms,
                states=STATES, matrix=[[sum(r['asserted'] == a and r['checked'] == c for r in rows)
                                        for c in STATES] for a in STATES],
                far_difference=reporting.rate(sum(map(delta, n)), len(n)),
                far_difference_bounds=bounds(sum(map(delta, n)), len(n), list(map(delta, u))),
                withdrawals=dict(all=withdrawn(rows), false_alarms=withdrawn(n),
                                 true_detections=withdrawn(f), unknown_truth=withdrawn(u)))


def analyze(data):
    exact(data, ('schema', 'scope', 'membership', 'reader', 'statuses', 'outputs', 'decisions', 'truth'))
    need(data['schema'] == 'C2-37-fixture/2' and data['scope'] == 'SYNTHETIC_ONLY', 'Production forbidden')
    cases, reader = locked_cases(), synthetic_reader()
    need(data['membership'] == cases and data['reader'] == reader, 'Locked synthetic membership or reader mismatch')
    by_id = {c['case_id']: c for c in cases}
    images = {c[k] for c in cases for k in ('before', 'after')}
    need(len(images) == 45, 'Synthetic fixture image cardinality')
    for k in ('statuses', 'outputs', 'decisions', 'truth'):
        need(type(data[k]) is list, 'Expected list')
    statuses, outputs, decisions, truths = {}, {}, {}, {}
    for item in data['statuses']:
        s = unseal(item, ('case_id', 'rights', 'proposals', 'adjudicated', 'reference', 'conditions', 'exposure'))
        k = s['case_id']
        need(k in by_id and k not in statuses, 'Status membership/duplicate')
        need(s['rights'] in ('PENDING', 'DENIED', 'PERMITTED') and type(s['proposals']) is int
             and 0 <= s['proposals'] <= 2 and type(s['adjudicated']) is bool, 'Invalid synthetic status')
        need(s['exposure'] in ('UNKNOWN', 'SYNTH_EXPOSED', 'SYNTH_UNEXPOSED'), 'Invalid exposure')
        exact(s['conditions'], CONDITIONS)
        need(all(v in ('PASS', 'FAIL', 'UNKNOWN') for v in s['conditions'].values()), 'Invalid condition')
        ref = s['reference']
        need(ref is None or ref == digest(['SYNTH_REFERENCE', k]), 'Wrong synthetic reference binding')
        need(not s['proposals'] or s['rights'] == 'PERMITTED', 'Proposals without rights')
        need(not s['adjudicated'] or s['proposals'] == 2, 'Adjudication without proposals')
        need((ref is not None) == (s['conditions']['reference_approved'] == 'PASS')
             and (ref is None or s['adjudicated']), 'Reference status mismatch')
        statuses[k] = s
    need(set(statuses) == set(by_id), 'Incomplete status panel')
    for item in data['outputs']:
        o = unseal(item, ('image', 'reader', 'content'))
        need(o['image'] in images and o['image'] not in outputs, 'Output membership/duplicate')
        need(o['reader'] == reader and type(o['content']) is str and o['content'].startswith('SYNTH_'), 'Output binding mismatch')
        outputs[o['image']] = item['record_sha256']
    def can_pair(c):
        s = statuses[c['case_id']]
        return (s['rights'] == 'PERMITTED' and s['conditions']['provenance_verified'] == 'PASS'
                and c['before'] in outputs and c['after'] in outputs)
    for item in data['decisions']:
        d = unseal(item, ('case_id', 'shared_payload', 'asserted', 'checked'))
        k = d['case_id']
        need(k in by_id and k not in decisions, 'Decision membership/duplicate')
        c, s = by_id[k], statuses[k]
        need(can_pair(c), 'Decision without rights, verified provenance or paired outputs')
        need(d['shared_payload'] == payload(c, s, reader, outputs[c['before']], outputs[c['after']]), 'Wrong shared payload')
        a, z = d['asserted'], d['checked']
        need(a in STATES and z in STATES and (a == z or a in BINARY and z == 'UNKNOWN'), 'Invalid D4 transition')
        need(s['reference'] is not None or not ({a, z} & BINARY), 'Binary without reference')
        decisions[k] = d
    for item in data['truth']:
        t = unseal(item, ('case_id', 'field', 'after_record', 'basis', 'value', 'evidence'))
        k = t['case_id']
        need(k in decisions and k not in truths, 'Truth membership/duplicate')
        c = by_id[k]
        need(t['field'] == c['field'] and t['after_record'] == outputs[c['after']], 'Truth field/output mismatch')
        need(type(t['value']) is bool and t['basis'] == 'SYNTH_INDEPENDENT' and
             t['evidence'] == digest(['SYNTH_TRUTH', k, c['field'], t['after_record']]), 'Truth basis/binding mismatch')
        truths[k] = t['value']
    def qualification(c):
        s = statuses[c['case_id']]; cond = s['conditions']
        if s['rights'] == 'DENIED' or any(cond[k] == 'FAIL' for k in CONDITIONS if k != 'reference_approved'):
            return 'NOT_QUALIFIED'
        if s['rights'] == 'PERMITTED' and all(v == 'PASS' for v in cond.values()):
            return 'QUALIFIED'
        return 'PENDING'
    q = {c['case_id']: qualification(c) for c in cases}
    def paired(c):
        return c['before'] in outputs and c['after'] in outputs
    def flow(cs):
        tests = dict(enrolled=lambda c: True, rights_permitted=lambda c: statuses[c['case_id']]['rights']=='PERMITTED',
                     two_proposals=lambda c: statuses[c['case_id']]['proposals']==2,
                     adjudicated=lambda c: statuses[c['case_id']]['adjudicated'],
                     reference_approved=lambda c: statuses[c['case_id']]['reference'] is not None,
                     qualified=lambda c: q[c['case_id']]=='QUALIFIED', pending=lambda c: q[c['case_id']]=='PENDING',
                     not_qualified=lambda c: q[c['case_id']]=='NOT_QUALIFIED', cached_pair=paired,
                     authorized_pair=can_pair, paired_decision=lambda c: c['case_id'] in decisions,
                     known_truth=lambda c: c['case_id'] in truths,
                     missing_truth_in_decision=lambda c: c['case_id'] in decisions and c['case_id'] not in truths,
                     missing_output=lambda c: not paired(c), missing_decision_given_authorized_pair=lambda c: can_pair(c) and c['case_id'] not in decisions,
                     rights_pending=lambda c: statuses[c['case_id']]['rights']=='PENDING', rights_denied=lambda c: statuses[c['case_id']]['rights']=='DENIED',
                     provenance_unverified=lambda c: statuses[c['case_id']]['conditions']['provenance_verified']!='PASS')
        return {k: counts([c for c in cs if test(c)]) for k,test in tests.items()}
    def frame(cs, pending=False):
        rs = [dict(c, asserted=decisions[c['case_id']]['asserted'], checked=decisions[c['case_id']]['checked'],
                   truth=truths.get(c['case_id'])) for c in cs if c['case_id'] in decisions]
        status = ('QUALIFICATION_PENDING' if pending else 'EMPTY_FRAME' if not cs else
                  'COMPLETE_SYNTHETIC_FRAME' if len(rs)==len(cs) else 'INCOMPLETE_FRAME')
        result = dict(status=status, expected=counts(cs), available=counts(rs),
                      fraction_of_enrolled=reporting.rate(len(rs), 37), metrics=None)
        if status == 'COMPLETE_SYNTHETIC_FRAME':
            result['metrics'] = metrics(rs)
        return result
    selected = [c for c in cases if q[c['case_id']]=='QUALIFIED']
    return dict(scope='SYNTHETIC_ONLY', scientific_gate='GO_PREPARATORY_ONLY', superiority='NOT_EVALUATED',
                fixture_membership_sha256=digest(cases), flow=flow(cases), unique_cached_images=len(outputs),
                conditions={k:{v:counts([c for c in cases if statuses[c['case_id']]['conditions'][k]==v])
                               for v in ('PASS','FAIL','UNKNOWN')} for k in CONDITIONS},
                exposure={v:counts([c for c in cases if statuses[c['case_id']]['exposure']==v])
                          for v in ('UNKNOWN','SYNTH_EXPOSED','SYNTH_UNEXPOSED')},
                by_template={k:flow([c for c in cases if c['template']==k]) for k in ('05','32','41')},
                by_field={k:flow([c for c in cases if c['field']==k]) for k in ('SYNTH_IDENTIFIER','SYNTH_DATE')},
                by_synthetic_id={k:flow([c for c in cases if c['physical_id']==k]) for k in sorted({c['physical_id'] for c in cases})},
                enrolled_frame=frame(cases), qualified_frame_proposal=frame(selected, pending='PENDING' in q.values()))
