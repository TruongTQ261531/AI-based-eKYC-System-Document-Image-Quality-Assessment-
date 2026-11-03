"""Evidence-backed progress and a development/train-only hard-case inventory.

This post-hoc diagnostic does not train, change labels or re-open test outputs.
Private case identifiers stay in cache. Public files contain counts and hashes.
"""
import collections
import math
from pathlib import Path

from research.v2_common import ROOT, OUT as R2OUT, CACHE as R2CACHE, read, save, sha, preserve_v1
from research.v3_common import DATA, CACHE as SOURCE_CACHE, OUT as SOURCE_OUT, signature
from research.v3_metrics import canonical, scoring

OUT = ROOT/'research/results/current_progress'
CACHE = ROOT/'research/cache/current_progress'
NEIGHBOR_GAP = .08  # Fraction of image diagonal; diagnostic only, not legibility.


def bbox(quad):
    return (min(p[0] for p in quad), min(p[1] for p in quad),
            max(p[0] for p in quad), max(p[1] for p in quad))


def gap(a, b):
    return math.hypot(max(0., a[0]-b[2], b[0]-a[2]),
                      max(0., a[1]-b[3], b[1]-a[3]))


def geometry(sample):
    """Only declared body regions and source-aware supported keys are considered."""
    supported = set(sample['target'])
    hidden = {f['key'] for f in sample['fields']} - supported
    hidden_boxes = [bbox(f['quad']) for f in sample['fields'] if f['key'] in hidden]
    neighbor = set()
    for field in sample['fields']:
        key = field['key']
        if key not in supported or field.get('occluded', False):
            continue
        # An alternate MRZ source can keep the key supported even when its body
        # is outside the frame. Do not call that body region a visible neighbor.
        if not any(r['kind'].startswith('body') for r in sample['source_refs'].get(key, [])):
            continue
        box = bbox(field['quad'])
        if box[0] < 0 or box[1] < 0 or box[2] > sample['width'] or box[3] > sample['height']:
            continue
        if hidden_boxes and min(gap(box, other) for other in hidden_boxes) <= NEIGHBOR_GAP*math.hypot(sample['width'], sample['height']):
            neighbor.add(key)
    return hidden, neighbor


def diagnose(sample, text):
    if sample['role'] != 'development':
        raise ValueError('Model-error mining accepts development only; never test')
    metrics, fields = scoring(sample, text)
    hidden, neighbor = geometry(sample)
    omitted = neighbor - set(fields)
    wrong = {key for key in neighbor & set(fields)
             if not any(canonical(key, fields[key]) == canonical(key, ref['value'], ref['kind'])
                        for ref in sample['source_refs'][key])}
    return dict(uid=sample['uid'], physical_id=sample['physical_id'],
                hidden_output_keys=sorted(hidden & set(fields)),
                neighbor_omission_keys=sorted(omitted), neighbor_wrong_keys=sorted(wrong),
                supported_neighbor_keys=sorted(neighbor),
                unsupported_nonempty=metrics['unsupported_nonempty'],
                visible_omissions=metrics['visible_omissions'])


def select_train(rows, error_keys, limit=32):
    if any(row['role'] != 'train' for row in rows):
        raise ValueError('Hard-example training inventory must contain train only')
    ranked = []
    for row in rows:
        if row['capture'] not in ('value_mask', 'field_clip'):
            continue
        hidden, neighbor = geometry(row)
        if not hidden or not neighbor:
            continue
        weight = sum(error_keys.get(k, 0) for k in hidden | neighbor)
        ranked.append((weight, row['uid'], row))
    ranked.sort(key=lambda r: (-r[0], r[1]))
    selected, ids = [], set()
    for weight, _, row in ranked:
        if row['physical_id'] in ids:
            continue
        selected.append(dict(uid=row['uid'], physical_id=row['physical_id'],
                             input_sha256=row['input_sha256'], dev_error_key_weight=weight))
        ids.add(row['physical_id'])
        if len(selected) == limit:
            break
    return selected


def development_records(model, samples):
    folder = (SOURCE_CACHE if model.startswith('source_') else R2CACHE)/'predictions'/('development_'+model)
    seen, records, evidence = set(), [], []
    for path in sorted(folder.glob('*.json')):
        prediction = read(path)
        uid = prediction['uid']
        if uid not in samples or uid in seen:
            raise ValueError('Duplicate or non-development prediction in mining input')
        sample = samples[uid]
        if prediction['input_sha256'] != sample['input_sha256']:
            raise ValueError('Development pixels differ')
        records.append(diagnose(sample, prediction['_private_text']))
        evidence.append(dict(file=path.relative_to(ROOT).as_posix(), sha256=sha(path)))
        seen.add(uid)
    if seen != set(samples):
        raise ValueError('Missing development predictions')
    return records, evidence


def make():
    preserve_v1()
    raw = read(DATA/'samples.json')
    if sha(DATA/'samples.json') != read(SOURCE_OUT/'dataset_card.json')['samples_sha256']:
        raise ValueError('Sealed data changed')
    development = {r['uid']:r for r in raw if r['role']=='development'}
    training = [r for r in raw if r['role']=='train' and r['variant']=='partial']
    models, private, evidence = {}, {}, []
    for model in ('control_42','partial_42','source_42','control_31415','partial_31415','source_31415'):
        records, proof = development_records(model, development)
        private[model] = records
        evidence.extend(proof)
        models[model] = dict(cases=len(records),
            hidden_supported_contract_outputs=sum(len(r['hidden_output_keys']) for r in records),
            neighbor_visible_omissions=sum(len(r['neighbor_omission_keys']) for r in records),
            neighbor_visible_wrong_values=sum(len(r['neighbor_wrong_keys']) for r in records),
            neighbor_visible_reference_keys=sum(len(r['supported_neighbor_keys']) for r in records),
            cases_with_both_errors=sum(bool(r['hidden_output_keys'] and r['neighbor_omission_keys']) for r in records))
    # The previously development-selected deployment candidate supplies error
    # types, not test performance; development IDs never enter training.
    selected_model = read(SOURCE_OUT/'test_lock.json')['selected_model']
    if selected_model not in private:
        raise ValueError('Selected comparator unavailable for diagnostic')
    keys = collections.Counter(k for r in private[selected_model]
        for name in ('hidden_output_keys','neighbor_omission_keys','neighbor_wrong_keys') for k in r[name])
    selected = select_train(training, keys)
    dev_ids = {r['physical_id'] for r in development.values()}
    if dev_ids & {r['physical_id'] for r in selected}:
        raise ValueError('Development identity entered training inventory')
    cache_record = dict(development_errors=private, selected_train=selected,
                        model=selected_model, next_training_started=False)
    save(CACHE/'hard_case_inventory.json',cache_record)
    training_runs = []
    for folder, pattern in ((R2OUT,'train_*.json'),(SOURCE_OUT,'train_*.json')):
        for path in sorted(folder.glob(pattern)):
            run = read(path); events = run['events']
            training_runs.append(dict(name=path.stem, optimizer_updates=events[-1]['step'],
                presentations=events[-1]['cursor'], first_update_utc=events[0]['time_utc'],
                last_update_utc=events[-1]['time_utc'], last_event_wall_seconds=events[-1]['wall_seconds'],
                peak_allocated_GiB=max(e['peak_allocated_bytes'] for e in events)/2**30,
                evidence_sha256=sha(path)))
    profiles = read(R2OUT/'input_choice.json')
    progress = dict(date='2026-11-03', source_signature=signature(),
        source_data_sha256=sha(DATA/'samples.json'), completed_training_runs=training_runs,
        sum_recorded_training_event_wall_seconds=sum(r['last_event_wall_seconds'] for r in training_runs),
        training_event_wall_excludes_setup_and_evaluation=True,
        new_neural_calls_in_this_diagnostic=0, new_finetunes_in_this_diagnostic=0,
        input_profiles=[dict(profile=r['profile'],development_f1=r['summary']['f1'],
                            mean_fresh_seconds=r['mean_fresh_seconds']) for r in profiles['comparisons']],
        selected_input=profiles['profile'], development_error_diagnostic=models,
        diagnostic_neighbor_gap_fraction_of_diagonal=NEIGHBOR_GAP,
        independent_human_legibility_annotations=0, independent_new_camera_collection=False,
        hard_case_training_inventory_size=len(selected), hard_case_training_identities=len({r['physical_id'] for r in selected}),
        hard_case_selection_source='train geometry plus development-only error types',
        hard_case_inventory_sha256=sha(CACHE/'hard_case_inventory.json'),
        test_outputs_opened_for_mining=0, next_hard_case_training_started=False,
        old_test_is_now_open=True, next_changed_method_requires_new_test=True,
        V1_used_as_unmatched_transfer_baseline=True, matched_R2_source_steps=320,
        priorities=dict(labels='partial: author/synthetic text+geometry; no independent legibility',
            input='completed bounded 4-profile development experiment; not all camera populations',
            errors='partial: uniform partial training complete; hard-case inventory now prepared, not trained',
            comparison='matched R2/V3 and test fresh relative to V1 complete; no fresh test for a future intervention'),
        development_prediction_hashes=evidence)
    save(OUT/'progress.json',progress)
    lines=['# Tiến độ bốn ưu tiên: đối chiếu với bằng chứng', '',
        'Bản cập nhật ngày 2026-11-03. Đây là chẩn đoán hậu nghiệm từ train/development; '
        'không huấn luyện lại hoặc sửa các kết quả đã công bố.', '',
        '| Ưu tiên | Đã thực hiện | Còn thiếu |','|---|---|---|',
        '| 1. Nhãn OCR | R2/V3 có transcript tác giả/giả lập, vị trí và trạng thái hiển thị theo hình học; train 128 ID/640 slot mỗi arm, dev 24 ID/72 ảnh, test 48 ID/144 ảnh | Chưa có người gán nhãn legibility độc lập; chưa có bộ camera Việt Nam mới. Clean/Blur không được dùng thay transcript |',
        '| 2. Ảnh vào VLM | Bốn profile raw2/raw4/rect2/rect4 trên cùng 16 ảnh từ 8 ID development; chọn rect2 trước train/test; có probe backward 2/4 tile và đo suy luận từ pixel | Probe ngắn không phải full training mọi profile; VRAM allocated không phải tổng VRAM vật lý; camera quần thể mới chưa kiểm chứng |',
        '| 3. Hai lỗi đối nghịch | Huấn luyện complete/partial hai seed; thêm source supervision hai seed. Bổ sung kiểm kê lỗi dev và danh sách ca train khó trong cập nhật này | Danh sách ca khó chưa được dùng huấn luyện; chưa có kết quả test mới cho một can thiệp hard mining |',
        '| 4. Đối chứng | R2/V3 cùng 128 ID, 640 slot, 320 update, 1280 lượt ảnh/arm, hai seed; test mới so với V1; giữ nguyên V1 | V1 là transfer baseline khác budget, không phải đối chứng nhân quả. Test R2/V3 đã mở; mọi sửa phương pháp sau đây cần test mới khác |', '',
        '## Vì sao thời gian lượt hoàn tất ngắn', '',
        f'Sáu run đã có đủ checkpoint trước lượt chốt. Tổng bộ đếm wall ở update cuối của sáu run: '
        f'{progress["sum_recorded_training_event_wall_seconds"]/60:.2f} phút. Số này không gồm chuẩn bị feature, '
        'development, benchmark, audit và chờ tiến trình; không phải tổng thời gian GPU hoạt động. '
        'Một lượt benchmark V1 còn chứa 5 giờ 20 phút máy sleep do pin, có nhật ký riêng. '
        'Không quy toàn bộ thời gian treo máy thành thời gian huấn luyện.', '',
        '| Run | Update | Lượt ảnh | Wall update cuối (phút) | Peak allocated GiB |',
        '|---|---:|---:|---:|---:|']
    lines += [f'| {r["name"]} | {r["optimizer_updates"]} | {r["presentations"]} | {r["last_event_wall_seconds"]/60:.2f} | {r["peak_allocated_GiB"]:.3f} |' for r in training_runs]
    lines += ['', '## Thử ảnh đầu vào đã chạy', '', '| Profile | F1 development panel | Thời gian trung bình từ pixel (s) |','|---|---:|---:|']
    lines += [f'| {r["profile"]} | {r["development_f1"]:.4f} | {r["mean_fresh_seconds"]:.2f} |' for r in progress['input_profiles']]
    lines += ['', 'Chọn rect2 trên development. Backward smoke probe: raw2 '
        f'{max(e["peak_allocated_bytes"] for e in read(R2OUT/"probe_raw2.json")["events"])/2**30:.3f} GiB; raw4 '
        f'{max(e["peak_allocated_bytes"] for e in read(R2OUT/"probe_raw4.json")["events"])/2**30:.3f} GiB allocated. '
        'Đây là bốn bước với ảnh smoke riêng, không phải bốn full training run.', '',
        '## Hai nhóm lỗi trên development', '',
        'Cạnh vùng thiếu: khoảng cách hai bounding box tối đa 8% đường chéo ảnh; chỉ xét thân chữ '
        'còn nguyên và có nguồn hỗ trợ. Đây là quy tắc chẩn đoán hình học, không phải nhãn đọc được của người. '
        'Key còn nguồn MRZ không bị gọi là vắng chỉ vì ô thân thẻ bị che.', '',
        '| Model | Ảnh dev | Output key mất toàn bộ nguồn khai báo | Bỏ sót key rõ cạnh vùng thiếu | Sai key rõ cạnh vùng thiếu |',
        '|---|---:|---:|---:|---:|']
    lines += [f'| {m} | {r["cases"]} | {r["hidden_supported_contract_outputs"]} | {r["neighbor_visible_omissions"]} | {r["neighbor_visible_wrong_values"]} |' for m,r in models.items()]
    lines += ['', f'Đã chọn {len(selected)} ca train từ {len({r["physical_id"] for r in selected})} ID, '
        'mỗi ID tối đa một ca, để có cả phần bị che/cắt và phần thân chữ rõ bên cạnh. '
        'Loại lỗi được lấy từ model partial_42 đã chọn bằng dev. Không đưa ID development vào train, '
        'không mở output test để chọn ca. Danh sách/đáp án riêng ở cache local; public chỉ có số lượng và hash. '
        'Đây mới là inventory; không tính thành lần train, ảnh mới hay cải tiến test.', '']
    if (OUT/'verification.json').exists():
        checked=read(OUT/'verification.json')
        lines += ['## Kiểm thử bản cập nhật', '',
            f'{checked["combined_unique_python_checks_passed"]} kiểm tra Python và '
            f'{checked["subtests_passed"]} subtest đã qua. Môi trường chính qua 274 bài và '
            'bỏ qua 4 bài cần training cache; chạy riêng cả 4 bằng overlay có sẵn đều qua. '
            f'Frontend: {checked["frontend_behavior_checks_passed"]} bài qua, gồm mentor và các bản nghiên cứu. '
            'Test camera/network là mô phỏng, không phải benchmark người dùng thật.', '',
            'Lần chạy bị giới hạn quyền local đã kẹt trong Windows socketpair. Bản wrapper chẩn đoán '
            'đầu thiếu đường dẫn repository khi import; lần sửa wrapper xác nhận chỗ chờ socket. '
            'Bộ test chạy lại với quyền local đã qua; không sửa runtime để né lỗi. '
            'Các nhật ký thất bại/gián đoạn được giữ trong cache và băm trong '
            '[verification.json](results/current_progress/verification.json).', '']
    lines += [
        '## Bước còn dang dở', '',
        'Thiết kế và đăng ký vòng huấn luyện dùng ca khó, tạo đối chứng cùng exposure, '
        'chuẩn bị một tập test chưa từng dùng để điều chỉnh phương pháp, rồi mới huấn luyện/chấm và báo cáo tất cả seed. '
        'Người đánh giá và bộ camera mới hiện chưa có; không thay bằng nhãn do model tự viết. '
        'Không gọi bốn ưu tiên là hoàn tất hoàn toàn hoặc khẳng định đạt CORE B.', '',
        'Bằng chứng máy đọc: [progress.json](results/current_progress/progress.json). '
        'Kết quả benchmark cũ: [V3](V3_RESULTS_VI.md), [R2](V2_RESULTS_VI.md).']
    (ROOT/'research/PRIORITY_PROGRESS_VI.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print('PROGRESS_AUDIT_READY',len(training_runs),'completed_runs;',len(selected),'train_hard_cases; new_neural_calls=0')


if __name__ == '__main__':
    make()
