// Synthetic DOM/answers only. These checks never create human research labels.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../v3_review_web/app.js'),'utf8');
async function harness(){
 const nodes=new Map(),blobs=[],events={};
 function make(){const n={value:'',checked:false,disabled:false,textContent:'',children:[],listeners:{},append(...a){this.children.push(...a)},replaceChildren(...a){this.children=a},addEventListener(k,f){this.listeners[k]=f},setAttribute(){},click(){}};Object.defineProperty(n,'id',{set(v){this._id=v;nodes.set(v,this)},get(){return this._id}});return n;}
 const el=id=>{if(!nodes.has(id)){const n=make();n.id=id;}return nodes.get(id)};
 const spec={items:[{id:'case_001',file:'case_001.png',image_sha256:'a'.repeat(64)},{id:'case_002',file:'case_002.png',image_sha256:'b'.repeat(64)}],keys:['full_name','dob']};
 const context=vm.createContext({document:{getElementById:el,createElement:make},window:{addEventListener:(k,f)=>events[k]=f},fetch:async()=>({ok:true,json:async()=>spec}),Blob,URL:{createObjectURL:b=>{blobs.push(b);return 'blob:fake'},revokeObjectURL(){}},Date});
 vm.runInContext(source,context);await new Promise(r=>setImmediate(r));
 return {el,spec,blobs,click:id=>el(id).listeners.click(),set:(id,v)=>{el(id).value=v;return el(id).listeners.change?.()}};
}
test('starts with every field unreviewed, no value and no completed answer',async()=>{const h=await harness();assert.match(h.el('count').textContent,/0\/2/);assert.equal(h.el('s-full_name').value,'');assert.equal(h.el('v-full_name').value,'');assert.equal(h.el('v-full_name').disabled,true);});
test('cannot mark incomplete form as a completed human review',async()=>{const h=await harness();h.click('complete');assert.match(h.el('status').textContent,/đánh giá mọi trường/);assert.match(h.el('count').textContent,/0\/2/);});
test('changing a completed judgment invalidates completion and clears unreadable text',async()=>{const h=await harness();h.set('s-full_name','readable');h.el('v-full_name').value='FAKE TEST';h.set('s-dob','absent');h.click('complete');assert.match(h.el('count').textContent,/1\/2/);h.set('s-full_name','unreadable');assert.equal(h.el('v-full_name').value,'');h.click('next');assert.match(h.el('count').textContent,/0\/2/);});
test('partial export preserves hashes and does not invent blind attestation or completed labels',async()=>{const h=await harness();h.click('export');assert.equal(h.blobs.length,0);h.el('rater').value='MOCK_TEST';h.click('export');const data=JSON.parse(await h.blobs[0].text());assert.equal(data.rater_attests_no_model_output_access,false);assert.equal(data.answers.case_001.completed,false);assert.equal(data.answers.case_001.fields.full_name.text,'');assert.deepEqual(data.packet,h.spec.items.map(i=>({id:i.id,image_sha256:i.image_sha256})));});
test('import rejects wrong packet and cannot turn unanswered fields into completed labels',async()=>{const h=await harness();h.el('rater').value='MOCK_TEST';h.click('export');const data=JSON.parse(await h.blobs[0].text());data.answers.case_001.completed=true;h.el('import').files=[{text:async()=>JSON.stringify(data)}];await h.el('import').listeners.change();assert.match(h.el('count').textContent,/0\/2/);data.packet[0].image_sha256='wrong';await h.el('import').listeners.change();assert.match(h.el('status').textContent,/bộ ảnh khác/);});
