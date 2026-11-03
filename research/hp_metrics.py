"""Source-aware transcription plus explicit opposing-error diagnostics."""
from research.v3_metrics import scoring as original_scoring,summary as original_summary,canonical
from research.priority_progress import geometry


def scoring(sample,text):
    metrics,fields=original_scoring(sample,text)
    hidden,neighbor=geometry(sample)
    def correct(key):
        return key in fields and any(canonical(key,fields[key])==canonical(key,r['value'],r['kind']) for r in sample['source_refs'][key])
    eligible='pair_hidden_key' in sample
    metrics.update(declared_hidden_outputs=len(hidden&set(fields)),declared_hidden_reference_keys=len(hidden),
        neighbor_reference_keys=len(neighbor),neighbor_correct=sum(correct(k) for k in neighbor),
        neighbor_omissions=len(neighbor-set(fields)),neighbor_wrong=sum(k in fields and not correct(k) for k in neighbor),
        pair_eligible=eligible,pair_hidden_leaked=int(eligible and sample['pair_hidden_key'] in fields),
        pair_kept_correct=int(eligible and correct(sample['pair_kept_key'])),
        pair_success=int(eligible and sample['pair_hidden_key'] not in fields and correct(sample['pair_kept_key'])))
    return metrics,fields


def summary(rows):
    value=original_summary(rows)
    for k in ('declared_hidden_outputs','declared_hidden_reference_keys','neighbor_reference_keys','neighbor_correct',
              'neighbor_omissions','neighbor_wrong','pair_eligible','pair_hidden_leaked','pair_kept_correct','pair_success'):
        value[k]=sum(r[k] for r in rows)
    value['neighbor_recall']=value['neighbor_correct']/max(1,value['neighbor_reference_keys'])
    value['pair_success_rate']=value['pair_success']/max(1,value['pair_eligible'])
    return value
