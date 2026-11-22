import numpy as np
import pytest

from research.evidence_contract.adjudication import synthetic_dry_run as fixture
from research.evidence_contract.oracle_reliability import post_p6_geometry as geom
from research.evidence_contract.oracle_reliability import reference_registry as registry
from research.evidence_contract.oracle_reliability import semantic_registry, policy
from research.evidence_contract.oracle_reliability.c2_evidence_audit import CONDITIONS, classify
from research.evidence_contract.reviewer_tools.strict import digest


@pytest.mark.parametrize('change',['missing_before','missing_after','different_parent','different_instance'])
def test_exact_image_lineage_required(change):
    b = dict(physical_id='unit',file='a'*64)
    a = dict(physical_id='unit',source_sha256='a'*64,input_sha256='b'*64)
    assert geom.same_lineage(b,a)
    if change=='missing_before':
        b=None
    if change=='missing_after':
        a=None
    if change=='different_parent':
        a['source_sha256']='c'*64
    if change=='different_instance':
        a['physical_id']='other'
    assert not geom.same_lineage(b,a)


def test_crop_origin_and_pixel_mutation_must_match():
    parent=np.arange(120,dtype=np.uint8).reshape(5,8,3)
    child=parent[:,2:].copy()
    row=dict(capture='field_clip',capture_transform=dict(crop_origin=[2,0],blur_glare=False))
    valid=geom.replay_mutation(parent,child,row,None)
    assert valid['origin']==[2,0]
    assert geom.region_impact([[0,0],[1,0],[1,3],[0,3]],valid)==1
    assert geom.region_impact([[3,0],[5,0],[5,3],[3,3]],valid)==0
    child[0,0,0]^=1
    assert geom.replay_mutation(parent,child,row,None) is None
    row['capture_transform']['crop_origin']=[1,0]
    assert geom.replay_mutation(parent,parent[:,2:],row,None) is None


def test_unresolved_alias_and_duplicate_region_do_not_bind():
    c=dict(primary_source_id='region_0',backup_source_id='mrz_line0+mrz_line1',field='id_number')
    regs=[dict(region_attributes=dict(field_name=k)) for k in ('number','mrz_line0','mrz_line1')]
    q=dict.fromkeys(range(3),[[0,0],[1,0],[1,1],[0,1]])
    assert geom.regions(c,dict(regions=regs),q) is None
    regs[0]['region_attributes']['field_name']='id_number'
    assert geom.regions(c,dict(regions=regs),q)
    assert geom.regions(c,dict(regions=regs+[regs[1]]),q) is None
    conditions,eligible=classify('same','same',dict.fromkeys(CONDITIONS,'PASS'))
    assert conditions['distinct_sources']=='FAIL' and not eligible


def test_one_wrong_native_quad_invalidates_common_mapping():
    regs,fields=[],[]
    for i,k in enumerate(('id_number','mrz_line0','mrz_line1','extra')):
        s=dict(name='rect',x=10*i,y=11*i,width=5,height=3)
        regs.append(dict(shape_attributes=s,region_attributes=dict(field_name=k,value='unit')))
        fields.append(dict(author_key=k,value='unit',quad=geom.rectangle(s).tolist()))
    src=dict(fields=fields,template_dimensions=[101,101],gt=[[0,0],[100,0],[100,100],[0,100]])
    assert len(geom.mapped_sources(dict(regions=regs),src))==4
    fields[1]['quad'][1][1]+=2
    assert geom.mapped_sources(dict(regions=regs),src)=={}


def test_td3_format_precision_and_approval_are_separate():
    assert policy.td3_value(dict(line1='ID',line2='000'), 'dob','date_yymmdd')==(None,'mrz_format_unsupported')
    assert semantic_registry.normalize('1974-08-12','dob')!=semantic_registry.normalize(
        '740812','dob',source='mrz_td3',precision='date_yymmdd')
    assert not semantic_registry.proposal('id_number')['human_approved']


@pytest.mark.parametrize('block',['reviewer_signature','adjudicator_signature','missing_rights',
                                   'missing_authority','majority_vote','automatic_approval'])
def test_approval_cannot_be_inferred(block):
    private, public=fixture.test_keys()
    candidate,_=fixture.synthetic_candidate()
    if block=='missing_rights':
        candidate['rights_record_sha256']=None
        candidate['candidate_id']=digest({k:v for k,v in candidate.items() if k!='candidate_id'})
    steps=[('REVIEW_PROPOSED','SYNTHETIC_A'),('REVIEW_PROPOSED','SYNTHETIC_B'),
           ('ADJUDICATED_ACCEPT','SYNTHETIC_ADJ'),('OWNER_APPROVED','SYNTHETIC_OWNER')]
    if block=='majority_vote':
        del steps[2]
    if block=='automatic_approval':
        steps=steps[-1:]
    events=[]
    for action,actor in steps:
        events.append(fixture.event(candidate,action,actor,events,private))
    if block in ('reviewer_signature','adjudicator_signature'):
        events[0 if block=='reviewer_signature' else 2]['signature_hex']='00'*64
    if block=='missing_authority':
        public={}
    with pytest.raises(ValueError):
        registry.replay([candidate],events,keys=public,mode='SYNTHETIC')
