// From repository root: node research/evidence_contract/cloud_g01_g03/test_c2_37_fixture.cjs
const {analyzeFixture}=require('./c2_37_fixture.cjs');
function fixture(){
  const h=n=>n.toString(16).padStart(64,"0");
  const reader={name:"SYNTH_READER",checkpoint_sha256:h(10001),config_sha256:h(10002),runtime_sha256:h(10003),profile:"SYNTH_RECT2"};
  const cases=[],outputs=[],decisions=[],images=new Map();
  let idx=0,id=0,extra=0;
  const conditions=["backup_supported_after","backup_supported_before","distinct_sources","primary_removed_after","primary_supported_before","provenance_verified","reference_approved","semantic_equality_approved"];
  for(const [template,nids,ncases] of [["05",7,12],["32",4,11],["41",7,14]]){
    const pool=Array.from({length:nids},()=>{const i=++id;return {id:i,b:h(100+i),a:h(200+i)}});
    for(let j=0;j<ncases;j++){
      const p=pool[j%nids],a=j>=nids&&extra<9?h(300+(++extra)):p.a;
      for(const v of [p.b,a])if(!images.has(v))images.set(v,h(3000+images.size));
      const k=++idx,ref=h(500+k);
      cases.push({case_id:"SYNTH_C"+k,physical_id:"SYNTH_ID"+p.id,template,field_kind:k<=11?"IDENTIFIER":"DATE_FULL",before_sha256:p.b,after_sha256:a,rights:true,two_proposals:true,adjudicated:true,reference_sha256:ref,conditions:Object.fromEntries(conditions.map(v=>[v,"PASS"]))});
      const x=["FAULT","FAULT","NO_FAULT","UNKNOWN","INVALID_TEST","FAULT","NO_FAULT"][(k-1)%7],y=["UNKNOWN","FAULT","UNKNOWN","UNKNOWN","INVALID_TEST","FAULT","NO_FAULT"][(k-1)%7];
      const value=k%3===0?null:k%3===1;
      const binding={before_output_sha256:images.get(p.b),after_output_sha256:images.get(a),reference_sha256:ref};
      decisions.push({case_id:"SYNTH_C"+k,tier:1,endpoint:"pointwise",asserted:{state:x,...binding},checked:{state:y,...binding},truth:{value,basis:value===null?null:"SYNTHETIC_INDEPENDENT_FIXTURE",evidence_sha256:value===null?null:h(700+k),after_output_sha256:images.get(a)}});
    }
  }
  for(const [image_sha256,output_sha256] of images)outputs.push({image_sha256,output_sha256,reader:{...reader}});
  return {schema:"C2-37-fixture/1",scope:"SYNTHETIC_ONLY",reader,cases,outputs,decisions};
}
function testSuite(analyzeFixture,fixture){
  const passed=[],failed=[];
  const test=(name,fn)=>{try{if(!fn())throw Error("assertion false");passed.push(name)}catch(e){failed.push({name,error:String(e)})}};
  const rejects=(change,contains)=>{const f=fixture();change(f);try{analyzeFixture(f)}catch(e){return String(e).includes(contains)}return false};
  const a=analyzeFixture(fixture()),m=a.metrics;
  test("complete status",()=>a.status==="COMPLETE_SYNTHETIC_FRAME_DESCRIPTIVE_ONLY");
  test("37 candidates 18 IDs 45 images",()=>a.flow.enrolled===37&&a.flow.physical_ids===18&&a.flow.unique_images_with_output===45);
  test("template strata",()=>a.by_template["05"].n===12&&a.by_template["05"].physical_ids===7&&a.by_template["32"].n===11&&a.by_template["32"].physical_ids===4&&a.by_template["41"].n===14&&a.by_template["41"].physical_ids===7);
  test("field composition",()=>a.by_field.IDENTIFIER.n===11&&a.by_field.DATE_FULL.n===26);
  test("clusters conserve cases",()=>a.cluster_contributions.reduce((s,r)=>s+r.n,0)===37&&a.cluster_contributions.length===18);
  test("transition matrix exact",()=>JSON.stringify(m.asserted_to_checked)===JSON.stringify([[11,0,6,0],[0,5,5,0],[0,0,5,0],[0,0,0,5]]));
  test("coverage includes missing truth",()=>m.arms.checked.coverage.n===37&&m.arms.asserted.coverage.n===37);
  test("truth counts conserve",()=>m.truth_faults+m.truth_nonfaults+m.truth_missing===37);
  test("UNKNOWN distinct from truth missing",()=>m.arms.checked.states.UNKNOWN!==m.truth_missing);
  test("withdrawals conserve",()=>m.withdrawn_alarms===m.withdrawn_false_alarms+m.withdrawn_true_detections+m.withdrawn_unknown_truth);
  test("all fault sensitivity denominator",()=>m.arms.checked.sensitivity.n===m.truth_faults);
  test("missed faults conserve",()=>Object.values(m.arms.checked.missed_faults_by_state).reduce((s,v)=>s+v,0)+m.arms.checked.sensitivity.k===m.truth_faults);
  test("FAR delta",()=>Math.abs(m.far_difference.value-(m.arms.asserted.far.value-m.arms.checked.far.value))<1e-12);
  test("missing truth -> null rates",()=>{const f=fixture();for(const d of f.decisions)Object.assign(d.truth,{value:null,basis:null,evidence_sha256:null});const x=analyzeFixture(f).metrics;return x.arms.checked.far.value===null&&x.arms.checked.sensitivity.value===null&&x.arms.checked.selective_risk.value===null&&x.arms.checked.coverage.n===37&&x.far_difference_missing_truth_bounds.can_be_undefined});
  test("all fault -> no FAR",()=>{const f=fixture();for(const d of f.decisions)Object.assign(d.truth,{value:true,basis:"SYNTHETIC_INDEPENDENT_FIXTURE",evidence_sha256:"a".repeat(64)});return analyzeFixture(f).metrics.far_difference.value===null});
  test("missing output suppresses metrics",()=>{const f=fixture(),h=f.cases[0].before_sha256,ids=new Set(f.cases.filter(c=>c.before_sha256===h).map(c=>c.case_id));f.outputs=f.outputs.filter(o=>o.image_sha256!==h);f.decisions=f.decisions.filter(d=>!ids.has(d.case_id));const r=analyzeFixture(f);return r.metrics===null&&r.flow.missing_output_candidates===ids.size&&r.flow.missing_decisions_given_outputs===0});
  test("missing decision suppresses metrics",()=>{const f=fixture();f.decisions.pop();const r=analyzeFixture(f);return r.metrics===null&&r.flow.missing_output_candidates===0&&r.flow.missing_decisions_given_outputs===1});
  test("zero outputs not UNKNOWN",()=>{const f=fixture();f.outputs=[];f.decisions=[];const r=analyzeFixture(f);return r.metrics===null&&r.flow.availability.NEITHER===37&&r.flow.missing_output_candidates===37});
  test("reject production",()=>rejects(f=>f.scope="PRODUCTION","Production input"));
  test("reject extra field",()=>rejects(f=>f.raw="not allowed","Invalid input schema"));
  test("reject duplicate case",()=>rejects(f=>f.cases[1].case_id=f.cases[0].case_id,"duplicate candidate"));
  test("reject incomplete cohort",()=>rejects(f=>f.cases.pop(),"37 candidate"));
  test("reject Greek template",()=>rejects(f=>f.cases[0].template="25","Unknown template"));
  for(const [k,v] of Object.entries({name:"SYNTH_OTHER",checkpoint_sha256:"a".repeat(64),config_sha256:"a".repeat(64),runtime_sha256:"a".repeat(64),profile:"SYNTH_OTHER"}))test("reject changed "+k,()=>rejects(f=>f.outputs[0].reader[k]=v,"mismatch"));
  test("reject duplicate output",()=>rejects(f=>f.outputs.push(f.outputs[0]),"Duplicate output"));
  test("reject extraneous image",()=>rejects(f=>f.outputs[0].image_sha256="f".repeat(64),"extraneous output"));
  test("reject wrong arm output",()=>rejects(f=>f.decisions[0].checked.after_output_sha256="f".repeat(64),"Arm evidence"));
  test("reject wrong arm reference",()=>rejects(f=>f.decisions[0].checked.reference_sha256="f".repeat(64),"Arm evidence"));
  test("reject wrong tier",()=>rejects(f=>f.decisions[0].tier=2,"Wrong endpoint"));
  test("reject wrong endpoint",()=>rejects(f=>f.decisions[0].endpoint="relation","Wrong endpoint"));
  test("reject binary reversal",()=>rejects(f=>f.decisions[0].checked.state="NO_FAULT","Unexpected frozen"));
  test("reject truth from reader",()=>rejects(f=>f.decisions[0].truth.basis="OCR_PREDICTION","Truth must"));
  test("reject truth wrong output",()=>rejects(f=>f.decisions[0].truth.after_output_sha256="f".repeat(64),"Truth binding"));
  test("reject approval without adjudication",()=>rejects(f=>f.cases[0].adjudicated=false,"Reference approval"));
  test("reject proposals before rights",()=>rejects(f=>f.cases[0].rights=false,"Proposal before rights"));
  test("reject duplicate decision",()=>rejects(f=>f.decisions.push(f.decisions[0]),"duplicate decision"));
  test("reject truth string",()=>rejects(f=>f.decisions[0].truth.value="true","Truth must"));
  test("no scientific promotion",()=>a.superiority==="NOT_EVALUATED"&&a.scientific_gate==="GO_PREPARATORY_ONLY");
  // Exhaustively assign the 12 missing fixture truth values (4096 possibilities).
  test("missing-truth extrema verified by exhaustive assignment",()=>{
    const f=fixture(),u=f.decisions.filter(d=>d.truth.value===null);
    let minSens=Infinity,maxSens=-Infinity,minDelta=Infinity,maxDelta=-Infinity;
    for(let bits=0;bits<(1<<u.length);bits++){
      let F=0,N=0,H=0,D=0;
      for(const d of f.decisions){
        const i=u.indexOf(d),v=i<0?d.truth.value:Boolean(bits&(1<<i));
        if(v){F++;D+=Number(d.checked.state==="FAULT")}else{N++;H+=Number(d.asserted.state==="FAULT")-Number(d.checked.state==="FAULT")}
      }
      if(F){minSens=Math.min(minSens,D/F);maxSens=Math.max(maxSens,D/F)}
      if(N){minDelta=Math.min(minDelta,H/N);maxDelta=Math.max(maxDelta,H/N)}
    }
    const s=m.arms.checked.sensitivity_missing_truth_bounds,z=m.far_difference_missing_truth_bounds;
    return Math.abs(s.minimum-minSens)<1e-12&&Math.abs(s.maximum-maxSens)<1e-12&&Math.abs(z.minimum-minDelta)<1e-12&&Math.abs(z.maximum-maxDelta)<1e-12;
  });
  return {passed,failed,fixture_summary:{flow:a.flow,metrics:a.metrics}};
}
const result=testSuite(analyzeFixture,fixture);
console.log(JSON.stringify(result,null,2));
if(result.failed.length)process.exitCode=1;
