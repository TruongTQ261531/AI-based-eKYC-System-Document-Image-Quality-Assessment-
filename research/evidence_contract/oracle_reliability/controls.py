"""Authored logical controls, not images, human annotations or model calls.

Expected decisions specify the proposed policy. Separate truth values express
constructed task truth; a deliberately poisoned reference can pass the schema
and yield a WRONG oracle decision despite matching the policy expectation.
"""
from copy import deepcopy
from dataclasses import replace
import json

from ..normalized_output import NativeOutput, ReaderSpec, normalize
from ..source_graph import digest
from . import policy as p

SPEC = ReaderSpec('oracle_reliability_unit', 'symbolic/1', '1' * 64, '{}', '2' * 64, '{}', 'oracle_unit_injected')
LINE1 = 'P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<'
LINE2 = 'L898902C36UTO7408122F1204159ZE184226B<<<<<10'


def output(text, pixel, *, actual_origin_probe=False):
    result = normalize(SPEC, NativeOutput(text, 0., 0., {'scope': 'unit control; no inference'}),
                       input_file_sha256=digest(['symbolic_file', pixel]), input_pixel_sha256=pixel,
                       cache_key=digest(['unit_cache', text, pixel]), call_id=digest(['unit_call', text, pixel]))
    return replace(result, output_origin='actual_model') if actual_origin_probe else result


def base(name):
    ctx = p.PairContext('C3', 'id_number', digest('unit_before'), digest('unit_after'), digest('unit_mutation'), 'VALID', 'mask')
    source = dict(source_id='main', semantic_key='id_number', kind='body', state='SUPPORTED', value='DEMO1',
                  conditions=dict(semantic_link=True, integrity=True, context_present=True), mrz=None)
    ref = dict(schema=p.SCHEMA, policy=p.POLICY, scope='constructed_control', field_key='id_number',
               value_kind='identifier', provenance='Authored symbolic unit control, not an image or independent gold',
               mutation_sha256=ctx.mutation_sha256, main_source_id='main',
               before=dict(pixel_sha256=ctx.before_pixel_sha256, inventory_complete=True, sources=[deepcopy(source)]),
               after=dict(pixel_sha256=ctx.after_pixel_sha256, inventory_complete=True, sources=[deepcopy(source)]))
    return dict(name=name,context=ctx.__dict__,reference_payload=ref,before_raw='{"id_number":"DEMO1"}',
                after_raw='{"id_number":"WRONG"}',expected=['FAULT','FAULT','NO_FAULT'],
                truth=[True,True,False],actual_origin_probe=False,tamper_after_seal=False)


def make_controls():
    cases = []
    def add(name, expected=('UNKNOWN','UNKNOWN','NO_FAULT'), truth=(None,None,False)):
        case=base(name);case['expected']=list(expected);case['truth']=list(truth);cases.append(case);return case
    for original in ('correct','wrong','empty'):
        for followup in ('correct','wrong','empty'):
            point='NO_FAULT' if followup=='correct' else 'FAULT'
            relation=point if original=='correct' else 'UNKNOWN'
            case=add('C3_'+original+'_to_'+followup,(point,relation,'NO_FAULT'),
                     (followup!='correct',followup!='correct' if original=='correct' else None,False))
            for side,mode in [('before',original),('after',followup)]:
                case[side+'_raw']=json.dumps({'id_number':{'correct':'DEMO1','wrong':'WRONG','empty':''}[mode]})
    case=add('C4_unsupported_operator',('FAULT','UNKNOWN','NO_FAULT'),(True,None,False))
    case['context'].update(contract='C4',operator='rotate_unverified')
    case=add('C4_identity',('FAULT','FAULT','NO_FAULT'),(True,True,False));case['context'].update(contract='C4',operator='identity')
    for mode in ('empty','emitted'):
        state='NO_FAULT' if mode=='empty' else 'FAULT'
        case=add('C1_complete_'+mode,(state,state,'NO_FAULT'),(mode!='empty',mode!='empty',False))
        case['context']['contract']='C1';case['reference_payload']['after']['sources'][0]['state']='REMOVED'
        case['after_raw']=json.dumps({'id_number':'' if mode=='empty' else 'DEMO1'})
    case=add('C1_partial_inventory');case['context']['contract']='C1'
    case['reference_payload']['after'].update(inventory_complete=False)
    case['reference_payload']['after']['sources'][0]['state']='REMOVED'
    case=add('C1_missing_source_record');case['context']['contract']='C1';case['reference_payload']['after']['sources']=[]
    case=add('partial_but_supported',('FAULT','FAULT','NO_FAULT'),(True,True,False));case['reference_payload']['after']['inventory_complete']=False
    case=add('C2_main_not_removed',('FAULT','UNKNOWN','NO_FAULT'),(True,None,False));case['context']['contract']='C2'
    case=add('C2_verified_duplicate_backup',('FAULT','FAULT','NO_FAULT'),(True,True,False));case['context']['contract']='C2'
    for side in ('before','after'):
        sources=case['reference_payload'][side]['sources'];sources.append(dict(deepcopy(sources[0]),source_id='backup',kind='duplicated_body'))
    case['reference_payload']['after']['sources'][0]['state']='REMOVED'
    case=add('C2_new_source_not_surviving_backup',('FAULT','UNKNOWN','NO_FAULT'),(True,None,False));case['context']['contract']='C2'
    case['reference_payload']['after']['sources'].append(dict(deepcopy(case['reference_payload']['after']['sources'][0]),source_id='new'))
    case['reference_payload']['after']['sources'][0]['state']='REMOVED'
    for kind in ('conflict','unresolved'):
        case=add('source_'+kind);source=deepcopy(case['reference_payload']['after']['sources'][0]);source['source_id']='other'
        source.update(value='CONFLICT',state='SUPPORTED' if kind=='conflict' else 'UNKNOWN')
        case['reference_payload']['after']['sources'].append(source)
    for flag in ('semantic_link','integrity','context_present'):
        for value in (False,None):
            case=add(flag+'_'+str(value));case['reference_payload']['after']['sources'][0]['conditions'][flag]=value
    for corruption in ('pixel','field','mutation','source_semantic','duplicate','boolean_string','schema','hash','unhashable_kind','null_source'):
        case=add('bad_'+corruption);ref=case['reference_payload']
        if corruption=='pixel':ref['after']['pixel_sha256']='f'*64
        if corruption=='field':ref['field_key']='school'
        if corruption=='mutation':ref['mutation_sha256']='f'*64
        if corruption=='source_semantic':ref['after']['sources'][0]['semantic_key']='school'
        if corruption=='duplicate':ref['after']['sources']*=2
        if corruption=='boolean_string':ref['after']['inventory_complete']='true'
        if corruption=='schema':ref['schema']='bound-field-reference/1'
        if corruption=='hash':case['tamper_after_seal']=True
        if corruption=='unhashable_kind':ref['value_kind']=[]
        if corruption=='null_source':ref['after']['sources']=[None]
    case=add('reference_unapproved');case['reference_payload']['scope']='external_reference'
    case=add('constructed_reference_actual_origin_probe');case['actual_origin_probe']=True
    for validity in ('INVALID_TEST','INCONCLUSIVE'):
        state='INVALID_TEST' if validity=='INVALID_TEST' else 'UNKNOWN'
        case=add('validity_'+validity,(state,state,'NO_FAULT'));case['context']['validity']=validity
    case=add('malformed_followup',('UNKNOWN','UNKNOWN','STRUCTURAL_ERROR'),(None,None,True));case['after_raw']='{"id_number":'
    case=add('malformed_original',('FAULT','UNKNOWN','NO_FAULT'),(True,None,False));case['before_raw']='{"id_number":'
    for key,kind,value in [('id_number','identifier','L898902C3'),('dob','date_yymmdd','740812'),('expiry_date','date_yymmdd','120415')]:
        case=add('TD3_'+key,('FAULT','FAULT','NO_FAULT'),(True,True,False))
        case['context'].update(contract='C2',key=key);ref=case['reference_payload'];ref.update(field_key=key,value_kind=kind)
        for side in ('before','after'):
            source=ref[side]['sources'][0];source.update(semantic_key=key,value=value)
            ref[side]['sources'].append(dict(deepcopy(source),source_id='backup',kind='mrz',mrz=dict(line1=LINE1,line2=LINE2)))
        ref['after']['sources'][0]['state']='REMOVED';case['before_raw']=json.dumps({key:value});case['after_raw']=json.dumps({key:'WRONG'})
    for variant in ('bad_checksum','missing_literal','wrong_value','no_field_checksum','wrong_precision','invalid_date'):
        case=deepcopy(next(c for c in cases if c['name']=='TD3_id_number'));case['name']='TD3_'+variant
        case.update(expected=['UNKNOWN','UNKNOWN','NO_FAULT'],truth=[None,None,False]);cases.append(case)
        source=case['reference_payload']['after']['sources'][1]
        if variant=='bad_checksum':source['mrz']['line2']=LINE2[:9]+'7'+LINE2[10:]
        if variant=='missing_literal':source['mrz']=None
        if variant=='wrong_value':source['value']='DEMO1'
        if variant in ('no_field_checksum','wrong_precision'):
            key='full_name' if variant=='no_field_checksum' else 'dob'
            kind='text' if variant=='no_field_checksum' else 'date_full'
            value='ANNA MARIA ERIKSSON' if variant=='no_field_checksum' else '1974-08-12'
            case['context']['key']=key;case['reference_payload'].update(field_key=key,value_kind=kind)
            for side in ('before','after'):
                for src in case['reference_payload'][side]['sources']:src.update(semantic_key=key,value=value)
        if variant=='invalid_date':source['mrz']['line2']=LINE2[:13]+'740230'+LINE2[19:]
    for value in ('2023-02-29','000229'):
        case=add('invalid_or_ambiguous_date_'+value);case['reference_payload']['value_kind']='date_full' if '-' in value else 'date_yymmdd'
        for side in ('before','after'):case['reference_payload'][side]['sources'][0]['value']=value
    case=add('typed_O_vs_zero',('FAULT','FAULT','NO_FAULT'),(True,True,False));case['after_raw']='{"id_number":"DEM01"}'
    case=add('shared_wrong_reference',('FAULT','UNKNOWN','NO_FAULT'),(False,None,False))
    case['after_raw']=case['before_raw']
    for side in ('before','after'):case['reference_payload'][side]['sources'][0]['value']='POISON'
    case=add('corroborated_body',('FAULT','FAULT','NO_FAULT'),(True,True,False))
    for side in ('before','after'):
        source=case['reference_payload'][side]['sources'][0];case['reference_payload'][side]['sources'].append(dict(deepcopy(source),source_id='copy',kind='duplicated_body'))
    poisoned=deepcopy(case);poisoned['name']='corroborated_shared_wrong_reference'
    poisoned.update(expected=['FAULT','UNKNOWN','NO_FAULT'],truth=[False,None,False])
    poisoned['after_raw']=poisoned['before_raw']
    for side in ('before','after'):
        for source in poisoned['reference_payload'][side]['sources']:source['value']='POISON'
    cases.append(poisoned)
    return cases


def inputs(case):
    context=p.PairContext(**case['context']);ref=p.seal_reference(deepcopy(case['reference_payload']))
    if case['tamper_after_seal']:ref['after']['sources'][0]['value']='TAMPERED'
    before=output(case['before_raw'],context.before_pixel_sha256,actual_origin_probe=case['actual_origin_probe'])
    after=output(case['after_raw'],context.after_pixel_sha256,actual_origin_probe=case['actual_origin_probe'])
    return ref,context,before,after
