"""Render the joint D4 descriptive table from aggregate cells (no member inputs)."""
import argparse
import json
from pathlib import Path

SHORT={'FAULT':'F','NO_FAULT':'N','UNKNOWN':'U','INVALID_TEST':'I'}


def table(data):
    lines=['# D4 · Bảng phân tầng đầy đủ','',
           'Mỗi dòng là một tổ hợp quan sát trên controls dựng sẵn. F = FAULT, N = NO_FAULT, U = UNKNOWN, I = INVALID_TEST. '
           'Chiều chuyển là asserted → checked. Trong mỗi ô lý do, thứ tự cũng là asserted → checked. '
           'Hai cột rút quyết định ghi số FAULT / NO_FAULT. Reference được chấp nhận ở đây chỉ là reference dựng sẵn.','',
           '| Tier | Trường / kiểu | Nguồn sau biến đổi | Literal sau / guard chung | Pointwise và lý do | Relation và lý do | Rút pointwise F/N | Rút relation F/N | Reference | Ca |',
           '|---:|---|---|---|---|---|---:|---:|---|---:|']
    for s in data['d4']['strata']:
        def transition(ep):
            pair=' → '.join(SHORT[s[ep+'_'+arm]] for arm in ('asserted','checked'))
            reasons=' → '.join(s[ep+'_'+arm+'_reason'] for arm in ('asserted','checked'))
            return f'{pair} ({reasons})'
        def withdrawals(ep):
            return f"{s[ep+'_withdrawn_alarms']} / {s[ep+'_withdrawn_no_fault']}"
        cols=[str(s['tier']),s['field']+' / '+s['value_kind'],s['after_sources'],
              s['after_literal']+' / '+s['shared_gate'],transition('pointwise'),transition('relation'),
              withdrawals('pointwise'),withdrawals('relation'),s['reference_status'],str(s['count'])]
        lines.append('| '+' | '.join(cols)+' |')
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('aggregate',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    with args.output.open('x',encoding='utf8',newline='\n') as f:
        f.write(table(json.loads(args.aggregate.read_bytes())))
