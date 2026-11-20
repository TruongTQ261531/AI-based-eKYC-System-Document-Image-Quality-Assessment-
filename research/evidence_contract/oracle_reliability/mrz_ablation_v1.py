"""D4 narrow equal-information comparator; no changes to the frozen v2 policy.

Both engines execute the SAME frozen evaluate code object/admission boundary.
An isolated resolver adapter replaces exactly one TD3 call's argument, allowing
the asserted arm to consume the already-declared typed source value. The rest
of the resolver AST is identical. No module global is patched. Unsupported
field/precision profiles stay rejected in both arms; only literal validation is
ablated. This construction is pinned to the audited policy source hash.
"""
import ast
from copy import deepcopy
from dataclasses import asdict
import hashlib
import inspect
from pathlib import Path
from time import perf_counter_ns
from types import FunctionType

from . import policy,reference_registry
from ..source_graph import digest

VERSION='checked-v2-vs-mrz-metadata-asserted/1'
FROZEN_POLICY_SHA256='c30218c6e0727ac9a56efa4addd7390f2a68527af29d2ae60c0524a7b5518a26'


def verify_frozen_source():
    if hashlib.sha256(Path(policy.__file__).read_bytes()).hexdigest()!=FROZEN_POLICY_SHA256:
        raise ValueError('Frozen v2 changed; review and version the adapter before use')


verify_frozen_source()
_profile_tree=ast.parse(inspect.getsource(policy.td3_value))
_profiles=[n for n in ast.walk(_profile_tree) if isinstance(n,ast.Assign) and
           any(isinstance(t,ast.Name) and t.id=='profiles' for t in n.targets)]
if len(_profiles)!=1:raise ValueError('Frozen MRZ profile extraction changed')
PROFILES=ast.literal_eval(_profiles[0].value)
_original=ast.parse(inspect.getsource(policy.resolve));_adapted=deepcopy(_original)
_calls=[n for n in ast.walk(_adapted) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='td3_value']
if len(_calls)!=1 or ast.unparse(_calls[0])!="td3_value(source['mrz'], key, kind)":
    raise ValueError('Resolver adaptation boundary changed')
_calls[0].args[0]=ast.copy_location(ast.Name(id='source',ctx=ast.Load()),_calls[0].args[0])
_code=compile(ast.fix_missing_locations(_adapted),'<D4 isolated source resolver>','exec')


def adapter_proof():
    restored=deepcopy(_adapted)
    calls=[n for n in ast.walk(restored) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='td3_value']
    calls[0].args[0]=ast.parse("source['mrz']",mode='eval').body
    return dict(frozen_policy_sha256=FROZEN_POLICY_SHA256,
        evaluate_code_object_shared=True,changed_resolver_call_sites=1,
        other_resolver_ast_identical=ast.dump(restored,include_attributes=False)==ast.dump(_original,include_attributes=False),
        common_mrz_field_precision_profiles=PROFILES,global_monkeypatch=False)


def _clone(function,**bindings):
    result=FunctionType(function.__code__,dict(function.__globals__,**bindings),function.__name__,function.__defaults__,function.__closure__)
    result.__kwdefaults__=deepcopy(function.__kwdefaults__)
    return result


def _engine(asserted,stats):
    def td3(source_or_literal,key,kind):
        start=perf_counter_ns()
        try:
            if asserted:
                stats['declared_mrz_resolutions']+=1
                if key not in PROFILES or PROFILES[key][2]!=kind:
                    return None,'mrz_field_or_precision_unsupported'
                return policy.canonical(source_or_literal['value'],kind),'metadata_asserted_without_literal_check'
            stats['literal_td3_calls']+=1
            return policy.td3_value(source_or_literal,key,kind)
        finally:stats['mrz_work_ns']+=perf_counter_ns()-start
    if asserted:
        namespace=dict(policy.resolve.__globals__,td3_value=td3)
        exec(_code,namespace)
        resolver=namespace['resolve']
    else:resolver=_clone(policy.resolve,td3_value=td3)
    return _clone(policy.evaluate,resolve=resolver)


def compare_pair(reference,context,before,after,*,minimum_grade=1,production=False,candidates=(),events=()):
    """Production obtains authorization ONLY from the designated signed registry.

    Development never grants any external reference ID, even if requested in the
    input metadata. Constructed controls remain identified by frozen origin rules.
    Truth/expected labels are deliberately absent from this API.
    """
    if type(production) is not bool:raise ValueError('Explicit evidence domain required')
    if not production and (candidates or events):raise ValueError('Development cannot grant approval')
    payload=dict(reference=reference,context=asdict(context),before=asdict(before),after=asdict(after),tier=minimum_grade)
    fingerprint=digest(payload)
    start=perf_counter_ns()
    approved=reference_registry.approved_ids(candidates,events) if production else frozenset()
    authority_ns=perf_counter_ns()-start
    results={};costs={}
    for name,asserted in [('checked_v2',False),('mrz_metadata_asserted',True)]:
        stats=dict(literal_td3_calls=0,declared_mrz_resolutions=0,mrz_work_ns=0)
        engine=_engine(asserted,stats);start=perf_counter_ns()
        results[name]=engine(reference,context,before,after,approved_external_ids=approved,minimum_grade=minimum_grade)
        stats['evaluation_ns']=perf_counter_ns()-start
        costs[name]=stats
    if digest(dict(reference=reference,context=asdict(context),before=asdict(before),after=asdict(after),tier=minimum_grade))!=fingerprint:
        raise ValueError('Comparator mutated its shared input')
    return dict(schema=VERSION,shared_input_sha256=fingerprint,minimum_grade=minimum_grade,
        mode='PRODUCTION_GATE' if production else 'CONSTRUCTED_DEVELOPMENT',arms=results,
        cost=dict(shared_authority_ns=authority_ns,arms=costs,model_calls=0,training_runs=0,
                  human_active_minutes=None,annotation_collections=0),approved_reference_count=len(approved),
        independent_gold=False,scientific_go=False)
