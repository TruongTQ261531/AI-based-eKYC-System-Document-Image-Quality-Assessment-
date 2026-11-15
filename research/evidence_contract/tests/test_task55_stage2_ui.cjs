const test = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {runInNewContext} = require('node:vm');

test('output review locks conditions before displaying predictions and requires notes for errors', () => {
  const source = readFileSync(join(__dirname, '../task55/ifv_stage2.js'), 'utf8');
  const elements = new Map();
  const field = (id) => {
    if (!elements.has(id)) elements.set(id, {value: '', add() {}, addEventListener() {}});
    return elements.get(id);
  };
  const observed = {availability: 'visible', readability: 'readable', observed_transcript: 'UNIT',
    sources: [{kind:'mrz',location:'bottom',availability:'visible',readability:'readable',
      observed_text:'UNIT',mrz_line_1:'UNIT_LINE_1',mrz_line_2:'UNIT_LINE_2'}], notes: ''};
  const packet = {packet_id: 'stage2-ui-unit', cases: [{case_id: 'CASE-unit', label: 'Unit Field',
    contract: 'C3', target_label: 'Another Field', before_evidence: observed, after_evidence: observed,
    author_reference: 'UNIT', before_image: 'unit-a.png', after_image: 'unit-b.png',
    before_output: {value: 'UNIT', structured_output_usable: true},
    after_output: {value: 'WRONG_UNIT', structured_output_usable: true}}]};
  let saved;
  const downloads = [];
  runInNewContext(source, {
    window: {OUTPUT_PACKET: packet, addEventListener() {}},
    document: {getElementById: field, body:{append(){}}, createElement:()=>({click(){},remove(){}})},
    localStorage: {getItem() { return null; }, setItem(key, value) { saved = JSON.parse(value); }},
    Option: function () {}, Blob,
    URL:{createObjectURL:blob=>{downloads.push(blob);return 'unit';},revokeObjectURL(){}},
    setTimeout:fn=>fn()
  });
  assert.equal(field('output').hidden, true);
  assert.equal(field('after-value').textContent, '');
  field('reveal').onclick();
  assert.equal(field('output').hidden, true);
  assert.equal(saved, undefined);
  assert.match(field('before-evidence').textContent, /MRZ 1: UNIT_LINE_1/);
  assert.match(field('before-evidence').textContent, /MRZ 2: UNIT_LINE_2/);
  field('test_validity').value = 'valid';
  field('reason').value = 'Unit test evidence';
  field('reveal').onclick();
  assert.equal(saved['CASE-unit'].test_validity, 'valid');
  assert.equal(field('reason').disabled, true);
  assert.equal(field('after-value').textContent, 'WRONG_UNIT');
  field('export').onclick();
  assert.equal(downloads.length, 0);
  assert.match(field('message').textContent, /ít nhất một ca/);
  field('export-draft').onclick();
  assert.equal(downloads.length, 1);
  field('before_reading').value = 'correct';
  field('after_reading').value = 'wrong_value';
  field('save').onclick();
  assert.equal(saved['CASE-unit'].after_reading, undefined);
  field('output-note').value = 'Injected mismatch';
  field('save').onclick();
  assert.equal(saved['CASE-unit'].after_reading, 'wrong_value');
  field('export').onclick();
  assert.equal(downloads.length, 2);
});

test('full export waits for every case; draft retains pre-reveal conditions', async () => {
  const elements = new Map(), downloads = [];
  const field = id => {
    if (!elements.has(id)) elements.set(id,{value:'',add(){},addEventListener(){}});
    return elements.get(id);
  };
  const evidence = {availability:'not_seen',readability:'unreadable',observed_transcript:'',sources:[]};
  const cases = [0,1].map(n=>({case_id:'UNIT-'+n,contract:'C1',label:'Unit',target_label:'Unit',
    before_evidence:evidence,after_evidence:evidence,before_output:{value:'',structured_output_usable:true},
    after_output:{value:'',structured_output_usable:true}}));
  runInNewContext(readFileSync(join(__dirname,'../task55/ifv_stage2.js'),'utf8'),{
    window:{OUTPUT_PACKET:{packet_id:'unit',phase1_snapshot:'unit',cases},addEventListener(){},confirm:()=>true},
    document:{getElementById:field,body:{append(){}},createElement:()=>({click(){},remove(){}})},
    localStorage:{getItem:()=>null,setItem(){}},Option:function(){},Blob,
    URL:{createObjectURL:blob=>{downloads.push(blob);return 'unit';},revokeObjectURL(){}},setTimeout:fn=>fn()
  });
  field('test_validity').value='uncertain'; field('absence_check').value='not_established';
  field('reason').value='Unit evidence'; field('reveal').onclick();
  field('export-draft').onclick();
  const backup=JSON.parse(await downloads[0].text());
  assert.equal(backup.export_kind,'draft');
  assert.equal(backup.items[0].reason,'Unit evidence');
  assert.ok(backup.items[0].first_reveal_at);
  field('before_reading').value='uncertain';field('after_reading').value='uncertain';
  field('save').onclick();field('export').onclick();
  assert.equal(downloads.length,1);
  assert.match(field('message').textContent,/Còn 1 ca/);
  field('export-partial').onclick();
  const partial=JSON.parse(await downloads[1].text());
  assert.equal(partial.export_kind,'reviewed_observations');
  assert.equal(partial.items.length,1);
});
