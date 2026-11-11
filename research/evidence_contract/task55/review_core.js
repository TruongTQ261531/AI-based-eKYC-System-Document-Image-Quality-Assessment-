/* Offline review state only. No OCR/model output, reference or verdict input. */
(function(root){
  'use strict';
  const AVAIL=['visible','partial','not_seen','uncertain'];
  const READ=['readable','partial','unreadable','uncertain','language_unknown','unassessed'];
  const SEM=['yes','no','uncertain'];
  const TYPES=['body','duplicated_body','mrz','other','uncertain'];
  function blank(){return {touched:false,availability:'',readability:'',semantic_key_confirmed:'',observed_transcript:'',sources:[],notes:'',prior_exposure:''};}
  function initial(packet){return {schema:'blind-review-draft/1',packet_id:packet.packet_id,profile:{reviewer_id:'',role:'',output_exposure:''},answers:{},page:0};}
  function observationErrors(o){
    const e=[];
    if(!o||!o.touched)return ['Chưa ghi nhận đánh giá.'];
    if(!AVAIL.includes(o.availability))e.push('Chọn tình trạng xuất hiện của giá trị.');
    if(!READ.includes(o.readability))e.push('Chọn mức đọc được.');
    if(!SEM.includes(o.semantic_key_confirmed))e.push('Xác nhận có xác định được ý nghĩa trường hay không.');
    if(!['no','yes','uncertain'].includes(o.prior_exposure))e.push('Ghi nhận đã biết ảnh/giá trị này từ trước hay chưa.');
    if(o.readability==='readable'&&!o.observed_transcript.trim())e.push('Trường đọc rõ cần có phần chữ bạn thực sự nhìn thấy.');
    if(o.availability==='not_seen'&&o.observed_transcript.trim())e.push('Không thấy giá trị: để trống bản chép, ghi giải thích trong ghi chú.');
    if(o.availability==='not_seen'&&o.readability==='readable')e.push('Không thể vừa không thấy vừa đọc rõ giá trị.');
    if(o.availability==='visible'&&!o.sources.length)e.push('Thêm ít nhất một nguồn chữ đã quan sát.');
    for(const s of o.sources){
      if(!TYPES.includes(s.kind))e.push('Chọn loại của từng nguồn.');
      if(!s.location.trim())e.push('Mô tả vị trí nguồn trên ảnh.');
      if(!AVAIL.includes(s.availability))e.push('Chọn tình trạng của từng nguồn.');
      if(!READ.includes(s.readability))e.push('Chọn mức đọc được ở từng nguồn.');
    }
    return e;
  }
  function profileErrors(p){const e=[];
    if(!p.reviewer_id.trim())e.push('Nhập mã người đánh giá (không cần họ tên thật).');
    if(!['project_author','external_reviewer','unknown'].includes(p.role))e.push('Chọn vai trò của bạn.');
    if(!['none','aggregate_only','per_image','unknown'].includes(p.output_exposure))e.push('Ghi nhận mức đã xem kết quả trước đây.');
    return e;
  }
  function slots(packet){return packet.pages.flatMap(p=>p.fields.map(f=>({...f,image_id:p.image_id,image_sha256:p.file_sha256})));}
  function progress(packet,state){const s=slots(packet);return {total:s.length,complete:s.filter(f=>!observationErrors(state.answers[f.slot_id]).length).length,touched:s.filter(f=>state.answers[f.slot_id]?.touched).length};}
  function saveDraft(state,storage){
    const value=JSON.stringify(state);
    try{storage.setItem('document-review/'+state.packet_id,value);return {saved:true,message:'Đã lưu bản nháp tại trình duyệt trên máy này.'};}
    catch(_){return {saved:false,message:'Trình duyệt không cho lưu tại đây. Phiếu vẫn đang mở; hãy bấm Xuất bản nháp JSON để giữ dữ liệu.'};}
  }
  function checkedAnswer(item){
    for(const key of ['availability','readability','semantic_key_confirmed','observed_transcript','notes','prior_exposure']){
      if(typeof item[key]!=='string')throw new Error('Phiếu thiếu dữ liệu trường.');
    }
    if(!Array.isArray(item.sources)||!item.sources.every(s=>s&&['kind','location','availability','readability','observed_text','mrz_line_1','mrz_line_2'].every(k=>typeof s[k]==='string'))){
      throw new Error('Phiếu có mục nguồn chữ sai định dạng.');
    }
    return item;
  }
  function restoreBackup(packet,value){
    if(value?.schema!=='blind-human-review/1'||value.packet_id!==packet.packet_id||
       value.packet_purpose!==packet.purpose||!Array.isArray(value.items)){
      throw new Error('File JSON thuộc bộ ảnh hoặc định dạng khác.');
    }
    const state=initial(packet), byId=new Map(slots(packet).map(s=>[s.slot_id,s]));
    for(const key of Object.keys(state.profile)){
      if(typeof value.reviewer?.[key]!=='string')throw new Error('File thiếu thông tin người đánh giá.');
      state.profile[key]=value.reviewer[key];
    }
    for(const item of value.items){
      const slot=byId.get(item?.slot_id);
      if(!slot||state.answers[slot.slot_id]||item.touched!==true||item.image_id!==slot.image_id||
         item.image_sha256!==slot.image_sha256||item.field_key!==slot.field_key){
        throw new Error('File không khớp ảnh hoặc chứa mục trùng.');
      }
      state.answers[slot.slot_id]=checkedAnswer(item);
    }
    return state;
  }
  function restore(packet,storage){
    try{const text=storage.getItem('document-review/'+packet.packet_id);if(!text)return {state:initial(packet)};
      const state=JSON.parse(text);
      if(state.packet_id!==packet.packet_id||state.schema!=='blind-review-draft/1'||!Number.isInteger(state.page)
        ||!state.profile||!state.answers||typeof state.answers!=='object'||Array.isArray(state.answers))throw new Error();
      for(const key of ['reviewer_id','role','output_exposure'])if(typeof state.profile[key]!=='string')throw new Error();
      for(const item of Object.values(state.answers))checkedAnswer(item);
      return {state};
    }catch(_){return {state:initial(packet),warning:'Không đọc được bản nháp cũ. Bản cũ chưa bị xóa; hãy giữ file JSON đã xuất nếu có.'};}
  }
  function exportReview(packet,state,finalize=false){
    const p=progress(packet,state);const errors=profileErrors(state.profile);
    if(finalize&&errors.length)return {errors};
    if(finalize&&!p.complete)return {errors:['Chưa có mục đủ thông tin. Bạn vẫn có thể xuất bản nháp để giữ dữ liệu.']};
    const items=slots(packet).filter(s=>state.answers[s.slot_id]?.touched).map(s=>({slot_id:s.slot_id,image_id:s.image_id,
      image_sha256:s.image_sha256,field_key:s.field_key,...state.answers[s.slot_id],
      entry_complete:!observationErrors(state.answers[s.slot_id]).length}));
    return {value:{schema:'blind-human-review/1',packet_id:packet.packet_id,packet_purpose:packet.purpose,
      mode:packet.purpose==='ui_unit_control'?'unit_injected':'human_entered',export_kind:finalize?'reviewed_observations':'draft',
      exported_at:new Date().toISOString(),reviewer:{...state.profile,independence_verified:false},
      review_state:p.complete===p.total?'complete':'partial',items,
      no_model_outputs_shown_by_packet:true,no_expected_values_shown_by_packet:true}};
  }
  const api={AVAIL,READ,SEM,TYPES,blank,initial,observationErrors,profileErrors,slots,progress,saveDraft,restore,restoreBackup,exportReview};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.BlindReviewCore=api;
})(typeof globalThis!=='undefined'?globalThis:this);
