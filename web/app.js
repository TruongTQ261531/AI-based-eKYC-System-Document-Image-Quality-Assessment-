'use strict';
const $ = id => document.getElementById(id);
const fieldNames = ['full_name', 'id_number', 'dob', 'gender', 'address'];
let activeCoreFields = [], additionalInputs = new Map();
let stream = null, photo = null, photoURL = null, token = null;
let mode = 'card', facing = 'environment', busy = false, cameraGeneration = 0;
let expiryTimer = null, requestController = null, generation = 0;
let canMatchSelfie = true;
let liveRunning = false, liveProof = false, livePacket = null, liveEpoch = 0;
let liveTimer = null, proofTimer = null, liveCancellation = Promise.resolve();

function message(text) { $('status').textContent = text; }
function clearDocumentInfo() {
  activeCoreFields=[]; additionalInputs.clear(); $('dynamic-fields').replaceChildren();
  for(const key of fieldNames) { $(key).value=''; $('row-'+key).hidden=true; }
  $('ocr-text').textContent=''; $('ocr-text-panel').hidden=true; $('document-kind').textContent='';
}
function renderDocumentInfo(result) {
  clearDocumentInfo();
  // Older responses can still be reviewed without rendering empty template fields.
  const items=Array.isArray(result.document_fields) ? result.document_fields :
    fieldNames.filter(key=>result.fields?.[key]).map(key=>({key,value:result.fields[key]}));
  const seen=new Set();
  for(const item of items.slice(0,35)) {
    if(seen.has(item.key) || !/^[a-z][a-z0-9_]{0,79}$/.test(item.key) || !item.value) continue;
    seen.add(item.key);
    if(fieldNames.includes(item.key)) {
      $(item.key).value=result.fields?.[item.key] || item.value;
      $('row-'+item.key).hidden=false; activeCoreFields.push(item.key);
    } else {
      const row=document.createElement('div'),label=document.createElement('label');
      const input=document.createElement('input');
      input.id='document-'+item.key; input.name=item.key; input.type=item.input_type==='date'?'date':'text';
      input.value=result.additional_fields?.[item.key] || item.value; input.maxLength=500; input.autocomplete='off';
      label.htmlFor=input.id; label.textContent=item.label || item.key;
      row.append(label,input); $('dynamic-fields').append(row); additionalInputs.set(item.key,input);
    }
  }
  $('document-kind').textContent=result.document_type?.label ? `Loại giấy tờ theo nội dung OCR: ${result.document_type.label}` : '';
  $('recognized-summary').textContent=seen.size ? `Đã tự động điền ${seen.size} mục đọc được. Kiểm tra và sửa nội dung nếu cần; không yêu cầu mọi loại thẻ phải có cùng các mục.` :
    'Chưa gán chắc chắn được mục thông tin. Xem văn bản OCR bên dưới; có thể chụp lại để đọc rõ hơn.';
  const text=Array.isArray(result.ocr_text)?result.ocr_text.join('\n'):'';
  $('ocr-text').textContent=text; $('ocr-text-panel').hidden=!text;
}
function showFeedback(issues = []) {
  $('feedback-items').replaceChildren();
  $('feedback-panel').hidden = !issues.length;
  for (const issue of issues) {
    const section = document.createElement('div');
    const heading = document.createElement('h3'); heading.textContent = issue.title;
    const detail = document.createElement('p'); detail.textContent = issue.detail;
    const list = document.createElement('ul');
    for (const instruction of issue.instructions || []) {
      const item = document.createElement('li'); item.textContent = instruction; list.append(item);
    }
    section.append(heading, detail, list); $('feedback-items').append(section);
  }
}
function stopLiveness(invalidate = true) {
  liveEpoch++; clearTimeout(liveTimer); clearTimeout(proofTimer);
  const hadChallenge = liveRunning || liveProof || livePacket;
  liveRunning = false; liveProof = false; livePacket = null;
  $('cancel-liveness').hidden = true; $('start-liveness').hidden = mode !== 'selfie' || !stream;
  $('geometry-overlay').hidden = true; $('gaze-target').hidden = true;
  if (invalidate && hadChallenge && token) {
    const previous = token;
    liveCancellation = liveCancellation.then(() => fetch('/api/liveness', {
      method:'DELETE', headers:{'X-Session-Token':previous}, keepalive:true
    }).catch(() => {}));
  }
}
function stopCamera({preserveProof = false} = {}) {
  if (!preserveProof) stopLiveness();
  cameraGeneration++;
  if (stream) stream.getTracks().forEach(track => track.stop());
  stream = null; $('video').srcObject = null;
  $('capture').hidden = true; $('switch-camera').hidden = true; $('start-liveness').hidden = true;
  $('geometry-overlay').hidden = true; $('gaze-target').hidden = true;
}
function clearPhoto() {
  photo = null;
  if (photoURL) URL.revokeObjectURL(photoURL);
  photoURL = null; $('preview').removeAttribute('src'); $('preview').hidden = true;
  $('video').hidden = false; $('guide').hidden = false;
  $('retake').hidden = true; $('confirm-photo').hidden = true;
  $('resolution').textContent = '';
}
function setBusy(value) {
  busy = value;
  document.querySelectorAll('button').forEach(button => { button.disabled = value && button.id !== 'reset'; });
  $('confirm-details').disabled = value || !canMatchSelfie;
  $('cancel-liveness').disabled = !liveRunning;
  $('capture').disabled = value || (mode === 'selfie' && !liveProof);
}
function showStep(step) {
  ['card', 'form', 'selfie'].forEach(name => {
    if (name === step) $('step-' + name).setAttribute('aria-current', 'step');
    else $('step-' + name).removeAttribute('aria-current');
  });
  $('camera-panel').hidden = step === 'form' || step === 'result';
  $('form-panel').hidden = step !== 'form';
  $('result-panel').hidden = step !== 'result';
}
function deleteRemoteSession() {
  const previous = token; token = null;
  clearTimeout(expiryTimer);
  if (previous) fetch('/api/session', {method: 'DELETE', headers: {'X-Session-Token': previous}, keepalive: true}).catch(() => {});
}
function reset() {
  generation++; requestController?.abort(); requestController = null;
  stopCamera(); clearPhoto(); deleteRemoteSession();
  $('details-form').reset(); clearDocumentInfo(); $('result-title').textContent = ''; $('result-score').textContent = '';
  $('result-checks').replaceChildren(); $('result-liveness').textContent = '';
  $('liveness-panel').hidden = true; $('live-progress').value = 0;
  for (const name of ['live-pose','live-eyes','live-gaze','live-quality','live-pad']) $(name).textContent = 'Chưa đo';
  canMatchSelfie = true; $('portrait-status').textContent = '';
  mode = 'card'; facing = 'environment'; setBusy(false); showStep('card');
  showFeedback();
  $('camera-title').textContent = 'Chụp giấy tờ';
  $('camera-help').textContent = 'Đặt toàn bộ giấy tờ trong khung, tránh lóa và giữ máy ổn định. Khung chỉ để căn chỉnh, ảnh gửi đi giữ toàn bộ khung hình.';
  $('guide').classList.remove('face'); $('open-camera').hidden = false;
  message('Bấm “Mở camera” để bắt đầu.');
}
function cameraError(error) {
  const messages = {
    NotAllowedError: 'Bạn chưa cho phép camera. Hãy cấp quyền camera trong trình duyệt rồi thử lại.',
    NotFoundError: 'Không tìm thấy camera trên thiết bị này.',
    NotReadableError: 'Camera đang được ứng dụng khác sử dụng hoặc không truy cập được.',
    OverconstrainedError: 'Camera không hỗ trợ cấu hình yêu cầu. Hãy thử đổi camera.',
    SecurityError: 'Trình duyệt chặn camera. Hãy dùng localhost hoặc HTTPS.',
    AbortError: 'Camera bị ngắt. Vui lòng mở lại.'
  };
  return messages[error.name] || 'Không mở được camera. Kiểm tra thiết bị và quyền truy cập.';
}
async function openCamera() {
  if (busy) return;
  stopCamera(); clearPhoto();
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    message('Camera cần localhost hoặc HTTPS và trình duyệt hỗ trợ getUserMedia. Trên điện thoại hãy dùng HTTPS có chứng chỉ tin cậy.'); return;
  }
  const cameraRequest = cameraGeneration;
  message('Đang xin quyền camera… Bạn có thể bấm “Xóa phiên” để hủy.');
  $('open-camera').disabled = true;
  try {
    let next;
    try {
      next = await navigator.mediaDevices.getUserMedia({audio: false, video: {
        facingMode: {ideal: facing}, width: {ideal: 2560}, height: {ideal: 1440}
      }});
    } catch (error) {
      if (error.name !== 'OverconstrainedError' || cameraRequest !== cameraGeneration) throw error;
      next = await navigator.mediaDevices.getUserMedia({audio: false, video: {facingMode: {ideal: facing}}});
    }
    if (cameraRequest !== cameraGeneration) { next.getTracks().forEach(t => t.stop()); return; }
    stream = next; $('video').srcObject = stream;
    const track = stream.getVideoTracks()[0];
    const mirrored = (track.getSettings().facingMode || facing) === 'user';
    $('video').classList.toggle('mirror', mirrored);
    $('geometry-overlay').classList.toggle('mirror', mirrored);
    track.addEventListener('ended', () => {
      if (stream === next) { stopCamera(); setBusy(false); $('open-camera').hidden = false; message('Camera đã bị ngắt. Vui lòng mở lại và thực hiện lại thử thách.'); }
    });
    await $('video').play();
    if (cameraRequest !== cameraGeneration) return;
    $('open-camera').hidden = true; $('capture').hidden = mode === 'selfie'; $('switch-camera').hidden = false;
    $('start-liveness').hidden = mode !== 'selfie'; $('liveness-panel').hidden = mode !== 'selfie';
    $('live-instruction').textContent = 'Nhìn thẳng vào camera. Bấm bắt đầu để gửi khung hình và thực hiện thử thách.';
    message(mode === 'card' ? 'Căn giấy tờ vào khung rồi chụp ảnh.' : 'Bấm “Bắt đầu kiểm tra cử động”, sau đó làm theo từng hướng dẫn.');
  } catch (error) {
    if (cameraRequest === cameraGeneration) { stopCamera(); $('open-camera').hidden = false; message(cameraError(error)); }
  } finally { $('open-camera').disabled = false; }
}
async function capturePhoto() {
  if (busy || !stream || !$('video').videoWidth) return;
  if (mode === 'selfie' && !liveProof) { message('Cần hoàn thành thử thách cử động trước khi chụp ảnh chân dung.'); return; }
  setBusy(true); const current = generation;
  try {
    const track = stream.getVideoTracks()[0];
    let blob;
    // Prefer sensor photo resolution. Fallback uses actual video dimensions, never CSS size.
    if (window.ImageCapture) {
      try {
        const camera = new ImageCapture(track);
        const capabilities = await camera.getPhotoCapabilities();
        const settings = {};
        if (capabilities.imageWidth?.max) settings.imageWidth = capabilities.imageWidth.max;
        if (capabilities.imageHeight?.max) settings.imageHeight = capabilities.imageHeight.max;
        blob = await camera.takePhoto(settings);
      } catch (_) { /* Browser may support video but not still-image capture. */ }
    }
    if (current !== generation) return;
    if (!blob) {
      const canvas = document.createElement('canvas');
      canvas.width = $('video').videoWidth; canvas.height = $('video').videoHeight;
      if (!canvas.width || !canvas.height) throw Error('Camera chưa sẵn sàng. Vui lòng mở lại.');
      canvas.getContext('2d').drawImage($('video'), 0, 0, canvas.width, canvas.height);
      blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.95));
      canvas.width = canvas.height = 0;
    }
    if (current !== generation) return;
    if (!blob) throw Error('Không chụp được ảnh. Vui lòng thử lại.');
    if (blob.size > 30 * 1024 * 1024) throw Error('Ảnh lớn hơn 30 MB. Hãy đổi camera hoặc giảm độ phân giải trong thiết bị.');
    photo = blob; photoURL = URL.createObjectURL(blob);
    $('preview').src = photoURL;
    await $('preview').decode();
    if (current !== generation) return;
    $('resolution').textContent = `Ảnh gốc: ${$('preview').naturalWidth} × ${$('preview').naturalHeight} pixel. Chưa gửi lên máy chủ.`;
    stopCamera({preserveProof: mode === 'selfie' && liveProof}); $('video').hidden = true; $('guide').hidden = true; $('preview').hidden = false;
    $('open-camera').hidden = true; $('retake').hidden = false; $('confirm-photo').hidden = false;
    message('Kiểm tra ảnh. Bạn có thể chụp lại hoặc xác nhận để xử lý.');
  } catch (error) { if (current === generation) message(error.message); }
  finally { if (current === generation) setBusy(false); }
}
async function api(path, options = {}) {
  requestController = new AbortController();
  const response = await fetch(path, {...options, signal: requestController.signal,
    headers: {...(token ? {'X-Session-Token': token} : {}), ...options.headers}});
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401) { reset(); throw Error('Phiên đã hết hạn. Vui lòng chụp lại giấy tờ.'); }
    if (result.issues) showFeedback(result.issues);
    const error = Error(typeof result.detail === 'string' ? result.detail : 'Thông tin không hợp lệ. Vui lòng kiểm tra lại.');
    error.status = response.status; error.livenessInvalidated = result.liveness_invalidated === true;
    throw error;
  }
  return result;
}

function renderLiveness(packet) {
  $('live-instruction').textContent = packet.instruction;
  $('live-progress').max = packet.total;
  $('live-progress').value = packet.completed;
  const timing = packet.status === 'failed'
    ? (packet.reason === 'challenge_timeout' ? 'Đã hết thời gian' : 'Đã dừng')
    : packet.status === 'passed' ? 'Hoàn thành' : `Còn ${Math.ceil(packet.expires_in)} giây`;
  $('live-progress-label').textContent = `${packet.completed}/${packet.total} động tác · ${timing}`;
  const obs = packet.observation;
  const padLabels = {pending:'Đang chờ khung hình',live:'Khung hình qua kiểm tra chống giả',
    spoof:'Từ chối: có dấu hiệu giả mạo',uncertain:'Chưa đủ bằng chứng, chưa cho phép tiếp tục'};
  $('live-pad').textContent = padLabels[packet.pad?.decision] || 'Chưa có kết quả chống giả';
  const gazeTarget = packet.phase === 'action' && ['look_left','look_right'].includes(packet.action);
  $('gaze-target').hidden = !gazeTarget;
  $('gaze-target').classList.toggle('right', packet.action === 'look_right');
  $('gaze-target').textContent = packet.action === 'look_right' ? '→' : '←';
  const overlay = $('geometry-overlay');
  overlay.hidden = !obs?.overlay?.length;
  if (!obs?.pose) {
    for (const name of ['live-pose','live-eyes','live-gaze','live-quality']) $(name).textContent = 'Chưa theo dõi rõ khuôn mặt';
    return;
  }
  $('live-pose').textContent = `${obs.pose.yaw.toFixed(1)}° / ${obs.pose.pitch.toFixed(1)}° / ${obs.pose.roll.toFixed(1)}°`;
  $('live-eyes').textContent = `Mức nhắm trái ${(obs.blink_left*100).toFixed(0)}% · phải ${(obs.blink_right*100).toFixed(0)}%`;
  const directions = {left:'Sang trái của bạn',right:'Sang phải của bạn',center:'Ở giữa',unknown:'Chưa rõ'};
  $('live-gaze').textContent = packet.measurements
    ? `${directions[packet.measurements.gaze_direction]} (ước lượng so với lúc căn chỉnh)`
    : obs.gaze_horizontal == null ? 'Chưa theo dõi rõ hai mắt' : 'Đang căn chỉnh ánh nhìn';
  $('live-quality').textContent = `${obs.metrics.sharpness.toFixed(0)} / ${obs.metrics.brightness.toFixed(0)} · ${obs.quality_ok ? 'Đủ điều kiện đo' : 'Cần điều chỉnh'}`;
  overlay.width = 640; overlay.height = Math.round(640 * $('video').videoHeight / $('video').videoWidth);
  const ctx = overlay.getContext('2d');
  if (ctx) {
    ctx.clearRect(0,0,overlay.width,overlay.height);
    ctx.fillStyle = obs.quality_ok ? '#56e8c0' : '#ffce65';
    for (const [x,y] of obs.overlay) { ctx.beginPath(); ctx.arc(x*overlay.width,y*overlay.height,3,0,Math.PI*2); ctx.fill(); }
  }
}
async function liveFrameBlob() {
  const video = $('video'), canvas = document.createElement('canvas');
  if (!video.videoWidth || !video.videoHeight) throw Error('Camera chưa có khung hình. Vui lòng mở lại.');
  const scale = Math.min(1,960/Math.max(video.videoWidth,video.videoHeight));
  canvas.width = Math.round(video.videoWidth*scale); canvas.height = Math.round(video.videoHeight*scale);
  canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
  const blob = await new Promise(resolve => canvas.toBlob(resolve,'image/jpeg',.85));
  canvas.width = canvas.height = 0;
  if (!blob) throw Error('Không đọc được khung hình camera.');
  return blob;
}
async function runLiveFrame(epoch) {
  if (!liveRunning || epoch !== liveEpoch || !stream) return;
  try {
    const blob = await liveFrameBlob();
    if (!liveRunning || epoch !== liveEpoch) return;
    const body = new FormData(); body.append('image',blob,'live-frame.jpg');
    const packet = await api('/api/liveness/frame',{method:'POST',body,headers:{
      'X-Liveness-Id':livePacket.challenge_id,'X-Frame-Token':livePacket.frame_token,
      'X-Frame-Sequence':String(livePacket.next_sequence)
    }});
    if (epoch !== liveEpoch) return;
    livePacket = packet; renderLiveness(packet);
    if (packet.status === 'passed') {
      liveRunning = false; liveProof = true; setBusy(false);
      $('cancel-liveness').hidden = true; $('start-liveness').hidden = true; $('capture').hidden = false;
      $('gaze-target').hidden = true;
      message('Đã hoàn thành thử thách cử động. Nhìn thẳng và chụp ảnh chân dung để xác nhận.');
      proofTimer = setTimeout(() => {
        if (!liveProof) return;
        stopLiveness();
        if (!busy) { clearPhoto(); $('capture').hidden = true; $('open-camera').hidden = !stream; }
        message('Kết quả thử thách đã hết hạn sau 45 giây. Vui lòng thực hiện lại.');
      }, packet.proof_expires_in*1000);
      return;
    }
    if (packet.status === 'failed') {
      const explanation = packet.instruction;
      stopLiveness(); setBusy(false); message(explanation); return;
    }
    liveTimer = setTimeout(() => runLiveFrame(epoch),150);
  } catch (error) {
    if (epoch !== liveEpoch) return;
    if (error.status === 429) { liveTimer = setTimeout(() => runLiveFrame(epoch),500); return; }
    stopLiveness(); setBusy(false);
    if (error.name !== 'AbortError') message(error.message || 'Mất kết nối kiểm tra camera. Vui lòng bắt đầu lại.');
  }
}
async function startLiveness() {
  if (busy || mode !== 'selfie' || !stream) return;
  stopLiveness(); liveRunning = true; const epoch = liveEpoch;
  setBusy(true); showFeedback(); $('capture').hidden = true;
  $('cancel-liveness').hidden = false; $('start-liveness').hidden = true;
  message('Đang bắt đầu thử thách. Khung hình camera được gửi để phân tích.');
  try {
    await liveCancellation;
    if (epoch !== liveEpoch) return;
    const packet = await api('/api/liveness/start',{method:'POST'});
    if (epoch !== liveEpoch) return;
    livePacket = packet; renderLiveness(packet);
    await runLiveFrame(epoch);
  } catch (error) {
    if (epoch !== liveEpoch) return;
    stopLiveness(); setBusy(false);
    if (error.name !== 'AbortError') message(error.message);
  }
}
async function confirmPhoto() {
  if (!photo || busy) return;
  if (mode === 'selfie' && !liveProof) { message('Thử thách camera đã hết hạn. Vui lòng thực hiện lại.'); return; }
  setBusy(true); showFeedback(); const current = generation;
  message(mode === 'card' ? 'Đang kiểm tra chất lượng, nắn ảnh và đọc OCR…' : 'Đang đối chiếu khuôn mặt…');
  try {
    const body = new FormData(); body.append(mode === 'card' ? 'card' : 'image', photo, 'camera.jpg');
    const result = await api(mode === 'card' ? '/api/document' : '/api/selfie', {method: 'POST', body});
    if (current !== generation) return;
    if (mode === 'card') {
      clearPhoto();
      if (result.status === 'retake') {
        const reasons = {quality_rejected: 'Ảnh không đạt chất lượng.', document_corners_not_found: 'Chưa tìm đủ góc giấy tờ.', id_face_unavailable: 'Chưa tìm được một chân dung rõ nét trên giấy tờ.'};
        $('open-camera').hidden = false;
        showFeedback(result.issues || []);
        message(result.issues?.length ? result.issues.map(issue => issue.title).join(' · ') + '. Xem hướng dẫn bên dưới và chụp lại.' : (reasons[result.reason] || 'Không đọc được giấy tờ.') + ' Vui lòng mở camera và chụp lại.'); return;
      }
      token = result.session_token;
      expiryTimer = setTimeout(() => { reset(); message('Phiên đã hết hạn sau 10 phút. Dữ liệu phiên đã được xóa.'); }, result.expires_in * 1000);
      renderDocumentInfo(result);
      canMatchSelfie = result.can_match_selfie !== false;
      $('portrait-status').textContent = canMatchSelfie
        ? 'Đã tách được chân dung để đối chiếu selfie. Đây chưa phải kết quả xác minh.'
        : 'Bạn vẫn xem và sửa được thông tin OCR. Chưa có chân dung giấy tờ đủ tin cậy để so selfie; nếu thẻ không có ảnh, cần dùng giấy tờ có ảnh cho bước đối chiếu khuôn mặt.';
      showFeedback(result.issues || []);
      showStep('form'); message(canMatchSelfie ? 'Đã tự động điền thông tin đọc được từ giấy tờ. Kiểm tra và chỉnh sửa trước khi chuyển sang selfie.' : 'Thông tin OCR đã sẵn sàng. Phần chân dung cần được chụp lại để tiếp tục đối chiếu.');
    } else {
      if (!result.liveness_checked || !result.liveness_passed || !result.liveness?.pad?.passed || !result.liveness?.pad?.final_selfie_passed) {
        throw Object.assign(Error('Chưa có kết quả kiểm tra cử động và chống giả hợp lệ. Vui lòng bắt đầu lại.'),{livenessInvalidated:true});
      }
      stopLiveness(false); $('liveness-panel').hidden = true;
      clearPhoto(); deleteRemoteSession(); $('details-form').reset(); clearDocumentInfo(); showStep('result');
      showFeedback(result.issues || []);
      $('result-title').textContent = result.status === 'matched' ? 'Khuôn mặt khớp theo ngưỡng mô hình' : 'Khuôn mặt chưa khớp';
      $('result-score').textContent = `Điểm cosine: ${result.matching.cosine_similarity.toFixed(3)} · Ngưỡng: ${result.matching.threshold.toFixed(3)}. Đây không phải xác suất xác minh.`;
      const labels = {blink:'Chớp cả hai mắt',turn_left:'Quay đầu trái',turn_right:'Quay đầu phải',look_left:'Ánh nhìn trái',look_right:'Ánh nhìn phải',nod:'Cúi đầu và trở lại'};
      $('result-checks').replaceChildren();
      for (const action of result.liveness?.completed_actions || []) {
        const item = document.createElement('li'); item.textContent = `${labels[action] || action}: đạt`; $('result-checks').append(item);
      }
      const continuity = document.createElement('li');
      continuity.textContent = `Khuôn mặt xuyên suốt thử thách và ảnh cuối: ${result.identity_consistent === true ? 'nhất quán theo ngưỡng mô hình' : 'chưa xác nhận nhất quán'}`;
      $('result-checks').append(continuity);
      const padCheck = document.createElement('li');
      padCheck.textContent = 'Kiểm tra chống giả trên khung hình và ảnh cuối: qua ngưỡng mô hình';
      $('result-checks').append(padCheck);
      $('result-liveness').textContent = `Đã hoàn thành thử thách cử động với ${result.liveness?.identity_samples || 0} mẫu khuôn mặt và kiểm tra chống giả bằng ảnh camera. Kết quả chưa thay thế việc xác minh danh tính.`;
      message('Đã kiểm tra cử động, chống giả và đối chiếu khuôn mặt. Dữ liệu phiên đã được xóa.');
    }
  } catch (error) {
    if (current !== generation) return;
    if (mode==='selfie' && (error.livenessInvalidated || error.status===409 || error.status===503)) {
      stopLiveness(); clearPhoto(); $('capture').hidden = true; $('open-camera').hidden = false;
    }
    if (error.name !== 'AbortError') message(error.message || 'Mất kết nối. Vui lòng thử lại.');
  }
  finally { if (current === generation) setBusy(false); }
}
$('details-form').addEventListener('submit', async event => {
  event.preventDefault(); if (busy) return;
  if (!canMatchSelfie) { message('Cần chụp lại mặt giấy tờ có ảnh chân dung trước khi đối chiếu selfie.'); return; }
  setBusy(true); const current = generation;
  try {
    const values = Object.fromEntries(activeCoreFields.map(key => [key, $(key).value]));
    if(additionalInputs.size) values.additional_fields=Object.fromEntries([...additionalInputs].map(([key,input])=>[key,input.value]));
    await api('/api/confirm', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(values)});
    if (current !== generation) return;
    showFeedback();
    mode = 'selfie'; facing = 'user'; showStep('selfie'); clearPhoto();
    $('camera-title').textContent = 'Kiểm tra cử động và chụp chân dung';
    $('camera-help').textContent = 'Đưa khuôn mặt trực tiếp trước camera; không dùng ảnh hoặc cuộc gọi video trên màn hình. Chỉ một người trong khung, giữ rõ trán, cằm và hai mắt. Làm theo hướng dẫn rồi chụp ảnh để đối chiếu.';
    $('guide').classList.add('face'); $('open-camera').hidden = false;
    message('Bấm mở camera trước để chụp selfie.');
  } catch (error) { if (error.name !== 'AbortError') message(error.message); }
  finally { if (current === generation) setBusy(false); }
});
$('open-camera').addEventListener('click', openCamera);
$('retake').addEventListener('click', openCamera);
$('switch-camera').addEventListener('click', () => { facing = facing === 'environment' ? 'user' : 'environment'; openCamera(); });
$('capture').addEventListener('click', capturePhoto);
$('confirm-photo').addEventListener('click', confirmPhoto);
$('start-liveness').addEventListener('click', startLiveness);
$('cancel-liveness').addEventListener('click', () => { stopLiveness(); setBusy(false); message('Đã dừng kiểm tra. Bấm bắt đầu để thực hiện thử thách mới.'); });
$('reset').addEventListener('click', reset);
$('retake-document').addEventListener('click', () => { reset(); openCamera(); });
window.addEventListener('pagehide', reset);
document.addEventListener('visibilitychange', () => {
  if (document.hidden && stream) { const wasLive = liveRunning; stopCamera(); if (wasLive) setBusy(false); $('open-camera').hidden = false; message('Camera đã tắt khi rời trang. Bấm mở camera và thực hiện lại thử thách để tiếp tục.'); }
});
