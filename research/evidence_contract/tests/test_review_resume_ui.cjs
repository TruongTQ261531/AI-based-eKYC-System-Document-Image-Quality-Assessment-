const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const core = require('../task55/review_core.js');

function fixture() {
  const packet = {packet_id:'unit-resume', purpose:'ui_unit_control', pages:[0,1].map(n=>({
    image_id:'img'+n, image:'images/'+n+'.png', file_sha256:'hash'+n,
    fields:[{slot_id:'F'+n, field_key:'field'+n, label:'Unit field '+n}]
  }))};
  const state = core.initial(packet);
  state.profile = {reviewer_id:'unit',role:'unknown',output_exposure:'none'};
  for (const n of [0,1]) state.answers['F'+n] = {...core.blank(),touched:true,
    availability:'visible',readability:'readable',semantic_key_confirmed:'yes',prior_exposure:'no',
    observed_transcript:'UNIT TEXT '+n};
  return {packet, state, submission:core.exportReview(packet,state).value};
}

function mount(packet, submission, saved=null, profile=null) {
  const nodes = new Map(), sections = new Map(), local = new Map();
  if(saved)local.set('resume-isolated',JSON.stringify(saved));
  const get = id => {if(!nodes.has(id))nodes.set(id,{value:''});return nodes.get(id);};
  get('fields').querySelectorAll=()=>{
    sections.clear();
    for(const m of get('fields').innerHTML.matchAll(/data-slot="([^"]+)"/g)) {
      const callbacks={}, add={}, validation={}, copy={dataset:{index:'0'}};
      const section={dataset:{slot:m[1]},callbacks,add,copy,validation,
        addEventListener:(event,fn)=>callbacks[event]=fn,
        querySelector:selector=>selector==='.add-source'?add:validation,
        querySelectorAll:selector=>selector==='.copy-field-source'?[copy]:[]};
      sections.set(m[1],section);
    }
    return [...sections.values()];
  };
  const downloads=[];
  const window={BLIND_PACKET:packet,BlindReviewCore:core,BLIND_REVIEW_RESUME:submission,BLIND_REVIEW_PROFILE:profile,
    BLIND_REVIEW_STORAGE_KEY:'resume-isolated',BLIND_IMAGE_PREFIX:'../frozen/',
    localStorage:{getItem:k=>local.get(k),setItem:(k,v)=>local.set(k,v)},
    addEventListener(){},scrollTo(){},confirm:()=>false};
  const document={getElementById:get,body:{append(){}},createElement:()=>({click(){},remove(){}})};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../task55/review_ui.js'),'utf8'),{
    window,document,Blob,URL:{createObjectURL:blob=>{downloads.push(blob);return 'unit';},revokeObjectURL(){}},setTimeout:fn=>fn()
  });
  return {get,sections,local,downloads,window};
}

test('resume retains text, shows pending progress and blocks misleading full export',()=>{
  const {packet,submission}=fixture();
  const m=mount(packet,submission);
  assert.match(m.get('progress').textContent,/0\/2/);
  assert.match(m.get('fields').innerHTML,/UNIT TEXT 0/);
  assert.match(m.get('fields').innerHTML,/Thêm ít nhất một nguồn/);
  assert.equal(m.get('image').src,'../frozen/images/0.png');
  m.get('export-review').onclick();
  assert.equal(m.downloads.length,0);
  assert.match(m.get('message').textContent,/còn 2 trường/);
  m.get('export-partial').onclick();
  assert.equal(m.downloads.length,0);
  m.get('save').onclick();
  const saved=JSON.parse(m.local.get('resume-isolated'));
  assert.equal(saved.answers.F0.observed_transcript,'UNIT TEXT 0');
  assert.deepEqual(saved.answers.F0.sources,[]);
  assert.equal(m.local.has('document-review/'+packet.packet_id),false);
});

test('portable reviewer code is prefilled without attesting output exposure',()=>{
  const {packet}=fixture();
  const m=mount(packet,null,null,{reviewer_id:'R02',role:'external_reviewer'});
  assert.equal(m.get('profile-reviewer_id').value,'R02');
  assert.equal(m.get('profile-role').value,'external_reviewer');
  assert.equal(m.get('profile-output_exposure').value,'');
  m.get('export-review').onclick();
  assert.equal(m.downloads.length,0);
});

test('next-pending and page-select retain incomplete answers',()=>{
  const {packet,submission}=fixture(), m=mount(packet,submission);
  m.get('next-pending').onclick();
  assert.match(m.get('progress').textContent,/Ảnh 2\/2/);
  assert.match(m.get('fields').innerHTML,/UNIT TEXT 1/);
  m.get('page-select').onchange({target:{value:'0'}});
  assert.match(m.get('fields').innerHTML,/UNIT TEXT 0/);
});

test('new source is blank until reviewer explicitly reuses their own reading',()=>{
  const {packet,submission}=fixture(), m=mount(packet,submission);
  m.sections.get('F0').add.onclick();
  let saved=JSON.parse(m.local.get('resume-isolated'));
  assert.equal(saved.answers.F0.sources[0].observed_text,'');
  m.sections.get('F0').copy.onclick();
  saved=JSON.parse(m.local.get('resume-isolated'));
  assert.equal(saved.answers.F0.sources[0].observed_text,'UNIT TEXT 0');
  assert.equal(saved.answers.F0.sources[0].kind,'');
  assert.equal(saved.answers.F0.sources[0].location,'');
  assert.equal(core.progress(packet,saved).complete,0);
});

test('newer saved draft takes priority over embedded original and backup still exports',async()=>{
  const {packet,submission,state}=fixture();state.answers.F0.notes='newer user note';
  const m=mount(packet,submission,state);
  assert.match(m.get('fields').innerHTML,/newer user note/);
  m.get('export-draft').onclick();
  assert.equal(m.downloads.length,1);
  const backup=JSON.parse(await m.downloads[0].text());
  assert.equal(backup.mode,'unit_injected');
  assert.equal(backup.export_kind,'draft');
  assert.equal(backup.items[0].notes,'newer user note');
  assert.equal(backup.items.length,2);
});
