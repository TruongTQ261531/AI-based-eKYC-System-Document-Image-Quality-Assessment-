"""Aggregate frozen D4 payloads and arm outcomes. No reader or policy evaluation."""
from collections import Counter
from ....oracle_reliability.policy import canonical, td3_value


def literal_status(reference, key, called):
    if not called:
        return 'not_called_on_pair'
    if not reference:
        return 'unavailable'
    result = []
    for src in reference['after']['sources']:
        flags = src['conditions']
        if (src['kind'] != 'mrz' or src['state'] != 'SUPPORTED'
                or not all(flags[k] is True for k in ('semantic_link','integrity','context_present'))):
            continue
        kind = reference['value_kind']
        value = canonical(src['value'],kind)
        if value is None:
            continue
        actual, reason = td3_value(src['mrz'],key,kind)
        result.append('literal_value_mismatch' if actual is not None and actual != value else reason)
    return '+'.join(sorted(set(result))) or 'no_eligible_after_literal'


def summarize(rows, history, counterexamples):
    fields = ('tier','field','value_kind','after_sources','after_literal','shared_gate',
              'pointwise_asserted','pointwise_checked','relation_asserted','relation_checked',
              'pointwise_asserted_reason','pointwise_checked_reason','relation_asserted_reason',
              'relation_checked_reason','reference_status')
    strata = Counter()
    totals = Counter()
    for row in rows:
        payload = row['shared_input']
        ref = payload['reference']
        key = payload['context']['key']
        for tier, panel in row['panels'].items():
            checked, asserted = (panel['arms'][name] for name in ('checked_v2','mrz_metadata_asserted'))
            cp, ap, cr, ar = (checked['pointwise'],asserted['pointwise'],checked['relation'],asserted['relation'])
            reason = cp['reason']
            gate = reason if reason in ('mutation_gate','output_binding','reference_rejected','structure_unusable') else 'entered_resolver'
            literal = literal_status(ref,key,panel['cost']['arms']['checked_v2']['literal_td3_calls'])
            source_rows = ref['after']['sources'] if ref else []
            sources = '+'.join(sorted({s['kind'] if isinstance(s,dict) and isinstance(s.get('kind'),str)
                                       else 'malformed_source' for s in source_rows})) or 'unavailable'
            kind = ref['value_kind'] if ref else 'unavailable'
            if not isinstance(kind,str):
                kind='malformed_value_kind'
            reference_status = 'accepted_constructed' if checked['reference_accepted'] else 'unaccepted_or_not_reached'
            strata[(int(tier),key,kind,sources,literal,gate,
                    ap['state'],cp['state'],ar['state'],cr['state'],ap['reason'],cp['reason'],ar['reason'],cr['reason'],
                    reference_status)] += 1
            for name,a,c in [('pointwise',ap,cp),('relation',ar,cr)]:
                if a['state'] in ('FAULT','NO_FAULT') and c['state'] in ('UNKNOWN','INVALID_TEST'):
                    totals[int(tier),name,a['state']] += 1
    table = []
    for values,count in sorted(strata.items()):
        row=dict(zip(fields,values))
        for endpoint in ('pointwise','relation'):
            withdrawn=row[endpoint+'_checked'] in ('UNKNOWN','INVALID_TEST')
            row[endpoint+'_withdrawn_alarms']=count*int(withdrawn and row[endpoint+'_asserted']=='FAULT')
            row[endpoint+'_withdrawn_no_fault']=count*int(withdrawn and row[endpoint+'_asserted']=='NO_FAULT')
        table.append(dict(row,count=count))
    return dict(constructed_controls=len(rows),paired_tier_results=sum(strata.values()),strata=table,
                withdrawals={str(t):{ep:{s:totals[t,ep,s] for s in ('FAULT','NO_FAULT')} for ep in ('pointwise','relation')}
                             for t in (1,2)}, shared_wrong_reference_controls=counterexamples,
                replay={k:history[k] for k in ('cases','parity_pairs','primary_cases','primary_physical_ids',
                       'production_approvals','truth_labels_used','state_counts')},
                independent_truth_cases_available=0,missed_true_faults=None,real_fault_sensitivity=None)
