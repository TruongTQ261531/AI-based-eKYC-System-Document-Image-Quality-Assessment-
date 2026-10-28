// Unit tests of the shipped frontend with mocked DOM/media/network, no real camera.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');

function harness({secure = true, deny = false, pending = false} = {}) {
  const elements = new Map(), requests = [], constraints = [], canvases = [], streams = [], responses = [], timers = [];
  let releaseCamera;
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      id, value:'', hidden:false, disabled:false, textContent:'', listeners:{},
      videoWidth:2560, videoHeight:1440, naturalWidth:2560, naturalHeight:1440,
      classList:{toggle(){},add(){},remove(){}},
      children:[],replaceChildren(...children){this.children=children;},append(...children){this.children.push(...children);},
      setAttribute(){}, removeAttribute(name){delete this[name];},
      addEventListener(name, callback){this.listeners[name]=callback;},
      async play(){}, async decode(){},
      reset(){['full_name','id_number','dob','gender','address'].forEach(key=>element(key).value='');}
    });
    return elements.get(id);
  }
  function stream() {
    const track = {stopped:false,stop(){this.stopped=true;},getSettings(){return {facingMode:'environment'};},addEventListener(){}};
    const value={getTracks:()=>[track],getVideoTracks:()=>[track],track};
    streams.push(value); return value;
  }
  const document = {
    hidden:false,getElementById:element,querySelectorAll:()=>Array.from(elements.values()),addEventListener(){},
    createElement(tag){
      if(tag!=='canvas') return {textContent:'',children:[],append(...children){this.children.push(...children);}};
      const canvas={width:0,height:0,getContext(){return {drawImage(){}};},toBlob(fn){this.captured=[this.width,this.height];fn(new Blob(['photo'],{type:'image/jpeg'}));}};canvases.push(canvas);return canvas;
    }
  };
  const context=vm.createContext({document, navigator:{mediaDevices:{async getUserMedia(value){
    constraints.push(value);
    if(deny) throw Object.assign(new Error(),{name:'NotAllowedError'});
    if(pending) return new Promise(resolve=>{releaseCamera=()=>resolve(stream());});
    return stream();
  }}}, window:{isSecureContext:secure,addEventListener(){}},
    URL:{createObjectURL:()=> 'blob:photo',revokeObjectURL(){}},Blob,FormData,AbortController,
    setTimeout(fn,delay){timers.push({fn,delay,cancelled:false});return timers.length;},clearTimeout(id){if(timers[id-1])timers[id-1].cancelled=true;},
    async fetch(url,options){requests.push({url,options});const next=responses.shift()||{};return {ok:!next.error,status:next.status||200,json:async()=>next};}
  });
  vm.runInContext(source,context);
  return {context,element,requests,constraints,canvases,streams,responses,release:()=>releaseCamera(),timers,
    async tick(delay){const timer=timers.find(t=>!t.cancelled&&t.delay===delay);assert.ok(timer);timer.cancelled=true;await timer.fn();},
    click:id=>element(id).listeners.click(),submit:()=>element('details-form').listeners.submit({preventDefault(){}})};
}

test('insecure origin and denied camera produce actionable errors without upload',async()=>{
  let h=harness({secure:false});await h.click('open-camera');
  assert.match(h.element('status').textContent,/localhost hoặc HTTPS/);assert.equal(h.constraints.length,0);
  h=harness({deny:true});await h.click('open-camera');
  assert.match(h.element('status').textContent,/chưa cho phép camera/);assert.equal(h.requests.length,0);
});

test('rear camera, full video resolution, preview then explicit confirmation',async()=>{
  const h=harness();await h.click('open-camera');
  assert.equal(h.constraints[0].video.facingMode.ideal,'environment');assert.equal(h.constraints[0].audio,false);
  await h.click('capture');
  assert.deepEqual(h.canvases[0].captured,[2560,1440]);
  assert.equal(h.requests.length,0);assert.equal(h.element('preview').hidden,false);
  assert.equal(h.streams[0].track.stopped,true);
  h.responses.push({status:'retake',reason:'quality_rejected'});await h.click('confirm-photo');
  assert.equal(h.requests[0].url,'/api/document');
  assert.match(h.element('status').textContent,/không đạt chất lượng/);
  assert.equal(h.element('open-camera').hidden,false);
});

test('reset cancels pending camera and stops a late permission response',async()=>{
  const h=harness({pending:true});const opening=h.click('open-camera');
  h.click('reset');h.release();await opening;
  assert.equal(h.streams[0].track.stopped,true);assert.equal(h.element('video').srcObject,null);
});

test('OCR edits are submitted and the front camera requires a challenge before selfie',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');
  h.responses.push({status:'review',session_token:'test-token',expires_in:600,fields:{full_name:'From OCR',id_number:'001234567890'}});
  await h.click('confirm-photo');
  assert.equal(h.element('form-panel').hidden,false);assert.equal(h.element('full_name').value,'From OCR');
  assert.equal(h.element('dob').value,'');assert.equal(h.element('gender').value,'');
  h.element('full_name').value='User correction';h.responses.push({status:'selfie_required'});await h.submit();
  const confirmation=h.requests.find(r=>r.url==='/api/confirm');
  assert.equal(JSON.parse(confirmation.options.body).full_name,'User correction');
  assert.equal(confirmation.options.headers['X-Session-Token'],'test-token');
  await h.click('open-camera');assert.equal(h.constraints.at(-1).video.facingMode.ideal,'user');
  assert.equal(h.element('capture').hidden,true);
  assert.equal(h.element('start-liveness').hidden,false);
  await h.click('capture');
  assert.match(h.element('status').textContent,/hoàn thành thử thách/);
  assert.equal(h.requests.filter(r=>r.url==='/api/selfie').length,0);
});

test('Vietnamese OCR autofills all fields and replaces old values on a new scan',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');
  const fields={full_name:'NGUYỄN THỊ ÁNH',id_number:'001234567890',dob:'1999-02-03',gender:'Nữ',address:'Phường Bến Nghé, Thành phố Hồ Chí Minh'};
  h.responses.push({status:'review',session_token:'test',expires_in:600,fields});
  await h.click('confirm-photo');
  for(const [key,value] of Object.entries(fields)) assert.equal(h.element(key).value,value);
  assert.match(h.element('status').textContent,/tự động điền/);
  await h.click('retake-document');
  await Promise.resolve();await Promise.resolve();
  await h.click('capture');
  h.responses.push({status:'review',session_token:'new',expires_in:600,fields:{full_name:'Tên khác'}});
  await h.click('confirm-photo');
  assert.equal(h.element('full_name').value,'Tên khác');assert.equal(h.element('address').value,'');
});

test('student card renders only observed fields, keeps raw OCR, and submits editable extra fields',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');
  h.responses.push({status:'review',session_token:'student',expires_in:600,can_match_selfie:true,
    fields:{full_name:'NGUYỄN VĂN AN'},additional_fields:{student_id:'HS0042',class_name:'12A1'},
    document_type:{key:'student_card',label:'Thẻ học sinh / sinh viên'},
    document_fields:[{key:'full_name',label:'Họ tên',value:'NGUYỄN VĂN AN'},
      {key:'student_id',label:'Mã học sinh',value:'HS0042'},{key:'class_name',label:'Lớp',value:'12A1'}],
    ocr_text:['THẺ HỌC SINH','Dòng chưa phân loại <img src=x>']});
  await h.click('confirm-photo');
  assert.equal(h.element('row-full_name').hidden,false);
  for(const key of ['id_number','dob','gender','address']) assert.equal(h.element('row-'+key).hidden,true);
  assert.match(h.element('document-kind').textContent,/Thẻ học sinh/);
  assert.equal(h.element('dynamic-fields').children.length,2);
  assert.match(h.element('ocr-text').textContent,/<img src=x>/);
  h.element('dynamic-fields').children[1].children[1].value='12A2';
  h.responses.push({status:'selfie_required'});await h.submit();
  const body=JSON.parse(h.requests.find(r=>r.url==='/api/confirm').options.body);
  assert.equal(body.additional_fields.class_name,'12A2');assert.equal(body.additional_fields.student_id,'HS0042');
  assert.equal(body.dob,undefined);assert.equal(body.id_number,undefined);
  await h.click('reset');assert.equal(h.element('ocr-text').textContent,'');
  assert.equal(h.element('dynamic-fields').children.length,0);
});

test('unknown card can show unassigned text without inventing required fields',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');
  h.responses.push({status:'review',session_token:'other',expires_in:600,can_match_selfie:false,
    fields:{},document_fields:[],ocr_text:['THẺ THƯ VIỆN','Một dòng chữ chưa có nhãn']});
  await h.click('confirm-photo');
  assert.equal(h.element('form-panel').hidden,false);assert.equal(h.element('ocr-text-panel').hidden,false);
  for(const key of ['full_name','id_number','dob','gender','address']) assert.equal(h.element('row-'+key).hidden,true);
  assert.equal(h.element('confirm-details').disabled,true);
});

async function selfieCamera(h) {
  await h.click('open-camera');await h.click('capture');
  h.responses.push({status:'review',session_token:'test',expires_in:600,fields:{}});
  await h.click('confirm-photo');h.responses.push({status:'selfie_required',liveness_required:true});
  await h.submit();await h.click('open-camera');
}

function livePacket(overrides={}) {
  return {status:'running',challenge_id:'challenge',frame_token:'nonce',next_sequence:0,
    instruction:'Chớp cả hai mắt',completed:0,total:4,expires_in:180,action:'blink',phase:'action',...overrides};
}

test('server challenge, preview confirmation and final result are required in order',async()=>{
  const h=harness();await selfieCamera(h);
  h.responses.push(livePacket(),livePacket({next_sequence:1,frame_token:'next',completed:1}));
  await h.click('start-liveness');
  assert.equal(h.element('capture').hidden,true);
  assert.equal(h.element('live-progress').max,4);
  assert.deepEqual(h.canvases.at(-1).captured,[960,540]);
  const frame=h.requests.find(r=>r.url==='/api/liveness/frame');
  assert.equal(frame.options.headers['X-Frame-Token'],'nonce');
  assert.equal(frame.options.headers['X-Frame-Sequence'],'0');
  h.responses.push(livePacket({status:'passed',completed:4,proof_expires_in:45,next_sequence:2}));
  await h.tick(150);
  assert.equal(h.element('capture').hidden,false);
  await h.click('capture');
  assert.deepEqual(h.canvases.at(-1).captured,[2560,1440]);
  assert.equal(h.requests.filter(r=>r.url==='/api/selfie').length,0);
  h.responses.push({status:'matched',matching:{cosine_similarity:.8,threshold:.363},liveness_checked:true,liveness_passed:true,identity_consistent:true,
    liveness:{completed_actions:['blink','turn_left','turn_right','nod'],identity_samples:6,pad:{passed:true,final_selfie_passed:true}}});
  await h.click('confirm-photo');
  assert.equal(h.element('result-panel').hidden,false);
  assert.equal(h.element('result-checks').children.length,6);
  assert.match(h.element('status').textContent,/Đã kiểm tra cử động/);
  assert.equal(h.element('full_name').value,'');
});

test('failed challenge cannot enable capture and cancelling invalidates server state',async()=>{
  const h=harness();await selfieCamera(h);
  h.responses.push(livePacket(),livePacket({status:'failed',instruction:'Có nhiều khuôn mặt.'}));
  await h.click('start-liveness');
  assert.match(h.element('status').textContent,/nhiều khuôn mặt/);
  assert.equal(h.element('capture').hidden,true);
  assert.equal(h.element('start-liveness').hidden,false);
  await h.click('capture');
  assert.equal(h.requests.filter(r=>r.url==='/api/selfie').length,0);
  await Promise.resolve();
  assert.ok(h.requests.some(r=>r.url==='/api/liveness'&&r.options.method==='DELETE'));
});

test('timeout shows an ended timer instead of contradictory remaining seconds',async()=>{
  const h=harness();await selfieCamera(h);
  h.responses.push(livePacket(),livePacket({status:'failed',completed:3,expires_in:0,
    reason:'challenge_timeout',instruction:'Hết thời gian thực hiện.'}));
  await h.click('start-liveness');
  assert.equal(h.element('live-progress').max,4);
  assert.match(h.element('live-progress-label').textContent,/3\/4 động tác · Đã hết thời gian/);
  assert.doesNotMatch(h.element('live-progress-label').textContent,/Còn/);
});

test('spoof on final photo clears the photo and requires a new challenge',async()=>{
  const h=harness();await selfieCamera(h);
  h.responses.push(livePacket(),livePacket({status:'passed',completed:4,proof_expires_in:45}));
  await h.click('start-liveness');await h.click('capture');
  h.responses.push({error:true,status:403,detail:'Từ chối: khuôn mặt qua màn hình.',liveness_invalidated:true});
  await h.click('confirm-photo');
  assert.match(h.element('status').textContent,/Từ chối/);
  assert.equal(h.element('preview').hidden,true);assert.equal(h.element('confirm-photo').hidden,true);
  assert.equal(h.element('open-camera').hidden,false);assert.equal(h.element('capture').hidden,true);
});

test('frame spoof rejection is displayed before any selfie can be submitted',async()=>{
  const h=harness();await selfieCamera(h);
  h.responses.push(livePacket(),livePacket({status:'failed',reason:'spoof_detected',
    instruction:'Từ chối: có dấu hiệu khuôn mặt qua màn hình.',pad:{decision:'spoof'}}));
  await h.click('start-liveness');
  assert.match(h.element('live-pad').textContent,/Từ chối/);
  assert.equal(h.element('capture').hidden,true);
  assert.equal(h.requests.filter(r=>r.url==='/api/selfie').length,0);
});

test('retake discards captured image and opens a fresh stream',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');await h.click('retake');
  assert.equal(h.streams.length,2);assert.equal(h.element('preview').hidden,true);assert.equal(h.requests.length,0);
});

test('a failed capture displays backend diagnosis and concrete instructions',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');
  h.responses.push({status:'retake',reason:'quality_rejected',issues:[{
    title:'Ảnh có dấu hiệu bị mờ',detail:'Thiếu chi tiết.',instructions:['Giữ điện thoại đứng yên.','Lau ống kính.']
  }]});
  await h.click('confirm-photo');
  assert.equal(h.element('feedback-panel').hidden,false);
  assert.match(h.element('status').textContent,/bị mờ/);
  const block=h.element('feedback-items').children[0];
  assert.equal(block.children[2].children[0].textContent,'Giữ điện thoại đứng yên.');
  h.click('reset');assert.equal(h.element('feedback-panel').hidden,true);
});

test('missing portrait keeps OCR form but blocks selfie and offers a fresh document capture',async()=>{
  const h=harness();await h.click('open-camera');await h.click('capture');
  h.responses.push({status:'review',session_token:'test',expires_in:600,
    fields:{full_name:'OCR available'},can_match_selfie:false,issues:[]});
  await h.click('confirm-photo');
  assert.equal(h.element('form-panel').hidden,false);
  assert.equal(h.element('full_name').value,'OCR available');
  assert.equal(h.element('confirm-details').disabled,true);
  await h.submit();
  assert.equal(h.requests.filter(r=>r.url==='/api/confirm').length,0);
  h.click('retake-document');
  assert.equal(h.element('form-panel').hidden,true);
  assert.equal(h.element('full_name').value,'');
  assert.ok(h.requests.some(r=>r.url==='/api/session'&&r.options.method==='DELETE'));
});
