// Isolated synthetic form: never POST mock answers to the human review service.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../web/labels_review.js'),'utf8');
async function harness(post){
 const nodes=new Map(),requests=[];
 function make(){return {value:'',checked:false,disabled:false,textContent:'',dataset:{},children:[],listeners:{},classList:{toggle(){}},append(...x){this.children.push(...x)},replaceChildren(...x){this.children=x},addEventListener(k,f){this.listeners[k]=f},setAttribute(){},removeAttribute(){},scrollIntoView(){},focus(){this.focused=true;}};}
 function el(id){if(!nodes.has(id))nodes.set(id,make());return nodes.get(id);}
 const c=vm.createContext({document:{getElementById:el,createElement:make,createElementNS:make},URLSearchParams,fetch:async(url,options)=>{
  if(options?.method==='POST'){requests.push({url,payload:JSON.parse(options.body)});return post?post():{ok:true,json:async()=>({saved:true})};}
  return {ok:true,json:async()=>url==='/api/health'?{corpus_images:21050,evaluation_images:304,review:{}}:{items:[],total:0}};
 }});
 vm.runInContext(source,c);await new Promise(r=>setImmediate(r));
 const status=make(),text=make(),card=make();card.dataset.fieldId='f1';card.querySelector=s=>s.includes('status')?status:text;card.querySelectorAll=()=>[];
 el('fields').children=[card];el('reviewer').value='MOCK_TEST';el('languages').value='vi';status.value='readable';text.value='SYNTHETIC TEST';
 vm.runInContext("state.sample={id:'fake',fields:[{field_id:'f1',raw_key:'full_name',semantic_key:'full_name',polygon:[[0,0],[1,0],[1,1]]}]};state.mode='blind';state.blindIds=['fake','other'];",c);
 return {el,status,text,requests,submit:()=>el('review').listeners.submit({preventDefault(){}}),clear:()=>vm.runInContext('state.sample=null',c)};
}
test('missing sample explains why saving cannot run',async()=>{const h=await harness();h.clear();await h.submit();assert.equal(h.requests.length,0);assert.match(h.el('saveStatus').textContent,/Chưa chọn mẫu/);});
test('missing status and missing observed text name the exact field beside Save',async()=>{const h=await harness();h.status.value='';await h.submit();assert.equal(h.requests.length,0);assert.match(h.el('saveStatus').textContent,/Họ và tên.*chưa chọn trạng thái/);assert.equal(h.status.focused,true);h.status.value='readable';h.text.value='';await h.submit();assert.match(h.el('saveStatus').textContent,/Họ và tên.*ghi phần chữ/);assert.equal(h.text.focused,true);});
test('unreadable with guessed text is rejected without silently clearing user input',async()=>{const h=await harness();h.status.value='unreadable';await h.submit();assert.equal(h.requests.length,0);assert.equal(h.text.value,'SYNTHETIC TEST');assert.match(h.el('saveStatus').textContent,/cần để trống/);});
test('successful save is visible beside the button and unchanged re-click does not create another event',async()=>{const h=await harness();h.el('notes').value='MOCK NOTE';await h.submit();assert.equal(h.requests.length,1);assert.equal(h.requests[0].payload.notes,'MOCK NOTE');assert.equal(h.requests[0].payload.items[0].text,'SYNTHETIC TEST');assert.match(h.el('saveStatus').textContent,/ĐÃ LƯU/);assert.equal(h.el('save').disabled,true);assert.equal(h.el('nextTask').disabled,false);await h.submit();assert.equal(h.requests.length,1);});
test('double click while request is pending creates only one request',async()=>{let release;const h=await harness(()=>new Promise(r=>release=r));const first=h.submit();assert.equal(h.el('save').disabled,true);await h.submit();assert.equal(h.requests.length,1);release({ok:true,json:async()=>({saved:true})});await first;assert.match(h.el('saveStatus').textContent,/ĐÃ LƯU/);});
test('network error keeps draft and allows a retry; editing saved text allows a new revision',async()=>{const h=await harness(async()=>{throw Error('mock network failure');});await h.submit();assert.equal(h.text.value,'SYNTHETIC TEST');assert.equal(h.el('save').disabled,false);assert.match(h.el('saveStatus').textContent,/Chưa lưu được.*mock network failure/);const good=await harness();await good.submit();good.text.value='REVISED TEST';good.el('review').listeners.input();assert.equal(good.el('save').disabled,false);assert.equal(good.el('nextTask').disabled,true);await good.submit();assert.equal(good.requests.length,2);});
