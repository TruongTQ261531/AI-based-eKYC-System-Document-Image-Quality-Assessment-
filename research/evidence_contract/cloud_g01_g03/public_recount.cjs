// Independent public-artifact arithmetic; no OCR, training, or private input.
// Run from repository root: node research/evidence_contract/cloud_g01_g03/public_recount.cjs
const fs = require('node:fs');
const crypto = require('node:crypto');
const paths = {
  "controls": "research/evidence_contract/execution/master_01/d4_development_20261117/controls_01/control_results.json",
  "controlSummary": "research/evidence_contract/execution/master_01/d4_development_20261117/controls_01/summary.json",
  "historical": "research/evidence_contract/execution/master_01/d4_development_20261117/historical_01/summary.json",
  "design": "research/evidence_contract/execution/master_01/p5b_calibration_20261121/design.json",
  "calibration": "research/evidence_contract/execution/master_01/p5b_calibration_20261121/calibration.json",
  "heldOut": "research/evidence_contract/execution/master_01/p5b_calibration_20261121/held_out.json",
  "p5": "research/evidence_contract/execution/master_01/p5_simulation_20261121/verification.json",
  "p6": "research/evidence_contract/execution/master_01/p6_integrity_20261121/aggregate.json",
  "p6verify": "research/evidence_contract/execution/master_01/p6_integrity_20261121/verification.json",
  "ifv": "research/evidence_contract/execution/master_01/reviewer_intake_20261120_r03_phase2/r02_r03_agreement.json",
  "ifvAuthor": "research/evidence_contract/execution/master_01/reviewer_intake_20261120_r03_phase2/author_r03_agreement.json",
  "c2": "research/evidence_contract/human_gate/receipts/c2_37_20261123/aggregate.json",
  "c2verify": "research/evidence_contract/human_gate/receipts/c2_37_20261123/verification.json"
};
function audit(d){
  const checks=[],failures=[];
  function check(name,x){checks.push(name);if(!x)failures.push(name)}
  const sum=a=>a.reduce((x,y)=>x+y,0);
  const states=["FAULT","NO_FAULT","UNKNOWN","INVALID_TEST"];
  const matrices={},unique=new Set();let differences=0,nonTreatment=0,expectationMismatch=0;
  for(const t of ["1","2"]){
    const m=states.map(()=>states.map(()=>0)); matrices[t]=m;
    for(const row of d.controls){
      const p=row.panels[t], a=p.arms.mrz_metadata_asserted,c=p.arms.checked_v2;
      const endpoints=["pointwise","relation","structure"];
      const x=states.indexOf(a.pointwise.state),y=states.indexOf(c.pointwise.state);
      if(x<0||y<0)throw new Error("Unexpected pointwise state");
      m[x][y]++;
      for(const arm of ["checked_v2","mrz_metadata_asserted"]){
        if(JSON.stringify(endpoints.map(k=>p.arms[arm][k].state))!==JSON.stringify(row.expected[t][arm]))expectationMismatch++;
      }
      if(endpoints.some(k=>a[k].state!==c[k].state)){differences++;unique.add(row.name);if(!row.family.includes("mrz"))nonTreatment++;}
    }
    check("D4 tier "+t+" denominator",sum(m.flat())===72);
    check("D4 tier "+t+" transitions match monotonicity",m.every((r,i)=>r.every((v,j)=>v===0||i===j||(i<2&&j===2))));
    check("D4 tier "+t+" exact published withdrawal counts",m[0][2]===6&&m[1][2]===2);
  }
  check("D4 72 unique controls",d.controls.length===72&&new Set(d.controls.map(r=>r.name)).size===72);
  check("D4 expected state vectors match",expectationMismatch===0);
  check("D4 divergence counts",differences===d.controlSummary.divergence_tier_pairs&&unique.size===d.controlSummary.divergence_unique_controls);
  for(const arm of ["checked_v2","mrz_metadata_asserted"]){
    const c=d.historical.state_counts[arm];check("Historical "+arm+" semantic abstention",c.pointwise.UNKNOWN===46&&c.relation.UNKNOWN===46&&c.structure.NO_FAULT===46);
  }
  check("Historical replay is not truth",d.historical.production_approvals===0&&d.historical.truth_labels_used===false&&d.historical.primary_physical_ids===3);
  function agreement(obj,label){
    const out={};
    for(const [view,v] of Object.entries(obj.views)){
      out[view]={};
      for(const [endpoint,x] of Object.entries(v.derived)){
        if(!x.contingencies||typeof x.compared!=="number")continue;
        const n=sum(x.contingencies.map(c=>c.count)), matched=sum(x.contingencies.filter(c=>c.first===c.second).map(c=>c.count));
        const labs=[...new Set(x.contingencies.flatMap(c=>[c.first,c.second]))];
        const pe=n?sum(labs.map(l=>sum(x.contingencies.filter(c=>c.first===l).map(c=>c.count))*sum(x.contingencies.filter(c=>c.second===l).map(c=>c.count))))/(n*n):null;
        const k=n&&pe!==1?(matched/n-pe)/(1-pe):null;
        check(label+" "+view+" "+endpoint+" totals",n===x.compared&&matched===x.matched&&n-matched===x.disagreed);
        check(label+" "+view+" "+endpoint+" agreement",n?Math.abs(matched/n-x.exact_agreement)<1e-12:x.exact_agreement===null);
        check(label+" "+view+" "+endpoint+" kappa",k===null?x.cohen_kappa===null:Math.abs(k-x.cohen_kappa)<1e-12);
        out[view][endpoint]={n,matched,kappa:k};
      }
    }
    return out;
  }
  const ifv={external:agreement(d.ifv,"IFV external"),author:agreement(d.ifvAuthor,"IFV author")};
  function wilson(k,n){if(!n)return null;const z=1.959963984540054,p=k/n,den=1+z*z/n,mid=(p+z*z/(2*n))/den,h=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return {k,n,rate:p,lo:Math.max(0,mid-h),hi:Math.min(1,mid+h)}}
  const p5b={};
  for(const stage of ["calibration","heldOut"]){
    const obj=d[stage],N=obj.n, out={};p5b[stage]=out;
    const expectedN=d.design.stages[stage==="heldOut"?"held_out":stage].repetitions;
    check(stage+" repetition count",N===expectedN);
    const entries=Object.entries(obj.points).filter(([k,v])=>v.methods);
    check(stage+" 23 evaluated scenarios",entries.length===23);
    for(const [s,v] of entries){
      check(stage+" "+s+" probability mass",Math.abs(sum(v.cells.map(c=>c.probability))-1)<1e-9&&v.cells.every(c=>c.probability>=0));
      for(const [m,r] of Object.entries(v.methods)){
        check(stage+" "+s+" "+m+" count constraints",r.issued+r.insufficient===N&&r.joint<=r.issued&&r.passes.every(x=>x>=r.joint&&x<=r.issued)&&r.covers.every(x=>x<=r.issued&&x>=0));
      }
    }
    for(const m of d.design.methods){
      const ref=obj.points.mixed_200.methods[m];
      const power=wilson(ref.joint,N),coverage=ref.covers.map(x=>wilson(x,ref.issued));
      const nulls=["null_far","null_sensitivity","null_coverage","null_joint"];
      const sizes=Object.fromEntries(nulls.map(s=>[s,wilson(obj.points[s].methods[m].joint,N)]));
      const marginalSizes=[wilson(obj.points.null_coverage.methods[m].passes[0],N),wilson(obj.points.null_sensitivity.methods[m].passes[1],N),wilson(obj.points.null_far.methods[m].passes[2],N)];
      const allSizes=[...Object.values(sizes),...marginalSizes];
      const infeasible=power.hi<.8||coverage.some(x=>x.hi<.95)||allSizes.some(x=>x.lo>.05);
      const feasible=power.lo>=.8&&coverage.every(x=>x.lo>=.95)&&allSizes.every(x=>x.hi<=.05);
      const verdict=infeasible?"INFEASIBLE":feasible?"FEASIBLE":"INSUFFICIENT_EVIDENCE";
      check(stage+" "+m+" recomputed verdict",verdict===obj.verdicts[m]);
      out[m]={power,coverage,sizes,marginalSizes,verdict};
    }
  }
  const p5={};for(const [k,v] of Object.entries(d.p5.independent_replication)){
    p5[k]={};
    for(const [name,x] of Object.entries(v)){
      const items=name==="coverage_if_issued"?Object.entries(x):[[name,x]];
      for(const [label,z] of items){const w=wilson(z.k,z.n);check("P5 "+k+" "+label+" Wilson",Math.abs(w.rate-z.rate)<1e-12&&Math.abs(w.lo-z.lo)<1e-9&&Math.abs(w.hi-z.hi)<1e-9);p5[k][label]=w;}
    }
  }
  const p=d.p6;
  const localEvals=p.local_adapters.flatMap(x=>x.evaluations);
  const p6={groups:p.groups,roles:p.by_role,adapters:p.local_adapters.length,adapterEvaluations:localEvals.length,importedEvaluations:p.imported_vlm.evaluations.length,trainPresentationsPerRun:[...new Set(p.local_adapters.map(x=>x.candidate_presentations))],sameCheckpointOverlap:p.status_counts.CONFIRMED_SAME_CHECKPOINT_OVERLAP,upstreamPretrainingUnknown:p.checkpoint_pretraining_unknown_groups,independentTruth:p.d4.independent_truth_cases_available};
  check("P6 role counts sum",sum(Object.values(p.by_role))===p.groups);
  check("P6 status counts sum",sum(Object.values(p.status_counts))===p.groups);
  check("P6 adapter counts and memberships",p.local_adapters.length===12&&p.local_adapters.every(x=>x.candidate_training_groups===24&&x.candidate_presentations===48)&&p.groups===24&&p.candidate_member_files===144);
  check("P6 evaluated local rows do not intersect audited pixel groups",localEvals.every(x=>x.candidate_pixel_groups===0&&x.confirmed_candidate_overlap===0));
  check("P6 D4 withdrawals agree with independent matrix",["1","2"].every(t=>p.d4.withdrawals[t].pointwise.FAULT===matrices[t][0][2]&&p.d4.withdrawals[t].pointwise.NO_FAULT===matrices[t][1][2]));
  check("P6 verification counters match",d.p6verify.public.candidate_groups===p.groups&&d.p6verify.public.local_adapter_runs===p.local_adapters.length&&d.p6verify.public.paired_D4_evaluations===144);
  const c=d.c2,s=c.selected,v=d.c2verify;
  check("C2 partition counts",s.scope.candidates+c.held.candidates===45&&s.scope.physical_ids+c.held.physical_ids===24&&s.scope.candidates===37&&s.scope.physical_ids===18);
  check("C2 technical counts",v.total_forms===2*c.forms_per_workspace&&v.images_per_workspace===c.images_per_workspace&&v.excluded_asset_or_form_matches===0&&v.retained_candidates===37&&v.retained_physical_ids===18&&v.rights_versions_checked===5);
  check("C2 rights state not promoted",c.owner_approval===null&&c.assessor_sharing==="REVIEW_ACCESS_PENDING"&&s.approved.candidates===0&&s.eligible.candidates===0&&s.shareable.candidates===0&&s.observations_received.candidates===0);
  for(const [name,z] of Object.entries(s.conditions))check("C2 condition "+name+" counts",sum(Object.values(z).map(x=>x.candidates))===37);
  return {scope:"PUBLIC_ROW_RECOUNT_AND_AGGREGATE_ARITHMETIC_ONLY",checks:checks.length,failures,states,matrices,divergenceTierPairs:differences,divergenceControls:unique.size,expectationMismatch,ifv,p5,p5b,p6,c2:{candidates:37,physicalIds:18,approved:s.approved.candidates,eligible:s.eligible.candidates,shareable:s.shareable.candidates},historical:{cases:d.historical.cases,primary:d.historical.primary_cases,physicalIds:d.historical.primary_physical_ids,selectiveRisk:d.historical.selective_risk_pointwise}};
}
const blobs = {}, data = {};
for(const [k,p] of Object.entries(paths)){
  const buf=fs.readFileSync(p);
  blobs[k]=crypto.createHash('sha1').update('blob '+buf.length+'\0').update(buf).digest('hex');
  data[k]=JSON.parse(buf.toString('utf8'));
}
const result=audit(data);
console.log(JSON.stringify({source_blobs:blobs,result},null,2));
if(result.failures.length)process.exitCode=1;
