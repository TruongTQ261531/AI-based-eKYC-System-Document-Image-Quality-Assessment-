// Camera/network/DOM are simulated; these are behavior tests, not OCR accuracy.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const web=process.env.OCR_TEST_WEB==='v3'?'v3_web':'v2_web';
const source=fs.readFileSync(path.join(__dirname,'..',web,'app.js'),'utf8');
function harness({deny=false,pendingCamera=false,pendingScan=false,recommended=true}={}){
 const elements=new Map(),requests=[],streams=[],constraints=[],canvases=[],revoked=[],events={};let releaseCamera,releaseScan,answer=null;
 function make(id=''){return {id,value:'',checked:false,hidden:false,disabled:false,textContent:'',children:[],listeners:{},dataset:{},videoWidth:2560,videoHeight:1440,
  classList:{toggle(){}},replaceChildren(...x){this.children=x},append(...x){this.children.push(...x)},removeAttribute(x){delete this[x]},addEventListener(k,f){this.listeners[k]=f},async play(){},
  querySelectorAll(q){return this.children.flatMap(x=>[...x.children.filter(c=>c.name!==undefined),...x.querySelectorAll(q)])}}}
 function element(id){if(!elements.has(id))elements.set(id,make(id));return elements.get(id)}
 const demos=['full','field_clip','value_mask'].map(demo=>Object.assign(make(),{dataset:{demo}}));
 const document={getElementById:element,querySelectorAll:q=>q==='[data-demo]'?demos:[...elements.values(),...demos],createElement(tag){if(tag!=='canvas')return make();const c={getContext:()=>({drawImage(){}}),toBlob(fn,type){this.captured=[this.width,this.height];fn(new Blob(['MOCK'],{type}))}};canvases.push(c);return c}};
 function stream(){const track={stopped:false,stop(){this.stopped=true}};const s={track,getTracks:()=>[track]};streams.push(s);return s}
 const context=vm.createContext({document,isSecureContext:true,window:{addEventListener:(k,f)=>events[k]=f},navigator:{mediaDevices:{async getUserMedia(c){constraints.push(c);if(deny)throw Object.assign(Error(),{name:'NotAllowedError'});if(pendingCamera)return new Promise(r=>releaseCamera=()=>r(stream()));return stream()}}},Blob,AbortController,URL:{createObjectURL:()=> 'blob:mock',revokeObjectURL:u=>revoked.push(u)},setInterval(){},
 async fetch(url,options){requests.push({url,options});if(url==='/api/health')return {json:async()=>({ready:true,recommended,message:'Ready'})};if(url.startsWith('/api/specimen/'))return {ok:true,blob:async()=>new Blob(['SPECIMEN'],{type:'image/png'})};const response=()=>({ok:!answer?.error,json:async()=>answer});if(pendingScan)return new Promise(r=>releaseScan=()=>r(response()));return response()}});
 vm.runInContext(source,context);
 return {element,requests,streams,constraints,canvases,revoked,events,demos,releaseCamera:()=>releaseCamera(),releaseScan:()=>releaseScan(),respond:x=>answer=x,click:id=>element(id).listeners.click()};
}
const answer=()=>({fields:{student_id:'DEMO001',dob:'01/02/2000'},warnings:[],model:'partial_42',profile:'rect4',inference_seconds:.5,source_dimensions:[1200,800]});
test('captures native resolution and does not POST before confirmation',async()=>{
 const h=harness();await h.click('open-camera');await h.click('capture');
 assert.equal(h.constraints[0].audio,false);assert.equal(h.constraints[0].video.facingMode.ideal,'environment');
 assert.deepEqual(h.canvases[0].captured,[2560,1440]);assert.equal(h.streams[0].track.stopped,true);
 assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,0);
});
test('late permission is stopped after reset',async()=>{
 const h=harness({pendingCamera:true});const opening=h.click('open-camera');await h.click('clear');h.releaseCamera();await opening;
 assert.equal(h.streams[0].track.stopped,true);assert.equal(h.element('video').srcObject,null);
});
test('camera permission denial provides a useful message',async()=>{
 const h=harness({deny:true});await h.click('open-camera');assert.match(h.element('status').textContent,/quyền camera/);
});
test('fills only returned fields, keeps dates editable and marks edits manual',async()=>{
 const h=harness();await h.demos[0].listeners.click();h.respond(answer());await h.click('submit');
 const inputs=h.element('fields').children.map(x=>x.children[1]);assert.equal(inputs.length,2);
 assert.equal(inputs.find(x=>x.name==='id_number'),undefined);assert.equal(inputs.find(x=>x.name==='dob').value,'01/02/2000');
 assert.equal(inputs[0].dataset.source,'model');await h.click('confirm');inputs[0].listeners.input();
 assert.equal(inputs[0].dataset.source,'manual');assert.equal(h.element('confirmed').hidden,true);
});
test('unapproved model cannot POST until explicit opt-in',async()=>{
 const h=harness({recommended:false});await h.demos[0].listeners.click();h.respond(answer());await h.click('submit');
 assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,0);
 h.element('opt-in').checked=true;await h.click('submit');
 assert.equal(h.requests.find(r=>r.options?.method==='POST').options.headers['X-Research-Opt-In'],'yes');
});
test('manual additions are distinguished from OCR and duplicate names are rejected',async()=>{
 const h=harness();h.element('manual-key').value='Nơi cấp';h.element('manual-value').value='DEMO';await h.click('add-field');
 assert.equal(h.element('fields').children[0].children[1].dataset.source,'manual');
 h.element('manual-key').value='Nơi cấp';h.element('manual-value').value='OTHER';await h.click('add-field');assert.equal(h.element('fields').children.length,1);
});
test('clearing during an outstanding scan discards even a late response',async()=>{
 const h=harness({pendingScan:true});await h.demos[0].listeners.click();h.respond(answer());const scanning=h.click('submit');
 await h.click('clear');h.releaseScan();await scanning;assert.equal(h.element('fields').children.length,0);
 assert.equal(h.element('capture-preview').hidden,true);assert.equal(h.element('submit').disabled,false);
});
test('failed retry cannot leave old values to confirm; pagehide clears all data',async()=>{
 const h=harness();await h.demos[0].listeners.click();h.respond(answer());await h.click('submit');await h.click('confirm');
 h.respond({error:true,detail:'Temporary failure'});await h.click('submit');assert.equal(h.element('fields').children.length,0);assert.equal(h.element('confirmed').hidden,true);
 h.events.pagehide();assert.equal(h.element('manual-value').value,'');assert.ok(h.revoked.length);
});
