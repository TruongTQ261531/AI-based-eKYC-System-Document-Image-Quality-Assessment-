const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function mount() {
  const elements=new Map();
  const get=id=>{if(!elements.has(id))elements.set(id,{value:'',add(){},addEventListener(){}});return elements.get(id);};
  const evidence={availability:'visible',readability:'readable',semantic_key_confirmed:'yes',
    observed_transcript:'DEMO12345',sources:[],notes:''};
  const packet={packet_id:'unit',cases:[{case_id:'unit',contract:'C3',label:'Unit',target_label:'Unit',
    before_evidence:evidence,after_evidence:evidence,
    before_output:{value:'DEMO12345',structured_output_usable:true},
    after_output:{value:'DEM012345',structured_output_usable:true}}]};
  let saved;
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../task55/ifv_stage2.js'),'utf8'),{
    window:{OUTPUT_PACKET:packet,addEventListener(){}},document:{getElementById:get},Option:function(){},
    localStorage:{getItem:()=>null,setItem:(key,value)=>saved=JSON.parse(value)}
  });
  get('test_validity').value='valid';get('reason').value='Unit evidence';get('reveal').onclick();
  get('before_reading').value='correct';
  return {get,saved:()=>saved};
}

test('nonempty field cannot be recorded as an omission',()=>{
  const m=mount();m.get('after_reading').value='readable_omission';m.get('output-note').value='Unit note';
  m.get('save').onclick();
  assert.equal(m.saved().unit.after_reading,undefined);
  assert.match(m.get('message').textContent,/không trống không phải bỏ sót/);
});

test('literal O/0 discrepancy requires a note, without auto-correcting a judgment',()=>{
  const m=mount();m.get('after_reading').value='correct';m.get('save').onclick();
  assert.equal(m.saved().unit.after_reading,undefined);
  assert.match(m.get('message').textContent,/chữ O và số 0/);
  m.get('output-note').value='Unit reviewer explanation of their discrepancy';m.get('save').onclick();
  assert.equal(m.saved().unit.after_reading,'correct');
});
