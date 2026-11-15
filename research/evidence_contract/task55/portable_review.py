"""Build standalone reviewer ZIPs; phase 2 requires that reviewer's sealed phase 1.

Only the offline UI, manifest and fictional images leave the project. Author
answers, other reviewers' observations, model identities and analyst joins are
excluded. Preparing a package never counts as a completed or independent review.
"""
from pathlib import Path
import argparse
import json
import re
import zipfile

from .data import EC, OUT, read, sha, digest, save_new
from .review import PACKET_ROOT
from . import ifv

EXPORTS=EC/'local/reviewer_exports'
UI_ROOT=Path(__file__).resolve().parent


def reviewer_code(value):
    if not re.fullmatch(r'R[0-9]{2,8}',value):
        raise ValueError('Use an assigned pseudonym such as R02, not a real name')
    return value


def script_literal(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')


def frozen_packet():
    packet=read(PACKET_ROOT/'packet_manifest.json')
    prepared=read(OUT/'review_packet_preparation.json')
    ifv.bound_manifest(packet,'packet_id')
    if packet['packet_id']!=prepared['packet_id']:raise ValueError('Wrong original packet')
    for name,expected in prepared['file_hashes'].items():
        if sha(PACKET_ROOT/name)!=expected:raise ValueError('Original packet asset changed')
    return packet


def write_bytes(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(payload)


def package_zip(folder,job):
    save_new(folder/'REVIEW_JOB.json',job)
    files={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
    save_new(folder/'MANIFEST.json',dict(schema='portable-review-package/1',job=job['job_id'],files=files))
    archive=folder.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as package:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                info=zipfile.ZipInfo(folder.name+'/'+path.relative_to(folder).as_posix(),(2020,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                package.writestr(info,path.read_bytes())
    return dict(status='PREPARED_NOT_REVIEWED',phase=job['phase'],reviewer_id=job['reviewer_id'],
        job_id=job['job_id'],archive_name=archive.name,archive_sha256=sha(archive),
        archive_bytes=archive.stat().st_size,files=len(files)+1,
        images=job['image_count'],actual_new_reviewers=0,independence_verified=False,
        model_calls=0,author_answers_included=False,analyst_join_included=False)


def destination(code,phase,root):
    root=Path(root).resolve()
    if not root.is_relative_to((EC/'local').resolve()):raise ValueError('Reviewer bundles remain under local/')
    folder=root/('reviewer_'+code+'_'+phase)
    if folder.exists() or folder.with_suffix('.zip').exists():raise FileExistsError('Preserve existing reviewer packages')
    folder.mkdir(parents=True)
    return folder


def phase1(code,root=EXPORTS):
    code=reviewer_code(code);packet=frozen_packet();folder=destination(code,'phase1',root)
    payload='<script>window.BLIND_PACKET='+script_literal(packet)+';\n'
    payload+='window.BLIND_REVIEW_STORAGE_KEY='+script_literal('portable-phase1/'+code+'/'+packet['packet_id'])+';\n'
    payload+='window.BLIND_REVIEW_PROFILE='+script_literal(dict(reviewer_id=code,role='external_reviewer'))+';</script>'
    template=(UI_ROOT/'review_template.html').read_text(encoding='utf-8')
    if template.count('<!--PACKET-->')!=1:raise ValueError('Unexpected phase-1 template')
    template=template.replace('<div id="fields"></div>',
        '<p class="card">Tình trạng của một trường xét trên toàn ảnh: nếu giá trị còn đọc được ở nguồn phụ, '
        'ghi nhận giá trị đó và nguồn phụ. Nguồn phải diễn đạt đúng trường đang hỏi; không lấy số giấy tờ '
        'điền vào tên trường. Không đoán phần đã che.</p><div id="fields"></div>')
    write_bytes(folder/'index.html',template.replace('<!--PACKET-->',payload).encode('utf-8'))
    for name in ('review_core.js','review_ui.js'):
        write_bytes(folder/name,(UI_ROOT/name).read_bytes())
    write_bytes(folder/'packet_manifest.json',(PACKET_ROOT/'packet_manifest.json').read_bytes())
    for page in packet['pages']:
        write_bytes(folder/page['image'],(PACKET_ROOT/page['image']).read_bytes())
        if sha(folder/page['image'])!=page['file_sha256']:raise ValueError('Copied image changed')
    guide=f'''HƯỚNG DẪN NGƯỜI ĐÁNH GIÁ {code} — PHA 1

1. Giải nén toàn bộ ZIP. Mở index.html bằng Chrome/Edge trên máy.
   Không cần project, Python, model, tài khoản GitHub hoặc server.
2. Mã {code} và vai trò ngoài dự án được điền sẵn; sửa nếu không đúng.
   Tự chọn mức đã xem kết quả. Tính độc lập chưa được tự xác nhận.
3. Đọc 31 ảnh, ghi 86 mục. Chỉ chép từ ảnh hiện tại; không đoán phần che.
   Với mỗi nguồn nhìn thấy, ghi loại, vị trí, mức đọc và chữ quan sát được.
   Nếu có MRZ, chép cả hai dòng khi đọc được; giữ chữ O và số 0 khác nhau.
   Tình trạng của trường xét trên toàn ảnh, không chỉ ô chính: nếu nguồn phụ
   vẫn hỗ trợ đúng trường và đọc được, ghi nhận chữ và nguồn phụ đó.
4. Lưu nháp khi nghỉ. Xuất bản nháp JSON để sao lưu và nạp lại nếu cần.
   Khi đủ mục, bấm Xuất phiếu hoàn chỉnh; gửi file review-{code}-*.json.
   Các ghi chú khó hiểu/không chắc được ghi ngay trong từng trường.
5. Gửi riêng cho người tổ chức; không đăng câu trả lời lên GitHub.
   Giữ riêng số phút thực làm nếu thuận tiện. Phiếu không đo active time.

Đây chỉ là pha đọc ảnh. Chưa gửi output, đáp án hoặc phiếu tác giả.
Sau khi JSON này được nhận và khóa, bạn sẽ được cấp ZIP pha 2 riêng,
đối chiếu 46 cặp output bằng chính quan sát đã khóa của bạn.
Không trao đổi đáp án với người đánh giá khác trước khi hoàn tất độc lập.
Không cần gửi cả folder lại; chỉ gửi JSON đã xuất. Giữ ZIP để kiểm hash nếu cần.
'''
    write_bytes(folder/'README_VI.txt',guide.encode('utf-8'))
    job=dict(schema='reviewer-job/1',phase='phase1',reviewer_id=code,
        packet_id=packet['packet_id'],image_count=len(packet['pages']),
        field_slots=sum(len(p['fields']) for p in packet['pages']),
        model_outputs_included=False,author_answers_included=False,
        independence_verified=False,role_is_self_attested=True,
        ui_sha256=sha(folder/'review_ui.js'),instructions_sha256=sha(folder/'README_VI.txt'))
    job['job_id']=digest(job)
    return package_zip(folder,job)


def phase2(snapshot,root=EXPORTS):
    _,_,reviewer=ifv.sealed_phase1(snapshot)
    code=reviewer_code(reviewer['reviewer_id'])
    # This is the first access to cached output, after this reviewer's evidence seal.
    canonical_path=ifv.open_stage2(snapshot)
    packet=read(canonical_path.parent/'packet.json')
    portable=dict(packet,cases=[{k:v for k,v in c.items() if k!='author_reference'} for c in packet['cases']])
    folder=destination(code,'phase2',root)
    inner=folder/'reviews'/canonical_path.parent.name
    template=(UI_ROOT/'ifv_stage2.html').read_text(encoding='utf-8')
    reference_row='<p>Tham chiếu tác giả <strong id="reference"></strong></p>'
    if template.count(reference_row)!=1:raise ValueError('Unexpected reference display')
    template=template.replace(reference_row,'<span id="reference" hidden></span>')
    template=template.replace('Đáp án tác giả giúp đối chiếu nhưng không chứng minh phần chữ đã che còn đọc được.',
        'Giữ bất định khi thiếu căn cứ; gói này không cung cấp đáp án tác giả.')
    ui=(UI_ROOT/'ifv_stage2.js').read_text(encoding='utf-8')
    if ui.count("$('reference').textContent = c.author_reference;")!=1:
        raise ValueError('Unexpected reference reveal code')
    ui=ui.replace("$('reference').textContent = c.author_reference;","$('reference').textContent = '';")
    html=template.replace('<!--PACKET-->','<script>window.OUTPUT_PACKET='+script_literal(portable)+';</script>')
    html=html.replace('<!--UI-->','<script>'+ui+'</script>')
    write_bytes(inner/'index.html',html.encode('utf-8'))
    landing='<meta charset="utf-8"><a href="reviews/'+canonical_path.parent.name+'/index.html">Mở phiếu pha 2</a>'
    write_bytes(folder/'index.html',landing.encode('utf-8'))
    images=set()
    for case in packet['cases']:
        for side in ('before','after'):
            source=(canonical_path.parent/case[side+'_image']).resolve()
            target=(inner/case[side+'_image']).resolve()
            if not source.is_relative_to((PACKET_ROOT/'images').resolve()) or not target.is_relative_to(folder.resolve()):
                raise ValueError('Image path escaped reviewer package')
            if sha(source)!=case[side+'_evidence']['image_sha256']:raise ValueError('Bound image changed')
            if target not in images:write_bytes(target,source.read_bytes());images.add(target)
    guide=f'''PHA 2 — {code}
Mở index.html sau giải nén. Xem hai ảnh và quan sát pha 1 của chính bạn.
Ghi điều kiện/lý do trước khi mở output. Sau đó đánh giá cả hai giá trị;
chú ý O/0, ký tự thiếu và output không trống không phải trường hợp bỏ sót.
Đáp án tác giả và kết quả người khác không nằm trong gói này.
Lưu từng ca, có thể sao lưu/nạp nháp. Khi đủ {len(packet['cases'])} ca,
xuất phiếu hoàn chỉnh JSON và gửi lại. Không đăng phiếu lên GitHub.
'''
    write_bytes(folder/'README_VI.txt',guide.encode('utf-8'))
    job=dict(schema='reviewer-job/1',phase='phase2',reviewer_id=code,phase1_snapshot=snapshot,
        canonical_packet_id=packet['packet_id'],portable_view_sha256=digest(portable),
        image_count=len(images),cases=len(packet['cases']),author_answers_included=False,
        source_publication_sha256=sha(canonical_path.parent/'publication.json'),independence_verified=False)
    job['job_id']=digest(job)
    return package_zip(folder,job)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('phase1','phase2'))
    parser.add_argument('--reviewer')
    parser.add_argument('--snapshot')
    args=parser.parse_args()
    if args.phase=='phase1' and not args.reviewer:parser.error('--reviewer is required')
    if args.phase=='phase2' and not args.snapshot:parser.error('--snapshot is required')
    result=phase1(args.reviewer) if args.phase=='phase1' else phase2(args.snapshot)
    print(json.dumps(result))
