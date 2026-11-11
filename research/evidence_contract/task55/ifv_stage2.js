(function () {
  'use strict';
  const packet = window.OUTPUT_PACKET;
  const $ = (id) => document.getElementById(id);
  const storageKey = 'ifv-output/' + packet.packet_id;
  const readings = [
    ['', 'Chưa chọn'],
    ['correct', 'Đúng hoặc để trống phù hợp khi xác minh không còn nguồn'],
    ['wrong_value', 'Sai giá trị đọc được'],
    ['readable_omission', 'Bỏ sót giá trị đọc được'],
    ['unsupported_verified', 'Điền giá trị dù đã xác minh không còn nguồn'],
    ['uncertain', 'Chưa xác định']
  ];
  const conditions = {
    C1: 'Kiểm tra nguồn của trường cần che trên cả ảnh. Việc không nhìn thấy chữ chưa đủ để khẳng định mọi nguồn đã bị xóa.',
    C2: 'Kiểm tra vị trí chính đã bị che và một nguồn khác vẫn đọc được. Nếu là MRZ, cần dòng chép từ phiếu đọc ảnh để xác minh định dạng và mã kiểm tra.',
    C3: 'Kiểm tra trường được giữ lại có cùng giá trị và còn đủ ngữ cảnh để nhận diện trường. Xem tác động của phần đã che.',
    C4: 'Kiểm tra ảnh biến đổi còn nguyên vùng chữ và nhãn giải thích của trường đánh giá.'
  };
  let items = {};
  let current = 0;
  let dirty = false;
  let needsBackup = false;
  const record = () => packet.cases[current];
  function note(text) { $('message').textContent = text; }
  function persist() {
    try { localStorage.setItem(storageKey, JSON.stringify(items)); }
    catch (_) { needsBackup = true; note('Trình duyệt không lưu nháp tại đây. Hãy xuất JSON trước khi đóng trang.'); return false; }
    needsBackup = false;
    return true;
  }
  function checkedItems(values) {
    if (!Array.isArray(values)) throw new Error('Thiếu danh sách ca.');
    const known = new Set(packet.cases.map((c) => c.case_id));
    const result = {};
    for (const item of values) {
      if (!known.has(item?.case_id) || result[item.case_id]) throw new Error('Mã ca sai hoặc trùng.');
      result[item.case_id] = item;
    }
    return result;
  }
  try {
    items = checkedItems(Object.values(JSON.parse(localStorage.getItem(storageKey) || '{}')));
  } catch (_) { note('Không đọc được bản nháp. Bạn có thể nạp bản JSON đã xuất.'); }
  for (const id of ['before_reading', 'after_reading']) {
    for (const [key, name] of readings) $(id).add(new Option(name, key));
  }
  function evidenceText(evidence) {
    const sources = evidence.sources.map((s) => s.kind + ' – ' + s.location).join(', ');
    return [
      'Phiếu pha 1: ' + evidence.availability + ' / ' + evidence.readability,
      'Chữ đã chép: ' + (evidence.observed_transcript || '(trống)'),
      sources ? 'Vị trí đã ghi: ' + sources : '',
      evidence.notes || ''
    ].filter(Boolean).join(' · ');
  }
  function reveal() {
    const c = record();
    $('reference').textContent = c.author_reference;
    for (const key of ['before', 'after']) {
      const o = c[key + '_output'];
      $(key + '-value').textContent = o.structured_output_usable ? o.value || '(trống)' : '(cấu trúc không dùng được)';
    }
    $('output').hidden = false;
    for (const id of ['test_validity', 'absence_check', 'reason', 'reveal']) $(id).disabled = true;
  }
  function render() {
    const c = record();
    const a = items[c.case_id] || {};
    $('progress').textContent = 'Ca ' + (current + 1) + '/' + packet.cases.length +
      ' · ' + Object.values(items).filter((x) => x.before_reading && x.after_reading).length + ' ca đã đánh giá';
    $('field').textContent = c.case_id + ' · ' + c.label;
    $('condition').textContent = conditions[c.contract] + ' Vùng tác động dự kiến: ' + c.target_label + '.';
    $('absence-label').hidden = c.contract !== 'C1';
    for (const key of ['before', 'after']) {
      $(key + '-image').src = c[key + '_image'];
      $(key + '-link').href = c[key + '_image'];
      $(key + '-evidence').textContent = evidenceText(c[key + '_evidence']);
    }
    for (const id of ['test_validity', 'absence_check', 'reason', 'before_reading', 'after_reading']) $(id).value = a[id] || '';
    $('output-note').value = a.output_note || '';
    $('output').hidden = true;
    for (const id of ['test_validity', 'absence_check', 'reason', 'reveal']) $(id).disabled = false;
    $('reference').textContent = '';
    $('before-value').textContent = '';
    $('after-value').textContent = '';
    $('previous').disabled = current === 0;
    $('next').disabled = current === packet.cases.length - 1;
    if (a.test_validity && a.reason) reveal();
  }
  $('reveal').onclick = () => {
    const c = record();
    const test_validity = $('test_validity').value;
    const absence_check = c.contract === 'C1' ? $('absence_check').value : 'not_applicable';
    const reason = $('reason').value.trim();
    if (!test_validity || !absence_check || !reason) { note('Chọn tình trạng phép thử và ghi lý do trước.'); return; }
    if (items[c.case_id]) return;
    items[c.case_id] = { case_id: c.case_id, test_validity, absence_check, reason,
      first_reveal_at: new Date().toISOString() };
    if (persist()) note('Đã ghi điều kiện. Bây giờ có thể đối chiếu đầu ra.');
    dirty = false;
    reveal();
  };
  $('save').onclick = () => {
    const a = items[record().case_id];
    const before_reading = $('before_reading').value;
    const after_reading = $('after_reading').value;
    if (!before_reading || !after_reading) { note('Chọn đánh giá cho cả ảnh gốc và ảnh biến đổi.'); return; }
    const output_note = $('output-note').value.trim();
    if (['wrong_value', 'readable_omission', 'unsupported_verified'].includes(after_reading) && !output_note) {
      note('Ghi lý do quan sát được cho giá trị sai, bị bỏ sót hoặc được điền khi thiếu nguồn.'); return;
    }
    a.before_reading = before_reading;
    a.after_reading = after_reading;
    a.output_note = output_note;
    if (persist()) note('Đã lưu đánh giá ca này.');
    dirty = false;
    render();
  };
  for (const id of ['test_validity', 'absence_check', 'reason', 'before_reading', 'after_reading', 'output-note']) {
    $(id).addEventListener('input', () => { dirty = true; });
  }
  function move(delta) {
    if (dirty && !window.confirm('Ca này có chỉnh sửa chưa lưu. Chuyển sang ca khác?')) return;
    dirty = false; current += delta; render();
  }
  $('previous').onclick = () => move(-1);
  $('next').onclick = () => move(1);
  $('export').onclick = () => {
    const completed = Object.values(items).filter((a) => a.before_reading && a.after_reading);
    if (dirty || !completed.length) { note('Hãy lưu ít nhất một ca và lưu ca đang sửa trước khi xuất.'); return; }
    const value = { schema: 'ifv-output-observations/1', mode: 'human_entered', packet_id: packet.packet_id,
      phase1_snapshot: packet.phase1_snapshot, exported_at: new Date().toISOString(), items: completed };
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url; a.download = 'ifv-output-' + packet.packet_id.slice(0, 12) + '.json';
    document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    needsBackup = false;
    note('Kiểm tra thư mục Downloads để giữ bản phiếu JSON.');
  };
  $('load').onchange = async (event) => {
    const file = event.target.files[0]; event.target.value = ''; if (!file) return;
    try {
      const value = JSON.parse(await file.text());
      if (value.schema !== 'ifv-output-observations/1' || value.packet_id !== packet.packet_id ||
          value.phase1_snapshot !== packet.phase1_snapshot || value.mode !== 'human_entered') {
        throw new Error('Phiếu thuộc bộ khác hoặc sai định dạng.');
      }
      const imported = checkedItems(value.items);
      if ((dirty || Object.keys(items).length) && !window.confirm('Thay phiếu đang mở bằng bản JSON?')) return;
      items = imported; dirty = false; render(); if (persist()) note('Đã nạp phiếu JSON.');
    } catch (error) { note(error.message); }
  };
  window.addEventListener('beforeunload', (event) => { if (dirty || needsBackup) event.preventDefault(); });
  render();
})();
