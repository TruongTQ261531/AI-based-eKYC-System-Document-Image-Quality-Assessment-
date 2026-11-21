"""Evaluate the frozen provider inventory against local, hash-bound evidence."""
from collections import Counter

from . import c2_inventory, reference_registry
from .pixel_lineage_audit import safe_path
from ..reviewer_tools.strict import digest

CONDITIONS = ('primary_supported_before','primary_removed_after','backup_supported_before',
              'backup_supported_after','semantic_equality_approved','provenance_verified','reference_approved')
UNKNOWN, PASS, FAIL = 'UNKNOWN','PASS','FAIL'


def classify(primary, backup, conditions):
    if set(conditions)!=set(CONDITIONS) or not set(conditions.values()) <= {UNKNOWN,PASS,FAIL}:
        raise ValueError('Expected seven explicit tri-state findings')
    distinct = UNKNOWN
    if all(isinstance(i,str) and i.strip() for i in (primary,backup)):
        distinct = PASS if primary.strip()!=backup.strip() else FAIL
    states=dict(conditions,distinct_sources=distinct)
    return states, all(v==PASS for v in states.values())


def assess(candidate, ids_with_image, ids_with_parent):
    """This inventory supplies template regions but no authorized paired region observations."""
    states=dict.fromkeys(CONDITIONS,UNKNOWN)
    # In this snapshot production authority is demonstrably empty. This condition
    # asks about current approval, not whether the reference content is true.
    states['reference_approved']=FAIL
    conditions, eligible=classify(candidate['primary_source_id'],candidate['backup_source_id'],states)
    pid=candidate['physical_instance']
    priority=('image_and_parent_link' if pid in ids_with_parent else
              'image_bound' if pid in ids_with_image else 'provider_only')
    reasons=['no_bound_primary_before_observation','no_bound_primary_removal',
             'no_bound_backup_before_observation','no_bound_backup_after_observation',
             'semantic_equivalence_pending','source_pair_provenance_unverified','no_production_approval']
    if candidate['mechanical_comparison']!='LITERAL_EQUAL_NOT_APPROVED':
        reasons.append(candidate['mechanical_comparison'])
    return dict(candidate_id=candidate['candidate_id'],conditions=conditions,eligible=eligible,
                followup_group=priority,missing_evidence=reasons)


def audit(root,lineage,pixels,prior):
    safe_path(root/'research/data/midv2020/template_head.bin',root)
    trusted=reference_registry.production_trust()
    if trusted['authorities'] or reference_registry.approved_ids():
        raise ValueError('Trust state changed; re-evaluate reference bindings before auditing')
    rows, replay=c2_inventory.build(root,lineage)
    if replay!=prior or len({c['candidate_id'] for c in rows})!=len(rows):
        raise ValueError('Frozen candidate inventory mismatch')
    ids,parents=set(),set()
    for image in pixels:
        if 'pixel' not in image:
            continue
        for m in image['records']:
            if m.get('physical_id'):
                ids.add(m['physical_id'])
                if any(m.get(k) in image['bound_parent_files'] for k in ('source_sha256','original_sha256')):
                    parents.add(m['physical_id'])
    detail=[assess(row,ids,parents) for row in rows]
    totals={k:{s:sum(d['conditions'][k]==s for d in detail) for s in (PASS,FAIL,UNKNOWN)}
            for k in (*CONDITIONS,'distinct_sources')}
    return dict(candidate_count=len(rows), physical_ids=replay['candidate_instances'],
        candidate_inventory_digest=digest(rows),eligible=sum(d['eligible'] for d in detail),
        by_field=replay['by_field'],by_kind=replay['by_kind'],mechanical=replay['mechanical_status'],
        condition_counts=totals,followup_groups=dict(Counter(d['followup_group'] for d in detail)),
        missing_evidence=dict(Counter(r for d in detail for r in d['missing_evidence'])),
        production_authorities=len(trusted['authorities']),approved_references=0),detail
