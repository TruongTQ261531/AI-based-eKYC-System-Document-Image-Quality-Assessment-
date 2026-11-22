
import pytest

from research.evidence_contract.human_gate import closure, prepare, review
from research.evidence_contract.reviewer_tools.strict import digest


def example():
    before,after=digest('before'),digest('after')
    item=dict(candidate_id=digest('candidate'),allowed_evidence_sha256=[before,after],
              evidence_by_side=dict(before=[before],after=[after]))
    form=dict(schema='c2-source-review/1',role='reviewer',assessor='R02',
              candidate_id=item['candidate_id'],item_sha256=digest(item),exposure='PREVIOUSLY_SEEN',
              observations=dict.fromkeys(review.QUESTIONS,'UNKNOWN'),semantic_judgment='UNKNOWN',
              precision_judgment='UNKNOWN',basis_sha256=[before,after],rationale='Source unclear in both views.')
    return item,form


def test_complete_unknown_observation_is_not_approval():
    item,form=example()
    result=review.validate(form,item,'R02')
    assert not result['signature_verified'] and not result['approved_reference']
    assert result['exposure']=='PREVIOUSLY_SEEN'
    with pytest.raises(ValueError,match='authority pending'):
        review.registry_receipt(form,item,'R02',[],[])


@pytest.mark.parametrize('mutation',['assessor','candidate','item','exposure','role','missing_answer','invalid_answer',
    'precision','semantic','one_side','foreign_evidence','duplicate','rationale','auto_approve','majority'])
def test_invalid_or_unbound_human_form(mutation):
    item,form=example()
    if mutation=='assessor': form['assessor']='R03'
    if mutation=='candidate': form['candidate_id']='0'*64
    if mutation=='item': item['new_version']=2
    if mutation=='exposure': form['exposure']=''
    if mutation=='role': form['role']='reference_approver'
    if mutation=='missing_answer': del form['observations'][review.QUESTIONS[0]]
    if mutation=='invalid_answer': form['observations'][review.QUESTIONS[1]]=True
    if mutation=='precision': form['precision_judgment']='INFER_CENTURY'
    if mutation=='semantic': form['semantic_judgment']='CHECKSUM_PASSED'
    if mutation=='one_side': form['basis_sha256'].pop()
    if mutation=='foreign_evidence': form['basis_sha256'][0]='0'*64
    if mutation=='duplicate': form['basis_sha256']*=2
    if mutation=='rationale': form['rationale']='  '
    if mutation=='auto_approve': form['reference_approved']=True
    if mutation=='majority': form['majority_vote']='PASS'
    with pytest.raises(ValueError):
        review.validate(form,item,'R02')


def test_precision_keeps_two_digit_year_and_unrecognized_pattern():
    assert prepare.precision('dob','01 JAN 75')=='DAY_MONTH_NAME_TWO_DIGIT_YEAR'
    assert prepare.precision('dob','01.01.1975.')=='DAY_MONTH_FOUR_DIGIT_YEAR'
    assert prepare.precision('expiry_date','?')=='UNRESOLVED_NATIVE_DATE_FORMAT'
    assert prepare.precision('id_number','O01')=='LITERAL_IDENTIFIER'


def test_signed_closure_cannot_change_cutoff_or_skip_signature(monkeypatch):
    draft=dict(round_id='round',view_sha256=['v'],cutoff_basis='frozen',schema='review-round-closure/1',
               mode='PRODUCTION',authority_role='round_owner',authority_id=None,timestamp=None)
    monkeypatch.setattr(closure,'frozen',lambda:(draft,{}))
    payload=dict(draft,authority_id='absent',timestamp='2026-11-22T12:00:00Z')
    with pytest.raises(ValueError,match='cutoff'):
        closure.signed_packet(dict(payload=dict(payload,cutoff_basis='changed'),signature_hex='00'))
    with pytest.raises(ValueError,match='designated'):
        closure.signed_packet(dict(payload=payload,signature_hex='00'))


def test_overlap_counted_once_per_physical_document():
    rows=[dict(physical_instance='same',candidate_id=str(i),conditions=dict(semantic_equality_approved='UNKNOWN',
          reference_approved='FAIL',provenance_verified='PASS')) for i in range(3)]
    result=prepare.cluster_metrics(rows,{'0','1'})
    assert result['scope']==dict(candidates=3,physical_ids=1)
    assert result['waiting_both_prepared']==dict(candidates=2,physical_ids=1)
    assert result['eligible']==dict(candidates=0,physical_ids=0)
