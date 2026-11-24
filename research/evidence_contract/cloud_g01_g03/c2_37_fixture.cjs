// C2-37 pure fixture analysis. No production mode, no model calls, no private input.
function analyzeFixture(input){
  // Fixture-only development. Never authenticates production rights, bytes or truth.
  const S=["FAULT","NO_FAULT","UNKNOWN","INVALID_TEST"], B=new Set(S.slice(0,2));
  const C=["backup_supported_after","backup_supported_before","distinct_sources","primary_removed_after","primary_supported_before","provenance_verified","reference_approved","semantic_equality_approved"];
  const T={"05":[12,7],"32":[11,4],"41":[14,7]};
  const need=(ok,msg)=>{if(!ok)throw Error(msg)};
  const exact=(x,keys)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const hash=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x), sid=x=>typeof x==="string"&&/^SYNTH_[A-Z0-9_]+$/.test(x);
  const count=(r,p)=>r.filter(p).length, rate=(k,n)=>({k,n,value:n?k/n:null});
  const group=(rs,key)=>{const m=new Map();for(const r of rs){const k=key(r);if(!m.has(k))m.set(k,[]);m.get(k).push(r)}return m};
  need(exact(input,["schema","scope","reader","cases","outputs","decisions"]),"Invalid input schema");
  need(input.schema==="C2-37-fixture/1"&&input.scope==="SYNTHETIC_ONLY","Production input forbidden");
  const spec=input.reader, sk=["name","checkpoint_sha256","config_sha256","runtime_sha256","profile"];
  need(exact(spec,sk)&&sid(spec.name)&&sid(spec.profile)&&sk.slice(1,4).every(k=>hash(spec[k])),"Invalid synthetic reader binding");
  need(Array.isArray(input.cases)&&input.cases.length===37&&Array.isArray(input.outputs)&&Array.isArray(input.decisions),"Require full 37 candidate fixture");
  const cases=new Map(),ids=new Map(),owner=new Map(),before=new Set(),after=new Set();
  const ck=["case_id","physical_id","template","field_kind","before_sha256","after_sha256","rights","two_proposals","adjudicated","reference_sha256","conditions"];
  for(const c of input.cases){
    need(exact(c,ck)&&sid(c.case_id)&&sid(c.physical_id)&&!cases.has(c.case_id),"Invalid or duplicate candidate");
    need(Object.hasOwn(T,c.template)&&["IDENTIFIER","DATE_FULL"].includes(c.field_kind),"Unknown template/field");
    need(hash(c.before_sha256)&&hash(c.after_sha256)&&c.before_sha256!==c.after_sha256,"Invalid image pair");
    need(["rights","two_proposals","adjudicated"].every(k=>typeof c[k]==="boolean"),"Invalid gate value");
    need(c.reference_sha256===null||hash(c.reference_sha256),"Invalid reference digest");
    need(exact(c.conditions,C)&&C.every(k=>["PASS","FAIL","UNKNOWN"].includes(c.conditions[k])),"Invalid conditions");
    need(!c.two_proposals||c.rights,"Proposal before rights");
    need(!c.adjudicated||c.two_proposals,"Adjudication before proposals");
    const approved=c.conditions.reference_approved==="PASS";
    need(approved===Boolean(c.reference_sha256)&&(!approved||c.adjudicated),"Reference approval mismatch");
    const prior=ids.get(c.physical_id);
    need(!prior||(prior.template===c.template&&prior.before===c.before_sha256),"Physical ID inconsistency");
    ids.set(c.physical_id,{template:c.template,before:c.before_sha256});
    for(const v of [c.before_sha256,c.after_sha256]){need(!owner.has(v)||owner.get(v)===c.physical_id,"Image reused across IDs");owner.set(v,c.physical_id)}
    before.add(c.before_sha256);after.add(c.after_sha256);cases.set(c.case_id,c);
  }
  need(ids.size===18&&before.size===18&&after.size===27&&[...before].every(h=>!after.has(h)),"Incorrect physical/image counts");
  for(const [t,[n,ni]] of Object.entries(T)){const rs=input.cases.filter(c=>c.template===t);need(rs.length===n&&new Set(rs.map(c=>c.physical_id)).size===ni,"Template counts changed")}
  need(count(input.cases,c=>c.field_kind==="IDENTIFIER")===11,"Field composition changed");
  const outputs=new Map();
  for(const o of input.outputs){
    need(exact(o,["image_sha256","reader","output_sha256"])&&owner.has(o.image_sha256)&&hash(o.output_sha256),"Invalid or extraneous output");
    need(exact(o.reader,sk)&&sk.every(k=>o.reader[k]===spec[k]),"Reader/checkpoint/config/runtime/profile mismatch");
    need(!outputs.has(o.image_sha256),"Duplicate output");outputs.set(o.image_sha256,o.output_sha256);
  }
  const decisions=new Map(), ak=["state","before_output_sha256","after_output_sha256","reference_sha256"],tk=["value","basis","evidence_sha256","after_output_sha256"];
  for(const d of input.decisions){
    need(exact(d,["case_id","tier","endpoint","asserted","checked","truth"])&&cases.has(d.case_id)&&!decisions.has(d.case_id),"Invalid or duplicate decision");
    const c=cases.get(d.case_id), b=outputs.get(c.before_sha256),a=outputs.get(c.after_sha256);
    need(c.rights&&b&&a,"Decision without rights or complete outputs");
    need(d.tier===1&&d.endpoint==="pointwise","Wrong endpoint/tier");
    for(const arm of [d.asserted,d.checked]){
      need(exact(arm,ak)&&S.includes(arm.state),"Invalid oracle state");
      need(arm.before_output_sha256===b&&arm.after_output_sha256===a&&arm.reference_sha256===c.reference_sha256,"Arm evidence binding mismatch");
      need(c.reference_sha256!==null||!B.has(arm.state),"Binary decision without approved reference in fixture");
    }
    const x=d.asserted.state,y=d.checked.state;
    need(x===y||(B.has(x)&&y==="UNKNOWN"),"Unexpected frozen D4 pointwise transition");
    const t=d.truth;need(exact(t,tk)&&t.after_output_sha256===a,"Truth binding mismatch");
    if(t.value===null)need(t.basis===null&&t.evidence_sha256===null,"Missing truth must have null basis");
    else need(typeof t.value==="boolean"&&t.basis==="SYNTHETIC_INDEPENDENT_FIXTURE"&&hash(t.evidence_sha256),"Truth must be independently supplied in fixture");
    decisions.set(d.case_id,{...c,asserted:x,checked:y,truth:t.value});
  }
  const rs=[...decisions.values()], cs=input.cases, eligible=c=>C.every(k=>c.conditions[k]==="PASS")&&c.rights&&c.adjudicated;
  const availability={BOTH_BOUND:0,BEFORE_ONLY:0,AFTER_ONLY:0,NEITHER:0};
  for(const c of cs){const b=outputs.has(c.before_sha256),a=outputs.has(c.after_sha256);availability[b?(a?"BOTH_BOUND":"BEFORE_ONLY"):(a?"AFTER_ONLY":"NEITHER")]++}
  const flow={enrolled:37,physical_ids:18,rights:count(cs,c=>c.rights),two_proposals:count(cs,c=>c.two_proposals),adjudicated:count(cs,c=>c.adjudicated),reference_approved:count(cs,c=>c.reference_sha256!==null),eight_conditions_pass:count(cs,eligible),unique_images_with_output:outputs.size,unique_images_expected:45,paired_outputs:availability.BOTH_BOUND,paired_decisions:rs.length,missing_output_candidates:37-availability.BOTH_BOUND,missing_decisions_given_outputs:availability.BOTH_BOUND-rs.length,truth_known_in_frame:count(rs,r=>r.truth!==null),missing_truth_in_frame:count(rs,r=>r.truth===null),frame_coverage:rate(rs.length,37),physical_ids_in_frame:new Set(rs.map(r=>r.physical_id)).size,availability};
  const report={schema:"C2-37-fixture-report/1",scope:"SYNTHETIC_ONLY",scientific_gate:"GO_PREPARATORY_ONLY",superiority:"NOT_EVALUATED",flow,condition_counts:Object.fromEntries(C.map(k=>[k,Object.fromEntries(["PASS","FAIL","UNKNOWN"].map(v=>[v,count(cs,c=>c.conditions[k]===v)]))])),status:"INCOMPLETE_FRAME_NO_PRIMARY_METRICS",metrics:null};
  if(rs.length!==37)return report;
  // Extremize a ratio by sorting contributions and enumerating prefix lengths.
  function bounds(s,n,vals){
    const out=[];if(n)out.push(s/n);
    for(const rev of [false,true]){let a=s,b=n;for(const v of [...vals].sort((x,y)=>rev?y-x:x-y)){a+=v;b++;out.push(a/b)}}
    return {minimum:out.length?Math.min(...out):null,maximum:out.length?Math.max(...out):null,can_be_undefined:n===0};
  }
  function metrics(r){
    const F=r.filter(x=>x.truth===true),N=r.filter(x=>x.truth===false),U=r.filter(x=>x.truth===null),arms={};
    for(const arm of ["asserted","checked"]){
      const d=r.filter(x=>B.has(x[arm])),dt=d.filter(x=>x.truth!==null);
      const det=count(F,x=>x[arm]==="FAULT"),fa=count(N,x=>x[arm]==="FAULT");
      arms[arm]={states:Object.fromEntries(S.map(s=>[s,count(r,x=>x[arm]===s)])),coverage:rate(d.length,r.length),abstention:rate(count(r,x=>x[arm]==="UNKNOWN"),r.length),sensitivity:rate(det,F.length),far:rate(fa,N.length),selective_risk:rate(count(dt,x=>(x[arm]==="FAULT")!==x.truth),dt.length),missed_faults_by_state:Object.fromEntries(S.slice(1).map(s=>[s,count(F,x=>x[arm]===s)])),sensitivity_missing_truth_bounds:bounds(det,F.length,U.map(x=>Number(x[arm]==="FAULT"))),far_missing_truth_bounds:bounds(fa,N.length,U.map(x=>Number(x[arm]==="FAULT")))};
    }
    const withdrawn=x=>x.asserted==="FAULT"&&x.checked==="UNKNOWN",diff=arms.asserted.far.k-arms.checked.far.k;
    return {n:r.length,truth_known:F.length+N.length,truth_faults:F.length,truth_nonfaults:N.length,truth_missing:U.length,truth_availability:rate(F.length+N.length,r.length),states:S,asserted_to_checked:S.map(a=>S.map(c=>count(r,x=>x.asserted===a&&x.checked===c))),arms,far_difference:rate(diff,N.length),withdrawn_alarms:count(r,withdrawn),withdrawn_false_alarms:count(N,withdrawn),withdrawn_true_detections:count(F,withdrawn),withdrawn_unknown_truth:count(U,withdrawn),far_difference_missing_truth_bounds:bounds(diff,N.length,U.map(x=>Number(x.asserted==="FAULT")-Number(x.checked==="FAULT")))};
  }
  report.status="COMPLETE_SYNTHETIC_FRAME_DESCRIPTIVE_ONLY";report.metrics=metrics(rs);
  report.by_template=Object.fromEntries([...group(rs,r=>r.template)].map(([k,v])=>[k,{physical_ids:new Set(v.map(r=>r.physical_id)).size,...metrics(v)}]));
  report.by_field=Object.fromEntries([...group(rs,r=>r.field_kind)].map(([k,v])=>[k,metrics(v)]));
  report.cluster_contributions=[...group(rs,r=>r.physical_id)].map(([k,v])=>({synthetic_id:k,template:v[0].template,...metrics(v)}));
  return report;
}
module.exports={analyzeFixture};
