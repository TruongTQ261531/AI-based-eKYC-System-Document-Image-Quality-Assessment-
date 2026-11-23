"""Render two offline, self-contained assessor workspaces with empty responses."""
from html import escape
from shutil import copyfile

from ..reviewer_tools.strict import digest, need
from ..task55.data import sha
from .review import PROPS

QUESTIONS_VI = {
    'exposure':'Trước khi mở hồ sơ này, bạn đã gặp ảnh, giá trị hoặc kết quả của ca này chưa?',
    'primary_supported_before':'Trước biến đổi, vùng chính có đọc được và đúng trường không?',
    'primary_removed_after':'Sau biến đổi, giá trị ở nguồn chính đã mất hoặc không còn đọc được?',
    'backup_supported_before':'Trước biến đổi, nguồn MRZ dự phòng có đọc được và hỗ trợ trường?',
    'backup_supported_after':'Sau biến đổi, nguồn MRZ dự phòng còn đọc được và hỗ trợ trường?',
    'semantic_judgment':'Hai nguồn có biểu đạt cùng trường ngữ nghĩa?',
    'precision_judgment':'Độ chính xác của hai cách biểu diễn có tương thích cho phép so này?'
}


def select(key,values):
    options=''.join('<option>'+e+'</option>' for e in values)
    return f'<p><label>{QUESTIONS_VI[key]} <select required name="{key}"><option value=""></option>{options}</select></label></p>'


SCRIPT = """
document.addEventListener('submit', function (event) {
  event.preventDefault();
  const f = event.target;
  const data = new FormData(f);
  const refs = data.getAll('basis');
  for (const side of ['before','after']) {
    if (!f.querySelector('input[data-side="'+side+'"]:checked')) {
      alert('Hãy chọn ít nhất một hash cho từng thời điểm.'); return;
    }
  }
  if (!data.get('rationale').trim()) {alert('Cần lý do bằng văn bản.'); return;}
  const record = {schema:'c2-source-review/1', role:'reviewer', assessor:f.dataset.assessor,
    candidate_id:f.dataset.candidate,item_sha256:f.dataset.item,exposure:data.get('exposure'),
    semantic_judgment:data.get('semantic_judgment'),precision_judgment:data.get('precision_judgment'),
    basis_sha256:[...new Set(refs)],rationale:data.get('rationale'),observations:{}};
  for (const key of ['primary_supported_before','primary_removed_after','backup_supported_before','backup_supported_after']) {
    record.observations[key]=data.get(key);
  }
  const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));
  const link=document.createElement('a'); link.href=url; link.download=record.assessor+'-'+record.candidate_id+'.json';
  link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
"""


def render(folder, assessor, items, assets, *, scope='C2_MASTER_45'):
    need((scope, len(items)) in {('C2_MASTER_45',45),('C2_37_PROPOSED',37)},'Unexpected package scope')
    folder.mkdir()
    (folder/'assets').mkdir()
    names={}
    for h,src in sorted(assets.items()):
        suffix=src.suffix.lower()
        need(suffix in {'.png','.jpg','.jpeg'},'Unknown image format')
        names[h]='assets/'+h+suffix
        copyfile(src,folder/names[h])
        need(sha(folder/names[h])==h,'Packaged asset hash')
    sections=['<!doctype html><html lang="vi"><meta charset="utf-8"><title>C2 review</title>',
        '<h1>C2 · '+assessor+'</h1><p>Bản chuẩn bị nội bộ. Chờ chủ dự án xác nhận D10 trước khi cấp quyền truy cập.</p>',
        '<p>Điền riêng cho từng ca. PASS = có đủ căn cứ, FAIL = quan sát bác bỏ, UNKNOWN = thiếu căn cứ. '
        'Xem ảnh đầy đủ khi crop thiếu ngữ cảnh. Giữ nguyên O/0 và độ chính xác ngày. Xuất riêng từng phiếu JSON. '
        'Trang chạy ngoại tuyến, không tự lưu hoặc gửi câu trả lời.</p>',
        '<p>Nguồn MIDV-2020, Bulatov và cộng sự, Computer Optics 46(2), 2022. '
        'CC BY-SA 2.5. Chân dung tổng hợp từ Generated Photos. Các ảnh dẫn xuất đã cắt/che vùng.</p>']
    if scope == 'C2_37_PROPOSED':
        sections.append('<p>C2-37 · MIDV-2020: A Comprehensive Benchmark Dataset for Identity Document Analysis. '
                        'DOI 10.18287/2412-6179-CO-1006. Ảnh và dẫn xuất: https://creativecommons.org/licenses/by-sa/2.5/. '
                        'Chân dung: Generated Photos (https://generated.photos/). Mẫu nền: Government of Azerbaijan, '
                        'Government of Latvia, Government of Serbia / Twofortnights / Wikimedia Commons. Nguồn: EdisonTD. '
                        'Ảnh dẫn xuất do nhóm nghiên cứu cắt/che; crop trích vùng body và MRZ.</p>')
    for n,item in enumerate(items,1):
        sections.append(f'<details><summary>{n}/{len(items)} · {escape(item["field"])} · {item["candidate_id"]}</summary>')
        sections.append(f'<form data-assessor="{assessor}" data-candidate="{item["candidate_id"]}" data-item="{digest(item)}">')
        sections.append(select('exposure',PROPS['exposure']['enum']))
        sections.append('<p>Trường body '+escape(item['native_key'])+' · '+escape(item['source_precision']['body'])+
                        ' / MRZ '+escape(item['source_precision']['mrz'])+'</p>')
        for side in ('before','after'):
            h=item['full'][side]['file']
            sections.append(f'<h3>{side}</h3><a href="{names[h]}">Ảnh đầy đủ</a> <code>{h}</code>')
            for reg in (i for i in item['regions'] if i['side']==side):
                label=escape(reg['native_key']+' · '+reg['region'])
                if 'sha256' in reg:
                    sections.append(f'<figure><img loading="lazy" width="340" src="{names[reg["sha256"]]}"><figcaption>{label}</figcaption></figure>')
                else:
                    sections.append('<p>'+label+' · vùng nằm ngoài khung. Đối chiếu ảnh đầy đủ.</p>')
            sections.append('<p>Chọn hash bằng chứng đã dùng</p>')
            for h in item['evidence_by_side'][side]:
                desc='ảnh đầy đủ' if h==item['full'][side]['file'] else next(
                    r['native_key'] for r in item['regions'] if r.get('sha256')==h and r['side']==side)
                sections.append(f'<label><input type="checkbox" name="basis" data-side="{side}" value="{h}">{escape(desc)} · <code>{h}</code></label><br>')
        for k,field in PROPS['observations']['properties'].items():
            sections.append(select(k,field['enum']))
        for k in ('semantic_judgment','precision_judgment'):
            sections.append(select(k,PROPS[k]['enum']))
        sections.append('<p><label>Lý do và giới hạn quan sát <textarea required maxlength="20000" name="rationale"></textarea></label></p>'
                        '<button>Xuất phiếu ca này</button></form></details>')
    sections.append('<script>'+SCRIPT+'</script></html>')
    (folder/'index.html').write_bytes('\n'.join(sections).encode())
    return {p.relative_to(folder).as_posix():sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
