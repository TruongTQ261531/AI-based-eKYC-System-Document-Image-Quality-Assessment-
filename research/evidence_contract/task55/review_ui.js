(function(){
 'use strict';const P=window.BLIND_PACKET,C=window.BlindReviewCore;
 const storage={getItem:k=>window.localStorage.getItem(window.BLIND_REVIEW_STORAGE_KEY||k),setItem:(k,v)=>window.localStorage.setItem(window.BLIND_REVIEW_STORAGE_KEY||k,v)};
 const restored=C.restore(P,storage);let state=restored.state;let dirty=false;
 if(window.BLIND_REVIEW_PROFILE&&!state.profile.reviewer_id&&!Object.values(state.answers).some(a=>a.touched)){
   for(const key of ['reviewer_id','role'])state.profile[key]=window.BLIND_REVIEW_PROFILE[key]||'';
 }
 if(window.BLIND_REVIEW_RESUME&&!restored.warning&&!Object.values(state.answers).some(a=>a.touched)){
   state=C.restoreBackup(P,window.BLIND_REVIEW_RESUME);
   state.page=C.pendingSlots(P,state)[0]?.page||0;
 }
 const $=id=>document.getElementById(id);
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const opts=(items,value)=>'<option value="">— Chưa chọn —</option>'+items.map(([v,t])=>`<option value="${v}" ${v===value?'selected':''}>${t}</option>`).join('');
 const avail=[['visible','Nhìn thấy đầy đủ giá trị'],['partial','Chỉ thấy một phần'],['not_seen','Không thấy giá trị'],['uncertain','Chưa chắc']];
 const readable=[['readable','Đọc rõ toàn bộ'],['partial','Đọc được một phần'],['unreadable','Không đọc được'],['uncertain','Chưa chắc'],['language_unknown','Không biết ngôn ngữ hoặc ký tự'],['unassessed','Chưa đánh giá mức đọc được']];
 const kinds=[['body','Nội dung chính trên thẻ'],['duplicated_body','Một vị trí lặp lại trên thẻ'],['mrz','Dòng máy đọc MRZ'],['other','Nguồn khác'],['uncertain','Chưa xác định']];
 function note(message,bad=false){$('message').textContent=message;$('message').className=bad?'message error':'message';}
 function persist(){const r=C.saveDraft(state,storage);if(r.saved)dirty=false;note(r.message,!r.saved);update();return r;}
 function update(){const p=C.progress(P,state);$('progress').textContent=`Ảnh ${state.page+1}/${P.pages.length} · ${p.complete}/${p.total} trường đủ thông tin · ${p.touched} trường đã ghi nháp`;
   $('previous').disabled=state.page===0;$('next').disabled=state.page===P.pages.length-1;
   const pending=C.pendingSlots(P,state);
   $('pending-summary').textContent=pending.length?`Còn ${pending.length} trường cần bổ sung trên ${new Set(pending.map(s=>s.page)).size} ảnh. Phần bạn đã nhập được giữ nguyên.`:'Tất cả trường đã đủ thông tin để xuất phiếu. Đây là kiểm tra độ đầy đủ, chưa xác minh đúng/sai.';
   $('next-pending').disabled=!pending.length;
   const select=$('page-select');select.innerHTML=P.pages.map((page,i)=>{const n=pending.filter(s=>s.page===i).length;return `<option value="${i}" ${i===state.page?'selected':''}>Ảnh ${i+1}/${P.pages.length} · ${n?'còn '+n+' trường':'đủ thông tin'}</option>`;}).join('');}
 function answer(slot){if(!state.answers[slot])state.answers[slot]=C.blank();return state.answers[slot];}
 function sourceRow(slot,s,index){return `<div class="source" data-source="${index}"><label>Loại nguồn<select data-key="kind">${opts(kinds,s.kind)}</select></label>
   <label>Vị trí bạn quan sát<input data-key="location" value="${esc(s.location)}" placeholder="Ví dụ: góc trên bên phải, dòng thứ hai"></label>
   <div class="grid"><label>Tình trạng nguồn<select data-key="availability">${opts(avail,s.availability)}</select></label>
   <label>Mức đọc ở nguồn<select data-key="readability">${opts(readable,s.readability)}</select></label></div>
   <label>Chữ nhìn thấy tại nguồn này<textarea data-key="observed_text" rows="2">${esc(s.observed_text)}</textarea></label>
   <button class="secondary copy-field-source" type="button" data-index="${index}">Nguồn này có cùng chữ và mức đọc tôi đã nhập ở trên</button>
   <p class="muted">Chỉ bấm khi bạn đã kiểm tra nguồn này. Loại nguồn và vị trí vẫn cần bạn ghi nhận.</p>
   <details><summary>Nếu là MRZ: chép cả dòng khi đọc được</summary><p class="muted">Cần cả hai dòng để kiểm tra MRZ. Không đọc được thì giữ trống và chọn đúng mức đọc.</p><label>Dòng 1<textarea data-key="mrz_line_1" rows="2">${esc(s.mrz_line_1)}</textarea></label><label>Dòng 2<textarea data-key="mrz_line_2" rows="2">${esc(s.mrz_line_2)}</textarea></label></details>
   <button class="secondary remove-source" type="button" data-index="${index}">Bỏ nguồn nhập nhầm</button></div>`;}
 function render(){state.page=Math.max(0,Math.min(P.pages.length-1,state.page));const page=P.pages[state.page];
   const imagePath=(window.BLIND_IMAGE_PREFIX||'')+page.image;
   $('image').src=imagePath;$('image').alt='Ảnh giả lập cần đánh giá';$('full-image').href=imagePath;
   $('image-code').textContent=page.image_id;
   $('fields').innerHTML=page.fields.map(f=>{const a=answer(f.slot_id);return `<section class="field" data-slot="${f.slot_id}"><h2>${esc(f.label)}</h2>
    <div class="validation" aria-live="polite">${esc(C.observationErrors(a).join(' '))}</div>
    <p class="muted">Trường này có thể không xuất hiện. Chỉ chép từ ảnh đang xem, không bổ sung theo trí nhớ hoặc ảnh khác.</p>
    <div class="grid"><label>Tình trạng giá trị<select data-key="availability">${opts(avail,a.availability)}</select></label><label>Mức đọc được<select data-key="readability">${opts(readable,a.readability)}</select></label>
    <label>Có xác định được ý nghĩa trường này không?<select data-key="semantic_key_confirmed">${opts([['yes','Có'],['no','Không'],['uncertain','Chưa chắc']],a.semantic_key_confirmed)}</select></label>
    <label>Bạn đã biết ảnh hoặc giá trị này từ trước?<select data-key="prior_exposure">${opts([['no','Chưa'],['yes','Đã biết'],['uncertain','Không chắc']],a.prior_exposure)}</select></label></div>
    <label>Bản chép chữ bạn thực sự đọc được<textarea data-key="observed_transcript" rows="2">${esc(a.observed_transcript)}</textarea></label>
    <p class="source-help">Nếu nhìn thấy giá trị, cần ghi ít nhất một nguồn chữ: loại nguồn, vị trí và mức đọc. Ví dụ vị trí: “dòng cạnh nhãn Họ tên”. Bạn không cần vẽ khung. Nếu có nhiều vị trí thì thêm từng nguồn.</p>
    <div class="sources">${a.sources.map((s,i)=>sourceRow(f.slot_id,s,i)).join('')}</div><button type="button" class="secondary add-source">Thêm nguồn chữ quan sát được</button>
    <label>Ghi chú / phần chưa chắc<textarea data-key="notes" rows="2">${esc(a.notes)}</textarea></label></section>`;}).join('');
   for(const section of $('fields').querySelectorAll('.field')){
    const slot=section.dataset.slot;
    const storeEdit=e=>{const key=e.target.dataset.key;if(!key)return;const a=answer(slot);a.touched=true;dirty=true;
      const source=e.target.closest('[data-source]');if(source)a.sources[Number(source.dataset.source)][key]=e.target.value;else a[key]=e.target.value;
      section.querySelector('.validation').textContent=C.observationErrors(a).join(' ');update();};
    section.addEventListener('input',storeEdit);
    section.addEventListener('change',e=>{storeEdit(e);section.querySelector('.validation').textContent=C.observationErrors(answer(slot)).join(' ');});
    section.querySelector('.add-source').onclick=()=>{const a=answer(slot);a.touched=true;dirty=true;a.sources.push({kind:'',location:'',availability:'',readability:'',observed_text:'',mrz_line_1:'',mrz_line_2:''});persist();render();};
    for(const button of section.querySelectorAll('.remove-source'))button.onclick=()=>{answer(slot).sources.splice(Number(button.dataset.index),1);persist();render();};
    for(const button of section.querySelectorAll('.copy-field-source'))button.onclick=()=>{const a=answer(slot),s=a.sources[Number(button.dataset.index)];
      s.observed_text=a.observed_transcript;s.availability=a.availability;s.readability=a.readability;a.touched=true;dirty=true;persist();render();};
   }
   update();
 }
 for(const key of ['reviewer_id','role','output_exposure']){const element=$('profile-'+key);element.value=state.profile[key]||'';
   element.oninput=element.onchange=()=>{state.profile[key]=element.value;dirty=true;};}
 $('save').onclick=()=>{persist();for(const section of $('fields').querySelectorAll('.field'))section.querySelector('.validation').textContent=C.observationErrors(answer(section.dataset.slot)).join(' ');};
 $('previous').onclick=()=>{persist();state.page--;render();window.scrollTo(0,0);};
 $('next').onclick=()=>{persist();state.page++;render();window.scrollTo(0,0);};
 $('page-select').onchange=e=>{persist();state.page=Number(e.target.value);render();window.scrollTo(0,0);};
 $('next-pending').onclick=()=>{const pending=C.pendingSlots(P,state);if(!pending.length)return;
   const target=pending.find(s=>s.page>state.page)||pending[0];persist();state.page=target.page;render();window.scrollTo(0,0);};
 function download(finalize,allowPartial=false){const p=C.progress(P,state);
   if(finalize&&!allowPartial&&p.complete!==p.total){note(`Phiếu còn ${p.total-p.complete} trường chưa đủ thông tin. Bấm “Đến ảnh cần bổ sung” để xem. Bạn có thể xuất bản nháp để giữ toàn bộ phần đã làm.`,true);return;}
   const result=C.exportReview(P,state,finalize);if(result.errors){note(result.errors.join(' '),true);return;}
   const blob=new Blob([JSON.stringify(result.value,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);
   const a=document.createElement('a');a.href=url;a.download='review-'+(state.profile.reviewer_id||'draft').replace(/[^A-Za-z0-9_-]/g,'-')+'-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
   note((p.complete===p.total?'Đã xuất phiếu đủ thông tin. ':'Đã xuất bản chưa hoàn chỉnh; các mục thiếu vẫn được giữ. ')+'Kiểm tra file JSON trong Downloads. Phiếu này chưa phải kết quả đã xác minh độc lập.');}
 $('export-draft').onclick=()=>download(false);$('export-review').onclick=()=>download(true);
 $('export-partial').onclick=()=>{if(window.confirm('Xuất phần đã làm dưới dạng phiếu chưa hoàn chỉnh? Các mục còn thiếu vẫn được giữ và chưa đủ điều kiện mở pha 2.'))download(true,true);};
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
 else if(window.BLIND_REVIEW_RESUME)note('Đã nạp phần bạn đã nhập từ file đánh giá. Chỉ bổ sung mục còn thiếu; không cần chép lại từ đầu. Nếu đã có bản nháp mới hơn trên trình duyệt, bản nháp đó được ưu tiên.');
})();
