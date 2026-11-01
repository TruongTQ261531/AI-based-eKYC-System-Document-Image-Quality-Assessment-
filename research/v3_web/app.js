const $=id=>document.getElementById(id);
const labels={full_name:'Họ và tên',first_name:'Tên',last_name:'Họ',id_number:'Số giấy tờ',personal_number:'Số định danh cá nhân',dob:'Ngày sinh',gender:'Giới tính',address:'Địa chỉ',nationality:'Quốc tịch',birth_place:'Nơi sinh',issue_date:'Ngày cấp',expiry_date:'Ngày hết hạn',authority:'Cơ quan cấp',student_id:'Mã sinh viên',school:'Trường',course:'Khóa học',license_class:'Hạng giấy phép'};
let stream=null,photo=null,url=null,busy=false,generation=0,ready=false,recommended=false,pending=null;
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function stop(){stream?.getTracks().forEach(t=>t.stop());stream=null;$('video').srcObject=null;$('video').hidden=true;$('guide').hidden=true;}
function clearResult(){$('fields').replaceChildren();$('confirmed').hidden=true;$('confirm').hidden=true;$('empty-result').hidden=false;$('warnings').textContent='';$('timing').textContent='';$('manual-key').value='';$('manual-value').value='';}
function reset(){generation++;pending?.abort();pending=null;busy=false;stop();photo=null;if(url)URL.revokeObjectURL(url);url=null;$('capture-preview').removeAttribute('src');$('capture-preview').hidden=true;$('empty-camera').hidden=false;clearResult();$('capture').hidden=true;$('submit').hidden=true;$('open-camera').hidden=false;$('resolution').textContent='Ảnh và thông tin đã được bỏ khỏi trang.';document.querySelectorAll('button').forEach(b=>b.disabled=false);}
function usePhoto(blob){photo=blob;if(url)URL.revokeObjectURL(url);url=URL.createObjectURL(blob);$('capture-preview').src=url;$('capture-preview').hidden=false;$('empty-camera').hidden=true;$('open-camera').hidden=true;$('capture').hidden=true;$('submit').hidden=false;}
function addField(key,value,manual=false){
 const label=document.createElement('label'),title=document.createElement('span');title.textContent=(labels[key]||key)+(manual?' · Bạn nhập':' · OCR');
 const input=document.createElement('input');input.type='text';input.value=String(value);input.name=key;input.autocomplete='off';input.dataset.source=manual?'manual':'model';
 input.addEventListener('input',()=>{input.dataset.source='manual';title.textContent=(labels[key]||key)+' · Bạn đã sửa';$('confirmed').hidden=true;status('Đã sửa thông tin; cần đối chiếu lại.');});
 label.append(title,input);$('fields').append(label);$('empty-result').hidden=true;$('confirm').hidden=false;
}
$('open-camera').addEventListener('click',async()=>{if(busy)return;reset();const current=++generation;try{
 if(!isSecureContext||!navigator.mediaDevices?.getUserMedia)throw Error('Camera cần localhost hoặc HTTPS.');
 const next=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:2560},height:{ideal:1440}}});
 if(current!==generation){next.getTracks().forEach(t=>t.stop());return;}stream=next;$('video').srcObject=next;$('video').hidden=false;$('empty-camera').hidden=true;$('guide').hidden=false;$('open-camera').hidden=true;$('capture').hidden=false;await $('video').play();status('Giữ rõ chữ rồi bấm Chụp ảnh.');
 }catch(e){if(current!==generation)return;stop();status(e.name==='NotAllowedError'?'Chưa có quyền camera. Cho phép camera rồi thử lại.':e.name==='NotReadableError'?'Camera đang bận; đóng ứng dụng đang dùng camera.':e.name==='NotFoundError'?'Không tìm thấy camera.':e.message,true);}});
$('capture').addEventListener('click',async()=>{const v=$('video');if(!v.videoWidth||!v.videoHeight){status('Camera chưa sẵn sàng.',true);return;}const current=generation,c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',.96));if(!blob||current!==generation)return;stop();usePhoto(blob);$('resolution').textContent=`Ảnh gốc ${c.width} × ${c.height} pixel. Chưa gửi.`;status('Kiểm tra ảnh rồi Xác nhận & đọc.');});
$('clear').addEventListener('click',()=>{reset();status('Đã xóa ảnh và thông tin.');});
document.querySelectorAll('[data-demo]').forEach(b=>b.addEventListener('click',async()=>{if(busy)return;reset();const current=generation;try{const r=await fetch('/api/specimen/'+b.dataset.demo,{cache:'no-store'});if(!r.ok)throw Error('Chưa có ảnh mẫu.');const blob=await r.blob();if(current!==generation)return;usePhoto(blob);$('resolution').textContent='SPECIMEN thuộc tập train. Chỉ kiểm tra giao diện; không phải kết quả test.';status('Xác nhận để chạy model thật.');}catch(e){if(current===generation)status(e.message,true);}}));
$('submit').addEventListener('click',async()=>{
 if(busy||!photo)return;if(!ready){status('Model chưa hoàn tất audit.',true);return;}if(!recommended&&!$('opt-in').checked){status('V3 chưa vượt cổng development. Hãy đọc trạng thái và chủ động chọn chế độ nghiên cứu nếu muốn thử.',true);return;}
 clearResult();busy=true;const current=generation,controller=new AbortController();pending=controller;
 document.querySelectorAll('button:not(#clear)').forEach(b=>b.disabled=true);status('Đang đọc ảnh trên máy…');
 try{const r=await fetch('/api/scan',{method:'POST',headers:{'Content-Type':photo.type,'X-Research-Opt-In':$('opt-in').checked?'yes':'no'},body:photo,cache:'no-store',signal:controller.signal});const result=await r.json();if(current!==generation)return;if(!r.ok)throw Error(result.detail||'Không đọc được ảnh.');
 for(const [key,value] of Object.entries(result.fields))addField(key,value);
 $('warnings').textContent=result.warnings.join(' ');$('timing').textContent=`${result.model} · ${result.profile} · ${result.inference_seconds.toFixed(2)}s · ${result.source_dimensions.join(' × ')} pixel`;
 status(Object.keys(result.fields).length?'Đọc xong. Đối chiếu từng trường trước khi xác nhận.':'Chưa đọc được trường nào. Chụp gần hơn, tránh lóa hoặc tự nhập thông tin đã đối chiếu.',!Object.keys(result.fields).length);
 }catch(e){if(current===generation&&e.name!=='AbortError')status(e.message,true);}
 finally{if(current===generation){busy=false;pending=null;document.querySelectorAll('button').forEach(b=>b.disabled=false);}}
});
$('add-field').addEventListener('click',()=>{if(busy)return;const key=$('manual-key').value.trim(),value=$('manual-value').value.trim();if(!key||!value){status('Nhập tên trường và giá trị đã đối chiếu.',true);return;}const same=[...$('fields').querySelectorAll('input')].find(i=>i.name===key);if(same){status('Trường này đã có; hãy sửa trực tiếp.',true);return;}addField(key,value,true);$('manual-key').value='';$('manual-value').value='';$('confirmed').hidden=true;status('Đã thêm thông tin do bạn nhập.');});
$('confirm').addEventListener('click',()=>{$('confirmed').hidden=false;status('Đã xác nhận trên trình duyệt, không gửi thêm dữ liệu.');});
window.addEventListener('pagehide',reset);
async function health(){try{const r=await(await fetch('/api/health',{cache:'no-store'})).json();ready=r.ready;recommended=r.recommended;$('ready-state').textContent=ready?(recommended?'V3 sẵn sàng':'V3 chỉ để nghiên cứu'):'Đang chuẩn bị V3';$('model-state').textContent=r.message;if(r.progress){const p=r.progress;$('progress-state').textContent=`Huấn luyện ${p.training_completed}/${p.training_total} lượt · Tập phát triển ${p.development_completed}/${p.development_total} lượt đọc · Test cuối ${p.test_completed}/${p.test_total} lượt đọc.`;}$('opt-in-label').hidden=!ready||recommended;if(!photo&&!stream&&!busy)status(r.message);}catch{status('Chưa kết nối được máy chủ.',true);}}
health();setInterval(health,30000);
