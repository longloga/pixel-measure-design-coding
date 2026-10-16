#!/usr/bin/env python3
"""Ghi & báo cáo hiệu suất mỗi lần code 1 trang: thời gian thực tế, số vòng render-sửa, số lần bị yêu cầu
sửa (và lỗi thuộc bài học nào trong references/lessons.md), độ lệch cuối, lỗi audit, lỗi phát sinh sau giao.
Dữ liệu dùng chung mọi dự án: <skill>/metrics/runs.jsonl (mỗi dòng 1 sự kiện). Run hiện tại lưu theo cwd.

  python3 metrics.py start --page index --source png --note "LP top, PC+SP"
  python3 metrics.py iter --pixeldiff m/pd_pc.json --pixeldiff m/pd_sp.json --audit m/audit.json
  python3 metrics.py fix --by user --lesson L-RESP-02 --note "SP override làm vỡ PC"     # người dùng yêu cầu sửa
  python3 metrics.py fix --by self --lesson L-MEAS-03 --note "line-height p bị base ghi đè"  # tự phát hiện khi review
  python3 metrics.py end --deliver                  # giao cho người dùng (bắt đầu tính lỗi sau giao)
  python3 metrics.py fix --by user --after --lesson L-LINK-01 --note "link PDF hỏng"     # lỗi phát sinh sau giao
  python3 metrics.py review --score 4 --note "lệch nhẹ footer"   # đánh giá chất lượng sau review (1-5)
  python3 metrics.py report                         # bảng tất cả run + bài học tái phạm nhiều nhất
  python3 metrics.py report --project my-project --csv out.csv
"""
import argparse, json, os, sys, time
from collections import Counter, defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(HERE, 'metrics', 'runs.jsonl')
CUR = os.path.join(HERE, 'metrics', 'current.json')


def now(): return datetime.now().isoformat(timespec='seconds')


def load_cur():
    try: return json.load(open(CUR)).get(os.getcwd())
    except Exception: return None


def save_cur(rid):
    os.makedirs(os.path.dirname(CUR), exist_ok=True)
    try: d = json.load(open(CUR))
    except Exception: d = {}
    if rid: d[os.getcwd()] = rid
    else: d.pop(os.getcwd(), None)
    json.dump(d, open(CUR, 'w'), ensure_ascii=False, indent=1)


def emit(ev):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    ev.setdefault('ts', now())
    with open(LOG, 'a') as f: f.write(json.dumps(ev, ensure_ascii=False) + '\n')


def need_run(a):
    rid = a.run or load_cur()
    if not rid: sys.exit('Chưa có run — chạy `metrics.py start --page ...` trước (hoặc --run ID).')
    return rid


def events():
    if not os.path.exists(LOG): return []
    return [json.loads(l) for l in open(LOG) if l.strip()]


def summarize():
    runs = defaultdict(lambda: {'iters': [], 'fix_user': [], 'fix_self': [], 'fix_after': [], 'reviews': []})
    for e in events():
        r = runs[e['run']]; t = e['type']
        if t == 'start': r.update(start=e['ts'], project=e['project'], page=e['page'], source=e.get('source'), note=e.get('note'))
        elif t == 'iter': r['iters'].append(e)
        elif t == 'fix':
            key = 'fix_after' if e.get('after') else ('fix_user' if e['by'] == 'user' else 'fix_self')
            r[key].append(e)
        elif t == 'end': r['end'] = e['ts']; r['active_min'] = e.get('active_min')
        elif t == 'review': r['reviews'].append(e)
    out = []
    for rid, r in runs.items():
        if 'start' not in r: continue
        st = datetime.fromisoformat(r['start']); en = datetime.fromisoformat(r['end']) if r.get('end') else None
        last = r['iters'][-1] if r['iters'] else {}
        out.append({
            'run': rid, 'project': r['project'], 'page': r['page'], 'source': r.get('source'), 'start': r['start'][:16],
            'minutes': round(((en or datetime.now()) - st).total_seconds() / 60),
            'active_min': r.get('active_min'), 'done': bool(en),
            'iterations': len(r['iters']),
            'user_fixes': len(r['fix_user']), 'self_fixes': len(r['fix_self']), 'bugs_after': len(r['fix_after']),
            'max_delta': last.get('max_abs_delta'), 'mean_diff': last.get('mean_diff_pct'),
            'audit_E': last.get('audit_E'), 'audit_W': last.get('audit_W'),
            'review': r['reviews'][-1]['score'] if r['reviews'] else None,
            'lessons': [f.get('lesson') for f in r['fix_user'] + r['fix_self'] + r['fix_after'] if f.get('lesson')],
            'first_diff': r['iters'][0].get('mean_diff_pct') if r['iters'] else None,
        })
    return out


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('start'); s.add_argument('--page', required=True); s.add_argument('--project', default=os.path.basename(os.getcwd()))
    s.add_argument('--source', choices=['png', 'xd', 'figma', 'other'], default='png'); s.add_argument('--note', default='')
    i = sub.add_parser('iter'); i.add_argument('--pixeldiff', action='append', default=[]); i.add_argument('--audit'); i.add_argument('--note', default='')
    f = sub.add_parser('fix'); f.add_argument('--by', choices=['user', 'self'], required=True); f.add_argument('--lesson', default='')
    f.add_argument('--after', action='store_true', help='lỗi phát hiện SAU khi đã giao'); f.add_argument('--note', default='')
    e = sub.add_parser('end'); e.add_argument('--deliver', action='store_true'); e.add_argument('--active-min', type=int, help='thời gian làm thực (phút), nếu khác wall time')
    v = sub.add_parser('review'); v.add_argument('--score', type=int, choices=range(1, 6), required=True); v.add_argument('--note', default='')
    r = sub.add_parser('report'); r.add_argument('--project'); r.add_argument('--last', type=int, default=30); r.add_argument('--csv')
    sub.add_parser('status')
    for p in (i, f, e, v): p.add_argument('--run')
    a = ap.parse_args()

    if a.cmd == 'start':
        rid = f'{a.project}/{a.page}/{datetime.now():%Y%m%d-%H%M}'
        emit({'run': rid, 'type': 'start', 'project': a.project, 'page': a.page, 'source': a.source, 'note': a.note, 'cwd': os.getcwd()})
        save_cur(rid); print('run:', rid)
    elif a.cmd == 'iter':
        rid = need_run(a); ev = {'run': rid, 'type': 'iter', 'note': a.note}
        pds = [json.load(open(p))['summary'] for p in a.pixeldiff]
        if pds:
            ev['max_abs_delta'] = max(p['max_abs_delta'] for p in pds)
            ev['mean_diff_pct'] = round(sum(p['mean_diff_pct'] for p in pds) / len(pds), 2)
            ev['bands_bad'] = sum(p['bands_bad'] for p in pds); ev['height_diff'] = [p['height_diff'] for p in pds]
        if a.audit:
            t = json.load(open(a.audit))['total']; ev['audit_E'] = t.get('E', 0); ev['audit_W'] = t.get('W', 0)
        n = sum(1 for x in events() if x['run'] == rid and x['type'] == 'iter') + 1
        emit(ev); print(f'vòng {n}:', {k: v for k, v in ev.items() if k not in ('run', 'type')})
    elif a.cmd == 'fix':
        rid = need_run(a); emit({'run': rid, 'type': 'fix', 'by': a.by, 'after': a.after, 'lesson': a.lesson, 'note': a.note})
        if a.lesson:
            hits = Counter(x.get('lesson') for x in events() if x['type'] == 'fix')[a.lesson]
            if hits >= 2: print(f'! {a.lesson} đã lặp lại {hits} lần (mọi dự án) — cân nhắc nâng mức nghiêm trọng / thêm bước kiểm tra tự động trong lessons.md')
        print('đã ghi fix', a.by, a.lesson)
    elif a.cmd == 'end':
        rid = need_run(a); emit({'run': rid, 'type': 'end', 'deliver': a.deliver, 'active_min': a.active_min}); print('kết thúc', rid)
    elif a.cmd == 'review':
        rid = need_run(a); emit({'run': rid, 'type': 'review', 'score': a.score, 'note': a.note}); print('đã ghi review', a.score)
    elif a.cmd == 'status':
        print('run hiện tại:', load_cur() or '(không có)')
    elif a.cmd == 'report':
        rows = [x for x in summarize() if not a.project or x['project'] == a.project][-a.last:]
        if not rows: print('Chưa có dữ liệu.'); return
        cols = ['start', 'project', 'page', 'minutes', 'iterations', 'user_fixes', 'self_fixes', 'bugs_after', 'first_diff', 'mean_diff', 'max_delta', 'audit_E', 'review']
        w = {c: max(len(c), *(len(str(x[c])) for x in rows)) for c in cols}
        print('  '.join(c.ljust(w[c]) for c in cols))
        for x in rows: print('  '.join(str(x[c] if x[c] is not None else '-').ljust(w[c]) for c in cols) + ('' if x['done'] else '  (đang làm)'))
        done = [x for x in rows if x['done']]
        if done:
            avg = lambda k: round(sum(x[k] or 0 for x in done) / len(done), 1)
            print(f'\nTB {len(done)} run xong: {avg("minutes")} phút, {avg("iterations")} vòng, {avg("user_fixes")} lần bị yêu cầu sửa, '
                  f'{avg("bugs_after")} lỗi sau giao, review {avg("review")}/5')
        lc = Counter(l for x in rows for l in x['lessons'])
        if lc:
            print('\nBài học bị vi phạm nhiều nhất (ưu tiên đưa vào kiểm tra tự động / nhắc trong SKILL.md):')
            for l, n in lc.most_common(10): print(f'  {n:>3}× {l}')
        if a.csv:
            import csv
            with open(a.csv, 'w', newline='') as fh:
                wr = csv.DictWriter(fh, fieldnames=cols + ['lessons']); wr.writeheader()
                for x in rows: wr.writerow({**{c: x[c] for c in cols}, 'lessons': ' '.join(x['lessons'])})
            print('csv:', a.csv)


if __name__ == '__main__':
    main()
