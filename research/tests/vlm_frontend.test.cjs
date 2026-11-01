// Mocked camera/DOM/network. No real camera or identity data is used.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../vlm_web/app.js'),'utf8');
function harness({deny=false,pending=false}={}){
 const elements=new Map(),requests=[],streams=[],constraints=[],canvases=[],revoked=[],events={};let release,answer=null;
 function make(id=''){return {id,value:'',hidden:false,disabled:false,textContent:'',children:[],listeners:{},videoWidth:2560,videoHeight:1440,
  classList:{toggle(){}},replaceChildren(...x){this.children=x},append(...x){this.children.push(...x)},removeAttribute(x){delete this[x]},addEventListener(k,f){this.listeners[k]=f},async play(){}}}
 function element(id){if(!elements.has(id))elements.set(id,make(id));return elements.get(id)}
 const demos=['full','field_clip','value_mask'].map(demo=>Object.assign(make(),{dataset:{demo}}));
 const document={getElementById:element,querySelectorAll:q=>q==='[data-demo]'?demos:[...elements.values(),...demos],createElement(tag){if(tag!=='canvas')return make();const c={getContext:()=>({drawImage(){}}),toBlob(fn,type){this.captured=[this.width,this.height];fn(new Blob(['MOCK'],{type}))}};canvases.push(c);return c}};
 function stream(){const track={stopped:false,stop(){this.stopped=true}};const s={track,getTracks:()=>[track]};streams.push(s);return s}
 const context=vm.createContext({document,isSecureContext:true,window:{addEventListener:(k,f)=>events[k]=f},navigator:{mediaDevices:{async getUserMedia(c){constraints.push(c);if(deny)throw Object.assign(Error(),{name:'NotAllowedError'});if(pending)return new Promise(r=>release=()=>r(stream()));return stream()}}},Blob,URL:{createObjectURL:()=> 'blob:mock',revokeObjectURL:u=>revoked.push(u)},setInterval(){},
 async fetch(url,options){requests.push({url,options});if(url==='/api/health')return {json:async()=>({ready:true,message:'Ready'})};if(url.startsWith('/api/specimen/'))return {ok:true,blob:async()=>new Blob(['SPECIMEN'],{type:'image/png'})};return {ok:!answer?.error,json:async()=>answer}}});
 vm.runInContext(source,context);
 return {element,requests,streams,constraints,canvases,revoked,events,demos,release:()=>release(),respond:x=>answer=x,click:id=>element(id).listeners.click()};
}
test('native-resolution camera capture waits for confirmation',async()=>{
 const h=harness();await h.click('open-camera');await h.click('capture');
 assert.equal(h.constraints[0].audio,false);assert.equal(h.constraints[0].video.facingMode.ideal,'environment');
 assert.deepEqual(h.canvases[0].captured,[2560,1440]);assert.equal(h.streams[0].track.stopped,true);
 assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,0);
});
test('late camera permission is stopped after reset',async()=>{
 const h=harness({pending:true});const opening=h.click('open-camera');await h.click('clear');h.release();await opening;
 assert.equal(h.streams[0].track.stopped,true);assert.equal(h.element('video').srcObject,null);
});
test('camera denial provides guidance',async()=>{
 const h=harness({deny:true});await h.click('open-camera');assert.match(h.element('status').textContent,/cấp quyền camera/);
});
test('only model fields appear, dates remain editable, edits invalidate confirmation',async()=>{
 const h=harness();await h.demos[0].listeners.click();h.respond({fields:{student_id:'MOCK001',dob:'01/02/2000'},warnings:[],model:'seed_42',inference_seconds:.5,source_dimensions:[1000,680]});
 await h.click('submit');const inputs=h.element('fields').children.map(x=>x.children[0]);
 assert.equal(inputs.length,2);assert.equal(inputs.find(x=>x.name==='id_number'),undefined);
 assert.equal(inputs.find(x=>x.name==='dob').value,'01/02/2000');assert.equal(inputs.find(x=>x.name==='dob').type,'text');
 const posts=h.requests.filter(r=>r.options?.method==='POST').length;await h.click('confirm');
 assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,posts);assert.equal(h.element('confirmed').hidden,false);
 inputs[0].listeners.input();assert.equal(h.element('confirmed').hidden,true);
 h.events.pagehide();assert.equal(h.element('fields').children.length,0);assert.ok(h.revoked.length);
});
test('unavailable model never fabricates fields',async()=>{
 const h=harness();await h.demos[0].listeners.click();h.respond({error:true,detail:'Model not approved'});await h.click('submit');
 assert.equal(h.element('fields').children.length,0);assert.match(h.element('status').textContent,/Model not approved/);assert.equal(h.element('submit').disabled,false);
});
test('failed retry cannot leave an old successful result to confirm',async()=>{
 const h=harness();await h.demos[0].listeners.click();h.respond({fields:{id_number:'MOCK'},warnings:[],model:'mock',inference_seconds:.1,source_dimensions:[100,70]});
 await h.click('submit');await h.click('confirm');assert.equal(h.element('fields').children.length,1);
 h.respond({error:true,detail:'Temporary failure'});await h.click('submit');
 assert.equal(h.element('fields').children.length,0);assert.equal(h.element('confirmed').hidden,true);assert.equal(h.element('confirm').hidden,true);
});
