#!/usr/bin/env python3
"""1 ページのコーディングごとの実績を記録・レポートする: 実作業時間、レンダリング→修正のループ回数、修正依頼の回数
（とそれが references/lessons.md のどの教訓に該当するか）、最終的なズレ、audit エラー、納品後に発生した不具合。
データは全案件共通: <skill>/metrics/runs.jsonl（1 行 1 イベント）。現在の run は cwd ごとに保存。

  python3 metrics.py start --page index --source png --note "LP top, PC+SP"
  python3 metrics.py iter --pixeldiff m/pd_pc.json --pixeldiff m/pd_sp.json --audit m/audit.json
  python3 metrics.py fix --by user --lesson L-RESP-02 --note "SP の上書きで PC が崩れた"     # ユーザーからの修正依頼
  python3 metrics.py fix --by self --lesson L-MEAS-03 --note "p の line-height が base に上書きされた"  # レビュー時に自分で発見
  python3 metrics.py end --deliver                  # ユーザーに納品（ここから納品後の不具合をカウント）
  python3 metrics.py fix --by user --after --lesson L-LINK-01 --note "PDF リンク切れ"     # 納品後に発生した不具合
  python3 metrics.py review --score 4 --note "footer が少しずれ"   # レビュー後の品質評価（1-5）
  python3 metrics.py report                         # 全 run の一覧 + 再発の多い教訓
  python3 metrics.py report --project my-project --csv out.csv
"""
import argparse, glob, json, os, sys, time
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


STALE_H = 12  # `end` されず 12時間以上新しいイベントが無い run → 中断扱い


def find_sources(days=60, near_days=14):
    """L-MEAS-11: XD/Figma の元ファイルを探す。（プロジェクト内は 3 階層以内、Desktop/Downloads は near_days 日以内に更新されたもの）を返す。"""
    now_ = time.time()
    proj = {p for d in range(4) for ext in ('xd', 'fig')
            for p in glob.glob(os.path.join(os.getcwd(), *(['*'] * d), f'*.{ext}')) if os.path.getmtime(p) > now_ - days * 86400}
    near = {p for base in ('~/Desktop', '~/Downloads') for ext in ('xd', 'fig')
            for p in glob.glob(os.path.join(os.path.expanduser(base), f'*.{ext}')) if os.path.getmtime(p) > now_ - near_days * 86400}
    key = lambda p: -os.path.getmtime(p)
    return sorted(proj, key=key), sorted(near - proj, key=key)


def summarize():
    runs = defaultdict(lambda: {'iters': [], 'fix_user': [], 'fix_self': [], 'fix_after': [], 'reviews': []})
    for e in events():
        r = runs[e['run']]; t = e['type']; r['last'] = e['ts']
        if t == 'start': r.update(start=e['ts'], project=e['project'], page=e['page'], source=e.get('source'), note=e.get('note'))
        elif t == 'iter': r['iters'].append(e)
        elif t == 'fix':
            key = 'fix_after' if e.get('after') else ('fix_user' if e['by'] == 'user' else 'fix_self')
            r[key].append(e)
        elif t == 'end': r['end'] = e['ts']; r['active_min'] = e.get('active_min'); r['abandoned'] = e.get('abandoned', False)
        elif t == 'review': r['reviews'].append(e)
    out = []
    for rid, r in runs.items():
        if 'start' not in r: continue
        st = datetime.fromisoformat(r['start']); en = datetime.fromisoformat(r['end']) if r.get('end') else None
        last_ts = datetime.fromisoformat(r['last'])
        if en is None and (datetime.now() - last_ts).total_seconds() > STALE_H * 3600:
            en = last_ts; r['abandoned'] = True          # 中断: 現在時刻ではなく最後のイベントまでで計算
        if r.get('abandoned') and r.get('end'):
            en = min(en, last_ts) if en else last_ts
        last = r['iters'][-1] if r['iters'] else {}
        out.append({
            'run': rid, 'project': r['project'], 'page': r['page'], 'source': r.get('source'), 'start': r['start'][:16],
            'minutes': round(((en or datetime.now()) - st).total_seconds() / 60),
            'active_min': r.get('active_min'), 'done': bool(en), 'abandoned': bool(r.get('abandoned')),
            'iterations': len(r['iters']),
            'user_fixes': len(r['fix_user']), 'self_fixes': len(r['fix_self']), 'bugs_after': len(r['fix_after']),
            # ユーザーからの修正依頼すべて（納品前＋納品後）— 以前は納品前のみ数えていたため常に ≈ 0 だった
            'user_req': len(r['fix_user']) + sum(1 for x in r['fix_after'] if x.get('by') == 'user'),
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
    s.add_argument('--no-source-check', action='store_true', help='bỏ cảnh báo L-MEAS-11 (đã xác nhận không có file nguồn dùng được)')
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
        old = load_cur()
        if old:
            last = max((x['ts'] for x in events() if x['run'] == old), default=now())
            if not any(x['run'] == old and x['type'] == 'end' for x in events()):
                emit({'run': old, 'type': 'end', 'deliver': False, 'abandoned': True, 'ts': last})
                print(f'! run cũ {old} chưa end → tự đóng (bỏ dở) tại {last[:16]}')
        if a.source in ('png', 'other') and not a.no_source_check:
            proj, near = find_sources()
            if proj or near:
                print('!! L-MEAS-11: có file nguồn XD/Figma — HỎI người dùng file nào là design của trang này; có thì lấy spec bằng')
                print('   xdspec.py / figspec.py và start lại với --source xd|figma, KHÔNG đo từ ảnh.')
                for p in proj[:5]: print(f'   [trong dự án] {p}')
                for p in near[:5]: print(f'   [{datetime.fromtimestamp(os.path.getmtime(p)):%m-%d}] {p}')
                print('   (đã xác nhận không dùng được → chạy lại với --no-source-check, ghi lý do vào --note)')
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
        cols = ['start', 'project', 'page', 'minutes', 'iterations', 'user_req', 'bugs_after', 'self_fixes', 'first_diff', 'mean_diff', 'max_delta', 'audit_E', 'review']
        w = {c: max(len(c), *(len(str(x[c])) for x in rows)) for c in cols}
        print('  '.join(c.ljust(w[c]) for c in cols))
        for x in rows: print('  '.join(str(x[c] if x[c] is not None else '-').ljust(w[c]) for c in cols)
                             + ('  (bỏ dở)' if x['abandoned'] else '' if x['done'] else '  (đang làm)'))
        done = [x for x in rows if x['done'] and not x['abandoned']]
        if done:
            def avg(k):
                v = [x[k] for x in done if x[k] is not None]
                return round(sum(v) / len(v), 1) if v else '-'
            nrev = sum(1 for x in done if x['review'] is not None)
            print(f'\nTB {len(done)} run xong (bỏ {sum(x["abandoned"] for x in rows)} run bỏ dở): {avg("minutes")} phút, {avg("iterations")} vòng, '
                  f'{avg("user_req")} lần người dùng yêu cầu sửa (trong đó {avg("bugs_after")} sau giao), '
                  f'review {avg("review")}/5 ({nrev} run có chấm)')
            if nrev < len(done) / 2:
                print('  ! dưới nửa số run có điểm review → sau mỗi lần giao hỏi người dùng 1–5 rồi `metrics.py review --score N`')
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
