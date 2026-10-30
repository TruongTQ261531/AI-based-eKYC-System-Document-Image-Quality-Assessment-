// Research frontend tests: mocked camera/DOM/network, never real personal data.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');

function harness({deny=false,pending=false}={}){
 const elements=new Map(),requests=[],constraints=[],streams=[],canvases=[],revoked=[];let release,answer=null;
 function make(id='') {return {id,value:'',hidden:false,disabled:false,textContent:'',children:[],listeners:{},videoWidth:2560,videoHeight:1440,
  classList:{toggle(){}},replaceChildren(...x){this.children=x;},append(...x){this.children.push(...x);},removeAttribute(x){delete this[x];},
  addEventListener(k,f){this.listeners[k]=f;},async play(){}};}
 function element(id){if(!elements.has(id))elements.set(id,make(id));return elements.get(id);}
 const demos=['full','corner_clip','field_clip','blur_glare'].map(kind=>Object.assign(make(),{dataset:{demo:kind}}));
 const document={getElementById:element,querySelectorAll:selector=>selector==='[data-demo]'?demos:[...elements.values(),...demos],
  createElement(tag){if(tag!=='canvas')return make();const canvas={getContext:()=>({drawImage(){}}),toBlob(fn,type){this.captured=[this.width,this.height];fn(new Blob(['test-photo'],{type}));}};canvases.push(canvas);return canvas;}};
 function stream(){const track={stopped:false,stop(){this.stopped=true;}};const s={getTracks:()=>[track],track};streams.push(s);return s;}
 const context=vm.createContext({document,window:{isSecureContext:true,addEventListener(){}},navigator:{mediaDevices:{async getUserMedia(c){constraints.push(c);if(deny)throw Object.assign(new Error(),{name:'NotAllowedError'});if(pending)return new Promise(resolve=>release=()=>resolve(stream()));return stream();}}},
  Blob,URL:{createObjectURL:()=> 'blob:test-photo',revokeObjectURL:x=>revoked.push(x)},setInterval(){},
  async fetch(url,options){requests.push({url,options});if(url==='/api/health')return {json:async()=>({completed:0,expected:588,selector_ready:false})};if(url==='/api/results')return {json:async()=>({status:'running',message:'Pending'})};if(url.startsWith('/api/specimen/'))return {ok:true,blob:async()=>new Blob(['specimen'],{type:'image/png'})};return {ok:!answer?.error,json:async()=>answer};}});
 vm.runInContext(source,context);
 return {element,requests,constraints,streams,canvases,revoked,demos,release:()=>release(),respond:value=>answer=value,click:id=>element(id).listeners.click()};
}

test('research camera preserves source resolution and waits for explicit upload',async()=>{
 const h=harness();await h.click('open-camera');await h.click('capture');
 assert.equal(h.constraints[0].video.facingMode.ideal,'environment');assert.equal(h.constraints[0].audio,false);
 assert.deepEqual(h.canvases[0].captured,[2560,1440]);assert.equal(h.streams[0].track.stopped,true);
 assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,0);assert.equal(h.element('submit').hidden,false);
});

test('late camera permission cannot reactivate camera after reset',async()=>{
 const h=harness({pending:true});const opening=h.click('open-camera');await h.click('clear');h.release();await opening;
 assert.equal(h.streams[0].track.stopped,true);assert.equal(h.element('video').srcObject,null);
});

test('camera denial is actionable and never submits a photo',async()=>{
 const h=harness({deny:true});await h.click('open-camera');
 assert.match(h.element('status').textContent,/cấp quyền camera/);assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,0);
});

test('observed student fields are editable without invented CCCD fields',async()=>{
 const h=harness();await h.demos[0].listeners.click();
 h.respond({fields:{student_id:'MOCK42',dob:'2000-11-12'},field_labels:{student_id:'Student ID'},warnings:[],predictions:[{text:'<script>TEST</script>'}],
  selected_policy:'raw',actual_wall_seconds:.2,request_processing_wall_seconds:.3,ocr_executions:1,source_dimensions:[1000,640],reader:'rapid_latin_v5',preview_data_url:'data:image/jpeg;base64,AA',review_recommended:false});
 await h.click('submit');const inputs=h.element('fields').children.map(label=>label.children[0]);
 assert.equal(inputs.length,2);assert.equal(inputs.find(x=>x.name==='id_number'),undefined);
 assert.equal(inputs.find(x=>x.name==='student_id').value,'MOCK42');assert.equal(inputs.find(x=>x.name==='dob').type,'date');
 inputs[0].value='Corrected';const posts=h.requests.filter(r=>r.options?.method==='POST').length;await h.click('confirm-fields');
 assert.equal(h.requests.filter(r=>r.options?.method==='POST').length,posts);assert.equal(h.element('ocr-text').textContent,'<script>TEST</script>');
 await h.click('clear');assert.equal(h.element('fields').children.length,0);assert.ok(h.revoked.length>0);
});

test('backend unavailability leaves a retake path and no fabricated form',async()=>{
 const h=harness();await h.demos[1].listeners.click();h.respond({error:true,detail:'Model not locked'});await h.click('submit');
 assert.equal(h.element('fields').children.length,0);assert.equal(h.element('submit').disabled,false);assert.match(h.element('status').textContent,/Model not locked/);
});
