"""Potential backup pairs from provider metadata, not approved C2 test cases."""
from collections import Counter
from itertools import combinations

from ..reviewer_tools.strict import digest
from .corpus_audit import provider_templates
from .semantic_registry import field_for_alias, normalize
from .policy import td3_value


def eligibility(candidate):
    checks = ('primary_supported_before', 'primary_removed_after', 'backup_supported_before',
              'backup_supported_after', 'semantic_equality_approved', 'provenance_verified', 'reference_approved')
    reasons = [key for key in checks if candidate.get(key) is not True]
    if any(not isinstance(candidate.get(key), str) or not candidate[key].strip()
           for key in ('primary_source_id','backup_source_id')):
        reasons.append('missing_source_identity')
    if candidate.get('primary_source_id') == candidate.get('backup_source_id'):
        reasons.append('sources_not_distinct')
    return dict(eligible=not reasons, reasons=reasons)


def build(root, lineage):
    templates, artifact_sha = provider_templates(root)
    exposure = {r['physical_instance']: r['historical_exposure'] for r in lineage}
    candidates = []
    for pid, item in sorted(templates.items()):
        fields = []; mrz = {}
        for index, region in enumerate(item['regions']):
            attrs = region['region_attributes']; key = attrs['field_name']; value = attrs.get('value')
            if key in ('mrz_line0', 'mrz_line1'):
                if key in mrz: mrz[key] = None
                else: mrz[key] = value
            semantic = field_for_alias(key)
            if semantic and isinstance(value, str):
                fields.append((f'region_{index}', semantic, value))
        pairs = []
        for first, second in combinations(fields, 2):
            if first[1] == second[1]:
                left, right = normalize(first[2], first[1]), normalize(second[2], second[1])
                status = 'LITERAL_EQUAL_NOT_APPROVED' if left is not None and left == right else 'LITERAL_DIFFERENT_OR_UNSUPPORTED'
                pairs.append((first[0], second[0], first[1], status, 'body_duplicate'))
        for source_id, field, value in fields:
            if field not in ('id_number', 'dob', 'expiry_date') or set(mrz) != {'mrz_line0', 'mrz_line1'}:
                continue
            kind = 'identifier' if field == 'id_number' else 'date_yymmdd'
            parsed, reason = td3_value(dict(line1=mrz['mrz_line0'], line2=mrz['mrz_line1']), field, kind)
            body = normalize(value, field)
            status = reason if parsed is None else 'LITERAL_EQUAL_NOT_APPROVED' if body == parsed else 'LITERAL_OR_PRECISION_DIFFERENCE'
            pairs.append((source_id, 'mrz_line0+mrz_line1', field, status, 'body_mrz'))
        for primary, backup, field, status, kind in pairs:
            row = dict(physical_instance=pid, field=field, primary_source_id=primary, backup_source_id=backup,
                candidate_kind=kind, before_support='PROVIDER_TEMPLATE_ONLY', after_support='UNKNOWN_NO_BOUND_MUTATION',
                mechanical_comparison=status, primary_supported_before=None, primary_removed_after=None,
                backup_supported_before=None, backup_supported_after=None, semantic_equality_approved=False,
                provenance_verified=False, reference_approved=False, provenance_status='HEADER_HASHED_NOT_IMAGE_PAIR_VALIDATED',
                reference_approval_status='PENDING_HUMAN', source_artifact_sha256=artifact_sha,
                exposure_state=exposure.get(pid, 'EXPOSURE_UNKNOWN'))
            row['candidate_id'] = digest(row); row.update(eligibility(row)); candidates.append(row)
    summary = dict(schema='c2-inventory-feasibility/1', provider_instances_scanned=len(templates),
        candidate_pairs=len(candidates), candidate_instances=len({c['physical_instance'] for c in candidates}),
        eligible_pairs=sum(c['eligible'] for c in candidates), approved_references=0,
        by_field=dict(Counter(c['field'] for c in candidates)), by_kind=dict(Counter(c['candidate_kind'] for c in candidates)),
        mechanical_status=dict(Counter(c['mechanical_comparison'] for c in candidates)),
        reason_counts=dict(Counter(r for c in candidates for r in c['reasons'])),
        scope='Potential source pairs in cached provider template metadata; no before/after mutation or semantic approval',
        candidate_inventory_digest=digest(candidates), new_model_calls=0, cohort_selected=False)
    return candidates, summary
