(function(){
 'use strict';const P=window.BLIND_PACKET,C=window.BlindReviewCore;
 const storage={getItem:k=>window.localStorage.getItem(k),setItem:(k,v)=>window.localStorage.setItem(k,v)};
 const restored=C.restore(P,storage);let state=restored.state;let dirty=false;
 const $=id=>document.getElementById(id);
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const opts=(items,value)=>'<option value="">— Chưa chọn —</option>'+items.map(([v,t])=>`<option value="${v}" ${v===value?'selected':''}>${t}</option>`).join('');
 const avail=[['visible','Nhìn thấy đầy đủ giá trị'],['partial','Chỉ thấy một phần'],['not_seen','Không thấy giá trị'],['uncertain','Chưa chắc']];
 const readable=[['readable','Đọc rõ toàn bộ'],['partial','Đọc được một phần'],['unreadable','Không đọc được'],['uncertain','Chưa chắc'],['language_unknown','Không biết ngôn ngữ hoặc ký tự'],['unassessed','Chưa đánh giá mức đọc được']];
 const kinds=[['body','Nội dung chính trên thẻ'],['duplicated_body','Một vị trí lặp lại trên thẻ'],['mrz','Dòng máy đọc MRZ'],['other','Nguồn khác'],['uncertain','Chưa xác định']];
 function note(message,bad=false){$('message').textContent=message;$('message').className=bad?'message error':'message';}
 function persist(){const r=C.saveDraft(state,storage);if(r.saved)dirty=false;note(r.message,!r.saved);update();return r;}
 function update(){const p=C.progress(P,state);$('progress').textContent=`Ảnh ${state.page+1}/${P.pages.length} · ${p.complete}/${p.total} trường đủ thông tin · ${p.touched} trường đã ghi nháp`;
   $('previous').disabled=state.page===0;$('next').disabled=state.page===P.pages.length-1;}
 function answer(slot){if(!state.answers[slot])state.answers[slot]=C.blank();return state.answers[slot];}
 function sourceRow(slot,s,index){return `<div class="source" data-source="${index}"><label>Loại nguồn<select data-key="kind">${opts(kinds,s.kind)}</select></label>
   <label>Vị trí bạn quan sát<input data-key="location" value="${esc(s.location)}" placeholder="Ví dụ: góc trên bên phải, dòng thứ hai"></label>
   <div class="grid"><label>Tình trạng nguồn<select data-key="availability">${opts(avail,s.availability)}</select></label>
   <label>Mức đọc ở nguồn<select data-key="readability">${opts(readable,s.readability)}</select></label></div>
   <label>Chữ nhìn thấy tại nguồn này<textarea data-key="observed_text" rows="2">${esc(s.observed_text)}</textarea></label>
   <details><summary>Nếu là MRZ: chép cả dòng khi đọc được (tùy chọn)</summary><label>Dòng 1<textarea data-key="mrz_line_1" rows="2">${esc(s.mrz_line_1)}</textarea></label><label>Dòng 2<textarea data-key="mrz_line_2" rows="2">${esc(s.mrz_line_2)}</textarea></label></details>
   <button class="secondary remove-source" type="button" data-index="${index}">Bỏ nguồn nhập nhầm</button></div>`;}
 function render(){state.page=Math.max(0,Math.min(P.pages.length-1,state.page));const page=P.pages[state.page];
   $('image').src=page.image;$('image').alt='Ảnh giả lập cần đánh giá';$('full-image').href=page.image;
   $('image-code').textContent=page.image_id;
   $('fields').innerHTML=page.fields.map(f=>{const a=answer(f.slot_id);return `<section class="field" data-slot="${f.slot_id}"><h2>${esc(f.label)}</h2>
    <p class="muted">Trường này có thể không xuất hiện. Chỉ chép từ ảnh đang xem, không bổ sung theo trí nhớ hoặc ảnh khác.</p>
    <div class="grid"><label>Tình trạng giá trị<select data-key="availability">${opts(avail,a.availability)}</select></label><label>Mức đọc được<select data-key="readability">${opts(readable,a.readability)}</select></label>
    <label>Có xác định được ý nghĩa trường này không?<select data-key="semantic_key_confirmed">${opts([['yes','Có'],['no','Không'],['uncertain','Chưa chắc']],a.semantic_key_confirmed)}</select></label>
    <label>Bạn đã biết ảnh hoặc giá trị này từ trước?<select data-key="prior_exposure">${opts([['no','Chưa'],['yes','Đã biết'],['uncertain','Không chắc']],a.prior_exposure)}</select></label></div>
    <label>Bản chép chữ bạn thực sự đọc được<textarea data-key="observed_transcript" rows="2">${esc(a.observed_transcript)}</textarea></label>
    <div class="sources">${a.sources.map((s,i)=>sourceRow(f.slot_id,s,i)).join('')}</div><button type="button" class="secondary add-source">Thêm nguồn chữ quan sát được</button>
    <label>Ghi chú / phần chưa chắc<textarea data-key="notes" rows="2">${esc(a.notes)}</textarea></label><div class="validation" aria-live="polite"></div></section>`;}).join('');
   for(const section of $('fields').querySelectorAll('.field')){
    const slot=section.dataset.slot;
    const storeEdit=e=>{const key=e.target.dataset.key;if(!key)return;const a=answer(slot);a.touched=true;dirty=true;
      const source=e.target.closest('[data-source]');if(source)a.sources[Number(source.dataset.source)][key]=e.target.value;else a[key]=e.target.value;update();};
    section.addEventListener('input',storeEdit);
    section.addEventListener('change',e=>{storeEdit(e);section.querySelector('.validation').textContent=C.observationErrors(answer(slot)).join(' ');});
    section.querySelector('.add-source').onclick=()=>{const a=answer(slot);a.touched=true;dirty=true;a.sources.push({kind:'',location:'',availability:'',readability:'',observed_text:'',mrz_line_1:'',mrz_line_2:''});persist();render();};
    for(const button of section.querySelectorAll('.remove-source'))button.onclick=()=>{answer(slot).sources.splice(Number(button.dataset.index),1);persist();render();};
   }
   update();
 }
 for(const key of ['reviewer_id','role','output_exposure']){const element=$('profile-'+key);element.value=state.profile[key]||'';
   element.oninput=element.onchange=()=>{state.profile[key]=element.value;dirty=true;};}
 $('save').onclick=()=>{persist();for(const section of $('fields').querySelectorAll('.field'))section.querySelector('.validation').textContent=C.observationErrors(answer(section.dataset.slot)).join(' ');};
 $('previous').onclick=()=>{persist();state.page--;render();window.scrollTo(0,0);};
 $('next').onclick=()=>{persist();state.page++;render();window.scrollTo(0,0);};
 function download(finalize){const result=C.exportReview(P,state,finalize);if(result.errors){note(result.errors.join(' '),true);return;}
   const blob=new Blob([JSON.stringify(result.value,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);
   const a=document.createElement('a');a.href=url;a.download='review-'+(state.profile.reviewer_id||'draft').replace(/[^A-Za-z0-9_-]/g,'-')+'-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
   note('Đã yêu cầu tải file JSON. Kiểm tra thư mục Downloads của trình duyệt; đây chưa phải kết quả đã xác minh độc lập.');}
 $('export-draft').onclick=()=>download(false);$('export-review').onclick=()=>download(true);
 $('restore-backup').onchange=async event=>{
   const file=event.target.files[0];event.target.value='';if(!file)return;
   try{
     const imported=C.restoreBackup(P,JSON.parse(await file.text()));
     if(Object.values(state.answers).some(a=>a.touched)&&!window.confirm('Nạp file sẽ thay bản đang mở. Tiếp tục nếu bạn đã xuất bản sao cần giữ.'))return;
     state=imported;dirty=true;
     for(const key of Object.keys(state.profile))$('profile-'+key).value=state.profile[key];
     render();persist();
   }catch(error){note(error.message||'Không đọc được file phiếu.',true);}
 };
 window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
 render();if(restored.warning)note(restored.warning,true);
})();
